"""Phase 2: Execution and Tracking"""

import sys
import shlex
from common import PROJECT_ROOT, get_configs, _build_env, _expand_env_vars, _safe_run
from utils.mlflow_client import configure_mlflow, start_run, log_params, log_metrics

def execute_run(exp_name: str) -> None:
    """Phase 2: Execution Router"""
    print(f"\n[PHASE: RUN] Initiating training for experiment: {exp_name}")
    try:
        exp_def, model_def, dataset_def, model_dir, dataset_path = get_configs(exp_name)
        
        model_key = exp_def["model"]
        dataset_key = exp_def["dataset"]
        train_script = (model_dir / model_def["train_script"]).resolve()

        if not train_script.is_file():
            raise FileNotFoundError(f"Train script not found: {train_script}")
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset path not found: {dataset_path}. Did you run 'prep' first?")

        env = _build_env(model_dir, dataset_path)

        base_cmd = exp_def.get("cmd")
        if not base_cmd:
            raise KeyError(f"Experiment '{exp_name}' must define a 'cmd' field.")
        
        extra = exp_def.get("extra_args", "")
        raw_cmd_string = f"{base_cmd} {extra}".strip()

        expanded_cmd_string = _expand_env_vars(raw_cmd_string, env)
        cmd_list = shlex.split(expanded_cmd_string)

        experiment_name = exp_def.get("mlflow_experiment", exp_name)
        configure_mlflow(experiment_name)

        params = {
            "experiment": exp_name,
            "model": model_key,
            "dataset": dataset_key,
            "dataset_path": str(dataset_path),
            "executed_cmd": " ".join(cmd_list),
        }

        print(f"  -> Executing: {' '.join(cmd_list)}")
        
        with start_run(run_name=exp_name, tags={"model": model_key, "dataset": dataset_key}):
            log_params(params)
            exit_code = _safe_run(cmd_list, cwd=model_dir, env=env)
            log_metrics({"exit_code": float(exit_code)})

            if exit_code != 0:
                raise RuntimeError(f"Training failed with exit code {exit_code}")

        print(f"[RUN] Successfully completed experiment '{exp_name}'.\n")

    except Exception as e:
        print(f"\n[ERROR] Execution failed: {e}")
        sys.exit(1)