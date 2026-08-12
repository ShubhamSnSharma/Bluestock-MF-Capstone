"""
Cohort Analysis Module
======================

This module provides reusable functions for cohort analysis of mutual fund investors.
Investors are grouped into cohorts based on their first transaction year to evaluate
long-term investor retention, total investment growth, SIP commitments, and fund preferences.

Functions:
    - prepare_transactions
    - create_investor_cohorts
    - cohort_summary
    - top_funds_by_cohort
"""

from pathlib import Path
from typing import Union, List
import pandas as pd
import numpy as np


def prepare_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validates required columns, cleans transaction dates, and removes invalid records.

    Parameters:
        df (pd.DataFrame): Raw investor transactions dataframe.

    Returns:
        pd.DataFrame: Cleaned transactions dataframe with parsed dates.

    Raises:
        TypeError: If input is not a pandas DataFrame.
        ValueError: If required columns are missing or if no valid records remain.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input 'df' must be a pandas DataFrame.")

    required_cols = {'investor_id', 'transaction_date', 'amfi_code', 'transaction_type', 'amount_inr'}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in transactions DataFrame: {missing}")

    cleaned = df.copy()
    cleaned['transaction_date'] = pd.to_datetime(cleaned['transaction_date'], errors='coerce')
    cleaned['amount_inr'] = pd.to_numeric(cleaned['amount_inr'], errors='coerce')
    cleaned['transaction_type'] = cleaned['transaction_type'].astype(str).str.strip().str.upper()

    cleaned = cleaned.dropna(subset=['transaction_date', 'investor_id', 'amount_inr']).copy()
    cleaned = cleaned[cleaned['amount_inr'] > 0].copy()

    if cleaned.empty:
        raise ValueError("No valid transaction records remain after cleaning.")

    return cleaned


def create_investor_cohorts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Determines the cohort year for each investor based on their earliest transaction date.

    Parameters:
        df (pd.DataFrame): Cleaned transactions dataframe.

    Returns:
        pd.DataFrame: Dataframe mapping investor_id to cohort_year.

    Raises:
        TypeError: If input is not a pandas DataFrame.
        ValueError: If required columns are missing.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input 'df' must be a pandas DataFrame.")

    if 'investor_id' not in df.columns or 'transaction_date' not in df.columns:
        raise ValueError("DataFrame must contain 'investor_id' and 'transaction_date' columns.")

    cleaned = df.copy()
    cleaned['transaction_date'] = pd.to_datetime(cleaned['transaction_date'], errors='coerce')

    first_tx = cleaned.groupby('investor_id')['transaction_date'].min().reset_index()
    first_tx['cohort_year'] = first_tx['transaction_date'].dt.year

    return first_tx[['investor_id', 'cohort_year']].copy()


def cohort_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes cohort summary metrics including investor counts, total investment,
    SIP totals, average/median investment per investor, and average SIP amounts.

    Parameters:
        df (pd.DataFrame): Cleaned transactions dataframe (with or without cohort_year).

    Returns:
        pd.DataFrame: Cohort summary aggregated by cohort_year.
    """
    cleaned = prepare_transactions(df)

    if 'cohort_year' not in cleaned.columns:
        cohorts = create_investor_cohorts(cleaned)
        cleaned = cleaned.merge(cohorts, on='investor_id', how='left')

    records = []
    for cohort_yr, group in cleaned.groupby('cohort_year'):
        inv_count = group['investor_id'].nunique()
        sip_rows = group[group['transaction_type'] == 'SIP']
        total_sip = float(sip_rows['amount_inr'].sum())
        total_invested = float(group['amount_inr'].sum())

        inv_totals = group.groupby('investor_id')['amount_inr'].sum()
        avg_inv_per_inv = float(inv_totals.mean()) if not inv_totals.empty else 0.0
        med_inv_per_inv = float(inv_totals.median()) if not inv_totals.empty else 0.0

        avg_sip = float(sip_rows['amount_inr'].mean()) if not sip_rows.empty else 0.0

        records.append({
            'cohort_year': int(cohort_yr),
            'investor_count': inv_count,
            'total_sip_amount': round(total_sip, 2),
            'total_invested_amount': round(total_invested, 2),
            'average_investment_per_investor': round(avg_inv_per_inv, 2),
            'average_sip': round(avg_sip, 2),
            'median_investment_per_investor': round(med_inv_per_inv, 2)
        })

    summary_df = pd.DataFrame(records).sort_values('cohort_year').reset_index(drop=True)
    return summary_df


def top_funds_by_cohort(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identifies the Top 5 mutual funds by total invested amount for every cohort year.

    Parameters:
        df (pd.DataFrame): Cleaned transactions dataframe.

    Returns:
        pd.DataFrame: Top 5 funds per cohort year with investment totals and ranks.
    """
    cleaned = prepare_transactions(df)

    if 'cohort_year' not in cleaned.columns:
        cohorts = create_investor_cohorts(cleaned)
        cleaned = cleaned.merge(cohorts, on='investor_id', how='left')

    top_records = []
    for cohort_yr, group in cleaned.groupby('cohort_year'):
        fund_totals = group.groupby('amfi_code')['amount_inr'].sum().reset_index()
        fund_totals = fund_totals.sort_values('amount_inr', ascending=False).head(5).reset_index(drop=True)

        for rank, row in enumerate(fund_totals.itertuples(), start=1):
            top_records.append({
                'cohort_year': int(cohort_yr),
                'rank': rank,
                'amfi_code': int(row.amfi_code),
                'total_invested_amount': round(float(row.amount_inr), 2)
            })

    return pd.DataFrame(top_records)
