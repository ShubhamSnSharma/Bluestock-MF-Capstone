"""
05_trends.py — Trend Analysis Screen
• Company search + multi-metric selector (overlay up to 3 metrics)
• 10-year line chart with YoY % change annotation on each point
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

from dashboard.utils.db import get_companies, get_ratios

# ── Title ─────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='font-size:1.8rem;font-weight:700;color:#e6edf3;margin-bottom:0.5rem;'>"
    "📈 Trend Analysis"
    "</h1>",
    unsafe_allow_html=True,
)

# ── Metric catalogue ───────────────────────────────────────────────────────────
METRIC_OPTIONS = {
    "ROE %"              : "return_on_equity_pct",
    "ROCE %"             : "return_on_capital_employed_pct",
    "Net Profit Margin %" : "net_profit_margin_pct",
    "OPM %"              : "operating_profit_margin_pct",
    "D/E Ratio"          : "debt_to_equity",
    "Interest Coverage"  : "interest_coverage",
    "FCF (₹ Cr)"         : "free_cash_flow_cr",
    "EPS"                : "earnings_per_share",
    "Revenue CAGR 5yr %" : "revenue_cagr_5yr",
    "PAT CAGR 5yr %"     : "pat_cagr_5yr",
    "Asset Turnover"     : "asset_turnover",
    "Composite Score"    : "composite_quality_score",
}

# ── Controls ───────────────────────────────────────────────────────────────────
companies_df = get_companies()
ticker_list  = sorted(companies_df["company_id"].tolist())
name_map     = dict(zip(companies_df["company_id"], companies_df["company_name"]))

col_ctrl1, col_ctrl2 = st.columns([2, 3])
with col_ctrl1:
    ticker = st.selectbox(
        "Company",
        [""] + ticker_list,
        format_func=lambda t: "Select a company…" if not t else f"{t} — {name_map.get(t, t)}",
        key="trend_ticker",
    )

with col_ctrl2:
    selected_metrics_labels = st.multiselect(
        "Select up to 3 metrics",
        list(METRIC_OPTIONS.keys()),
        default=["ROE %", "ROCE %"],
        max_selections=3,
        key="trend_metrics",
    )

if not ticker:
    st.info("👆 Select a company to view its trend charts.")
    st.stop()

if not selected_metrics_labels:
    st.warning("Please select at least one metric.")
    st.stop()

selected_cols = [METRIC_OPTIONS[lbl] for lbl in selected_metrics_labels]

# ── Load data ──────────────────────────────────────────────────────────────────
ratios_df = get_ratios(ticker=ticker)
num_df    = ratios_df[ratios_df["year"] != "TTM"].copy()
num_df["year_int"] = num_df["year"].astype(int)
num_df = num_df.sort_values("year_int")

if num_df.empty:
    st.warning(f"No historical ratio data found for **{ticker}**.")
    st.stop()

# ── Build chart ────────────────────────────────────────────────────────────────
COLORS = ["#58a6ff", "#3fb950", "#e3b341"]

fig = go.Figure()

for idx, (col, label) in enumerate(zip(selected_cols, selected_metrics_labels)):
    if col not in num_df.columns:
        continue

    series = num_df[["year", col]].dropna(subset=[col]).copy()
    if series.empty:
        continue

    yoy_pct = series[col].pct_change() * 100
    annotations_text = [
        f"+{v:.1f}%" if v > 0 else f"{v:.1f}%" if pd.notna(v) else ""
        for v in yoy_pct
    ]

    fig.add_trace(go.Scatter(
        x=series["year"].astype(str),
        y=series[col],
        mode="lines+markers+text",
        name=label,
        line=dict(color=COLORS[idx % len(COLORS)], width=2.5),
        marker=dict(size=8, color=COLORS[idx % len(COLORS)]),
        text=annotations_text,
        textposition="top center",
        textfont=dict(size=9, color=COLORS[idx % len(COLORS)]),
        hovertemplate=f"FY%{{x}}<br>{label}: %{{y:.2f}}<extra></extra>",
        yaxis=f"y{idx + 1}" if idx > 0 else "y",
    ))

# Build multiple y-axes if >1 metric
layout_kwargs: dict = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#8b949e"),
    height=420,
    margin=dict(l=10, r=40, t=40, b=40),
    xaxis=dict(gridcolor="#21262d", tickfont_color="#8b949e"),
    legend=dict(orientation="h", y=-0.15, font_color="#e6edf3"),
)

if len(selected_cols) >= 1:
    layout_kwargs["yaxis"] = dict(
        title=selected_metrics_labels[0],
        gridcolor="#21262d",
        tickfont_color=COLORS[0],
    )
if len(selected_cols) >= 2:
    layout_kwargs["yaxis2"] = dict(
        title=selected_metrics_labels[1],
        overlaying="y", side="right",
        tickfont_color=COLORS[1],
        showgrid=False,
    )
if len(selected_cols) >= 3:
    layout_kwargs["yaxis3"] = dict(
        title=selected_metrics_labels[2],
        overlaying="y", side="right",
        anchor="free", position=0.97,
        tickfont_color=COLORS[2],
        showgrid=False,
    )

fig.update_layout(**layout_kwargs)

company_name = name_map.get(ticker, ticker)
st.markdown(
    f"<div class='section-header'>{company_name} — {' / '.join(selected_metrics_labels)} Trend</div>",
    unsafe_allow_html=True,
)
st.plotly_chart(fig, use_container_width=True)

# ── Raw data table ─────────────────────────────────────────────────────────────
with st.expander("📋 View Raw Data"):
    show_cols = ["year"] + [c for c in selected_cols if c in num_df.columns]
    show_df   = num_df[show_cols].rename(
        columns={c: l for c, l in zip(selected_cols, selected_metrics_labels)}
    )
    st.dataframe(show_df, use_container_width=True, hide_index=True)
