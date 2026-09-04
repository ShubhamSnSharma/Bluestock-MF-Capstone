"""
test_performance.py — Profile data-loading performance QA.
Measures time to load all data for 5 tickers.
Target: < 3 seconds each (excluding Streamlit startup).
"""

from __future__ import annotations

import sys
import time
import types
import unittest.mock as mock
from pathlib import Path

import pytest

_SPRINT4 = Path(__file__).resolve().parents[1]
if str(_SPRINT4 / "src") not in sys.path:
    sys.path.insert(0, str(_SPRINT4 / "src"))


def _mock_st():
    st = types.ModuleType("streamlit")
    st.cache_data   = lambda **kw: (lambda f: f)
    st.session_state = {}
    return st


TICKERS = ["ADANIPORTS", "TCS", "HDFCBANK", "RELIANCE", "SUNPHARMA"]
TARGET_SECONDS = 3.0


@pytest.mark.parametrize("ticker", TICKERS)
def test_profile_data_load_under_3s(ticker):
    """
    Measure data-loading time for Company Profile screen.
    Loads: ratios, P&L, cash-flow, balance-sheet, pros/cons, market-cap.
    All queries must complete in under 3 seconds.
    """
    with mock.patch.dict("sys.modules", {"streamlit": _mock_st()}):
        from dashboard.utils.db import (
            get_ratios, get_pl, get_bs, get_cf, get_proscons,
            get_market_cap_all, get_documents,
        )

    start = time.perf_counter()

    ratios_df  = get_ratios(ticker=ticker)
    pl_df      = get_pl(ticker=ticker)
    bs_df      = get_bs(ticker=ticker)
    cf_df      = get_cf(ticker=ticker)
    pc_df      = get_proscons(ticker=ticker)
    mc_df      = get_market_cap_all(year="2024")
    docs_df    = get_documents(ticker=ticker)

    elapsed = time.perf_counter() - start

    assert elapsed < TARGET_SECONDS, (
        f"{ticker}: profile data load took {elapsed:.2f}s (target < {TARGET_SECONDS}s)"
    )
    assert not ratios_df.empty or not pl_df.empty, (
        f"{ticker}: no data returned from DB"
    )
