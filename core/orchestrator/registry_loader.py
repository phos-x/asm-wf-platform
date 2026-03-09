"""
Registry loader for experiments, datasets, and tuning configs.
All registry files live under project/registry and project/config.
"""

from __future__ import annotations
import os
from typing import Any, Dict

import yaml


def _load_yaml(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Registry file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_experiments(root: str) -> Dict[str, Any]:
    path = os.path.join(root, "registry", "experiments.yaml")
    return _load_yaml(path)


def load_datasets(root: str) -> Dict[str, Any]:
    path = os.path.join(root, "registry", "datasets.yaml")
    return _load_yaml(path)


def load_tuning(root: str) -> Dict[str, Any]:
    path = os.path.join(root, "registry", "tuning.yaml")
    return _load_yaml(path)


def load_models_config(root: str) -> Dict[str, Any]:
    """
    Load central models config from config/models.yaml.
    """
    path = os.path.join(root, "config", "models.yaml")
    return _load_yaml(path)
