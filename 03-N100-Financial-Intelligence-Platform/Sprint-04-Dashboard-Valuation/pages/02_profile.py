"""
02_profile.py — Company Profile Screen
• Text search box with autocomplete dropdown
• Company card: name, sector, sub-sector, NSE ticker, about description
• 6 KPI tiles: ROE, ROCE, Net Profit Margin, D/E, Revenue CAGR 5yr, FCF
• 10-year Revenue & Net Profit bar chart (Plotly)
• ROE and ROCE dual-axis line chart over 10 years
• Pros & Cons badges
• Friendly "Ticker not found" message
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

from dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_pl,
    get_market_cap_all,
    get_proscons,
)

# ── Title ────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='font-size:1.8rem;font-weight:700;color:#e6edf3;margin-bottom:0.5rem;'>"
    "🏢 Company Profile"
    "</h1>",
    unsafe_allow_html=True,
)

# ── Search box ───────────────────────────────────────────────────────────────
companies_df = get_companies()
ticker_list  = sorted(companies_df["company_id"].tolist())
name_map     = dict(zip(companies_df["company_id"], companies_df["company_name"]))

options     = [f"{t} — {name_map[t]}" for t in ticker_list]
search_opts = [""] + options

selected_opt = st.selectbox(
    "Search company name or ticker",
    search_opts,
    format_func=lambda x: x if x else "Type or select a company…",
    key="profile_search",
)

if not selected_opt:
    st.info("👆 Select a company from the dropdown above to view its profile.")
    st.stop()

ticker = selected_opt.split(" — ")[0].strip()

# ── Validate ticker ───────────────────────────────────────────────────────────
row = companies_df[companies_df["company_id"] == ticker]
if row.empty:
    st.error("⚠️ Ticker not found — please try another.")
    st.stop()

row = row.iloc[0]

# ── Load data ────────────────────────────────────────────────────────────────
ratios_df = get_ratios(ticker=ticker)
pl_df     = get_pl(ticker=ticker)
pc_df     = get_proscons(ticker=ticker)

# Latest year ratios (2024 preferred, else most recent numeric)
numeric_years = ratios_df[ratios_df["year"] != "TTM"]["year"].sort_values(ascending=False)
latest_year   = numeric_years.iloc[0] if not numeric_years.empty else None
latest_ratios = ratios_df[ratios_df["year"] == latest_year].iloc[0] if latest_year else None

mc_all  = get_market_cap_all(year=latest_year or "2024")
mc_row  = mc_all[mc_all["company_id"] == ticker]
fcf_val = latest_ratios["free_cash_flow_cr"] if latest_ratios is not None else None

# ── Company card ─────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style='background:linear-gradient(135deg,#161b22,#1c2128);
                border:1px solid #30363d;border-radius:14px;padding:1.4rem 1.8rem;
                margin-bottom:1.5rem;'>
      <div style='display:flex;align-items:flex-start;gap:1.5rem;'>
        <div>
          <div style='font-size:1.4rem;font-weight:700;color:#e6edf3;'>{row['company_name']}</div>
          <div style='margin-top:0.35rem;'>
            <span class='badge-blue'>🏷 {ticker}</span>
            <span class='badge-blue'>🏭 {row['broad_sector']}</span>
            <span class='badge-blue'>📂 {row['sub_sector']}</span>
          </div>
          <div style='margin-top:0.75rem;font-size:0.83rem;color:#8b949e;line-height:1.6;max-width:700px;'>
            {str(row['about_company'])[:400] + '…' if len(str(row['about_company'] or '')) > 400 else row['about_company'] or '—'}
          </div>
          <div style='margin-top:0.6rem;font-size:0.78rem;'>
            <a href='{row["nse_profile"]}' target='_blank' style='color:#58a6ff;margin-right:1rem;'>📊 NSE Profile</a>
            <a href='{row["bse_profile"]}' target='_blank' style='color:#58a6ff;'>📋 BSE Profile</a>
          </div>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── 6 KPI tiles ──────────────────────────────────────────────────────────────
def _safe(val, fmt=".1f", suffix=""):
    return f"{val:{fmt}}{suffix}" if pd.notna(val) and val is not None else "N/A"


def _kpi(value_str: str, label: str) -> str:
    return (
        f"<div class='kpi-card'>"
        f"<div class='kpi-value'>{value_str}</div>"
        f"<div class='kpi-label'>{label}</div>"
        f"</div>"
    )


roe_val  = latest_ratios["return_on_equity_pct"]          if latest_ratios is not None else None
roce_val = latest_ratios["return_on_capital_employed_pct"] if latest_ratios is not None else None
npm_val  = latest_ratios["net_profit_margin_pct"]          if latest_ratios is not None else None
de_val   = latest_ratios["debt_to_equity"]                  if latest_ratios is not None else None
cagr_val = latest_ratios["revenue_cagr_5yr"]               if latest_ratios is not None else None

kpi_cols = st.columns(6)
kpi_items = [
    (_safe(roe_val,  ".1f", "%"), "ROE"),
    (_safe(roce_val, ".1f", "%"), "ROCE"),
    (_safe(npm_val,  ".1f", "%"), "Net Profit Margin"),
    (_safe(de_val,   ".2f", "x"), "Debt / Equity"),
    (_safe(cagr_val, ".1f", "%"), "Revenue CAGR 5yr"),
    (_safe(fcf_val,  ",.0f", " Cr"), "Free Cash Flow"),
]
for col, (val, lbl) in zip(kpi_cols, kpi_items):
    with col:
        st.markdown(_kpi(val, lbl), unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

# ── Partial-data note ─────────────────────────────────────────────────────────
pl_num = pl_df[pl_df["year"] != "TTM"].copy()
pl_years_count = len(pl_num)
rat_num_check  = ratios_df[ratios_df["year"] != "TTM"]
rat_years_count = len(rat_num_check)

if pl_years_count < 10 or rat_years_count < 10:
    min_yrs = min(pl_years_count, rat_years_count)
    st.markdown(
        f"<div style='background:rgba(227,179,65,0.1);border:1px solid #3d2f00;"
        f"border-radius:6px;padding:0.5rem 0.75rem;font-size:0.82rem;color:#e3b341;"
        f"margin-bottom:0.75rem;'>"
        f"ℹ️ Data available for {min_yrs} year(s) — charts will display available years only."
        f"</div>",
        unsafe_allow_html=True,
    )

pl_num["year_int"] = pd.to_numeric(pl_num["year"], errors="coerce")
pl_num = pl_num.dropna(subset=["year_int"]).sort_values("year_int")

col_c1, col_c2 = st.columns(2, gap="large")

with col_c1:
    yr_label = f"({pl_years_count}-Year)" if pl_years_count >= 10 else f"({pl_years_count} Years Available)"
    st.markdown(f"<div class='section-header'>Revenue & Net Profit {yr_label}</div>", unsafe_allow_html=True)
    if pl_num.empty:
        st.warning("No P&L data available.")
    else:
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=pl_num["year"].astype(str), y=pl_num["sales"],
            name="Revenue (₹ Cr)", marker_color="#58a6ff",
            hovertemplate="FY%{x}<br>Revenue: ₹%{y:,.0f} Cr<extra></extra>",
        ))
        fig_bar.add_trace(go.Bar(
            x=pl_num["year"].astype(str), y=pl_num["net_profit"],
            name="Net Profit (₹ Cr)", marker_color="#3fb950",
            hovertemplate="FY%{x}<br>Net Profit: ₹%{y:,.0f} Cr<extra></extra>",
        ))
        fig_bar.update_layout(
            barmode="group", height=320,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#8b949e"),
            legend=dict(orientation="h", y=-0.2),
            xaxis=dict(gridcolor="#21262d", tickfont_color="#8b949e"),
            yaxis=dict(gridcolor="#21262d", tickfont_color="#8b949e", tickprefix="₹", ticksuffix=" Cr"),
            margin=dict(l=0, r=0, t=20, b=0),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

with col_c2:
    st.markdown("<div class='section-header'>ROE & ROCE Trend (10-Year)</div>", unsafe_allow_html=True)
    rat_num = ratios_df[ratios_df["year"] != "TTM"].copy()
    rat_num["year_int"] = rat_num["year"].astype(int)
    rat_num = rat_num.sort_values("year_int")

    if rat_num.empty:
        st.warning("No ratio data available.")
    else:
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=rat_num["year"].astype(str),
            y=rat_num["return_on_equity_pct"],
            mode="lines+markers",
            name="ROE %",
            line=dict(color="#58a6ff", width=2),
            marker=dict(size=6),
            hovertemplate="FY%{x}<br>ROE: %{y:.1f}%<extra></extra>",
        ))
        fig_line.add_trace(go.Scatter(
            x=rat_num["year"].astype(str),
            y=rat_num["return_on_capital_employed_pct"],
            mode="lines+markers",
            name="ROCE %",
            line=dict(color="#3fb950", width=2, dash="dot"),
            marker=dict(size=6),
            yaxis="y2",
            hovertemplate="FY%{x}<br>ROCE: %{y:.1f}%<extra></extra>",
        ))
        fig_line.update_layout(
            height=320,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#8b949e"),
            legend=dict(orientation="h", y=-0.2),
            yaxis=dict(title="ROE %", gridcolor="#21262d", tickfont_color="#8b949e"),
            yaxis2=dict(title="ROCE %", overlaying="y", side="right", tickfont_color="#3fb950"),
            xaxis=dict(gridcolor="#21262d", tickfont_color="#8b949e"),
            margin=dict(l=0, r=0, t=20, b=0),
        )
        st.plotly_chart(fig_line, use_container_width=True)

# ── Pros & Cons ───────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>Pros & Cons</div>", unsafe_allow_html=True)

if pc_df.empty:
    st.info("No pros & cons data available for this company.")
else:
    pros_col, cons_col = st.columns(2, gap="large")
    pros_list = pc_df["pros"].dropna().tolist()
    cons_list = pc_df["cons"].dropna().tolist()

    with pros_col:
        st.markdown("**✅ Strengths**")
        if pros_list:
            for p in pros_list:
                st.markdown(f"<span class='badge-green'>✓ {p}</span>", unsafe_allow_html=True)
        else:
            st.caption("No pros available.")

    with cons_col:
        st.markdown("**⚠️ Concerns**")
        if cons_list:
            for c in cons_list:
                st.markdown(f"<span class='badge-red'>✗ {c}</span>", unsafe_allow_html=True)
        else:
            st.caption("No concerns listed.")
