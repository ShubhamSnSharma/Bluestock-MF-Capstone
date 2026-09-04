"""
04_peers.py — Peer Comparison Screen
• Peer group dropdown (all 11 groups)
• Radar chart: selected company vs peer group average (8 metrics)
• Side-by-side KPI table with benchmark row highlighted
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

_SPRINT4 = Path(__file__).resolve().parents[1]
if str(_SPRINT4 / "src") not in sys.path:
    sys.path.insert(0, str(_SPRINT4 / "src"))

from dashboard.utils.db import get_all_peer_groups, get_peers

# ── Title ─────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='font-size:1.8rem;font-weight:700;color:#e6edf3;margin-bottom:0.5rem;'>"
    "👥 Peer Comparison"
    "</h1>",
    unsafe_allow_html=True,
)

# ── Sidebar controls ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 👥 Peer Settings")
    peer_groups  = get_all_peer_groups()
    selected_grp = st.selectbox("Select Peer Group", peer_groups, key="peer_group_sel")

    peers_df = get_peers(selected_grp)

    if peers_df.empty:
        st.warning("No peers found for this group.")
        st.stop()

    # Company selector within the group
    ticker_options = peers_df["company_id"].tolist()
    default_idx    = 0
    bench_rows     = peers_df[peers_df["is_benchmark"] == 1]
    if not bench_rows.empty:
        bench_ticker = bench_rows.iloc[0]["company_id"]
        if bench_ticker in ticker_options:
            default_idx = ticker_options.index(bench_ticker)

    selected_ticker = st.selectbox(
        "Highlight Company",
        ticker_options,
        index=default_idx,
        format_func=lambda t: f"{t} — {peers_df[peers_df['company_id']==t]['company_name'].values[0]}",
        key="peer_ticker_sel",
    )

# ── Radar chart ────────────────────────────────────────────────────────────────
RADAR_METRICS = {
    "roe"          : "ROE %",
    "roce"         : "ROCE %",
    "npm"          : "NPM %",
    "revenue_cagr_5yr": "Rev CAGR 5yr %",
    "pat_cagr_5yr" : "PAT CAGR 5yr %",
    "composite_quality_score": "Quality Score",
    "pe_ratio"     : "P/E",
    "de"           : "D/E",
}
radar_keys   = list(RADAR_METRICS.keys())
radar_labels = list(RADAR_METRICS.values())

# Compute peer group average (exclude NaN)
group_avg = {k: peers_df[k].mean(skipna=True) for k in radar_keys}

# Selected company row
sel_row = peers_df[peers_df["company_id"] == selected_ticker]
if sel_row.empty:
    st.error("Selected company not found in peer group data.")
    st.stop()
sel_row = sel_row.iloc[0]

# Normalise for radar (0–1 scale, higher is always better)
# For D/E and P/E lower is better — invert
def _norm_series(values: list[float]) -> list[float]:
    arr = np.array(values, dtype=float)
    mn, mx = np.nanmin(arr), np.nanmax(arr)
    if mx == mn:
        return [0.5] * len(values)
    return ((arr - mn) / (mx - mn)).tolist()


raw_sel  = [float(sel_row[k]) if pd.notna(sel_row[k]) else 0.0 for k in radar_keys]
raw_avg  = [float(group_avg[k]) if pd.notna(group_avg[k]) else 0.0 for k in radar_keys]

combined     = [raw_sel, raw_avg]
# Normalise each metric across [sel, avg]
norm_sel, norm_avg = [], []
for i, k in enumerate(radar_keys):
    vals = [raw_sel[i], raw_avg[i]]
    inv  = k in ("de", "pe_ratio")
    mn, mx = min(vals), max(vals)
    if mx == mn:
        norm_sel.append(0.5); norm_avg.append(0.5)
    else:
        s = (raw_sel[i] - mn) / (mx - mn)
        a = (raw_avg[i] - mn) / (mx - mn)
        if inv:
            s, a = 1 - s, 1 - a
        norm_sel.append(s); norm_avg.append(a)

# Close the polygon
theta       = radar_labels + [radar_labels[0]]
norm_sel_c  = norm_sel + [norm_sel[0]]
norm_avg_c  = norm_avg + [norm_avg[0]]

sel_name = f"{selected_ticker} — {sel_row['company_name']}"

fig_radar = go.Figure()
fig_radar.add_trace(go.Scatterpolar(
    r=norm_sel_c, theta=theta,
    fill="toself", name=sel_name,
    line=dict(color="#58a6ff", width=2),
    fillcolor="rgba(88,166,255,0.15)",
    hovertemplate="%{theta}: %{r:.2f}<extra>" + sel_name + "</extra>",
))
fig_radar.add_trace(go.Scatterpolar(
    r=norm_avg_c, theta=theta,
    fill="toself", name="Peer Group Avg",
    line=dict(color="#3fb950", width=2, dash="dot"),
    fillcolor="rgba(63,185,80,0.10)",
    hovertemplate="%{theta}: %{r:.2f}<extra>Peer Avg</extra>",
))
fig_radar.update_layout(
    polar=dict(
        bgcolor="rgba(0,0,0,0)",
        radialaxis=dict(visible=True, range=[0, 1], tickfont_color="#8b949e",
                        gridcolor="#30363d", linecolor="#30363d"),
        angularaxis=dict(tickfont_color="#e6edf3", gridcolor="#21262d", linecolor="#21262d"),
    ),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    legend=dict(font_color="#e6edf3", bgcolor="rgba(0,0,0,0)"),
    height=420,
    margin=dict(l=40, r=40, t=40, b=40),
)

st.markdown(
    f"<div class='section-header'>Radar: {sel_name} vs {selected_grp} Peer Average</div>",
    unsafe_allow_html=True,
)
st.plotly_chart(fig_radar, use_container_width=True)

# ── Side-by-side KPI table ────────────────────────────────────────────────────
st.markdown("<div class='section-header'>Peer Group KPI Table</div>", unsafe_allow_html=True)

display_map = {
    "company_id"              : "Ticker",
    "company_name"            : "Company",
    "broad_sector"            : "Sector",
    "composite_quality_score" : "Quality Score",
    "roe"                     : "ROE %",
    "roce"                    : "ROCE %",
    "npm"                     : "NPM %",
    "de"                      : "D/E",
    "icr"                     : "ICR",
    "revenue_cagr_5yr"        : "Rev CAGR 5yr %",
    "pat_cagr_5yr"            : "PAT CAGR 5yr %",
    "pe_ratio"                : "P/E",
    "pb_ratio"                : "P/B",
    "market_cap_crore"        : "Mkt Cap (₹ Cr)",
    "is_benchmark"            : "Benchmark",
}

table = peers_df[[c for c in display_map if c in peers_df.columns]].copy()
table = table.rename(columns=display_map)

num_cols = ["Quality Score", "ROE %", "ROCE %", "NPM %", "D/E", "ICR",
            "Rev CAGR 5yr %", "PAT CAGR 5yr %", "P/E", "P/B", "Mkt Cap (₹ Cr)"]
for col in num_cols:
    if col in table.columns:
        table[col] = table[col].apply(lambda x: f"{x:,.1f}" if pd.notna(x) else "N/A")

if "Benchmark" in table.columns:
    table["Benchmark"] = table["Benchmark"].apply(lambda x: "⭐ Yes" if x == 1 else "")

# Highlight selected ticker row
def _highlight(row: pd.Series) -> list[str]:
    if row["Ticker"] == selected_ticker:
        return ["background-color: rgba(88,166,255,0.15);"] * len(row)
    if row.get("Benchmark") == "⭐ Yes":
        return ["background-color: rgba(63,185,80,0.08);"] * len(row)
    return [""] * len(row)

styled = table.style.apply(_highlight, axis=1)
st.dataframe(styled, use_container_width=True, hide_index=True, height=380)
