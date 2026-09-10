"""
Tests for Sprint 6 — Day 37: Sector-Level Outlier Detection.

Validates:
  - Output schema (correct columns, all 10 KPIs × 92 companies)
  - Z-score calculation within sectors
  - Outlier flagging threshold (|Z| > 3)
  - Edge cases: insufficient sector observations, zero std
  - No false positives (non-outliers have |Z| ≤ 3)
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
    OUTLIER_Z_THRESHOLD,
    TEN_KPIs,
    detect_sector_outliers,
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
def outlier_df(full_dataset):
    return detect_sector_outliers(full_dataset)


# ── Schema Tests ────────────────────────────────────────────────────────────


class TestOutlierSchema:
    def test_outlier_is_dataframe(self, outlier_df):
        assert isinstance(outlier_df, pd.DataFrame)

    def test_required_columns_exist(self, outlier_df):
        required = {
            "company_id",
            "broad_sector",
            "cluster_id",
            "metric",
            "metric_label",
            "metric_value",
            "sector_mean",
            "sector_std",
            "sector_count",
            "z_score",
            "abs_z_score",
            "outlier_flag",
            "handling",
        }
        assert required.issubset(set(outlier_df.columns))

    def test_all_kpis_present(self, outlier_df):
        metrics = set(outlier_df["metric"].unique())
        assert metrics == set(TEN_KPIs)

    def test_row_count_is_companies_times_kpis(self, outlier_df, full_dataset):
        # Expects 92 companies × 10 KPIs = 920 rows (minus any NaN values)
        assert len(outlier_df) >= 90 * 10  # At least 900 rows


# ── Z-Score Calculation Tests ──────────────────────────────────────────────


class TestZScoreCalculation:
    def test_z_scores_within_threshold_are_not_outliers(self, outlier_df):
        computed = outlier_df[outlier_df["handling"] == "computed"]
        non_outliers = computed[~computed["outlier_flag"]]
        assert all(non_outliers["abs_z_score"] <= OUTLIER_Z_THRESHOLD + 1e-10)

    def test_outlier_flag_implies_high_z_score(self, outlier_df):
        outliers = outlier_df[outlier_df["outlier_flag"]]
        assert all(outliers["abs_z_score"] > OUTLIER_Z_THRESHOLD - 1e-10)

    def test_z_score_sign_matches_deviation(self, outlier_df):
        computed = outlier_df[outlier_df["handling"] == "computed"]
        # Positive Z means value > sector mean
        positive_z = computed[computed["z_score"] > 0]
        assert all(positive_z["metric_value"] > positive_z["sector_mean"] - 1e-6)

        negative_z = computed[computed["z_score"] < 0]
        assert all(negative_z["metric_value"] < negative_z["sector_mean"] + 1e-6)


# ── Edge Case Tests ─────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_insufficient_sector_observations_handled(self, outlier_df):
        small_sector = outlier_df[
            outlier_df["handling"] == "insufficient_sector_observations"
        ]
        if len(small_sector) > 0:
            assert all(small_sector["sector_count"] < 3)
            assert all(pd.isna(small_sector["z_score"]))
            assert all(~small_sector["outlier_flag"])

    def test_zero_std_handled(self, outlier_df):
        zero_std = outlier_df[outlier_df["handling"] == "zero_std"]
        if len(zero_std) > 0:
            assert all(zero_std["sector_std"] == 0.0)
            assert all(zero_std["z_score"] == 0.0)
            assert all(~zero_std["outlier_flag"])

    def test_no_nans_in_outlier_flag(self, outlier_df):
        assert not outlier_df["outlier_flag"].isna().any()

    def test_handling_values_are_valid(self, outlier_df):
        valid = {"computed", "insufficient_sector_observations", "zero_std"}
        assert set(outlier_df["handling"].unique()).issubset(valid)


# ── Outlier Count Tests ────────────────────────────────────────────────────


class TestOutlierCounts:
    def test_outlier_count_reasonable(self, outlier_df):
        n_outliers = outlier_df["outlier_flag"].sum()
        # Should be small number of true outliers
        assert 5 <= n_outliers <= 30

    def test_no_company_is_outlier_on_all_kpis(self, outlier_df):
        outliers = outlier_df[outlier_df["outlier_flag"]]
        company_outlier_counts = outliers.groupby("company_id").size()
        assert all(company_outlier_counts <= 5)  # No company outlier on >5 KPIs
