# Production Operations Runbook

## Before go-live

1. Replace vendor/customer placeholders and install a valid signed license.
2. Use a customer-approved edge host with disk, RAM and CPU sized for the configured workload.
3. Connect exactly one approved data adapter and verify units, sampling rate, timestamps and machine identity.
4. Establish and archive a known-good reference dataset.
5. Validate model performance, drift thresholds and false-alarm behavior with the customer's engineering team.
6. Keep `/predict` reachable only from approved plant clients; use the customer's TLS reverse proxy when traffic leaves localhost.
7. Back up `model_store`, `config`, `.env`, and audit logs.
8. Do not connect model output directly to a safety instrumented system without a separate safety validation.

## Daily operations

- Check `/health`.
- Review container logs and `logs/audit.log`.
- Confirm current model version.
- Check disk capacity and backup status.

## Model change control

A model is deployable only after runtime validation. Keep the previous versions until the customer's retention policy allows deletion. Record who approved every production model.

## Rollback

Use `scripts/rollback.ps1 -ModelFile <validated-file>.onnx` on Windows, or write the selected filename atomically to `model_store/LATEST` and restart/reload the service on Linux. Verify `/health` and `/model/info` after rollback.

## Incident response

If predictions become unsafe or unreliable, isolate the prediction consumer, preserve logs/model artifacts, stop automatic retraining, restore the last validated model, and follow the customer's incident/change-control process.
