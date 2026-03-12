"""
Universal MLOps Orchestrator - Main CLI Router
Delegates commands to specialized phase modules.
"""

import argparse
from prep import execute_prep
from run import execute_run
from tune import execute_tune

def main() -> None:
    cli_description = "Universal MLOps Orchestrator - End-to-End Pipeline Manager"
    cli_epilog = """
Examples:
  1. Prep Data & Environment:
     python orchestrator.py prep --exp exp_bs_roformer_mel
     python orchestrator.py prep --exp exp_bs_roformer_mel --steps process

  2. Run Single Experiment:
     python orchestrator.py run --exp exp_bs_roformer_mel

  3. Tune Hyperparameters (Multi-GPU Ray Tune):
     python orchestrator.py tune --config tune_bs_roformer_mel
"""

    parser = argparse.ArgumentParser(
        description=cli_description,
        epilog=cli_epilog,
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True, help="Workflow phase to execute")

    parser_prep = subparsers.add_parser("prep", help="Prepare the environment, clone repos, and process datasets.")
    parser_prep.add_argument("--exp", required=True, help="Experiment name from registry/experiments.yaml")
    parser_prep.add_argument(
        "--steps", 
        nargs="+", 
        choices=["clone", "install", "download", "process", "all"],
        default=["all"],
        help="Specific prep steps to execute. Pass multiple separated by space. (Default: all)"
    )

    parser_run = subparsers.add_parser("run", help="Execute a single training run with MLflow tracking.")
    parser_run.add_argument("--exp", required=True, help="Experiment name from registry/experiments.yaml")

    parser_tune = subparsers.add_parser("tune", help="Execute a multi-GPU hyperparameter sweep with Ray Tune.")
    parser_tune.add_argument("--config", required=True, help="Tuning profile from registry/tuning.yaml")

    args = parser.parse_args()

    if args.command == "prep":
        execute_prep(args.exp, args.steps)
    elif args.command == "run":
        execute_run(args.exp)
    elif args.command == "tune":
        execute_tune(args.config)

if __name__ == "__main__":
    main()