"""
Configuration file for the LLM-based code fixing agent.
"""
import os
from pathlib import Path

class Config:
    # Model configuration
    MODEL_ID = "bigcode/starcoder2-3b"  # Your original model
    MAX_NEW_TOKENS = 512
    TEMPERATURE = 0.3
    TOP_K = 50
    TOP_P = 0.95
    
    # Execution configuration
    MAX_ATTEMPTS = 3
    TIMEOUT_SECONDS = 10
    
    # Paths - will be set automatically
    BASE_DIR = Path("/home/coder/project/experiments")
    
    # Device configuration
    DEVICE = "auto"  # Will use GPU if available
    USE_8BIT = True  # Use 8-bit quantization for efficiency
    
    @classmethod
    def setup_paths(cls, base_path=None):
        """Setup base directory for experiments."""
        if base_path:
            cls.BASE_DIR = Path(base_path)
        else:
            # Use current working directory + experiments
            cls.BASE_DIR = Path.cwd() / "experiments"
        
        cls.BASE_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Experiments will be saved to: {cls.BASE_DIR.absolute()}")
        return cls.BASE_DIR
    
    @classmethod
    def get_model_config(cls):
        """Get model configuration dictionary."""
        return {
            'model_id': cls.MODEL_ID,
            'max_new_tokens': cls.MAX_NEW_TOKENS,
            'temperature': cls.TEMPERATURE,
            'top_k': cls.TOP_K,
            'top_p': cls.TOP_P,
            'device': cls.DEVICE,
            'use_8bit': cls.USE_8BIT
        }