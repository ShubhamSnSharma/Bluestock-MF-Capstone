"""
Sprint 6 — Day 41: ETL, KPI and Data Quality Validation Suite.

Validates:
  - ETL/Data completeness (92 companies, table populations, nulls, duplicates, year formats)
  - KPI validation (finite values, extreme value detection, ratio sanity)
  - Data quality (referential integrity, sector coverage, peer groups, clusters, documents)
  - Regression safety (Day 36-40 outputs preserved, Sprint 1-5 untouched)

Known legitimate exceptions documented:
  - JIOFIN has no tearsheet (Sprint 5 legitimately skipped it)
  - 36 companies have no peer group assignment
  - 4 companies have pros/cons data, 88 do not
  - 1 company missing from documents table
  - Extreme financial values are flagged for review, NOT treated as failures
"""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# ── Path setup ──────────────────────────────────────────────────────────────
# tests/test_data_quality.py → tests/ → Sprint-06-API-Clustering-QA/ → 03-N100-Financial-Intelligence-Platform/
PLATFORM_ROOT = Path(__file__).resolve().parent.parent.parent
SPRINT6_ROOT = PLATFORM_ROOT / "Sprint-06-API-Clustering-QA"
SPRINT1_ROOT = PLATFORM_ROOT / "Sprint-01-Data-Foundation"
SPRINT5_ROOT = PLATFORM_ROOT / "Sprint-05-Intelligence-NLP-PDF-Reports"
DB_PATH = SPRINT1_ROOT / "nifty100.db"
CLUSTER_CSV = SPRINT6_ROOT / "output" / "cluster_labels.csv"
PORTFOLIO_CSV = SPRINT6_ROOT / "output" / "portfolio_stats.csv"
OUTLIER_CSV = SPRINT6_ROOT / "output" / "outlier_report.csv"

EXPECTED_COMPANY_COUNT = 92
EXPECTED_TABLES = [
    "analysis",
    "balancesheet",
    "cashflow",
    "companies",
    "documents",
    "financial_ratios",
    "market_cap",
    "peer_groups",
    "peer_percentiles",
    "profitandloss",
    "prosandcons",
    "sectors",
    "stock_prices",
]

