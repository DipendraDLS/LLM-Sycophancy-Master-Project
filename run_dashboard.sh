#!/bin/bash
#SBATCH --job-name=llm_dashboard
#SBATCH --partition=a40
#SBATCH -C el9
#SBATCH --gres=gpu:1
#SBATCH --time=04:00:00       
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --output=logs/dashboard_%j.log

# --- PROFESSIONAL TERMINAL COLORS ---
BOLD='\033[1m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${CYAN}${BOLD}====================================================="
echo -e "   SYCOPHANCY EVALUATION : EXECUTION ENGINE          "
echo -e "=====================================================${NC}"

# 1. MODULE ORCHESTRATION
echo -e "${BLUE}[INFO]${NC} Purging environment and loading CUDA modules..."
module purge
module load cuda/12.1.1       
module load gcc

# 2. DYNAMIC PATH RESOLUTION
if [ -n "$SLURM_SUBMIT_DIR" ]; then
    cd "$SLURM_SUBMIT_DIR"
else
    cd "$(dirname "$0")"
fi

# 3. ENVIRONMENT COUPLING
echo -e "${BLUE}[INFO]${NC} Activating isolated virtual environment assets..."
source .venv/bin/activate

# 4. RESOURCE ISOLATION
export TRITON_CACHE_DIR="/tmp/triton_cache_${USER}"
mkdir -p "$TRITON_CACHE_DIR"
unset TORCH_LOGS

# 5. ENGINE LAUNCH
echo -e "${GREEN}[SUCCESS]${NC} Background execution workers initialized."
echo -e "${BLUE}[INFO]${NC} Launching Streamlit dashboard on port 8501..."
echo ""
streamlit run app/main.py --server.port=8501 --server.address=0.0.0.0