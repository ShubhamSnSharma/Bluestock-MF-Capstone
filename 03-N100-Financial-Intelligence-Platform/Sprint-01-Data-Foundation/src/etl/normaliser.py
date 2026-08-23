"""
N100 Financial Intelligence Platform — ETL Normaliser Module
Provides robust, deterministic normalization routines for tickers, dates/years,
company names, URLs, and financial numbers across all 12 datasets.
"""

import re
from datetime import datetime, date
from typing import Any, Optional, Tuple, List, Dict
import pandas as pd
import numpy as np


# Explicit mapping for deterministic typo corrections in source data
TICKER_CORRECTIONS = {
    "AGTL": "ATGL",  # Adani Total Gas Ltd typo in Cashflow dataset
}


def normalize_ticker(ticker: Any) -> Optional[str]:
    """
    Normalizes stock tickers / company IDs:
    - Strips leading/trailing whitespace, newlines, and carriage returns.
    - Converts to standard uppercase ASCII.
    - Corrects deterministic source typos (e.g. AGTL -> ATGL).
    - Returns None if input is null, empty, or invalid.
    """
    if ticker is None or pd.isna(ticker):
        return None

    t_str = str(ticker).strip().upper()
    # Remove any embedded newlines or extra tabs
    t_str = re.sub(r"\s+", "", t_str)

    if not t_str or t_str == "NAN" or t_str == "NONE":
        return None

    # Apply deterministic correction if present
    return TICKER_CORRECTIONS.get(t_str, t_str)


def normalize_year(year_val: Any) -> Optional[str]:
    """
    Normalizes varied financial reporting year representations to standard 4-digit fiscal years:
    - Standard years: '2023', 2023, 2023.0 -> '2023'
    - Month-Year strings: 'Dec 2012' -> '2012', 'Mar 2024' -> '2024'
    - Hyphenated strings: 'Mar-13' -> '2013', 'Mar-2013' -> '2013'
    - FY prefixes: 'FY23' -> '2023', 'FY 2023' -> '2023', 'FY-24' -> '2024'
    - Trailing Twelve Months: 'TTM', 'ttm', 'Ttm' -> 'TTM'
    - Datetime / Timestamp / Date objects: datetime(2023, 3, 31) -> '2023'
    - Returns None if unparseable or null.
    """
    if year_val is None or pd.isna(year_val):
        return None

    if isinstance(year_val, (datetime, date, pd.Timestamp)):
        return str(year_val.year)

    # If float, check if it is a whole number year
    if isinstance(year_val, float):
        if np.isnan(year_val):
            return None
        if year_val.is_integer() and 1900 <= int(year_val) <= 2100:
            return str(int(year_val))
        year_str = str(int(year_val))
    elif isinstance(year_val, int):
        if 1900 <= year_val <= 2100:
            return str(year_val)
        year_str = str(year_val)
    else:
        year_str = str(year_val).strip()

    if not year_str or year_str.upper() in ("NAN", "NONE", "NULL", ""):
        return None

    # Check for TTM
    if year_str.upper() == "TTM":
        return "TTM"

    # 4-digit year directly: '2023'
    m_4digit = re.match(r"^(\d{4})$", year_str)
    if m_4digit:
        yr = int(m_4digit.group(1))
        if 1900 <= yr <= 2100:
            return str(yr)

    # Month + 4-digit year: 'Dec 2012', 'March 2024', 'Mar. 2020'
    m_mon_yr4 = re.search(r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\.-]+(\d{4})", year_str, re.IGNORECASE)
    if m_mon_yr4:
        return m_mon_yr4.group(1)

    # 4-digit year + Month: '2012 Dec', '2024-Mar'
    m_yr4_mon = re.search(r"^(\d{4})[\s\.-]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)", year_str, re.IGNORECASE)
    if m_yr4_mon:
        return m_yr4_mon.group(1)

    # Month + 2-digit year: 'Mar-13', 'Dec 12', 'Mar. 23'
    m_mon_yr2 = re.search(r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\.-]+(\d{2})$", year_str, re.IGNORECASE)
    if m_mon_yr2:
        yr2 = int(m_mon_yr2.group(1))
        # 2000-2099 assumption for contemporary Nifty100 data
        yr4 = 2000 + yr2 if yr2 < 70 else 1900 + yr2
        return str(yr4)

    # FY formats: 'FY23', 'FY 2023', 'FY-24', 'FY2024'
    m_fy = re.search(r"FY[\s\.-]*(\d{2,4})", year_str, re.IGNORECASE)
    if m_fy:
        raw_yr = m_fy.group(1)
        if len(raw_yr) == 4:
            return raw_yr
        elif len(raw_yr) == 2:
            yr2 = int(raw_yr)
            yr4 = 2000 + yr2 if yr2 < 70 else 1900 + yr2
            return str(yr4)

    # Date string format: '2023-03-31' or '31/03/2023'
    m_iso_date = re.match(r"^(\d{4})-\d{1,2}-\d{1,2}", year_str)
    if m_iso_date:
        return m_iso_date.group(1)

    m_dmy_date = re.match(r"^\d{1,2}[\/\.-]\d{1,2}[\/\.-](\d{4})", year_str)
    if m_dmy_date:
        return m_dmy_date.group(1)

    # Fallback: extract any 4-digit number between 1900 and 2100
    m_any_yr = re.search(r"\b(19\d{2}|20\d{2})\b", year_str)
    if m_any_yr:
        return m_any_yr.group(1)

    return None


