"""
Experiment runner.

This script:
  - reads experiment definitions from registry/experiments.yaml
  - resolves model + dataset configuration
  - invokes the appropriate model training script
  - logs to MLflow using a consistent interface
"""

from __future__ import annotations
import os
import subprocess
from typing import Dict, Any

from utils.mlflow_client import configure_mlflow, start_run, log_params, log_metrics
from registry_loader import load_experiments, load_models_config, load_datasets


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _safe_run(cmd: str, cwd: str | None = None) -> int:
    """
    Run a shell command safely, capturing exit code.
    Avoids shell=True where possible for security.
    """
    parts = cmd.split()
    result = subprocess.run(parts, cwd=cwd, check=False)
    return result.returncode


def run_single_experiment(exp_name: str) -> None:
    experiments = load_experiments(PROJECT_ROOT)
    models_cfg = load_models_config(PROJECT_ROOT)
    datasets_cfg = load_datasets(PROJECT_ROOT)

    exp_def = experiments.get("experiments", {}).get(exp_name)
    if not exp_def:
        raise KeyError(f"Experiment '{exp_name}' not found in registry/experiments.yaml")

    model_key = exp_def["model"]
    dataset_key = exp_def["dataset"]

    model_def = models_cfg.get("models", {}).get(model_key)
    if not model_def:
        raise KeyError(f"Model '{model_key}' not found in config/models.yaml")

    dataset_def = datasets_cfg.get("datasets", {}).get(dataset_key)
    if not dataset_def:
        raise KeyError(f"Dataset '{dataset_key}' not found in registry/datasets.yaml")

    model_dir = os.path.join(PROJECT_ROOT, model_def["target_dir"])
    train_script = os.path.join(model_dir, model_def["train_script"])
    config_path = os.path.join(model_dir, model_def["config_path"])

    if not os.path.exists(train_script):
        raise FileNotFoundError(f"Train script not found: {train_script}")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    experiment_name = exp_def.get("mlflow_experiment", exp_name)
    configure_mlflow(experiment_name)

    params: Dict[str, Any] = {
        "experiment": exp_name,
        "model": model_key,
        "dataset": dataset_key,
        "config_path": config_path,
    }
    params.update(exp_def.get("params", {}))

    with start_run(run_name=exp_name, tags={"model": model_key, "dataset": dataset_key}):
        log_params(params)

        cmd = f"python {train_script} --config {config_path}"
        if "extra_args" in exp_def:
            cmd += f" {exp_def['extra_args']}"

        exit_code = _safe_run(cmd, cwd=model_dir)
        log_metrics({"exit_code": float(exit_code)})

        if exit_code != 0:
            raise RuntimeError(f"Training command failed with exit code {exit_code}")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run a registered experiment.")
    parser.add_argument("--name", required=True, help="Experiment name as defined in registry/experiments.yaml")
    args = parser.parse_args()

    run_single_experiment(args.name)


if __name__ == "__main__":
    main()
