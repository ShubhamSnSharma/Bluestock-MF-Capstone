"""
Unit tests for Profitability, Leverage, and Efficiency Ratios.
Sprint 2 — Financial Ratio Engine
"""

import pytest
from src.analytics.ratios import (
    compute_net_profit_margin,
    compute_operating_profit_margin,
    compute_return_on_equity,
    compute_return_on_capital_employed,
    compute_return_on_assets,
    compute_debt_to_equity,
    compute_interest_coverage,
    compute_net_debt,
    compute_asset_turnover,
)


def test_npm_normal():
    # Net Profit 150 Cr, Sales 1000 Cr -> 15.0%
    assert compute_net_profit_margin(150.0, 1000.0) == pytest.approx(15.0)


def test_npm_zero_sales():
    assert compute_net_profit_margin(50.0, 0.0) is None
    assert compute_net_profit_margin(50.0, None) is None


def test_opm_normal_and_match():
    # Operating Profit 200 Cr, Sales 1000 Cr -> 20.0%
    val, anomaly = compute_operating_profit_margin(200.0, 1000.0, reported_opm=20.0)
    assert val == pytest.approx(20.0)
    assert anomaly is None


def test_opm_zero_sales():
    val, anomaly = compute_operating_profit_margin(50.0, 0.0)
    assert val is None
    assert anomaly is None


def test_opm_anomaly_mismatch():
    # Calculated 20.0%, Reported 25.0% -> Anomaly (>1%)
    val, anomaly = compute_operating_profit_margin(200.0, 1000.0, reported_opm=25.0)
    assert val == pytest.approx(20.0)
    assert anomaly is not None
    assert anomaly["difference"] == pytest.approx(5.0)
    assert anomaly["category"] == "FORMULA_DISCREPANCY"


def test_roe_normal():
    # Net profit 200 Cr, Equity 100 Cr, Reserves 900 Cr -> Net Worth 1000 Cr -> 20.0%
    assert compute_return_on_equity(200.0, 100.0, 900.0) == pytest.approx(20.0)


def test_roe_negative_or_zero_equity():
    # Net worth = 100 + (-200) = -100 <= 0 -> None
    assert compute_return_on_equity(50.0, 100.0, -200.0) is None
    assert compute_return_on_equity(50.0, 100.0, -100.0) is None


def test_roce_normal():
    # EBIT = 250 + 50 = 300 Cr, Capital Employed = 100 + 400 + 500 = 1000 Cr -> 30.0%
    assert compute_return_on_capital_employed(250.0, 50.0, 100.0, 400.0, 500.0) == pytest.approx(30.0)


def test_roce_negative_or_zero_capital_employed():
    assert compute_return_on_capital_employed(100.0, 10.0, 50.0, -100.0, 20.0) is None


def test_roa_normal():
    # Net profit 120 Cr, Total Assets 1200 Cr -> 10.0%
    assert compute_return_on_assets(120.0, 1200.0) == pytest.approx(10.0)


def test_roa_zero_assets():
    assert compute_return_on_assets(120.0, 0.0) is None
    assert compute_return_on_assets(120.0, -10.0) is None


def test_debt_to_equity_debt_free():
    # Borrowings = 0 -> returns (0.0, False)
    val, flag = compute_debt_to_equity(0.0, 100.0, 500.0)
    assert val == 0.0
    assert flag is False


def test_debt_to_equity_normal():
    # Borrowings 500 Cr, Net worth 1000 Cr -> 0.5
    val, flag = compute_debt_to_equity(500.0, 100.0, 900.0)
    assert val == pytest.approx(0.5)
    assert flag is False


def test_debt_to_equity_high_leverage_non_financial():
    # Borrowings 6000 Cr, Net worth 1000 Cr -> D/E = 6.0 (> 5.0) -> high_leverage_flag = True
    val, flag = compute_debt_to_equity(6000.0, 100.0, 900.0, is_financial=False)
    assert val == pytest.approx(6.0)
    assert flag is True


def test_debt_to_equity_financial_carve_out():
    # Financial sector company with high D/E -> flag is suppressed
    val, flag = compute_debt_to_equity(6000.0, 100.0, 900.0, is_financial=True)
    assert val == pytest.approx(6.0)
    assert flag is False


def test_icr_normal():
    # EBIT = 300 + 50 = 350 Cr, Interest = 70 Cr -> ICR = 5.0 (No warning)
    val, label, warning = compute_interest_coverage(300.0, 50.0, 70.0)
    assert val == pytest.approx(5.0)
    assert label is None
    assert warning is False


def test_icr_zero_interest_debt_free():
    # Interest = 0 -> (None, "Debt Free", False)
    val, label, warning = compute_interest_coverage(300.0, 50.0, 0.0)
    assert val is None
    assert label == "Debt Free"
    assert warning is False


def test_icr_warning_flag():
    # EBIT = 100 Cr, Interest = 100 Cr -> ICR = 1.0 (< 1.5) -> warning = True
    val, label, warning = compute_interest_coverage(100.0, 0.0, 100.0)
    assert val == pytest.approx(1.0)
    assert label is None
    assert warning is True


def test_net_debt_computation():
    # Borrowings 1000 Cr, Investments 400 Cr -> Net Debt 600 Cr
    assert compute_net_debt(1000.0, 400.0) == pytest.approx(600.0)
    # Borrowings 200 Cr, Investments 500 Cr -> Net Debt -300 Cr (Cash positive)
    assert compute_net_debt(200.0, 500.0) == pytest.approx(-300.0)


def test_asset_turnover():
    # Sales 1500 Cr, Total Assets 1000 Cr -> 1.5
    assert compute_asset_turnover(1500.0, 1000.0) == pytest.approx(1.5)
    assert compute_asset_turnover(1500.0, 0.0) is None
