# Bluestock Mutual Fund Capstone
## Day 06: Power BI Dashboard Design & Data Model Specification

This directory contains the complete Power BI implementation blueprint and semantic data model preparation files for Day 06 of the Bluestock Mutual Fund Analytics Capstone.

---

## Deliverables & Organization

```text
Day-06-PowerBI-Dashboard-Design/
├── dashboard_specification.md  # Complete 4-page Power BI visual blueprint & UX guidelines
├── dashboard_theme.json         # Production Power BI theme JSON configuration
├── dax_measures.md             # Complete DAX measures dictionary (20+ calculations)
├── data_model.md               # Star Schema topology, relationships & Date Table setup
├── field_folders.md            # Display folder organization mapping for DAX measures
└── README.md                   # Module documentation index
```

---

## Deliverables Summary

| File | Description |
| :--- | :--- |
| [`dashboard_specification.md`](./dashboard_specification.md) | Enterprise-grade Power BI visual specification covering data model mapping, visual layout, dynamic slicers, drillthrough targets, and VertiPaq performance optimization rules. |
| [`dashboard_theme.json`](./dashboard_theme.json) | Production-ready Power BI JSON theme file defining colors (Navy `#1E3A8A`, Slate `#0F172A`, Green `#10B981`, Red `#EF4444`), typography (Segoe UI), and visual element styles. |
| [`dax_measures.md`](./dax_measures.md) | Complete DAX measure library for Core KPIs (`Total AUM`, `Total Investors`, `Total SIP`), Performance (`CAGR`, `Sharpe`, `Sortino`, `Alpha`, `Beta`, `Max Drawdown`), Risk (`VaR 95`, `CVaR 95`, `HHI`), and Investor Continuity (`At Risk Investors`, `At Risk Rate`). |
| [`data_model.md`](./data_model.md) | Semantic data model specification documenting Star Schema tables, relationships matrix, $1:N$ single-direction filter rules, hidden columns, and DAX `Dim_Calendar` table script. |
| [`field_folders.md`](./field_folders.md) | Display folder hierarchy mapping (`01 Executive KPIs`, `02 Performance Metrics`, `03 Risk Analytics`, `04 Investor Behavior`, `05 Benchmark Comparison`) for clean model governance. |
