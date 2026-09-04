"""
01_home.py — Home Screen
• 6 KPI tiles: Avg ROE, Median P/E, Median D/E, Total Companies,
               Median Revenue CAGR 5yr, Debt-Free Companies count
• Sector donut chart (11 sectors)
• Top-5 companies by composite quality score
• Year selector in sidebar (2019–2024)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Path shim so relative imports work when loaded by app.py
_SPRINT4 = Path(__file__).resolve().parents[1]
if str(_SPRINT4 / "src") not in sys.path:
    sys.path.insert(0, str(_SPRINT4 / "src"))

from dashboard.utils.db import get_companies, get_ratios_all, get_market_cap_all

# ── Sidebar year selector ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Home Settings")
    selected_year = st.selectbox(
        "Select Year",
        ["2024", "2023", "2022", "2021", "2020", "2019"],
        index=0,
        key="home_year",
    )

# ── Load data ────────────────────────────────────────────────────────────────
ratios_df  = get_ratios_all(year=selected_year)
mc_df      = get_market_cap_all(year=selected_year)
companies  = get_companies()

# Merge ratios + market_cap for full picture
merged = ratios_df.merge(
    mc_df[["company_id", "market_cap_crore", "pe_ratio", "pb_ratio", "dividend_yield_pct"]],
    on="company_id",
    how="left",
    suffixes=("", "_mc"),
)

# ── Page title ───────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style='margin-bottom:1.5rem;'>
      <h1 style='font-size:2rem; font-weight:700; color:#e6edf3; margin:0;'>
        📈 Nifty 100 Analytics
      </h1>
      <p style='color:#8b949e; margin:0.3rem 0 0 0; font-size:0.9rem;'>
        FY{selected_year} · 92 Companies · Real Financial Intelligence
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── KPI Tiles ────────────────────────────────────────────────────────────────
avg_roe        = merged["return_on_equity_pct"].mean()
median_pe      = merged["pe_ratio"].median()
median_de      = merged["debt_to_equity"].median()
total_cos      = len(companies)
median_rev_cagr = merged["revenue_cagr_5yr"].median()
debt_free_cnt  = int((merged["debt_to_equity"].fillna(999) <= 0.05).sum())


def _kpi(value_str: str, label: str, delta: str = "") -> str:
    delta_html = f"<div class='kpi-delta' style='color:#3fb950;'>{delta}</div>" if delta else ""
    return (
        f"<div class='kpi-card'>"
        f"<div class='kpi-value'>{value_str}</div>"
        f"<div class='kpi-label'>{label}</div>"
        f"{delta_html}"
        f"</div>"
    )


cols = st.columns(6)
kpi_data = [
    (f"{avg_roe:.1f}%"        if pd.notna(avg_roe)         else "N/A", "Avg ROE",              ""),
    (f"{median_pe:.1f}x"      if pd.notna(median_pe)        else "N/A", "Median P/E",            ""),
    (f"{median_de:.2f}x"      if pd.notna(median_de)        else "N/A", "Median D/E",            ""),
    (f"{total_cos}"                                                    , "Total Companies",       "Nifty 100"),
    (f"{median_rev_cagr:.1f}%" if pd.notna(median_rev_cagr) else "N/A", "Median Rev CAGR 5yr",  ""),
    (f"{debt_free_cnt}"                                                , "Debt-Free Companies",   "D/E ≤ 0.05"),
]
for col, (val, lbl, delta) in zip(cols, kpi_data):
    with col:
        st.markdown(_kpi(val, lbl, delta), unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

# ── Two-column layout: Donut + Top-5 table ───────────────────────────────────
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown("<div class='section-header'>Sector Breakdown</div>", unsafe_allow_html=True)

    sector_counts = (
        companies.groupby("broad_sector")["company_id"]
        .count()
        .reset_index()
        .rename(columns={"company_id": "count"})
        .sort_values("count", ascending=False)
    )

    SECTOR_COLORS = [
        "#58a6ff", "#3fb950", "#e3b341", "#f85149", "#bc8cff",
        "#39c5cf", "#ff9100", "#d2a8ff", "#7ee787", "#ffa657",
        "#79c0ff",
    ]

    fig_donut = go.Figure(
        go.Pie(
            labels=sector_counts["broad_sector"],
            values=sector_counts["count"],
            hole=0.55,
            marker_colors=SECTOR_COLORS,
            textinfo="label+percent",
            textfont_size=11,
            hovertemplate="<b>%{label}</b><br>Companies: %{value}<br>Share: %{percent}<extra></extra>",
        )
    )
    fig_donut.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=20, b=10),
        height=360,
        showlegend=False,
        annotations=[
            dict(
                text=f"<b>{total_cos}</b><br>Companies",
                x=0.5, y=0.5,
                font_size=14,
                font_color="#e6edf3",
                showarrow=False,
            )
        ],
    )
    st.plotly_chart(fig_donut, use_container_width=True)

with col_right:
    st.markdown("<div class='section-header'>Top 5 — Composite Quality Score</div>", unsafe_allow_html=True)

    top5 = (
        merged[["company_id", "company_name", "broad_sector",
                "composite_quality_score", "return_on_equity_pct",
                "revenue_cagr_5yr", "pe_ratio"]]
        .dropna(subset=["composite_quality_score"])
        .nlargest(5, "composite_quality_score")
        .reset_index(drop=True)
    )
    top5.index = top5.index + 1  # 1-based rank

    top5_display = top5.rename(columns={
        "company_id"             : "Ticker",
        "company_name"           : "Company",
        "broad_sector"           : "Sector",
        "composite_quality_score": "Quality Score",
        "return_on_equity_pct"   : "ROE %",
        "revenue_cagr_5yr"       : "Rev CAGR 5yr %",
        "pe_ratio"               : "P/E",
    })

    for col in ["Quality Score", "ROE %", "Rev CAGR 5yr %", "P/E"]:
        top5_display[col] = top5_display[col].apply(
            lambda x: f"{x:.1f}" if pd.notna(x) else "N/A"
        )

    st.dataframe(
        top5_display[["Ticker", "Company", "Sector", "Quality Score", "ROE %", "P/E"]],
        use_container_width=True,
        hide_index=False,
        height=280,
    )

    st.markdown("<br/>", unsafe_allow_html=True)
    # Sector KPI summary table
    st.markdown("<div class='section-header'>Sector Median KPIs</div>", unsafe_allow_html=True)
    sector_kpi = (
        merged.groupby("broad_sector")
        .agg(
            Companies=("company_id", "count"),
            Avg_ROE=("return_on_equity_pct", "mean"),
            Median_PE=("pe_ratio", "median"),
            Median_DE=("debt_to_equity", "median"),
        )
        .reset_index()
        .rename(columns={"broad_sector": "Sector"})
    )
    for c in ["Avg_ROE", "Median_PE", "Median_DE"]:
        sector_kpi[c] = sector_kpi[c].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")

    st.dataframe(sector_kpi, use_container_width=True, hide_index=True, height=240)

# ── Footer divider ────────────────────────────────────────────────────────────
st.markdown("<br/><hr/>", unsafe_allow_html=True)
st.markdown(
    f"<div style='text-align:center;font-size:0.72rem;color:#484f58;'>"
    f"Data as of FY{selected_year} · Nifty 100 Financial Intelligence Platform · Sprint 4"
    f"</div>",
    unsafe_allow_html=True,
)
