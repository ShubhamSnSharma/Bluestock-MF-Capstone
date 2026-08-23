"""
Unit test suite for ETL normaliser module (35+ test cases).
Verifies normalize_year, normalize_ticker, clean_company_name, clean_url,
clean_numeric, and deduplication logic.
"""

from datetime import datetime, date
import pytest
import pandas as pd
import numpy as np

from src.etl.normaliser import (
    normalize_ticker,
    normalize_year,
    clean_company_name,
    clean_url,
    clean_numeric,
    deduplicate_dataframe
)


# ==============================================================================
# 1. normalize_year Test Suite (22 test cases)
# ==============================================================================

@pytest.mark.parametrize("input_val, expected", [
    ("2023", "2023"),                           # Standard 4-digit string
    (2024, "2024"),                             # Standard integer
    (2022.0, "2022"),                           # Float integer
    ("Dec 2012", "2012"),                       # Month 4-digit year (space)
    ("Mar 2014", "2014"),                       # March 4-digit year
    ("March 2020", "2020"),                     # Full month name
    ("Mar-13", "2013"),                         # Month hyphen 2-digit year
    ("Mar-2013", "2013"),                       # Month hyphen 4-digit year
    ("Dec-12", "2012"),                         # December 2-digit
    ("FY23", "2023"),                           # FY 2-digit
    ("FY 2024", "2024"),                        # FY space 4-digit
    ("FY-2021", "2021"),                        # FY hyphen 4-digit
    ("TTM", "TTM"),                             # Trailing twelve months uppercase
    ("ttm", "TTM"),                             # Trailing twelve months lowercase
    ("Ttm", "TTM"),                             # Trailing twelve months mixed case
    ("2023-03-31", "2023"),                     # ISO Date string
    ("31/03/2024", "2024"),                     # UK/IN Date string
    (datetime(2023, 3, 31), "2023"),            # Python datetime object
    (date(2022, 12, 31), "2022"),               # Python date object
    (pd.Timestamp("2024-06-30"), "2024"),       # Pandas Timestamp object
    ("Dec. 2019", "2019"),                      # Abbreviated period month
    ("2018 Mar", "2018"),                       # Year preceding month
])
def test_normalize_year_valid(input_val, expected):
    assert normalize_year(input_val) == expected


@pytest.mark.parametrize("invalid_val", [
    None,
    np.nan,
    "",
    "   ",
    "InvalidYear",
    "ABC 12",
    1850,
    2250,
])
def test_normalize_year_invalid(invalid_val):
    assert normalize_year(invalid_val) is None


# ==============================================================================
# 2. normalize_ticker Test Suite (18 test cases)
# ==============================================================================

@pytest.mark.parametrize("input_ticker, expected", [
    ("ABB", "ABB"),                             # Clean standard ticker
    ("tcs", "TCS"),                             # Lowercase conversion
    (" Infy ", "INFY"),                         # Leading/trailing whitespace
    ("HDFCBANK\n", "HDFCBANK"),                 # Trailing newline
    ("RELIANCE\r\n", "RELIANCE"),               # Windows newline
    ("BAJAJ-AUTO", "BAJAJ-AUTO"),               # Hyphenated ticker
    ("M&M", "M&M"),                             # Special character &
    ("L&T", "L&T"),                             # Ampersand symbol
    ("AGTL", "ATGL"),                           # Deterministic typo correction (AGTL -> ATGL)
    (" agtl ", "ATGL"),                         # Lowercase + whitespace + typo
    ("LICI", "LICI"),                           # Standard symbol
    ("DRREDDY", "DRREDDY"),                     # Standard symbol
    ("NESTLEIND", "NESTLEIND"),                 # Standard symbol
    ("ICICIBANK", "ICICIBANK"),                 # Standard symbol
    ("TATAMOTORS", "TATAMOTORS"),               # Standard symbol
])
def test_normalize_ticker_valid(input_ticker, expected):
    assert normalize_ticker(input_ticker) == expected


@pytest.mark.parametrize("invalid_ticker", [
    None,
    np.nan,
    "",
    "   ",
    "NAN",
    "NONE",
])
def test_normalize_ticker_invalid(invalid_ticker):
    assert normalize_ticker(invalid_ticker) is None


# ==============================================================================
# 3. clean_company_name Test Suite
# ==============================================================================

def test_clean_company_name_multiline():
    raw_name = "Asian Paints\nIndian Multi-National Paint and Coating Manufacturing Company"
    expected = "Asian Paints - Indian Multi-National Paint and Coating Manufacturing Company"
    assert clean_company_name(raw_name) == expected


def test_clean_company_name_trailing_newline():
    raw_name = "Reliance Industries Ltd\n"
    assert clean_company_name(raw_name) == "Reliance Industries Ltd"


def test_clean_company_name_null():
    assert clean_company_name(None) == ""
    assert clean_company_name(np.nan) == ""


# ==============================================================================
# 4. clean_url Test Suite
# ==============================================================================

def test_clean_url_double_slash_fix():
    bad_url = "https://www.bseindia.com/xml-data/corpfiling/AttachHis//68827cf7-67af-4209-91f5-3854d3e1e8a2.pdf"
    expected = "https://www.bseindia.com/xml-data/corpfiling/AttachHis/68827cf7-67af-4209-91f5-3854d3e1e8a2.pdf"
    assert clean_url(bad_url) == expected


def test_clean_url_valid():
    url = "https://www.abbott.co.in/"
    assert clean_url(url) == url


def test_clean_url_null():
    assert clean_url(None) is None
    assert clean_url("-") is None
    assert clean_url("NULL") is None


# ==============================================================================
# 5. clean_numeric Test Suite
# ==============================================================================

def test_clean_numeric_percentage_and_commas():
    assert clean_numeric("24.6%") == 24.6
    assert clean_numeric("240,893") == 240893.0
    assert clean_numeric("₹45,908.50") == 45908.50
    assert clean_numeric("-152.0") == -152.0
    assert clean_numeric(None) is None
    assert clean_numeric("N/A") is None


# ==============================================================================
# 6. deduplicate_dataframe Test Suite
# ==============================================================================

def test_deduplicate_dataframe():
    sample_df = pd.DataFrame([
        {"id": 1, "company_id": "ADANIPORTS", "year": "2013", "sales": 3577},
        {"id": 2, "company_id": "ADANIPORTS", "year": "2013", "sales": 3577},
        {"id": 3, "company_id": "ADANIPORTS", "year": "2014", "sales": 4830},
    ])
    deduped_df, audit = deduplicate_dataframe(sample_df, ["company_id", "year"], "profitandloss")
    assert len(deduped_df) == 2
    assert len(audit) == 1
    assert audit[0]["table_name"] == "profitandloss"
    assert audit[0]["severity"] == "CRITICAL"
