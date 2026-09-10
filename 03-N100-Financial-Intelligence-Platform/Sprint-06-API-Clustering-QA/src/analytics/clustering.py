"""
Sprint 6 — Day 36: KMeans Clustering for N100 Financial Intelligence Platform.

Clusters all 92 Nifty-100 companies into 5 groups using five financial features:
    - return_on_equity_pct          (financial_ratios, year=2024)
    - debt_to_equity                (financial_ratios, year=2024)
    - revenue_cagr_5yr              (financial_ratios, year=2024)
    - fcf_cagr_5yr                  (Sprint-05 cashflow_intelligence.xlsx)
    - operating_profit_margin_pct   (financial_ratios, year=2024)

Data Preparation:
    1. Source latest available year (2024) for four features from the Sprint-01 DB.
    2. Source fcf_cagr_5yr from Sprint-05 cashflow_intelligence.xlsx.
    3. Impute missing values using the MEDIAN of the same feature
       within the company's broad_sector (from the sectors table).
    4. Apply StandardScaler so all features have zero mean and unit variance.

Clustering:
    KMeans(n_clusters=5, random_state=42, n_init=10)

Cluster Naming:
    Names are assigned based on each cluster's dominant financial profile
    (median values of the five features), NOT by positional ROE ordering.
    This ensures names are financially meaningful and deterministic.

Outputs:
    output/cluster_labels.csv     — 92 rows: company_id, cluster_id, cluster_name,
                                    distance_from_centroid
    reports/elbow_plot.png        — Inertia vs k (k=2..10) elbow curve

Data Source Authority:
    - Sprint-01-Data-Foundation/nifty100.db  (companies, sectors, financial_ratios)
    - Sprint-05-Intelligence-NLP-PDF-Reports/output/cashflow_intelligence.xlsx
    NO data is fabricated. All values originate from existing pipeline outputs.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib

matplotlib.use("Agg")  # non-interactive backend — safe for CI / headless runs
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

FEATURES: List[str] = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]

N_CLUSTERS: int = 5
RANDOM_STATE: int = 42
ELBOW_K_RANGE: range = range(2, 11)  # k = 2..10

# Cluster name mapping — profile-based.
# Names are assigned AFTER clustering by identifying each cluster's dominant
# financial characteristics (median values), NOT by positional ROE ordering.
# This makes naming stable and financially meaningful across re-runs.
CLUSTER_NAME_MAP: Dict[int, str] = {
    0: "High FCF Growth Outlier",
    1: "Financial Sector — High Leverage Growth",
    2: "Capital Efficient",
    3: "Premium Margin Leaders",
    4: "Defense PSU — Extreme ROE Outlier",
}

# ──────────────────────────────────────────────────────────────────────────────
# Path resolution helpers
# ──────────────────────────────────────────────────────────────────────────────


def _resolve_paths(
    db_path: Optional[str] = None,
    cashflow_path: Optional[str] = None,
    sprint6_root: Optional[str] = None,
) -> Tuple[Path, Path, Path]:
    """
    Returns (db_path, cashflow_excel_path, sprint6_root).

    Default resolution walks up from this file's location to find:
      - Sprint-01-Data-Foundation/nifty100.db
      - Sprint-05-Intelligence-NLP-PDF-Reports/output/cashflow_intelligence.xlsx
    """
    this_file = Path(__file__).resolve()
    # clustering.py lives at Sprint-06-API-Clustering-QA/src/analytics/
    # so parent.parent.parent = Sprint-06 root, parent×4 = platform root
    sprint6 = Path(sprint6_root) if sprint6_root else this_file.parent.parent.parent
    platform = sprint6.parent

    resolved_db = (
        Path(db_path)
        if db_path
        else (platform / "Sprint-01-Data-Foundation" / "nifty100.db")
    )
    resolved_cf = (
        Path(cashflow_path)
        if cashflow_path
        else (
            platform
            / "Sprint-05-Intelligence-NLP-PDF-Reports"
            / "output"
            / "cashflow_intelligence.xlsx"
        )
    )
    return resolved_db, resolved_cf, sprint6


# ──────────────────────────────────────────────────────────────────────────────
# Data loading
# ──────────────────────────────────────────────────────────────────────────────


def load_feature_matrix(
    db_path: Path,
    cashflow_path: Path,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads and joins the five clustering features for all 92 companies.

    Returns:
        (feature_df, imputation_log_df)

        feature_df has columns:
            company_id, broad_sector,
            return_on_equity_pct, debt_to_equity, revenue_cagr_5yr,
            fcf_cagr_5yr, operating_profit_margin_pct

        imputation_log_df records each cell that was imputed:
            company_id, feature, original_value, imputed_value, sector_used
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    if not cashflow_path.exists():
        raise FileNotFoundError(f"Cashflow output not found: {cashflow_path}")

    conn = sqlite3.connect(str(db_path))

    # ── 1. financial_ratios: four features, year=2024 ──────────────────────
    # year='2024' is the latest numeric year for all 92 companies (verified).
    fr_df = pd.read_sql(
        """
        SELECT
            company_id,
            return_on_equity_pct,
            debt_to_equity,
            revenue_cagr_5yr,
            operating_profit_margin_pct
        FROM financial_ratios
        WHERE year = '2024'
        ORDER BY company_id
        """,
        conn,
    )
    logger.info("Loaded %d rows from financial_ratios (year=2024)", len(fr_df))

    # ── 2. sectors: broad_sector for each company ──────────────────────────
    sectors_df = pd.read_sql(
        "SELECT company_id, broad_sector FROM sectors ORDER BY company_id",
        conn,
    )
    conn.close()
    logger.info("Loaded %d sector rows", len(sectors_df))

    # ── 3. Sprint-05 cashflow: fcf_cagr_5yr ───────────────────────────────
    cf_df = pd.read_excel(str(cashflow_path), usecols=["company_id", "fcf_cagr_5yr"])
    logger.info(
        "Loaded cashflow_intelligence.xlsx: %d rows, %d non-null fcf_cagr_5yr",
        len(cf_df),
        cf_df["fcf_cagr_5yr"].notna().sum(),
    )

    # ── 4. Merge all sources ───────────────────────────────────────────────
    df = fr_df.merge(cf_df, on="company_id", how="left")
    df = df.merge(sectors_df, on="company_id", how="left")

    if len(df) != 92:
        raise ValueError(
            f"Expected 92 companies after merge, got {len(df)}. "
            "Check financial_ratios for year='2024'."
        )
    if df["company_id"].duplicated().any():
        dups = df[df["company_id"].duplicated(keep=False)]["company_id"].tolist()
        raise ValueError(f"Duplicate company_ids after merge: {dups}")

    # ── 5. Sector-median imputation ────────────────────────────────────────
    df, imputation_log = _impute_sector_medians(df)

    return df, imputation_log


def _impute_sector_medians(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Imputes missing feature values with the broad_sector median.

    Imputation order: within each (sector, feature) group, compute the median
    of all non-null values in that group, then fill nulls.

    Records every imputation in a log DataFrame.
    """
    df = df.copy()
    imputation_records: List[dict] = []

    for feature in FEATURES:
        # Compute sector medians using only non-null values
        sector_medians = (
            df.groupby("broad_sector")[feature].median().rename("sector_median")
        )
        for idx, row in df.iterrows():
            if pd.isna(row[feature]):
                sector = row["broad_sector"]
                median_val = sector_medians.get(sector, np.nan)

                if pd.isna(median_val):
                    # Fallback: global median if entire sector is null for this feature
                    median_val = df[feature].median()
                    logger.warning(
                        "Global fallback imputation for %s / %s (sector '%s' has no data)",
                        row["company_id"],
                        feature,
                        sector,
                    )

                imputation_records.append(
                    {
                        "company_id": row["company_id"],
                        "feature": feature,
                        "original_value": None,
                        "imputed_value": round(float(median_val), 6),
                        "sector_used": sector,
                    }
                )
                df.at[idx, feature] = median_val
                logger.debug(
                    "Imputed %s / %s → %.4f (sector=%s median)",
                    row["company_id"],
                    feature,
                    median_val,
                    sector,
                )

    imputation_log = pd.DataFrame(
        imputation_records,
        columns=[
            "company_id",
            "feature",
            "original_value",
            "imputed_value",
            "sector_used",
        ],
    )
    logger.info(
        "Total imputations: %d across %d features",
        len(imputation_log),
        imputation_log["feature"].nunique() if len(imputation_log) else 0,
    )
    return df, imputation_log


