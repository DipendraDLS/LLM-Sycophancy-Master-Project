from components.package_loader import *
import os
import sys
import io
import gc
import contextlib
import subprocess
import logging
import warnings
import time
import re
from pathlib import Path
from dotenv import load_dotenv

import streamlit as st
from huggingface_hub import hf_hub_download, list_repo_files

# ---  DYNAMIC PATH ENVELOPE RESOLUTION ---
current_path = Path(__file__).resolve()
while current_path.name != "evaluating-sycophancy" and current_path.parent != current_path:
    current_path = current_path.parent
PROJECT_ROOT = str(current_path)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Suppress internal frame framework warnings and logging noise
warnings.filterwarnings("ignore", category=SyntaxWarning)   
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
logging.getLogger("torch").setLevel(logging.ERROR)
logging.getLogger("torch.utils").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)

#CLEAN ENVIRONMENT OVERRIDE
# Stripped out the broken os.environ["TORCH_LOGS"] string assignments completely!
os.environ["PYTORCH_JIT_LOG_LEVEL"] = "ERROR"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

load_dotenv()

# Cluster Experimental Model Mapping Registry
MODEL_REGISTRY = {
    "Mistral-7B-Instruct-v0.3-AWQ": {
        "repo_id": "solidrust/Mistral-7B-Instruct-v0.3-AWQ",
        "env_var": "MISTRAL_AWQ_MODEL_PATH"
    },
    "Zephyr-7B-beta-AWQ": {
        "repo_id": "TheBloke/zephyr-7B-beta-AWQ",
        "env_var": "ZEPHYR_AWQ_MODEL_PATH"
    },
    "Gemma-7b-it-AWQ": {
        "repo_id": "TechxGenus/gemma-7b-it-AWQ",
        "env_var": "GEMMA_AWQ_MODEL_PATH"
    }
}

class StreamToCallback(io.StringIO):
    """Intercepts framework runtime output segments and funnels them directly to a UI function."""
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def write(self, s):
        if s:
            self.callback(s)
        return super().write(s)

def configure_alex_cluster_cuda():
    """Maps runtime environments to absolute local SPACK targets on the Alex Cluster."""
    cuda_path = "/apps/SPACK/1.1.1-alex/opt/spack/linux-almalinux9-zen3/none-none/cuda-13.2.0-muu4y5j66hnxz4ijk3xkmchxguoddbsh"
    os.environ["CUDA_HOME"] = cuda_path
    os.environ["PATH"] = f"{cuda_path}/bin:" + os.environ.get("PATH", "")
    os.environ["LD_LIBRARY_PATH"] = f"{cuda_path}/lib64:" + os.environ.get("LD_LIBRARY_PATH", "")

configure_alex_cluster_cuda()

def get_missing_models():
    """Scans environmental cache targets for unprovisioned files."""
    missing_models = []
    for model_name, config in MODEL_REGISTRY.items():
        local_path = os.getenv(config["env_var"])
        if not local_path:
            missing_models.append(model_name)
            continue
        path = Path(local_path)
        if not path.exists() or not any(path.iterdir()):
            missing_models.append(model_name)
    return missing_models

def download_selected_models(models_to_download, progress_callback=None):
    """Pulls missing remote model assets into local cluster network storage lanes."""
    for current_model in models_to_download:
        if current_model not in MODEL_REGISTRY:
            continue
        config = MODEL_REGISTRY[current_model]
        repo_id = config["repo_id"]
        cache_dir = os.getenv(config["env_var"])
        
        if progress_callback:
            progress_callback(f"Connecting to remote endpoint: {repo_id}\nParsing manifest layout...")

        try:
            files = list_repo_files(repo_id=repo_id)
        except Exception as e:
            raise RuntimeError(f"Hugging Face Hub connection dropped: {str(e)}")

        for file_name in files:
            if file_name.startswith("."): 
                continue
            if progress_callback:
                progress_callback(f"Downloading slice segment: {file_name}")
            hf_hub_download(repo_id=repo_id, filename=file_name, cache_dir=cache_dir)
            if progress_callback:
                progress_callback(f"✅ Segment sync complete: {file_name}")
    return True

if not hasattr(st, "_global_gpu_model_pool"):
    st._global_gpu_model_pool = {}
    
def load_cached_llm(model_name: str, _progress_callback=None):
    """
    Constructs model objects into VRAM securely while explicitly 
    preventing double-allocation across browser sessions.
    """
    # THE GUARD MUTEX INTERCEPT:
    # If the model is already initialized in our global process registry,
    # pull it from hardware memory immediately.
    if model_name in st._global_gpu_model_pool:
        if _progress_callback:
            _progress_callback(f"♻️ VRAM Registry Hit: {model_name} recovered. Re-linking memory tracks...")
        return st._global_gpu_model_pool[model_name]

    # LOCALIZED SHIELD FOR PYTORCH
    import os
    import torch
    import contextlib
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if model_name not in MODEL_REGISTRY:
        raise ValueError(f"Target model identifier '{model_name}' missing from mapping schema.")
    if not torch.cuda.is_available():
        raise RuntimeError("Isolated device lane validation failed. CUDA context missing from active process.")
        
    config = MODEL_REGISTRY[model_name]
    repo_id = config["repo_id"]
    cache_dir = os.getenv(config["env_var"])
    
    @contextlib.contextmanager
    def capture_progress_stream():
        if _progress_callback:
            stdout_redirect = StreamToCallback(_progress_callback)
            stderr_redirect = StreamToCallback(_progress_callback)
            with contextlib.redirect_stdout(stdout_redirect), contextlib.redirect_stderr(stderr_redirect):
                yield
        else:
            yield

    with capture_progress_stream():
        # Load model in FP16 to stay within VRAM bounds
        model = AutoModelForCausalLM.from_pretrained(
            repo_id, 
            cache_dir=cache_dir, 
            device_map="auto", 
            torch_dtype=torch.float16
        )
        tokenizer = AutoTokenizer.from_pretrained(repo_id, cache_dir=cache_dir)
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "left"
        
    # STORE IN PERSISTENT TRACKER:
    st._global_gpu_model_pool[model_name] = (model, tokenizer)
        
    return model, tokenizer

def clear_gpu_vram():
    """Flushes pointers, references, and caches across the application to prevent OOM errors."""
    # LOCALIZED SHIELD FOR PYTORCH
    import torch
    import gc

    st.session_state.pop("active_model", None)
    st.session_state.pop("active_tokenizer", None)
    st.session_state.pop("active_model_name", None)
    
    # ACTION: Integrate dynamic device mapping here:
    # This empties out the hidden dictionary tracking your memory addresses!
    if hasattr(st, "_global_gpu_model_pool"):
        st._global_gpu_model_pool.clear()

    # Empty resource references managed by Streamlit cache controllers
    load_cached_llm.clear()
    
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()