"""
Unit tests for CAGR Engine & 6 Edge Case Handlers.
Sprint 2 — Financial Ratio Engine
"""

import pytest
from src.analytics.cagr import calculate_cagr, compute_series_cagr


def test_cagr_positive_to_positive_normal():
    # 100 to 200 in 5 years -> ((200/100)^(1/5) - 1)*100 = 14.8698%
    val, flag = calculate_cagr(100.0, 200.0, 5)
    assert val == pytest.approx(14.8698, rel=1e-4)
    assert flag is None


def test_cagr_3yr_normal():
    # 1000 to 1331 in 3 years -> 10.0%
    val, flag = calculate_cagr(1000.0, 1331.0, 3)
    assert val == pytest.approx(10.0, rel=1e-4)
    assert flag is None


def test_cagr_10yr_normal():
    # 100 to 259.374 in 10 years -> 10.0%
    val, flag = calculate_cagr(100.0, 259.374246, 10)
    assert val == pytest.approx(10.0, rel=1e-4)
    assert flag is None


def test_cagr_positive_to_negative_decline_to_loss():
    val, flag = calculate_cagr(100.0, -50.0, 5)
    assert val is None
    assert flag == "DECLINE_TO_LOSS"


def test_cagr_negative_to_positive_turnaround():
    val, flag = calculate_cagr(-50.0, 100.0, 5)
    assert val is None
    assert flag == "TURNAROUND"


def test_cagr_both_negative():
    val, flag = calculate_cagr(-100.0, -50.0, 5)
    assert val is None
    assert flag == "BOTH_NEGATIVE"


def test_cagr_zero_base():
    val, flag = calculate_cagr(0.0, 100.0, 5)
    assert val is None
    assert flag == "ZERO_BASE"


def test_cagr_insufficient_or_none():
    val, flag = calculate_cagr(None, 100.0, 5)
    assert val is None
    assert flag == "INSUFFICIENT"


def test_compute_series_cagr_success():
    series = {
        "2019": 100.0,
        "2020": 110.0,
        "2021": 125.0,
        "2022": 140.0,
        "2023": 160.0,
        "2024": 200.0
    }
    # 5-yr CAGR from 2019 (100) to 2024 (200) -> 14.87%
    val, flag = compute_series_cagr(series, "2024", 5)
    assert val == pytest.approx(14.8698, rel=1e-4)
    assert flag is None


def test_compute_series_cagr_missing_gap_insufficient():
    series = {
        "2020": 110.0,
        "2021": 125.0,
        "2022": 140.0,
        "2023": 160.0,
        "2024": 200.0
    }
    # 2019 does not exist in series -> returns INSUFFICIENT
    val, flag = compute_series_cagr(series, "2024", 5)
    assert val is None
    assert flag == "INSUFFICIENT"


def test_compute_series_cagr_ttm_insufficient():
    series = {"2024": 200.0, "TTM": 220.0}
    val, flag = compute_series_cagr(series, "TTM", 5)
    assert val is None
    assert flag == "INSUFFICIENT"