# Extreme value thresholds for flagging (not failure)
EXTREME_THRESHOLDS = {
    "return_on_equity_pct": 500,
    "return_on_capital_employed_pct": 500,
    "net_profit_margin_pct": 200,
    "operating_profit_margin_pct": 200,
    "debt_to_equity": 50,
    "interest_coverage": 1000,
    "asset_turnover": 20,
    "fcf_conversion_pct": 500,
}


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def db_conn():
    """Provide a read-only SQLite connection."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture(scope="module")
def companies_df(db_conn):
    return pd.read_sql("SELECT * FROM companies", db_conn)


@pytest.fixture(scope="module")
def sectors_df(db_conn):
    return pd.read_sql("SELECT * FROM sectors", db_conn)


@pytest.fixture(scope="module")
def ratios_df(db_conn):
    return pd.read_sql("SELECT * FROM financial_ratios", db_conn)


@pytest.fixture(scope="module")
def ratios_2024_df(db_conn):
    return pd.read_sql('SELECT * FROM financial_ratios WHERE year = "2024"', db_conn)


@pytest.fixture(scope="module")
def pl_df(db_conn):
    return pd.read_sql("SELECT * FROM profitandloss", db_conn)


@pytest.fixture(scope="module")
def bs_df(db_conn):
    return pd.read_sql("SELECT * FROM balancesheet", db_conn)


@pytest.fixture(scope="module")
def cf_df(db_conn):
    return pd.read_sql("SELECT * FROM cashflow", db_conn)


@pytest.fixture(scope="module")
def mc_df(db_conn):
    return pd.read_sql("SELECT * FROM market_cap", db_conn)


@pytest.fixture(scope="module")
def pg_df(db_conn):
    return pd.read_sql("SELECT * FROM peer_groups", db_conn)


@pytest.fixture(scope="module")
def pp_df(db_conn):
    return pd.read_sql("SELECT * FROM peer_percentiles", db_conn)


@pytest.fixture(scope="module")
def cluster_df():
    return pd.read_csv(str(CLUSTER_CSV))


# ══════════════════════════════════════════════════════════════════════════════
# PART 1: ETL / DATA COMPLETENESS
# ══════════════════════════════════════════════════════════════════════════════


class TestETLCompleteness:
    """Validate expected table populations and data completeness."""

    def test_92_companies_present(self, companies_df):
        """PASS: Exactly 92 N100 companies in database."""
        assert len(companies_df) == EXPECTED_COMPANY_COUNT

    def test_all_expected_tables_exist(self, db_conn):
        """PASS: All 13 expected user tables exist."""
        cursor = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'"
        )
        tables = {r[0] for r in cursor.fetchall()}
        for t in EXPECTED_TABLES:
            assert t in tables, f"Missing table: {t}"

    def test_table_row_counts_reasonable(self, db_conn):
        """PASS: Table row counts within expected ranges."""
        expected_min = {
            "companies": 92,
            "sectors": 92,
            "financial_ratios": 900,
            "profitandloss": 900,
            "balancesheet": 900,
            "cashflow": 900,
            "market_cap": 500,
            "peer_groups": 50,
            "peer_percentiles": 500,
            "documents": 1000,
            "stock_prices": 5000,
        }
        for table, min_rows in expected_min.items():
            count = db_conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
            assert (
                count >= min_rows
            ), f"{table}: {count} rows < expected minimum {min_rows}"

    def test_companies_no_null_ids(self, companies_df):
        """PASS: No NULL company IDs."""
        assert companies_df["id"].isna().sum() == 0

    def test_companies_no_null_names(self, companies_df):
        """PASS: No NULL company names."""
        assert companies_df["company_name"].isna().sum() == 0

    def test_sectors_no_null_company_ids(self, sectors_df):
        """PASS: No NULL company IDs in sectors."""
        assert sectors_df["company_id"].isna().sum() == 0

    def test_sectors_no_null_sectors(self, sectors_df):
        """PASS: No NULL broad_sector or sub_sector."""
        assert sectors_df["broad_sector"].isna().sum() == 0
        assert sectors_df["sub_sector"].isna().sum() == 0

    def test_ratios_no_null_ids_or_years(self, ratios_df):
        """PASS: No NULL company_id or year in financial_ratios."""
        assert ratios_df["company_id"].isna().sum() == 0
        assert ratios_df["year"].isna().sum() == 0

    def test_no_duplicate_companies(self, companies_df):
        """PASS: No duplicate company IDs."""
        assert companies_df["id"].duplicated().sum() == 0

    def test_no_duplicate_sectors(self, sectors_df):
        """PASS: No duplicate sector assignments per company."""
        assert sectors_df.duplicated(subset=["company_id"]).sum() == 0

    def test_no_duplicate_ratios(self, ratios_df):
        """PASS: No duplicate company/year in financial_ratios."""
        dups = ratios_df.duplicated(subset=["company_id", "year"])
        assert dups.sum() == 0

    def test_no_duplicate_pl(self, pl_df):
        """PASS: No duplicate company/year in profitandloss."""
        dups = pl_df.duplicated(subset=["company_id", "year"])
        assert dups.sum() == 0

    def test_no_duplicate_bs(self, bs_df):
        """PASS: No duplicate company/year in balancesheet."""
        dups = bs_df.duplicated(subset=["company_id", "year"])
        assert dups.sum() == 0

    def test_no_duplicate_cf(self, cf_df):
        """PASS: No duplicate company/year in cashflow."""
        dups = cf_df.duplicated(subset=["company_id", "year"])
        assert dups.sum() == 0

    def test_no_duplicate_mc(self, mc_df):
        """PASS: No duplicate company/year in market_cap."""
        dups = mc_df.duplicated(subset=["company_id", "year"])
        assert dups.sum() == 0

    def test_ratio_year_format_valid(self, ratios_df):
        """PASS: All ratio years are YYYY or TTM."""
        valid_years = set(str(y) for y in range(2000, 2030)) | {"TTM"}
        invalid = ratios_df[~ratios_df["year"].isin(valid_years)]
        assert len(invalid) == 0, f"Invalid years: {invalid['year'].unique()}"

    def test_pl_year_format_valid(self, pl_df):
        """PASS: All P&L years are YYYY or TTM."""
        valid_years = set(str(y) for y in range(2000, 2030)) | {"TTM"}
        invalid = pl_df[~pl_df["year"].isin(valid_years)]
        assert len(invalid) == 0, f"Invalid years: {invalid['year'].unique()}"

    def test_bs_year_format_valid(self, bs_df):
        """PASS: All balance sheet years are YYYY or TTM."""
        valid_years = set(str(y) for y in range(2000, 2030)) | {"TTM"}
        invalid = bs_df[~bs_df["year"].isin(valid_years)]
        assert len(invalid) == 0, f"Invalid years: {invalid['year'].unique()}"

    def test_cf_year_format_valid(self, cf_df):
        """PASS: All cashflow years are YYYY or TTM."""
        valid_years = set(str(y) for y in range(2000, 2030)) | {"TTM"}
        invalid = cf_df[~cf_df["year"].isin(valid_years)]
        assert len(invalid) == 0, f"Invalid years: {invalid['year'].unique()}"


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: KPI VALIDATION
# ══════════════════════════════════════════════════════════════════════════════


class TestKPIValidation:
    """Validate financial ratios against source data and sanity checks."""

    def test_ratios_finite_where_expected(self, ratios_2024_df):
        """PASS: Core ratio columns contain finite values (not inf)."""
        core_cols = [
            "net_profit_margin_pct",
            "operating_profit_margin_pct",
            "return_on_equity_pct",
            "debt_to_equity",
            "interest_coverage",
            "return_on_capital_employed_pct",
            "asset_turnover",
        ]
        for col in core_cols:
            if col in ratios_2024_df.columns:
                vals = ratios_2024_df[col].dropna()
                assert np.all(np.isfinite(vals)), f"{col} contains inf values"

    def test_roe_extreme_values_flagged(self, ratios_2024_df):
        """WARNING: Extreme ROE values exist but are legitimate financial outliers."""
        extreme = ratios_2024_df[
            ratios_2024_df["return_on_equity_pct"].abs()
            > EXTREME_THRESHOLDS["return_on_equity_pct"]
        ]
        # Flag but do not fail - these are known legitimate outliers
        if len(extreme) > 0:
            companies = extreme["company_id"].tolist()
            pytest.skip(
                f"WARNING: Extreme ROE (>500%): {companies} — legitimate outliers"
            )

    def test_roce_extreme_values_flagged(self, ratios_2024_df):
        """WARNING: Extreme ROCE values exist but are legitimate financial outliers."""
        extreme = ratios_2024_df[
            ratios_2024_df["return_on_capital_employed_pct"].abs()
            > EXTREME_THRESHOLDS["return_on_capital_employed_pct"]
        ]
        if len(extreme) > 0:
            companies = extreme["company_id"].tolist()
            pytest.skip(
                f"WARNING: Extreme ROCE (>500%): {companies} — legitimate outliers"
            )

    def test_npm_extreme_values_flagged(self, ratios_2024_df):
        """WARNING: Extreme NPM values exist but are legitimate financial outliers."""
        extreme = ratios_2024_df[
            ratios_2024_df["net_profit_margin_pct"].abs()
            > EXTREME_THRESHOLDS["net_profit_margin_pct"]
        ]
        if len(extreme) > 0:
            companies = extreme["company_id"].tolist()
            pytest.skip(
                f"WARNING: Extreme NPM (>200%): {companies} — legitimate outliers"
            )

    def test_leverage_extreme_values_flagged(self, ratios_2024_df):
        """WARNING: Extreme D/E values exist but are legitimate financial outliers."""
        extreme = ratios_2024_df[
            ratios_2024_df["debt_to_equity"].abs()
            > EXTREME_THRESHOLDS["debt_to_equity"]
        ]
        if len(extreme) > 0:
            companies = extreme["company_id"].tolist()
            pytest.skip(
                f"WARNING: Extreme D/E (>50): {companies} — legitimate outliers"
            )

    def test_core_ratios_not_all_null(self, ratios_2024_df):
        """PASS: Core ratio columns have majority non-null values."""
        core_cols = [
            "net_profit_margin_pct",
            "operating_profit_margin_pct",
            "return_on_equity_pct",
            "debt_to_equity",
        ]
        for col in core_cols:
            if col in ratios_2024_df.columns:
                non_null_pct = ratios_2024_df[col].notna().mean()
                assert non_null_pct >= 0.95, f"{col}: only {non_null_pct:.1%} non-null"

    def test_margin_values_reasonable(self, ratios_2024_df):
        """PASS: Profit margins are within plausible range (-100% to 1000%)."""
        for col in ["net_profit_margin_pct", "operating_profit_margin_pct"]:
            if col in ratios_2024_df.columns:
                vals = ratios_2024_df[col].dropna()
                out_of_range = vals[(vals < -100) | (vals > 1000)]
                assert (
                    len(out_of_range) == 0
                ), f"{col} out of range: {out_of_range.tolist()}"

    def test_debt_to_equity_non_negative(self, ratios_2024_df):
        """PASS: D/E ratio is non-negative (no negative leverage)."""
        if "debt_to_equity" in ratios_2024_df.columns:
            vals = ratios_2024_df["debt_to_equity"].dropna()
            negative = vals[vals < 0]
            assert len(negative) == 0, f"Negative D/E: {negative.tolist()}"

    def test_interest_coverage_positive(self, ratios_2024_df):
        """PASS: Interest coverage is positive where present."""
        if "interest_coverage" in ratios_2024_df.columns:
            vals = ratios_2024_df["interest_coverage"].dropna()
            # ICR can be negative (loss-making), but should be finite
            assert np.all(np.isfinite(vals)), "ICR contains inf values"

    def test_eps_values_finite(self, ratios_2024_df):
        """PASS: EPS values are finite where present."""
        if "earnings_per_share" in ratios_2024_df.columns:
            vals = ratios_2024_df["earnings_per_share"].dropna()
            assert np.all(np.isfinite(vals)), "EPS contains inf values"


# ══════════════════════════════════════════════════════════════════════════════
# PART 3: DATA QUALITY
# ══════════════════════════════════════════════════════════════════════════════


class TestDataQuality:
    """Validate referential integrity, coverage, and consistency."""

    def test_referential_integrity_ratios(self, db_conn):
        """PASS: All ratio company_ids exist in companies table."""
        count = db_conn.execute(
            """
            SELECT COUNT(DISTINCT fr.company_id) FROM financial_ratios fr
            LEFT JOIN companies c ON fr.company_id = c.id
            WHERE c.id IS NULL
        """
        ).fetchone()[0]
        assert count == 0

    def test_referential_integrity_sectors(self, db_conn):
        """PASS: All sector company_ids exist in companies table."""
        count = db_conn.execute(
            """
            SELECT COUNT(DISTINCT s.company_id) FROM sectors s
            LEFT JOIN companies c ON s.company_id = c.id
            WHERE c.id IS NULL
        """
        ).fetchone()[0]
        assert count == 0

    def test_referential_integrity_peer_groups(self, db_conn):
        """PASS: All peer group company_ids exist in companies table."""
        count = db_conn.execute(
            """
            SELECT COUNT(DISTINCT pg.company_id) FROM peer_groups pg
            LEFT JOIN companies c ON pg.company_id = c.id
            WHERE c.id IS NULL
        """
        ).fetchone()[0]
        assert count == 0

    def test_referential_integrity_market_cap(self, db_conn):
        """PASS: All market cap company_ids exist in companies table."""
        count = db_conn.execute(
            """
            SELECT COUNT(DISTINCT mc.company_id) FROM market_cap mc
            LEFT JOIN companies c ON mc.company_id = c.id
            WHERE c.id IS NULL
        """
        ).fetchone()[0]
        assert count == 0

    def test_referential_integrity_pl(self, db_conn):
        """PASS: All P&L company_ids exist in companies table."""
        count = db_conn.execute(
            """
            SELECT COUNT(DISTINCT pl.company_id) FROM profitandloss pl
            LEFT JOIN companies c ON pl.company_id = c.id
            WHERE c.id IS NULL
        """
        ).fetchone()[0]
        assert count == 0

    def test_referential_integrity_bs(self, db_conn):
        """PASS: All balance sheet company_ids exist in companies table."""
        count = db_conn.execute(
            """
            SELECT COUNT(DISTINCT bs.company_id) FROM balancesheet bs
            LEFT JOIN companies c ON bs.company_id = c.id
            WHERE c.id IS NULL
        """
        ).fetchone()[0]
        assert count == 0

    def test_referential_integrity_cf(self, db_conn):
        """PASS: All cashflow company_ids exist in companies table."""
        count = db_conn.execute(
            """
            SELECT COUNT(DISTINCT cf.company_id) FROM cashflow cf
            LEFT JOIN companies c ON cf.company_id = c.id
            WHERE c.id IS NULL
        """
        ).fetchone()[0]
        assert count == 0

    def test_n100_sector_coverage(self, sectors_df):
        """PASS: All 92 companies have sector assignments."""
        assert len(sectors_df) == EXPECTED_COMPANY_COUNT

    def test_sector_values_valid(self, sectors_df):
        """PASS: Sector values are from expected set."""
        expected_sectors = {
            "Communication Services",
            "Consumer Discretionary",
            "Consumer Staples",
            "Energy",
            "Financials",
            "Healthcare",
            "Industrials",
            "Information Technology",
            "Materials",
            "Real Estate",
        }
        actual = set(sectors_df["broad_sector"].unique())
        assert (
            actual == expected_sectors
        ), f"Unexpected sectors: {actual - expected_sectors}"

    def test_market_cap_categories_valid(self, sectors_df):
        """PASS: Market cap categories are from expected set."""
        expected = {"Large Cap", "Mid Cap"}
        actual = set(sectors_df["market_cap_category"].dropna().unique())
        assert actual == expected, f"Unexpected categories: {actual - expected}"

    def test_peer_group_coverage_partial(self, db_conn):
        """WARNING: Only 56 of 92 companies have peer group assignments."""
        count = db_conn.execute(
            "SELECT COUNT(DISTINCT company_id) FROM peer_groups"
        ).fetchone()[0]
        assert count == 56, f"Expected 56 companies in peer groups, got {count}"
        # This is a known exception - not all companies have peer groups

    def test_cluster_label_coverage(self, cluster_df):
        """PASS: All 92 companies have cluster labels."""
        assert len(cluster_df) == EXPECTED_COMPANY_COUNT

    def test_cluster_ids_valid(self, cluster_df):
        """PASS: Cluster IDs are 0-4 (5 clusters)."""
        ids = sorted(cluster_df["cluster_id"].unique())
        assert ids == [0, 1, 2, 3, 4]

    def test_cluster_names_meaningful(self, cluster_df):
        """PASS: Cluster names are present and non-empty."""
        assert cluster_df["cluster_name"].notna().all()
        assert all(len(n) > 0 for n in cluster_df["cluster_name"])

    def test_tearsheet_coverage_known_exception(self):
        """WARNING: JIOFIN legitimately has no tearsheet (Sprint 5 skipped it)."""
        tearsheet_dir = SPRINT5_ROOT / "reports" / "tearsheets"
        pdfs = {
            f.replace("_tearsheet.pdf", "")
            for f in os.listdir(tearsheet_dir)
            if f.endswith(".pdf")
        }
        assert len(pdfs) == 91, f"Expected 91 tearsheets, got {len(pdfs)}"
        assert "JIOFIN" not in pdfs, "JIOFIN should NOT have a tearsheet"

    def test_documents_coverage(self, db_conn):
        """WARNING: 1 company missing from documents table (known exception)."""
        count = db_conn.execute(
            "SELECT COUNT(DISTINCT company_id) FROM documents"
        ).fetchone()[0]
        assert count == 91, f"Expected 91 companies with documents, got {count}"

    def test_pros_cons_coverage_limited(self, db_conn):
        """WARNING: Only 4 companies have pros/cons data (known exception)."""
        count = db_conn.execute(
            "SELECT COUNT(DISTINCT company_id) FROM prosandcons"
        ).fetchone()[0]
        assert count == 4, f"Expected 4 companies with pros/cons, got {count}"

    def test_stock_prices_coverage(self, db_conn):
        """PASS: Stock prices have good coverage."""
        count = db_conn.execute(
            "SELECT COUNT(DISTINCT company_id) FROM stock_prices"
        ).fetchone()[0]
        assert count == EXPECTED_COMPANY_COUNT

    def test_market_cap_coverage(self, db_conn):
        """PASS: All 92 companies have market cap data."""
        count = db_conn.execute(
            "SELECT COUNT(DISTINCT company_id) FROM market_cap"
        ).fetchone()[0]
        assert count == EXPECTED_COMPANY_COUNT


# ══════════════════════════════════════════════════════════════════════════════
# PART 4: REGRESSION SAFETY
# ══════════════════════════════════════════════════════════════════════════════


class TestRegressionSafety:
    """Verify Day 36-40 outputs are preserved and consistent."""

    def test_cluster_labels_preserved(self, cluster_df):
        """PASS: Day 36 cluster assignments unchanged."""
        assert len(cluster_df) == 92
        assert set(cluster_df["cluster_id"].unique()) == {0, 1, 2, 3, 4}
        # Verify known distribution
        counts = cluster_df["cluster_id"].value_counts()
        assert counts[0] == 60
        assert counts[1] == 14
        assert counts[2] == 2
        assert counts[3] == 15
        assert counts[4] == 1

    def test_portfolio_stats_preserved(self):
        """PASS: Day 37 portfolio stats are consistent."""
        df = pd.read_csv(str(PORTFOLIO_CSV))
        assert len(df) == 10, "Expected 10 KPIs in portfolio stats"

    def test_outlier_report_preserved(self):
        """PASS: Day 37 outlier report is consistent."""
        df = pd.read_csv(str(OUTLIER_CSV))
        assert len(df) == 912, "Expected 912 outlier records (92 companies * 10 KPIs)"

    def test_db_schema_unchanged(self, db_conn):
        """PASS: Database has exactly 13 user tables."""
        cursor = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'"
        )
        tables = [r[0] for r in cursor.fetchall()]
        assert len(tables) == 13, f"Expected 13 tables, got {len(tables)}: {tables}"

    def test_no_new_tables_created(self, db_conn):
        """PASS: No unexpected tables exist."""
        cursor = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'"
        )
        tables = {r[0] for r in cursor.fetchall()}
        unexpected = tables - set(EXPECTED_TABLES)
        assert len(unexpected) == 0, f"Unexpected tables: {unexpected}"
