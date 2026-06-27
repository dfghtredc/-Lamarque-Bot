# Backward compatibility shim.
# New code should import from config_manager directly.
from config_manager import config, save_config as _save, load_config as _load

def load_config() -> dict:
    return config

def save_config(cfg: dict = None) -> None:
    if cfg is not None:
        config.update(cfg)
    _save()
