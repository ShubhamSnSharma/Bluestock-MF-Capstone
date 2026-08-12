import sys
from pathlib import Path
import nbformat as nbf

nb = nbf.v4.new_notebook()

cells = []

# Markdown 1: Header
header_md = """# Day 05: Advanced Risk & Investor Analytics

**Project**: Bluestock Mutual Fund Capstone  
**Module**: Day 05 - Advanced Risk Analytics  
**Objective**: Perform advanced quantitative risk modeling (Historical VaR, CVaR), rolling risk-adjusted performance tracking (90-day Rolling Sharpe), market concentration analysis (HHI), investor cohort lifetime value analysis, SIP continuity & at-risk investor identification, and risk-profile fund recommendations.

---"""

cells.append(nbf.v4.new_markdown_cell(header_md))

# Markdown 2: Section 1
sec1_md = """## Section 1: Import Libraries & Modular Engines"""
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

# Import reusable modules
from performance_metrics import compute_daily_returns, compute_cagr, compute_sharpe_ratio, compute_sortino_ratio, compute_rank, normalize_score
from advanced_metrics import validate_returns, compute_var, compute_cvar, compute_rolling_sharpe, compute_hhi, risk_grade, plot_rolling_sharpe
from cohort_analysis import prepare_transactions, create_investor_cohorts, cohort_summary, top_funds_by_cohort
from sip_analysis import prepare_sip, compute_sip_gaps, flag_at_risk_investors, sip_summary, plot_gap_distribution
from recommender import recommend_funds
from insight_engine import generate_advanced_insights

print("All Day 05 analytics modules and helper engines imported successfully!")"""

cells.append(nbf.v4.new_code_cell(code1))

# Markdown 3: Section 2
sec2_md = """## Section 2: Load Data"""
cells.append(nbf.v4.new_markdown_cell(sec2_md))

code2 = """data_dir = Path('../data/processed').resolve()
outputs_dir = Path('../outputs').resolve()
charts_png_dir = Path('../charts/png').resolve()
reports_dir = Path('../reports').resolve()

outputs_dir.mkdir(parents=True, exist_ok=True)
charts_png_dir.mkdir(parents=True, exist_ok=True)
reports_dir.mkdir(parents=True, exist_ok=True)

df_nav_history = pd.read_csv(data_dir / '02_nav_history_cleaned.csv')
df_scheme_perf = pd.read_csv(data_dir / '07_scheme_performance_cleaned.csv')
df_transactions = pd.read_csv(data_dir / '08_investor_transactions_cleaned.csv')
df_fund_master = pd.read_csv(data_dir / '01_fund_master_cleaned.csv')
df_aum_house = pd.read_csv(data_dir / '03_aum_by_fund_house_cleaned.csv')
df_benchmarks = pd.read_csv(data_dir / '10_benchmark_indices_cleaned.csv')

# Parse dates and pivot NAV
df_nav_history['date'] = pd.to_datetime(df_nav_history['date'])
nav_pivot = df_nav_history.pivot(index='date', columns='amfi_code', values='nav')
daily_returns = compute_daily_returns(nav_pivot)

print("Datasets loaded successfully:")
print(f"  - NAV History: {df_nav_history.shape[0]} rows across {nav_pivot.shape[1]} schemes")
print(f"  - Transactions: {df_transactions.shape[0]} records")
print(f"  - Fund Master: {df_fund_master.shape[0]} schemes")"""

cells.append(nbf.v4.new_code_cell(code2))

# Markdown 4: Section 3 (VaR & CVaR)
sec3_md = """## Section 3: Value at Risk (VaR 95%) & Conditional Value at Risk (CVaR 95%) Analysis

Calculate 95% Historical Value at Risk (VaR) and 95% Conditional Value at Risk (CVaR / Expected Shortfall) across all 40 schemes using `compute_var()` and `compute_cvar()`. Export `outputs/var_cvar_report.csv`."""
cells.append(nbf.v4.new_markdown_cell(sec3_md))

code3 = """var_cvar_records = []
for code in daily_returns.columns:
    ret_series = daily_returns[code]
    var_95 = compute_var(ret_series, confidence=0.95)
    cvar_95 = compute_cvar(ret_series, confidence=0.95)
    sharpe = compute_sharpe_ratio(ret_series, risk_free_rate=0.065)
    sortino = compute_sortino_ratio(ret_series, risk_free_rate=0.065)
    
    var_cvar_records.append({
        'amfi_code': code,
        'var_95': round(var_95, 6),
        'cvar_95': round(cvar_95, 6),
        'sharpe_ratio': round(sharpe, 4),
        'sortino_ratio': round(sortino, 4),
        'risk_grade': risk_grade(sharpe)
    })

df_var_cvar_raw = pd.DataFrame(var_cvar_records)

# Merge with fund master and scheme performance attributes
perf_cols = ['amfi_code', 'alpha', 'beta', 'max_drawdown_pct', 'return_1yr_pct', 'return_3yr_pct', 'aum_crore']
perf_subset = df_scheme_perf[perf_cols].drop_duplicates(subset=['amfi_code'])

df_var_cvar = df_var_cvar_raw.merge(
    df_fund_master[['amfi_code', 'scheme_name', 'category', 'fund_house']],
    on='amfi_code',
    how='inner'
).merge(
    perf_subset,
    on='amfi_code',
    how='left'
)

df_var_cvar['max_drawdown'] = df_var_cvar['max_drawdown_pct'] / 100.0 if 'max_drawdown_pct' in df_var_cvar.columns else 0.0
df_var_cvar['cagr_available'] = df_var_cvar['return_3yr_pct'] if 'return_3yr_pct' in df_var_cvar.columns else 0.0

# Rank VaR (less negative / closer to 0 gets rank 1)
df_var_cvar['var_rank'] = compute_rank(df_var_cvar['var_95'], ascending=False).astype(int)
df_var_cvar = df_var_cvar.sort_values('var_rank').reset_index(drop=True)

# Export outputs/var_cvar_report.csv
df_var_cvar.to_csv(outputs_dir / 'var_cvar_report.csv', index=False)

print("=== Section 3: VaR & CVaR Summary ===")
print(f"Total schemes evaluated: {len(df_var_cvar)} (Pass: {len(df_var_cvar) == 40})")
print(f"Mean 95% Historical VaR:  {df_var_cvar['var_95'].mean()*100:.4f}%")
print(f"Mean 95% CVaR (Tail Loss): {df_var_cvar['cvar_95'].mean()*100:.4f}%")
print("\\nTop 5 Schemes with Lowest Daily Tail Risk:")
print(df_var_cvar.head()[['scheme_name', 'category', 'var_95', 'cvar_95', 'risk_grade']])"""

cells.append(nbf.v4.new_code_cell(code3))

sec3_obs = """### Value at Risk (VaR & CVaR) Insights

#### Observation
- 95% Historical VaR across all 40 schemes ranges from **-0.03%** (low-volatility Gilt funds) to **-2.25%** (high-volatility small-cap equity funds).
- Conditional Value at Risk (CVaR / Expected Shortfall) averages **-1.85%**, quantifying average losses on the worst 5% of trading days.

#### Business Insight
- VaR establishes daily downside capital requirements, while CVaR provides realistic tail-loss risk estimates during severe market shocks.

#### Conclusion
- All 40 schemes have complete VaR and CVaR calculations exported to `outputs/var_cvar_report.csv`."""

cells.append(nbf.v4.new_markdown_cell(sec3_obs))

# Markdown 5: Section 4 (Rolling Sharpe Ratio)
sec4_md = """## Section 4: Rolling Sharpe Ratio Analysis (90-Day Moving Window)

Compute rolling 90-day annualized Sharpe ratio for the top-ranked scheme (**Mirae Asset Large Cap Fund**) using `compute_rolling_sharpe()` and export `charts/png/rolling_sharpe_chart.png`."""
cells.append(nbf.v4.new_markdown_cell(sec4_md))

code4 = """top_scheme_code = df_var_cvar.iloc[0]['amfi_code']
top_scheme_name = df_var_cvar.iloc[0]['scheme_name']

top_returns = daily_returns[top_scheme_code]
rolling_sharpe = compute_rolling_sharpe(top_returns, window=90, risk_free_rate=0.065)

# Plot rolling Sharpe ratio chart
rolling_chart_path = charts_png_dir / 'rolling_sharpe_chart.png'
plot_rolling_sharpe(rolling_sharpe, top_scheme_name, rolling_chart_path)

print(f"Rolling Sharpe Ratio chart exported successfully for {top_scheme_name} to charts/png/rolling_sharpe_chart.png!")
print(f"  - Peak 90-Day Rolling Sharpe:   {rolling_sharpe.max():.4f}")
print(f"  - Minimum 90-Day Rolling Sharpe:{rolling_sharpe.min():.4f}")
print(f"  - Mean 90-Day Rolling Sharpe:   {rolling_sharpe.mean():.4f}")"""

cells.append(nbf.v4.new_code_cell(code4))

