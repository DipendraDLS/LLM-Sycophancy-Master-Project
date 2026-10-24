#!/bin/bash

# --- PROFESSIONAL TERMINAL COLORS ---
BOLD='\033[1m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Exit immediately if a command exits with a non-zero status
set -e

echo -e "${CYAN}${BOLD}====================================================="
echo -e "   SYCOPHANCY EVALUATION : PROJECT INFRASTRUCTURE    "
echo -e "=====================================================${NC}"
echo -e "${BLUE}[INFO]${NC} Initializing automated environment orchestration..."
echo ""
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}[SETUP]${NC} 'uv' package manager not found. Installing locally..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Ensure it's immediately accessible in the current execution subshell
    if [ -f "$HOME/.local/bin/env" ]; then
        source "$HOME/.local/bin/env"
    else
        export PATH="$HOME/.local/bin:$PATH"
    fi
else
    echo -e "${GREEN}[SUCCESS]${NC} 'uv' package manager verified."
fi

# Permanently inject uv into user profile files if not already tracked
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "${BLUE}[INFO]${NC} Exporting 'uv' binaries permanently to path profiles..."
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.profile
fi

# ==============================================================================
# 2. BUILD VIRTUAL ENVIRONMENT USING TARGET CONFIGURATIONS
# ==============================================================================
# Read target Python version dynamically from project's tracking file
PYTHON_VERSION="3.10"
if [ -f ".python-version" ]; then
    PYTHON_VERSION=$(cat .python-version | tr -d '[:space:]')
    echo -e "${BLUE}[INFO]${NC} Target engine profile detected: ${BOLD}Python $PYTHON_VERSION${NC}"
else
    echo -e "${YELLOW}[WARN]${NC} .python-version missing. Defaulting to Python 3.10"
fi

if [ ! -d ".venv" ]; then
    echo -e "${BLUE}[SETUP]${NC} Building isolated virtual environment..."
    uv venv .venv --python "$PYTHON_VERSION"
fi

# Activate environment targets
source .venv/bin/activate

# ==============================================================================
# 3. INSTALL REQUIREMENTS DIRECTLY FROM PYPROJECT.TOML
# ==============================================================================
if [ -f "pyproject.toml" ]; then
    echo -e "${BLUE}[SYNC]${NC} Synchronizing dependencies from pyproject.toml specification..."
    uv sync
else
    echo -e "${YELLOW}[WARN]${NC} pyproject.toml not found! Falling back to individual installs..."
    uv pip install streamlit sqlalchemy psycopg2-binary python-dotenv
fi

# ==============================================================================
# 4. DOWNLOAD POSTGRESQL SOURCE CODE FROM WORKING SOURCE
# ==============================================================================
if [ ! -d ".postgres_bin" ] || [ ! -f ".postgres_bin/src/bin/initdb/initdb.c" ]; then
    echo -e "${BLUE}[FETCH]${NC} Authenticating with PostgreSQL v15.4 official source mirror..."
    rm -rf .postgres_bin postgresql-15.4.tar.gz
    mkdir -p .postgres_bin
    
    # Using the clean, validated stable source distribution FTP mirror
    wget -q --show-progress https://ftp.postgresql.org/pub/source/v15.4/postgresql-15.4.tar.gz
    
    echo -e "${BLUE}[BUILD]${NC} Extracting source tree straight into project space..."
    tar -xzf postgresql-15.4.tar.gz -C ".postgres_bin" --strip-components=1
    rm postgresql-15.4.tar.gz
else
    echo -e "${BLUE}[INFO]${NC} PostgreSQL source structure verified."
fi

# ==============================================================================
# 5. COMPILING BINARIES FOR LOCAL USER SPACE
# ==============================================================================
if [ ! -f ".postgres_bin/bin/initdb" ] || [ ! -f ".postgres_bin/bin/pg_ctl" ]; then
    echo -e "${BLUE}[BUILD]${NC} Initiating C-compilation framework on cluster architecture..."
    
    # Cache active working position
    ORIGINAL_DIR=$PWD
    cd .postgres_bin

    echo -e "${BLUE}[CONFIG]${NC} Configuring target layout for internal project mapping..."
    ./configure --prefix="$PWD" --without-readline --without-zlib

    echo -e "${BLUE}[MAKE]${NC} Executing parallel build compilation (4 threads)..."
    make -j4
    
    echo -e "${BLUE}[INSTALL]${NC} Finalizing system installation routine..."
    make install

    # Head back out to the workspace root securely
    cd "$ORIGINAL_DIR"
    echo -e "${GREEN}[SUCCESS]${NC} PostgreSQL binaries compiled successfully."
else
    echo -e "${BLUE}[INFO]${NC} Existing PostgreSQL binaries detected."
fi

echo ""
echo -e "${CYAN}${BOLD}====================================================="
echo -e "   SETUP COMPLETE : ENVIRONMENT LOCKED & READY       "
echo -e "=====================================================${NC}"
echo -e "${BLUE}[GUIDE]${NC} To begin evaluation, execute:"
echo -e "        ${BOLD}source .venv/bin/activate${NC}"
echo -e "        ${BOLD}uv run streamlit run app/main.py${NC}"
echo ""
 