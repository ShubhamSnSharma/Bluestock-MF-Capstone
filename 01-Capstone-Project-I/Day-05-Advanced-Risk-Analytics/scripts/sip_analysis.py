"""
SIP Continuity Analysis Module
===============================

This module provides reusable functions for analyzing Systematic Investment Plan (SIP)
continuity, computing gaps between consecutive SIP payments, identifying at-risk investors
with delayed contributions, and visualizing SIP gap distributions.

Functions:
    - prepare_sip
    - compute_sip_gaps
    - flag_at_risk_investors
    - sip_summary
    - plot_gap_distribution
"""

from pathlib import Path
from typing import Union, Dict, Any
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def prepare_sip(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validates transaction columns, filters for SIP transactions, parses dates,
    and sorts records by investor_id and transaction_date.

    Parameters:
        df (pd.DataFrame): Raw or cleaned transactions dataframe.

    Returns:
        pd.DataFrame: Filtered and sorted SIP transaction dataframe.

    Raises:
        TypeError: If input is not a pandas DataFrame.
        ValueError: If required columns are missing or no SIP records exist.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input 'df' must be a pandas DataFrame.")

    required_cols = {'investor_id', 'transaction_date', 'transaction_type', 'amount_inr'}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in SIP DataFrame: {missing}")

    cleaned = df.copy()
    cleaned['transaction_date'] = pd.to_datetime(cleaned['transaction_date'], errors='coerce')
    cleaned['amount_inr'] = pd.to_numeric(cleaned['amount_inr'], errors='coerce')
    cleaned['transaction_type'] = cleaned['transaction_type'].astype(str).str.strip().str.upper()

    cleaned = cleaned.dropna(subset=['transaction_date', 'investor_id']).copy()

    sip_df = cleaned[cleaned['transaction_type'] == 'SIP'].copy()

    if sip_df.empty:
        raise ValueError("No SIP transactions found in the input DataFrame.")

    sorted_sip = sip_df.sort_values(['investor_id', 'transaction_date']).reset_index(drop=True)
    return sorted_sip


def compute_sip_gaps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the gap in days between consecutive SIP transactions for each investor.

    Parameters:
        df (pd.DataFrame): Transactions or SIP dataframe.

    Returns:
        pd.DataFrame: Dataframe containing investor_id, transaction_date, and gap_days.
    """
    sip_df = prepare_sip(df)

    sip_df['prev_transaction_date'] = sip_df.groupby('investor_id')['transaction_date'].shift(1)
    sip_df['gap_days'] = (sip_df['transaction_date'] - sip_df['prev_transaction_date']).dt.days

    gap_df = sip_df[['investor_id', 'transaction_date', 'gap_days']].copy()
    return gap_df


def flag_at_risk_investors(
    gap_df: pd.DataFrame,
    threshold: int = 35
) -> pd.DataFrame:
    """
    Identifies and flags investors with SIP payment gaps exceeding a specified threshold.

    An investor is flagged as 'At Risk' if their maximum consecutive SIP gap or elapsed days
    since their last SIP exceeds the threshold (default 35 days).

    Parameters:
        gap_df (pd.DataFrame): Dataframe output from compute_sip_gaps.
        threshold (int): Gap threshold in days (default 35 days).

    Returns:
        pd.DataFrame: Dataframe of investors with max_gap_days, last_sip_date, days_since_last_sip, and is_at_risk status.

    Raises:
        TypeError: If input is not a pandas DataFrame.
        ValueError: If required columns are missing or threshold is invalid.
    """
    if not isinstance(gap_df, pd.DataFrame):
        raise TypeError("Input 'gap_df' must be a pandas DataFrame.")
    if 'investor_id' not in gap_df.columns or 'gap_days' not in gap_df.columns:
        raise ValueError("DataFrame must contain 'investor_id' and 'gap_days' columns.")
    if not isinstance(threshold, (int, float)) or threshold <= 0:
        raise ValueError("Threshold must be a positive number.")

    max_dataset_date = gap_df['transaction_date'].max()

    summary = gap_df.groupby('investor_id').agg(
        max_consecutive_gap=('gap_days', 'max'),
        last_sip_date=('transaction_date', 'max'),
        total_sip_count=('transaction_date', 'count')
    ).reset_index()

    summary['days_since_last_sip'] = (max_dataset_date - summary['last_sip_date']).dt.days
    summary['max_consecutive_gap'] = summary['max_consecutive_gap'].fillna(0)

    # At Risk if either consecutive gap > threshold OR days since last SIP > threshold
    summary['is_at_risk'] = (summary['max_consecutive_gap'] > threshold) | (summary['days_since_last_sip'] > threshold)

    return summary.sort_values('days_since_last_sip', ascending=False).reset_index(drop=True)


def sip_summary(gap_df: pd.DataFrame, threshold: int = 35) -> Dict[str, Any]:
    """
    Calculates summary metrics for SIP continuity and risk status across all investors.

    Parameters:
        gap_df (pd.DataFrame): Dataframe output from compute_sip_gaps.
        threshold (int): At-risk gap threshold in days (default 35).

    Returns:
        Dict[str, Any]: Summary dictionary containing:
            - total_investors (int)
            - active_investors (int)
            - at_risk_investors (int)
            - at_risk_percentage (float)
            - average_gap (float)
            - median_gap (float)
            - maximum_gap (float)
    """
    if not isinstance(gap_df, pd.DataFrame):
        raise TypeError("Input 'gap_df' must be a pandas DataFrame.")

    flagged = flag_at_risk_investors(gap_df, threshold=threshold)
    valid_gaps = gap_df['gap_days'].dropna()

    total_inv = int(len(flagged))
    at_risk_inv = int(flagged['is_at_risk'].sum())
    active_inv = total_inv - at_risk_inv
    pct_at_risk = round((at_risk_inv / total_inv * 100.0), 2) if total_inv > 0 else 0.0

    avg_gap = float(valid_gaps.mean()) if not valid_gaps.empty else 0.0
    med_gap = float(valid_gaps.median()) if not valid_gaps.empty else 0.0
    max_gap = float(valid_gaps.max()) if not valid_gaps.empty else 0.0

    return {
        'total_investors': total_inv,
        'active_investors': active_inv,
        'at_risk_investors': at_risk_inv,
        'at_risk_percentage': pct_at_risk,
        'average_gap': round(avg_gap, 2),
        'median_gap': round(med_gap, 2),
        'maximum_gap': round(max_gap, 2)
    }


def plot_gap_distribution(
    gap_df: pd.DataFrame,
    save_path: Union[str, Path]
) -> None:
    """
    Creates and exports a publication-quality histogram of SIP payment gap days.

    Parameters:
        gap_df (pd.DataFrame): Dataframe output from compute_sip_gaps.
        save_path (str or Path): Destination filepath for PNG output.
    """
    if not isinstance(gap_df, pd.DataFrame):
        raise TypeError("Input 'gap_df' must be a pandas DataFrame.")
    if 'gap_days' not in gap_df.columns:
        raise ValueError("Input DataFrame must contain 'gap_days' column.")

    clean_gaps = gap_df['gap_days'].dropna()

    out_path = Path(save_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(12, 6))
    plt.hist(clean_gaps, bins='auto', color='#1f77b4', edgecolor='none', alpha=0.75)
    plt.axvline(35.0, color='red', linestyle='--', linewidth=1.5, label='At-Risk Threshold (35 Days)')
    plt.axvline(clean_gaps.median(), color='green', linestyle=':', linewidth=1.5, label=f'Median Gap: {clean_gaps.median():.1f} Days')

    plt.title('Distribution of Days Between Consecutive SIP Transactions', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Gap Between SIP Transactions (Days)', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(fontsize=10, loc='upper right')
    plt.tight_layout()

    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
