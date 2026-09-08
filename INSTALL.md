# Customer Installation & Commissioning

## Prerequisites

Windows 11/Windows Server or a supported Linux host, Docker Engine/Desktop, CPU sized for the customer's workload, and an approved network/security configuration.

Python 3.12 is required only on hosts that run the training/bootstrap pipeline. The always-on inference service runs in Docker.

On Windows, Docker Desktop also requires WSL 2 and several gigabytes of free space on `C:` for system components. The Docker disk image and this project may be placed on another drive, but a nearly full system drive will prevent installation. Run the WSL and Docker installation steps from an elevated PowerShell session.

For local training and validation, use a Python 3.12 virtual environment on a drive with free space:

```powershell
New-Item -ItemType Directory -Force E:\edgemlops-tmp | Out-Null
$env:TEMP = "E:\edgemlops-tmp"
$env:TMP = "E:\edgemlops-tmp"
$env:ZENML_LOCAL_STORES_PATH = "E:\\edgemlops-zenml\\local_stores"
py -3.12 -m venv E:\edgemlops-venv
E:\edgemlops-venv\Scripts\Activate.ps1
```

## Production installation

A production license is required. The vendor supplies a signed `license.json` for the customer/site.

### Windows

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\installer\install.ps1 -LicenseFile .\license.json
```

### Linux

```bash
sudo ./installer/install.sh /path/to/license.json
```

The service binds to `127.0.0.1` by default. If LAN access is required, change `EDGE_BIND` only after the customer's firewall and TLS design has been approved.

## Evaluation

```powershell
.\installer\install.ps1 -Demo
```

Demo mode is intentionally not a commercial entitlement.

### Local end-to-end validation

From the repository root, after installing the Python requirements and test dependencies:

```powershell
$env:EDGE_LICENSE_MODE = "demo"
python -m pytest tests\test_end_to_end.py -v
```

The expected result is five passing tests. Warnings from ZenML, Pydantic and FastAPI are dependency deprecations and do not indicate a failed test; investigate any `FAILED` result or traceback separately.

## Commissioning

1. Configure company/site/machine and sensor definitions.
2. Replace the simulator with an approved data connector.
3. Establish the known-good reference period.
4. Validate units, sampling, timestamps and missing-value behavior.
5. Validate drift thresholds.
6. Validate model accuracy and false alarms.
7. Test model rollback.
8. Verify backup restoration.
9. Verify API authentication and network isolation.
10. Obtain customer engineering acceptance before production use.
