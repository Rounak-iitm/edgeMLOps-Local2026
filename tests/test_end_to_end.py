"""End-to-end test suite for the Zero-Cloud Edge Retraining Loop.

Run with:  python -m pytest tests/ -v
(or just:  python tests/test_end_to_end.py)

Covers, against real demo data (no mocks):
  1. Pipeline correctly SKIPS retraining when there's no drift.
  2. Pipeline correctly DETECTS drift and retrains + deploys when the
     machine is simulated as degrading.
  3. The exported ONNX model actually runs in onnxruntime standalone.
  4. The FastAPI inference service serves predictions from the deployed
     model, validates input shape, and hot-reloads when a new model is
     atomically published to the model store — with zero downtime.
  5. The predictive_maintenance task type also works end to end (not just
     the default anomaly_detection task).
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "services", "inference"))

from common.config import load_config
from pipelines.edge_retrain_pipeline import edge_retraining_loop_pipeline


def _run(cfg, simulate_drift, seed=2):
    run = edge_retraining_loop_pipeline(cfg, simulate_drift=simulate_drift, live_seed=seed)
    steps = run.steps
    drift_report = steps["detect_drift"].outputs["output"].load()
    metrics = steps["retrain_model"].outputs["metrics"].load()
    deployment_result = steps["deploy_to_edge"].outputs["output"].load()
    return drift_report, metrics, deployment_result


def test_no_drift_skips_retrain():
    cfg = load_config()
    drift_report, metrics, deployment_result = _run(cfg, simulate_drift=False, seed=101)
    assert drift_report["drift_detected"] is False
    assert metrics["skipped"] is True
    assert deployment_result["deployed"] is False
    print("PASS: no-drift run correctly skipped retraining")


def test_drift_triggers_retrain_and_deploy():
    cfg = load_config()
    drift_report, metrics, deployment_result = _run(cfg, simulate_drift=True, seed=202)
    assert drift_report["drift_detected"] is True
    assert len(drift_report["drifted_sensors"]) > 0
    assert metrics["skipped"] is False
    assert deployment_result["deployed"] is True
    assert os.path.exists(deployment_result["model_path"])
    assert os.path.exists(deployment_result["metadata_path"])
    print("PASS: drift run correctly retrained and deployed a new ONNX model")
    return deployment_result


def test_onnx_model_runs_standalone(deployment_result=None):
    import numpy as np
    import onnxruntime as ort

    deployment_result = deployment_result or test_drift_triggers_retrain_and_deploy()
    sess = ort.InferenceSession(deployment_result["model_path"], providers=["CPUExecutionProvider"])
    n_features = sess.get_inputs()[0].shape[1]
    x = np.random.rand(5, n_features).astype(np.float32)
    outputs = sess.run(None, {sess.get_inputs()[0].name: x})
    assert outputs[0].shape[0] == 5
    print(f"PASS: exported ONNX model runs standalone in onnxruntime (features={n_features})")


def test_inference_service_serves_and_hot_reloads():
    from fastapi.testclient import TestClient

    cfg = load_config()
    store_dir = os.path.abspath(cfg["deployment"]["model_store_dir"])
    os.environ["MODEL_STORE_DIR"] = store_dir

    # Reload app module fresh so it picks up the env var.
    if "app" in sys.modules:
        del sys.modules["app"]
    import app as inference_app  # noqa: E402

    with TestClient(inference_app.app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        first_model = r.json()["model_loaded"]

        r = client.get("/model/info")
        assert r.status_code == 200
        n_features = len(r.json()["features"])

        instances = [[1.0] * n_features, [2.0] * n_features]
        r = client.post("/predict", json={"instances": instances})
        assert r.status_code == 200
        assert "label" in r.json() or "variable" in r.json()

        r = client.post("/predict", json={"instances": [[1.0]]})
        assert r.status_code == 400
        print("PASS: inference service serves predictions and rejects bad input shape")

        # Trigger a brand new deployment while the service is "live" and
        # confirm the file watcher hot-reloads it with zero restarts.
        cfg2 = load_config()
        run = edge_retraining_loop_pipeline(cfg2, simulate_drift=True, live_seed=303)
        deployment_result = run.steps["deploy_to_edge"].outputs["output"].load()
        assert deployment_result["deployed"] is True

        for _ in range(20):
            time.sleep(0.5)
            r = client.get("/health")
            if r.json()["model_loaded"] != first_model:
                break
        else:
            raise AssertionError("Inference service did not hot-reload the new model in time")
        print(f"PASS: inference service hot-reloaded from {first_model} to {r.json()['model_loaded']}")


def test_predictive_maintenance_task():
    cfg = load_config()
    cfg = json_clone(cfg)
    cfg["model"]["task"] = "predictive_maintenance"
    drift_report, metrics, deployment_result = _run(cfg, simulate_drift=True, seed=404)
    assert metrics["skipped"] is False
    assert metrics["task"] == "predictive_maintenance"
    assert "test_mae" in metrics
    assert deployment_result["deployed"] is True
    print("PASS: predictive_maintenance task trains, converts, and deploys correctly")


def json_clone(d):
    return json.loads(json.dumps(d))


if __name__ == "__main__":
    test_no_drift_skips_retrain()
    deployment_result = test_drift_triggers_retrain_and_deploy()
    test_onnx_model_runs_standalone(deployment_result)
    test_inference_service_serves_and_hot_reloads()
    test_predictive_maintenance_task()
    print("\nALL TESTS PASSED")
