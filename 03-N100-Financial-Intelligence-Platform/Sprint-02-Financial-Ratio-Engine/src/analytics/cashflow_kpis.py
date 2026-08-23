"""
Cash Flow KPIs, Quality Scores, and Capital Allocation Pattern Classifier.
Sprint 2 — Financial Ratio Engine
"""

from typing import Optional, Tuple, List, Dict, Any


def compute_free_cash_flow(cfo: Optional[float], cfi: Optional[float]) -> Optional[float]:
    """
    Computes Free Cash Flow (FCF) in ₹ Cr: operating_activity + investing_activity.
    Negative values are valid.
    """
    if cfo is None or cfi is None:
        return None
    return cfo + cfi


def compute_cfo_quality_score(
    cfo_pat_pairs_5yr: List[Tuple[Optional[float], Optional[float]]]
) -> Tuple[Optional[float], Optional[str]]:
    """
    Computes CFO Quality Score as 5-year average of (CFO / PAT).
    - If PAT == 0 for a period, excludes that period from average.
    - If no valid periods exist, returns (None, None).
    Classification:
    - > 1.0: "High Quality"
    - 0.5 - 1.0: "Moderate"
    - < 0.5: "Accrual Risk"
    """
    valid_ratios = []
    for cfo, pat in cfo_pat_pairs_5yr:
        if cfo is not None and pat is not None and pat != 0:
            valid_ratios.append(cfo / pat)

    if not valid_ratios:
        return None, None

    avg_score = sum(valid_ratios) / float(len(valid_ratios))

    if avg_score > 1.0:
        label = "High Quality"
    elif avg_score >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"

    return avg_score, label


def compute_capex_intensity(
    investing_activity: Optional[float],
    sales: Optional[float]
) -> Tuple[Optional[float], Optional[str]]:
    """
    Computes CapEx Intensity percentage: (abs(investing_activity) / sales) * 100.
    Classification:
    - < 3%: "Asset Light"
    - 3 - 8%: "Moderate"
    - > 8%: "Capital Intensive"
    Returns None if sales is None or sales <= 0.
    """
    if investing_activity is None or sales is None or sales <= 0:
        return None, None

    intensity = (abs(investing_activity) / sales) * 100.0

    if intensity < 3.0:
        label = "Asset Light"
    elif intensity <= 8.0:
        label = "Moderate"
    else:
        label = "Capital Intensive"

    return intensity, label


def compute_fcf_conversion_rate(
    fcf: Optional[float],
    operating_profit: Optional[float]
) -> Optional[float]:
    """
    Computes FCF Conversion Rate percentage: (FCF / operating_profit) * 100.
    Returns None if operating_profit is None or operating_profit == 0.
    """
    if fcf is None or operating_profit is None or operating_profit == 0:
        return None
    return (fcf / operating_profit) * 100.0


def classify_capital_allocation(
    cfo: Optional[float],
    cfi: Optional[float],
    cff: Optional[float],
    cfo_quality_score: Optional[float] = None
) -> Tuple[str, str, str, str]:
    """
    Classifies 8-pattern Capital Allocation based on signs of (CFO, CFI, CFF).
    Signs: '+' if val > 0, '-' if val < 0, '0' if val == 0 or None.
    Pattern Precedence:
    - (+,-,-) AND cfo_quality_score > 1.0: "Shareholder Returns"
    - (+,-,-) otherwise: "Reinvestor"
    - (+,+,-): "Liquidating Assets"
    - (-,+,+): "Distress Signal"
    - (-,-,+): "Growth Funded by Debt"
    - (+,+,+): "Cash Accumulator"
    - (-,-,-): "Pre-Revenue"
    - (+,-,+): "Mixed"
    - Unlisted combinations: "Other"
    Returns (cfo_sign, cfi_sign, cff_sign, pattern_label).
    """
    def get_sign(val: Optional[float]) -> str:
        if val is None:
            return "0"
        if val > 0:
            return "+"
        elif val < 0:
            return "-"
        return "0"

    s_cfo = get_sign(cfo)
    s_cfi = get_sign(cfi)
    s_cff = get_sign(cff)
    pattern = (s_cfo, s_cfi, s_cff)

    if pattern == ("+", "-", "-"):
        if cfo_quality_score is not None and cfo_quality_score > 1.0:
            label = "Shareholder Returns"
        else:
            label = "Reinvestor"
    elif pattern == ("+", "+", "-"):
        label = "Liquidating Assets"
    elif pattern == ("-", "+", "+"):
        label = "Distress Signal"
    elif pattern == ("-", "-", "+"):
        label = "Growth Funded by Debt"
    elif pattern == ("+", "+", "+"):
        label = "Cash Accumulator"
    elif pattern == ("-", "-", "-"):
        label = "Pre-Revenue"
    elif pattern == ("+", "-", "+"):
        label = "Mixed"
    else:
        label = "Other"

    return s_cfo, s_cfi, s_cff, label
