"""
Tests for Sprint 6 — Day 37: Cluster Profiling.

Validates:
  - Cluster profile schema (CSV columns, row count = 5)
  - Cluster membership consistency with Day-36 cluster_labels.csv
  - All clustering features present in profile
  - Mean/median columns exist for each feature
  - Company lists match cluster_labels.csv assignments
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
    CLUSTERING_FEATURES,
    TEN_KPIs,
    Day37Pipeline,
    build_cluster_profile,
    load_full_dataset,
)

# ── Fixtures ────────────────────────────────────────────────────────────────
SPRINT1_ROOT = SPRINT6_ROOT.parent / "Sprint-01-Data-Foundation"
SPRINT5_ROOT = SPRINT6_ROOT.parent / "Sprint-05-Intelligence-NLP-PDF-Reports"
DB_PATH = SPRINT1_ROOT / "nifty100.db"
CASHFLOW_PATH = SPRINT5_ROOT / "output" / "cashflow_intelligence.xlsx"
CLUSTER_CSV = SPRINT6_ROOT / "output" / "cluster_labels.csv"
PROFILE_CSV = SPRINT6_ROOT / "output" / "cluster_profile.csv"


@pytest.fixture(scope="module")
def full_dataset():
    return load_full_dataset(DB_PATH, CASHFLOW_PATH, CLUSTER_CSV)


@pytest.fixture(scope="module")
def cluster_profile(full_dataset):
    return build_cluster_profile(full_dataset)


@pytest.fixture(scope="module")
def cluster_labels():
    return pd.read_csv(CLUSTER_CSV)


# ── Profile Schema Tests ────────────────────────────────────────────────────


class TestProfileSchema:
    def test_profile_is_dataframe(self, cluster_profile):
        assert isinstance(cluster_profile, pd.DataFrame)

    def test_profile_row_count(self, cluster_profile):
        assert len(cluster_profile) == 5

    def test_profile_has_required_columns(self, cluster_profile):
        required = {"cluster_id", "cluster_name", "company_count", "companies"}
        assert required.issubset(set(cluster_profile.columns))

    def test_cluster_ids_are_0_through_4(self, cluster_profile):
        ids = sorted(cluster_profile["cluster_id"].tolist())
        assert ids == [0, 1, 2, 3, 4]

    def test_company_count_sums_to_92(self, cluster_profile):
        assert cluster_profile["company_count"].sum() == 92


# ── Feature Completeness Tests ──────────────────────────────────────────────


class TestFeatureCompleteness:
    def test_mean_columns_exist(self, cluster_profile):
        for feat in CLUSTERING_FEATURES:
            col = f"{feat}_mean"
            assert col in cluster_profile.columns, f"Missing column: {col}"

    def test_median_columns_exist(self, cluster_profile):
        for feat in CLUSTERING_FEATURES:
            col = f"{feat}_median"
            assert col in cluster_profile.columns, f"Missing column: {col}"

    def test_mean_values_are_numeric(self, cluster_profile):
        for feat in CLUSTERING_FEATURES:
            col = f"{feat}_mean"
            vals = cluster_profile[col].dropna()
            assert all(isinstance(v, (int, float, np.floating)) for v in vals)


# ── Membership Consistency Tests ────────────────────────────────────────────


class TestMembershipConsistency:
    def test_companies_in_profile_match_labels(self, cluster_profile, cluster_labels):
        profile_companies = set()
        for companies_str in cluster_profile["companies"]:
            profile_companies.update(c.strip() for c in companies_str.split(","))
        label_companies = set(cluster_labels["company_id"])
        assert profile_companies == label_companies

    def test_company_counts_match_labels(self, cluster_profile, cluster_labels):
        label_counts = cluster_labels["cluster_id"].value_counts().to_dict()
        for _, row in cluster_profile.iterrows():
            cid = row["cluster_id"]
            assert row["company_count"] == label_counts.get(
                cid, 0
            ), f"Cluster {cid}: profile count {row['company_count']} != label count {label_counts.get(cid, 0)}"

    def test_each_cluster_has_at_least_one_company(self, cluster_profile):
        assert all(cluster_profile["company_count"] >= 1)


# ── KPI Data Tests ──────────────────────────────────────────────────────────


class TestKPIData:
    def test_full_dataset_has_92_rows(self, full_dataset):
        assert len(full_dataset) == 92

    def test_full_dataset_has_all_kpis(self, full_dataset):
        for kpi in TEN_KPIs:
            assert kpi in full_dataset.columns, f"Missing KPI: {kpi}"

    def test_full_dataset_has_cluster_columns(self, full_dataset):
        assert "cluster_id" in full_dataset.columns
        assert "cluster_name" in full_dataset.columns

    def test_full_dataset_has_sector(self, full_dataset):
        assert "broad_sector" in full_dataset.columns
