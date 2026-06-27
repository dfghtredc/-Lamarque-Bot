"""
config_manager.py
-----------------
Persistent config using SQLite via aiosqlite.
Falls back to config.json for migration on first run.

Tables:
    config      — key/value store for all bot settings
    audit_log   — last 100 bot actions
    spam_track  — per-user message timestamps for anti-spam
"""

import json
import asyncio
import aiosqlite
from pathlib import Path

DB_PATH = Path("bot.db")
CONFIG_JSON = Path("config.json")

# ── In-memory config cache ────────────────────────────────────
config: dict = {}

_db: aiosqlite.Connection | None = None


async def init_db() -> None:
    """Initialize database and tables. Called once at startup."""
    global _db
    _db = await aiosqlite.connect(DB_PATH)
    await _db.execute("PRAGMA journal_mode=WAL")  # better concurrent write performance

    await _db.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    await _db.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL DEFAULT (datetime('now')),
            guild_id    INTEGER,
            user_id     INTEGER,
            user_name   TEXT,
            command     TEXT,
            detail      TEXT
        )
    """)

    await _db.execute("""
        CREATE TABLE IF NOT EXISTS spam_track (
            user_id     INTEGER NOT NULL,
            guild_id    INTEGER NOT NULL,
            timestamp   REAL NOT NULL
        )
    """)

    await _db.execute("""
        CREATE TABLE IF NOT EXISTS allowlist (
            guild_id    INTEGER PRIMARY KEY
        )
    """)

    await _db.commit()

    # migrate from config.json if it exists and db is empty
    await _migrate_from_json()

    # load all config into memory
    await _load_into_memory()


async def _migrate_from_json() -> None:
    """One-time migration from config.json to SQLite."""
    if not CONFIG_JSON.exists():
        return

    async with _db.execute("SELECT COUNT(*) FROM config") as cursor:
        count = (await cursor.fetchone())[0]
        if count > 0:
            return  # already migrated

    print("[CONFIG] Migrating config.json to SQLite...")
    try:
        data = json.loads(CONFIG_JSON.read_text())
        for key, value in data.items():
            await _db.execute(
                "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                (key, json.dumps(value))
            )
        await _db.commit()
        CONFIG_JSON.rename("config.json.migrated")
        print("[CONFIG] Migration complete. config.json renamed to config.json.migrated")
    except Exception as e:
        print(f"[CONFIG] Migration failed: {e}")


async def _load_into_memory() -> None:
    """Load all config rows into the in-memory dict."""
    global config
    config.clear()
    async with _db.execute("SELECT key, value FROM config") as cursor:
        async for row in cursor:
            config[row[0]] = json.loads(row[1])


async def save_config() -> None:
    """Persist the in-memory config dict to SQLite."""
    for key, value in config.items():
        await _db.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (key, json.dumps(value))
        )
    await _db.commit()


async def set_config(key: str, value) -> None:
    """Set a single config key and persist immediately."""
    config[key] = value
    await _db.execute(
        "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
        (key, json.dumps(value))
    )
    await _db.commit()


async def delete_config(key: str) -> None:
    """Delete a config key."""
    config.pop(key, None)
    await _db.execute("DELETE FROM config WHERE key = ?", (key,))
    await _db.commit()


# ── Audit log ─────────────────────────────────────────────────

async def log_action(guild_id: int, user_id: int, user_name: str, command: str, detail: str = "") -> None:
    """Log a bot action to the audit_log table. Keeps last 500 rows."""
    await _db.execute(
        "INSERT INTO audit_log (guild_id, user_id, user_name, command, detail) VALUES (?, ?, ?, ?, ?)",
        (guild_id, user_id, user_name, command, detail)
    )
    # prune old entries — keep last 500
    await _db.execute("""
        DELETE FROM audit_log WHERE id NOT IN (
            SELECT id FROM audit_log ORDER BY id DESC LIMIT 500
        )
    """)
    await _db.commit()


async def get_audit_log(guild_id: int, limit: int = 20) -> list[dict]:
    """Fetch the last N audit log entries for a guild."""
    rows = []
    async with _db.execute(
        "SELECT timestamp, user_name, command, detail FROM audit_log WHERE guild_id = ? ORDER BY id DESC LIMIT ?",
        (guild_id, limit)
    ) as cursor:
        async for row in cursor:
            rows.append({
                "timestamp": row[0],
                "user_name": row[1],
                "command":   row[2],
                "detail":    row[3]
            })
    return rows


# ── Saved quotes ──────────────────────────────────────────────

def get_saved_quotes() -> set:
    """Return saved_quotes as a set for O(1) lookup."""
    return set(config.get("saved_quotes", []))


async def add_saved_quote(message_id: int) -> None:
    """Add a message ID to saved_quotes and persist."""
    saved = list(get_saved_quotes())
    if message_id in saved:
        return
    saved.append(message_id)
    # cap at 5000
    if len(saved) > 5000:
        saved = saved[-5000:]
    config["saved_quotes"] = saved
    await set_config("saved_quotes", saved)


def is_saved(message_id: int) -> bool:
    """O(1) check — no disk read."""
    return message_id in get_saved_quotes()


async def clear_saved_quotes() -> None:
    """Clear all saved quotes."""
    config["saved_quotes"] = []
    await set_config("saved_quotes", [])


# ── Allowlist ─────────────────────────────────────────────────

async def add_to_allowlist(guild_id: int) -> None:
    await _db.execute("INSERT OR IGNORE INTO allowlist (guild_id) VALUES (?)", (guild_id,))
    await _db.commit()


async def remove_from_allowlist(guild_id: int) -> None:
    await _db.execute("DELETE FROM allowlist WHERE guild_id = ?", (guild_id,))
    await _db.commit()


async def is_allowlisted(guild_id: int) -> bool:
    async with _db.execute("SELECT 1 FROM allowlist WHERE guild_id = ?", (guild_id,)) as cursor:
        return await cursor.fetchone() is not None


async def get_allowlist() -> list[int]:
    rows = []
    async with _db.execute("SELECT guild_id FROM allowlist") as cursor:
        async for row in cursor:
            rows.append(row[0])
    return rows


# ── Spam tracking ─────────────────────────────────────────────

async def record_message(user_id: int, guild_id: int, timestamp: float) -> None:
    await _db.execute(
        "INSERT INTO spam_track (user_id, guild_id, timestamp) VALUES (?, ?, ?)",
        (user_id, guild_id, timestamp)
    )
    # prune entries older than 10 seconds
    await _db.execute(
        "DELETE FROM spam_track WHERE timestamp < ?",
        (timestamp - 10,)
    )
    await _db.commit()


async def get_message_count(user_id: int, guild_id: int, window: float, since: float) -> int:
    async with _db.execute(
        "SELECT COUNT(*) FROM spam_track WHERE user_id = ? AND guild_id = ? AND timestamp > ?",
        (user_id, guild_id, since)
    ) as cursor:
        row = await cursor.fetchone()
        return row[0] if row else 0


# ── Shutdown ──────────────────────────────────────────────────

async def close_db() -> None:
    if _db:
        await _db.close()
