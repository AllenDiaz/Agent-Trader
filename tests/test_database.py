"""Tests for backend/database.py — SQLite persistence for accounts and logs."""

from backend import database


def test_account_round_trip(temp_db):
    database.write_account("Warren", {"balance": 123.45, "holdings": {"AAPL": 3}})
    assert database.read_account("warren") == {"balance": 123.45, "holdings": {"AAPL": 3}}


def test_read_missing_account_returns_none(temp_db):
    assert database.read_account("nobody") is None


def test_account_name_is_case_insensitive(temp_db):
    database.write_account("CATHIE", {"balance": 1.0})
    assert database.read_account("cathie") == {"balance": 1.0}
    assert database.read_account("Cathie") == {"balance": 1.0}


def test_write_account_upserts(temp_db):
    database.write_account("ray", {"balance": 1.0})
    database.write_account("ray", {"balance": 2.0})
    assert database.read_account("ray") == {"balance": 2.0}


def test_logs_written_and_read(temp_db):
    database.write_log("george", "account", "first")
    database.write_log("george", "account", "second")
    rows = list(database.read_log("george", last_n=10))
    messages = {message for _, _, message in rows}
    assert messages == {"first", "second"}


def test_read_log_respects_last_n(temp_db):
    for i in range(5):
        database.write_log("george", "account", f"m{i}")
    rows = list(database.read_log("george", last_n=2))
    assert len(rows) == 2
