"""SQLite-based short-term memory for local persistence."""

import sqlite3
import time
import json
from pathlib import Path
from typing import Any

from agenthelm.memory.base import BaseShortTermMemory


class SqliteShortTermMemory(BaseShortTermMemory):
    """
    SQLite-based key-value store with TTL support.

    Provides persistent local storage without requiring Docker or network services.
    Uses lazy TTL expiration on access.

    Example:
        memory = SqliteShortTermMemory(db_path="./data/short_term.db")
        await memory.set("user:123:name", "Alice", ttl=3600)
        name = await memory.get("user:123:name")
    """

    def __init__(self, db_path: str | Path):
        """
        Initialize SQLite short-term memory.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS kv_store (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expiry REAL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_expiry ON kv_store(expiry)")
            conn.commit()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        return sqlite3.connect(self.db_path)

    async def get(self, key: str) -> Any | None:
        """Get a value by key. Returns None if not found or expired."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT value, expiry FROM kv_store WHERE key = ?", (key,)
            )
            row = cursor.fetchone()

            if row is None:
                return None

            value_json, expiry = row

            # Check if expired
            if expiry is not None and time.time() > expiry:
                conn.execute("DELETE FROM kv_store WHERE key = ?", (key,))
                conn.commit()
                return None

            return json.loads(value_json)

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """
        Set a value with TTL in seconds.

        Args:
            key: The key to store under
            value: Any JSON-serializable value
            ttl: Time-to-live in seconds (default: 1 hour, 0 for no expiration)
        """
        if ttl > 0:
            expiry = time.time() + ttl
        else:
            expiry = None

        value_json = json.dumps(value)

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO kv_store (key, value, expiry) 
                VALUES (?, ?, ?)
                """,
                (key, value_json, expiry),
            )
            conn.commit()

    async def delete(self, key: str) -> None:
        """Delete a key if it exists."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM kv_store WHERE key = ?", (key,))
            conn.commit()

    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT expiry FROM kv_store WHERE key = ?", (key,))
            row = cursor.fetchone()

            if row is None:
                return False

            expiry = row[0]

            if expiry is not None and time.time() > expiry:
                conn.execute("DELETE FROM kv_store WHERE key = ?", (key,))
                conn.commit()
                return False

            return True

    async def keys(self, pattern: str = "*") -> list[str]:
        """
        List keys matching a pattern.

        Note: Uses SQL LIKE pattern matching (% for wildcard).
        '*' is converted to '%' for SQL compatibility.
        """
        sql_pattern = pattern.replace("*", "%")

        # Clean up expired keys first
        now = time.time()
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM kv_store WHERE expiry IS NOT NULL AND expiry < ?", (now,)
            )
            cursor = conn.execute(
                "SELECT key FROM kv_store WHERE key LIKE ?", (sql_pattern,)
            )
            return [row[0] for row in cursor.fetchall()]

    def clear(self) -> None:
        """Clear all stored data."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM kv_store")
            conn.commit()

    async def close(self) -> None:
        """Close resources (no-op for SQLite, connections are per-operation)."""
        pass
