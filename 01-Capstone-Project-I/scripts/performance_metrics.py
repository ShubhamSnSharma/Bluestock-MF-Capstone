"""
Fund Performance Analytics Metrics Module
==========================================

This module provides reusable, pure financial calculation functions for mutual fund performance,
risk metrics, alpha/beta estimation, drawdowns, and portfolio risk scoring.

Functions:
    - compute_daily_returns
    - compute_cagr
    - compute_sharpe_ratio
    - compute_sortino_ratio
    - compute_alpha_beta
    - compute_max_drawdown
    - tracking_error
    - compute_rank
    - normalize_score
"""

from typing import Union, Tuple, Dict, Any, Optional
import numpy as np
import pandas as pd
from scipy import stats


def compute_daily_returns(prices: Union[pd.Series, pd.DataFrame]) -> Union[pd.Series, pd.DataFrame]:
    """
    Computes daily percentage returns from a price or NAV series/dataframe.

    Parameters:
        prices (pd.Series or pd.DataFrame): Historical prices or NAVs.

    Returns:
        pd.Series or pd.DataFrame: Daily percentage returns.
    """
    if not isinstance(prices, (pd.Series, pd.DataFrame)):
        raise TypeError("Input 'prices' must be a pandas Series or DataFrame.")
    if prices.empty:
        raise ValueError("Input 'prices' cannot be empty.")
    
    return prices.pct_change(fill_method=None).copy()


def compute_cagr(
    data: Union[pd.Series, pd.DataFrame, float],
    years: Optional[float] = None,
    end_value: Optional[float] = None
) -> Union[float, pd.Series, pd.DataFrame]:
    """
    Computes Compound Annual Growth Rate (CAGR).

    Can accept:
        - A float start_value with end_value and years specified.
        - A pd.Series of NAVs (indexed by date or with explicit years provided).
        - A pd.DataFrame of NAVs across multiple schemes.

    Parameters:
        data (pd.Series, pd.DataFrame, or float): Start value or NAV series/dataframe.
        years (float, optional): Number of years over which CAGR is calculated.
        end_value (float, optional): Ending value if data is a start float value.

    Returns:
        float, pd.Series, or pd.DataFrame: Calculated CAGR value(s).
    """
    if isinstance(data, (int, float)):
        if end_value is None or years is None:
            raise ValueError("When 'data' is a float/int start value, 'end_value' and 'years' must be provided.")
        if data <= 0 or end_value <= 0 or years <= 0:
            raise ValueError("Start value, end value, and years must all be positive numbers.")
        return float((end_value / data) ** (1 / years) - 1)

    if isinstance(data, pd.Series):
        if data.empty or len(data) < 2:
            raise ValueError("NAV Series must contain at least 2 data points.")
        start_val = data.iloc[0]
        end_val = data.iloc[-1]
        if start_val <= 0 or end_val <= 0:
            raise ValueError("NAV values must be positive.")

        if years is None:
            if isinstance(data.index, pd.DatetimeIndex):
                years = (data.index[-1] - data.index[0]).days / 365.25
            else:
                raise ValueError("If 'years' is not provided, the Series index must be a DatetimeIndex.")

        if years <= 0:
            raise ValueError("Duration in years must be positive.")

        return float((end_val / start_val) ** (1 / years) - 1)

    if isinstance(data, pd.DataFrame):
        if data.empty or len(data) < 2:
            raise ValueError("NAV DataFrame must contain at least 2 rows.")
        
        cagr_results = {}
        for col in data.columns:
            series = data[col].dropna()
            if len(series) >= 2:
                cagr_results[col] = compute_cagr(series, years=years)
            else:
                cagr_results[col] = np.nan
        return pd.Series(cagr_results)

    raise TypeError("Input 'data' must be a float, int, pd.Series, or pd.DataFrame.")


