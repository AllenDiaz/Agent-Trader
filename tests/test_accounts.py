"""Tests for backend/accounts.py — the Account model and trading logic.

Share prices are monkeypatched to a fixed value so buy/sell math is
deterministic and no market data provider is contacted.
"""

import pytest

from backend import accounts
from backend.accounts import Account

FIXED_PRICE = 100.0


@pytest.fixture
def fixed_price(monkeypatch):
    monkeypatch.setattr(accounts, "get_share_price", lambda symbol: FIXED_PRICE)
    return FIXED_PRICE


def test_get_creates_account_with_initial_balance(temp_db):
    account = Account.get("newbie")
    assert account.balance == accounts.INITIAL_BALANCE
    assert account.holdings == {}
    assert account.transactions == []


def test_deposit_and_withdraw(temp_db):
    account = Account.get("depositor")
    account.deposit(500)
    assert account.balance == accounts.INITIAL_BALANCE + 500
    account.withdraw(200)
    assert account.balance == accounts.INITIAL_BALANCE + 300


def test_deposit_must_be_positive(temp_db):
    account = Account.get("x")
    with pytest.raises(ValueError):
        account.deposit(0)


def test_withdraw_insufficient_funds(temp_db):
    account = Account.get("y")
    with pytest.raises(ValueError):
        account.withdraw(accounts.INITIAL_BALANCE + 1)


def test_buy_shares_updates_holdings_and_balance(temp_db, fixed_price):
    account = Account.get("buyer")
    account.buy_shares("AAPL", 10, "value play")
    assert account.holdings == {"AAPL": 10}
    expected_cost = FIXED_PRICE * (1 + accounts.SPREAD) * 10
    assert account.balance == pytest.approx(accounts.INITIAL_BALANCE - expected_cost)
    assert len(account.transactions) == 1


def test_buy_shares_insufficient_funds(temp_db, fixed_price):
    account = Account.get("poor")
    with pytest.raises(ValueError):
        account.buy_shares("AAPL", 1000, "too much")


def test_sell_shares_updates_holdings(temp_db, fixed_price):
    account = Account.get("seller")
    account.buy_shares("AAPL", 10, "buy")
    account.sell_shares("AAPL", 4, "trim")
    assert account.holdings == {"AAPL": 6}


def test_sell_position_to_zero_removes_holding(temp_db, fixed_price):
    account = Account.get("closer")
    account.buy_shares("AAPL", 3, "buy")
    account.sell_shares("AAPL", 3, "exit")
    assert "AAPL" not in account.holdings


def test_sell_more_than_held_raises(temp_db, fixed_price):
    account = Account.get("greedy")
    account.buy_shares("AAPL", 2, "buy")
    with pytest.raises(ValueError):
        account.sell_shares("AAPL", 5, "oops")


def test_portfolio_value_and_pnl(temp_db, fixed_price):
    account = Account.get("valuer")
    account.buy_shares("AAPL", 10, "buy")
    value = account.calculate_portfolio_value()
    assert value == pytest.approx(account.balance + FIXED_PRICE * 10)
    # Only cost incurred is the spread paid on entry.
    pnl = account.calculate_profit_loss(value)
    assert pnl == pytest.approx(-FIXED_PRICE * accounts.SPREAD * 10)


def test_get_persists_and_reloads(temp_db, fixed_price):
    account = Account.get("persist")
    account.buy_shares("AAPL", 5, "buy")
    reloaded = Account.get("persist")
    assert reloaded.holdings == {"AAPL": 5}
    assert reloaded.balance == pytest.approx(account.balance)
