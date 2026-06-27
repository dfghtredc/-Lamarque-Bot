"""
config_manager.py
-----------------
Single source of truth for bot config.
Loads from disk once at startup, keeps in memory.
Writes to disk only on mutation.
Replaces utils.py load_config/save_config pattern.

Usage:
    from config_manager import config, save_config

    # read
    channel_id = config.get("quoteboard_channel")

    # write
    config["quoteboard_channel"] = channel_id
    save_config()
"""

import json
import os
import shutil
from pathlib import Path

CONFIG_PATH = Path("config.json")
BACKUP_PATH = Path("config.backup.json")

# ── In-memory config dict ─────────────────────────────────────
# This is the single live copy. All cogs import and mutate this directly.
config: dict = {}

def load_config() -> None:
    """
    Load config from disk into the in-memory dict.
    Called once at bot startup. Not called per-command.
    """
    global config
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text("{}")

    try:
        data = json.loads(CONFIG_PATH.read_text())
        config.clear()
        config.update(data)
    except json.JSONDecodeError:
        print("[CONFIG] config.json is corrupt. Loading backup.")
        if BACKUP_PATH.exists():
            try:
                data = json.loads(BACKUP_PATH.read_text())
                config.clear()
                config.update(data)
                print("[CONFIG] Backup loaded successfully.")
            except json.JSONDecodeError:
                print("[CONFIG] Backup also corrupt. Starting with empty config.")
                config.clear()
        else:
            print("[CONFIG] No backup found. Starting with empty config.")
            config.clear()


def save_config() -> None:
    """
    Write the in-memory config dict to disk atomically.
    Uses a temp file + rename to prevent partial writes corrupting config.
    Also writes a backup before overwriting.
    """
    try:
        # backup current file before overwriting
        if CONFIG_PATH.exists():
            shutil.copy2(CONFIG_PATH, BACKUP_PATH)

        # write to temp file first
        tmp_path = CONFIG_PATH.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(config, indent=4))

        # atomic rename — either the full file is written or nothing changes
        tmp_path.replace(CONFIG_PATH)

    except OSError as e:
        print(f"[CONFIG] Failed to save config: {e}")


def get_saved_quotes() -> set:
    """Return saved_quotes as a set for O(1) lookup."""
    return set(config.get("saved_quotes", []))


def add_saved_quote(message_id: int) -> None:
    """Add a message ID to saved_quotes and persist."""
    saved = get_saved_quotes()
    saved.add(message_id)
    # cap at 5000 most recent — trim oldest if over limit
    if len(saved) > 5000:
        saved_list = config.get("saved_quotes", [])
        saved_list = saved_list[-5000:]  # keep newest 5000
        config["saved_quotes"] = saved_list
    else:
        config["saved_quotes"] = list(saved)
    save_config()


def is_saved(message_id: int) -> bool:
    """O(1) check — no disk read."""
    return message_id in get_saved_quotes()
