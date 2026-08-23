"""Shared pytest fixtures.

The backend constructs LLM clients at import time and reads/writes a SQLite
database at a module-level path. These fixtures make the suite run fully
offline and against a throwaway database so the real accounts.db is untouched.
"""

import os

# Model clients (backend/traders.py) are built at import and require a key to
# exist. Set a dummy one before any backend module is imported so the suite
# runs without real credentials (e.g. in CI).
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

import sqlite3

import pytest

from backend import database


def _create_schema(db_path: str) -> None:
    """Create the same tables backend/database.py builds at import time."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS accounts (name TEXT PRIMARY KEY, account TEXT)")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                datetime DATETIME,
                type TEXT,
                message TEXT
            )
            """
        )
        conn.commit()


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Point all database access at a fresh temp file for the duration of a test."""
    db_path = tmp_path / "test_accounts.db"
    monkeypatch.setattr(database, "DB", str(db_path))
    _create_schema(str(db_path))
    return db_path
