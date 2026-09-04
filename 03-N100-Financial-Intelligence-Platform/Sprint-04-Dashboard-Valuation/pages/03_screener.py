"""
03_screener.py — Screener Screen
• 10 metric sliders in sidebar
• 6 preset buttons (Quality, Value, Growth, Dividend, Debt-Free, Turnaround)
• Financials sector EXEMPT from D/E filter (spec requirement)
• Debt-Free companies (icr_label == "Debt Free") pass every ICR minimum
• Turnaround Watch: Revenue CAGR 3yr > 10%, FCF > 0, D/E declining YoY
• Live-updating results table with result count label
• CSV download button (numeric values preserved in CSV)
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

_SPRINT4 = Path(__file__).resolve().parents[1]
if str(_SPRINT4 / "src") not in sys.path:
    sys.path.insert(0, str(_SPRINT4 / "src"))

from dashboard.utils.db import get_ratios_all, get_market_cap_all, get_de_decline_flags

# ── Preset definitions ────────────────────────────────────────────────────────
PRESETS: dict[str, dict] = {
    "Quality Compounder": {
        "roe_min": 15.0, "de_max": 1.0, "fcf_min": 0.0,
        "rev_cagr_min": 10.0, "pat_cagr_min": 0.0, "opm_min": 0.0,
        "pe_max": 100.0, "pb_max": 100.0, "div_yield_min": 0.0, "icr_min": 0.0,
        "turnaround": False,
    },
    "Value Pick": {
        "roe_min": 0.0, "de_max": 2.0, "fcf_min": -9999.0,
        "rev_cagr_min": 0.0, "pat_cagr_min": 0.0, "opm_min": 0.0,
        "pe_max": 20.0, "pb_max": 3.0, "div_yield_min": 1.0, "icr_min": 0.0,
        "turnaround": False,
    },
    "Growth Accelerator": {
        "roe_min": 0.0, "de_max": 2.0, "fcf_min": -9999.0,
        "rev_cagr_min": 15.0, "pat_cagr_min": 20.0, "opm_min": 0.0,
        "pe_max": 100.0, "pb_max": 100.0, "div_yield_min": 0.0, "icr_min": 0.0,
        "turnaround": False,
    },
    "Dividend Champion": {
        "roe_min": 0.0, "de_max": 100.0, "fcf_min": 0.0,
        "rev_cagr_min": 0.0, "pat_cagr_min": 0.0, "opm_min": 0.0,
        "pe_max": 100.0, "pb_max": 100.0, "div_yield_min": 2.0, "icr_min": 0.0,
        "turnaround": False,
    },
    "Debt-Free Blue Chip": {
        "roe_min": 12.0, "de_max": 0.05, "fcf_min": -9999.0,
        "rev_cagr_min": 0.0, "pat_cagr_min": 0.0, "opm_min": 0.0,
        "pe_max": 100.0, "pb_max": 100.0, "div_yield_min": 0.0, "icr_min": 0.0,
        "turnaround": False,
    },
    "Turnaround Watch": {
        # Rev CAGR 3yr > 10%, FCF > 0, D/E declining YoY
        "roe_min": 0.0, "de_max": 100.0, "fcf_min": 0.0,
        "rev_cagr_min": 10.0, "pat_cagr_min": 0.0, "opm_min": 0.0,
        "pe_max": 100.0, "pb_max": 100.0, "div_yield_min": 0.0, "icr_min": 0.0,
        "turnaround": True,   # activates D/E declining + 3yr CAGR logic
    },
}

# Short aliases mapping to canonical full names
PRESET_ALIASES: dict[str, str] = {
    "Quality": "Quality Compounder",
    "Value": "Value Pick",
    "Growth": "Growth Accelerator",
    "Dividend": "Dividend Champion",
    "Debt-Free": "Debt-Free Blue Chip",
    "Turnaround": "Turnaround Watch",
}

# ── Session state init ────────────────────────────────────────────────────────
DEFAULTS: dict = {
    "scr_roe_min": 0.0, "scr_de_max": 10.0, "scr_fcf_min": -500.0,
    "scr_rev_cagr_min": 0.0, "scr_pat_cagr_min": 0.0, "scr_opm_min": 0.0,
    "scr_pe_max": 100.0, "scr_pb_max": 20.0, "scr_div_yield_min": 0.0,
    "scr_icr_min": 0.0, "scr_turnaround_mode": False,
    "scr_active_preset": None,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar controls ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Screener Filters")

    # Preset buttons
    st.markdown("**Presets**")
    preset_cols = st.columns(2)
    preset_names = list(PRESETS.keys())
    for i, name in enumerate(preset_names):
        col = preset_cols[i % 2]
        if col.button(name, key=f"preset_{i}", use_container_width=True):
            p = PRESETS[name]
            st.session_state["scr_roe_min"]          = p["roe_min"]
            st.session_state["scr_de_max"]            = p["de_max"]
            st.session_state["scr_fcf_min"]           = p["fcf_min"]
            st.session_state["scr_rev_cagr_min"]      = p["rev_cagr_min"]
            st.session_state["scr_pat_cagr_min"]      = p["pat_cagr_min"]
            st.session_state["scr_opm_min"]           = p["opm_min"]
            st.session_state["scr_pe_max"]            = p["pe_max"]
            st.session_state["scr_pb_max"]            = p["pb_max"]
            st.session_state["scr_div_yield_min"]     = p["div_yield_min"]
            st.session_state["scr_icr_min"]           = p["icr_min"]
            st.session_state["scr_turnaround_mode"]   = p["turnaround"]
            st.session_state["scr_active_preset"]     = name
            st.rerun()

    if st.session_state.get("scr_active_preset"):
        active_name = st.session_state["scr_active_preset"]
        st.info(f"Active Preset: **{active_name}**")
        if st.button("✕ Reset to Custom Filters", use_container_width=True):
            st.session_state["scr_active_preset"] = None
            for dk, dv in DEFAULTS.items():
                st.session_state[dk] = dv
            st.rerun()

    st.markdown("---")

    roe_min       = st.slider("ROE min (%)",          0.0,  50.0, st.session_state["scr_roe_min"],      0.5,  key="scr_roe_min")
    de_max        = st.slider("D/E max (x)",          0.0,  10.0, st.session_state["scr_de_max"],       0.05, key="scr_de_max")
    fcf_min       = st.slider("FCF min (₹ Cr)",    -500.0, 5000.0, st.session_state["scr_fcf_min"],    50.0, key="scr_fcf_min")
    rev_cagr_min  = st.slider("Revenue CAGR min (%)", 0.0,  40.0, st.session_state["scr_rev_cagr_min"], 0.5,  key="scr_rev_cagr_min")
    pat_cagr_min  = st.slider("PAT CAGR 5yr min (%)", 0.0,  50.0, st.session_state["scr_pat_cagr_min"], 0.5,  key="scr_pat_cagr_min")
    opm_min       = st.slider("OPM min (%)",          0.0,  50.0, st.session_state["scr_opm_min"],      0.5,  key="scr_opm_min")
    pe_max        = st.slider("P/E max (x)",          0.0, 100.0, st.session_state["scr_pe_max"],       1.0,  key="scr_pe_max")
    pb_max        = st.slider("P/B max (x)",          0.0,  20.0, st.session_state["scr_pb_max"],       0.1,  key="scr_pb_max")
    div_yield_min = st.slider("Dividend Yield min (%)", 0.0, 10.0, st.session_state["scr_div_yield_min"], 0.1, key="scr_div_yield_min")
    icr_min       = st.slider("ICR min (x)",          0.0,  20.0, st.session_state["scr_icr_min"],      0.1,  key="scr_icr_min")
    turnaround_mode = st.session_state.get("scr_turnaround_mode", False)

    if turnaround_mode:
        st.markdown(
            "<div style='background:rgba(88,166,255,0.1);border:1px solid #1f6feb;"
            "border-radius:6px;padding:0.5rem 0.75rem;font-size:0.8rem;color:#58a6ff;'>"
            "⚡ Turnaround mode active — D/E declining YoY enforced + Rev CAGR uses 3yr"
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        "<div style='font-size:0.72rem;color:#484f58;margin-top:0.5rem;'>"
        "ℹ️ Financials sector exempt from D/E filter. "
        "Debt-Free companies pass all ICR minimums."
        "</div>",
        unsafe_allow_html=True,
    )

# ── Load data ─────────────────────────────────────────────────────────────────
ratios_df   = get_ratios_all(year="2024")
mc_df       = get_market_cap_all(year="2024")
de_flags    = get_de_decline_flags()          # D/E declining YoY flags

merged = ratios_df.merge(
    mc_df[["company_id", "pe_ratio", "pb_ratio", "dividend_yield_pct", "market_cap_crore"]],
    on="company_id", how="left", suffixes=("", "_mc"),
)
merged = merged.merge(
    de_flags[["company_id", "de_declining"]],
    on="company_id", how="left",
)
merged["de_declining"] = merged["de_declining"].fillna(False)

# ── Filter helpers (strict and inclusive) ─────────────────────────────────────
def _gt(s: pd.Series, val: float) -> pd.Series:
    """Strictly greater than — NaN fails the filter."""
    return s.fillna(float("-inf")) > val

def _lt(s: pd.Series, val: float) -> pd.Series:
    """Strictly less than — NaN fails the filter."""
    return s.fillna(float("inf")) < val

def _ge(s: pd.Series, val: float) -> pd.Series:
    """Greater-than-or-equal — NaN fails the filter."""
    return s.fillna(float("-inf")) >= val

def _le(s: pd.Series, val: float) -> pd.Series:
    """Less-than-or-equal — NaN fails the filter."""
    return s.fillna(float("inf")) <= val

def apply_preset(df: pd.DataFrame, preset_name: str) -> pd.Series:
    """
    Apply strict preset conditions per specification:
    • Quality Compounder: ROE > 15%, D/E < 1.0 (Financials exempt), FCF > 0, Revenue CAGR 5yr > 10%
    • Value Pick: P/E < 20, P/B < 3.0, D/E < 2.0 (Financials exempt), Dividend Yield > 1%
    • Growth Accelerator: PAT CAGR 5yr > 20%, Revenue CAGR 5yr > 15%, D/E < 2.0 (Financials exempt)
    • Dividend Champion: Dividend Yield > 2%, Dividend Payout < 80%, FCF > 0
    • Debt-Free Blue Chip: D/E = 0 / documented proxy (D/E <= 0.05 or Financials exempt), ROE > 12%, Revenue > 5000 Cr
    • Turnaround Watch: Revenue CAGR 3yr > 10%, FCF > 0 (strictly positive), D/E declining YoY
    """
    is_financials = df["broad_sector"].eq("Financials")
    name = PRESET_ALIASES.get(preset_name, preset_name)

    if name == "Quality Compounder":
        de_pass = is_financials | _lt(df["debt_to_equity"], 1.0)
        return (
            _gt(df["return_on_equity_pct"], 15.0)
            & de_pass
            & _gt(df["free_cash_flow_cr"], 0.0)
            & _gt(df["revenue_cagr_5yr"], 10.0)
        )
    elif name == "Value Pick":
        de_pass = is_financials | _lt(df["debt_to_equity"], 2.0)
        return (
            _lt(df["pe_ratio"], 20.0)
            & _lt(df["pb_ratio"], 3.0)
            & de_pass
            & _gt(df["dividend_yield_pct"], 1.0)
        )
    elif name == "Growth Accelerator":
        de_pass = is_financials | _lt(df["debt_to_equity"], 2.0)
        return (
            _gt(df["pat_cagr_5yr"], 20.0)
            & _gt(df["revenue_cagr_5yr"], 15.0)
            & de_pass
        )
    elif name == "Dividend Champion":
        payout = df["dividend_payout_ratio_pct"]
        return (
            _gt(df["dividend_yield_pct"], 2.0)
            & _lt(payout, 80.0)
            & _gt(df["free_cash_flow_cr"], 0.0)
        )
    elif name == "Debt-Free Blue Chip":
        debt_free = (
            is_financials
            | _le(df["debt_to_equity"], 0.05)
            | df.get("icr_label", pd.Series(index=df.index)).eq("Debt Free")
        )
        sales = df["sales"] if "sales" in df.columns else pd.Series(0.0, index=df.index)
        return (
            debt_free
            & _gt(df["return_on_equity_pct"], 12.0)
            & _gt(sales, 5000.0)
        )
    elif name == "Turnaround Watch":
        de_declining = df["de_declining"].eq(True)
        return (
            _gt(df["revenue_cagr_3yr"], 10.0)
            & _gt(df["free_cash_flow_cr"], 0.0)
            & de_declining
        )
    return pd.Series([True] * len(df), index=df.index)

# ── Apply filters ─────────────────────────────────────────────────────────────
active_preset = st.session_state.get("scr_active_preset")

if active_preset and active_preset in PRESETS:
    mask = apply_preset(merged, active_preset)
else:
    is_financials = merged["broad_sector"].eq("Financials")

    # Financials exempt from D/E filter
    de_pass = is_financials | _le(merged["debt_to_equity"], de_max)

    # Debt-Free proxy — D/E <= 0.05 or icr_label == 'Debt Free'
    debt_free = (
        is_financials
        | (merged["debt_to_equity"].fillna(float("inf")) <= 0.05)
        | merged.get("icr_label", pd.Series(index=merged.index)).eq("Debt Free")
    )
    icr_pass = debt_free | _ge(merged["interest_coverage"], icr_min)

    # Turnaround uses 3yr Revenue CAGR + D/E declining YoY + FCF strictly > 0
    if turnaround_mode:
        rev_cagr_pass = _gt(merged["revenue_cagr_3yr"], rev_cagr_min)
        fcf_pass = _gt(merged["free_cash_flow_cr"], 0.0)
        de_decline_pass = merged["de_declining"].eq(True)
    else:
        rev_cagr_pass = _ge(merged["revenue_cagr_5yr"], rev_cagr_min)
        fcf_pass = _ge(merged["free_cash_flow_cr"], fcf_min)
        de_decline_pass = pd.Series([True] * len(merged), index=merged.index)

    mask = (
        _ge(merged["return_on_equity_pct"],        roe_min)
        & de_pass
        & fcf_pass
        & rev_cagr_pass
        & _ge(merged["pat_cagr_5yr"],               pat_cagr_min)
        & _ge(merged["operating_profit_margin_pct"], opm_min)
        & _le(merged["pe_ratio"],                   pe_max)
        & _le(merged["pb_ratio"],                   pb_max)
        & _ge(merged["dividend_yield_pct"],         div_yield_min)
        & icr_pass
        & de_decline_pass
    )

results = merged[mask].copy()

# ── Page display ──────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='font-size:1.8rem;font-weight:700;color:#e6edf3;margin-bottom:0.5rem;'>"
    "🔍 Stock Screener"
    "</h1>",
    unsafe_allow_html=True,
)

count = len(results)
color = "#3fb950" if count >= 5 else ("#e3b341" if count >= 1 else "#f85149")
st.markdown(
    f"<div style='font-size:1.05rem;font-weight:600;color:{color};margin-bottom:1rem;'>"
    f"{'✅' if count >= 5 else '⚠️'} {count} {'companies match' if count != 1 else 'company matches'} your filters"
    f"</div>",
    unsafe_allow_html=True,
)

if results.empty:
    st.warning("No companies match the current filter criteria. Try relaxing some sliders.")
else:
    # Determine which CAGR column to show based on mode
    cagr_col     = "revenue_cagr_3yr" if turnaround_mode else "revenue_cagr_5yr"
    cagr_label   = "Rev CAGR 3yr %" if turnaround_mode else "Rev CAGR 5yr %"

    display_cols = {
        "company_id"               : "Ticker",
        "company_name"             : "Company",
        "broad_sector"             : "Sector",
        "composite_quality_score"  : "Quality Score",
        "return_on_equity_pct"     : "ROE %",
        "debt_to_equity"           : "D/E",
        "free_cash_flow_cr"        : "FCF (₹ Cr)",
        cagr_col                   : cagr_label,
        "pat_cagr_5yr"             : "PAT CAGR 5yr %",
        "operating_profit_margin_pct": "OPM %",
        "pe_ratio"                 : "P/E",
        "pb_ratio"                 : "P/B",
        "dividend_yield_pct"       : "Div Yield %",
        "interest_coverage"        : "ICR",
        "market_cap_crore"         : "Mkt Cap (₹ Cr)",
    }

    # --- Raw numeric table for CSV download (before string formatting) ---
    raw_table = results[[c for c in display_cols if c in results.columns]].rename(
        columns=display_cols
    ).reset_index(drop=True)

    # --- Display table with formatted strings ---
    display_table = raw_table.copy()
    num_cols = [
        "Quality Score", "ROE %", "D/E", "FCF (₹ Cr)", cagr_label,
        "PAT CAGR 5yr %", "OPM %", "P/E", "P/B", "Div Yield %",
        "ICR", "Mkt Cap (₹ Cr)",
    ]
    for c in num_cols:
        if c in display_table.columns:
            display_table[c] = display_table[c].apply(
                lambda x: f"{x:,.1f}" if pd.notna(x) else "N/A"
            )

    st.dataframe(display_table, use_container_width=True, hide_index=True, height=400)

    # CSV download — uses raw_table (numeric values preserved)
    csv_buf = io.StringIO()
    raw_table.to_csv(csv_buf, index=False)
    st.download_button(
        label="📥 Download Results as CSV",
        data=csv_buf.getvalue().encode("utf-8"),
        file_name="screener_results.csv",
        mime="text/csv",
    )
