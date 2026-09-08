# Architecture Notes

## Two independent environments, on purpose

| | Training / orchestration side | Serving side |
|---|---|---|
| Runs | on demand or on a schedule | 24/7 |
| Dependencies | ZenML, scikit-learn, skl2onnx (`requirements.txt`) | FastAPI, onnxruntime only (`services/inference/requirements.txt`) |
| Hardware | any machine on the local network | can be a low-spec factory-floor mini-PC |
| Handoff artifact | `.onnx` file + `latest_metadata.json` | consumes only those two files |

This split is deliberate: the serving container should be as small and
boring as possible, since it's the thing that has to stay up. The training
side can be heavier because it runs briefly and infrequently.

## Why the pipeline always runs all 5 steps

Rather than short-circuiting the ZenML DAG when no drift is found (which
gets complicated with ZenML's static graph compilation), `retrain_model`,
`convert_to_onnx`, and `deploy_to_edge` all accept a `drift_report` /
`metrics` payload and no-op gracefully when retraining shouldn't happen
per `retrain.trigger` in the config. This means:

- Every run — even ones that don't retrain — is logged in ZenML's local
  run history, which is valuable for audits ("prove the model hasn't
  silently gone stale").
- The pipeline code stays simple: one linear DAG, no conditional branching
  to maintain.

## Why deployment is "just a file write"

`deploy_to_edge` does an atomic write (`tmp` file + `os.replace`) of the
`.onnx` model, then rewrites a plain-text `LATEST` pointer file. This
avoids ever serving a half-written file, without needing a database, a
message queue, or a model registry service. The inference container's
`watchdog` observer picks up the change and calls the same `load_latest()`
logic the container uses at startup — there is only one code path for
"load the current model," which keeps the hot-reload logic trustworthy.

Rollback is equally simple: overwrite `LATEST` with the filename of an
older `.onnx` still on disk (the pipeline never deletes old versions).

## Drift detection method choice

- **KS-test** (default): non-parametric, no binning required, works well
  with the sample sizes a typical polling window produces (hundreds of
  rows). Threshold is a p-value.
- **PSI**: bins the reference distribution into deciles and compares
  populations. This is the metric most familiar to model-risk / MLOps
  teams coming from a credit-risk or fraud background; threshold is the
  conventional 0.2 "significant shift" cutoff.

Both are computed **per sensor**, so an operator can see exactly which
sensor(s) drifted rather than a single fused score.

## Extending to more model types

`steps/retrain_model.py` and `steps/convert_to_onnx.py` are the only files
that know about scikit-learn specifically. To add a new `model.task`:

1. Add a branch in `retrain_model()` that trains your estimator and
   returns `(model, metrics)` with `metrics["features"]` set to the
   ordered list of input columns.
2. `convert_to_onnx()` already handles any scikit-learn-compatible
   estimator via `skl2onnx` — no changes usually needed there.
3. Add the new task's hyperparameters to `company_config.yaml` under
   `model.<your_task>`.

## Multi-machine / multi-line deployments

Each machine gets its own `company_config.yaml` (e.g.
`config/cnc-mill-07.yaml`, `config/press-03.yaml`) and its own
`model_store` directory + inference container/port. Run
`EDGE_MLOPS_CONFIG=config/press-03.yaml python run_pipeline.py` per
machine, or drive it from a small wrapper script that loops over a
directory of configs.