def clean_company_name(name: Any) -> str:
    """
    Cleans company names by removing trailing/leading whitespace, linebreaks,
    and collapsing multiple spaces into a single space.
    """
    if name is None or pd.isna(name):
        return ""

    name_str = str(name).strip()
    # Replace newlines and multi-spaces with single space
    name_str = re.sub(r"[\r\n]+", " - ", name_str)
    name_str = re.sub(r"\s+", " ", name_str)
    return name_str.strip()


def clean_url(url: Any) -> Optional[str]:
    """
    Cleans URL strings:
    - Trims whitespace.
    - Resolves double slash typos in URL paths (e.g. AttachHis//uuid.pdf -> AttachHis/uuid.pdf).
    - Preserves valid http:// or https:// protocol.
    """
    if url is None or pd.isna(url):
        return None

    u_str = str(url).strip()
    if not u_str or u_str.upper() in ("NAN", "NONE", "NULL", "-"):
        return None

    # Fix double slashes in path after protocol
    if "://" in u_str:
        proto, path = u_str.split("://", 1)
        path = re.sub(r"/+", "/", path)
        return f"{proto}://{path}"

    return u_str


def clean_numeric(val: Any) -> Optional[float]:
    """
    Cleans numeric financial line items:
    - Strips commas, currency symbols, and percentage signs.
    - Returns standard float or None if missing/unparseable.
    """
    if val is None or pd.isna(val):
        return None

    if isinstance(val, (int, float)):
        return float(val) if not np.isnan(val) else None

    v_str = str(val).strip().replace(",", "").replace("%", "").replace("₹", "").replace("Rs.", "")
    if not v_str or v_str.upper() in ("NAN", "NONE", "NULL", "-", "NA", "N/A"):
        return None

    try:
        return float(v_str)
    except ValueError:
        return None


def deduplicate_dataframe(
    df: pd.DataFrame,
    subset_cols: List[str],
    table_name: str
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Deduplicates a DataFrame based on natural composite key subset columns.
    Returns:
    - Deduplicated DataFrame (retaining first occurrence).
    - List of rejection audit dictionaries detailing dropped rows.
    """
    duplicates_mask = df.duplicated(subset=subset_cols, keep="first")
    rejected_rows = df[duplicates_mask]

    audit_records = []
    for idx, row in rejected_rows.iterrows():
        key_vals = {col: row.get(col) for col in subset_cols}
        audit_records.append({
            "table_name": table_name,
            "row_identifier": str(key_vals),
            "rejection_reason": f"Duplicate natural key on {subset_cols}",
            "severity": "CRITICAL",
            "action": "Deduplicated / Rejected Duplicate Row"
        })

    deduped_df = df[~duplicates_mask].copy()
    return deduped_df, audit_records
