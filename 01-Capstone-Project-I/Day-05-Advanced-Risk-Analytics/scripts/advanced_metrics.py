"""
Advanced Financial Metrics Module
=================================

This module provides production-grade advanced financial risk and performance
analytic functions including Value at Risk (VaR), Conditional Value at Risk (CVaR),
rolling Sharpe Ratio calculations, Herfindahl-Hirschman Index (HHI) concentration,
risk grading, and rolling performance plotting.

Functions:
    - validate_returns
    - compute_var
    - compute_cvar
    - compute_rolling_sharpe
    - compute_hhi
    - risk_grade
    - plot_rolling_sharpe
"""

from pathlib import Path
from typing import Union
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def validate_returns(returns: pd.Series) -> pd.Series:
    """
    Validates and cleans a pandas Series of returns.

    Removes infinite values (+inf, -inf), drops NaN entries, and casts to float.

    Parameters:
        returns (pd.Series): Input return series.

    Returns:
        pd.Series: Cleaned pandas Series containing only valid float values.

    Raises:
        TypeError: If input is not a pandas Series.
        ValueError: If cleaned Series is empty.
    """
    if not isinstance(returns, pd.Series):
        raise TypeError("Input 'returns' must be a pandas Series.")

    cleaned = returns.replace([np.inf, -np.inf], np.nan).dropna().astype(float).copy()

    if cleaned.empty:
        raise ValueError("Cleaned return series is empty.")

    return cleaned


def compute_var(returns: pd.Series, confidence: float = 0.95) -> float:
    """
    Computes Historical Value at Risk (VaR) at a specified confidence level.

    Parameters:
        returns (pd.Series): Daily return series.
        confidence (float): Confidence level (default 0.95 for 95% VaR).

    Returns:
        float: Historical VaR return threshold (5th percentile for 95% confidence).

    Raises:
        ValueError: If confidence is not strictly between 0 and 1.
    """
    if not (0 < confidence < 1):
        raise ValueError("Confidence level must be strictly between 0 and 1.")

    clean_series = validate_returns(returns)
    percentile = (1.0 - confidence) * 100.0
    return float(np.percentile(clean_series, percentile))


def compute_cvar(returns: pd.Series, confidence: float = 0.95) -> float:
    """
    Computes Conditional Value at Risk (CVaR / Expected Shortfall).

    CVaR represents the expected return below the VaR threshold.

    Parameters:
        returns (pd.Series): Daily return series.
        confidence (float): Confidence level (default 0.95 for 95% CVaR).

    Returns:
        float: Mean return of tail losses below the VaR threshold.
    """
    clean_series = validate_returns(returns)
    var_threshold = compute_var(clean_series, confidence=confidence)
    tail_returns = clean_series[clean_series <= var_threshold]

    if tail_returns.empty:
        return var_threshold

    return float(tail_returns.mean())


def compute_rolling_sharpe(
    returns: pd.Series,
    window: int = 90,
    risk_free_rate: float = 0.065
) -> pd.Series:
    """
    Computes rolling annualized Sharpe Ratio over a moving window.

    Parameters:
        returns (pd.Series): Daily return series.
        window (int): Moving window size in trading days (default 90).
        risk_free_rate (float): Annualized risk-free rate proxy (default 0.065 for 6.5%).

    Returns:
        pd.Series: Rolling annualized Sharpe Ratio.

    Raises:
        ValueError: If window size is less than 2.
    """
    if not isinstance(window, int) or window < 2:
        raise ValueError("Window size must be an integer greater than or equal to 2.")

    clean_series = validate_returns(returns)
    daily_rf = risk_free_rate / 252.0
    excess_returns = clean_series - daily_rf

    rolling_mean = excess_returns.rolling(window=window).mean()
    rolling_std = excess_returns.rolling(window=window).std()

    # Avoid division by zero
    rolling_std = rolling_std.replace(0.0, np.nan)
    rolling_sharpe = (rolling_mean / rolling_std) * np.sqrt(252.0)

    return rolling_sharpe


def compute_hhi(weights: Union[pd.Series, np.ndarray, list]) -> float:
    """
    Computes the Herfindahl-Hirschman Index (HHI) for portfolio concentration.

    Accepts weights as percentages (e.g., 40, 35, 25) or fractions (e.g., 0.40, 0.35, 0.25)
    and automatically normalizes them to sum to 1.0.

    Parameters:
        weights (pd.Series, np.ndarray, or list): Portfolio weight distribution.

    Returns:
        float: HHI concentration score (sum of squared fractional weights, 0.0 to 1.0).

    Raises:
        TypeError: If input is not a Series, array, or list.
        ValueError: If weights are empty, negative, or sum to zero.
    """
    if isinstance(weights, (pd.Series, np.ndarray)):
        arr = np.asarray(weights, dtype=float)
    elif isinstance(weights, list):
        arr = np.array(weights, dtype=float)
    else:
        raise TypeError("Input 'weights' must be a pandas Series, numpy array, or list.")

    arr = arr[~np.isnan(arr)]
    if arr.size == 0:
        raise ValueError("Input 'weights' cannot be empty.")
    if np.any(arr < 0):
        raise ValueError("Portfolio weights cannot be negative.")

    total_weight = float(np.sum(arr))
    if total_weight == 0:
        raise ValueError("Sum of portfolio weights cannot be zero.")

    normalized_weights = arr / total_weight
    return float(np.sum(normalized_weights ** 2))


def risk_grade(sharpe: float) -> str:
    """
    Categorizes scheme risk-adjusted performance grade based on Sharpe Ratio.

    Categorization:
        - Sharpe >= 1.0: "High"
        - 0.5 <= Sharpe < 1.0: "Moderate"
        - Sharpe < 0.5: "Low"

    Parameters:
        sharpe (float): Annualized Sharpe Ratio.

    Returns:
        str: Risk-adjusted rating grade ("High", "Moderate", or "Low").

    Raises:
        TypeError: If input sharpe is not numeric.
        ValueError: If input sharpe is NaN or infinite.
    """
    if not isinstance(sharpe, (int, float, np.number)):
        raise TypeError("Input 'sharpe' must be a numeric value.")
    if np.isnan(sharpe) or np.isinf(sharpe):
        raise ValueError("Input 'sharpe' must be a finite number.")

    if sharpe >= 1.0:
        return "High"
    elif sharpe >= 0.5:
        return "Moderate"
    else:
        return "Low"


def plot_rolling_sharpe(
    rolling_series: pd.Series,
    fund_name: str,
    save_path: Union[str, Path]
) -> None:
    """
    Creates and exports a publication-quality rolling Sharpe Ratio line chart.

    Parameters:
        rolling_series (pd.Series): Moving window Sharpe Ratio series indexed by date.
        fund_name (str): Mutual fund scheme name for chart title.
        save_path (str or Path): Destination filepath for PNG output.
    """
    if not isinstance(rolling_series, pd.Series):
        raise TypeError("Input 'rolling_series' must be a pandas Series.")

    out_path = Path(save_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(12, 6))
    plt.plot(rolling_series.index, rolling_series.values, color='#1f77b4', linewidth=1.8, label='Rolling Sharpe Ratio')
    plt.axhline(0.0, color='red', linestyle='--', linewidth=1.0, alpha=0.7, label='Zero Baseline')
    plt.axhline(1.0, color='green', linestyle=':', linewidth=1.0, alpha=0.7, label='High Performance Baseline (1.0)')

    plt.title(f'Rolling Sharpe Ratio (90-Day Window) - {fund_name}', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Annualized Sharpe Ratio', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(fontsize=10, loc='upper right')
    plt.tight_layout()

    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
