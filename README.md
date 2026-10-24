# Evaluating Sycophancy in LLMs

This project implements an automated execution pipeline on an HPC (High-Performance Computing) cluster to evaluate sycophancy in Large Language Models (LLMs). The project features a Streamlit dashboard interface to monitor environment prerequisites, initialize evaluation nodes, and track multi-model automation workflows.

---

## Configuration & Installation

Follow these steps to configure your environment and run the pipeline on the HPC **alex** node.

### Prerequisites

- Ensure you have configured your SSH keys in GitLab before attempting to clone.
- Make sure you are logged into the HPC **alex** login node.

### 1. Clone the Repository

Clone the repository and switch to the `main` branch:

```bash
# Clone via SSH (Recommended)
git clone git@github.com:DipendraDLS/LLM-Sycophancy-Master-Project.git

# OR clone via HTTPS
git clone https://github.com/DipendraDLS/LLM-Sycophancy-Master-Project.git

# Navigate into the project directory
cd LLM-Sycophancy-Master-Project

# Fetch remote branches and switch to main
git fetch --all --prune
git checkout main
```

### 2. Setting Up the Environment

Run the setup script from the root directory to configure the required dependencies, virtual environment (`uv`), and the backend database:

```bash
./setup.sh
```

### 3. Running the Dashboard Interface

To launch the user interface for monitoring and executing the evaluation, run the dashboard shell script:

```bash
uv run streamlit run app/dashboard.py
```

> **Troubleshooting:** If you encounter errors related to the package manager `uv`, install it locally and update your system path:
>

> ```bash
> # Install uv locally
> curl -LsSf https://astral.sh/uv/install.sh | sh
>
> # Make uv usable globally
> export PATH="$HOME/.local/bin:$PATH"
> ```

---

## 📂 Project Structure

Below is the directory structure of the repository. The central execution workflow is driven by the orchestration components.

```
evaluating-sycophancy/

├── app/                          # Main application package
│   ├── backend/                  # Backend logic and services
│   │   ├── database/             # Database models and connection handling
│   │   ├── llms/                 # LLM client/wrapper implementations
│   │   └── orchestration/        # Pipeline execution and scheduling logic
│   │       ├── gpu_validator.py     # GPU/environment validation checks
│   │       └── pipeline_runner.py   # 📌 Core pipeline execution orchestration
│   ├── components/               # Streamlit UI components and layout views
│   ├── styles/                   # UI styling assets
│   ├── templates/                # Template files
│   ├── utils/                    # Shared utility functions
│   └── main.py                   # Application entry point
├── data/                         # Dataset directories
├── logs/                         # Runtime and pipeline logs
├── postgres_database/            # Local Postgres database files
├── .env                          # Environment variables
├── .python-version               # Python version pin
├── config.py                     # Global configuration and path setups
├── pyproject.toml                # Project metadata and dependencies
├── uv.lock                       # Lockfile for reproducible environment setup
├── run_dashboard.sh              # Startup script for dashboard
└── setup.sh                      # Initial project setup script
```

---

## Pipeline Architecture

Below is the conceptual architecture of the automated evaluation framework.
![Pipeline Architecture](docs/images/DS-IProj-M-Pipeline-Architecture.png)

### Architecture Overview

1. **Orchestration Layer** — The main execution script (`orchestration/`) serves as the central control plane, initializing environment validation checks (GPU configurations, folder structures, database connectivity).

2. **HPC Background Execution** — Once validated, the orchestrator triggers an asynchronous job on the HPC backend via SLURM.

   > **Tip:** You can close your browser tab once execution begins; the job will safely finish processing in the background.

3. **Model Automation Loop** — The execution loop sequentially passes the evaluation data through the target models to isolate sycophantic behavior.

4. **Data Persistence** — Output datasets and metrics are simultaneously backed up locally under `data/backup_runs/` and written to the database for historical tracking.

---

## Execution & Evaluation Options

Once the Evaluation Environment is successfully initialized via the dashboard, you have two runtime options:

| Mode | Description | Estimated Time |
|------|-------------|-----------------|
| **Demo Run** | Executes only 1 essay to verify end-to-end telemetry. | ~8–10 minutes |
| **Full Run** | Executes all 30 essays across the entire model loop for a comprehensive evaluation. | ~5 hours |

> ⚠️ **System Asset Flushing:** If you click **Flush System Assets** at any point, your active job will be completely terminated, and the allocated GPU nodes will immediately be released back to the HPC server pool.
