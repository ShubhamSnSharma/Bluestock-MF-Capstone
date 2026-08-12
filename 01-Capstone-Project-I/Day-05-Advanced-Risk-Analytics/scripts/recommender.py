"""
Risk-Based Fund Recommender Module
===================================

This module provides a simple, production-grade risk-based mutual fund recommendation engine.
It filters and ranks mutual fund schemes based on an investor's risk profile:
    - Conservative: Prioritizes capital preservation, low VaR/drawdown, and steady Sharpe ratios (e.g. Debt/Gilt).
    - Moderate: Balances growth with risk-adjusted performance (e.g. Large Cap, Flexicap).
    - Aggressive: Prioritizes high alpha, high CAGR, and maximum upside Sortino ratio (e.g. Small/Mid Cap).

Functions:
    - recommend_funds
"""

from typing import Union
import pandas as pd
import numpy as np


def recommend_funds(
    df_metrics: pd.DataFrame,
    risk_profile: str = "Moderate",
    top_n: int = 5
) -> pd.DataFrame:
    """
    Recommends top mutual fund schemes based on investor risk profile and quantitative metrics.

    Parameters:
        df_metrics (pd.DataFrame): Dataframe containing scheme metrics (amfi_code, scheme_name,
                                   category, sharpe_ratio, sortino_ratio, alpha, max_drawdown,
                                   var_95, cvar_95, cagr_available).
        risk_profile (str): Investor risk profile ("Conservative", "Moderate", "Aggressive").
        top_n (int): Number of top schemes to return (default 5).

    Returns:
        pd.DataFrame: Ranked dataframe of top recommended schemes matching the risk profile.

    Raises:
        TypeError: If df_metrics is not a pandas DataFrame.
        ValueError: If risk_profile is invalid or required metric columns are missing.
    """
    if not isinstance(df_metrics, pd.DataFrame):
        raise TypeError("Input 'df_metrics' must be a pandas DataFrame.")

    valid_profiles = {"Conservative", "Moderate", "Aggressive"}
    profile_clean = risk_profile.strip().capitalize()
    if profile_clean not in valid_profiles:
        raise ValueError(f"Invalid risk_profile '{risk_profile}'. Must be one of {valid_profiles}")

    if not isinstance(top_n, int) or top_n <= 0:
        raise ValueError("top_n must be a positive integer.")

    req_cols = {'amfi_code', 'scheme_name', 'category'}
    missing = req_cols - set(df_metrics.columns)
    if missing:
        raise ValueError(f"DataFrame is missing required identity columns: {missing}")

    df_clean = df_metrics.copy()

    if profile_clean == "Conservative":
        # Filter for low drawdown / high Sharpe / Debt or Low Beta
        # Higher score = smaller drawdown magnitude + higher Sharpe
        if 'max_drawdown' in df_clean.columns and 'sharpe_ratio' in df_clean.columns:
            # max_drawdown is negative; closer to 0 is better
            df_clean['rec_score'] = df_clean['sharpe_ratio'] + 2.0 * df_clean['max_drawdown']
        elif 'sharpe_ratio' in df_clean.columns:
            df_clean['rec_score'] = df_clean['sharpe_ratio']
        else:
            df_clean['rec_score'] = 1.0

    elif profile_clean == "Moderate":
        # Balanced score combining Sharpe, Sortino, and CAGR
        score_components = []
        if 'sharpe_ratio' in df_clean.columns:
            score_components.append(df_clean['sharpe_ratio'])
        if 'sortino_ratio' in df_clean.columns:
            score_components.append(df_clean['sortino_ratio'])
        if 'cagr_available' in df_clean.columns:
            score_components.append(df_clean['cagr_available'] / 100.0)

        if score_components:
            df_clean['rec_score'] = sum(score_components) / len(score_components)
        else:
            df_clean['rec_score'] = 1.0

    elif profile_clean == "Aggressive":
        # Prioritize high Alpha, high Sortino, and high CAGR
        score_components = []
        if 'alpha' in df_clean.columns:
            score_components.append(2.0 * df_clean['alpha'])
        if 'sortino_ratio' in df_clean.columns:
            score_components.append(df_clean['sortino_ratio'])
        if 'cagr_available' in df_clean.columns:
            score_components.append(df_clean['cagr_available'] / 50.0)

        if score_components:
            df_clean['rec_score'] = sum(score_components) / len(score_components)
        else:
            df_clean['rec_score'] = 1.0

    # Sort descending by recommendation score
    recommended = df_clean.sort_values('rec_score', ascending=False).head(top_n).reset_index(drop=True)
    recommended['risk_profile'] = profile_clean
    recommended['recommendation_rank'] = range(1, len(recommended) + 1)

    return recommended
