"""
MLflow client utilities.

This module centralizes MLflow configuration and logging helpers so that
all models and experiments use a consistent tracking setup.
"""

from __future__ import annotations
import os
from typing import Dict, Any, Optional

import mlflow


def get_tracking_uri() -> str:
    """
    Resolve MLflow tracking URI from environment or local file.
    Priority:
      1. MLFLOW_TRACKING_URI env var
      2. mlflow/tracking_uri.txt
      3. default local ./mlruns
    """
    env_uri = os.getenv("MLFLOW_TRACKING_URI")
    if env_uri:
        return env_uri

    local_file = os.path.join(os.path.dirname(__file__), "..", "..", "mlflow", "tracking_uri.txt")
    local_file = os.path.abspath(local_file)
    if os.path.exists(local_file):
        with open(local_file, "r", encoding="utf-8") as f:
            uri = f.read().strip()
            if uri:
                return uri

    return "file:./mlruns"


def configure_mlflow(experiment_name: str) -> None:
    """
    Configure MLflow with a tracking URI and experiment name.
    Creates the experiment if it does not exist.
    """
    uri = get_tracking_uri()
    mlflow.set_tracking_uri(uri)
    mlflow.set_experiment(experiment_name)


def start_run(run_name: Optional[str] = None, tags: Optional[Dict[str, str]] = None):
    """
    Context manager wrapper for mlflow.start_run with optional tags.
    """
    return mlflow.start_run(run_name=run_name, tags=tags)


def log_params(params: Dict[str, Any]) -> None:
    mlflow.log_params(params)


def log_metrics(metrics: Dict[str, float], step: Optional[int] = None) -> None:
    mlflow.log_metrics(metrics, step=step)


def log_artifact(path: str, artifact_path: Optional[str] = None) -> None:
    mlflow.log_artifact(path, artifact_path=artifact_path)
