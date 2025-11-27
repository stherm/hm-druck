from pathlib import Path
import os
import json


def get_config_dir() -> Path:
    if os.name == "nt":
        base = os.getenv("APPDATA")
        if not base:
            base = str(Path.home())
        base_path = Path(base)
    else:
        base_path = Path.home() / ".config"

    cfg_dir = base_path / "hm-druck"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir


def get_config_path() -> Path:
    return get_config_dir() / "config.json"


def load_config() -> dict:
    path = get_config_path()
    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
    except Exception:
        return {}


def save_config(cfg: dict) -> None:
    path = get_config_path()
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass

