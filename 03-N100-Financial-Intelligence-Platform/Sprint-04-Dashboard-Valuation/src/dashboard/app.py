"""
app.py — Main Streamlit entry point for N100 Financial Intelligence Dashboard.
Sprint 4 — Dashboard & Valuation Module

Run: streamlit run src/dashboard/app.py
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Path setup — ensure src/ and pages/ are importable from any CWD
# ---------------------------------------------------------------------------
_SPRINT4_ROOT = Path(__file__).resolve().parents[2]
_PAGES_DIR    = _SPRINT4_ROOT / "pages"
_SRC_DIR      = _SPRINT4_ROOT / "src"

for _p in [str(_SPRINT4_ROOT), str(_SRC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ---------------------------------------------------------------------------
# Streamlit page config — must be the FIRST st call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — premium dark theme
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* ── Global base ─────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .stApp { background: #0d1117; color: #e6edf3; }

    /* ── Sidebar ─────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #161b22 0%, #0d1117 100%);
        border-right: 1px solid #21262d;
    }
    [data-testid="stSidebar"] .stRadio label {
        font-size: 0.9rem;
        padding: 0.35rem 0.5rem;
        border-radius: 6px;
        transition: background 0.15s;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(88,166,255,0.08);
        color: #58a6ff;
    }

    /* ── KPI tiles ───────────────────────────────────── */
    .kpi-card {
        background: linear-gradient(135deg, #161b22 0%, #1c2128 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        text-align: center;
        transition: box-shadow 0.2s, transform 0.2s;
    }
    .kpi-card:hover {
        box-shadow: 0 0 0 1px #58a6ff55, 0 8px 24px rgba(0,0,0,0.4);
        transform: translateY(-2px);
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #58a6ff;
        line-height: 1.1;
    }
    .kpi-label {
        font-size: 0.75rem;
        color: #8b949e;
        margin-top: 0.3rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .kpi-delta {
        font-size: 0.8rem;
        margin-top: 0.25rem;
    }

    /* ── Section headers ─────────────────────────────── */
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #e6edf3;
        border-left: 3px solid #58a6ff;
        padding-left: 0.75rem;
        margin: 1.5rem 0 1rem 0;
    }

    /* ── Badge pills ─────────────────────────────────── */
    .badge-green { background:#1a4731; color:#3fb950; padding:3px 10px; border-radius:20px; font-size:0.78rem; margin:2px; display:inline-block; }
    .badge-red   { background:#4b1113; color:#f85149; padding:3px 10px; border-radius:20px; font-size:0.78rem; margin:2px; display:inline-block; }
    .badge-yellow{ background:#3d2f00; color:#e3b341; padding:3px 10px; border-radius:20px; font-size:0.78rem; margin:2px; display:inline-block; }
    .badge-blue  { background:#0d2c4b; color:#58a6ff; padding:3px 10px; border-radius:20px; font-size:0.78rem; margin:2px; display:inline-block; }

    /* ── Tables ──────────────────────────────────────── */
    [data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }

    /* ── Buttons ─────────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, #1f6feb, #388bfd);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 500;
        transition: opacity 0.2s, transform 0.1s;
    }
    .stButton > button:hover {
        opacity: 0.88;
        transform: translateY(-1px);
    }

    /* ── Divider ─────────────────────────────────────── */
    hr { border-color: #21262d; }

    /* ── Scrollbar ───────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #0d1117; }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
PAGES = {
    "🏠  Home"               : "01_home",
    "🏢  Company Profile"    : "02_profile",
    "🔍  Screener"           : "03_screener",
    "👥  Peer Comparison"    : "04_peers",
    "📈  Trend Analysis"     : "05_trends",
    "🏭  Sector Analysis"    : "06_sectors",
    "💰  Capital Allocation" : "07_capital",
    "📄  Annual Reports"     : "08_reports",
}

with st.sidebar:
    st.markdown(
        """
        <div style='text-align:center; padding: 1rem 0 0.5rem 0;'>
          <span style='font-size:2rem;'>📈</span><br/>
          <span style='font-weight:700; font-size:1.05rem; color:#e6edf3;'>Nifty 100 Analytics</span><br/>
          <span style='font-size:0.72rem; color:#8b949e;'>N100 Financial Intelligence Platform</span>
        </div>
        <hr style='margin:0.75rem 0;'/>
        """,
        unsafe_allow_html=True,
    )

    selected_page = st.radio(
        "Navigate",
        list(PAGES.keys()),
        label_visibility="collapsed",
    )

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:0.68rem; color:#484f58; text-align:center;'>"
        "Sprint 4 · FY2024 Data · 92 Companies"
        "</div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Dynamic page loader
# ---------------------------------------------------------------------------
module_name = PAGES[selected_page]
module_path = _PAGES_DIR / f"{module_name}.py"

if not module_path.exists():
    st.error(f"Page file not found: {module_path}")
    st.stop()

spec   = importlib.util.spec_from_file_location(module_name, module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
