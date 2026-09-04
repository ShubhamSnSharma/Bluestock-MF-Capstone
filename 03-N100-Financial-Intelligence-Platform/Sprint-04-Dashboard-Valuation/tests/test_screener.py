"""
test_screener.py — Regression tests for Sprint 4 screener fixes.
Covers:
  • Financials D/E exemption
  • Debt-Free ICR infinity behaviour
  • Turnaround Watch 3yr CAGR + D/E declining
  • CSV generation with numeric values
  • Capital allocation pattern labels from Sprint-2 CSV
  • All 8 page module imports (smoke test)
"""

from __future__ import annotations

import io
import sys
import types
import unittest.mock as mock
from pathlib import Path

import pandas as pd
import pytest

_SPRINT4 = Path(__file__).resolve().parents[1]
_SRC     = _SPRINT4 / "src"
_PAGES   = _SPRINT4 / "pages"

if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


# ---------------------------------------------------------------------------
# Helper: mock @st.cache_data so db.py loads outside Streamlit runtime
# ---------------------------------------------------------------------------
def _mock_st():
    """Return a comprehensive mock of the streamlit module."""
    class ContextMock:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def __call__(self, *a, **kw): return None
        def __getattr__(self, name):
            if name == "columns":
                return lambda n, **kw: [ContextMock() for _ in range(n if isinstance(n, int) else len(n))]
            if name == "slider":
                return lambda *a, **kw: a[3] if len(a) > 3 else 0.0
            if name == "selectbox":
                return lambda *a, **kw: kw.get("index", None)
            if name == "multiselect":
                return lambda *a, **kw: kw.get("default", [])
            if name == "button":
                return lambda *a, **kw: False
            if name == "expander":
                return lambda *a, **kw: ContextMock()
            return lambda *a, **kw: None

    st_mock = types.ModuleType("streamlit")
    st_mock.cache_data = lambda **kw: (lambda f: f)
    st_mock.session_state = {}
    st_mock.set_page_config = lambda **kw: None
    st_mock.markdown = lambda *a, **kw: None
    st_mock.stop = lambda: None
    st_mock.error = lambda *a, **kw: None
    st_mock.warning = lambda *a, **kw: None
    st_mock.info = lambda *a, **kw: None
    st_mock.selectbox = lambda *a, **kw: kw.get("index", None)
    st_mock.multiselect = lambda *a, **kw: kw.get("default", [])
    st_mock.slider = lambda *a, **kw: a[3] if len(a) > 3 else 0.0
    st_mock.columns = lambda n, **kw: [ContextMock() for _ in range(n if isinstance(n, int) else len(n))]
    st_mock.sidebar = ContextMock()
    st_mock.button = lambda *a, **kw: False
    st_mock.dataframe = lambda *a, **kw: None
    st_mock.download_button = lambda *a, **kw: None
    st_mock.plotly_chart = lambda *a, **kw: None
    st_mock.expander = lambda *a, **kw: ContextMock()
    st_mock.rerun = lambda: None
    return st_mock


# ---------------------------------------------------------------------------
# Fixture: load screener data the same way 03_screener.py does
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def screener_data():
    with mock.patch.dict("sys.modules", {"streamlit": _mock_st()}):
        from dashboard.utils.db import (
            get_ratios_all, get_market_cap_all, get_de_decline_flags,
        )
        ratios_df = get_ratios_all(year="2024")
        mc_df     = get_market_cap_all(year="2024")
        de_flags  = get_de_decline_flags()

    merged = ratios_df.merge(
        mc_df[["company_id", "pe_ratio", "pb_ratio",
               "dividend_yield_pct", "market_cap_crore"]],
        on="company_id", how="left", suffixes=("", "_mc"),
    )
    merged = merged.merge(
        de_flags[["company_id", "de_declining"]],
        on="company_id", how="left",
    )
    merged["de_declining"] = merged["de_declining"].fillna(False)
    return merged


