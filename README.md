# EdgeMLOps Local — Enterprise Edge 2.0.0

**On-premise MLOps for industrial machine-learning workloads.**

EdgeMLOps Local keeps sensor data, model training, model validation and inference inside the customer's environment. It is designed for factories that require local processing, restricted connectivity or controlled data residency.

## What the customer buys

- Local drift monitoring (KS / PSI)
- Automated retraining policies
- ONNX runtime validation before publication
- Atomic model deployment and version retention
- Low-footprint FastAPI + ONNX inference runtime
- API-key authentication
- Audit logging
- Backup and rollback tooling
- Docker-based repeatable deployment
- CSV-drop connector included
- Optional MQTT and OPC-UA connector adapters
- Windows and Linux installation
- Offline-capable runtime after dependencies/images are staged

## Supported use cases

- Equipment anomaly detection
- Condition monitoring
- Predictive-maintenance baselines
- Sensor-distribution monitoring
- Local model refresh without cloud model registries

## Production boundary

This is a deployable industrial ML product, but it is not a safety PLC, safety-instrumented system, MES/SCADA replacement, or a universal remaining-useful-life guarantee. The customer's engineering team must approve sensor mappings, thresholds, model performance, network controls and fail-safe behavior before production use.

## Production installation

### Windows

Run PowerShell as Administrator:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\installer\install.ps1 -LicenseFile .\license.json
```

Evaluation only:

```powershell
.\installer\install.ps1 -Demo
```

### Linux

```bash
sudo ./installer/install.sh /path/to/license.json
```

The production installer requires a vendor-signed license. The evaluation installer deliberately uses demo mode and must not be used as a production entitlement.

## Local validation

The training and end-to-end test workflow requires Python 3.12. Keep the virtual environment and pip temporary files on a drive with sufficient free space; the example below uses `E:` on Windows:

```powershell
New-Item -ItemType Directory -Force E:\edgemlops-tmp | Out-Null
$env:TEMP = "E:\edgemlops-tmp"
$env:TMP = "E:\edgemlops-tmp"
$env:ZENML_LOCAL_STORES_PATH = "E:\\edgemlops-zenml\\local_stores"
py -3.12 -m venv E:\edgemlops-venv
E:\edgemlops-venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

$env:EDGE_LICENSE_MODE = "demo"
Set-Location "D:\OUR PROJECT\EdgeMLOps-Enterprise-Edge-2.0.0"
python -m pytest tests\test_end_to_end.py -v
```

The test suite validates drift detection, retraining, ONNX export/runtime validation, inference, hot reload and predictive-maintenance mode. Demo mode is for evaluation only.

## Docker on Windows

Docker Desktop requires WSL 2 and free space on the system drive even when the project and Docker disk image are stored on another drive. On Windows Home, install WSL 2 first and configure Docker Desktop's disk image location under **Settings > Resources > Advanced**. A production container also requires a vendor-signed license and an API key.

## Customer data flow

```text
PLC / SCADA / MQTT / OPC-UA / CSV
              |
              v
       Sensor Adapter
              |
              v
       Drift Detection
          KS / PSI
              |
          drift?
        /          \
      no            yes
      |               |
      |        Local Retraining
      |               |
      |          ONNX Validation
      |               |
      |        Versioned Model Store
      |               |
      +-------+-------+
              |
              v
       Edge Inference API
        FastAPI + ONNX RT
              |
              v
       MES / Apps / Analytics
```

## Operations

Use `edgemlopsctl.py` for start/stop/restart/status/logs/update, and the scripts under `scripts/` for Windows backup and model rollback.

See:
- `INSTALL.md` — installation and commissioning
- `docs/PRODUCTION-OPERATIONS.md` — runbook
- `docs/SECURITY.md` — security baseline
- `docs/SALES-AND-SCOPE.md` — commercial scope
- `product/VENDOR-RELEASE-CHECKLIST.md` — vendor release gate
