"""
CAGR Engine — Growth Metrics & Edge Case Handling.
Sprint 2 — Financial Ratio Engine
"""

from typing import Optional, Tuple, Dict, Any


def calculate_cagr(start_val: Optional[float], end_val: Optional[float], n: int) -> Tuple[Optional[float], Optional[str]]:
    """
    Computes Compound Annual Growth Rate (CAGR) percentage: ((end / start) ** (1 / n) - 1) * 100
    Handles all 6 edge cases:
    1. Positive -> Positive: Computes normally, flag = None
    2. Positive -> Negative: value = None, flag = "DECLINE_TO_LOSS"
    3. Negative -> Positive: value = None, flag = "TURNAROUND"
    4. Negative -> Negative: value = None, flag = "BOTH_NEGATIVE"
    5. Zero base: value = None, flag = "ZERO_BASE"
    6. Insufficient history: value = None, flag = "INSUFFICIENT"
    """
    if start_val is None or end_val is None or n <= 0:
        return None, "INSUFFICIENT"

    if start_val == 0:
        return None, "ZERO_BASE"

    if start_val > 0 and end_val > 0:
        cagr_val = (((end_val / start_val) ** (1.0 / float(n))) - 1.0) * 100.0
        return cagr_val, None

    if start_val > 0 and end_val < 0:
        return None, "DECLINE_TO_LOSS"

    if start_val < 0 and end_val > 0:
        return None, "TURNAROUND"

    if start_val < 0 and end_val < 0:
        return None, "BOTH_NEGATIVE"

    if end_val == 0:
        return -100.0, None

    return None, "INSUFFICIENT"


def compute_series_cagr(
    year_val_map: Dict[str, float],
    target_year: str,
    n: int
) -> Tuple[Optional[float], Optional[str]]:
    """
    Computes n-year CAGR for a time series dictionary {year_str: value}.
    Verifies that the target year t and base year t-n exist as valid numeric fiscal years.
    Returns (cagr_value, cagr_flag).
    """
    if target_year == "TTM" or not target_year.isdigit():
        return None, "INSUFFICIENT"

    end_year_int = int(target_year)
    start_year_int = end_year_int - n
    start_year_str = str(start_year_int)

    if start_year_str not in year_val_map or target_year not in year_val_map:
        return None, "INSUFFICIENT"

    start_val = year_val_map[start_year_str]
    end_val = year_val_map[target_year]

    return calculate_cagr(start_val, end_val, n)
