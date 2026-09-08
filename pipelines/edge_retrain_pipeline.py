"""The Zero-Cloud Edge Retraining Loop — one ZenML pipeline, fully local.

    Step 1  simulate_reference_batch / simulate_live_batch
              -> live sensor logs from the factory machine
    Step 2  detect_drift
              -> is the machine's data distribution drifting?
    Step 3  retrain_model
              -> local scikit-learn retrain, triggered by the drift result
    Step 4  convert_to_onnx
              -> portable model artifact for the edge runtime
    Step 5  deploy_to_edge
              -> atomically publish into the Docker container's model volume

Everything — orchestration metadata, artifacts, the SQLite run history — stays
on the machine that runs this script. No cloud service is contacted.
"""
from __future__ import annotations

from zenml import pipeline

from steps.convert_to_onnx import convert_to_onnx
from steps.deploy_to_edge import deploy_to_edge
from steps.detect_drift import detect_drift
from steps.retrain_model import retrain_model
from steps.simulate_sensor_logs import simulate_live_batch, simulate_reference_batch


@pipeline(enable_cache=False)
def edge_retraining_loop_pipeline(cfg: dict, simulate_drift: bool = False, live_seed: int = 2):
    reference_df = simulate_reference_batch(cfg)
    live_df = simulate_live_batch(cfg, drift=simulate_drift, seed=live_seed)

    drift_report = detect_drift(reference_df, live_df, cfg)
    model, metrics = retrain_model(reference_df, live_df, drift_report, cfg)
    onnx_bytes = convert_to_onnx(model, metrics, cfg)
    deployment_result = deploy_to_edge(onnx_bytes, metrics, drift_report, cfg)

    return deployment_result
