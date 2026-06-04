import os
import sys

def get_optimal_gpu_layers() -> int:
    """
    Dynamically determines how many layers to offload to the GPU
    based on the running system's hardware.
    """
    # Total layers for Qwen 2.5 7B is 28
    
    # Check if a collaberator explicitly wants to override via environment variables, possible by:
    # 1)Powershell terminal command: $env:APP_GPU_LAYERS=(insert desired number) and powershell run command for program
    # 2)Creating and storing .env file in project folder containing "APP_GPU_LAYERS=(insert desired number)"
    if "APP_GPU_LAYERS" in os.environ:
        return int(os.environ["APP_GPU_LAYERS"])
        
    # Cross-Platform Detection
    if sys.platform == "darwin":
        # Apple Silicon (M1/M2/M3) unified memory easily fits 7B models entirely on GPU
        print("[Config] Apple Silicon detected. Offloading 100% of layers to Metal.")
        return -1 
        
    elif sys.platform == "win32" or sys.platform.startswith("linux"):
        # If running on Windows/Linux, check if CUDA is actually available
        cuda_path = os.environ.get("CUDA_PATH") or os.environ.get("CUDA_HOME")
        
        if cuda_path:
            # Presence of dedicated NVIDIA GPU
            # Default to 20 layers to be safe on 4GB-6GB cards, leaving room for VRAM overhead
            print("[Config] Dedicated NVIDIA GPU infrastructure found. Utilizing Hybrid Mode.")
            return 20
            
    # Fallback: CPU-only mode
    print("[Config] No hardware acceleration profile matched. Defaulting to CPU Execution.")
    return 0