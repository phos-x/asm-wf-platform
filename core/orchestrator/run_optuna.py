"""
Optuna-based hyperparameter tuning runner.

This script:
  - reads tuning definitions from registry/tuning.yaml
  - links them to models from config/models.yaml
  - runs Optuna studies and logs results to MLflow
"""

from __future__ import annotations
import os
from typing import Any, Dict

import optuna

from utils.mlflow_client import configure_mlflow, start_run, log_params, log_metrics
from registry_loader import load_tuning, load_models_config


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def objective(trial: optuna.Trial, model_key: str, tuning_def: Dict[str, Any]) -> float:
    """
    Example objective function. You should adapt this to call the model's
    training script with trial-suggested hyperparameters and return a metric.
    """
    # Example hyperparameter suggestions
    lr = trial.suggest_float("lr", 1e-5, 1e-3, log=True)
    batch_size = trial.suggest_int("batch_size", 4, 64, log=True)

    # TODO: integrate with model training command and return validation metric.
    # For now, we just return a dummy value.
    return 0.0 - lr  # placeholder


def run_tuning(study_name: str, model_key: str) -> None:
    tuning_cfg = load_tuning(PROJECT_ROOT)
    models_cfg = load_models_config(PROJECT_ROOT)

    tuning_def = tuning_cfg.get("tuning", {}).get(model_key)
    if not tuning_def:
        raise KeyError(f"No tuning definition for model '{model_key}' in registry/tuning.yaml")

    if model_key not in models_cfg.get("models", {}):
        raise KeyError(f"Model '{model_key}' not found in config/models.yaml")

    n_trials = int(tuning_def.get("n_trials", 20))
    direction = tuning_def.get("direction", "minimize")

    configure_mlflow(experiment_name=f"tuning_{model_key}")

    study = optuna.create_study(study_name=study_name, direction=direction)

    def wrapped_objective(trial: optuna.Trial) -> float:
        with start_run(run_name=f"{study_name}_trial_{trial.number}", tags={"model": model_key}):
            params = {"model": model_key, "study": study_name}
            log_params(params)
            value = objective(trial, model_key, tuning_def)
            log_metrics({"objective": float(value)})
            return value

    study.optimize(wrapped_objective, n_trials=n_trials)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run Optuna tuning for a model.")
    parser.add_argument("--model", required=True, help="Model key as defined in config/models.yaml")
    parser.add_argument("--study", required=True, help="Study name")
    args = parser.parse_args()

    run_tuning(args.study, args.model)


if __name__ == "__main__":
    main()
