"""
test_valuation.py — Unit tests for Sprint 4 valuation module.
Tests FCF yield logic, P/E flag logic, output schema, and data quality.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

# Ensure src/ is importable from tests/
_SPRINT4 = Path(__file__).resolve().parents[1]
if str(_SPRINT4 / "src") not in sys.path:
    sys.path.insert(0, str(_SPRINT4 / "src"))

from analytics.valuation import (
    compute_valuation,
    CAUTION_MULTIPLIER,
    DISCOUNT_MULTIPLIER,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def valuation_df() -> pd.DataFrame:
    """Run the full valuation engine once for the test session."""
    return compute_valuation()


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

class TestSchema:
    REQUIRED_COLS = [
        "company_id", "company_name", "sector",
        "P/E", "P/B", "EV/EBITDA",
        "FCF_yield_pct", "5yr_median_PE", "sector_median_PE",
        "PE_vs_sector_median_pct", "flag",
    ]

    def test_required_columns_present(self, valuation_df):
        missing = [c for c in self.REQUIRED_COLS if c not in valuation_df.columns]
        assert not missing, f"Missing columns: {missing}"

    def test_row_count_equals_92(self, valuation_df):
        assert len(valuation_df) == 92, (
            f"Expected 92 rows, got {len(valuation_df)}"
        )

    def test_no_duplicate_company_ids(self, valuation_df):
        dupes = valuation_df["company_id"].duplicated().sum()
        assert dupes == 0, f"Found {dupes} duplicate company_id rows"

    def test_flag_values_are_valid(self, valuation_df):
        valid = {"Caution", "Discount", "Fair"}
        actual = set(valuation_df["flag"].unique())
        assert actual.issubset(valid), f"Unexpected flag values: {actual - valid}"

    def test_all_companies_have_flag(self, valuation_df):
        nulls = valuation_df["flag"].isna().sum()
        assert nulls == 0, f"Found {nulls} rows with null flag"

    def test_company_name_not_null(self, valuation_df):
        nulls = valuation_df["company_name"].isna().sum()
        assert nulls == 0, f"Found {nulls} rows with null company_name"

    def test_sector_not_null(self, valuation_df):
        nulls = valuation_df["sector"].isna().sum()
        assert nulls == 0, f"Found {nulls} rows with null sector"


# ---------------------------------------------------------------------------
# FCF Yield tests
# ---------------------------------------------------------------------------

class TestFCFYield:
    def test_fcf_yield_formula(self):
        """FCF yield = (FCF / Market Cap) × 100"""
        fcf = 500.0
        mc  = 10000.0
        expected = (fcf / mc) * 100   # = 5.0
        assert abs(expected - 5.0) < 1e-9

    def test_fcf_yield_negative_fcf(self):
        """Negative FCF should produce negative yield."""
        fcf = -200.0
        mc  = 5000.0
        yield_pct = (fcf / mc) * 100
        assert yield_pct < 0

    def test_fcf_yield_zero_market_cap_returns_none(self, valuation_df):
        """Zero or null market cap must not cause division errors."""
        # All rows should have a valid FCF_yield_pct or None — never inf/NaN from /0
        inf_rows = valuation_df[
            valuation_df["FCF_yield_pct"].apply(
                lambda x: x is not None and (x != x or abs(x) == float("inf"))
            )
        ]
        assert len(inf_rows) == 0, f"Found inf/NaN FCF yields: {inf_rows['company_id'].tolist()}"

    def test_fcf_yield_present_for_most_companies(self, valuation_df):
        """At least 80 of 92 companies should have a non-null FCF yield."""
        non_null = valuation_df["FCF_yield_pct"].notna().sum()
        assert non_null >= 80, f"Only {non_null} companies have FCF yield data"


# ---------------------------------------------------------------------------
# P/E Flag logic tests
# ---------------------------------------------------------------------------

class TestPEFlags:
    def test_caution_threshold(self):
        """P/E > sector_median × 1.5 → Caution"""
        sector_med = 20.0
        pe_caution = sector_med * CAUTION_MULTIPLIER + 0.1
        assert pe_caution > sector_med * CAUTION_MULTIPLIER

    def test_discount_threshold(self):
        """P/E < sector_median × 0.7 → Discount"""
        sector_med = 20.0
        pe_discount = sector_med * DISCOUNT_MULTIPLIER - 0.1
        assert pe_discount < sector_med * DISCOUNT_MULTIPLIER

    def test_fair_band(self):
        """P/E between 0.7× and 1.5× sector median → Fair"""
        sector_med = 20.0
        pe_fair    = sector_med * 1.0
        assert sector_med * DISCOUNT_MULTIPLIER <= pe_fair <= sector_med * CAUTION_MULTIPLIER

    def test_caution_companies_have_high_pe(self, valuation_df):
        """All 'Caution' rows must have P/E > sector_median_PE × 1.5."""
        caution = valuation_df[valuation_df["flag"] == "Caution"].dropna(
            subset=["P/E", "sector_median_PE"]
        )
        for _, row in caution.iterrows():
            threshold = row["sector_median_PE"] * CAUTION_MULTIPLIER
            assert row["P/E"] > threshold, (
                f"{row['company_id']}: P/E={row['P/E']:.1f} should be > "
                f"sector_median×1.5={threshold:.1f}"
            )

    def test_discount_companies_have_low_pe(self, valuation_df):
        """All 'Discount' rows must have P/E < sector_median_PE × 0.7."""
        discount = valuation_df[valuation_df["flag"] == "Discount"].dropna(
            subset=["P/E", "sector_median_PE"]
        )
        for _, row in discount.iterrows():
            threshold = row["sector_median_PE"] * DISCOUNT_MULTIPLIER
            assert row["P/E"] < threshold, (
                f"{row['company_id']}: P/E={row['P/E']:.1f} should be < "
                f"sector_median×0.7={threshold:.1f}"
            )

    def test_fair_companies_within_band(self, valuation_df):
        """All 'Fair' rows with non-null P/E must be within the [0.7×, 1.5×] band."""
        fair = valuation_df[valuation_df["flag"] == "Fair"].dropna(
            subset=["P/E", "sector_median_PE"]
        )
        for _, row in fair.iterrows():
            lo = row["sector_median_PE"] * DISCOUNT_MULTIPLIER
            hi = row["sector_median_PE"] * CAUTION_MULTIPLIER
            assert lo <= row["P/E"] <= hi, (
                f"{row['company_id']}: P/E={row['P/E']:.1f} outside Fair band [{lo:.1f}, {hi:.1f}]"
            )

    def test_flag_distribution_sanity(self, valuation_df):
        """At least 1 company in each flag category (data permitting)."""
        counts = valuation_df["flag"].value_counts()
        for flag in ("Caution", "Discount", "Fair"):
            assert counts.get(flag, 0) >= 1, f"No companies with flag={flag}"


# ---------------------------------------------------------------------------
# PE vs Sector Median % tests
# ---------------------------------------------------------------------------

class TestPEVsMedian:
    def test_pe_vs_median_formula(self):
        """PE_vs_sector_median_pct = ((PE - median) / median) × 100"""
        pe, med = 30.0, 20.0
        expected = ((pe - med) / med) * 100  # = 50.0
        assert abs(expected - 50.0) < 1e-9

    def test_caution_rows_have_positive_vs_median(self, valuation_df):
        """Caution companies should have PE_vs_sector_median_pct > 0."""
        caution = valuation_df[
            (valuation_df["flag"] == "Caution")
            & valuation_df["PE_vs_sector_median_pct"].notna()
        ]
        assert all(caution["PE_vs_sector_median_pct"] > 0), (
            "Some Caution companies have non-positive PE_vs_sector_median_pct"
        )

    def test_discount_rows_have_negative_vs_median(self, valuation_df):
        """Discount companies should have PE_vs_sector_median_pct < 0."""
        discount = valuation_df[
            (valuation_df["flag"] == "Discount")
            & valuation_df["PE_vs_sector_median_pct"].notna()
        ]
        assert all(discount["PE_vs_sector_median_pct"] < 0), (
            "Some Discount companies have non-negative PE_vs_sector_median_pct"
        )


# ---------------------------------------------------------------------------
# Output file tests
# ---------------------------------------------------------------------------

class TestOutputFiles:
    XLSX_PATH = (
        Path(__file__).resolve().parents[1] / "output" / "valuation_summary.xlsx"
    )
    CSV_PATH = (
        Path(__file__).resolve().parents[1] / "output" / "valuation_flags.csv"
    )

    def test_xlsx_file_exists(self):
        assert self.XLSX_PATH.exists(), f"valuation_summary.xlsx not found at {self.XLSX_PATH}"

    def test_csv_flags_file_exists(self):
        assert self.CSV_PATH.exists(), f"valuation_flags.csv not found at {self.CSV_PATH}"

    def test_xlsx_has_92_data_rows(self):
        df = pd.read_excel(self.XLSX_PATH, engine="openpyxl")
        assert len(df) == 92, f"Expected 92 rows, got {len(df)}"

    def test_xlsx_has_all_required_columns(self):
        df = pd.read_excel(self.XLSX_PATH, engine="openpyxl")
        required = ["company_id", "company_name", "sector", "P/E", "P/B",
                    "EV/EBITDA", "FCF_yield_pct", "flag"]
        missing = [c for c in required if c not in df.columns]
        assert not missing, f"xlsx missing columns: {missing}"

    def test_csv_flags_contains_only_caution_and_discount(self):
        df = pd.read_csv(self.CSV_PATH)
        assert not df.empty, "valuation_flags.csv is empty"
        assert set(df["flag"].unique()).issubset({"Caution", "Discount"}), (
            "valuation_flags.csv contains unexpected flag values"
        )

    def test_csv_flags_has_required_columns(self):
        df = pd.read_csv(self.CSV_PATH)
        required = ["company_id", "company_name", "sector", "P/E", "flag"]
        missing = [c for c in required if c not in df.columns]
        assert not missing, f"valuation_flags.csv missing columns: {missing}"
