"""
08_reports.py — Annual Reports Screen
• Company search box
• List of available annual report years with clickable BSE PDF links
• Actual HTTP status check (200=available, 404=unavailable, other=unable to verify)
• Results cached per session to avoid repeated network calls
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

_SPRINT4 = Path(__file__).resolve().parents[1]
if str(_SPRINT4 / "src") not in sys.path:
    sys.path.insert(0, str(_SPRINT4 / "src"))

from dashboard.utils.db import get_companies, get_documents

# ── HTTP check (cached in session state to avoid re-checking on slider moves) ─
def _check_url(url: str) -> str:
    """
    Check HTTP status of a URL.
    Returns:
      'available'  — HTTP 200
      'unavailable' — HTTP 404
      'unverified'  — timeout, network error, or other HTTP status
    """
    if not url or not isinstance(url, str) or not url.startswith("http"):
        return "unavailable"

    # Cache in session_state to avoid repeated network calls within a session
    cache_key = f"url_status_{url}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]

    try:
        import urllib.request
        import urllib.error
        req = urllib.request.Request(url, method="HEAD")
        req.add_header(
            "User-Agent",
            "Mozilla/5.0 (compatible; N100-Dashboard/4.0)",
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            status = resp.status
    except urllib.error.HTTPError as e:
        status = e.code
    except Exception:
        # Network unreachable, timeout, SSL error, etc.
        st.session_state[cache_key] = "unverified"
        return "unverified"

    if status == 200:
        result = "available"
    elif status == 404:
        result = "unavailable"
    else:
        result = "unverified"   # 301/302/403/500 etc. — can't confirm

    st.session_state[cache_key] = result
    return result


# ── Title ─────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='font-size:1.8rem;font-weight:700;color:#e6edf3;margin-bottom:0.5rem;'>"
    "📄 Annual Reports"
    "</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#8b949e;font-size:0.88rem;margin-bottom:1.2rem;'>"
    "Browse and download annual reports for any Nifty 100 company. "
    "PDF links are verified via HTTP check — 200 OK shows as available, "
    "404 shows as unavailable, network errors show as unable to verify."
    "</p>",
    unsafe_allow_html=True,
)

# ── Company search ─────────────────────────────────────────────────────────────
companies_df = get_companies()
ticker_list  = sorted(companies_df["company_id"].tolist())
name_map     = dict(zip(companies_df["company_id"], companies_df["company_name"]))

ticker = st.selectbox(
    "Search company name or ticker",
    [""] + ticker_list,
    format_func=lambda t: "Select a company…" if not t else f"{t} — {name_map.get(t, t)}",
    key="reports_ticker",
)

if not ticker:
    st.info("👆 Select a company to view its available annual reports.")
    st.stop()

# ── Load docs ──────────────────────────────────────────────────────────────────
docs_df      = get_documents(ticker)
company_name = name_map.get(ticker, ticker)

st.markdown(
    f"<div style='font-size:1.1rem;font-weight:600;color:#e6edf3;margin:1rem 0 0.5rem 0;'>"
    f"📂 {company_name} ({ticker}) — Annual Reports"
    f"</div>",
    unsafe_allow_html=True,
)

if docs_df.empty:
    st.warning(f"No annual reports found in the database for **{ticker}**.")
    st.stop()

# ── Verification progress note ────────────────────────────────────────────────
total_docs = len(docs_df)
st.markdown(
    f"<div style='font-size:0.8rem;color:#8b949e;margin-bottom:0.75rem;'>"
    f"Verifying {total_docs} report URLs via HTTP … "
    f"(results cached for this session)"
    f"</div>",
    unsafe_allow_html=True,
)

# ── Report cards ───────────────────────────────────────────────────────────────
status_counts = {"available": 0, "unavailable": 0, "unverified": 0}

for _, doc_row in docs_df.iterrows():
    year = doc_row["year"]
    url  = doc_row["annual_report"]
    status = _check_url(url)
    status_counts[status] = status_counts.get(status, 0) + 1

    if status == "available":
        st.markdown(
            f"""
            <div style='background:linear-gradient(135deg,#161b22,#1c2128);
                        border:1px solid #30363d;border-radius:10px;
                        padding:0.9rem 1.2rem;margin-bottom:0.6rem;
                        display:flex;align-items:center;gap:1rem;'>
              <span style='font-size:1.4rem;'>📥</span>
              <div>
                <div style='font-weight:600;color:#e6edf3;'>FY{year} Annual Report</div>
                <div style='font-size:0.8rem;margin-top:0.2rem;'>
                  <a href='{url}' target='_blank'
                     style='color:#58a6ff;text-decoration:none;'>
                    📋 Open PDF from BSE India ↗
                  </a>
                  <span class='badge-green' style='margin-left:0.5rem;'>✓ Available</span>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif status == "unavailable":
        st.markdown(
            f"""
            <div style='background:rgba(75,17,19,0.3);
                        border:1px solid #4b1113;border-radius:10px;
                        padding:0.9rem 1.2rem;margin-bottom:0.6rem;
                        display:flex;align-items:center;gap:1rem;'>
              <span style='font-size:1.4rem;'>🚫</span>
              <div>
                <div style='font-weight:600;color:#e6edf3;'>FY{year} Annual Report</div>
                <div style='margin-top:0.2rem;'>
                  <span class='badge-red'>Report unavailable (HTTP 404)</span>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:  # unverified
        st.markdown(
            f"""
            <div style='background:rgba(61,47,0,0.3);
                        border:1px solid #3d2f00;border-radius:10px;
                        padding:0.9rem 1.2rem;margin-bottom:0.6rem;
                        display:flex;align-items:center;gap:1rem;'>
              <span style='font-size:1.4rem;'>⚠️</span>
              <div>
                <div style='font-weight:600;color:#e6edf3;'>FY{year} Annual Report</div>
                <div style='margin-top:0.2rem;'>
                  <span class='badge-yellow'>Unable to verify — try opening directly</span>
                  <a href='{url}' target='_blank'
                     style='color:#8b949e;font-size:0.78rem;margin-left:0.5rem;'>
                    ↗ Try link
                  </a>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Summary footer ─────────────────────────────────────────────────────────────
available   = status_counts.get("available", 0)
unavailable = status_counts.get("unavailable", 0)
unverified  = status_counts.get("unverified", 0)

st.markdown(
    f"""
    <div style='margin-top:1.5rem;padding:0.75rem 1rem;
                background:#161b22;border-radius:8px;border:1px solid #21262d;
                font-size:0.82rem;color:#8b949e;'>
      📊 <b style='color:#e6edf3;'>{total_docs}</b> total years ·
      <b style='color:#3fb950;'>{available}</b> available ·
      <b style='color:#f85149;'>{unavailable}</b> unavailable ·
      <b style='color:#e3b341;'>{unverified}</b> unable to verify
    </div>
    """,
    unsafe_allow_html=True,
)