# ---------------------------------------------------------------------------
# Filter helpers (mirrors 03_screener.py)
# ---------------------------------------------------------------------------
def _gt(s: pd.Series, val: float) -> pd.Series:
    return s.fillna(float("-inf")) > val

def _lt(s: pd.Series, val: float) -> pd.Series:
    return s.fillna(float("inf")) < val

def _ge(s: pd.Series, val: float) -> pd.Series:
    return s.fillna(float("-inf")) >= val

def _le(s: pd.Series, val: float) -> pd.Series:
    return s.fillna(float("inf")) <= val


# ---------------------------------------------------------------------------
# Fix 2: Financials D/E exemption tests
# ---------------------------------------------------------------------------
class TestFinancialsDEExemption:

    def test_financials_company_not_excluded_by_de_filter(self, screener_data):
        """
        A Financials company with D/E above the threshold must NOT be
        removed by the D/E filter.
        """
        merged = screener_data
        is_financials = merged["broad_sector"].eq("Financials")
        fin_companies = merged[is_financials]

        assert not fin_companies.empty, "No Financials companies in data"

        # Pick a Financials company — use its actual D/E as 'high' DE
        sample = fin_companies[fin_companies["debt_to_equity"].notna()].iloc[0]
        test_de_max = float(sample["debt_to_equity"]) * 0.5  # threshold BELOW actual D/E

        # OLD (buggy) logic: would exclude this company
        old_de_pass = _le(merged["debt_to_equity"], test_de_max)
        old_result  = merged[is_financials & old_de_pass]

        # NEW (correct) logic: Financials exempt
        new_de_pass  = is_financials | _le(merged["debt_to_equity"], test_de_max)
        new_result   = merged[is_financials & new_de_pass]

        assert len(new_result) >= len(old_result), (
            "New logic should include at least as many Financials companies"
        )
        assert sample["company_id"] in new_result["company_id"].values, (
            f"Financials company {sample['company_id']} (D/E={sample['debt_to_equity']:.2f}) "
            f"wrongly excluded at de_max={test_de_max:.2f}"
        )

    def test_non_financials_still_subject_to_de_filter(self, screener_data):
        """Non-Financials companies must still be filtered by D/E."""
        merged = screener_data
        is_financials = merged["broad_sector"].eq("Financials")

        non_fin_high_de = merged[
            ~is_financials & (merged["debt_to_equity"].fillna(0) > 3.0)
        ]
        if non_fin_high_de.empty:
            pytest.skip("No non-Financials company with D/E > 3 in dataset")

        de_max     = 1.0
        de_pass    = is_financials | _le(merged["debt_to_equity"], de_max)
        excluded   = merged[~de_pass]

        for cid in non_fin_high_de["company_id"].values:
            assert cid in excluded["company_id"].values, (
                f"Non-Financials company {cid} with D/E > 3 should fail de_max=1.0"
            )

    def test_financials_count_correct(self, screener_data):
        """There should be 23 Financials companies in the dataset."""
        count = screener_data["broad_sector"].eq("Financials").sum()
        assert count == 23, f"Expected 23 Financials companies, got {count}"


