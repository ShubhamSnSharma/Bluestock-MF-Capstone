"""
tests/test_nlp_parser.py
=========================
Day 29 — Tests for the NLP Analysis Text Parser.

Validates the ACTUAL Sprint 5 specification:
  - Source: analysis.xlsx (not the DB analysis table)
  - Required output schema: company_id, metric_type, period_years, value_pct
  - Required metric_type values
  - Mandated regex pattern
  - Invalid text → parse_failures.csv
  - company_id normalisation (trim + uppercase)
  - period_years is numeric (0 for TTM entries)
  - 5-year CAGR cross-validation vs financial_ratios
  - >5pp divergence flagging
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd
import pytest

# ---------------------------------------------------------------------------
SPRINT5 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SPRINT5))

from src.nlp.parser import AnalysisParser, _parse_cell, _MULTI_YEAR_RE, _TTM_RE

XLSX_PATH = (
    Path(__file__).resolve().parents[2]
    / "Sprint-01-Data-Foundation"
    / "core datasets"
    / "analysis.xlsx"
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def parser():
    p = AnalysisParser()
    p.parse()
    return p


@pytest.fixture(scope="module")
def parsed_df(parser):
    return parser.parsed_df


@pytest.fixture(scope="module")
def failures_df(parser):
    return parser.failures_df


# ===========================================================================
# T01 — Source file: analysis.xlsx exists
# ===========================================================================
def test_xlsx_source_exists():
    assert XLSX_PATH.exists(), f"analysis.xlsx not found at {XLSX_PATH}"


# ===========================================================================
# T02 — Parser reads from xlsx, not the DB analysis table
# ===========================================================================
def test_source_is_xlsx(parser):
    assert str(parser.xlsx_path).endswith("analysis.xlsx")


# ===========================================================================
# T03-T10 — Mandated regex (_parse_cell unit tests)
# ===========================================================================
class TestRegex:

    def test_10yr_clean(self):
        period, pct, err = _parse_cell("10 Years: 21%", "X", "m")
        assert period == 10 and pct == pytest.approx(21.0) and err is None

    def test_5yr_whitespace(self):
        period, pct, err = _parse_cell("5 Years:       24%", "X", "m")
        assert period == 5 and pct == pytest.approx(24.0) and err is None

    def test_3yr_whitespace(self):
        period, pct, err = _parse_cell("3 Years:       17%", "X", "m")
        assert period == 3 and pct == pytest.approx(17.0) and err is None

    def test_ttm_returns_period_zero(self):
        period, pct, err = _parse_cell("TTM:            43%", "X", "m")
        assert period == 0 and pct == pytest.approx(43.0) and err is None

    def test_1yr_returns_period_zero(self):
        period, pct, err = _parse_cell("1 Year:         -2%", "X", "m")
        assert period == 0 and pct == pytest.approx(-2.0) and err is None

    def test_last_year_returns_period_zero(self):
        period, pct, err = _parse_cell("Last Year:      12%", "X", "m")
        assert period == 0 and pct == pytest.approx(12.0) and err is None

    def test_negative_percentage(self):
        _, pct, err = _parse_cell("3 Years:      -1%", "X", "m")
        assert pct == pytest.approx(-1.0) and err is None

    def test_decimal_percentage(self):
        _, pct, err = _parse_cell("5 Years: 9.5%", "X", "m")
        assert pct == pytest.approx(9.5) and err is None

    def test_extra_trailing_spaces(self):
        """Actual data contains '10 Years:     11%             '"""
        period, pct, err = _parse_cell("10 Years:     11%             ", "X", "m")
        assert period == 10 and pct == pytest.approx(11.0) and err is None

    def test_leading_spaces(self):
        period, pct, err = _parse_cell("     5 Years:       8%", "X", "m")
        assert period == 5 and pct == pytest.approx(8.0) and err is None

    def test_garbage_returns_failure(self):
        period, pct, err = _parse_cell("N/A", "X", "m")
        assert period is None and pct is None and err is not None

    def test_none_returns_failure(self):
        period, pct, err = _parse_cell(None, "X", "m")
        assert period is None and pct is None and err is not None

    def test_empty_string_returns_failure(self):
        period, pct, err = _parse_cell("   ", "X", "m")
        assert err is not None


# ===========================================================================
# T11 — Required output schema
# ===========================================================================
REQUIRED_COLS = {"company_id", "metric_type", "period_years", "value_pct"}

def test_output_schema(parsed_df):
    assert REQUIRED_COLS.issubset(set(parsed_df.columns)), (
        f"Missing columns: {REQUIRED_COLS - set(parsed_df.columns)}"
    )

def test_no_extra_legacy_columns(parsed_df):
    """Old schema columns must NOT exist in output."""
    old_cols = {"id", "csg_period", "csg_pct", "cpg_period", "cpg_pct",
                "spc_period", "spc_pct", "roe_period", "roe_pct", "parse_status"}
    present_old = old_cols & set(parsed_df.columns)
    assert not present_old, f"Old schema columns still present: {present_old}"


# ===========================================================================
# T12 — Required metric_type values
# ===========================================================================
REQUIRED_METRICS = {
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe",
}

def test_metric_types_correct(parsed_df):
    found = set(parsed_df["metric_type"].unique())
    assert REQUIRED_METRICS.issubset(found), (
        f"Missing metric_types: {REQUIRED_METRICS - found}"
    )

def test_no_unknown_metric_types(parsed_df):
    found = set(parsed_df["metric_type"].unique())
    unknown = found - REQUIRED_METRICS
    assert not unknown, f"Unknown metric_type values: {unknown}"


# ===========================================================================
# T13 — period_years is numeric (int/float)
# ===========================================================================
def test_period_years_numeric(parsed_df):
    assert pd.api.types.is_numeric_dtype(parsed_df["period_years"]), (
        "period_years must be numeric"
    )

def test_period_years_allowed_values(parsed_df):
    allowed = {0, 3, 5, 10}
    found   = set(parsed_df["period_years"].dropna().astype(int).unique())
    unknown = found - allowed
    assert not unknown, f"Unexpected period_years values: {unknown}"


# ===========================================================================
# T14 — value_pct is float
# ===========================================================================
def test_value_pct_float(parsed_df):
    assert pd.api.types.is_float_dtype(parsed_df["value_pct"])


# ===========================================================================
# T15 — company_id normalisation: trim + uppercase
# ===========================================================================
def test_company_id_normalised(parsed_df):
    for cid in parsed_df["company_id"]:
        assert cid == cid.strip().upper(), f"Not normalised: {cid!r}"


# ===========================================================================
# T16 — xlsx covers all 5 companies (WIPRO included)
# ===========================================================================
def test_xlsx_has_5_companies(parsed_df):
    assert parsed_df["company_id"].nunique() == 5


def test_wipro_present(parsed_df):
    """WIPRO exists in analysis.xlsx and must be parsed."""
    assert "WIPRO" in set(parsed_df["company_id"].unique())


# ===========================================================================
# T17 — Specific value correctness
# ===========================================================================
def test_hdfcbank_10yr_csg(parsed_df):
    row = parsed_df[
        (parsed_df["company_id"] == "HDFCBANK")
        & (parsed_df["metric_type"] == "compounded_sales_growth")
        & (parsed_df["period_years"] == 10)
    ]
    assert not row.empty
    assert row.iloc[0]["value_pct"] == pytest.approx(21.0)


def test_tcs_10yr_roe(parsed_df):
    row = parsed_df[
        (parsed_df["company_id"] == "TCS")
        & (parsed_df["metric_type"] == "roe")
        & (parsed_df["period_years"] == 10)
    ]
    assert not row.empty
    assert row.iloc[0]["value_pct"] == pytest.approx(40.0)


def test_wipro_10yr_cpg(parsed_df):
    row = parsed_df[
        (parsed_df["company_id"] == "WIPRO")
        & (parsed_df["metric_type"] == "compounded_profit_growth")
        & (parsed_df["period_years"] == 10)
    ]
    assert not row.empty
    assert row.iloc[0]["value_pct"] == pytest.approx(3.0)


def test_sbilife_ttm_period_zero(parsed_df):
    """TTM entries must produce period_years = 0."""
    row = parsed_df[
        (parsed_df["company_id"] == "SBILIFE")
        & (parsed_df["metric_type"] == "compounded_sales_growth")
        & (parsed_df["period_years"] == 0)
    ]
    assert not row.empty


# ===========================================================================
# T18 — parse_failures.csv schema
# ===========================================================================
def test_failures_schema(tmp_path, parser):
    """Verify parse_failures.csv has the required columns.
    Since all cells in this dataset parse successfully, we verify the
    schema through save_outputs (which always writes the header row)."""
    parser.save_outputs(output_dir=tmp_path)
    df = pd.read_csv(tmp_path / "parse_failures.csv")
    expected = {"company_id", "metric_type", "raw_value", "reason"}
    assert expected.issubset(set(df.columns)), (
        f"Missing columns: {expected - set(df.columns)}"
    )


# ===========================================================================
# T19 — Every unmatched cell must be logged
# ===========================================================================
def test_no_silent_drop(parser, parsed_df, failures_df):
    """parsed + failed == total cells processed from xlsx."""
    import warnings
    warnings.filterwarnings("ignore")
    xl = pd.read_excel(parser.xlsx_path, sheet_name="Analysis", header=1)
    total_cells = len(xl) * 4   # 4 metric columns per row
    assert len(parsed_df) + len(failures_df) == total_cells


# ===========================================================================
# T20-T22 — 5-Year CAGR Cross-Validation
# ===========================================================================
@pytest.fixture(scope="module")
def cross_val_df(parser):
    return parser.cross_validate()


def test_cross_val_returns_dataframe(cross_val_df):
    assert isinstance(cross_val_df, pd.DataFrame)


def test_cross_val_schema(cross_val_df):
    expected = {"company_id", "metric_type", "xlsx_value", "db_value",
                "divergence_pct", "flag_for_review"}
    assert expected.issubset(set(cross_val_df.columns))


def test_cross_val_divergence_all_within_10pp(cross_val_df):
    """
    For the current N100 dataset, no 5-year CAGR divergence should exceed 10pp.
    Divergences >5pp are flagged but still valid (manual review, not error).
    """
    if not cross_val_df.empty:
        assert (cross_val_df["divergence_pct"] < 10).all(), (
            f"Unexpectedly large divergences:\n"
            f"{cross_val_df[cross_val_df['divergence_pct'] >= 10]}"
        )


def test_cross_val_flags_above_5pp(cross_val_df):
    """flag_for_review must be True for divergence_pct > 5."""
    if not cross_val_df.empty:
        should_flag = cross_val_df["divergence_pct"] > 5
        assert (cross_val_df.loc[should_flag, "flag_for_review"]).all()


# ===========================================================================
# T23 — save_outputs writes correct files
# ===========================================================================
def test_save_outputs(tmp_path, parser):
    paths = parser.save_outputs(output_dir=tmp_path)
    assert (tmp_path / "analysis_parsed.csv").exists()
    assert (tmp_path / "parse_failures.csv").exists()

    loaded = pd.read_csv(tmp_path / "analysis_parsed.csv")
    assert REQUIRED_COLS.issubset(set(loaded.columns))
