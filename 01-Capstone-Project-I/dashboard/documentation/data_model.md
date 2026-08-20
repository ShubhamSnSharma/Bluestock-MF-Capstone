# Power BI Semantic Data Model Documentation

This document defines the complete semantic data model specification for the Bluestock Mutual Fund Analytics Power BI solution. It documents all entity tables, relationship cardinalities, filter propagation rules, hidden columns, date calendar table setup, and recommended analytical hierarchies.

---

## 1. Entity Tables Inventory

The data model consists of 12 tables: 3 Core Dimension tables, 8 Fact tables, and 1 DAX-generated Calendar table.

| Table Name | Storage Mode | Description | Grain |
| :--- | :--- | :--- | :--- |
| `Dim_FundMaster` | Import | Master catalog of mutual fund schemes, fund houses, asset categories, and launch dates. | 1 row per `amfi_code` |
| `Dim_SchemePerformance` | Import | Quantitative risk and performance metrics (Sharpe, Sortino, Alpha, Beta, Max Drawdown). | 1 row per `amfi_code` |
| `Dim_Calendar` | Import (DAX) | Master fiscal and calendar date dimension table. | 1 row per Date |
| `Fact_NAVHistory` | Import | Daily Net Asset Value (NAV) pricing history and calculated daily returns. | 1 row per Date per Scheme |
| `Fact_InvestorTransactions` | Import | Transaction logs for investor investments, SIP payments, and redemptions. | 1 row per Transaction |
| `Fact_AUMByFundHouse` | Import | Quarterly AUM totals and scheme counts per Fund House (AMC). | 1 row per Date per AMC |
| `Fact_MonthlySIPInflows` | Import | Monthly macro SIP inflow totals and active SIP account counts. | 1 row per Month |
| `Fact_CategoryInflows` | Import | Monthly net capital inflow totals per asset category. | 1 row per Month per Category |
| `Fact_IndustryFolioCount` | Import | Industry-wide folio count statistics per asset category. | 1 row per Month per Category |
| `Fact_PortfolioHoldings` | Import | Detailed portfolio stock holdings, weight percentages, and market values. | 1 row per Stock per Scheme |
| `Fact_BenchmarkIndices` | Import | Daily benchmark index pricing and daily returns (e.g. Nifty 50, BSE Sensex). | 1 row per Date per Index |
| `Fact_RiskAnalytics` | Import | Tail-risk metrics including 95% Historical VaR, 95% CVaR, and risk grades. | 1 row per `amfi_code` |

---

## 2. Relationships Matrix & Topology

All relationships are configured with single-direction filter propagation from Dimension tables to Fact tables to ensure deterministic filter behavior and maximum VertiPaq compression.

| From Table (Dimension) | From Column | To Table (Fact) | To Column | Cardinality | Cross-Filter Direction | Relationship Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `Dim_Calendar` | `Date` | `Fact_NAVHistory` | `date` | $1 : N$ | Single (`Dim_Calendar` $\rightarrow$ `Fact_NAVHistory`) | **Active** |
| `Dim_Calendar` | `Date` | `Fact_InvestorTransactions` | `transaction_date` | $1 : N$ | Single (`Dim_Calendar` $\rightarrow$ `Fact_InvestorTransactions`) | **Active** |
| `Dim_Calendar` | `Date` | `Fact_AUMByFundHouse` | `date` | $1 : N$ | Single (`Dim_Calendar` $\rightarrow$ `Fact_AUMByFundHouse`) | **Active** |
| `Dim_Calendar` | `Date` | `Fact_MonthlySIPInflows` | `month_year` | $1 : N$ | Single (`Dim_Calendar` $\rightarrow$ `Fact_MonthlySIPInflows`) | **Inactive** |
| `Dim_FundMaster` | `amfi_code` | `Fact_NAVHistory` | `amfi_code` | $1 : N$ | Single (`Dim_FundMaster` $\rightarrow$ `Fact_NAVHistory`) | **Active** |
| `Dim_FundMaster` | `amfi_code` | `Fact_InvestorTransactions` | `amfi_code` | $1 : N$ | Single (`Dim_FundMaster` $\rightarrow$ `Fact_InvestorTransactions`) | **Active** |
| `Dim_FundMaster` | `amfi_code` | `Fact_PortfolioHoldings` | `amfi_code` | $1 : N$ | Single (`Dim_FundMaster` $\rightarrow$ `Fact_PortfolioHoldings`) | **Active** |
| `Dim_FundMaster` | `amfi_code` | `Dim_SchemePerformance` | `amfi_code` | $1 : 1$ | Both | **Active** |
| `Dim_FundMaster` | `amfi_code` | `Fact_RiskAnalytics` | `amfi_code` | $1 : 1$ | Both | **Active** |