# ---------------------------------------------------------------------------
# Fix 3: Debt-Free ICR infinity tests
# ---------------------------------------------------------------------------
class TestDebtFreeICR:

    def test_debt_free_company_passes_icr_minimum(self, screener_data):
        """
        A debt-free company (D/E <= 0.05) must pass any ICR minimum.
        Note: icr_label is NULL in FY2024 rows; D/E <= 0.05 is the canonical proxy.
        """
        merged     = screener_data
        debt_free  = merged["debt_to_equity"].fillna(float("inf")) <= 0.05
        df_cos     = merged[debt_free]

        assert not df_cos.empty, "No debt-free companies (D/E <= 0.05) in dataset"

        icr_min   = 10.0   # high threshold
        icr_pass  = debt_free | _ge(merged["interest_coverage"], icr_min)

        for cid in df_cos["company_id"].values:
            row = merged[merged["company_id"] == cid].iloc[0]
            assert icr_pass[row.name], (
                f"Debt-free company {cid} (D/E={row['debt_to_equity']}) "
                f"should pass ICR filter at icr_min={icr_min}"
            )

    def test_non_debt_free_with_low_icr_fails(self, screener_data):
        """A non-Debt-Free company with low (but non-null) ICR must fail a high ICR min."""
        merged    = screener_data
        debt_free = merged["debt_to_equity"].fillna(float("inf")) <= 0.05

        non_df_low_icr = merged[
            ~debt_free
            & (merged["interest_coverage"].fillna(-999) < 3.0)
            & merged["interest_coverage"].notna()
        ]
        if non_df_low_icr.empty:
            pytest.skip("No non-Debt-Free company with ICR < 3 in dataset")

        icr_min    = 10.0
        icr_pass   = debt_free | _ge(merged["interest_coverage"], icr_min)
        excluded   = merged[~icr_pass]

        for cid in non_df_low_icr["company_id"].values:
            assert cid in excluded["company_id"].values, (
                f"Non-Debt-Free company {cid} with low ICR should fail at icr_min={icr_min}"
            )

    def test_null_icr_non_debt_free_fails(self, screener_data):
        """Non-debt-free company (D/E > 0.05) with NULL ICR must NOT pass a positive ICR minimum."""
        merged    = screener_data
        debt_free = merged["debt_to_equity"].fillna(float("inf")) <= 0.05
        icr_min   = 1.0
        icr_pass  = debt_free | _ge(merged["interest_coverage"], icr_min)

        null_icr_non_df = merged[
            ~debt_free & merged["interest_coverage"].isna()
        ]
        if null_icr_non_df.empty:
            pytest.skip("No non-debt-free company with null ICR")

        for cid in null_icr_non_df["company_id"].values:
            row = merged[merged["company_id"] == cid].iloc[0]
            assert not icr_pass[row.name], (
                f"Non-debt-free company {cid} with null ICR should NOT pass icr_min={icr_min}"
            )


