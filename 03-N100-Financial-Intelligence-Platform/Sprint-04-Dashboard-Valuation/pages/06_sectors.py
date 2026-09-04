"""
06_sectors.py — Sector Analysis Screen
• Sector dropdown
• Bubble chart: X=Revenue, Y=ROE, bubble size=Market Cap, colour=sub_sector
• Sector median KPI bar chart
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

_SPRINT4 = Path(__file__).resolve().parents[1]
if str(_SPRINT4 / "src") not in sys.path:
    sys.path.insert(0, str(_SPRINT4 / "src"))

from dashboard.utils.db import get_sector_bubble_data, get_ratios_all

# ── Title ─────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='font-size:1.8rem;font-weight:700;color:#e6edf3;margin-bottom:0.5rem;'>"
    "🏭 Sector Analysis"
    "</h1>",
    unsafe_allow_html=True,
)

# ── Controls ───────────────────────────────────────────────────────────────────
bubble_df = get_sector_bubble_data(year="2024")

all_sectors  = sorted(bubble_df["broad_sector"].dropna().unique().tolist())
with st.sidebar:
    st.markdown("### 🏭 Sector Settings")
    selected_sector = st.selectbox("Select Sector", ["All Sectors"] + all_sectors, key="sector_sel")

if selected_sector != "All Sectors":
    filtered = bubble_df[bubble_df["broad_sector"] == selected_sector].copy()
else:
    filtered = bubble_df.copy()

filtered = filtered.dropna(subset=["revenue_cr", "roe", "market_cap_crore"])

# ── Bubble chart ───────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>Revenue vs ROE Bubble Chart</div>", unsafe_allow_html=True)

if filtered.empty:
    st.warning("No data available for the selected sector.")
else:
    sub_sectors = sorted(filtered["sub_sector"].dropna().unique().tolist())
    PALETTE = px.colors.qualitative.Plotly + px.colors.qualitative.Dark24
    colour_map = {s: PALETTE[i % len(PALETTE)] for i, s in enumerate(sub_sectors)}

    fig_bubble = go.Figure()
    for ss in sub_sectors:
        ss_df = filtered[filtered["sub_sector"] == ss]
        if ss_df.empty:
            continue
        fig_bubble.add_trace(go.Scatter(
            x=ss_df["revenue_cr"],
            y=ss_df["roe"],
            mode="markers",
            name=ss,
            marker=dict(
                size=ss_df["market_cap_crore"].clip(lower=1000).apply(lambda v: max(8, min(60, v / 20000))),
                color=colour_map.get(ss, "#58a6ff"),
                opacity=0.8,
                line=dict(width=0.5, color="white"),
                sizemode="diameter",
            ),
            text=ss_df["company_name"],
            customdata=ss_df[["company_id", "market_cap_crore"]],
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Revenue: ₹%{x:,.0f} Cr<br>"
                "ROE: %{y:.1f}%<br>"
                "Market Cap: ₹%{customdata[1]:,.0f} Cr"
                "<extra>%{name}</extra>"
            ),
        ))

    fig_bubble.update_layout(
        height=480,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8b949e"),
        xaxis=dict(
            title="Revenue (₹ Cr)", gridcolor="#21262d",
            tickfont_color="#8b949e", tickprefix="₹", ticksuffix=" Cr",
        ),
        yaxis=dict(
            title="ROE %", gridcolor="#21262d",
            tickfont_color="#8b949e", ticksuffix="%",
        ),
        legend=dict(
            font_color="#e6edf3", bgcolor="rgba(0,0,0,0)",
            orientation="v", x=1.02, y=1,
        ),
        margin=dict(l=10, r=140, t=20, b=10),
    )
    st.plotly_chart(fig_bubble, use_container_width=True)

# ── Sector median KPI bar chart ────────────────────────────────────────────────
st.markdown("<div class='section-header'>Sector Median KPIs</div>", unsafe_allow_html=True)

ratios_all = get_ratios_all(year="2024")
kpi_fields = {
    "return_on_equity_pct"     : "ROE %",
    "return_on_capital_employed_pct": "ROCE %",
    "net_profit_margin_pct"    : "NPM %",
    "operating_profit_margin_pct": "OPM %",
    "revenue_cagr_5yr"         : "Rev CAGR 5yr %",
    "debt_to_equity"           : "D/E",
}

sector_med = (
    ratios_all.groupby("broad_sector")[list(kpi_fields.keys())]
    .median()
    .reset_index()
)
sector_med.columns = ["Sector"] + list(kpi_fields.values())

if selected_sector != "All Sectors":
    plot_med = sector_med[sector_med["Sector"] == selected_sector]
else:
    plot_med = sector_med

kpi_col_select = st.selectbox(
    "KPI to display",
    list(kpi_fields.values()),
    key="sector_kpi_sel",
)

plot_med_sorted = plot_med.sort_values(kpi_col_select, ascending=True)

fig_bar = go.Figure(go.Bar(
    x=plot_med_sorted[kpi_col_select],
    y=plot_med_sorted["Sector"],
    orientation="h",
    marker=dict(
        color=plot_med_sorted[kpi_col_select],
        colorscale=[[0, "#1a4731"], [0.5, "#3fb950"], [1, "#58a6ff"]],
        showscale=False,
    ),
    hovertemplate="<b>%{y}</b><br>" + kpi_col_select + ": %{x:.1f}<extra></extra>",
))
fig_bar.update_layout(
    height=360,
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#8b949e"),
    xaxis=dict(gridcolor="#21262d", tickfont_color="#8b949e"),
    yaxis=dict(tickfont_color="#e6edf3"),
    margin=dict(l=10, r=10, t=20, b=10),
)
st.plotly_chart(fig_bar, use_container_width=True)
