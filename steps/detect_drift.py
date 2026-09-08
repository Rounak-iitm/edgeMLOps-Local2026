"""Step 2 — Detect data drift between the reference window and the live window.

Two interchangeable, dependency-light methods are supported so the product
works whether the customer prefers a statistical test (KS) or the industry-
standard PSI metric used in a lot of MLOps / model-risk tooling:

  * Kolmogorov-Smirnov two-sample test (scipy) — good default, no binning.
  * Population Stability Index (PSI) — the metric risk/credit and MLOps
    teams already know; PSI > 0.2 is the conventional "significant shift"
    cutoff.

Both are computed per-sensor so the report tells an operator *which*
sensor(s) drifted, not just a single opaque score.
"""
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from zenml import step


def _psi(reference: np.ndarray, live: np.ndarray, bins: int = 10) -> float:
    quantiles = np.linspace(0, 100, bins + 1)
    edges = np.unique(np.percentile(reference, quantiles))
    if len(edges) < 3:
        return 0.0
    ref_counts, _ = np.histogram(reference, bins=edges)
    live_counts, _ = np.histogram(live, bins=edges)
    ref_pct = np.clip(ref_counts / max(len(reference), 1), 1e-6, None)
    live_pct = np.clip(live_counts / max(len(live), 1), 1e-6, None)
    return float(np.sum((live_pct - ref_pct) * np.log(live_pct / ref_pct)))


@step(enable_cache=False)
def detect_drift(
    reference_df: pd.DataFrame,
    live_df: pd.DataFrame,
    cfg: dict,
) -> Dict[str, Any]:
    method = cfg["drift_detection"]["method"]
    sensor_cols = [s["name"] for s in cfg["sensors"]]

    per_sensor: Dict[str, Any] = {}
    drifted_sensors: List[str] = []

    for col in sensor_cols:
        ref_vals = reference_df[col].to_numpy()
        live_vals = live_df[col].to_numpy()

        if method == "psi":
            score = _psi(ref_vals, live_vals)
            is_drift = score > cfg["drift_detection"]["psi_threshold"]
            per_sensor[col] = {"method": "psi", "score": round(score, 4), "drift": is_drift}
        else:  # ks
            stat, p_value = ks_2samp(ref_vals, live_vals)
            is_drift = p_value < cfg["drift_detection"]["ks_p_value_threshold"]
            per_sensor[col] = {
                "method": "ks",
                "statistic": round(float(stat), 4),
                "p_value": round(float(p_value), 6),
                "drift": is_drift,
            }

        if is_drift:
            drifted_sensors.append(col)

    drift_detected = len(drifted_sensors) >= cfg["drift_detection"]["min_drifted_sensors_to_trigger"]

    report = {
        "drift_detected": drift_detected,
        "drifted_sensors": drifted_sensors,
        "per_sensor": per_sensor,
        "reference_rows": len(reference_df),
        "live_rows": len(live_df),
    }
    return report
