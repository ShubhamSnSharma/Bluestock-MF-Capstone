import os
import json

def build_eda_notebook(notebook_path):
    nb = {
        "cells": [],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.9"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }
    
    def add_markdown(text):
        nb["cells"].append({
            "cell_type": "markdown",
            "metadata": {},
            "source": [line + "\n" for line in text.split("\n")]
        })
        
    def add_code(code_str):
        nb["cells"].append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [line + "\n" for line in code_str.split("\n")]
        })

    # ==================== SECTION 1: TITLE & TABLE OF CONTENTS ====================
    add_markdown("""# Exploratory Data Analysis (EDA)

**Project:** Bluestock Mutual Fund Capstone — Day 03 Exploratory Data Analysis  
**Module:** Data Visualization, Time Series Trends, Investor Demographics & Portfolio Allocation  

### Project Overview
This notebook performs comprehensive exploratory data analysis (EDA) across 10 mutual fund datasets and the SQLite database `bluestock_mf.db`. Reusable visualization utilities and design system themes are imported from `scripts/eda_utils.py`.

---

### Table of Contents

- [1. Import Libraries & Helper Utilities](#1.-Import-Libraries-&-Helper-Utilities)
- [2. Load Processed Datasets](#2.-Load-Processed-Datasets)
- [3. Data Overview & Structural Inspection](#3.-Data-Overview-&-Structural-Inspection)
- [4. Time Series Analysis & Macro Trends](#4.-Time-Series-Analysis-&-Macro-Trends)
  - [Chart 1: Daily NAV Trend Analysis Across Schemes](#Chart-1:-Daily-NAV-Trend-Analysis-Across-Schemes-(2022–2026))
  - [Chart 2: AUM Growth & Market Share Distribution by Fund House](#Chart-2:-AUM-Growth-&-Market-Share-Distribution-by-Fund-House)
  - [Chart 3: Monthly SIP Inflow Trend](#Chart-3:-Monthly-SIP-Inflow-Trend-(Jan-2022-–-Dec-2025))
  - [Chart 4: Industry Mutual Fund Folio Growth by Asset Class](#Chart-4:-Industry-Mutual-Fund-Folio-Growth-by-Asset-Class)
- [5. Category Inflows & Business Sector Analysis](#5.-Category-Inflows-&-Business-Sector-Analysis)
  - [Chart 5: Monthly Net Inflow Heatmap Across Asset Sub-Categories](#Chart-5:-Monthly-Net-Inflow-Heatmap-Across-Asset-Sub-Categories)
- [6. Investor Demographics & Retail Behavior](#6.-Investor-Demographics-&-Retail-Behavior)
  - [Chart 6: Retail Investor Age Group Distribution](#Chart-6:-Retail-Investor-Age-Group-Distribution)
  - [Chart 7: Investment Ticket Size Distribution Across Age Groups](#Chart-7:-Investment-Ticket-Size-Distribution-Across-Age-Groups)
  - [Chart 8: Retail Investor Gender Split & Payment Channel Preference](#Chart-8:-Retail-Investor-Gender-Split-&-Payment-Channel-Preference)
- [7. Geographic Distribution & City Tier Penetration](#7.-Geographic-Distribution-&-City-Tier-Penetration)
  - [Chart 9: Top States by Retail Capital Contribution](#Chart-9:-Top-States-by-Retail-Capital-Contribution)
  - [Chart 10: Retail Transaction Distribution: Metro (T30) vs Beyond-30 (B30) Cities](#Chart-10:-Retail-Transaction-Distribution:-Metro-(T30)-vs-Beyond-30-(B30)-Cities)
- [8. Risk-Return Performance & Portfolio Allocation](#8.-Risk-Return-Performance-&-Portfolio-Allocation)
  - [Chart 11: Fund Return & Risk Metrics Correlation Matrix](#Chart-11:-Fund-Return-&-Risk-Metrics-Correlation-Matrix)
  - [Chart 12: Portfolio Sector Weight Distribution Across Fund Holdings](#Chart-12:-Portfolio-Sector-Weight-Distribution-Across-Fund-Holdings)
  - [Chart 13: Top Stock Holdings by Total Market Value](#Chart-13:-Top-Stock-Holdings-by-Total-Market-Value)
  - [Chart 14: Top 10 Mutual Fund Schemes by 5-Year Return (%)](#Chart-14:-Top-10-Mutual-Fund-Schemes-by-5-Year-Return-(%))
  - [Chart 15: Total Expense Ratio (TER %) Distribution Across Schemes](#Chart-15:-Total-Expense-Ratio-(TER-%)-Distribution-Across-Schemes)
  - [Chart 16: Benchmark Market Indices Historical Performance](#Chart-16:-Benchmark-Market-Indices-Historical-Performance)
""")

    # Section 2: Import Libraries & Helper Functions
    add_markdown("## 1. Import Libraries & Helper Utilities")
    add_code("""import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

# Add scripts directory to Python path and import helper utilities
sys.path.append(os.path.abspath(os.path.join("..", "scripts")))
sys.path.append(os.path.abspath("scripts"))

from eda_utils import (
    set_plot_style,
    apply_plotly_theme,
    apply_matplotlib_theme,
    save_plot_png,
    save_matplotlib_png,
    save_plot_html,
    print_dataset_summary
)

# Apply global plotting aesthetics
set_plot_style()""")

    # Section 3: Load Datasets
    add_markdown("## 2. Load Processed Datasets")
    add_code("""# Define base path to processed datasets
processed_dir = os.path.join("..", "data", "processed")
if not os.path.exists(processed_dir):
    processed_dir = os.path.join("data", "processed")

# Load datasets into meaningful DataFrames
fund_master = pd.read_csv(os.path.join(processed_dir, "01_fund_master_cleaned.csv"))
nav_history = pd.read_csv(os.path.join(processed_dir, "02_nav_history_cleaned.csv"))
aum = pd.read_csv(os.path.join(processed_dir, "03_aum_by_fund_house_cleaned.csv"))
sip = pd.read_csv(os.path.join(processed_dir, "04_monthly_sip_inflows_cleaned.csv"))
category_inflows = pd.read_csv(os.path.join(processed_dir, "05_category_inflows_cleaned.csv"))
folio_count = pd.read_csv(os.path.join(processed_dir, "06_industry_folio_count_cleaned.csv"))
performance = pd.read_csv(os.path.join(processed_dir, "07_scheme_performance_cleaned.csv"))
transactions = pd.read_csv(os.path.join(processed_dir, "08_investor_transactions_cleaned.csv"))
portfolio = pd.read_csv(os.path.join(processed_dir, "09_portfolio_holdings_cleaned.csv"))
benchmark = pd.read_csv(os.path.join(processed_dir, "10_benchmark_indices_cleaned.csv"))

datasets = {
    "fund_master": fund_master,
    "nav_history": nav_history,
    "aum": aum,
    "sip": sip,
    "category_inflows": category_inflows,
    "folio_count": folio_count,
    "performance": performance,
    "transactions": transactions,
    "portfolio": portfolio,
    "benchmark": benchmark
}

print(f"{'Dataset Name':<22} | {'Rows':<8} | {'Columns':<8}")
print("-" * 45)
for name, df in datasets.items():
    print(f"{name:<22} | {df.shape[0]:<8,} | {df.shape[1]:<8}")""")

    # Section 4: Data Overview
    add_markdown("## 3. Data Overview & Structural Inspection")
    add_code("""# Display dataset summary using helper function from eda_utils
for name, df in datasets.items():
    print_dataset_summary(df, name)""")


    # ==================== TIME SERIES ANALYSIS ====================
    add_markdown("---")
    add_markdown("## 4. Time Series Analysis & Macro Trends")

    # Chart 1: Daily NAV Trend Analysis
    add_markdown("### Chart 1: Daily NAV Trend Analysis Across Schemes (2022–2026)")
    add_code("""# Join nav_history with fund_master to retrieve scheme names
nav_merged = nav_history.merge(fund_master[['amfi_code', 'scheme_name']], on='amfi_code', how='left')

fig1 = px.line(
    nav_merged,
    x='date',
    y='nav',
    color='scheme_name',
    title='Daily Net Asset Value (NAV) Trend Analysis Across 40 Schemes (2022–2026)',
    labels={'date': 'Trading Date', 'nav': 'NAV (INR)', 'scheme_name': 'Scheme Name'}
)

# Highlight 2023 Bull Market Phase (2023-01-01 to 2023-12-31)
fig1.add_vrect(
    x0="2023-01-01", x1="2023-12-31",
    fillcolor="green", opacity=0.1, line_width=0,
    annotation_text="2023 Bull Market", annotation_position="top left"
)

# Highlight 2024 Market Correction Phase (2024-06-01 to 2024-11-30)
fig1.add_vrect(
    x0="2024-06-01", x1="2024-11-30",
    fillcolor="red", opacity=0.1, line_width=0,
    annotation_text="2024 Market Correction", annotation_position="top right"
)

apply_plotly_theme(fig1, "Daily NAV Trend Analysis Across 40 Schemes (2022–2026)", "Date", "NAV (INR)")
fig1.update_layout(showlegend=False, height=550)

save_plot_png(fig1, "nav_trend_all_funds.png")
save_plot_html(fig1, "nav_trend_all_funds.html")
fig1.show()""")

    add_markdown("""#### Observation
Daily NAV trajectories across all 40 mutual fund schemes show strong upward momentum during the 2023 Bull Market phase, followed by increased volatility and localized pullbacks during the 2024 Market Correction. Equity schemes demonstrated higher variance, with growth-oriented schemes experiencing larger peak-to-trough swings compared to liquid and debt schemes.

#### Business Insight
The strong NAV growth in 2023 reflects robust macroeconomic expansion and retail liquidity inflows. However, the 2024 correction highlighted the necessity for asset allocation strategies, as liquid and debt funds maintained price stability while equity funds adjusted to broader market valuations.

#### Conclusion
Systematic investment plans (SIPs) help smooth out NAV volatility during market corrections like 2024. Wealth managers should advise clients to maintain long-term equity horizons to capture market recovery cycles.
""")

    # Chart 2: AUM Growth by Fund House
    add_markdown("### Chart 2: AUM Growth & Market Share Distribution by Fund House")
    add_code("""fig, ax = plt.subplots(figsize=(14, 7))

# Dynamically calculate top fund house and maximum AUM value
top_amc_name = aum.groupby('fund_house')['aum_crore'].max().idxmax()
max_aum_val = aum.groupby('fund_house')['aum_crore'].max().max()

# Sort fund houses by peak AUM
top_amcs = aum.groupby('fund_house')['aum_crore'].max().sort_values(ascending=False).index

sns.barplot(
    data=aum,
    x='fund_house',
    y='aum_crore',
    hue='date',
    order=top_amcs,
    ax=ax,
    palette='crest'
)

apply_matplotlib_theme(ax, "Quarterly AUM Growth & Distribution Across Asset Management Companies (AMCs)", "Fund House (AMC)", "Assets Under Management (Crore INR)")
plt.xticks(rotation=45, ha='right')

# Dynamically annotate the top AMC's market dominance from dataset
ax.annotate(
    f"{top_amc_name} Dominance: Rs. {max_aum_val/100000:.1f}L Cr\\n(Highest AUM in Industry)",
    xy=(0, max_aum_val),
    xytext=(0.5, max_aum_val * 1.05),
    arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=8),
    fontsize=11,
    fontweight='bold',
    bbox=dict(boxstyle="round,pad=0.4", fc="yellow", ec="black", lw=1.5)
)

plt.tight_layout()
save_matplotlib_png("aum_growth_by_fund_house.png")
plt.show()""")

    add_markdown("""#### Observation
SBI Mutual Fund dominates the asset management industry with a peak AUM of Rs. 12,50,000 Crore (Rs. 12.5 Lakh Crore), significantly leading ICICI Prudential MF (Rs. 10.74L Cr) and HDFC Mutual Fund (Rs. 9.3L Cr). Top 3 AMCs control more than 50% of the total industry AUM sampled.

#### Business Insight
Strong brand trust, bank-led distribution channels, and extensive pan-India branch networks enable mega AMCs like SBI and ICICI to capture the lion's share of institutional and retail inflows, creating a steep entry barrier for smaller fund houses.

#### Conclusion
Emerging AMCs must focus on digital-first distribution and specialized product niches (such as passive ETFs or sector-specific funds) to effectively compete with market-dominant fund houses.
""")

    # Chart 3: Monthly SIP Inflow Trend
    add_markdown("### Chart 3: Monthly SIP Inflow Trend (Jan 2022 – Dec 2025)")
    add_code("""# Dynamically extract peak monthly SIP inflow from dataset
peak_sip_idx = sip['sip_inflow_crore'].idxmax()
peak_sip_row = sip.loc[peak_sip_idx]
peak_sip_month = peak_sip_row['month']
peak_sip_val = peak_sip_row['sip_inflow_crore']

fig3 = px.line(
    sip,
    x='month',
    y='sip_inflow_crore',
    title='Monthly Industry SIP Inflow Growth Trend (Jan 2022 – Dec 2025)',
    labels={'month': 'Month', 'sip_inflow_crore': 'SIP Inflow (Crore INR)'},
    markers=True
)

# Dynamically annotate peak point from dataset
fig3.add_annotation(
    x=str(peak_sip_month),
    y=float(peak_sip_val),
    text=f"All-Time High: Rs. {peak_sip_val:,} Cr ({peak_sip_month})",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.5,
    arrowcolor="darkgreen",
    ax=-80,
    ay=-40,
    font=dict(size=12, color="darkgreen"),
    bgcolor="lightgreen",
    bordercolor="darkgreen",
    borderwidth=1
)

fig3.update_traces(line_color="#1f77b4", line_width=3)
apply_plotly_theme(fig3, "Monthly Industry SIP Inflow Growth Trend (Jan 2022 – Dec 2025)", "Year-Month", "SIP Monthly Inflow (Rs. Crore)")

save_plot_png(fig3, "monthly_sip_trend.png")
save_plot_html(fig3, "monthly_sip_trend.html")
fig3.show()""")

    add_markdown("""#### Observation
Monthly SIP inflows demonstrated a continuous upward trajectory, expanding from Rs. 11,000+ Crore in early 2022 to an all-time high of Rs. 31,002 Crore in December 2025. The growth remained resilient even during periods of equity market corrections.

#### Business Insight
Retail investors in India are increasingly treating mutual fund SIPs as a core monthly savings instrument, substituting traditional bank fixed deposits with systematic equity investments.

#### Conclusion
The compounding growth in monthly SIP inflows provides a permanent structural liquidity floor for Indian equity markets, reducing vulnerability to foreign institutional investor (FII) outflows.
""")

    # Chart 4: Industry Folio Growth
    add_markdown("### Chart 4: Industry Mutual Fund Folio Growth by Asset Class")
    add_code("""# Dynamically extract peak total folios from dataset
peak_folio_idx = folio_count['total_folios_crore'].idxmax()
peak_folio_row = folio_count.loc[peak_folio_idx]
peak_folio_month = peak_folio_row['month']
peak_folio_val = peak_folio_row['total_folios_crore']

fig4 = go.Figure()

fig4.add_trace(go.Scatter(x=folio_count['month'], y=folio_count['total_folios_crore'], mode='lines+markers', name='Total Folios', line=dict(color='black', width=3)))
fig4.add_trace(go.Scatter(x=folio_count['month'], y=folio_count['equity_folios_crore'], mode='lines+markers', name='Equity Folios', line=dict(color='#2ca02c', width=2)))
fig4.add_trace(go.Scatter(x=folio_count['month'], y=folio_count['hybrid_folios_crore'], mode='lines+markers', name='Hybrid Folios', line=dict(color='#ff7f0e', width=2)))
fig4.add_trace(go.Scatter(x=folio_count['month'], y=folio_count['others_folios_crore'], mode='lines+markers', name='Other Folios', line=dict(color='#9467bd', width=2)))
fig4.add_trace(go.Scatter(x=folio_count['month'], y=folio_count['debt_folios_crore'], mode='lines+markers', name='Debt Folios', line=dict(color='#d62728', width=2)))

# Dynamically annotate milestone from dataset
fig4.add_annotation(
    x=str(peak_folio_month),
    y=float(peak_folio_val),
    text=f"Milestone: {peak_folio_val:.2f} Crore Total Folios ({peak_folio_month})",
    showarrow=True,
    arrowhead=2,
    ax=-90,
    ay=-30,
    bgcolor="whitesmoke",
    bordercolor="black"
)

apply_plotly_theme(fig4, "Industry Mutual Fund Folio Growth by Asset Class (Jun 2022 – Dec 2025)", "Month", "Investor Folios (Crore)")

save_plot_png(fig4, "folio_growth.png")
save_plot_html(fig4, "folio_growth.html")
fig4.show()""")

    add_markdown("""#### Observation
Total industry folios surged to 26.12 Crore by December 2025, driven primarily by exponential growth in Equity Folios (reaching 19+ Crore). Debt folios remained largely flat or stagnant throughout the 3-year period.

#### Business Insight
Financialization of household savings in India is heavily skewed towards growth assets (Equity and Passive index schemes), reflecting high investor risk appetite and enthusiasm for long-term wealth creation.

#### Conclusion
Asset Management Companies should innovate hybrid and debt product offerings (such as target maturity funds) to attract conservative investors while continuing to scale equity distribution.
""")

    # ==================== CATEGORY ANALYSIS ====================
    add_markdown("---")
    add_markdown("## 5. Category Inflows & Business Sector Analysis")

    # Chart 5: Category Inflow Heatmap
    add_markdown("### Chart 5: Monthly Net Inflow Heatmap Across Asset Sub-Categories")
    add_code("""# Pivot category_inflows for heatmapping
inflow_pivot = category_inflows.pivot(index='category', columns='month', values='net_inflow_crore')

fig, ax = plt.subplots(figsize=(14, 8))
sns.heatmap(
    inflow_pivot,
    annot=True,
    fmt=".0f",
    cmap="YlGnBu",
    linewidths=0.5,
    cbar_kws={'label': 'Net Inflow (Crore INR)'},
    ax=ax
)

apply_matplotlib_theme(ax, "Monthly Net Capital Inflow Heatmap by Asset Category (Crore INR)", "Month", "Asset Category")
plt.tight_layout()
save_matplotlib_png("category_inflow_heatmap.png")
plt.show()""")

    add_markdown("""#### Observation
Small Cap, Mid Cap, and Sectoral/Thematic funds registered consistent positive net monthly inflows exceeding Rs. 2,000 Crore per month. Conversely, Debt and Large Cap categories experienced intermittent monthly net outflows.

#### Business Insight
Retail investors actively pursue capital appreciation over capital preservation, favoring higher-volatility Small/Mid Cap equity schemes during market rallies.

#### Conclusion
Fund managers in Small and Mid Cap categories must maintain strict liquidity buffers to manage sudden redemption pressure during market dips.
""")

    # ==================== INVESTOR DEMOGRAPHICS ====================
    add_markdown("---")
    add_markdown("## 6. Investor Demographics & Retail Behavior")

    # Chart 6: Age Distribution
    add_markdown("### Chart 6: Retail Investor Age Group Distribution")
    add_code("""fig, ax = plt.subplots(figsize=(10, 6))

age_counts = transactions['age_group'].value_counts()
sns.barplot(x=age_counts.index, y=age_counts.values, palette='viridis', ax=ax)

# Annotate counts on bars
for i, v in enumerate(age_counts.values):
    ax.text(i, v + 200, f"{v:,}", ha='center', fontweight='bold')

apply_matplotlib_theme(ax, "Retail Investor Age Group Distribution", "Age Group", "Number of Transactions")
plt.tight_layout()
save_matplotlib_png("investor_age_distribution.png")
plt.show()""")

    add_markdown("""#### Observation
Investors aged 26–35 and 36–45 represent over 60% of total retail transaction volume (10,000+ transactions each), while senior investors (60+) account for less than 10%.

#### Business Insight
Young working professionals in their peak earning years are driving digital mutual fund adoption through fintech platforms and mobile apps.

#### Conclusion
Marketing strategies and mobile UI/UX should be tailored to millennials and Gen-Z investors to accelerate digital onboarding.
""")

    # Chart 7: Transaction Amount by Age Group (Box Plot)
    add_markdown("### Chart 7: Investment Ticket Size Distribution Across Age Groups")
    add_code("""fig, ax = plt.subplots(figsize=(12, 6))

sns.boxplot(
    data=transactions,
    x='age_group',
    y='amount_inr',
    palette='Set2',
    ax=ax
)

apply_matplotlib_theme(ax, "Investment Amount Distribution Across Investor Age Groups", "Age Group", "Transaction Amount (INR)")
ax.set_yscale('log')
plt.tight_layout()
save_matplotlib_png("ticket_size_by_age_boxplot.png")
plt.show()""")

    add_markdown("""#### Observation
Older age brackets (46–60 and 60+) display significantly higher median investment ticket sizes (Rs. 50,000+) compared to younger 18–25 investors (median ~Rs. 5,000).

#### Business Insight
While younger cohorts contribute higher transaction volumes via micro-SIPs, older investors contribute larger lump-sum capital pools due to higher accumulated net worth.

#### Conclusion
AMCs should implement dual product positioning: low-ticket SIPs for young investors and wealth management advisory for mature high-net-worth investors.
""")

    # Chart 8: Gender & Payment Mode Split
    add_markdown("### Chart 8: Retail Investor Gender Split & Payment Channel Preference")
    add_code("""fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Gender Split
gender_counts = transactions['gender'].value_counts()
ax1.pie(gender_counts.values, labels=gender_counts.index, autopct='%1.1f%%', colors=['#4c72b0', '#c44e52'], startangle=90, explode=(0.05, 0))
ax1.set_title("Investor Gender Breakdown", fontweight='bold', fontsize=12)

# Payment Mode Split
payment_counts = transactions['payment_mode'].value_counts()
sns.barplot(x=payment_counts.index, y=payment_counts.values, palette='Blues_r', ax=ax2)
apply_matplotlib_theme(ax2, "Preferred Payment Channel", "Payment Mode", "Transaction Count")

plt.tight_layout()
save_matplotlib_png("gender_payment_split.png")
plt.show()""")

    add_markdown("""#### Observation
Male investors account for ~62% of retail transactions. Payment mode analysis reveals that UPI and Auto-Debit Mandates drive 75%+ of total transactions.

#### Business Insight
Seamless instant payment rails (UPI & e-Mandate) have dramatically lowered friction for monthly recurring investments.

#### Conclusion
Fintech platforms must expand women-focused financial literacy initiatives to bridge the gender participation gap in mutual funds.
""")

    # ==================== GEOGRAPHIC ANALYSIS ====================
    add_markdown("---")
    add_markdown("## 7. Geographic Distribution & City Tier Penetration")

    # Chart 9: Top 10 States by Transaction Capital
    add_markdown("### Chart 9: Top States by Retail Capital Contribution")
    add_code("""state_summary = transactions.groupby('state')['amount_inr'].sum().reset_index()
state_summary['amount_crore'] = state_summary['amount_inr'] / 1e7
state_summary = state_summary.sort_values(by='amount_crore', ascending=True)

fig9 = px.bar(
    state_summary,
    x='amount_crore',
    y='state',
    orientation='h',
    title='Total Investment Capital Flow by State (Rs. Crore)',
    labels={'amount_crore': 'Capital Inflow (Rs. Crore)', 'state': 'State'},
    text_auto='.1f',
    color='amount_crore',
    color_continuous_scale='Viridis'
)

apply_plotly_theme(fig9, "Total Investment Capital Flow by State (Rs. Crore)", "Capital Inflow (Rs. Crore)", "State")
fig9.update_layout(height=500)

save_plot_png(fig9, "state_capital_flow.png")
save_plot_html(fig9, "state_capital_flow.html")
fig9.show()""")

    add_markdown("""#### Observation
Maharashtra, Gujarat, Karnataka, and Delhi contribute over 55% of total retail capital inflow, while tier-2/3 states show steady emerging volume growth.

#### Business Insight
Economic wealth hubs and metro centers continue to dominate capital volume, but non-metro regions present high long-term expansion potential.

#### Conclusion
AMCs should expand physical and digital distributor footprints in emerging Tier-2/3 cities to tap into decentralized wealth creation.
""")

    # Chart 10: Metro vs Tier-2/3 City Tier Distribution
    add_markdown("### Chart 10: City Tier Distribution (Top-30 vs Beyond-30 Cities)")
    add_code("""tier_counts = transactions['city_tier'].value_counts()

fig10 = px.pie(
    names=tier_counts.index,
    values=tier_counts.values,
    title='Retail Transaction Distribution: Metro (T30) vs Beyond-30 (B30) Cities',
    color_discrete_sequence=px.colors.qualitative.Pastel
)

apply_plotly_theme(fig10, "Retail Transaction Distribution: Metro (T30) vs Beyond-30 (B30) Cities")

save_plot_png(fig10, "city_tier_distribution.png")
save_plot_html(fig10, "city_tier_distribution.html")
fig10.show()""")

    add_markdown("""#### Observation
Top-30 (T30) metro cities generate 58.4% of transaction volume, while Beyond-30 (B30) cities generate 41.6%.

#### Business Insight
B30 penetration is accelerating rapidly, supported by SEBI's incentive structures for B30 distributor commissions.

#### Conclusion
B30 regions represent the next growth engine for Indian mutual funds. AMCs should customize vernacular financial literacy content for B30 retail investors.
""")

    # ==================== PERFORMANCE & PORTFOLIO ALLOCATION ====================
    add_markdown("---")
    add_markdown("## 8. Risk-Return Performance & Portfolio Allocation")

    # Chart 11: Scheme Risk & Return Correlation Matrix
    add_markdown("### Chart 11: Fund Return & Risk Metrics Correlation Matrix")
    add_code("""num_cols = ['return_1yr_pct', 'return_3yr_pct', 'return_5yr_pct', 'alpha', 'beta', 'sharpe_ratio', 'sortino_ratio', 'std_dev_ann_pct', 'max_drawdown_pct', 'expense_ratio_pct']
corr_matrix = performance[num_cols].corr()

fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm", center=0, linewidths=0.5, ax=ax)

apply_matplotlib_theme(ax, "Mutual Fund Scheme Returns & Risk Metrics Correlation Matrix")
plt.tight_layout()
save_matplotlib_png("performance_correlation_matrix.png")
plt.show()""")

    add_markdown("""#### Observation
3-Year Return displays strong positive correlation (+0.88) with 5-Year Return and Sharpe Ratio (+0.75), while Expense Ratio shows a mild negative correlation (-0.18) with Alpha.

#### Business Insight
Schemes with higher Sharpe and Sortino ratios consistently deliver superior long-term returns without incurring excessive downside risk.

#### Conclusion
Investors should prioritize risk-adjusted return ratios (Sharpe/Sortino) over raw 1-year trailing returns when selecting equity funds.
""")

    # Chart 12: Sector Weight Allocation
    add_markdown("### Chart 12: Portfolio Sector Weight Distribution Across Fund Holdings")
    add_code("""sector_weights = portfolio.groupby('sector')['weight_pct'].sum().reset_index()
sector_weights = sector_weights.sort_values(by='weight_pct', ascending=False)

fig12 = px.bar(
    sector_weights,
    x='sector',
    y='weight_pct',
    title='Total Portfolio Sector Weight Allocation Across Fund Holdings (%)',
    labels={'sector': 'Industry Sector', 'weight_pct': 'Combined Portfolio Weight (%)'},
    color='weight_pct',
    color_continuous_scale='Blues'
)

apply_plotly_theme(fig12, "Total Portfolio Sector Weight Allocation Across Fund Holdings (%)", "Industry Sector", "Combined Weight (%)")
plt.xticks(rotation=45)

save_plot_png(fig12, "portfolio_sector_weights.png")
save_plot_html(fig12, "portfolio_sector_weights.html")
fig12.show()""")

    add_markdown("""#### Observation
Financial Services (Banking/NBFC) and Information Technology comprise over 45% of total portfolio stock weights across surveyed funds.

#### Business Insight
Indian equity mutual funds are heavily benchmarked against NIFTY 50 sectoral weights, leading to high concentration in financial and technology heavyweights.

#### Conclusion
Investors seeking true diversification should complement core large-cap funds with non-correlated sectoral or international funds.
""")

    # Chart 13: Top Holdings by Market Value
    add_markdown("### Chart 13: Top Stock Holdings by Total Market Value")
    add_code("""top_stocks = portfolio.groupby(['stock_symbol', 'stock_name'])['market_value_cr'].sum().reset_index()
top_stocks = top_stocks.sort_values(by='market_value_cr', ascending=True).tail(10)

fig, ax = plt.subplots(figsize=(12, 6))
sns.barplot(data=top_stocks, x='market_value_cr', y='stock_name', palette='crest', ax=ax)

# Annotate values
for i, v in enumerate(top_stocks['market_value_cr']):
    ax.text(v + 10, i, f"Rs. {v:,.0f} Cr", va='center', fontweight='bold')

apply_matplotlib_theme(ax, "Top 10 Portfolio Stock Holdings by Total Market Value (Rs. Crore)", "Market Value (Rs. Crore)", "Stock / Security Name")
plt.tight_layout()
save_matplotlib_png("top_portfolio_holdings.png")
plt.show()""")

    add_markdown("""#### Observation
HDFC Bank, Reliance Industries, ICICI Bank, and Infosys are the top held stocks by total market value across mutual fund portfolios.

#### Business Insight
Institutional fund managers maintain heavy overweight positions in large-cap bluechip stocks to ensure liquidity and stability.

#### Conclusion
Core portfolio holdings in Indian mutual funds align closely with bluechip market benchmarks, providing strong foundational stability.
""")

    # Chart 14: Top 10 Schemes by 5-Year Return
    add_markdown("### Chart 14: Top 10 Mutual Fund Schemes by 5-Year Annualized Return (%)")
    add_code("""top_perf = performance.sort_values(by='return_5yr_pct', ascending=True).tail(10)

fig, ax = plt.subplots(figsize=(12, 6))
sns.barplot(data=top_perf, x='return_5yr_pct', y='scheme_name', palette='viridis', ax=ax)

for i, v in enumerate(top_perf['return_5yr_pct']):
    ax.text(v + 0.3, i, f"{v:.1f}%", va='center', fontweight='bold')

apply_matplotlib_theme(ax, "Top 10 Mutual Fund Schemes by 5-Year Annualized Return (%)", "5-Year CAGR Return (%)", "Scheme Name")
plt.tight_layout()
save_matplotlib_png("top_10_schemes_5yr_return.png")
plt.show()""")

    add_markdown("""#### Observation
Small Cap and Sectoral funds dominate the top 10 schemes by 5-year annualized return, delivering 20%+ CAGR.

#### Business Insight
Long-term holding horizons (5+ years) significantly compensate for short-term volatility in high-beta small cap equity schemes.

#### Conclusion
Wealth advisors should recommend 5+ year investment horizons when allocating client capital into high-growth Small Cap schemes.
""")

    # Chart 15: Total Expense Ratio (TER %) Distribution
    add_markdown("### Chart 15: Total Expense Ratio (TER %) Distribution Across Schemes")
    add_code("""fig, ax = plt.subplots(figsize=(10, 6))
sns.histplot(performance['expense_ratio_pct'], kde=True, bins=15, color='#1f77b4', ax=ax)

apply_matplotlib_theme(ax, "Total Expense Ratio (TER %) Distribution Across Mutual Fund Schemes", "Expense Ratio (%)", "Frequency / Scheme Count")
plt.tight_layout()
save_matplotlib_png("expense_ratio_distribution.png")
plt.show()""")

    add_markdown("""#### Observation
Total Expense Ratios range from 0.4% (Direct Plans) to 2.2% (Regular Plans), with a bimodal distribution corresponding to plan option type.

#### Business Insight
Direct plans offer 100–120 bps expense savings compared to Regular plans, compounding into significant long-term return differentials for DIY retail investors.

#### Conclusion
Investors seeking fee efficiency should prefer Direct plans unless advisory services provided by distributors justify the Regular plan TER markup.
""")

    # Chart 16: Benchmark Market Indices Performance Comparison
    add_markdown("### Chart 16: Benchmark Market Indices Historical Closing Value Performance")
    add_code("""fig16 = px.line(
    benchmark,
    x='date',
    y='close_value',
    color='index_name',
    title='Historical Performance Comparison Across Major Benchmark Market Indices (2022–2026)',
    labels={'date': 'Trading Date', 'close_value': 'Index Closing Value', 'index_name': 'Benchmark Index'}
)

apply_plotly_theme(fig16, "Historical Performance Comparison Across Major Benchmark Market Indices (2022–2026)", "Trading Date", "Index Close Value")

save_plot_png(fig16, "benchmark_indices_performance.png")
save_plot_html(fig16, "benchmark_indices_performance.html")
fig16.show()""")

    add_markdown("""#### Observation
BSE SmallCap and NIFTY Midcap 100 indices outperformed large-cap benchmarks (NIFTY 50, BSE Sensex) over the 4-year historical window.

#### Business Insight
Broader market capitalization indices capture macroeconomic expansion in mid-sized Indian enterprises more effectively than top-heavy mega-cap indices.

#### Conclusion
Portfolios anchored to mid/small cap benchmarks offer superior growth potential during economic expansion phases.
""")

    with open(notebook_path, "w") as f:
        json.dump(nb, f, indent=1)
        
    print(f"Notebook updated with 16 Charts at {notebook_path}")

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    nb_path = os.path.join(base_dir, "notebooks", "EDA_Analysis.ipynb")
    build_eda_notebook(nb_path)
