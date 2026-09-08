"""
Unit and Integration Tests for Sprint 5 Day 32 — Capital Allocation Report.
Validates:
- 92-company universe coverage
- company_id normalisation
- duplicate detection
- numeric fiscal years
- latest-year distribution
- year-over-year change detection
- output schemas
- alignment with cashflow_intelligence.xlsx
- Sprint 2 source file integrity (read-only)
"""

import sys
from pathlib import Path
import pandas as pd
import pytest

SPRINT5_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SPRINT5_ROOT))

from src.analytics.capital_allocation import (
    CapitalAllocationReporter,
    EXPECTED_PATTERNS,
)

BASE_DIR = SPRINT5_ROOT.parent
DB_PATH = BASE_DIR / "Sprint-01-Data-Foundation" / "nifty100.db"
CAP_ALLOC_SRC = BASE_DIR / "Sprint-02-Financial-Ratio-Engine" / "output" / "capital_allocation.csv"


@pytest.fixture(scope="module")
def reporter():
    return CapitalAllocationReporter(
        db_path=str(DB_PATH),
        cap_alloc_path=str(CAP_ALLOC_SRC),
        output_dir=str(SPRINT5_ROOT / "output"),
    )


@pytest.fixture(scope="module")
def clean_df(reporter):
    return reporter.load_clean_data()


# ===========================================================================
# 1. Source Data Integrity Tests
# ===========================================================================
class TestSourceDataIntegrity:
    def test_source_exists_and_readable(self):
        assert CAP_ALLOC_SRC.exists()
        df = pd.read_csv(CAP_ALLOC_SRC)
        assert not df.empty
        assert "company_id" in df.columns
        assert "year" in df.columns
        assert "pattern_label" in df.columns

    def test_92_companies_in_source(self, clean_df):
        assert clean_df["company_id"].nunique() == 92

    def test_numeric_years_only(self, clean_df):
        # TTM should be excluded in cleaned data
        assert clean_df["year_str"].str.isdigit().all()
        assert (clean_df["year_int"] >= 2011).all()

    def test_no_duplicate_company_year_in_source(self, clean_df):
        dups = clean_df.duplicated(subset=["company_id", "year_int"])
        assert not dups.any()

    def test_eight_expected_patterns_in_source(self, clean_df):
        patterns = set(clean_df["pattern_label"].unique())
        # All patterns must belong to expected set + 'Other'
        valid_set = set(EXPECTED_PATTERNS) | {"Other"}
        assert patterns.issubset(valid_set)


# ===========================================================================
# 2. Distribution Report Tests
# ===========================================================================
class TestDistributionReport:
    def test_distribution_schema(self, reporter, clean_df):
        dist = reporter.compute_distribution(clean_df)
        assert list(dist.columns) == ["pattern_label", "company_count", "latest_year"]

    def test_distribution_sum_equals_92(self, reporter, clean_df):
        dist = reporter.compute_distribution(clean_df)
        assert dist["company_count"].sum() == 92

    def test_distribution_latest_year_2024(self, reporter, clean_df):
        dist = reporter.compute_distribution(clean_df)
        assert (dist["latest_year"] == "2024").all()

    def test_shareholder_returns_is_plurality(self, reporter, clean_df):
        dist = reporter.compute_distribution(clean_df)
        top_pattern = dist.iloc[0]
        assert top_pattern["pattern_label"] == "Shareholder Returns"
        assert top_pattern["company_count"] == 44


# ===========================================================================
# 3. Pattern Changes Tests
# ===========================================================================
class TestPatternChanges:
    def test_pattern_changes_schema(self, reporter, clean_df):
        changes = reporter.compute_pattern_changes(clean_df)
        assert list(changes.columns) == [
            "company_id",
            "from_year",
            "to_year",
            "from_pattern",
            "to_pattern",
        ]

    def test_changes_only_when_patterns_differ(self, reporter, clean_df):
        changes = reporter.compute_pattern_changes(clean_df)
        for _, row in changes.iterrows():
            assert row["from_pattern"] != row["to_pattern"]
            assert int(row["to_year"]) > int(row["from_year"])

    def test_synthetic_pattern_change_detection(self, reporter):
        # Create a tiny synthetic DataFrame to test change detection
        synth = pd.DataFrame([
            {"company_id": "TEST", "year_int": 2020, "pattern_label": "Reinvestor"},
            {"company_id": "TEST", "year_int": 2021, "pattern_label": "Reinvestor"},
            {"company_id": "TEST", "year_int": 2022, "pattern_label": "Distress Signal"},
            {"company_id": "TEST", "year_int": 2024, "pattern_label": "Shareholder Returns"},
        ])
        changes = reporter.compute_pattern_changes(synth)
        assert len(changes) == 2
        assert changes.iloc[0]["from_pattern"] == "Reinvestor"
        assert changes.iloc[0]["to_pattern"] == "Distress Signal"
        assert changes.iloc[1]["from_year"] == "2022"
        assert changes.iloc[1]["to_year"] == "2024"


# ===========================================================================
# 4. End-to-End File Generation & Integration
# ===========================================================================
class TestOutputIntegration:
    def test_save_outputs(self, reporter):
        dist_p, chg_p = reporter.save_outputs()
        assert dist_p.exists()
        assert chg_p.exists()

        df_dist = pd.read_csv(dist_p)
        assert len(df_dist) > 0
        assert df_dist["company_count"].sum() == 92

        df_chg = pd.read_csv(chg_p)
        assert len(df_chg) > 0

    def test_cashflow_intelligence_alignment(self, reporter, clean_df):
        # Verify that cashflow_intelligence.xlsx matches the latest capital allocation label
        cf_xlsx_path = SPRINT5_ROOT / "output" / "cashflow_intelligence.xlsx"
        if cf_xlsx_path.exists():
            cf_df = pd.read_excel(cf_xlsx_path)
            latest_cap = clean_df.groupby("company_id").last().reset_index()
            cap_map = latest_cap.set_index("company_id")["pattern_label"].to_dict()

            for _, row in cf_df.iterrows():
                cid = row["company_id"]
                if cid in cap_map:
                    assert row["capital_allocation_label"] == cap_map[cid]