# ──────────────────────────────────────────────────────────────────────────────
# Feature scaling
# ──────────────────────────────────────────────────────────────────────────────


def scale_features(feature_matrix: np.ndarray) -> Tuple[np.ndarray, StandardScaler]:
    """
    Applies StandardScaler to the feature matrix.

    Returns (scaled_matrix, fitted_scaler).
    """
    scaler = StandardScaler()
    scaled = scaler.fit_transform(feature_matrix)
    logger.info(
        "StandardScaler applied: feature means after scaling ≈ %s",
        np.round(scaled.mean(axis=0), 6),
    )
    return scaled, scaler


# ──────────────────────────────────────────────────────────────────────────────
# Elbow curve
# ──────────────────────────────────────────────────────────────────────────────


def compute_elbow_inertias(
    scaled_matrix: np.ndarray,
    k_range: range = ELBOW_K_RANGE,
) -> Dict[int, float]:
    """
    Computes KMeans inertia for k in k_range.

    Uses random_state=42 and n_init=10 for reproducibility and stability.
    """
    inertias: Dict[int, float] = {}
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        km.fit(scaled_matrix)
        inertias[k] = float(km.inertia_)
        logger.debug("k=%d  inertia=%.4f", k, km.inertia_)
    return inertias


def plot_elbow_curve(
    inertias: Dict[int, float],
    output_path: Path,
    highlight_k: int = N_CLUSTERS,
) -> None:
    """
    Saves the elbow curve as a PNG.

    The selected k (highlight_k) is marked with a vertical dashed line.
    """
    ks = sorted(inertias.keys())
    vals = [inertias[k] for k in ks]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(ks, vals, marker="o", linewidth=2, color="#2563EB", label="Inertia")
    ax.axvline(
        x=highlight_k,
        color="#DC2626",
        linestyle="--",
        linewidth=1.5,
        label=f"Selected k={highlight_k}",
    )
    ax.set_xlabel("Number of Clusters (k)", fontsize=12)
    ax.set_ylabel("Inertia (Within-cluster SSE)", fontsize=12)
    ax.set_title(
        "KMeans Elbow Curve — N100 Financial Intelligence Platform", fontsize=13
    )
    ax.set_xticks(ks)
    ax.legend(fontsize=11)
    ax.grid(True, linestyle="--", alpha=0.4)

    # Annotate each inertia value
    for k, v in zip(ks, vals):
        ax.annotate(
            f"{v:,.0f}",
            xy=(k, v),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            fontsize=8,
            color="#374151",
        )

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(output_path), dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Elbow plot saved: %s", output_path)