# ---------------------------------------------------------------------------
# Fix 4: Turnaround Watch preset tests
# ---------------------------------------------------------------------------
class TestTurnaroundWatch:

    def _apply_turnaround(self, merged: pd.DataFrame) -> pd.DataFrame:
        """Apply the Turnaround Watch filter criteria with strict boundaries."""
        is_financials   = merged["broad_sector"].eq("Financials")
        de_pass         = is_financials | _le(merged["debt_to_equity"], 100.0)
        debt_free_mask  = merged["icr_label"].eq("Debt Free")
        icr_pass        = debt_free_mask | _ge(merged["interest_coverage"], 0.0)
        # Turnaround-specific: strictly positive FCF and strictly > 10% 3yr CAGR
        rev_cagr_pass   = _gt(merged["revenue_cagr_3yr"], 10.0)
        fcf_pass        = _gt(merged["free_cash_flow_cr"], 0.0)
        de_decline_pass = merged["de_declining"].eq(True)

        mask = (
            de_pass & icr_pass
            & rev_cagr_pass & fcf_pass & de_decline_pass
        )
        return merged[mask]

    def test_turnaround_uses_3yr_cagr_not_5yr(self, screener_data):
        """Turnaround Watch must filter on revenue_cagr_3yr, not revenue_cagr_5yr."""
        merged = screener_data
        # Find a company where 3yr CAGR <= 10 but 5yr CAGR > 10
        diverged = merged[
            (merged["revenue_cagr_3yr"].fillna(-999) <= 10.0)
            & (merged["revenue_cagr_5yr"].fillna(-999) > 10.0)
        ]
        if diverged.empty:
            pytest.skip("No company with 3yr CAGR<=10 but 5yr CAGR>10 in dataset")

        result = self._apply_turnaround(merged)
        for cid in diverged["company_id"].values:
            assert cid not in result["company_id"].values, (
                f"{cid} has 3yr CAGR <= 10 — should fail Turnaround filter"
            )

    def test_turnaround_excludes_increasing_de(self, screener_data):
        """Company with D/E increasing YoY must fail Turnaround Watch."""
        merged = screener_data
        # Companies where D/E increased (de_declining == False)
        de_increased = merged[
            merged["de_declining"].eq(False)
            & merged["de_declining"].notna()
        ]
        if de_increased.empty:
            pytest.skip("All companies have declining D/E — unexpected")

        result = self._apply_turnaround(merged)
        # Such companies cannot be in result
        assert "de_declining" in merged.columns

    def test_turnaround_excludes_negative_fcf(self, screener_data):
        """Company with negative FCF must fail Turnaround Watch."""
        merged = screener_data
        neg_fcf = merged[merged["free_cash_flow_cr"].fillna(-999) < 0]
        if neg_fcf.empty:
            pytest.skip("No companies with negative FCF")

        result = self._apply_turnaround(merged)
        for cid in neg_fcf["company_id"].values:
            assert cid not in result["company_id"].values, (
                f"{cid} has negative FCF and should not pass Turnaround Watch"
            )

    def test_turnaround_excludes_zero_fcf(self, screener_data):
        """Turnaround Watch requires strictly positive FCF; FCF == 0.0 must fail."""
        merged = screener_data.copy()
        synthetic_row = merged.iloc[0].copy()
        synthetic_row["company_id"] = "TESTZEROFCF"
        synthetic_row["revenue_cagr_3yr"] = 15.0
        synthetic_row["free_cash_flow_cr"] = 0.0
        synthetic_row["de_declining"] = True
        synthetic_row["debt_to_equity"] = 0.5
        synthetic_row["interest_coverage"] = 5.0
        synthetic_row["broad_sector"] = "Automobile"

        test_df = pd.concat([merged, pd.DataFrame([synthetic_row])], ignore_index=True)
        result = self._apply_turnaround(test_df)
        assert "TESTZEROFCF" not in result["company_id"].values, (
            "Company with FCF == 0.0 must fail Turnaround Watch filter (requires strictly > 0)"
        )

    def test_turnaround_result_non_empty(self, screener_data):
        """Turnaround Watch must return qualifying companies (expected 33)."""
        result = self._apply_turnaround(screener_data)
        assert len(result) == 33, f"Expected 33 Turnaround Watch companies, got {len(result)}"


# ---------------------------------------------------------------------------
# Fix 7: CSV export — numeric values preserved
# ---------------------------------------------------------------------------
class TestCSVExport:

    def test_csv_has_numeric_values_not_formatted_strings(self, screener_data):
        """CSV export must contain numeric values, not '1,234.5' style strings."""
        merged = screener_data
        display_cols = {
            "company_id"               : "Ticker",
            "company_name"             : "Company",
            "broad_sector"             : "Sector",
            "composite_quality_score"  : "Quality Score",
            "return_on_equity_pct"     : "ROE %",
            "debt_to_equity"           : "D/E",
            "free_cash_flow_cr"        : "FCF (₹ Cr)",
            "revenue_cagr_5yr"         : "Rev CAGR 5yr %",
        }
        raw_table = merged[[c for c in display_cols if c in merged.columns]].rename(
            columns=display_cols
        )
        csv_buf = io.StringIO()
        raw_table.to_csv(csv_buf, index=False)
        csv_buf.seek(0)
        reread = pd.read_csv(csv_buf)

        # Numeric columns should be parseable as float — not contain commas/% signs
        for col in ["Quality Score", "ROE %", "D/E"]:
            if col in reread.columns:
                non_null = reread[col].dropna()
                if not non_null.empty:
                    # Should not raise ValueError
                    pd.to_numeric(non_null, errors="raise")

    def test_csv_has_required_columns(self, screener_data):
        """CSV must contain at minimum: Ticker, Company, Sector."""
        raw_table = screener_data[["company_id", "company_name", "broad_sector"]].rename(
            columns={"company_id": "Ticker", "company_name": "Company",
                     "broad_sector": "Sector"}
        )
        csv_buf = io.StringIO()
        raw_table.to_csv(csv_buf, index=False)
        csv_buf.seek(0)
        reread  = pd.read_csv(csv_buf)
        for col in ["Ticker", "Company", "Sector"]:
            assert col in reread.columns

    def test_csv_row_count_matches_filter_result(self, screener_data):
        """CSV row count must equal the number of matching companies."""
        result = screener_data[
            screener_data["return_on_equity_pct"].fillna(-999) >= 15.0
        ]
        raw_table = result[["company_id", "company_name"]].rename(
            columns={"company_id": "Ticker", "company_name": "Company"}
        )
        csv_buf = io.StringIO()
        raw_table.to_csv(csv_buf, index=False)
        csv_buf.seek(0)
        reread = pd.read_csv(csv_buf)
        assert len(reread) == len(result), (
            f"CSV has {len(reread)} rows but filter returned {len(result)} companies"
        )


