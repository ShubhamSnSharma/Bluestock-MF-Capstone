"""
Sprint 6 — Day 37: Cluster Profiling, Correlation, Outlier Detection & Portfolio Statistics.

Reuses existing pipeline outputs (Sprint-1 DB, Sprint-5 cashflow_intelligence.xlsx,
Day-36 cluster_labels.csv). No KPIs are recalculated.

The 10 KPIs selected for correlation / outlier / portfolio analysis:
    1.  net_profit_margin_pct          — Profitability
    2.  operating_profit_margin_pct    — Operating profitability
    3.  return_on_equity_pct           — Return on equity
    4.  debt_to_equity                 — Leverage
    5.  return_on_capital_employed_pct — Capital efficiency
    6.  asset_turnover                 — Asset efficiency
    7.  revenue_cagr_5yr               — Revenue growth
    8.  fcf_conversion_pct             — Cash conversion
    9.  cfo_quality_score              — Cash flow quality
    10. capex_intensity_pct            — Capital intensity

Selection rationale:
    - All 10 are percentage or score metrics (comparable on same scale).
    - Availability ≥ 97.8% across 92 companies for year 2024.
    - Covers five analytical dimensions: profitability, leverage, efficiency,
      growth, and cash-flow quality.
    - All are computed by Sprint-2 KPI formulas and stored in nifty100.db.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

TEN_KPIs: List[str] = [
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "return_on_equity_pct",
    "debt_to_equity",
    "return_on_capital_employed_pct",
    "asset_turnover",
    "revenue_cagr_5yr",
    "fcf_conversion_pct",
    "cfo_quality_score",
    "capex_intensity_pct",
]

CLUSTERING_FEATURES: List[str] = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]

KPI_LABELS: Dict[str, str] = {
    "net_profit_margin_pct": "Net Profit Margin",
    "operating_profit_margin_pct": "Operating Profit Margin",
    "return_on_equity_pct": "Return on Equity",
    "debt_to_equity": "Debt to Equity",
    "return_on_capital_employed_pct": "ROCE",
    "asset_turnover": "Asset Turnover",
    "revenue_cagr_5yr": "Revenue CAGR 5Yr",
    "fcf_conversion_pct": "FCF Conversion",
    "cfo_quality_score": "CFO Quality Score",
    "capex_intensity_pct": "Capex Intensity",
}

OUTLIER_Z_THRESHOLD: float = 3.0


# ──────────────────────────────────────────────────────────────────────────────
# Path resolution
# ──────────────────────────────────────────────────────────────────────────────


def _resolve_paths(
    sprint6_root: Optional[str] = None,
) -> Tuple[Path, Path, Path, Path]:
    """Returns (sprint6_root, db_path, cashflow_path, cluster_csv_path)."""
    this_file = Path(__file__).resolve()
    s6 = Path(sprint6_root) if sprint6_root else this_file.parent.parent.parent
    platform = s6.parent
    return (
        s6,
        platform / "Sprint-01-Data-Foundation" / "nifty100.db",
        platform
        / "Sprint-05-Intelligence-NLP-PDF-Reports"
        / "output"
        / "cashflow_intelligence.xlsx",
        s6 / "output" / "cluster_labels.csv",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Data loading
# ──────────────────────────────────────────────────────────────────────────────


def load_kpi_data(
    db_path: Path,
    kpis: List[str] = TEN_KPIs,
    year: str = "2024",
) -> pd.DataFrame:
    """
    Loads the 10 KPIs for all companies from financial_ratios (year=2024).
    Returns DataFrame with company_id + all KPI columns.
    """
    cols = ", ".join(["company_id"] + kpis)
    df = pd.read_sql(
        f"SELECT {cols} FROM financial_ratios WHERE year = ?",
        sqlite3.connect(str(db_path)),
        params=(year,),
    )
    logger.info("Loaded %d rows, %d KPIs for year=%s", len(df), len(kpis), year)
    return df


def load_full_dataset(
    db_path: Path,
    cashflow_path: Path,
    cluster_csv_path: Path,
) -> pd.DataFrame:
    """
    Loads all data sources and merges into a single DataFrame:
    - 10 KPIs from financial_ratios (year=2024)
    - fcf_cagr_5yr from Sprint-05 cashflow_intelligence.xlsx
    - cluster assignments from Day-36 cluster_labels.csv
    - broad_sector from sectors table
    """
    conn = sqlite3.connect(str(db_path))

    # 10 KPIs
    cols = ", ".join(["company_id"] + TEN_KPIs)
    kpi_df = pd.read_sql(
        f"SELECT {cols} FROM financial_ratios WHERE year = '2024'",
        conn,
    )

    # Clustering features (including fcf_cagr_5yr from Sprint-05)
    cf_features = [f for f in CLUSTERING_FEATURES if f not in TEN_KPIs]
    if cf_features:
        cf_df = pd.read_excel(str(cashflow_path), usecols=["company_id"] + cf_features)
        kpi_df = kpi_df.merge(cf_df, on="company_id", how="left")

    # Sectors
    sectors_df = pd.read_sql(
        "SELECT company_id, broad_sector FROM sectors",
        conn,
    )
    conn.close()

    # Cluster labels
    cluster_df = pd.read_csv(str(cluster_csv_path))

    # Merge all
    df = kpi_df.merge(sectors_df, on="company_id", how="left")
    df = df.merge(cluster_df, on="company_id", how="left")

    logger.info("Full dataset: %d companies, %d columns", len(df), len(df.columns))
    return df


# ──────────────────────────────────────────────────────────────────────────────
# PART 1 — Cluster Profiling
# ──────────────────────────────────────────────────────────────────────────────


def build_cluster_profile(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds cluster profile: mean/median for each clustering feature per cluster.
    Also lists companies per cluster.
    """
    results = []
    for cid in sorted(df["cluster_id"].unique()):
        subset = df[df["cluster_id"] == cid]
        name = subset["cluster_name"].iloc[0]
        companies = sorted(subset["company_id"].tolist())

        row = {
            "cluster_id": cid,
            "cluster_name": name,
            "company_count": len(subset),
            "companies": ", ".join(companies),
        }
        for feat in CLUSTERING_FEATURES:
            vals = subset[feat].dropna()
            row[f"{feat}_mean"] = (
                round(float(vals.mean()), 4) if len(vals) > 0 else np.nan
            )
            row[f"{feat}_median"] = (
                round(float(vals.median()), 4) if len(vals) > 0 else np.nan
            )

        results.append(row)

    profile_df = pd.DataFrame(results)
    return profile_df


