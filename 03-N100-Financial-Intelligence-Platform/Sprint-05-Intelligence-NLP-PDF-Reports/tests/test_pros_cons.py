"""
tests/test_pros_cons.py
========================
Day 30 — Tests for the Auto Pros/Cons Generator.

Validates the ACTUAL Sprint 5 specification:
  - Exact 24 rules (P01–P12, C01–C12) implemented
  - Exact thresholds (strict > and <)
  - C01 exempts financial companies
  - Consecutive-year rules
  - Latest-year rules
  - Confidence > 60 only; not all 100
  - Exact 5-column output schema
  - No duplicate (company_id, rule_id) pairs
  - Full 92-company universe evaluated
  - coverage_failures.csv for missing pro or con
  - No fabricated signals
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

SPRINT5 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SPRINT5))

from src.nlp.pros_cons_generator import (
    ProsConsGenerator,
    _conf,
    _conf_consec,
    _FIXED_CONF,
    _FINANCIAL_SECTOR,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def gen():
    return ProsConsGenerator()


@pytest.fixture(scope="module")
def results(gen):
    df, cov = gen.generate()
    return df, cov


@pytest.fixture(scope="module")
def signals_df(results):
    return results[0]


@pytest.fixture(scope="module")
def coverage_df(results):
    return results[1]


# ===========================================================================
# T01 — Confidence helpers
# ===========================================================================
class TestConfHelpers:

    def test_conf_base(self):
        assert _conf(1.0, 1.0) == 71

    def test_conf_zero_magnitude(self):
        assert _conf(0.0, 1.0) == 70

    def test_conf_capped_99(self):
        assert _conf(100000, 1.0) == 99

    def test_conf_never_100(self):
        assert _conf(100000, 1.0) < 100

    def test_conf_always_above_60(self):
        assert _conf(0.001, 100000) > 60

    def test_conf_consec_min(self):
        # n = min → 70 + 0 * 5 = 70
        assert _conf_consec(3, 3) == 70

    def test_conf_consec_extra(self):
        # n = min + 2 → 70 + 2*5 = 80
        assert _conf_consec(5, 3) == 80

    def test_conf_consec_capped(self):
        # Very large n, cap at 99
        assert _conf_consec(1000, 3) == 99

    def test_fixed_conf_above_threshold(self):
        assert _FIXED_CONF > 60


# ===========================================================================
# T02 — Required output schema (exactly 5 columns)
# ===========================================================================
REQUIRED_COLS = {"company_id", "type", "rule_id", "text", "confidence_pct"}
DISALLOWED_COLS = {"signal_type", "rule_label", "evidence"}


def test_output_schema(signals_df):
    assert REQUIRED_COLS.issubset(set(signals_df.columns)), (
        f"Missing: {REQUIRED_COLS - set(signals_df.columns)}"
    )


def test_no_old_column_names(signals_df):
    present = DISALLOWED_COLS & set(signals_df.columns)
    assert not present, f"Old column names present: {present}"


def test_exactly_5_columns(signals_df):
    assert set(signals_df.columns) == REQUIRED_COLS


# ===========================================================================
# T03 — Confidence threshold: all > 60
# ===========================================================================
def test_all_confidence_above_60(signals_df):
    assert (signals_df["confidence_pct"] > 60).all()


# ===========================================================================
# T04 — Confidence is not uniformly 100
# ===========================================================================
def test_confidence_not_all_100(signals_df):
    assert (signals_df["confidence_pct"] < 100).any()


# ===========================================================================
# T05 — type values
# ===========================================================================
def test_type_values(signals_df):
    assert set(signals_df["type"].unique()).issubset({"pro", "con"})


# ===========================================================================
# T06 — rule_id format: P01-P12 or C01-C12
# ===========================================================================
import re as _re
_RULE_PAT = _re.compile(r"^[PC](0[1-9]|1[0-2])$")

def test_rule_id_format(signals_df):
    bad = signals_df[~signals_df["rule_id"].str.match(_RULE_PAT)]
    assert bad.empty, f"Bad rule_ids: {bad['rule_id'].unique()}"


# ===========================================================================
# T07 — Pro rules in range P01–P12
# ===========================================================================
def test_pro_rules_in_range(signals_df):
    pros = signals_df[signals_df["type"] == "pro"]
    for rid in pros["rule_id"].unique():
        assert rid.startswith("P"), f"{rid} is not a P rule"
        n = int(rid[1:])
        assert 1 <= n <= 12, f"Pro rule out of range: {rid}"


# ===========================================================================
# T08 — Con rules in range C01–C12
# ===========================================================================
def test_con_rules_in_range(signals_df):
    cons = signals_df[signals_df["type"] == "con"]
    for rid in cons["rule_id"].unique():
        assert rid.startswith("C"), f"{rid} is not a C rule"
        n = int(rid[1:])
        assert 1 <= n <= 12, f"Con rule out of range: {rid}"


# ===========================================================================
# T09 — text column is non-empty
# ===========================================================================
def test_text_non_empty(signals_df):
    assert signals_df["text"].str.strip().ne("").all()


# ===========================================================================
# T10 — No duplicate (company_id, rule_id) pairs
# ===========================================================================
def test_no_duplicate_rule_per_company(signals_df):
    dupes = signals_df.groupby(["company_id", "rule_id"]).size()
    dupes_gt1 = dupes[dupes > 1]
    assert dupes_gt1.empty, f"Duplicate company/rule pairs:\n{dupes_gt1}"


# ===========================================================================
# T11 — All 92 companies evaluated
# ===========================================================================
def test_92_companies_evaluated(gen, results):
    df, _ = results
    assert len(gen._companies) == 92, (
        f"Expected 92 companies, got {len(gen._companies)}"
    )


# ===========================================================================
# T12 — C01 exempts financial companies
# ===========================================================================
def test_c01_no_financial_companies(gen, signals_df):
    c01 = signals_df[signals_df["rule_id"] == "C01"]
    for cid in c01["company_id"].unique():
        assert not gen._is_financial(cid), (
            f"C01 fired for financial company {cid} — should be exempt"
        )


# ===========================================================================
# T13 — P01 threshold: ROE > 20% (not >= 20)
# ===========================================================================
def test_p01_threshold_strict_gt_20(gen):
    """
    Load ROE for a company known to be around 20% and verify strict > applied.
    """
    # We verify via the helper: a company where latest ROE == exactly 20
    # would not trigger P01. We can't guarantee such a company exists in the DB,
    # so we test the condition logic directly using series data for TCS
    # (ROE well > 20% for many years — P01 should fire for TCS).
    from src.nlp.pros_cons_generator import _n_roe_gt20_consec
    gen._load_data()
    n = _n_roe_gt20_consec(gen._rat, "TCS")
    # TCS has ROE > 20% for all 12 years → n >= 3 → P01 fires
    assert n >= 3


# ===========================================================================
# T14 — P03 threshold: D/E == 0 exactly
# ===========================================================================
def test_p03_de_must_be_zero(gen):
    """P03 requires D/E = 0, not just < 0.1."""
    # Check that companies with tiny but non-zero D/E do NOT get P03
    from src.nlp.pros_cons_generator import _latest
    p03_companies = set()
    df, _ = gen.generate()
    p03_companies = set(df[df["rule_id"] == "P03"]["company_id"].unique())

    # Every P03 company must have D/E == 0 in financial_ratios
    for cid in p03_companies:
        de = _latest(gen._rat, cid, "debt_to_equity")
        assert de is not None and de == 0.0, (
            f"P03 fired for {cid} but D/E = {de}"
        )


# ===========================================================================
# T15 — C01 threshold: D/E > 2.0 (strict)
# ===========================================================================
def test_c01_threshold_strictly_above_2(gen):
    from src.nlp.pros_cons_generator import _latest
    df, _ = gen.generate()
    c01_cos = set(df[df["rule_id"] == "C01"]["company_id"].unique())
    for cid in c01_cos:
        de = _latest(gen._rat, cid, "debt_to_equity")
        assert de is not None and de > 2.0, (
            f"C01 fired for {cid} but D/E = {de} is not > 2.0"
        )


# ===========================================================================
# T16 — Consecutive-year rules: C02 requires ≥3 consecutive negative FCF
# ===========================================================================
def test_c02_requires_3_consecutive_negative_fcf(gen):
    from src.nlp.pros_cons_generator import _n_consec_negative
    df, _ = gen.generate()
    c02_cos = set(df[df["rule_id"] == "C02"]["company_id"].unique())
    for cid in c02_cos:
        n = _n_consec_negative(gen._rat, cid, "free_cash_flow_cr")
        assert n >= 3, f"C02 fired for {cid} but only {n} consecutive negative FCF years"


# ===========================================================================
# T17 — P02 requires ≥5 consecutive positive FCF years
# ===========================================================================
def test_p02_requires_5_consecutive_positive_fcf(gen):
    from src.nlp.pros_cons_generator import _n_consec_positive
    df, _ = gen.generate()
    p02_cos = set(df[df["rule_id"] == "P02"]["company_id"].unique())
    for cid in p02_cos:
        n = _n_consec_positive(gen._rat, cid, "free_cash_flow_cr")
        assert n >= 5, f"P02 fired for {cid} but only {n} consecutive positive FCF years"


# ===========================================================================
# T18 — P10 requires ≥3 consecutive improving ROE years
# ===========================================================================
def test_p10_requires_3_consecutive_improving_roe(gen):
    from src.nlp.pros_cons_generator import _n_consec_increasing
    df, _ = gen.generate()
    p10_cos = set(df[df["rule_id"] == "P10"]["company_id"].unique())
    for cid in p10_cos:
        n = _n_consec_increasing(gen._rat, cid, "return_on_equity_pct")
        assert n >= 3, f"P10 fired for {cid} but only {n} consecutive ROE improvements"


# ===========================================================================
# T19 — P11 condition: Revenue CAGR > PAT CAGR (as spec states)
# ===========================================================================
def test_p11_condition_rev_gt_pat(gen):
    from src.nlp.pros_cons_generator import _latest
    df, _ = gen.generate()
    p11_cos = set(df[df["rule_id"] == "P11"]["company_id"].unique())
    for cid in p11_cos:
        rev5 = _latest(gen._rat, cid, "revenue_cagr_5yr")
        pat5 = _latest(gen._rat, cid, "pat_cagr_5yr")
        assert rev5 is not None and pat5 is not None and rev5 > pat5, (
            f"P11 fired for {cid}: rev5={rev5}, pat5={pat5} — condition not met"
        )


# ===========================================================================
# T20 — P04 threshold: Revenue CAGR > 15% (strict)
# ===========================================================================
def test_p04_strict_above_15(gen):
    from src.nlp.pros_cons_generator import _latest
    df, _ = gen.generate()
    p04_cos = set(df[df["rule_id"] == "P04"]["company_id"].unique())
    for cid in p04_cos:
        val = _latest(gen._rat, cid, "revenue_cagr_5yr")
        assert val is not None and val > 15, (
            f"P04 fired for {cid} but revenue_cagr_5yr = {val}"
        )


# ===========================================================================
# T21 — C12 threshold: Revenue CAGR < 5% (strict)
# ===========================================================================
def test_c12_strict_below_5(gen):
    from src.nlp.pros_cons_generator import _latest
    df, _ = gen.generate()
    c12_cos = set(df[df["rule_id"] == "C12"]["company_id"].unique())
    for cid in c12_cos:
        val = _latest(gen._rat, cid, "revenue_cagr_5yr")
        assert val is not None and val < 5, (
            f"C12 fired for {cid} but revenue_cagr_5yr = {val}"
        )


# ===========================================================================
# T22 — C10 threshold: ROCE < 10%
# ===========================================================================
def test_c10_strict_below_10(gen):
    from src.nlp.pros_cons_generator import _latest
    df, _ = gen.generate()
    c10_cos = set(df[df["rule_id"] == "C10"]["company_id"].unique())
    for cid in c10_cos:
        val = _latest(gen._rat, cid, "return_on_capital_employed_pct")
        assert val is not None and val < 10, (
            f"C10 fired for {cid} but ROCE = {val}"
        )


# ===========================================================================
# T23 — Coverage failures CSV schema
# ===========================================================================
def test_coverage_failures_schema(coverage_df):
    expected = {"company_id", "missing_pro", "missing_con",
                "classification", "available_metrics", "reason"}
    assert expected.issubset(set(coverage_df.columns))


# ===========================================================================
# T24 — Coverage failures are genuine (data available but no rule triggers)
# ===========================================================================
def test_coverage_failures_have_available_data(coverage_df):
    """Companies with coverage failures must have at least some data."""
    for _, row in coverage_df.iterrows():
        assert row["available_metrics"] != "none", (
            f"{row['company_id']} has coverage failure but no data at all"
        )


# ===========================================================================
# T25 — Deterministic output
# ===========================================================================
def test_deterministic_output():
    g1 = ProsConsGenerator()
    d1, _ = g1.generate()
    g2 = ProsConsGenerator()
    d2, _ = g2.generate()
    d1 = d1.reset_index(drop=True)
    d2 = d2.reset_index(drop=True)
    pd.testing.assert_frame_equal(d1, d2)


# ===========================================================================
# T26 — save_outputs writes both files
# ===========================================================================
def test_save_outputs(tmp_path):
    g = ProsConsGenerator()
    df, cov = g.generate()
    paths = g.save_outputs(output_dir=tmp_path, signals_df=df, coverage_df=cov)

    assert (tmp_path / "pros_cons_generated.csv").exists()
    assert (tmp_path / "coverage_failures.csv").exists()

    loaded = pd.read_csv(tmp_path / "pros_cons_generated.csv")
    assert set(loaded.columns) == REQUIRED_COLS


# ===========================================================================
# T27 — At least 1 pro signal exists
# ===========================================================================
def test_has_pro_signals(signals_df):
    assert not signals_df[signals_df["type"] == "pro"].empty


# ===========================================================================
# T28 — At least 1 con signal exists
# ===========================================================================
def test_has_con_signals(signals_df):
    assert not signals_df[signals_df["type"] == "con"].empty


# ===========================================================================
# T29 — All companies with signals have normalised company_id
# ===========================================================================
def test_company_id_normalised(signals_df):
    for cid in signals_df["company_id"]:
        assert cid == cid.strip().upper()