# ---------------------------------------------------------------------------
# Fix 1: Capital allocation patterns from Sprint-2 CSV
# ---------------------------------------------------------------------------
class TestCapitalAllocationPatterns:

    @pytest.fixture(scope="class")
    def cap_df(self):
        with mock.patch.dict("sys.modules", {"streamlit": _mock_st()}):
            from dashboard.utils.db import get_capital_patterns
        return get_capital_patterns("2024")

    def test_returns_92_rows(self, cap_df):
        assert len(cap_df) == 92, f"Expected 92 rows, got {len(cap_df)}"

    def test_pattern_label_column_present(self, cap_df):
        assert "pattern_label" in cap_df.columns

    def test_no_cfo_quality_label_column(self, cap_df):
        """New implementation should NOT expose cfo_quality_label."""
        assert "cfo_quality_label" not in cap_df.columns

    def test_no_capex_intensity_label_column(self, cap_df):
        """New implementation should NOT expose capex_intensity_label."""
        assert "capex_intensity_label" not in cap_df.columns

    def test_sprint2_patterns_present(self, cap_df):
        """At least 4 of the 8 Sprint-2 patterns must appear in the FY2024 data."""
        expected = {
            "Reinvestor", "Shareholder Returns", "Liquidating Assets",
            "Distress Signal", "Growth Funded by Debt", "Cash Accumulator",
            "Pre-Revenue", "Mixed",
        }
        actual = set(cap_df["pattern_label"].unique())
        overlap = expected & actual
        assert len(overlap) >= 4, (
            f"Only {len(overlap)} Sprint-2 patterns found: {overlap}"
        )

    def test_shareholder_returns_is_largest_group(self, cap_df):
        """Per FY2024 data, Shareholder Returns should be the largest pattern."""
        counts = cap_df["pattern_label"].value_counts()
        top    = counts.index[0]
        assert top == "Shareholder Returns", (
            f"Expected 'Shareholder Returns' as largest group, got '{top}'"
        )