# ──────────────────────────────────────────────────────────────────────────────
# PART 2 — Correlation Heatmap
# ──────────────────────────────────────────────────────────────────────────────


def build_correlation_heatmap(
    df: pd.DataFrame,
    output_path: Path,
) -> pd.DataFrame:
    """
    Computes Pearson correlation for 10 KPIs across 92 companies.
    Saves annotated heatmap as PNG.
    Returns the correlation matrix DataFrame.
    """
    kpi_data = df[TEN_KPIs].copy()
    kpi_data.columns = [KPI_LABELS.get(c, c) for c in kpi_data.columns]

    corr_matrix = kpi_data.corr(method="pearson")

    # Plot
    fig, ax = plt.subplots(figsize=(14, 11))
    mask = np.zeros_like(corr_matrix, dtype=bool)
    # No mask — show full matrix for clarity

    sns.heatmap(
        corr_matrix,
        annot=True,
        fmt=".2f",
        cmap="RdBu_r",
        center=0,
        vmin=-1,
        vmax=1,
        square=True,
        linewidths=0.5,
        ax=ax,
        annot_kws={"size": 9},
        cbar_kws={"shrink": 0.8},
    )
    ax.set_title(
        "Pearson Correlation — 10 Financial KPIs (N100, Year 2024)", fontsize=14, pad=15
    )
    plt.xticks(rotation=45, ha="right", fontsize=10)
    plt.yticks(rotation=0, fontsize=10)
    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(output_path), dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Correlation heatmap saved: %s", output_path)

    return corr_matrix


# ──────────────────────────────────────────────────────────────────────────────
# PART 3 — Sector-Level Outlier Detection
# ──────────────────────────────────────────────────────────────────────────────


