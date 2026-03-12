"""Phase 1: Environment and Dataset Preparation"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from common import PROJECT_ROOT, _safe_run, get_configs

def _prep_clone(model_def: Dict, model_dir: Path) -> None:
    source_repo = model_def.get("source_repo")
    branch = model_def.get("branch", "main")
    
    if not model_dir.exists() or not any(model_dir.iterdir()):
        if not source_repo:
            raise ValueError(f"Model dir '{model_dir}' is empty, but no 'source_repo' defined.")
        print(f"  [STEP: CLONE] Cloning {source_repo} (branch: {branch})...")
        model_dir.mkdir(parents=True, exist_ok=True)
        clone_cmd = ["git", "clone", "-b", branch, source_repo, str(model_dir)]
        if _safe_run(clone_cmd, cwd=PROJECT_ROOT, env=os.environ.copy()) != 0:
            raise RuntimeError(f"Failed to clone repository: {source_repo}")
    else:
        print(f"  [STEP: CLONE] Repo already exists at {model_dir}. Skipping.")

def _prep_install(model_def: Dict, model_dir: Path) -> None:
    req_file_name = model_def.get("requirements_file", "requirements.txt")
    req_path = model_dir / req_file_name
    flag_file = model_dir / ".orchestrator_reqs_installed"

    if req_path.exists():
        if not flag_file.exists():
            print(f"  [STEP: INSTALL] Installing requirements from {req_file_name}...")
            pip_cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_path)]
            if _safe_run(pip_cmd, cwd=model_dir, env=os.environ.copy()) != 0:
                raise RuntimeError(f"Failed to install requirements from {req_path}")
            flag_file.touch()
        else:
            print(f"  [STEP: INSTALL] Requirements flag found. Skipping pip install.")
    else:
        print(f"  [STEP: INSTALL] No {req_file_name} found. Skipping.")

def _prep_download(dataset_def: Dict, raw_path: Optional[Path]) -> None:
    source_url = dataset_def.get("source_url")
    if raw_path and source_url:
        if not raw_path.exists() or not any(raw_path.iterdir()):
            print(f"  [STEP: DOWNLOAD] Downloading from {source_url}...")
            raw_path.mkdir(parents=True, exist_ok=True)
            import urllib.request
            zip_target = raw_path / "dataset.zip"
            urllib.request.urlretrieve(source_url, str(zip_target))
            print(f"  [STEP: DOWNLOAD] Downloaded to {zip_target}")
        else:
            print(f"  [STEP: DOWNLOAD] Raw data already exists at {raw_path}. Skipping.")
    else:
        print("  [STEP: DOWNLOAD] No 'source_url' or 'raw_path' defined. Skipping.")

def _prep_process(dataset_def: Dict, raw_path: Optional[Path], dataset_path: Path) -> None:
    if dataset_path.exists() and any(dataset_path.iterdir()):
        print(f"  [STEP: PROCESS] Processed dataset exists at {dataset_path}. Skipping.")
        return

    extract_script_str = dataset_def.get("extract_script")
    if extract_script_str:
        extract_script = (PROJECT_ROOT / extract_script_str).resolve()
        if extract_script.exists():
            print(f"  [STEP: PROCESS] Running script: {extract_script.name}...")
            env = os.environ.copy()
            env["RAW_DATA_PATH"] = str(raw_path) if raw_path else ""
            env["PROCESSED_DATA_PATH"] = str(dataset_path)
            process_cmd = [sys.executable, str(extract_script)]
            if _safe_run(process_cmd, cwd=PROJECT_ROOT, env=env) != 0:
                raise RuntimeError("Dataset processing script failed.")
        else:
            print(f"  [WARNING] Extraction script not found: {extract_script}")
    else:
        print(f"  [WARNING] No extract_script defined for {dataset_path}.")

def execute_prep(exp_name: str, steps: List[str]) -> None:
    """Phase 1: Preparation Router"""
    print(f"\n[PHASE: PREP] Initiating preparation for experiment: {exp_name}")
    try:
        _, model_def, dataset_def, model_dir, dataset_path = get_configs(exp_name)
        raw_path_str = dataset_def.get("raw_path")
        raw_path = (PROJECT_ROOT / raw_path_str).resolve() if raw_path_str else None

        valid_steps = ["clone", "install", "download", "process"]
        steps_to_run = valid_steps if "all" in steps else [s for s in valid_steps if s in steps]

        print(f"  -> Execution plan: {steps_to_run}")

        if "clone" in steps_to_run: _prep_clone(model_def, model_dir)
        if "install" in steps_to_run: _prep_install(model_def, model_dir)
        if "download" in steps_to_run: _prep_download(dataset_def, raw_path)
        if "process" in steps_to_run: _prep_process(dataset_def, raw_path, dataset_path)

        print("\n[PREP] Requested preparation steps completed successfully.")
    except Exception as e:
        print(f"\n[ERROR] Preparation failed: {e}")
        sys.exit(1)