---

## 3. Hidden Columns Specification

To ensure a clean report authoring interface, all surrogate keys, foreign key join columns, raw timestamps, and temporary calculation columns must be hidden in the Report View:

| Table Name | Hidden Columns | Rationale |
| :--- | :--- | :--- |
| `Fact_NAVHistory` | `amfi_code`, `date` | FK columns used strictly for relationship join. |
| `Fact_InvestorTransactions` | `amfi_code`, `transaction_date`, `investor_id` | FK columns hidden; measures compute distinct counts. |
| `Fact_PortfolioHoldings` | `amfi_code` | FK column hidden; filtered via `Dim_FundMaster`. |
| `Dim_SchemePerformance` | `amfi_code` | Joined $1:1$ with `Dim_FundMaster`. |
| `Fact_RiskAnalytics` | `amfi_code` | Joined $1:1$ with `Dim_FundMaster`. |
| `Fact_AUMByFundHouse` | `date` | FK column hidden; filtered via `Dim_Calendar`. |

---

## 4. Date Table Specification (`Dim_Calendar`)

A dedicated DAX calculated Date Table is required to enable Time Intelligence calculations (`YTD`, `QTD`, `SAMEPERIODLASTYEAR`, `DATEADD`).

```dax
Dim_Calendar = 
VAR MinDate = DATE(2022, 1, 1)
VAR MaxDate = DATE(2025, 12, 31)
RETURN
ADDCOLUMNS(
    CALENDAR(MinDate, MaxDate),
    "Year", YEAR([Date]),
    "Quarter", "Q" & FORMAT([Date], "Q"),
    "QuarterNo", QUARTER([Date]),
    "MonthNo", MONTH([Date]),
    "MonthName", FORMAT([Date], "MMMM"),
    "MonthShort", FORMAT([Date], "MMM"),
    "MonthYear", FORMAT([Date], "MMM YYYY"),
    "MonthYearSort", YEAR([Date]) * 100 + MONTH([Date]),
    "DayOfWeek", FORMAT([Date], "dddd"),
    "DayOfWeekNo", WEEKDAY([Date], 2),
    "IsWeekend", IF(WEEKDAY([Date], 2) >= 6, TRUE, FALSE)
)
```

*Note: Mark `Dim_Calendar` as a Date Table (`Right click Dim_Calendar -> Mark as Date Table -> Select Date column`).*

---

## 5. Recommended Analytical Hierarchies

### 1. Geography Hierarchy (`Dim_Geography`)
```text
Geography Hierarchy
└── State
    └── City
        └── City Tier (T30 / B30)
```

### 2. Asset Class Hierarchy (`Dim_AssetClass`)
```text
Asset Class Hierarchy
└── Category (Equity / Debt / Hybrid / Solution Oriented)
    └── Sub-Category (Large Cap / Mid Cap / Small Cap / Gilt)
        └── Scheme Name
```

### 3. Time Hierarchy (`Dim_Calendar`)
```text
Time Hierarchy
└── Year
    └── Quarter
        └── MonthYear
            └── Date
```
