# Bluestock Mutual Fund Capstone
## Day 03: Exploratory Data Analysis

This project performs exploratory data analysis (EDA) on the cleaned mutual fund datasets prepared in Day 02 of the Bluestock Mutual Fund Capstone. Using Python, Seaborn, and Plotly, it explores mutual fund performance, investor behaviour, portfolio composition, and benchmark trends through interactive and publication-quality visualizations.

---

## Objectives

- Analyze mutual fund performance trends
- Explore retail investor behavior and demographics
- Visualize industry AUM and SIP inflow growth
- Study portfolio sector allocation and stock holdings
- Examine scheme risk-return relationships
- Generate publication-quality visualizations

---

## Project Workflow

```text
Processed CSVs & SQLite Database
            │
            ▼
      EDA Utilities
            │
            ▼
      EDA Notebook
            │
            ├── Time Series Analysis
            ├── Investor Analytics
            ├── Portfolio Analysis
            ├── Risk & Performance Analysis
            └── Benchmark Analysis
            │
            ▼
     Charts & Reports
```

---

## Project Structure

```text
Day-03-Exploratory-Data-Analysis/
├── data/
├── notebooks/
├── charts/
├── reports/
├── scripts/
├── README.md
└── requirements.txt
```

---

## Analysis Overview

| Category | Analysis |
|----------|----------|
| Time Series | NAV Trends, AUM Growth, SIP Growth, Folio Growth |
| Investor Analytics | Age Distribution, Gender Split, State-wise Investments, City Tier Analysis |
| Performance | Return Correlation, Expense Ratio Distribution |
| Portfolio | Sector Allocation, Top Holdings |
| Benchmark | Market Index Performance |

The notebook contains 16 visualizations with both static PNG exports and interactive Plotly charts where applicable. The complete analysis is available in `notebooks/EDA_Analysis.ipynb`, while all generated visualizations are exported to the `charts/` directory.

---

## How to Run

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Generate the notebook:
   ```bash
   python scripts/create_eda_notebook.py
   ```

3. Run verification:
   ```bash
   python scripts/run_final_verification.py
   ```

---

## Deliverables

- `EDA_Analysis.ipynb`
- 16 static PNG charts (300 DPI)
- 7 interactive Plotly HTML charts
- Visualization utilities (`eda_utils.py`)
- Validation reports
- Executive summary report (`eda_summary.md`)

---

## Technologies

- Python
- Pandas
- NumPy
- Matplotlib
- Seaborn
- Plotly
- Kaleido
- Git

---

## Results

- 16 publication-quality visualizations created.
- 7 interactive Plotly charts exported.
- Analysis performed on 10 cleaned mutual fund datasets.
- Notebook validated successfully.
- All deliverables completed.
