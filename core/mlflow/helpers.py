"""
Additional MLflow helpers.

Use this module for:
  - model registry interactions
  - artifact management
  - cross-run comparisons
"""

from __future__ import annotations
from typing import List

import mlflow


def list_runs(experiment_name: str) -> List[mlflow.entities.Run]:
    client = mlflow.tracking.MlflowClient()
    exp = client.get_experiment_by_name(experiment_name)
    if not exp:
        return []
    return client.search_runs([exp.experiment_id])
