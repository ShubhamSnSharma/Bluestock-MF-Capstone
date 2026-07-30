# Week 1 Data Analytics Project

This repository demonstrates an end-to-end data analytics workflow completed as part of a Data Analytics Internship. The project covers raw dataset ingestion, data cleaning, exploratory data analysis (EDA), KPI calculation, relational SQL querying, and executive dashboard development in Microsoft Excel and Power BI using the Sample Superstore dataset.

## Project Objectives
- Clean and format raw transactional data for analytics.
- Perform exploratory data analysis to uncover performance trends.
- Query transaction data using SQL for relational insights.
- Build executive dashboards in Microsoft Excel and Power BI.
- Synthesize actionable business insights for revenue and margin growth.

## Project Structure
```
Week1-Data-Analytics/
├── data/
│   ├── raw/
│   │   ├── Sample - Superstore.xls
│   │   └── superstore.csv
│   └── cleaned/
│       └── superstore_cleaned.csv
├── python/
│   ├── notebooks/
│   │   └── 01_data_cleaning_and_eda.ipynb
│   └── scripts/
│       └── create_sqlite_db.py
├── sql/
│   ├── superstore.db
│   └── analysis_queries.sql
├── excel/
│   └── Excel_Sales_Dashboard.xlsx
├── powerbi/
│   └── PowerBI_Superstore_Dashboard.pdf
├── reports/
│   ├── EDA_Report.md
│   ├── EDA_Report.pdf
│   └── images/
│       ├── discount_vs_profit.png
│       ├── monthly_sales_trend.png
│       ├── sales_by_category.png
│       └── sales_by_region.png
├── requirements.txt
└── .gitignore
```

## Dataset
The dataset used in this project is the Sample Superstore dataset, containing transactional records for a US retail company from January 2018 through December 2021.
- **Raw Records:** 9,994 order line items
- **Cleaned Records:** 9,983 valid records (after removing rows with missing location data)
- **Features:** 21 attributes including order dates, shipping modes, customer segments, geographic locations, product categories, sales, quantity, discounts, and profit.

## Technologies Used
- **Python** (Pandas, NumPy, Matplotlib)
- **Jupyter Notebook**
- **SQL** (SQLite)
- **Microsoft Excel**
- **Power BI**

## Project Workflow
- **Load Dataset:** Download raw data using KaggleHub and store locally in `data/raw/`.
- **Clean Data:** Standardize date formats, handle missing postal codes, and verify record uniqueness.
- **Perform EDA:** Analyze distributions, outliers, category metrics, and discount sensitivity.
- **Calculate KPIs:** Derive total sales, total profit, total order count, and total unique customers.
- **SQL Analysis:** Convert cleaned data to SQLite and execute 18 structured analytical queries.
- **Excel Dashboard:** Develop pivot tables and an interactive sales dashboard in Excel.
- **Power BI Dashboard:** Build an executive visual dashboard exported for presentation.

## Key Business Insights
- **Technology Category Leads Profitability:** Technology generated the highest total sales and net profit among all product categories.
- **Furniture Category Suffers Low Margins:** Furniture recorded strong sales volume but minimal profit due to aggressive discounting on tables and bookcases.
- **West Region Outperforms Nationally:** The West region led all geographic territories in both total sales and net profit.
- **Consumer Segment Drives Revenue:** Consumer customers contributed over 50% of total company sales and net profit.
- **Aggressive Discounting Destroys Profit:** Promotional discounts of 20% or higher led to severe profit erosion and negative profit margins.

## Deliverables
- [x] Cleaned Dataset (`data/cleaned/superstore_cleaned.csv`)
- [x] Python Analysis Notebook (`python/notebooks/01_data_cleaning_and_eda.ipynb`)
- [x] SQL Queries (`sql/analysis_queries.sql`)
- [x] EDA Report (`reports/EDA_Report.md`)
- [x] Excel Dashboard (`excel/Excel_Sales_Dashboard.xlsx`)
- [x] Power BI Dashboard (`powerbi/PowerBI_Superstore_Dashboard.pdf`)

## Installation
Clone the repository and install required dependencies:
```bash
pip install -r requirements.txt
```
Launch Jupyter Notebook to view the analysis notebook:
```bash
jupyter notebook python/notebooks/01_data_cleaning_and_eda.ipynb
```

## Repository Contents
- **data/**: Raw dataset files and the exported cleaned CSV file.
- **python/**: Jupyter notebook for EDA and Python script for SQLite database creation.
- **sql/**: SQLite database file and 18 structured SQL analytical queries.
- **excel/**: Excel workbook containing pivot tables and the interactive sales dashboard.
- **powerbi/**: PDF export of the interactive Power BI dashboard.
- **reports/**: Executive EDA Markdown report, PDF export, and embedded chart figures.

## Author
Shubham Sharma