def compute_sharpe_ratio(
    returns: Union[pd.Series, pd.DataFrame],
    risk_free_rate: float = 0.065,
    periods_per_year: int = 252
) -> Union[float, pd.Series]:
    """
    Computes the annualized Sharpe Ratio.

    Parameters:
        returns (pd.Series or pd.DataFrame): Daily return series or dataframe.
        risk_free_rate (float): Annualized risk-free rate proxy (default 0.065 for 6.5%).
        periods_per_year (int): Trading periods per year (default 252).

    Returns:
        float or pd.Series: Annualized Sharpe Ratio(s).
    """
    if not isinstance(returns, (pd.Series, pd.DataFrame)):
        raise TypeError("Input 'returns' must be a pandas Series or DataFrame.")
    if returns.empty:
        raise ValueError("Input 'returns' cannot be empty.")

    clean_returns = returns.dropna()
    mean_ret = clean_returns.mean()
    std_ret = clean_returns.std()

    ann_return = mean_ret * periods_per_year
    ann_std = std_ret * np.sqrt(periods_per_year)

    if isinstance(ann_std, pd.Series):
        ann_std = ann_std.replace(0, np.nan)
    elif ann_std == 0:
        return np.nan

    return (ann_return - risk_free_rate) / ann_std


def compute_sortino_ratio(
    returns: Union[pd.Series, pd.DataFrame],
    risk_free_rate: float = 0.065,
    periods_per_year: int = 252
) -> Union[float, pd.Series]:
    """
    Computes the annualized Sortino Ratio focusing on downside volatility.

    Parameters:
        returns (pd.Series or pd.DataFrame): Daily return series or dataframe.
        risk_free_rate (float): Annualized risk-free rate proxy (default 0.065 for 6.5%).
        periods_per_year (int): Trading periods per year (default 252).

    Returns:
        float or pd.Series: Annualized Sortino Ratio(s).
    """
    if not isinstance(returns, (pd.Series, pd.DataFrame)):
        raise TypeError("Input 'returns' must be a pandas Series or DataFrame.")
    if returns.empty:
        raise ValueError("Input 'returns' cannot be empty.")

    daily_rf = risk_free_rate / periods_per_year

    if isinstance(returns, pd.Series):
        clean_returns = returns.dropna()
        excess_returns = clean_returns - daily_rf
        downside_returns = np.minimum(excess_returns, 0.0)
        downside_std = np.sqrt(np.mean(downside_returns ** 2)) * np.sqrt(periods_per_year)

        if downside_std == 0:
            return np.nan

        ann_return = clean_returns.mean() * periods_per_year
        return float((ann_return - risk_free_rate) / downside_std)

    else:
        results = {}
        for col in returns.columns:
            results[col] = compute_sortino_ratio(
                returns[col], risk_free_rate=risk_free_rate, periods_per_year=periods_per_year
            )
        return pd.Series(results)


def compute_alpha_beta(
    fund_returns: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_rate: float = 0.065,
    periods_per_year: int = 252
) -> Tuple[float, float]:
    """
    Computes Jensen's Alpha (annualized) and Beta against a benchmark index
    using OLS regression (scipy.stats.linregress).

    Parameters:
        fund_returns (pd.Series): Daily fund return series.
        benchmark_returns (pd.Series): Daily benchmark return series.
        risk_free_rate (float): Annualized risk-free rate proxy (default 0.065 for 6.5%).
        periods_per_year (int): Trading periods per year (default 252).

    Returns:
        Tuple[float, float]: (annualized_alpha, beta)
    """
    if not isinstance(fund_returns, pd.Series) or not isinstance(benchmark_returns, pd.Series):
        raise TypeError("Both fund_returns and benchmark_returns must be pandas Series.")

    aligned = pd.concat([fund_returns, benchmark_returns], axis=1).dropna()
    if len(aligned) < 2:
        raise ValueError("At least 2 overlapping return points are required to compute Alpha/Beta.")

    f_ret = aligned.iloc[:, 0]
    b_ret = aligned.iloc[:, 1]

    daily_rf = risk_free_rate / periods_per_year
    f_excess = f_ret - daily_rf
    b_excess = b_ret - daily_rf

    slope, intercept, _, _, _ = stats.linregress(b_excess, f_excess)

    beta = float(slope)
    alpha = float(intercept * periods_per_year)

    return (alpha, beta)