# ──────────────────────────────────────────────────────────────────────────────
# KMeans clustering
# ──────────────────────────────────────────────────────────────────────────────


def run_kmeans(
    scaled_matrix: np.ndarray,
    n_clusters: int = N_CLUSTERS,
    random_state: int = RANDOM_STATE,
) -> Tuple[KMeans, np.ndarray, np.ndarray]:
    """
    Fits KMeans and returns (fitted_model, raw_labels, distances_from_centroid).

    cluster labels are the raw 0-based labels from sklearn (not yet re-indexed).
    distances are the Euclidean distance from each point to its assigned centroid.
    """
    km = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    km.fit(scaled_matrix)
    raw_labels = km.labels_

    # Distance from each sample to its assigned centroid
    centroids = km.cluster_centers_
    distances = np.array(
        [
            float(np.linalg.norm(scaled_matrix[i] - centroids[raw_labels[i]]))
            for i in range(len(scaled_matrix))
        ]
    )
    return km, raw_labels, distances


def _reindex_clusters_by_roe(
    raw_labels: np.ndarray,
    feature_df: pd.DataFrame,
) -> np.ndarray:
    """
    Re-maps raw sklearn cluster IDs so that cluster_id 0 always corresponds to
    the group with the LOWEST mean return_on_equity_pct and cluster_id 4 is
    the HIGHEST. This makes cluster_id assignment deterministic and human-interpretable
    regardless of sklearn's internal label ordering.

    Returns an array of new cluster IDs (0-indexed, same length as raw_labels).
    """
    roe_col = "return_on_equity_pct"
    temp = feature_df[roe_col].values
    raw_unique = sorted(set(raw_labels))

    # Mean ROE per raw cluster
    mean_roe_per_cluster = {c: np.mean(temp[raw_labels == c]) for c in raw_unique}
    # Sort clusters by ascending mean ROE → assign new IDs 0..4
    sorted_clusters = sorted(raw_unique, key=lambda c: mean_roe_per_cluster[c])
    remap = {old: new for new, old in enumerate(sorted_clusters)}

    return np.array([remap[lbl] for lbl in raw_labels], dtype=int)


