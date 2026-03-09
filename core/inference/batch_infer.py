"""
Batch inference script.

Intended to:
  - load a trained model
  - run inference on a dataset
  - write outputs + metrics
"""

from __future__ import annotations
import os
from typing import Any

from orchestrator.registry_loader import load_models_config


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Batch inference runner.")
    parser.add_argument("--model", required=True, help="Model key as defined in config/models.yaml")
    parser.add_argument("--input_dir", required=True)
    parser.add_argument("--output_dir", required=True)
    args = parser.parse_args()

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    models_cfg = load_models_config(project_root)
    model_def: dict[str, Any] = models_cfg.get("models", {}).get(args.model)
    if not model_def:
        raise KeyError(f"Model '{args.model}' not found in config/models.yaml")

    print(f"[inference] Placeholder for model={args.model}, input={args.input_dir}, output={args.output_dir}")


if __name__ == "__main__":
    main()
