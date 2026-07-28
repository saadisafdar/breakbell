"""Loads/saves BreakBell settings to a per-user JSON config file."""
import json
import os
import sys

DEFAULT_CONFIG = {
    "enabled": True,
    "work_seconds": 20 * 60,
    "break_seconds": 60,
    "title": "Take a break",
    "message": "Look away from the screen.\nRoll your shoulders.\nTake a few deep breaths.",
    "sound": "Ping",
}


def _config_dir():
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, "BreakBell")
    elif sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/BreakBell")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
        return os.path.join(base, "breakbell")


def config_path():
    return os.path.join(_config_dir(), "config.json")


def load_config():
    path = config_path()
    config = dict(DEFAULT_CONFIG)
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            config.update({k: v for k, v in saved.items() if k in DEFAULT_CONFIG})
    except Exception:
        pass  # Corrupt/unreadable config - fall back to defaults
    return config


def save_config(config):
    path = config_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception:
        return False
