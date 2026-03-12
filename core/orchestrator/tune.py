"""Phase 3: Hyperparameter Tuning (Ray Tune)"""

import sys
import shlex
import subprocess
import re
import yaml
from typing import Dict, Any

import ray
from ray import train, tune
from ray.tune.search.optuna import OptunaSearch
from ray.tune.schedulers import ASHAScheduler

from common import PROJECT_ROOT, get_configs, _build_env, _expand_env_vars, _get

def _ray_trial_runner(
    config: Dict[str, Any], 
    _cmd_template: str, 
    _env: dict, 
    _cwd: str, 
    _target_metric: str, 
    _metric_regex: str
) -> None:
    """Ray Trainable that executes the black-box script and parses stdout."""
    metric_pattern = re.compile(_metric_regex, re.IGNORECASE)

    cmd_str = _cmd_template
    for param_name, param_val in config.items():
        cmd_str += f" --{param_name} {param_val}"
    
    cmd_list = shlex.split(cmd_str)

    process = subprocess.Popen(
        cmd_list,
        cwd=_cwd,
        env=_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    try:
        for line in iter(process.stdout.readline, ''):
            print(f"[Trial] {line}", end='')
            match = metric_pattern.search(line)
            if match:
                current_metric = float(match.group(1))
                train.report({_target_metric: current_metric})
        
        process.wait()
        if process.returncode != 0:
            raise RuntimeError(f"Trial failed with exit code {process.returncode}")
            
    except Exception as e:
        process.terminate()
        process.wait()
        raise e


def execute_tune(tune_name: str) -> None:
    """Phase 3: Tuning Router - Fully driven by tuning.yaml"""
    print(f"\n[PHASE: TUNE] Initiating hyperparameter sweep: {tune_name}")
    try:
        # 1. Load the registries
        tuning_yaml_path = PROJECT_ROOT / "core/registry/tuning.yaml"
        if not tuning_yaml_path.exists():
            raise FileNotFoundError(f"Tuning registry not found at {tuning_yaml_path}")
            
        with open(tuning_yaml_path, 'r') as f:
            tuning_registry = yaml.safe_load(f)
            
        tune_def = _get(tuning_registry, "tuning", tune_name, context="registry/tuning.yaml")
        base_exp = tune_def["base_experiment"]

        # 2. Resolve Base Environment
        exp_def, model_def, dataset_def, model_dir, dataset_path = get_configs(base_exp)
        env = _build_env(model_dir, dataset_path)
        base_cmd = exp_def.get("cmd") + " " + exp_def.get("extra_args", "")
        expanded_base_cmd = _expand_env_vars(base_cmd.strip(), env)

        # =================================================================
        # 3. YAML Configuration Extraction
        # =================================================================
        
        target_metric = tune_def["target_metric"]
        mode = tune_def["mode"]
        
        # Resources
        resources = tune_def.get("resources_per_trial", {"gpu": 1, "cpu": 2})

        # General Tune Settings
        tune_cfg = tune_def.get("tune_config", {})
        num_samples = tune_cfg.get("num_samples", 10)
        max_concurrent_trials = tune_cfg.get("max_concurrent_trials", 2)

        # ASHA (Early Stopping) Settings
        asha_cfg = tune_def.get("asha_config", {})
        max_t = asha_cfg.get("max_t", 100)
        grace_period = asha_cfg.get("grace_period", 5)
        reduction_factor = asha_cfg.get("reduction_factor", 4)

        # Storage Path
        storage_path_str = tune_def.get("storage_path", "ray_results")
        storage_path = str(PROJECT_ROOT / storage_path_str)

        # Build the dynamic Search Space
        search_space = {}
        for param, props in tune_def.get("search_space", {}).items():
            p_type = props.get("type")
            if p_type == "loguniform":
                search_space[param] = tune.loguniform(float(props["low"]), float(props["high"]))
            elif p_type == "uniform":
                search_space[param] = tune.uniform(float(props["low"]), float(props["high"]))
            elif p_type == "choice":
                search_space[param] = tune.choice(props["values"])
            elif p_type == "randint":
                search_space[param] = tune.randint(int(props["low"]), int(props["high"]))
            else:
                raise ValueError(f"Unknown search space type: {p_type} for parameter {param}")

        # Static parameters to pass to the Trial Runner
        static_params = {
            "_cmd_template": expanded_base_cmd,
            "_env": env,
            "_cwd": str(model_dir),
            "_target_metric": target_metric,
            "_metric_regex": tune_def["metric_regex"]
        }

        # =================================================================
        # 4. Ray Tune Execution
        # =================================================================
        
        ray.init(ignore_reinit_error=True)

        optuna_search = OptunaSearch(
            metric=target_metric,
            mode=mode
        )

        asha_scheduler = ASHAScheduler(
            metric=target_metric,
            mode=mode,
            max_t=max_t,
            grace_period=grace_period,
            reduction_factor=reduction_factor
        )

        trainable_with_params = tune.with_parameters(_ray_trial_runner, **static_params)

        tuner = tune.Tuner(
            tune.with_resources(trainable_with_params, resources=resources),
            tune_config=tune.TuneConfig(
                search_alg=optuna_search,
                scheduler=asha_scheduler,
                num_samples=num_samples,
                max_concurrent_trials=max_concurrent_trials
            ),
            param_space=search_space,
            run_config=train.RunConfig(
                name=tune_name,
                storage_path=storage_path
            )
        )

        print(f"  -> Base command: {expanded_base_cmd}")
        print(f"  -> Metric tracking: '{target_metric}' ({mode})")
        print(f"  -> Launching {num_samples} total trials ({max_concurrent_trials} concurrently)...")
        
        results = tuner.fit()
        best_result = results.get_best_result()

        # =================================================================
        # 5. Result Summary
        # =================================================================
        print("\n" + "="*50)
        print("🏆 OPTIMIZATION COMPLETE")
        print("="*50)
        print("Best Configuration Found:")
        for k, v in best_result.config.items():
            print(f"  --{k}: {v}")
        print(f"\nBest {target_metric}: {best_result.metrics.get(target_metric)}")
        print(f"Dashboard logs saved to: {storage_path}/{tune_name}")
        print("="*50 + "\n")

    except Exception as e:
        print(f"\n[ERROR] Tuning failed: {e}")
        sys.exit(1)