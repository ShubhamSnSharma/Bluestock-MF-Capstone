import nbformat as nbf

nb = nbf.v4.new_notebook()

cells = []

# Markdown 1: Header
header_md = """# Fund Performance Analytics

**Project**: Bluestock Mutual Fund Capstone  
**Module**: Day 04 - Fund Performance Analytics  
**Objective**: Evaluate and quantify mutual fund performance, risk-adjusted metrics, Jensen's Alpha, Beta, Tracking Error, Maximum Drawdowns, and portfolio risk profiles for Bluestock Mutual Fund schemes.

---"""

cells.append(nbf.v4.new_markdown_cell(header_md))

# Markdown 2: Section 1
sec1_md = """## Section 1: Import Libraries"""
cells.append(nbf.v4.new_markdown_cell(sec1_md))

code1 = """import sys
from pathlib import Path

# Add scripts directory to sys.path
scripts_path = Path('../scripts').resolve()
if str(scripts_path) not in sys.path:
    sys.path.append(str(scripts_path))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import scipy.stats as stats

# Import reusable financial metrics from performance_metrics.py
from performance_metrics import (
    compute_daily_returns,
    compute_cagr,
    compute_sharpe_ratio,
    compute_sortino_ratio,
    compute_alpha_beta,
    compute_max_drawdown,
    tracking_error,
    compute_rank,
    normalize_score
)

print("Libraries and reusable performance metrics imported successfully!")"""

cells.append(nbf.v4.new_code_cell(code1))

# Markdown 3: Section 2
sec2_md = """## Section 2: Load Data"""
cells.append(nbf.v4.new_markdown_cell(sec2_md))

code2 = """data_dir = Path('../data/processed').resolve()

df_nav_history = pd.read_csv(data_dir / '02_nav_history_cleaned.csv')
df_scheme_perf = pd.read_csv(data_dir / '07_scheme_performance_cleaned.csv')
df_benchmarks = pd.read_csv(data_dir / '10_benchmark_indices_cleaned.csv')
df_fund_master = pd.read_csv(data_dir / '01_fund_master_cleaned.csv')

datasets = {
    'NAV History (02_nav_history_cleaned.csv)': df_nav_history,
    'Scheme Performance (07_scheme_performance_cleaned.csv)': df_scheme_perf,
    'Benchmark Indices (10_benchmark_indices_cleaned.csv)': df_benchmarks,
    'Fund Master (01_fund_master_cleaned.csv)': df_fund_master
}

for name, df in datasets.items():
    print("=" * 60)
    print(f"Dataset: {name}")
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
    print("-" * 60)
    print("Columns & Data Types:")
    print(df.dtypes)
    print("\\n")"""

cells.append(nbf.v4.new_code_cell(code2))

# Markdown 4: Section 3
sec3_md = """## Section 3: Data Validation"""
cells.append(nbf.v4.new_markdown_cell(sec3_md))

code3 = """print("Performing Data Validation Checks...\\n")

# Parse dates
df_nav_history['date'] = pd.to_datetime(df_nav_history['date'])
df_benchmarks['date'] = pd.to_datetime(df_benchmarks['date'])

# 1. Verify dates are sorted
nav_dates_sorted = df_nav_history.groupby('amfi_code')['date'].apply(lambda s: s.is_monotonic_increasing).all()
bench_dates_sorted = df_benchmarks.groupby('index_name')['date'].apply(lambda s: s.is_monotonic_increasing).all()

print(f"1. NAV dates sorted monotonically per scheme: {nav_dates_sorted}")
print(f"   Benchmark dates sorted monotonically per index: {bench_dates_sorted}")

# 2. Verify NAV values are positive
positive_nav = (df_nav_history['nav'] > 0).all()
print(f"2. All NAV values are strictly positive (> 0): {positive_nav}")

# 3. Verify no duplicate (amfi_code, date)
duplicates_count = df_nav_history.duplicated(subset=['amfi_code', 'date']).sum()
print(f"3. Duplicate (amfi_code, date) records count: {duplicates_count} (Pass: {duplicates_count == 0})")

# 4. Verify no missing NAV
missing_nav_count = df_nav_history['nav'].isna().sum()
print(f"4. Missing NAV values count: {missing_nav_count} (Pass: {missing_nav_count == 0})")

# 5. Benchmark dates alignment with NAV history
nav_min_date, nav_max_date = df_nav_history['date'].min(), df_nav_history['date'].max()
bench_min_date, bench_max_date = df_benchmarks['date'].min(), df_benchmarks['date'].max()

print(f"5. Date Ranges:")
print(f"   NAV History Date Range: {nav_min_date.strftime('%Y-%m-%d')} to {nav_max_date.strftime('%Y-%m-%d')}")
print(f"   Benchmark Date Range:   {bench_min_date.strftime('%Y-%m-%d')} to {bench_max_date.strftime('%Y-%m-%d')}")
bench_aligned = (bench_min_date <= nav_min_date) and (bench_max_date >= nav_max_date)
print(f"   Benchmark date range covers NAV history range: {bench_aligned}")

# 6. Exactly 40 mutual fund schemes exist
schemes_in_master = df_fund_master['amfi_code'].nunique()
schemes_in_nav = df_nav_history['amfi_code'].nunique()
schemes_in_perf = df_scheme_perf['amfi_code'].nunique()
print(f"6. Scheme counts across datasets:")
print(f"   Fund Master scheme count:       {schemes_in_master}")
print(f"   NAV History scheme count:       {schemes_in_nav}")
print(f"   Scheme Performance scheme count:{schemes_in_perf}")
print(f"   Exactly 40 schemes exist check: {schemes_in_master == 40 and schemes_in_nav == 40 and schemes_in_perf == 40}")

print("\\nData Validation Completed Successfully!")"""

