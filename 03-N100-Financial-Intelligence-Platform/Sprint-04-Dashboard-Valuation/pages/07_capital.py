"""
07_capital.py — Capital Allocation Map
• Treemap of all 92 companies using Sprint-2's actual 8 capital allocation patterns
  (loaded from Sprint-02-Financial-Ratio-Engine/output/capital_allocation.csv)
• Patterns: Reinvestor | Shareholder Returns | Liquidating Assets | Distress Signal
            Growth Funded by Debt | Cash Accumulator | Pre-Revenue | Mixed | Other
• Clicking a pattern shows the list of companies in that pattern
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

_SPRINT4 = Path(__file__).resolve().parents[1]
if str(_SPRINT4 / "src") not in sys.path:
    sys.path.insert(0, str(_SPRINT4 / "src"))

from dashboard.utils.db import get_capital_patterns

# ── Title ─────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='font-size:1.8rem;font-weight:700;color:#e6edf3;margin-bottom:0.5rem;'>"
    "💰 Capital Allocation Map"
    "</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#8b949e;font-size:0.88rem;margin-bottom:1.2rem;'>"
    "92 companies categorised by their Sprint-2 capital allocation pattern "
    "(Cash-Flow Sign Method: CFO / CFI / CFF signs). "
    "Tile size = Composite Quality Score. Select a pattern below to drill down."
    "</p>",
    unsafe_allow_html=True,
)

# ── Load data ──────────────────────────────────────────────────────────────────
df = get_capital_patterns(year="2024")

if df.empty:
    st.error("No capital allocation data found. Ensure Sprint-2 output exists.")
    st.stop()

df["score_size"] = df["composite_quality_score"].clip(lower=1).fillna(1)

# ── Colour palette for patterns ────────────────────────────────────────────────
PATTERN_COLORS = {
    "Reinvestor"            : "#1f6feb",
    "Shareholder Returns"   : "#3fb950",
    "Liquidating Assets"    : "#e3b341",
    "Distress Signal"       : "#f85149",
    "Growth Funded by Debt" : "#bc8cff",
    "Cash Accumulator"      : "#39c5cf",
    "Pre-Revenue"           : "#ff9100",
    "Mixed"                 : "#79c0ff",
    "Other"                 : "#484f58",
}

# ── Treemap ────────────────────────────────────────────────────────────────────
fig_treemap = go.Figure(go.Treemap(
    labels=df["company_name"],
    parents=df["pattern_label"],
    values=df["score_size"],
    ids=df["company_id"],
    textinfo="label",
    hovertemplate=(
        "<b>%{label}</b><br>"
        "Pattern: %{parent}<br>"
        "Quality Score: %{value:.1f}"
        "<extra></extra>"
    ),
    marker=dict(
        colors=[PATTERN_COLORS.get(p, "#30363d") for p in df["pattern_label"]],
        line=dict(width=1, color="#0d1117"),
    ),
    pathbar=dict(visible=True),
))

fig_treemap.update_layout(
    height=520,
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=0, r=0, t=10, b=10),
    font=dict(color="#e6edf3"),
)

st.plotly_chart(fig_treemap, use_container_width=True)

# ── Pattern legend ──────────────────────────────────────────────────────────────
PATTERN_DESCRIPTIONS = {
    "Reinvestor"            : "CFO+ / CFI- / CFF- — Earns cash, invests it, repays debt",
    "Shareholder Returns"   : "CFO+ / CFI- / CFF+ — Earns cash, invests, AND raises capital/pays dividends",
    "Liquidating Assets"    : "CFO- / CFI+ / CFF- — Sells assets to cover operations",
    "Distress Signal"       : "CFO- / CFI- / CFF+ — Needs external funding for both ops & capex",
    "Growth Funded by Debt" : "CFO+ / CFI- / CFF+ — Strong ops but raises debt/equity to accelerate growth",
    "Cash Accumulator"      : "CFO+ / CFI+ / CFF- — Earning + divesting + returning capital",
    "Pre-Revenue"           : "CFO- / CFI- / CFF- — Burning cash across all activities",
    "Mixed"                 : "Mixed cash flow signs — ambiguous allocation pattern",
    "Other"                 : "Unclassified or insufficient data",
}

with st.expander("ℹ️ Pattern Definitions"):
    for p, desc in PATTERN_DESCRIPTIONS.items():
        color = PATTERN_COLORS.get(p, "#484f58")
        cnt   = len(df[df["pattern_label"] == p])
        st.markdown(
            f"<div style='padding:4px 0;'>"
            f"<span style='display:inline-block;width:12px;height:12px;"
            f"background:{color};border-radius:2px;margin-right:8px;'></span>"
            f"<b style='color:#e6edf3;'>{p}</b>"
            f"<span style='color:#8b949e;font-size:0.82rem;'> ({cnt} companies) — {desc}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

# ── Pattern drill-down ─────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>Drill Down by Pattern</div>", unsafe_allow_html=True)

all_patterns   = sorted(df["pattern_label"].unique().tolist())
pattern_counts = df.groupby("pattern_label")["company_id"].count().to_dict()
pattern_opts   = [f"{p} ({pattern_counts.get(p, 0)} companies)" for p in all_patterns]

selected_pattern_opt = st.selectbox(
    "Select Capital Allocation Pattern",
    pattern_opts,
    key="capital_pattern_sel",
)
selected_pattern = selected_pattern_opt.rsplit(" (", 1)[0]

sub_df = df[df["pattern_label"] == selected_pattern].sort_values(
    "composite_quality_score", ascending=False
)

if sub_df.empty:
    st.info("No companies found for this pattern.")
else:
    count_in_pattern = len(sub_df)
    color = PATTERN_COLORS.get(selected_pattern, "#58a6ff")
    st.markdown(
        f"<div style='font-size:0.9rem;color:#8b949e;margin-bottom:0.75rem;'>"
        f"<b style='color:#e6edf3;'>{count_in_pattern}</b> companies in "
        f"<b style='color:{color};'>{selected_pattern}</b>"
        f"</div>",
        unsafe_allow_html=True,
    )

    show_cols = {
        "company_id"              : "Ticker",
        "company_name"            : "Company",
        "broad_sector"            : "Sector",
        "pattern_label"           : "Pattern",
        "composite_quality_score" : "Quality Score",
        "free_cash_flow_cr"       : "FCF (₹ Cr)",
        "market_cap_crore"        : "Mkt Cap (₹ Cr)",
    }
    table = sub_df[[c for c in show_cols if c in sub_df.columns]].rename(columns=show_cols)
    for c in ["Quality Score", "FCF (₹ Cr)", "Mkt Cap (₹ Cr)"]:
        if c in table.columns:
            table[c] = table[c].apply(lambda x: f"{x:,.1f}" if pd.notna(x) else "N/A")

    st.dataframe(table, use_container_width=True, hide_index=True, height=340)

# ── Pattern summary table ──────────────────────────────────────────────────────
with st.expander("📋 All Patterns — Summary Table"):
    summary = (
        df.groupby("pattern_label")
        .agg(
            Companies=("company_id", "count"),
            Avg_Score=("composite_quality_score", "mean"),
            Avg_FCF=("free_cash_flow_cr", "mean"),
        )
        .reset_index()
        .rename(columns={"pattern_label": "Pattern"})
        .sort_values("Companies", ascending=False)
    )
    for c in ["Avg_Score", "Avg_FCF"]:
        summary[c] = summary[c].apply(lambda x: f"{x:,.1f}" if pd.notna(x) else "N/A")
    st.dataframe(summary, use_container_width=True, hide_index=True)
