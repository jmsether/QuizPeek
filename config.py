import os
import json
import platform
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler

DEFAULTS = {
    "api_key": "",
    "save_key": False,
    "model": "meta-llama/llama-3.2-90b-vision-instruct",
    "hotkey": "ctrl",
    "top_crop_pct": 8,
    "bottom_crop_pct": 6,
    "max_width": 1024,
    "confidence_threshold": 0.70,
    "bypass_confidence": False,
    "show_notifications": False
}

def get_config_dir():
    system = platform.system()
    if system == "Windows":
        base = os.path.expandvars("%APPDATA%")
        return Path(base) / "QuizPeek"
    elif system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "QuizPeek"
    elif system == "Linux":
        return Path.home() / ".config" / "quizpeek"
    else:
        raise NotImplementedError(f"Unsupported platform: {system}")

def get_config_path():
    return get_config_dir() / "config.json"

def load_config() -> dict:
    config_path = get_config_path()
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        config = {}
    # Merge with defaults
    merged = DEFAULTS.copy()
    merged.update(config)
    return merged

def save_config(config: dict) -> None:
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

# Set up logging
config_dir = get_config_dir()
config_dir.mkdir(parents=True, exist_ok=True)
log_path = config_dir / "quizpeek.log"
handler = RotatingFileHandler(log_path, maxBytes=1024*1024, backupCount=5)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[handler]
)