def compute_max_drawdown(prices: pd.Series) -> Dict[str, Any]:
    """
    Computes Maximum Drawdown along with Peak Date, Trough Date, and Recovery Date.

    Parameters:
        prices (pd.Series): Historical price/NAV series indexed by date or sequential order.

    Returns:
        Dict[str, Any]: {
            "max_drawdown": float,
            "peak_date": Any,
            "trough_date": Any,
            "recovery_date": Any
        }
    """
    if not isinstance(prices, pd.Series):
        raise TypeError("Input 'prices' must be a pandas Series.")
    if prices.empty or len(prices) < 2:
        raise ValueError("Prices series must contain at least 2 data points.")

    clean_prices = prices.dropna()
    cummax = clean_prices.cummax()
    drawdown = (clean_prices - cummax) / cummax

    trough_date = drawdown.idxmin()
    max_dd = float(drawdown.loc[trough_date])

    peak_date = clean_prices.loc[:trough_date].idxmax()
    peak_val = clean_prices.loc[peak_date]

    post_trough_prices = clean_prices.loc[trough_date:]
    recovered = post_trough_prices[post_trough_prices >= peak_val]

    if not recovered.empty:
        recovery_date = recovered.index[0]
    else:
        recovery_date = None

    return {
        "max_drawdown": max_dd,
        "peak_date": peak_date,
        "trough_date": trough_date,
        "recovery_date": recovery_date
    }


def tracking_error(
    fund_returns: pd.Series,
    benchmark_returns: pd.Series,
    periods_per_year: int = 252
) -> float:
    """
    Computes annualized Tracking Error relative to a benchmark.

    Parameters:
        fund_returns (pd.Series): Daily fund return series.
        benchmark_returns (pd.Series): Daily benchmark return series.
        periods_per_year (int): Trading periods per year (default 252).

    Returns:
        float: Annualized tracking error.
    """
    if not isinstance(fund_returns, pd.Series) or not isinstance(benchmark_returns, pd.Series):
        raise TypeError("Both fund_returns and benchmark_returns must be pandas Series.")

    aligned = pd.concat([fund_returns, benchmark_returns], axis=1).dropna()
    if len(aligned) < 2:
        raise ValueError("At least 2 overlapping return points are required to compute tracking error.")

    diff = aligned.iloc[:, 0] - aligned.iloc[:, 1]
    return float(diff.std(ddof=1) * np.sqrt(periods_per_year))


def compute_rank(
    values: Union[pd.Series, pd.DataFrame],
    ascending: bool = False
) -> Union[pd.Series, pd.DataFrame]:
    """
    Computes relative rank for series or dataframe columns.

    Parameters:
        values (pd.Series or pd.DataFrame): Values to rank.
        ascending (bool): False for higher values = rank 1 (default False).

    Returns:
        pd.Series or pd.DataFrame: Ranked values.
    """
    if not isinstance(values, (pd.Series, pd.DataFrame)):
        raise TypeError("Input 'values' must be a pandas Series or DataFrame.")

    return values.rank(ascending=ascending, method='min').copy()


def normalize_score(
    values: Union[pd.Series, pd.DataFrame],
    target_min: float = 0.0,
    target_max: float = 100.0
) -> Union[pd.Series, pd.DataFrame]:
    """
    Min-Max normalizes values to a specified range (e.g. 0 to 100).

    Parameters:
        values (pd.Series or pd.DataFrame): Input values to normalize.
        target_min (float): Minimum score bound (default 0.0).
        target_max (float): Maximum score bound (default 100.0).

    Returns:
        pd.Series or pd.DataFrame: Normalized scores.
    """
    if not isinstance(values, (pd.Series, pd.DataFrame)):
        raise TypeError("Input 'values' must be a pandas Series or DataFrame.")

    min_val = values.min()
    max_val = values.max()

    if isinstance(values, pd.DataFrame):
        range_val = max_val - min_val
        range_val = range_val.replace(0, np.nan)
        normalized = (values - min_val) / range_val * (target_max - target_min) + target_min
        return normalized.fillna(target_min)
    else:
        if max_val == min_val:
            return pd.Series(target_min, index=values.index)
        return (values - min_val) / (max_val - min_val) * (target_max - target_min) + target_min
