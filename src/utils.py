import os
import shutil
import logging
import re
from pathlib import Path
from urllib.parse import urlparse
import subprocess

def setup_logging(log_dir, log_level="INFO"):
    """Configure logging with file and console handlers"""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "stem_splitter.log"

    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def validate_url(url, supported_platforms):
    """Validate if URL is from supported platform"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return any(platform in domain for platform in supported_platforms)
    except Exception:
        return False

def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Limit length
    return filename[:200]

def check_disk_space(directory, min_gb_required):
    """Check if sufficient disk space available"""
    stat = shutil.disk_usage(directory)
    free_gb = stat.free / (1024**3)
    return free_gb >= min_gb_required

def check_ffmpeg():
    """Verify FFmpeg is installed and accessible"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def create_directory_structure(base_dir):
    """Create necessary directories"""
    dirs = [base_dir / "output", base_dir / "temp", base_dir / "logs"]
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)
    return dirs
