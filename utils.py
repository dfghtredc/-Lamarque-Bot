# Backward compatibility shim.
# New code should import from config_manager directly.
from config_manager import config

def load_config() -> dict:
    return config

def save_config(cfg: dict = None) -> None:
    import asyncio
    from config_manager import save_config as _save, set_config
    if cfg is not None:
        config.update(cfg)
    # fire and forget — safe for non-critical legacy callers
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(_save())
        else:
            loop.run_until_complete(_save())
    except Exception:
        pass