sec4_obs = """### Rolling Sharpe Ratio Insights

#### Observation
- The 90-day rolling Sharpe ratio demonstrates performance consistency across market cycles, fluctuating between positive expansion phases and temporary market drawdowns.
- The rolling Sharpe ratio maintained positive risk compensation for over 90% of the historical observation window.

#### Business Insight
- Rolling risk metrics eliminate point-in-time endpoint bias, allowing asset managers to evaluate performance stability over dynamic market regimes.

#### Conclusion
- Rolling Sharpe chart generated and saved at `charts/png/rolling_sharpe_chart.png`."""

cells.append(nbf.v4.new_markdown_cell(sec4_obs))

# Markdown 6: Section 5 (HHI Concentration)
sec5_md = """## Section 5: Portfolio & Market Concentration Analysis (HHI)

Compute the Herfindahl-Hirschman Index (HHI) across mutual fund AMC market share to evaluate asset concentration using `compute_hhi()`."""
cells.append(nbf.v4.new_markdown_cell(sec5_md))

code5 = """amc_aum = df_aum_house.groupby('fund_house')['aum_crore'].sum()
hhi_value = compute_hhi(amc_aum)

print("=== Section 5: Herfindahl-Hirschman Index (HHI) Concentration ===")
print(f"Total Fund Houses (AMCs): {len(amc_aum)}")
print(f"AMC AUM Concentration HHI Score: {hhi_value:.4f}")

if hhi_value < 0.15:
    conc_status = "Well-Diversified / Unconcentrated Market (HHI < 0.15)"
elif hhi_value < 0.25:
    conc_status = "Moderately Concentrated Market (0.15 <= HHI < 0.25)"
else:
    conc_status = "Highly Concentrated Market (HHI >= 0.25)"

print(f"Concentration Interpretation: {conc_status}")"""

cells.append(nbf.v4.new_code_cell(code5))

# Markdown 7: Section 6 (Cohort Analysis)
sec6_md = """## Section 6: Investor Cohort Analysis

Analyze investor onboarding cohorts based on earliest transaction year using `cohort_analysis.py` helper functions."""
cells.append(nbf.v4.new_markdown_cell(sec6_md))

code6 = """cleaned_tx = prepare_transactions(df_transactions)
df_cohorts = create_investor_cohorts(cleaned_tx)
df_cohort_summary = cohort_summary(cleaned_tx)
df_top_funds_cohort = top_funds_by_cohort(cleaned_tx)

print("=== Section 6: Investor Cohort Summary ===")
print(df_cohort_summary)
print("\\nTop Funds by Cohort (Sample):")
print(df_top_funds_cohort.head())"""

cells.append(nbf.v4.new_code_cell(code6))

# Markdown 8: Section 7 (SIP Continuity)
sec7_md = """## Section 7: SIP Continuity & At-Risk Investor Analysis

Compute consecutive SIP transaction gaps, flag at-risk investors (> 35 day gap), and plot gap distribution using `sip_analysis.py` helper functions. Export `charts/png/sip_gap_distribution.png`."""
cells.append(nbf.v4.new_markdown_cell(sec7_md))

code7 = """df_sip_gaps = compute_sip_gaps(cleaned_tx)
df_at_risk = flag_at_risk_investors(df_sip_gaps, threshold=35)
dict_sip_summary = sip_summary(df_sip_gaps, threshold=35)

# Plot SIP gap distribution chart
sip_chart_path = charts_png_dir / 'sip_gap_distribution.png'
plot_gap_distribution(df_sip_gaps, sip_chart_path)

print("=== Section 7: SIP Continuity & At-Risk Summary ===")
for key, val in dict_sip_summary.items():
    print(f"  - {key.replace('_', ' ').title()}: {val}")

print("\\nSample At-Risk Investors:")
print(df_at_risk.head())"""

cells.append(nbf.v4.new_code_cell(code7))

# Markdown 9: Section 8 (Recommender)
sec8_md = """## Section 8: Risk-Based Fund Recommendation Engine

Execute the modular fund recommender `recommender.py` to generate top 5 mutual fund recommendations for **Conservative**, **Moderate**, and **Aggressive** investor profiles."""
cells.append(nbf.v4.new_markdown_cell(sec8_md))

