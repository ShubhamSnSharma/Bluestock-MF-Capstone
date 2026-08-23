"""
Unit tests for Cash Flow KPIs, Quality Scores, and Capital Allocation.
Sprint 2 — Financial Ratio Engine
"""

import pytest
from src.analytics.cashflow_kpis import (
    compute_free_cash_flow,
    compute_cfo_quality_score,
    compute_capex_intensity,
    compute_fcf_conversion_rate,
    classify_capital_allocation,
)


def test_free_cash_flow_normal():
    # CFO = 500 Cr, CFI = -200 Cr -> FCF = 300 Cr
    assert compute_free_cash_flow(500.0, -200.0) == pytest.approx(300.0)


def test_free_cash_flow_negative():
    # CFO = 100 Cr, CFI = -350 Cr -> FCF = -250 Cr
    assert compute_free_cash_flow(100.0, -350.0) == pytest.approx(-250.0)


def test_cfo_quality_score_high_quality():
    # 5-year CFO/PAT average = 1.25 -> High Quality
    pairs = [(120.0, 100.0), (130.0, 100.0), (110.0, 100.0), (140.0, 100.0), (125.0, 100.0)]
    score, label = compute_cfo_quality_score(pairs)
    assert score == pytest.approx(1.25)
    assert label == "High Quality"


def test_cfo_quality_score_moderate():
    # 5-year CFO/PAT average = 0.75 -> Moderate
    pairs = [(75.0, 100.0), (80.0, 100.0), (70.0, 100.0)]
    score, label = compute_cfo_quality_score(pairs)
    assert score == pytest.approx(0.75)
    assert label == "Moderate"


def test_cfo_quality_score_accrual_risk():
    # 5-year CFO/PAT average = 0.30 -> Accrual Risk
    pairs = [(30.0, 100.0), (25.0, 100.0), (35.0, 100.0)]
    score, label = compute_cfo_quality_score(pairs)
    assert score == pytest.approx(0.30)
    assert label == "Accrual Risk"


def test_cfo_quality_score_zero_pat_exclusion():
    # Exclude period where PAT == 0
    pairs = [(50.0, 0.0), (100.0, 100.0), (120.0, 100.0)]
    score, label = compute_cfo_quality_score(pairs)
    assert score == pytest.approx(1.10)
    assert label == "High Quality"


def test_capex_intensity_asset_light():
    # CFI = -20 Cr, Sales = 1000 Cr -> Intensity = 2.0% (<3%) -> Asset Light
    intensity, label = compute_capex_intensity(-20.0, 1000.0)
    assert intensity == pytest.approx(2.0)
    assert label == "Asset Light"


def test_capex_intensity_moderate():
    # CFI = -50 Cr, Sales = 1000 Cr -> Intensity = 5.0% (3-8%) -> Moderate
    intensity, label = compute_capex_intensity(-50.0, 1000.0)
    assert intensity == pytest.approx(5.0)
    assert label == "Moderate"


def test_capex_intensity_capital_intensive():
    # CFI = -120 Cr, Sales = 1000 Cr -> Intensity = 12.0% (>8%) -> Capital Intensive
    intensity, label = compute_capex_intensity(-120.0, 1000.0)
    assert intensity == pytest.approx(12.0)
    assert label == "Capital Intensive"


def test_fcf_conversion_rate():
    # FCF = 300 Cr, Operating Profit = 500 Cr -> 60.0%
    assert compute_fcf_conversion_rate(300.0, 500.0) == pytest.approx(60.0)
    assert compute_fcf_conversion_rate(300.0, 0.0) is None


def test_capital_allocation_patterns():
    # (+,-,-) with high CFO quality -> Shareholder Returns
    s_cfo, s_cfi, s_cff, label = classify_capital_allocation(500.0, -200.0, -100.0, cfo_quality_score=1.2)
    assert (s_cfo, s_cfi, s_cff) == ("+", "-", "-")
    assert label == "Shareholder Returns"

    # (+,-,-) with moderate CFO quality -> Reinvestor
    s_cfo, s_cfi, s_cff, label = classify_capital_allocation(500.0, -200.0, -100.0, cfo_quality_score=0.8)
    assert label == "Reinvestor"

    # (+,+,-) -> Liquidating Assets
    assert classify_capital_allocation(300.0, 100.0, -50.0)[3] == "Liquidating Assets"

    # (-,+,+) -> Distress Signal
    assert classify_capital_allocation(-100.0, 50.0, 80.0)[3] == "Distress Signal"

    # (-,-,+) -> Growth Funded by Debt
    assert classify_capital_allocation(-100.0, -200.0, 300.0)[3] == "Growth Funded by Debt"

    # (+,+,+) -> Cash Accumulator
    assert classify_capital_allocation(100.0, 50.0, 20.0)[3] == "Cash Accumulator"

    # (-,-,-) -> Pre-Revenue
    assert classify_capital_allocation(-50.0, -100.0, -20.0)[3] == "Pre-Revenue"

    # (+,-,+) -> Mixed
    assert classify_capital_allocation(100.0, -50.0, 30.0)[3] == "Mixed"
