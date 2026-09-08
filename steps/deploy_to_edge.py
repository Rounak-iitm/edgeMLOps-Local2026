"""Step 5 — "Deploy": atomically drop the new ONNX model into the local
model store that the Docker inference container has bind-mounted.

There is deliberately no network call, no registry push, and no cloud
dependency here — deployment on this product means "write a file to disk
inside the plant network," which is exactly what makes it work with zero
internet connectivity. The inference container either:

  1. auto-detects the new file via a filesystem watcher (default), or
  2. is pinged on cfg.deployment.inference_service.reload_endpoint if the
     customer's network allows container-to-container HTTP calls.
"""
import json
import os
import time
import uuid
from pathlib import Path

import onnxruntime as ort
from typing import Any, Dict

from zenml import step

from common.config import model_store_dir


def _atomic_replace(source: str, destination: str) -> None:
    for attempt in range(5):
        try:
            os.replace(source, destination)
            return
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.05)


@step(enable_cache=False)
def deploy_to_edge(
    onnx_bytes: bytes,
    metrics: dict,
    drift_report: dict,
    cfg: dict,
) -> Dict[str, Any]:
    if metrics.get("skipped") or not onnx_bytes:
        return {
            "deployed": False,
            "reason": metrics.get("reason", "retrain was skipped"),
        }

    store_dir = model_store_dir(cfg)
    prefix = cfg["deployment"]["onnx_filename_prefix"]
    version = time.strftime("%Y%m%d-%H%M%S")

    model_filename = f"{prefix}_{version}.onnx"
    model_path = os.path.join(store_dir, model_filename)

    # Atomic write: write to a temp file then rename, so the inference
    # container's file watcher never sees a half-written .onnx file.
    tmp_path = f"{model_path}.{uuid.uuid4().hex}.tmp"
    with open(tmp_path, "wb") as f:
        f.write(onnx_bytes)
    _atomic_replace(tmp_path, model_path)
    # Validate the artifact before publishing the pointer.
    try:
        ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
    except Exception:
        os.remove(model_path)
        raise ValueError("Generated ONNX model failed runtime validation; deployment aborted")

    metadata = {
        "version": version,
        "model_filename": model_filename,
        "company": cfg["company"],
        "task": metrics["task"],
        "features": metrics["features"],
        "metrics": metrics,
        "drift_report": {
            "drift_detected": drift_report["drift_detected"],
            "drifted_sensors": drift_report["drifted_sensors"],
        },
        "deployed_at": version,
    }
    metadata_path = os.path.join(store_dir, "latest_metadata.json")
    tmp_meta = f"{metadata_path}.{uuid.uuid4().hex}.tmp"
    with open(tmp_meta, "w") as f:
        json.dump(metadata, f, indent=2)
    _atomic_replace(tmp_meta, metadata_path)

    # "LATEST" pointer file — the inference service always loads whatever
    # filename this points to. This is what makes rollback trivial: just
    # rewrite this one file to an older *.onnx that's still on disk.
    pointer_path = os.path.join(store_dir, "LATEST")
    tmp_pointer = f"{pointer_path}.{uuid.uuid4().hex}.tmp"
    with open(tmp_pointer, "w") as f:
        f.write(model_filename)
    _atomic_replace(tmp_pointer, pointer_path)

    retain = int(cfg["deployment"].get("retain_versions", 10))
    versions = sorted(Path(store_dir).glob(f"{prefix}_*.onnx"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in versions[retain:]:
        try: old.unlink()
        except OSError: pass

    return {
        "deployed": True,
        "model_path": model_path,
        "metadata_path": metadata_path,
        "pointer_path": pointer_path,
        "version": version,
    }