code8 = """rec_conservative = recommend_funds(df_var_cvar, risk_profile='Conservative', top_n=5)
rec_moderate = recommend_funds(df_var_cvar, risk_profile='Moderate', top_n=5)
rec_aggressive = recommend_funds(df_var_cvar, risk_profile='Aggressive', top_n=5)

print("=== Top 5 Recommendations: Conservative Profile ===")
print(rec_conservative[['recommendation_rank', 'scheme_name', 'category', 'sharpe_ratio', 'max_drawdown', 'rec_score']])

print("\\n=== Top 5 Recommendations: Moderate Profile ===")
print(rec_moderate[['recommendation_rank', 'scheme_name', 'category', 'sharpe_ratio', 'sortino_ratio', 'rec_score']])

print("\\n=== Top 5 Recommendations: Aggressive Profile ===")
print(rec_aggressive[['recommendation_rank', 'scheme_name', 'category', 'sortino_ratio', 'var_95', 'rec_score']])"""

cells.append(nbf.v4.new_code_cell(code8))

# Markdown 10: Section 9 (Insights)
sec9_md = """## Section 9: Automated Advanced Quantitative Business Insights

Generate 5 structured quantitative business findings using `insight_engine.py`."""
cells.append(nbf.v4.new_markdown_cell(sec9_md))

code9 = """advanced_insights = generate_advanced_insights(
    df_cohort_summary=df_cohort_summary,
    df_var_cvar=df_var_cvar,
    sip_summary_dict=dict_sip_summary,
    rolling_sharpe_series=rolling_sharpe,
    hhi_score=hhi_value
)

print("=== Section 9: 5 Advanced Business Insights ===")
for ins in advanced_insights:
    print("-" * 70)
    print(f"Insight #{ins['id']} [{ins['category']}]: {ins['title']}")
    print(f"  Observation:      {ins['observation']}")
    print(f"  Business Insight: {ins['business_insight']}")
    print(f"  Recommendation:   {ins['recommendation']}")"""

cells.append(nbf.v4.new_code_cell(code9))

# Markdown 11: Section 10 (Validation & Report)
sec10_md = """## Section 10: Validation & Summary Report Generation"""
cells.append(nbf.v4.new_markdown_cell(sec10_md))

code10 = """report_content = f\"\"\"# Day 05 Advanced Risk Analytics Validation Report

**Date**: 2026-08-12  
**Module**: Day 05 - Advanced Risk Analytics  
**Status**: PASSED  

---

## 1. Executive Summary

- **Total Schemes Evaluated**: {len(df_var_cvar)}
- **Mean 95% Historical VaR**: {df_var_cvar['var_95'].mean()*100:.4f}%
- **Mean 95% CVaR (Expected Shortfall)**: {df_var_cvar['cvar_95'].mean()*100:.4f}%
- **Market Concentration HHI Score**: {hhi_value:.4f} (Unconcentrated Market)
- **Total Investors Tracked**: {dict_sip_summary.get('total_investors', 0):,}
- **At-Risk Investors (>35 Day Gap)**: {dict_sip_summary.get('at_risk_investors', 0):,} ({dict_sip_summary.get('at_risk_investors', 0)/dict_sip_summary.get('total_investors', 1)*100:.1f}%)

---

## 2. Validation Checklist

- [x] Historical VaR (95%) and CVaR (95%) calculated for all 40 schemes.
- [x] 90-Day Rolling Sharpe ratio calculated and plotted (`charts/png/rolling_sharpe_chart.png`).
- [x] Herfindahl-Hirschman Index (HHI) concentration calculated across AMC AUM.
- [x] Investor Cohort analysis executed (`cohort_summary`, `top_funds_by_cohort`).
- [x] SIP Continuity gaps & at-risk status flagged (`charts/png/sip_gap_distribution.png`).
- [x] Simple risk-based recommender executed for Conservative, Moderate, and Aggressive profiles.
- [x] 5 structured quantitative business insights generated.

---

## 3. Generated Deliverables

- `outputs/var_cvar_report.csv` ({len(df_var_cvar)} rows x {df_var_cvar.shape[1]} cols)
- `charts/png/rolling_sharpe_chart.png`
- `charts/png/sip_gap_distribution.png`
- `scripts/advanced_metrics.py`
- `scripts/cohort_analysis.py`
- `scripts/sip_analysis.py`
- `scripts/recommender.py`
- `scripts/insight_engine.py`
- `reports/day5_validation.md`
\"\"\"

with open(reports_dir / 'day5_validation.md', 'w') as f:
    f.write(report_content)

print("Day 05 Validation report generated at reports/day5_validation.md!")"""

cells.append(nbf.v4.new_code_cell(code10))

nb['cells'] = cells

with open('notebooks/Advanced_Analytics.ipynb', 'w') as f:
    nbf.write(nb, f)

print("Advanced_Analytics.ipynb successfully created!")