def _assign_cluster_names(
    labels: np.ndarray,
    feature_df: pd.DataFrame,
) -> Dict[int, str]:
    """
    Assigns a descriptive name to each KMeans cluster based on its dominant
    financial profile (median values of the five clustering features).

    Naming rules (applied in order of specificity):
      - Cluster with highest median FCF CAGR → "High FCF Growth Outlier"
      - Cluster with highest median D/E (financial sector signature) →
        "Financial Sector — High Leverage Growth"
      - Cluster with highest median OPM → "Premium Margin Leaders"
      - Cluster with highest median ROE → "Defense PSU — Extreme ROE Outlier"
      - Remaining cluster → "Capital Efficient"

    Returns a dict mapping cluster_id → name.
    """
    unique_ids = sorted(set(labels))
    name_map_local: Dict[int, str] = {}

    # Compute medians per cluster (skip NaN)
    medians: Dict[int, Dict[str, float]] = {}
    for c in unique_ids:
        mask = labels == c
        medians[c] = {
            "fcf_cagr_5yr": float(
                np.nanmedian(feature_df.loc[mask, "fcf_cagr_5yr"].values)
            ),
            "debt_to_equity": float(
                np.nanmedian(feature_df.loc[mask, "debt_to_equity"].values)
            ),
            "operating_profit_margin_pct": float(
                np.nanmedian(feature_df.loc[mask, "operating_profit_margin_pct"].values)
            ),
            "return_on_equity_pct": float(
                np.nanmedian(feature_df.loc[mask, "return_on_equity_pct"].values)
            ),
        }

    assigned: set = set()

    # 1. Highest median FCF CAGR → "High FCF Growth Outlier"
    best = max(unique_ids, key=lambda c: medians[c]["fcf_cagr_5yr"])
    name_map_local[best] = "High FCF Growth Outlier"
    assigned.add(best)

    # 2. Highest median D/E (financial sector signature) → "Financial Sector — High Leverage Growth"
    remaining = [c for c in unique_ids if c not in assigned]
    best = max(remaining, key=lambda c: medians[c]["debt_to_equity"])
    name_map_local[best] = "Financial Sector — High Leverage Growth"
    assigned.add(best)

    # 3. Highest median OPM → "Premium Margin Leaders"
    remaining = [c for c in unique_ids if c not in assigned]
    best = max(remaining, key=lambda c: medians[c]["operating_profit_margin_pct"])
    name_map_local[best] = "Premium Margin Leaders"
    assigned.add(best)

    # 4. Highest median ROE → "Defense PSU — Extreme ROE Outlier"
    remaining = [c for c in unique_ids if c not in assigned]
    best = max(remaining, key=lambda c: medians[c]["return_on_equity_pct"])
    name_map_local[best] = "Defense PSU — Extreme ROE Outlier"
    assigned.add(best)

    # 5. Remaining → "Capital Efficient"
    remaining = [c for c in unique_ids if c not in assigned]
    for c in remaining:
        name_map_local[c] = "Capital Efficient"
    assigned.update(remaining)

    for cid, name in sorted(name_map_local.items()):
        logger.info(
            "Cluster %d → %s  (median ROE=%.2f, D/E=%.2f, FCF_CAGR=%.2f, OPM=%.2f)",
            cid,
            name,
            medians[cid]["return_on_equity_pct"],
            medians[cid]["debt_to_equity"],
            medians[cid]["fcf_cagr_5yr"],
            medians[cid]["operating_profit_margin_pct"],
        )

    return name_map_local


