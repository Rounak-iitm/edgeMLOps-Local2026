"""Config loading + shared dataclasses.

Every step in the pipeline reads the same YAML file, so onboarding a new
customer / new machine is a config edit, never a code change.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = os.environ.get(
    "EDGE_MLOPS_CONFIG",
    os.path.join(os.path.dirname(__file__), "..", "config", "company_config.yaml"),
)


def load_config(path: str = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    with open(path, "r") as f:
        cfg = yaml.safe_load(f)
    _validate_config(cfg)
    return cfg


def _validate_config(cfg: dict[str, Any]) -> None:
    required_top = ["company", "sensors", "simulation", "drift_detection", "model", "retrain", "deployment"]
    missing = [k for k in required_top if k not in cfg]
    if missing:
        raise ValueError(f"company_config.yaml is missing required sections: {missing}")
    if not cfg["sensors"]:
        raise ValueError("company_config.yaml must define at least one sensor")
    for s in cfg["sensors"]:
        for key in ("name", "normal_mean", "normal_std"):
            if key not in s:
                raise ValueError(f"sensor entry {s} missing required field '{key}'")
    task = cfg["model"].get("task")
    if task not in ("anomaly_detection", "predictive_maintenance"):
        raise ValueError("model.task must be 'anomaly_detection' or 'predictive_maintenance'")
    if task == "predictive_maintenance":
        sensor_names = [s["name"] for s in cfg["sensors"]]
        if cfg["model"].get("target_sensor") not in sensor_names:
            raise ValueError("model.target_sensor must be one of the configured sensors")


def sensor_names(cfg: dict[str, Any]) -> list[str]:
    return [s["name"] for s in cfg["sensors"]]


def model_store_dir(cfg: dict[str, Any]) -> str:
    d = cfg["deployment"]["model_store_dir"]
    os.makedirs(d, exist_ok=True)
    return d
