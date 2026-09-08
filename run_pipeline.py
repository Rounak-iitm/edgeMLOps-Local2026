"""CLI entry point — run one iteration of the edge retraining loop.

Usage:
    python run_pipeline.py                 # normal machine, no drift
    python run_pipeline.py --simulate-drift  # simulate machine degradation
"""
from __future__ import annotations

import argparse
import json
import sys

from common.config import load_config
from pipelines.edge_retrain_pipeline import edge_retraining_loop_pipeline


def main():
    parser = argparse.ArgumentParser(description="Run the Zero-Cloud Edge Retraining Loop")
    parser.add_argument("--config", default=None, help="Path to company_config.yaml")
    parser.add_argument("--simulate-drift", action="store_true", help="Simulate machine degradation in the live batch")
    parser.add_argument("--seed", type=int, default=2, help="Random seed for the live batch")
    args = parser.parse_args()

    cfg = load_config(args.config) if args.config else load_config()

    print(f"=== Zero-Cloud Edge Retraining Loop ===")
    print(f"Company : {cfg['company']['name']} / {cfg['company']['site']}")
    print(f"Machine : {cfg['company']['machine_id']}")
    print(f"Task    : {cfg['model']['task']}")
    print(f"Simulating {'DEGRADED' if args.simulate_drift else 'NORMAL'} machine data...\n")

    run = edge_retraining_loop_pipeline(cfg, simulate_drift=args.simulate_drift, live_seed=args.seed)

    # Pull step outputs from the completed run for a human-readable summary.
    steps = run.steps
    drift_report = steps["detect_drift"].outputs["output"].load()
    metrics = steps["retrain_model"].outputs["metrics"].load()
    deployment_result = steps["deploy_to_edge"].outputs["output"].load()

    print("--- Drift report ---")
    print(json.dumps(drift_report, indent=2, default=str))
    print("\n--- Retrain result ---")
    print(json.dumps(metrics, indent=2, default=str))
    print("\n--- Deployment result ---")
    print(json.dumps(deployment_result, indent=2, default=str))

    if deployment_result.get("deployed"):
        print(f"\n✅ New model deployed: {deployment_result['model_path']}")
    else:
        print(f"\n➖ No deployment this run: {deployment_result.get('reason')}")


if __name__ == "__main__":
    sys.exit(main())