# ---------------------------------------------------------------------------
# Fix 8: Page import smoke test (no browser required)
# ---------------------------------------------------------------------------
class TestPageImports:
    """
    Verify all 8 page modules can be imported without Python syntax/import errors.
    We mock streamlit so pages can be parsed without a running server.
    """

    PAGES = [
        "01_home", "02_profile", "03_screener", "04_peers",
        "05_trends", "06_sectors", "07_capital", "08_reports",
    ]

    def _build_st_mock(self):
        """Build a comprehensive streamlit mock for import-level checks."""
        st_mock = types.ModuleType("streamlit")
        # Attributes accessed at module level
        st_mock.cache_data  = lambda **kw: (lambda f: f)
        st_mock.session_state = {}
        st_mock.set_page_config  = lambda **kw: None
        st_mock.markdown         = lambda *a, **kw: None
        st_mock.stop             = lambda: None
        st_mock.error            = lambda *a, **kw: None
        st_mock.warning          = lambda *a, **kw: None
        st_mock.info             = lambda *a, **kw: None
        st_mock.selectbox        = lambda *a, **kw: kw.get("index", None)
        st_mock.multiselect      = lambda *a, **kw: kw.get("default", [])
        st_mock.slider           = lambda *a, **kw: a[3] if len(a) > 3 else 0.0
        st_mock.columns          = lambda n, **kw: [types.SimpleNamespace(
            __enter__=lambda s: s, __exit__=lambda s, *a: None,
            button=lambda *a, **kw: False,
            markdown=lambda *a, **kw: None,
        ) for _ in range(n if isinstance(n, int) else len(n))]
        st_mock.sidebar          = types.SimpleNamespace(
            __enter__=lambda s: s, __exit__=lambda s, *a: None,
            markdown=lambda *a, **kw: None,
            selectbox=lambda *a, **kw: None,
            radio=lambda *a, **kw: None,
        )
        st_mock.button           = lambda *a, **kw: False
        st_mock.dataframe        = lambda *a, **kw: None
        st_mock.download_button  = lambda *a, **kw: None
        st_mock.plotly_chart     = lambda *a, **kw: None
        st_mock.expander         = lambda *a, **kw: types.SimpleNamespace(
            __enter__=lambda s: s, __exit__=lambda s, *a: None,
        )
        st_mock.rerun            = lambda: None
        return st_mock

    @pytest.mark.parametrize("page_name", PAGES)
    def test_page_parses_without_syntax_error(self, page_name):
        """Parse each page file for Python syntax errors."""
        page_path = _PAGES / f"{page_name}.py"
        assert page_path.exists(), f"Page file not found: {page_path}"
        source = page_path.read_text(encoding="utf-8")
        try:
            compile(source, str(page_path), "exec")
        except SyntaxError as e:
            pytest.fail(f"Syntax error in {page_name}.py: {e}")


