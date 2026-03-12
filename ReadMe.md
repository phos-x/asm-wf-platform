
# 🚀 Universal MLOps Orchestrator

A modular, config-driven pipeline for preparing datasets, executing machine learning experiments, and running multi-GPU hyperparameter sweeps.

This platform is completely **model-agnostic**. It treats external repositories as black boxes, allowing you to clone, train, and tune third-party models (like BSRoformer) without ever modifying their source code.

---

## ✨ Key Features

* **Idempotent Preparation (`prep`)**: Automatically clones external repos, installs `requirements.txt` only when needed, and downloads/processes datasets.
* **Black-Box Execution (`run`)**: Runs external `train.py` scripts in isolated subprocess environments. Dynamically injects absolute paths and arguments.
* **Zero-Touch Hyperparameter Tuning (`tune`)**: Uses **Ray Tune** and **Optuna** to run parallel, multi-GPU sweeps (e.g., on Kaggle 2x T4 instances).
* **Real-Time Metric Parsing**: Extracts validation metrics from the standard output (stdout) of black-box models in real-time using Regex, enabling **ASHA Early Stopping** without touching the model's codebase.
* **100% Config-Driven**: Everything from Git branches and dataset URLs to learning rate search spaces is controlled via YAML registries.

---

## 📂 Project Architecture

```text
.
├── core/
│   ├── config/
│   │   └── models.yaml          # Git repos and target train scripts
│   ├── registry/
│   │   ├── datasets.yaml        # Dataset URLs and processing scripts
│   │   ├── experiments.yaml     # Single-run configurations
│   │   └── tuning.yaml          # Ray Tune & Optuna search spaces
│   └── orchestrator/
│       ├── orchestrator.py      # The main CLI router
│       ├── common.py            # Shared path resolution and helpers
│       ├── prep.py              # Phase 1: Environment & Data setup
│       ├── run.py               # Phase 2: Execution & MLflow tracking
│       └── tune.py              # Phase 3: Multi-GPU Hyperparameter Tuning
└── infra/                       # Terraform & Docker setup for MLflow

```

---

## 🛠️ Command Line Interface (CLI)

The orchestrator is controlled via a unified CLI with specialized subcommands.

### Phase 1: Preparation (`prep`)

Ensure the environment is ready. This idempotently clones the repo, installs dependencies, and extracts the dataset.

```bash
# Run the full automated prep pipeline
python core/orchestrator/orchestrator.py prep --exp exp_bs_roformer_mel

# Run specific surgical steps (great for debugging data scripts)
python core/orchestrator/orchestrator.py prep --exp exp_bs_roformer_mel --steps process
python core/orchestrator/orchestrator.py prep --exp exp_bs_roformer_mel --steps clone install

```

### Phase 2: Execution (`run`)

Launch a single training job based on an experiment profile. The orchestrator isolates the environment and logs exit codes to MLflow.

```bash
python core/orchestrator/orchestrator.py run --exp exp_bs_roformer_mel

```

### Phase 3: Hyperparameter Tuning (`tune`)

Launch a multi-worker Ray Tune cluster. Automatically distributes Optuna trials across available GPUs and parses terminal output to catch validation metrics.

```bash
python core/orchestrator/orchestrator.py tune --config tune_bs_roformer_mel

```

---

## ⚙️ Configuration Guide

The platform is driven by four central YAML files. You rarely need to touch the Python code; just define your intent here.

### 1. `models.yaml` (The Codebase)

Defines where the model lives and how to pull it.

```yaml
models:
  bs_roformer:
    source_repo: "https://github.com/ZFTurbo/Music-Source-Separation-Training.git"
    branch: "main"
    target_dir: "core/models/bs_roformer"
    train_script: "train.py"

```

### 2. `datasets.yaml` (The Data)

Defines where to download the data and what script processes it.

```yaml
datasets:
  musdb18:
    source_url: "https://example.com/musdb18.zip"
    raw_path: "core/datasets/raw/musdb18"
    processed_path: "core/datasets/processed/musdb18"
    extract_script: "core/scripts/extract_stems.py"

```

### 3. `experiments.yaml` (The Execution)

Binds a model and a dataset together with specific command-line arguments. The orchestrator automatically expands `$DATASET_DIR` to the absolute path of the processed dataset.

```yaml
experiments:
  exp_bs_roformer_mel:
    model: "bs_roformer"
    dataset: "musdb18"
    mlflow_experiment: "stem_separation_baselines"
    cmd: "python train.py --data_path $DATASET_DIR/train"
    extra_args: "--model_type bs_roformer --batch_size 4"

```

### 4. `tuning.yaml` (The Sweep)

Inherits an experiment and defines the Optuna search space and Ray Tune hardware limits.

```yaml
tuning:
  tune_bs_roformer_mel:
    base_experiment: "exp_bs_roformer_mel"
    
    # Extract validation metrics from the model's terminal output!
    target_metric: "val_loss"
    mode: "min"
    metric_regex: '(?i)(?:valid(?:ation)?\s*loss|val_loss)\s*[:=]\s*([0-9]+\.[0-9]+)'
    
    resources_per_trial:
      gpu: 1
      cpu: 2
      
    tune_config:
      num_samples: 20
      max_concurrent_trials: 2 # Ideal for Kaggle 2x T4 setup
      
    search_space:
      lr:
        type: "loguniform"
        low: 1.0e-5
        high: 1.0e-3
      batch_size:
        type: "choice"
        values: [2, 4]

```

---

## 💡 How the "Black-Box" Tuning Works

Usually, distributed tuning requires modifying the model's `train.py` to include `ray.train.report()`.

To maintain a strict plug-and-play architecture, this orchestrator uses a **Subprocess Stream Parser**. It launches the external script in an isolated subprocess, captures `stdout` in real-time, and uses the `metric_regex` defined in `tuning.yaml` to extract the validation score epoch-by-epoch. This allows Ray's **ASHA Scheduler** to instantly kill underperforming trials and save massive amounts of GPU compute time, all without altering a single line of the original model code.