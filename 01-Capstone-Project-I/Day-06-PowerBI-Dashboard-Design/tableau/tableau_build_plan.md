# Tableau Dashboard Build & Implementation Plan

This document outlines the visual authoring instructions for building the 4 interactive dashboard pages in Tableau Desktop / Tableau Public.

---

## 1. Global Setup & Canvas Specifications

- **Dashboard Resolution**: Fixed Size, $1920 \times 1080$ pixels (16:9 Widescreen).
- **Color Palette**:
  - Primary Headers / Bars: Navy Blue (`#1E3A8A`)
  - Background / Containers: Light Slate (`#F8FAFC`) with White card backgrounds (`#FFFFFF`)
  - Positive / Returns: Green (`#10B981`)
  - Negative / Risk: Red (`#EF4444`)
  - Neutral / Accent: Amber (`#F59E0B`)
- **Typography**: Segoe UI / Tableau Bold for KPI values (24pt), Tableau Medium for Headers (14pt), Tableau Book for Table text (9.5pt).
- **Rubric Interactive Filter Policy**: Every dashboard page features **at least 2 meaningful interactive filters** that dynamically filter the page visuals.

---

## 2. Page-by-Page Construction Specifications

### PAGE 1: Industry Overview

#### Visual 1: KPI Cards (Top Banner)
- **Source**: `03_aum_by_fund_house_cleaned.csv`, `04_monthly_sip_inflows_cleaned.csv`, `06_industry_folio_count_cleaned.csv`
- **Cards Configuration**:
  1. **Top 10 AMC AUM**: `[Latest Top 10 AMC AUM (Lakh Cr)]` $\rightarrow$ Displays **₹62.74L Cr**  
     *Subtitle / Context: Assignment benchmark: ~₹81L Cr industry-wide*
  2. **Monthly SIP Inflow**: `[Latest Monthly SIP Inflow (Cr)]` $\rightarrow$ Displays **₹31,002 Cr** (Dec 2025 peak)
  3. **Industry Folios**: `[Latest Total Folios (Cr)]` $\rightarrow$ Displays **26.12 Cr** (Dec 2025)
  4. **Top 10 AMC Schemes**: `[Total Schemes (Top 10 AMC)]` $\rightarrow$ Displays **1,522**  
     *Subtitle / Context: Assignment benchmark: 1,908 industry-wide (Portfolio sample: 40)*

#### Visual 2: Industry AUM Trend (2022–2025)
- **Source**: `03_aum_by_fund_house_cleaned.csv`
- **Type**: Area / Line Chart
- **Columns (X-Axis)**: `date` (Continuous Date)
- **Rows (Y-Axis)**: `SUM(aum_lakh_crore)`
- **Marks**: Color `#1E3A8A`, Area opacity 30%, Tooltip with exact Lakh Cr values.

#### Visual 3: AUM by Asset Management Company (AMC)
- **Source**: `03_aum_by_fund_house_cleaned.csv`
- **Type**: Horizontal Bar Chart
- **Rows**: `fund_house` (Sorted descending by AUM)
- **Columns**: `SUM(aum_crore)`
- **Filters**: `date = 2025-12-31` (Latest recording date).
- **Marks**: Color `#1E3A8A`, Label `SUM(aum_crore)` formatted as `₹#,##0 Cr`.

#### Interactive Slicers & Filters (2 Required):
1. **`Date / Year`**: Slider / Dropdown (`2022`, `2023`, `2024`, `2025`) filtering the AUM trend and latest comparison.
2. **`Fund House`**: Multi-select dropdown filtering both the AMC bar chart and the historical AUM trend.

#### Methodology & Coverage Note (Footer Box):
> *"Methodology Note: AUM and Scheme metrics reflect the Top 10 Asset Management Companies (AMCs) available in the project dataset (₹62.74 Lakh Cr AUM across 1,522 schemes), accounting for ~78% of the total Indian mutual fund industry benchmark (~₹81 Lakh Cr across 1,908 schemes)."*

---

### PAGE 2: Fund Performance & Scorecard

#### Visual 1: Return vs. Risk Scatter Plot
- **Source**: `07_scheme_performance_cleaned.csv`
- **Type**: Scatter Plot
- **Columns (X-Axis)**: `[Volatility StdDev (%)]` (`std_dev_ann_pct / 100`)
- **Rows (Y-Axis)**: `[Return 3Y (%)]` (`return_3yr_pct / 100`)
- **Detail**: `scheme_name`
- **Size**: `aum_crore` (Bubble size proportional to scheme AUM)
- **Color**: `category` (Equity, Debt, Hybrid, Solution Oriented)

#### Visual 2: Sortable Fund Performance Scorecard
- **Source**: `07_scheme_performance_cleaned.csv`
- **Type**: Text / Highlight Table
- **Rows**: `scheme_name`, `fund_house`, `category`, `plan`
- **Measures**: `return_1yr_pct`, `return_3yr_pct`, `alpha`, `beta`, `sharpe_ratio`, `sortino_ratio`, `max_drawdown_pct`, `expense_ratio_pct`
- **Sorting**: Interactive sort enabled on all header columns.
- **Interactivity**: Serves as the source sheet for the drill-through action.

#### Visual 3: Historical NAV vs. Benchmark Performance
- **Source**: `02_nav_history_cleaned.csv` + `10_benchmark_indices_cleaned.csv`
- **Type**: Dual-Axis Line Chart
- **Columns**: `date` (Continuous Day/Month)
- **Rows (Dual Axis)**:
  - Axis 1 (Left): `AVG(nav)` (Fund NAV Line)
  - Axis 2 (Right): `AVG(close_value)` (Benchmark Index Price Line for `index_name = 'NIFTY50'`)