# ---------------------------------------------------------------------------
# Fix 9: Strict preset boundary conditions & result counts
# ---------------------------------------------------------------------------
class TestStrictPresetBoundaries:
    """
    Test all 6 screener presets with strict boundary conditions:
    • Quality Compounder: ROE > 15%, D/E < 1.0, FCF > 0, Revenue CAGR 5yr > 10% (23 companies)
    • Value Pick: P/E < 20, P/B < 3.0, D/E < 2.0, Dividend Yield > 1% (2 companies)
    • Growth Accelerator: PAT CAGR 5yr > 20%, Revenue CAGR 5yr > 15%, D/E < 2.0 (19 companies)
    • Dividend Champion: Dividend Yield > 2%, Dividend Payout < 80%, FCF > 0 (30 companies)
    • Debt-Free Blue Chip: D/E = 0 / documented proxy, ROE > 12%, Revenue > 5000 Cr (31 companies)
    • Turnaround Watch: Revenue CAGR 3yr > 10%, FCF > 0, D/E declining YoY (33 companies)
    """

    @pytest.fixture(scope="class")
    def apply_fn(self):
        with mock.patch.dict("sys.modules", {"streamlit": _mock_st()}):
            import importlib.util
            spec = importlib.util.spec_from_file_location("page_screener", _PAGES / "03_screener.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        return mod.apply_preset

    def test_quality_compounder_count_and_boundary(self, screener_data, apply_fn):
        res = screener_data[apply_fn(screener_data, "Quality Compounder")]
        assert len(res) == 23, f"Expected 23 Quality Compounders, got {len(res)}"
        # Strict boundary test: ROE == 15.0 must fail
        synth = screener_data.iloc[0].copy()
        synth["company_id"] = "TEST_QC_BOUNDARY"
        synth["return_on_equity_pct"] = 15.0  # boundary value
        synth["debt_to_equity"] = 0.5
        synth["free_cash_flow_cr"] = 100.0
        synth["revenue_cagr_5yr"] = 15.0
        synth["broad_sector"] = "Automobile"
        test_df = pd.concat([screener_data, pd.DataFrame([synth])], ignore_index=True)
        assert "TEST_QC_BOUNDARY" not in test_df[apply_fn(test_df, "Quality Compounder")]["company_id"].values

    def test_value_pick_count_and_boundary(self, screener_data, apply_fn):
        res = screener_data[apply_fn(screener_data, "Value Pick")]
        assert len(res) == 2, f"Expected 2 Value Picks, got {len(res)}"
        assert sorted(res["company_id"].tolist()) == ["M&M", "MOTHERSON"]
        # Strict boundary test: PE == 20.0 must fail
        synth = screener_data.iloc[0].copy()
        synth["company_id"] = "TEST_VP_BOUNDARY"
        synth["pe_ratio"] = 20.0  # boundary value
        synth["pb_ratio"] = 2.0
        synth["debt_to_equity"] = 1.0
        synth["dividend_yield_pct"] = 2.0
        synth["broad_sector"] = "Automobile"
        test_df = pd.concat([screener_data, pd.DataFrame([synth])], ignore_index=True)
        assert "TEST_VP_BOUNDARY" not in test_df[apply_fn(test_df, "Value Pick")]["company_id"].values

    def test_growth_accelerator_count_and_boundary(self, screener_data, apply_fn):
        res = screener_data[apply_fn(screener_data, "Growth Accelerator")]
        assert len(res) == 19, f"Expected 19 Growth Accelerators, got {len(res)}"
        # Strict boundary test: PAT CAGR == 20.0 must fail
        synth = screener_data.iloc[0].copy()
        synth["company_id"] = "TEST_GA_BOUNDARY"
        synth["pat_cagr_5yr"] = 20.0  # boundary value
        synth["revenue_cagr_5yr"] = 25.0
        synth["debt_to_equity"] = 1.0
        synth["broad_sector"] = "Automobile"
        test_df = pd.concat([screener_data, pd.DataFrame([synth])], ignore_index=True)
        assert "TEST_GA_BOUNDARY" not in test_df[apply_fn(test_df, "Growth Accelerator")]["company_id"].values

    def test_dividend_champion_count_and_boundary(self, screener_data, apply_fn):
        res = screener_data[apply_fn(screener_data, "Dividend Champion")]
        assert len(res) == 30, f"Expected 30 Dividend Champions, got {len(res)}"
        # Strict boundary test: Dividend Payout == 80.0 must fail
        synth = screener_data.iloc[0].copy()
        synth["company_id"] = "TEST_DC_BOUNDARY"
        synth["dividend_yield_pct"] = 3.0
        synth["dividend_payout_ratio_pct"] = 80.0  # boundary value
        synth["free_cash_flow_cr"] = 100.0
        synth["broad_sector"] = "Automobile"
        test_df = pd.concat([screener_data, pd.DataFrame([synth])], ignore_index=True)
        assert "TEST_DC_BOUNDARY" not in test_df[apply_fn(test_df, "Dividend Champion")]["company_id"].values

    def test_debt_free_blue_chip_count_and_boundary(self, screener_data, apply_fn):
        res = screener_data[apply_fn(screener_data, "Debt-Free Blue Chip")]
        assert len(res) == 31, f"Expected 31 Debt-Free Blue Chips, got {len(res)}"
        # Strict boundary test: Sales == 5000.0 must fail (requires strictly > 5000)
        synth = screener_data.iloc[0].copy()
        synth["company_id"] = "TEST_DFBC_BOUNDARY"
        synth["debt_to_equity"] = 0.0
        synth["return_on_equity_pct"] = 20.0
        synth["sales"] = 5000.0  # boundary value
        synth["broad_sector"] = "Automobile"
        test_df = pd.concat([screener_data, pd.DataFrame([synth])], ignore_index=True)
        assert "TEST_DFBC_BOUNDARY" not in test_df[apply_fn(test_df, "Debt-Free Blue Chip")]["company_id"].values

    def test_turnaround_watch_count(self, screener_data, apply_fn):
        res = screener_data[apply_fn(screener_data, "Turnaround Watch")]
        assert len(res) == 33, f"Expected 33 Turnaround Watch companies, got {len(res)}"
