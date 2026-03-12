"""Shared utilities for the orchestrator modules."""

import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, Mapping, List

from registry_loader import load_experiments, load_models_config, load_datasets

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def _get(mapping: Mapping[str, Any], *keys: str, context: str) -> Any:
    current = mapping
    for key in keys:
        if key not in current:
            path = " -> ".join(keys)
            raise KeyError(f"Missing configuration key '{path}' in {context}")
        current = current[key]
    return current

def _sanitize_path(raw: Any) -> str:
    if isinstance(raw, list):
        if len(raw) != 1:
            raise ValueError(f"Dataset path list must contain exactly one element: {raw}")
        raw = raw[0]
    if not isinstance(raw, str):
        raise TypeError(f"Dataset path must be a string, got: {type(raw)}")
    cleaned = raw.strip()
    if cleaned.startswith("[") and cleaned.endswith("]"):
        cleaned = cleaned[1:-1].strip()
    return cleaned

def _build_env(model_dir: Path, dataset_path: Path) -> Dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{str(model_dir)}{os.pathsep}{existing}" if existing else str(model_dir)
    env["DATASET_DIR"] = str(dataset_path)
    return env

def _expand_env_vars(text: str, env: Dict[str, str]) -> str:
    def replace(match: re.Match) -> str:
        var_name = match.group(1) or match.group(2)
        return env.get(var_name, match.group(0))
    return re.sub(r'\$(\w+)|\$\{(\w+)\}', replace, text)

def _safe_run(cmd_list: List[str], cwd: Path, env: Dict[str, str]) -> int:
    try:
        result = subprocess.run(cmd_list, cwd=str(cwd), env=env, check=False)
        return result.returncode
    except FileNotFoundError:
        print(f"[ERROR] Executable not found. Command was: {' '.join(cmd_list)}")
        return 127

def get_configs(exp_name: str) -> tuple[Dict, Dict, Dict, Path, Path]:
    """Loads registries and resolves the core paths needed for an experiment."""
    experiments = load_experiments(str(PROJECT_ROOT))
    models_cfg = load_models_config(str(PROJECT_ROOT))
    datasets_cfg = load_datasets(str(PROJECT_ROOT))

    exp_def = _get(experiments, "experiments", exp_name, context="registry/experiments.yaml")
    model_key = exp_def["model"]
    dataset_key = exp_def["dataset"]

    model_def = _get(models_cfg, "models", model_key, context="config/models.yaml")
    dataset_def = _get(datasets_cfg, "datasets", dataset_key, context="registry/datasets.yaml")

    model_dir = (PROJECT_ROOT / model_def["target_dir"]).resolve()
    dataset_path_str = _sanitize_path(dataset_def["processed_path"])
    dataset_path = (PROJECT_ROOT / dataset_path_str).resolve()

    return exp_def, model_def, dataset_def, model_dir, dataset_path