def detect_sector_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each of the 10 KPIs, calculates Z-score within each broad_sector.
    Flags |Z| > 3 as outlier.

    Handles edge cases:
    - Sectors with < 3 observations: Z-score set to NaN (not computable)
    - Sectors with zero standard deviation: Z-score set to 0 (company is at mean)
    """
    records = []

    for _, company_row in df.iterrows():
        company_id = company_row["company_id"]
        sector = company_row["broad_sector"]
        cluster_id = company_row["cluster_id"]

        if pd.isna(sector):
            continue

        for kpi in TEN_KPIs:
            value = company_row[kpi]
            if pd.isna(value):
                continue

            sector_data = df[df["broad_sector"] == sector][kpi].dropna()

            if len(sector_data) < 3:
                # Insufficient observations — cannot compute reliable Z-score
                z_score = np.nan
                is_outlier = False
                handling = "insufficient_sector_observations"
            elif sector_data.std() == 0:
                # Zero variance — all companies identical on this metric
                z_score = 0.0
                is_outlier = False
                handling = "zero_sector_std"
            else:
                sector_mean = sector_data.mean()
                sector_std = sector_data.std()
                z_score = (value - sector_mean) / sector_std
                is_outlier = abs(z_score) > OUTLIER_Z_THRESHOLD
                handling = "computed"

            records.append(
                {
                    "company_id": company_id,
                    "broad_sector": sector,
                    "cluster_id": cluster_id,
                    "metric": kpi,
                    "metric_label": KPI_LABELS.get(kpi, kpi),
                    "metric_value": round(float(value), 6),
                    "sector_mean": (
                        round(float(sector_data.mean()), 6)
                        if len(sector_data) > 0
                        else np.nan
                    ),
                    "sector_std": (
                        round(float(sector_data.std()), 6)
                        if len(sector_data) > 1
                        else np.nan
                    ),
                    "sector_count": int(len(sector_data)),
                    "z_score": (
                        round(float(z_score), 6) if not np.isnan(z_score) else np.nan
                    ),
                    "abs_z_score": (
                        round(float(abs(z_score)), 6)
                        if not np.isnan(z_score)
                        else np.nan
                    ),
                    "outlier_flag": bool(is_outlier),
                    "handling": handling,
                }
            )

    outlier_df = pd.DataFrame(records)
    total_outliers = outlier_df["outlier_flag"].sum()
    logger.info(
        "Outlier detection: %d records, %d outliers flagged",
        len(outlier_df),
        total_outliers,
    )
    return outlier_df


# ──────────────────────────────────────────────────────────────────────────────
# PART 4 — Portfolio Statistics
# ──────────────────────────────────────────────────────────────────────────────


def compute_portfolio_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes P10, P25, P50, P75, P90, Mean, Std for each of the 10 KPIs.
    Documents NaN handling and valid observation counts.
    """
    stats_rows = []

    for kpi in TEN_KPIs:
        vals = df[kpi].dropna()
        n_total = len(df)
        n_valid = len(vals)
        n_missing = n_total - n_valid

        row = {
            "metric": kpi,
            "metric_label": KPI_LABELS.get(kpi, kpi),
            "n_valid": int(n_valid),
            "n_missing": int(n_missing),
            "p10": round(float(vals.quantile(0.10)), 6) if n_valid > 0 else np.nan,
            "p25": round(float(vals.quantile(0.25)), 6) if n_valid > 0 else np.nan,
            "p50": round(float(vals.quantile(0.50)), 6) if n_valid > 0 else np.nan,
            "p75": round(float(vals.quantile(0.75)), 6) if n_valid > 0 else np.nan,
            "p90": round(float(vals.quantile(0.90)), 6) if n_valid > 0 else np.nan,
            "mean": round(float(vals.mean()), 6) if n_valid > 0 else np.nan,
            "std": round(float(vals.std()), 6) if n_valid > 1 else np.nan,
        }
        stats_rows.append(row)

    stats_df = pd.DataFrame(stats_rows)
    logger.info("Portfolio stats computed for %d KPIs", len(stats_df))
    return stats_df


# ──────────────────────────────────────────────────────────────────────────────
# Main pipeline entry point
# ──────────────────────────────────────────────────────────────────────────────


class Day37Pipeline:
    """
    Orchestrates the full Day-37 workflow:
      1. Load all data sources
      2. Build cluster profiles
      3. Compute correlation heatmap
      4. Detect sector outliers
      5. Compute portfolio statistics
      6. Export all outputs
    """

    def __init__(self, sprint6_root: Optional[str] = None) -> None:
        self.sprint6_root, self.db_path, self.cashflow_path, self.cluster_csv = (
            _resolve_paths(sprint6_root)
        )
        self.output_dir = self.sprint6_root / "output"
        self.reports_dir = self.sprint6_root / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self.df: Optional[pd.DataFrame] = None
        self.cluster_profile: Optional[pd.DataFrame] = None
        self.corr_matrix: Optional[pd.DataFrame] = None
        self.outlier_df: Optional[pd.DataFrame] = None
        self.portfolio_stats: Optional[pd.DataFrame] = None

    def run(self) -> None:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

        # Step 1: Load data
        logger.info("=== Step 1: Loading data ===")
        self.df = load_full_dataset(self.db_path, self.cashflow_path, self.cluster_csv)

        # Step 2: Cluster profiling
        logger.info("=== Step 2: Cluster profiling ===")
        self.cluster_profile = build_cluster_profile(self.df)
        profile_path = self.output_dir / "cluster_profile.csv"
        self.cluster_profile.to_csv(str(profile_path), index=False)
        logger.info("Cluster profile saved: %s", profile_path)

        # Step 3: Correlation heatmap
        logger.info("=== Step 3: Correlation heatmap ===")
        corr_path = self.reports_dir / "correlation_heatmap.png"
        self.corr_matrix = build_correlation_heatmap(self.df, corr_path)

        # Step 4: Outlier detection
        logger.info("=== Step 4: Sector outlier detection ===")
        self.outlier_df = detect_sector_outliers(self.df)
        outlier_path = self.output_dir / "outlier_report.csv"
        self.outlier_df.to_csv(str(outlier_path), index=False)
        logger.info("Outlier report saved: %s", outlier_path)
        logger.info("Total outliers flagged: %d", self.outlier_df["outlier_flag"].sum())

        # Step 5: Portfolio statistics
        logger.info("=== Step 5: Portfolio statistics ===")
        self.portfolio_stats = compute_portfolio_stats(self.df)
        stats_path = self.output_dir / "portfolio_stats.csv"
        self.portfolio_stats.to_csv(str(stats_path), index=False)
        logger.info("Portfolio stats saved: %s", stats_path)

        logger.info("=== Day 37 pipeline complete ===")


if __name__ == "__main__":
    pipeline = Day37Pipeline()
    pipeline.run()