# ──────────────────────────────────────────────────────────────────────────────
# Main pipeline entry point
# ──────────────────────────────────────────────────────────────────────────────


class ClusteringPipeline:
    """
    Orchestrates the full Day-36 clustering workflow:
      1. Load data from Sprint-01 DB + Sprint-05 cashflow output
      2. Impute nulls with sector medians
      3. Scale with StandardScaler
      4. Compute elbow curve (k=2..10)
      5. Fit KMeans(n_clusters=5, random_state=42)
      6. Assign cluster names based on dominant financial profiles
      7. Export cluster_labels.csv and elbow_plot.png
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        cashflow_path: Optional[str] = None,
        sprint6_root: Optional[str] = None,
    ) -> None:
        self.db_path, self.cashflow_path, self.sprint6_root = _resolve_paths(
            db_path, cashflow_path, sprint6_root
        )
        self.output_dir = self.sprint6_root / "output"
        self.reports_dir = self.sprint6_root / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # State populated after run()
        self.feature_df: Optional[pd.DataFrame] = None
        self.imputation_log: Optional[pd.DataFrame] = None
        self.scaled_matrix: Optional[np.ndarray] = None
        self.scaler: Optional[StandardScaler] = None
        self.kmeans_model: Optional[KMeans] = None
        self.cluster_labels_df: Optional[pd.DataFrame] = None
        self.inertias: Optional[Dict[int, float]] = None

    # ── Public API ───────────────────────────────────────────────────────────

    def run(self) -> pd.DataFrame:
        """
        Executes the full pipeline.
        Returns the cluster_labels DataFrame (also written to CSV).
        """
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

        # Step 1: Load data
        logger.info("=== Step 1: Loading feature matrix ===")
        self.feature_df, self.imputation_log = load_feature_matrix(
            self.db_path, self.cashflow_path
        )
        logger.info(
            "Feature matrix: %d companies, %d features",
            len(self.feature_df),
            len(FEATURES),
        )
        logger.info(
            "Imputations applied:\n%s",
            (
                self.imputation_log.groupby("feature")
                .size()
                .rename("count")
                .to_string()
                if len(self.imputation_log) > 0
                else "  none"
            ),
        )

        # Step 2: Scale
        logger.info("=== Step 2: StandardScaler ===")
        raw_matrix = self.feature_df[FEATURES].values
        self.scaled_matrix, self.scaler = scale_features(raw_matrix)

        # Step 3: Elbow curve
        logger.info("=== Step 3: Computing elbow curve (k=2..10) ===")
        self.inertias = compute_elbow_inertias(self.scaled_matrix, ELBOW_K_RANGE)
        for k, v in sorted(self.inertias.items()):
            logger.info("  k=%2d  inertia = %.2f", k, v)

        elbow_path = self.reports_dir / "elbow_plot.png"
        plot_elbow_curve(self.inertias, elbow_path, highlight_k=N_CLUSTERS)

        # Step 4: KMeans
        logger.info(
            "=== Step 4: KMeans(n_clusters=%d, random_state=%d) ===",
            N_CLUSTERS,
            RANDOM_STATE,
        )
        self.kmeans_model, raw_labels, distances = run_kmeans(
            self.scaled_matrix, n_clusters=N_CLUSTERS, random_state=RANDOM_STATE
        )
        logger.info("KMeans inertia: %.4f", self.kmeans_model.inertia_)

        # Step 5: Assign cluster names based on dominant financial profiles
        # (uses median values — NOT positional ROE ordering)
        logger.info("=== Step 5: Profile-based cluster naming ===")
        profile_name_map = _assign_cluster_names(raw_labels, self.feature_df)

        # Step 6: Build output DataFrame — use raw KMeans labels directly
        result_df = self.feature_df[["company_id"]].copy()
        result_df["cluster_id"] = raw_labels.astype(int)
        result_df["cluster_name"] = result_df["cluster_id"].map(profile_name_map)
        result_df["distance_from_centroid"] = np.round(distances, 6)

        # Validate
        self._validate_output(result_df)

        # Save
        csv_path = self.output_dir / "cluster_labels.csv"
        result_df.to_csv(str(csv_path), index=False)
        logger.info("cluster_labels.csv written: %s", csv_path)

        # Log cluster membership
        logger.info("=== Cluster membership ===")
        for cid in sorted(result_df["cluster_id"].unique()):
            members = result_df[result_df["cluster_id"] == cid]
            logger.info(
                "  Cluster %d (%s): %d companies",
                cid,
                profile_name_map[cid],
                len(members),
            )

        self.cluster_labels_df = result_df
        return result_df

    def get_imputation_summary(self) -> pd.Series:
        """Returns count of imputations per feature."""
        if self.imputation_log is None or len(self.imputation_log) == 0:
            return pd.Series(dtype=int)
        return self.imputation_log.groupby("feature").size().rename("imputation_count")

    # ── Validation ───────────────────────────────────────────────────────────

    @staticmethod
    def _validate_output(df: pd.DataFrame) -> None:
        """Raises ValueError if output constraints are violated."""
        if len(df) != 92:
            raise ValueError(f"Expected 92 rows, got {len(df)}")
        if df["company_id"].duplicated().any():
            raise ValueError("Duplicate company_id in output")
        if set(df["cluster_id"].unique()) != set(range(N_CLUSTERS)):
            raise ValueError(f"cluster_id values must be exactly 0-{N_CLUSTERS-1}")
        if df["cluster_name"].isna().any():
            raise ValueError("Null cluster_name found")
        if (df["distance_from_centroid"] < 0).any():
            raise ValueError("Negative distance_from_centroid found")
        logger.info("Output validation passed ✓")


# ──────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    pipeline = ClusteringPipeline()
    result = pipeline.run()

    # Print summary table
    print("\n=== CLUSTER LABELS (first 10 rows) ===")
    print(result.head(10).to_string(index=False))

    print("\n=== CLUSTER MEMBERSHIP ===")
    for cid in sorted(result["cluster_id"].unique()):
        members = result[result["cluster_id"] == cid]["company_id"].tolist()
        print(f"  Cluster {cid} — {CLUSTER_NAME_MAP[cid]}: {len(members)} companies")
        print(f"    {', '.join(members)}")

    print("\n=== IMPUTATION SUMMARY ===")
    print(pipeline.get_imputation_summary().to_string())

    print("\n=== ELBOW INERTIAS ===")
    for k, v in sorted(pipeline.inertias.items()):
        print(f"  k={k:2d}  inertia={v:10.2f}")

    sys.exit(0)
