import os
from pathlib import Path

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"
LOGS_DIR = BASE_DIR / "logs"

# Demucs settings
DEFAULT_MODEL = "htdemucs"  # Best balance of quality/speed
AVAILABLE_MODELS = ["htdemucs", "htdemucs_ft", "htdemucs_6s", "mdx_extra"]

# Auto-detect GPU (lazy import to avoid errors before torch is installed)
def get_device():
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"

DEVICE = get_device()

# Audio settings
OUTPUT_FORMAT = "wav"  # Can be: wav, mp3, flac
SAMPLE_RATE = 44100
BIT_DEPTH = 16

# Download settings
MAX_RETRIES = 3
TIMEOUT = 30
SUPPORTED_PLATFORMS = ["youtube.com", "youtu.be", "soundcloud.com", "m.soundcloud.com"]

# File management
KEEP_ORIGINAL = True
CLEANUP_TEMP = True
MIN_FREE_SPACE_GB = 2  # Minimum disk space required

# Logging
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
