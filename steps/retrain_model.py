"""Step 3 — Retrain a scikit-learn model locally, entirely on-prem.

Supports two task types out of the box (chosen in company_config.yaml):

  * anomaly_detection      -> IsolationForest flags abnormal machine states
                               using every configured sensor as a feature.
  * predictive_maintenance -> RandomForestRegressor predicts one "target"
                               sensor from the others, so a growing residual
                               error becomes an early-warning signal.

Both branches train on reference + live data combined, i.e. the model
"catches up" to the new normal the moment drift is confirmed — this is the
actual retraining loop, no cloud round-trip involved.
"""
from typing import Any, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from typing_extensions import Annotated
from zenml import step


def _should_retrain(drift_report: dict, cfg: dict) -> tuple[bool, str]:
    policy = cfg["retrain"]["trigger"]
    if policy == "always":
        return True, "trigger policy is 'always'"
    if policy == "manual":
        return False, "trigger policy is 'manual' (no automatic retrain)"
    # default: "on_drift"
    if drift_report["drift_detected"]:
        return True, f"drift detected on sensors: {drift_report['drifted_sensors']}"
    return False, "no drift detected; existing model left in place"


@step(enable_cache=False)
def retrain_model(
    reference_df: pd.DataFrame,
    live_df: pd.DataFrame,
    drift_report: dict,
    cfg: dict,
) -> Tuple[Annotated[object, "model"], Annotated[dict, "metrics"]]:
    should_retrain, reason = _should_retrain(drift_report, cfg)
    if not should_retrain:
        return None, {"skipped": True, "reason": reason}

    sensor_cols = [s["name"] for s in cfg["sensors"]]
    combined = pd.concat([reference_df, live_df], ignore_index=True)

    if len(combined) < cfg["retrain"]["min_samples_required"]:
        raise ValueError(
            f"Not enough samples to retrain: got {len(combined)}, "
            f"need >= {cfg['retrain']['min_samples_required']}"
        )

    task = cfg["model"]["task"]

    if task == "anomaly_detection":
        X = combined[sensor_cols].to_numpy()
        params = cfg["model"]["isolation_forest"]
        model = IsolationForest(
            n_estimators=params["n_estimators"],
            contamination=params["contamination"],
            random_state=params["random_state"],
        )
        model.fit(X)
        preds = model.predict(X)  # -1 = anomaly, 1 = normal
        anomaly_rate = float(np.mean(preds == -1))
        metrics = {
            "skipped": False,
            "task": task,
            "n_train_rows": len(combined),
            "anomaly_rate_on_train": round(anomaly_rate, 4),
            "features": sensor_cols,
        }
        return model, metrics

    else:  # predictive_maintenance
        target = cfg["model"]["target_sensor"]
        feature_cols = [c for c in sensor_cols if c != target]
        X = combined[feature_cols].to_numpy()
        y = combined[target].to_numpy()

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        params = cfg["model"]["random_forest"]
        model = RandomForestRegressor(
            n_estimators=params["n_estimators"],
            max_depth=params["max_depth"],
            random_state=params["random_state"],
        )
        model.fit(X_train, y_train)
        mae = float(mean_absolute_error(y_test, model.predict(X_test)))
        metrics = {
            "skipped": False,
            "task": task,
            "n_train_rows": len(combined),
            "target_sensor": target,
            "features": feature_cols,
            "test_mae": round(mae, 4),
        }
        return model, metrics
