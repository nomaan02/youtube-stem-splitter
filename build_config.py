"""
Build configuration for YouTube Stem Splitter executable packaging
"""
import os
import sys

# Application metadata
APP_NAME = "YouTube Stem Splitter"
APP_VERSION = "1.0.0"
APP_AUTHOR = "nomaan02"

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'models')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
TEMP_DIR = os.path.join(BASE_DIR, 'temp')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Ensure directories exist
for directory in [MODELS_DIR, OUTPUT_DIR, STATIC_DIR, TEMPLATES_DIR, TEMP_DIR, LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)

# PyTorch/CUDA settings
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
os.environ['OMP_NUM_THREADS'] = '1'

# Suppress warnings
os.environ['PYTHONWARNINGS'] = 'ignore'

print(f"[Build Config] Base directory: {BASE_DIR}")
print(f"[Build Config] Output directory: {OUTPUT_DIR}")
print(f"[Build Config] CUDA device: {os.environ.get('CUDA_VISIBLE_DEVICES', 'default')}")
