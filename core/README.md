# Multi-Model Experimentation Project

This repository is structured for:
- multiple models (vendored under `models/`)
- multiple datasets
- experiment tracking with MLflow
- hyperparameter tuning with Optuna
- reproducible orchestration via Python + PowerShell

## Quick start

1. Edit `config/models.yaml` with your real model repos.
2. Run the PowerShell bootstrap script to create structure and clone models.
3. Use `orchestrator/run_experiment.py` to launch experiments.
