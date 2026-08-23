"""
Profitability, Leverage, and Efficiency Ratios Calculation Engine.
Sprint 2 — Financial Ratio Engine
"""

from typing import Optional, Tuple, Dict, Any


def compute_net_profit_margin(net_profit: Optional[float], sales: Optional[float]) -> Optional[float]:
    """
    Computes Net Profit Margin percentage: (net_profit / sales) * 100.
    Returns None if sales is None or sales == 0.
    """
    if net_profit is None or sales is None or sales == 0:
        return None
    return (net_profit / sales) * 100.0


def compute_operating_profit_margin(
    operating_profit: Optional[float],
    sales: Optional[float],
    reported_opm: Optional[float] = None,
    tolerance: float = 1.0
) -> Tuple[Optional[float], Optional[Dict[str, Any]]]:
    """
    Computes Operating Profit Margin percentage: (operating_profit / sales) * 100.
    Returns (calculated_opm, anomaly_info).
    If reported_opm is provided and difference > tolerance, returns anomaly dictionary.
    """
    if operating_profit is None or sales is None or sales == 0:
        return None, None

    calc_opm = (operating_profit / sales) * 100.0
    anomaly = None

    if reported_opm is not None:
        diff = abs(calc_opm - reported_opm)
        if diff > tolerance:
            anomaly = {
                "metric": "OPM",
                "calculated_value": calc_opm,
                "source_value": reported_opm,
                "difference": diff,
                "category": "FORMULA_DISCREPANCY",
                "explanation": f"Calculated OPM ({calc_opm:.2f}%) differs from reported OPM ({reported_opm:.2f}%) by {diff:.2f}%"
            }

    return calc_opm, anomaly


def compute_return_on_equity(
    net_profit: Optional[float],
    equity_capital: Optional[float],
    reserves: Optional[float]
) -> Optional[float]:
    """
    Computes Return on Equity (ROE) percentage: net_profit / (equity_capital + reserves) * 100.
    Returns None if equity_capital + reserves <= 0 (negative/zero net worth).
    """
    if net_profit is None or equity_capital is None or reserves is None:
        return None

    net_worth = equity_capital + reserves
    if net_worth <= 0:
        return None

    return (net_profit / net_worth) * 100.0


def compute_return_on_capital_employed(
    operating_profit: Optional[float],
    other_income: Optional[float],
    equity_capital: Optional[float],
    reserves: Optional[float],
    borrowings: Optional[float]
) -> Optional[float]:
    """
    Computes Return on Capital Employed (ROCE) percentage:
    ROCE = (EBIT / Capital Employed) * 100
    where EBIT = operating_profit + (other_income or 0)
    and Capital Employed = equity_capital + reserves + borrowings.
    Returns None if Capital Employed <= 0.
    """
    if operating_profit is None or equity_capital is None or reserves is None or borrowings is None:
        return None

    ebit = operating_profit + (other_income if other_income is not None else 0.0)
    capital_employed = equity_capital + reserves + borrowings

    if capital_employed <= 0:
        return None

    return (ebit / capital_employed) * 100.0


def compute_return_on_assets(
    net_profit: Optional[float],
    total_assets: Optional[float]
) -> Optional[float]:
    """
    Computes Return on Assets (ROA) percentage: (net_profit / total_assets) * 100.
    Returns None if total_assets is None or total_assets <= 0.
    """
    if net_profit is None or total_assets is None or total_assets <= 0:
        return None

    return (net_profit / total_assets) * 100.0


def compute_debt_to_equity(
    borrowings: Optional[float],
    equity_capital: Optional[float],
    reserves: Optional[float],
    is_financial: bool = False
) -> Tuple[Optional[float], bool]:
    """
    Computes Debt-to-Equity ratio: borrowings / (equity_capital + reserves).
    - If borrowings == 0: returns (0.0, False) [Debt-free].
    - If net worth <= 0: returns (None, False).
    - If D/E > 5 and company is NOT in Financials sector: high_leverage_flag = True.
    Returns (debt_to_equity, high_leverage_flag).
    """
    if borrowings is None or equity_capital is None or reserves is None:
        return None, False

    if borrowings == 0:
        return 0.0, False

    net_worth = equity_capital + reserves
    if net_worth <= 0:
        return None, False

    de_ratio = borrowings / net_worth
    high_leverage = (de_ratio > 5.0) and (not is_financial)

    return de_ratio, high_leverage


def compute_interest_coverage(
    operating_profit: Optional[float],
    other_income: Optional[float],
    interest: Optional[float]
) -> Tuple[Optional[float], Optional[str], bool]:
    """
    Computes Interest Coverage Ratio (ICR):
    ICR = (operating_profit + other_income) / interest
    - If interest == 0: returns (None, "Debt Free", False).
    - If ICR < 1.5: icr_warning_flag = True.
    Returns (icr_value, icr_label, icr_warning_flag).
    """
    if interest is None:
        return None, None, False

    if interest == 0:
        return None, "Debt Free", False

    ebit = (operating_profit if operating_profit is not None else 0.0) + (other_income if other_income is not None else 0.0)
    icr = ebit / interest
    warning = (icr < 1.5)

    return icr, None, warning


def compute_net_debt(
    borrowings: Optional[float],
    investments: Optional[float]
) -> Optional[float]:
    """
    Computes Net Debt: borrowings - investments (using investments as liquid asset proxy).
    """
    if borrowings is None:
        return None
    inv = investments if investments is not None else 0.0
    return borrowings - inv


def compute_asset_turnover(
    sales: Optional[float],
    total_assets: Optional[float]
) -> Optional[float]:
    """
    Computes Asset Turnover ratio: sales / total_assets.
    Returns None if total_assets is None or total_assets <= 0.
    """
    if sales is None or total_assets is None or total_assets <= 0:
        return None

    return sales / total_assets
