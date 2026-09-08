"""Step 1 — Simulate live sensor logs from a factory machine.

Swap this one file for a real OPC-UA / Modbus / MQTT poller in production;
every other step only depends on the pandas DataFrame shape (one column per
configured sensor), so nothing downstream needs to change.
"""
import numpy as np
import pandas as pd
from zenml import step


def _generate_batch(cfg: dict, n_rows: int, drift: bool, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    data = {}
    for s in cfg["sensors"]:
        mean = s["normal_mean"]
        std = s["normal_std"]
        if drift:
            # Simulate real machinery degradation: mean shifts and the sensor
            # gets noisier (e.g. a bearing wearing out raises both vibration
            # and its variance).
            mean = mean * 1.35
            std = std * 1.8
        data[s["name"]] = rng.normal(loc=mean, scale=std, size=n_rows)
    df = pd.DataFrame(data)
    df.insert(0, "timestamp", pd.date_range(end=pd.Timestamp.now(), periods=n_rows, freq="s"))
    df.insert(1, "machine_id", cfg["company"]["machine_id"])
    return df


@step(enable_cache=False)
def simulate_reference_batch(cfg: dict) -> pd.DataFrame:
    """Generates the 'known-good' baseline window used as the drift reference."""
    n = cfg["simulation"]["reference_batch_size"]
    return _generate_batch(cfg, n, drift=False, seed=1)


@step(enable_cache=False)
def simulate_live_batch(cfg: dict, drift: bool = False, seed: int = 2) -> pd.DataFrame:
    """Generates one polling window of 'live' sensor data.

    drift=True simulates a machine that has started to degrade, so the demo
    can show the pipeline detecting it and retraining automatically.
    """
    n = cfg["simulation"]["live_batch_size"]
    return _generate_batch(cfg, n, drift=drift, seed=seed)
