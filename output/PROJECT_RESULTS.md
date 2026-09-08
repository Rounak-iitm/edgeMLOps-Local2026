# EdgeMLOps Enterprise Edge Results

## Project

EdgeMLOps Enterprise Edge 2.0.0 is an on-premise industrial MLOps platform for sensor monitoring, drift detection, local retraining, ONNX validation, model deployment, and edge inference.

## What Was Achieved

- Python 3.12 runtime configured on the D: drive.
- Training and inference dependencies installed.
- ZenML pipeline configured with artifacts stored on D:.
- Sensor simulation completed.
- Drift detection completed.
- Automatic retraining completed after detected drift.
- ONNX conversion completed.
- ONNX Runtime validation completed.
- Versioned model deployment completed.
- Atomic model replacement made reliable on Windows.
- FastAPI inference service started successfully.
- FastAPI model hot reload verified.
- ZenML dashboard started successfully.
- Project documentation updated.
- Project pushed to GitHub:
  `git@github.com:Rounak-iitm/edgeMLOps-Local2026.git`

## Verified Test Result

The complete end-to-end test suite passed:

```text
5 passed
```

The tests validated:

1. No-drift runs skip retraining.
2. Detected drift triggers retraining and deployment.
3. The exported ONNX model runs independently.
4. FastAPI serves predictions and hot-reloads new models.
5. Predictive-maintenance mode works.

## Live Services

### FastAPI inference service

```text
http://127.0.0.1:8080
```

Swagger documentation:

```text
http://127.0.0.1:8080/docs
```

Health endpoint:

```text
http://127.0.0.1:8080/health
```

### ZenML dashboard

```text
http://127.0.0.1:8237
```

Local demo login:

```text
Username: default
Password: leave blank
```

## Generated Model Results

Models are generated under:

```text
model_store/
```

Important runtime files include:

```text
edge_model_<version>.onnx
LATEST
latest_metadata.json
```

The `LATEST` file identifies the active model. Model binaries and runtime logs are intentionally excluded from Git.

## Runtime Locations

```text
D:\edgemlops-venv
D:\edgemlops-tmp
D:\edgemlops-zenml\local_stores
```

The D: drive is used because the system C: drive does not have sufficient free space.

## Demo Run Outcome

A degraded-machine demo run detected drift in four sensors, retrained the anomaly-detection model using 800 rows, converted it to ONNX, validated it with ONNX Runtime, deployed a new version, and hot-reloaded that version into FastAPI.

## Current Readiness

Ready for:

- Development
- Demonstration
- Technical evaluation
- Local end-to-end validation

Not yet production-approved until the following are completed:

- Docker Desktop and WSL 2 installation.
- Vendor-signed production license.
- Production API key and approved secret handling.
- TLS, firewall, and network configuration.
- Dependency and container vulnerability scans.
- SBOM generation and release signing.
- Customer-specific sensor and model acceptance.
- Backup, rollback, and commissioning drills.
- Legal review of commercial licensing and support terms.

## Important Boundary

This project is not a safety PLC, safety-instrumented system, MES/SCADA replacement, or universal remaining-useful-life guarantee. Production use requires customer engineering approval and separate safety validation where applicable.
