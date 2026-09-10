"""
Tests for Sprint 6 — Day 37: Portfolio Statistics.

Validates:
  - Output schema (10 rows, correct columns)
  - Percentile ordering (P10 ≤ P25 ≤ P50 ≤ P75 ≤ P90)
  - NaN handling documentation (n_valid + n_missing)
  - Mean/Std computed correctly for known values
  - No missing KPIs
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# ── Path setup ──────────────────────────────────────────────────────────────
SPRINT6_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = SPRINT6_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from analytics.day37 import (
    TEN_KPIs,
    KPI_LABELS,
    compute_portfolio_stats,
    load_full_dataset,
)

# ── Fixtures ────────────────────────────────────────────────────────────────
SPRINT1_ROOT = SPRINT6_ROOT.parent / "Sprint-01-Data-Foundation"
SPRINT5_ROOT = SPRINT6_ROOT.parent / "Sprint-05-Intelligence-NLP-PDF-Reports"
DB_PATH = SPRINT1_ROOT / "nifty100.db"
CASHFLOW_PATH = SPRINT5_ROOT / "output" / "cashflow_intelligence.xlsx"
CLUSTER_CSV = SPRINT6_ROOT / "output" / "cluster_labels.csv"


@pytest.fixture(scope="module")
def full_dataset():
    return load_full_dataset(DB_PATH, CASHFLOW_PATH, CLUSTER_CSV)


@pytest.fixture(scope="module")
def portfolio_stats(full_dataset):
    return compute_portfolio_stats(full_dataset)


# ── Schema Tests ────────────────────────────────────────────────────────────


class TestPortfolioSchema:
    def test_stats_is_dataframe(self, portfolio_stats):
        assert isinstance(portfolio_stats, pd.DataFrame)

    def test_stats_has_10_rows(self, portfolio_stats):
        assert len(portfolio_stats) == 10

    def test_stats_has_required_columns(self, portfolio_stats):
        required = {
            "metric",
            "metric_label",
            "n_valid",
            "n_missing",
            "p10",
            "p25",
            "p50",
            "p75",
            "p90",
            "mean",
            "std",
        }
        assert required.issubset(set(portfolio_stats.columns))

    def test_all_kpis_present(self, portfolio_stats):
        metrics = set(portfolio_stats["metric"])
        assert metrics == set(TEN_KPIs)


# ── Percentile Ordering Tests ───────────────────────────────────────────────


class TestPercentileOrdering:
    def _check_ordering(self, row):
        """P10 ≤ P25 ≤ P50 ≤ P75 ≤ P90 (ignoring NaN)."""
        vals = [row["p10"], row["p25"], row["p50"], row["p75"], row["p90"]]
        valid = [v for v in vals if not np.isnan(v)]
        return valid == sorted(valid)

    def test_percentiles_ordered_for_each_kpi(self, portfolio_stats):
        for _, row in portfolio_stats.iterrows():
            assert self._check_ordering(row), (
                f"{row['metric']}: percentiles not ordered. "
                f"P10={row['p10']}, P25={row['p25']}, P50={row['p50']}, "
                f"P75={row['p75']}, P90={row['p90']}"
            )


# ── NaN Handling Tests ──────────────────────────────────────────────────────


class TestNaNHandling:
    def test_n_valid_plus_n_missing_equals_92(self, portfolio_stats):
        for _, row in portfolio_stats.iterrows():
            assert (
                row["n_valid"] + row["n_missing"] == 92
            ), f"{row['metric']}: n_valid={row['n_valid']} + n_missing={row['n_missing']} != 92"

    def test_n_valid_at_least_80(self, portfolio_stats):
        for _, row in portfolio_stats.iterrows():
            assert (
                row["n_valid"] >= 80
            ), f"{row['metric']}: n_valid={row['n_valid']} < 80"

    def test_missing_kpi_documented(self, portfolio_stats):
        # fcf_cagr_5yr is not in the 10 KPIs (only in clustering features)
        # operating_profit_margin_pct has 1 missing
        # return_on_equity_pct has 1 missing
        # debt_to_equity has 1 missing
        # return_on_capital_employed_pct has 2 missing
        for _, row in portfolio_stats.iterrows():
            if row["n_missing"] > 0:
                assert (
                    row["n_missing"] <= 5
                ), f"{row['metric']}: unexpected high missing count = {row['n_missing']}"


# ── Statistical Accuracy Tests ──────────────────────────────────────────────


class TestStatisticalAccuracy:
    def test_mean_matches_manual_calc(self, full_dataset, portfolio_stats):
        for _, row in portfolio_stats.iterrows():
            kpi = row["metric"]
            vals = full_dataset[kpi].dropna()
            expected_mean = vals.mean()
            assert (
                abs(row["mean"] - expected_mean) < 1e-4
            ), f"{kpi}: mean={row['mean']} != {expected_mean}"

    def test_std_matches_manual_calc(self, full_dataset, portfolio_stats):
        for _, row in portfolio_stats.iterrows():
            kpi = row["metric"]
            vals = full_dataset[kpi].dropna()
            if len(vals) > 1:
                expected_std = vals.std()
                assert (
                    abs(row["std"] - expected_std) < 1e-4
                ), f"{kpi}: std={row['std']} != {expected_std}"

    def test_p50_matches_median(self, full_dataset, portfolio_stats):
        for _, row in portfolio_stats.iterrows():
            kpi = row["metric"]
            vals = full_dataset[kpi].dropna()
            expected_p50 = vals.median()
            assert (
                abs(row["p50"] - expected_p50) < 1e-4
            ), f"{kpi}: p50={row['p50']} != median={expected_p50}"