- **Interactivity**: Filtered dynamically when a user clicks a scheme in the scorecard.

#### Interactive Slicers & Filters (3 Required):
1. **`Fund House`**: Dropdown filter.
2. **`Category`**: Multi-select checklist filter.
3. **`Plan`**: Radio/List (`Regular` vs `Direct`).

---

### PAGE 3: Investor Analytics

#### Visual 1: Transaction Amount by State (Bar Chart)
- **Source**: `08_investor_transactions_cleaned.csv`
- **Sheet Name**: `P3_Transaction_Amount_by_State_Bar`
- **Type**: Horizontal Bar Chart
- **Rows**: `state` (Sorted descending by `SUM(amount_inr)`)
- **Columns**: `SUM(amount_inr)`
- **Color**: `#1E3A8A`
- **Tooltip**: State Name, Total Investment Amount (₹ Cr), Active Investor Count.

#### Visual 2: Transaction Type Breakdown
- **Source**: `08_investor_transactions_cleaned.csv`
- **Type**: Donut Chart (Pie chart with dual-axis blank circle center)
- **Color Dimension**: `transaction_type` (`SIP`, `Lumpsum`, `Redemption`)
- **Angle / Measure**: `SUM(amount_inr)`
- **Labels**: Transaction Type & `[Transaction Amount Share (%)]`.

#### Visual 3: Age Group vs. Average SIP Amount
- **Source**: `08_investor_transactions_cleaned.csv`
- **Type**: Clustered Column Bar Chart
- **Columns (X-Axis)**: `age_group` (`18-25`, `26-35`, `36-45`, `46-55`, `56+`)
- **Rows (Y-Axis)**: `[Average SIP Amount (INR)]`
- **Filter**: `transaction_type = 'SIP'`
- **Color**: `#10B981` (Green).

#### Visual 4: Monthly Transaction Volume Trend
- **Source**: `08_investor_transactions_cleaned.csv`
- **Type**: Line Chart
- **Columns**: `DATETRUNC('month', transaction_date)`
- **Rows**: `[Transaction Volume]` (`COUNT(investor_id)`)
- **Color**: `#1E3A8A`.

#### Interactive Slicers & Filters (3 Required):
1. **`State`**: Dropdown filter.
2. **`Age Group`**: Multi-select checklist.
3. **`City Tier`**: Radio toggle (`T30` vs `B30`).

---

### PAGE 4: SIP & Market Trends

#### Visual 1: Monthly SIP Inflow vs. NIFTY 50 Month-End Close (2022–2025)
- **Source**: `04_monthly_sip_inflows_cleaned.csv` + `10_benchmark_indices_cleaned.csv`
- **Type**: Dual-Axis Combination Chart
- **Columns (X-Axis)**: `[Month Date]` (Continuous Month: `2022-01` to `2025-12`)
- **Rows (Y-Axis 1 - Bars)**: `SUM(sip_inflow_crore)` (Monthly SIP Inflow Bar in `#1E3A8A`)
- **Rows (Y-Axis 2 - Line)**: `[NIFTY 50 Month-End Close]` (Actual Month-End Closing Price in `#F59E0B`)
- **Dual Axis**: Synchronized timeline across 48 months.

#### Visual 2: Category Net Inflow Heatmap
- **Source**: `05_category_inflows_cleaned.csv`
- **Type**: Heatmap / Highlight Table
- **Rows**: `category` (12 categories: Large Cap, Mid Cap, Small Cap, Flexi Cap, etc.)
- **Columns**: `month` (`2024-04` to `2025-03`)
- **Color**: `SUM(net_inflow_crore)` (Sequential Green/Blue diverging palette).

#### Visual 3: Top 5 Categories by Net Inflow (FY25)
- **Source**: `05_category_inflows_cleaned.csv`
- **Type**: Horizontal Bar Chart
- **Rows**: `category` (Sorted descending by `[FY25 Category Net Inflow (Cr)]`)
- **Columns**: `[FY25 Category Net Inflow (Cr)]`
- **Filters**: `[Is Top 5 Category FY25] = True`
- **Labels**: `SUM(net_inflow_crore)` formatted as `₹#,##0 Cr`.

#### Interactive Slicers & Filters (2 Required):
1. **`Fiscal Year / Date Range`**: Range slider / dropdown filter.
2. **`Category`**: Multi-select checklist filter.

---

## 3. Interactivity, Tooltips & Drill-Through Configuration

### Drill-Through Action (Page 2 Scheme Table $\rightarrow$ NAV Detail)
1. In Tableau, navigate to **Dashboard -> Actions -> Add Action -> Filter**.
2. **Source Sheet**: `Scorecard Table` (Page 2).
3. **Target Sheet**: `NAV vs Benchmark Line` (Page 2 detail).
4. **Target Fields**: Selected Fields $\rightarrow$ `amfi_code`.
5. **Behavior**: Clicking any fund row filters the NAV history chart specifically for that scheme's historical trajectory.

---

## 4. Final Delivery & Export Instructions

1. **Packaged Workbook**:
   - File -> Export Packaged Workbook -> Save as `bluestock_mf_dashboard.twbx`.
2. **Dashboard PDF Export**:
   - File -> Print to PDF -> Entire Workbook (Landscape, A4/Letter) -> Save as `Dashboard.pdf`.
3. **PNG Page Screenshots**:
   - Dashboard -> Export Image -> 4 separate PNG files saved as:
     - `page1_industry_overview.png`
     - `page2_fund_performance.png`
     - `page3_investor_analytics.png`
     - `page4_sip_market_trends.png`
