# app/backend/orchestration/gpu_validator.py
import torch

def is_gpu_node_available() -> bool:
    """
    Checks if an accessible NVIDIA GPU node is bound to the server thread.
    Returns True if cuda-compliant hardware is online.
    """
    return torch.cuda.is_available()