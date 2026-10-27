import pandas as pd
import numpy as np
import pytest
from backtester_v3 import calculate_rsi, run_strategy

# ---------------- RSI TESTS ----------------

def test_calculate_rsi_values_between_0_and_100():
    prices = pd.Series([100, 101, 102, 101, 100, 99, 100, 101, 102, 103])
    rsi = calculate_rsi(prices, window=5).dropna()
    assert (rsi >= 0).all() and (rsi <= 100).all()


def test_calculate_rsi_handles_constant_prices():
    prices = pd.Series([100] * 20)
    rsi = calculate_rsi(prices, window=14).dropna()
    assert rsi.isna().all() or ((rsi >= 0) & (rsi <= 100)).all()


# ---------------- STRATEGY TESTS ----------------

@pytest.mark.parametrize("strategy", ["ma", "rsi"])
def test_run_strategy_returns_expected_outputs(strategy):
    df = pd.DataFrame({
        "Date": pd.date_range(start="2020-01-01", periods=100),
        "Price": np.linspace(100, 200, 100)
    }).set_index("Date")

    total_return, sharpe_ratio, equity_curve = run_strategy(df, strategy)

    assert isinstance(total_return, float)
    assert isinstance(sharpe_ratio, float)
    assert isinstance(equity_curve, pd.Series)
    assert len(equity_curve) == len(df)