cells.append(nbf.v4.new_code_cell(code3))

# Markdown 5: Section 4
sec4_md = """## Section 4: Reusable Functions Module

The financial performance functions have been modularized inside `scripts/performance_metrics.py`.

The available functions are:
- `compute_daily_returns`: Calculates daily percentage returns (`pct_change`).
- `compute_cagr`: Computes Compound Annual Growth Rate over specified period/years.
- `compute_sharpe_ratio`: Calculates annualized Sharpe Ratio using $R_f = 6.5\\%$.
- `compute_sortino_ratio`: Calculates annualized Sortino Ratio focusing on downside risk using $R_f = 6.5\\%$.
- `compute_alpha_beta`: Estimates Jensen's Alpha and Beta against benchmark indices using $R_f = 6.5\\%$.
- `compute_max_drawdown`: Computes Maximum Drawdown along with Peak Date, Trough Date, and Recovery Date.
- `tracking_error`: Calculates annualized Tracking Error relative to benchmark returns.
- `compute_rank`: Ranks metrics across funds/schemes.
- `normalize_score`: Min-Max scales scores to a 0–100 range for composite scorecard evaluation.

*(Full calculations across the complete dataset will be executed in subsequent sections.)*"""

cells.append(nbf.v4.new_markdown_cell(sec4_md))

# Markdown 6: Section 5
sec5_md = """## Section 5: Helper Function Smoke Tests

Smoke testing all reusable functions on sample data to confirm correctness before full dataset evaluation."""

cells.append(nbf.v4.new_markdown_cell(sec5_md))

code4 = """print("Running Smoke Tests on Reusable Helper Functions...\\n")

# Create sample dataset
sample_dates = pd.date_range('2023-01-01', periods=252, freq='B')
np.random.seed(42)
sample_nav = pd.Series(100 * np.exp(np.cumsum(np.random.normal(0.0005, 0.01, 252))), index=sample_dates)
sample_bench = pd.Series(1000 * np.exp(np.cumsum(np.random.normal(0.0003, 0.008, 252))), index=sample_dates)

# Test compute_daily_returns
s_rets = compute_daily_returns(sample_nav)
b_rets = compute_daily_returns(sample_bench)
assert len(s_rets) == 252, "Daily returns length mismatch"

# Test compute_cagr
sample_cagr = compute_cagr(sample_nav)
assert isinstance(sample_cagr, float), "CAGR should return a float"

# Test compute_sharpe_ratio
sample_sharpe = compute_sharpe_ratio(s_rets, risk_free_rate=0.065)
assert not np.isnan(sample_sharpe), "Sharpe ratio should be numeric"

# Test compute_sortino_ratio
sample_sortino = compute_sortino_ratio(s_rets, risk_free_rate=0.065)
assert not np.isnan(sample_sortino), "Sortino ratio should be numeric"

# Test compute_alpha_beta
sample_alpha, sample_beta = compute_alpha_beta(s_rets, b_rets, risk_free_rate=0.065)
assert isinstance(sample_alpha, float) and isinstance(sample_beta, float), "Alpha/Beta should return floats"

# Test compute_max_drawdown
sample_mdd = compute_max_drawdown(sample_nav)
assert "max_drawdown" in sample_mdd and "peak_date" in sample_mdd, "Max drawdown dictionary keys missing"

# Test tracking_error
sample_te = tracking_error(s_rets, b_rets)
assert isinstance(sample_te, float), "Tracking error should return a float"

# Test compute_rank & normalize_score
sample_scores = pd.Series([0.15, 0.22, 0.08, 0.30])
sample_rank = compute_rank(sample_scores)
sample_norm = normalize_score(sample_scores, 0, 100)
assert sample_norm.max() == 100.0 and sample_norm.min() == 0.0, "Normalization bounds failed"

print("All smoke tests passed successfully!")
print(f"Sample Results:")
print(f"  - CAGR:          {sample_cagr:.4%}")
print(f"  - Sharpe Ratio:  {sample_sharpe:.4f}")
print(f"  - Sortino Ratio: {sample_sortino:.4f}")
print(f"  - Alpha:         {sample_alpha:.4f}")
print(f"  - Beta:          {sample_beta:.4f}")
print(f"  - Max Drawdown:  {sample_mdd['max_drawdown']:.4%} (Peak: {sample_mdd['peak_date'].strftime('%Y-%m-%d')}, Trough: {sample_mdd['trough_date'].strftime('%Y-%m-%d')})")
print(f"  - Tracking Error:{sample_te:.4%}")"""

cells.append(nbf.v4.new_code_cell(code4))

nb['cells'] = cells

with open('notebooks/Performance_Analytics.ipynb', 'w') as f:
    nbf.write(nb, f)

print("Performance_Analytics.ipynb successfully created!")
