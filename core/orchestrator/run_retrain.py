"""
Retraining runner.

This script is intended for:
  - loading best hyperparameters from previous studies
  - retraining models on updated datasets
  - logging retraining runs to MLflow
"""

from __future__ import annotations
import os

from utils.mlflow_client import configure_mlflow, start_run, log_params
from registry_loader import load_models_config


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Retrain a model with selected configuration.")
    parser.add_argument("--model", required=True, help="Model key as defined in config/models.yaml")
    parser.add_argument("--config_override", help="Optional path to override config file")
    args = parser.parse_args()

    models_cfg = load_models_config(PROJECT_ROOT)
    model_def = models_cfg.get("models", {}).get(args.model)
    if not model_def:
        raise KeyError(f"Model '{args.model}' not found in config/models.yaml")

    model_dir = os.path.join(PROJECT_ROOT, model_def["target_dir"])
    config_path = args.config_override or os.path.join(model_dir, model_def["config_path"])

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    configure_mlflow(experiment_name=f"retrain_{args.model}")

    with start_run(run_name=f"retrain_{args.model}", tags={"model": args.model}):
        log_params({"model": args.model, "config_path": config_path})
        # TODO: call model-specific retraining command here.


if __name__ == "__main__":
    main()
