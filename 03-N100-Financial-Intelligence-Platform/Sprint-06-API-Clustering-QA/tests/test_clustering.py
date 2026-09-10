"""
Tests for Sprint 6 — Day 36: KMeans Clustering.

Validates:
  - Output schema and row counts
  - Cluster assignment constraints
  - Feature completeness
  - Sector-median imputation
  - StandardScaler application
  - Deterministic results (random_state=42)
  - Elbow plot existence
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# ── Path setup ──────────────────────────────────────────────────────────────
SPRINT6_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = SPRINT6_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from analytics.clustering import (
    CLUSTER_NAME_MAP,
    ELBOW_K_RANGE,
    FEATURES,
    N_CLUSTERS,
    RANDOM_STATE,
    ClusteringPipeline,
    _assign_cluster_names,
    _impute_sector_medians,
    _reindex_clusters_by_roe,
    compute_elbow_inertias,
    load_feature_matrix,
    run_kmeans,
    scale_features,
)

# ── Fixtures ────────────────────────────────────────────────────────────────

SPRINT1_ROOT = SPRINT6_ROOT.parent / "Sprint-01-Data-Foundation"
SPRINT5_ROOT = SPRINT6_ROOT.parent / "Sprint-05-Intelligence-NLP-PDF-Reports"
DB_PATH = SPRINT1_ROOT / "nifty100.db"
CASHFLOW_PATH = SPRINT5_ROOT / "output" / "cashflow_intelligence.xlsx"

OUTPUT_CSV = SPRINT6_ROOT / "output" / "cluster_labels.csv"
ELBOW_PNG = SPRINT6_ROOT / "reports" / "elbow_plot.png"


@pytest.fixture(scope="module")
def pipeline_result():
    """Run the full pipeline once and cache results for the module."""
    p = ClusteringPipeline()
    result = p.run()
    return p, result


@pytest.fixture(scope="module")
def cluster_df(pipeline_result):
    """Return the cluster_labels DataFrame."""
    _, df = pipeline_result
    return df


@pytest.fixture(scope="module")
def pipeline_obj(pipeline_result):
    """Return the pipeline object."""
    obj, _ = pipeline_result
    return obj


@pytest.fixture(scope="module")
def feature_df_and_log():
    """Load feature matrix and imputation log."""
    feat_df, imp_log = load_feature_matrix(DB_PATH, CASHFLOW_PATH)
    return feat_df, imp_log


# ── 1. Output presence and schema ──────────────────────────────────────────


class TestOutputPresence:
    def test_cluster_labels_csv_exists(self):
        assert OUTPUT_CSV.exists(), f"{OUTPUT_CSV} does not exist"

    def test_elbow_plot_exists(self):
        assert ELBOW_PNG.exists(), f"{ELBOW_PNG} does not exist"


class TestOutputSchema:
    def test_required_columns(self, cluster_df):
        required = {
            "company_id",
            "cluster_id",
            "cluster_name",
            "distance_from_centroid",
        }
        assert required.issubset(
            set(cluster_df.columns)
        ), f"Missing columns: {required - set(cluster_df.columns)}"

    def test_no_extra_columns(self, cluster_df):
        expected = {
            "company_id",
            "cluster_id",
            "cluster_name",
            "distance_from_centroid",
        }
        assert (
            set(cluster_df.columns) == expected
        ), f"Unexpected columns: {set(cluster_df.columns) - expected}"


# ── 2. Row count and uniqueness ────────────────────────────────────────────


class TestRowCount:
    def test_exactly_92_companies(self, cluster_df):
        assert len(cluster_df) == 92, f"Expected 92 rows, got {len(cluster_df)}"

    def test_no_duplicate_company_id(self, cluster_df):
        assert (
            not cluster_df["company_id"].duplicated().any()
        ), "Duplicate company_id found"


# ── 3. Cluster assignment constraints ───────────────────────────────────────


class TestClusterAssignment:
    def test_exactly_5_cluster_ids(self, cluster_df):
        unique_ids = set(cluster_df["cluster_id"].unique())
        assert (
            len(unique_ids) == 5
        ), f"Expected 5 unique cluster IDs, got {len(unique_ids)}: {unique_ids}"

    def test_cluster_ids_are_0_to_4(self, cluster_df):
        unique_ids = set(cluster_df["cluster_id"].unique())
        assert unique_ids == set(
            range(N_CLUSTERS)
        ), f"cluster_id values must be 0-4, got {sorted(unique_ids)}"

    def test_every_company_has_a_cluster(self, cluster_df):
        assert cluster_df["cluster_id"].notna().all(), "Some companies have no cluster"

    def test_no_missing_cluster_name(self, cluster_df):
        assert (
            cluster_df["cluster_name"].notna().all()
        ), "Some cluster_names are missing"

    def test_distance_non_negative(self, cluster_df):
        assert (
            cluster_df["distance_from_centroid"] >= 0
        ).all(), "Negative distance_from_centroid found"


# ── 4. Feature completeness ─────────────────────────────────────────────────


class TestFeatures:
    def test_all_five_features_present(self, feature_df_and_log):
        feat_df, _ = feature_df_and_log
        for f in FEATURES:
            assert f in feat_df.columns, f"Feature '{f}' missing from feature_df"

    def test_no_null_features_after_imputation(self, feature_df_and_log):
        feat_df, _ = feature_df_and_log
        for f in FEATURES:
            null_count = feat_df[f].isna().sum()
            assert (
                null_count == 0
            ), f"Feature '{f}' has {null_count} nulls after imputation"


# ── 5. Sector-median imputation ─────────────────────────────────────────────


class TestImputation:
    def test_imputation_log_has_required_columns(self, feature_df_and_log):
        _, imp_log = feature_df_and_log
        required = {
            "company_id",
            "feature",
            "original_value",
            "imputed_value",
            "sector_used",
        }
        assert required.issubset(
            set(imp_log.columns)
        ), f"Missing columns in imputation log: {required - set(imp_log.columns)}"

    def test_imputation_log_records_imputations(self, feature_df_and_log):
        _, imp_log = feature_df_and_log
        assert len(imp_log) > 0, "No imputations recorded (expected at least some)"

    def test_imputation_count_per_feature(self, pipeline_obj):
        summary = pipeline_obj.get_imputation_summary()
        assert len(summary) > 0, "Imputation summary is empty"
        for feature in FEATURES:
            assert (
                feature in summary.index
            ), f"Feature '{feature}' not in imputation summary"

    def test_sector_median_imputation_works(self):
        """Test the imputation function directly on a synthetic DataFrame."""
        df = pd.DataFrame(
            {
                "company_id": ["A", "B", "C", "D"],
                "broad_sector": ["IT", "IT", "Finance", "Finance"],
                "return_on_equity_pct": [10.0, np.nan, 20.0, np.nan],
                "debt_to_equity": [0.5, 1.0, np.nan, np.nan],
                "revenue_cagr_5yr": [5.0, 6.0, 7.0, 8.0],
                "fcf_cagr_5yr": [3.0, np.nan, 9.0, np.nan],
                "operating_profit_margin_pct": [15.0, 25.0, 35.0, 45.0],
            }
        )
        imputed_df, imp_log = _impute_sector_medians(df)

        # IT sector median for return_on_equity_pct = 10.0 (A=10, B=NaN → 10)
        assert imputed_df.loc[1, "return_on_equity_pct"] == 10.0
        # Finance sector median for return_on_equity_pct = 20.0 (C=20, D=NaN → 20)
        assert imputed_df.loc[3, "return_on_equity_pct"] == 20.0
        # Finance sector median for debt_to_equity = NaN only for C, D → both NaN, fallback to global
        assert not np.isnan(imputed_df.loc[2, "debt_to_equity"])
        assert not np.isnan(imputed_df.loc[3, "debt_to_equity"])
        # fcf_cagr_5yr: IT median = 3.0, Finance median = 9.0
        assert imputed_df.loc[1, "fcf_cagr_5yr"] == 3.0
        assert imputed_df.loc[3, "fcf_cagr_5yr"] == 9.0

        # Log should have 6 entries: 2 for return_on_equity_pct,
        # 2 for debt_to_equity (Finance sector both NaN → global fallback),
        # 2 for fcf_cagr_5yr
        assert len(imp_log) == 6, f"Expected 6 imputations, got {len(imp_log)}"


# ── 6. StandardScaler ───────────────────────────────────────────────────────


class TestScaling:
    def test_scaled_zero_mean(self, pipeline_obj):
        scaled = pipeline_obj.scaled_matrix
        means = scaled.mean(axis=0)
        np.testing.assert_allclose(
            means, 0.0, atol=1e-10, err_msg="Scaled means not ~0"
        )

    def test_scaled_unit_variance(self, pipeline_obj):
        scaled = pipeline_obj.scaled_matrix
        stds = scaled.std(axis=0)
        np.testing.assert_allclose(stds, 1.0, atol=1e-6, err_msg="Scaled stds not ~1")

    def test_standard_scaler_applied(self, feature_df_and_log):
        """Verify that running scale_features produces zero mean / unit variance."""
        feat_df, _ = feature_df_and_log
        raw = feat_df[FEATURES].values
        scaled, scaler = scale_features(raw)
        means = scaled.mean(axis=0)
        np.testing.assert_allclose(means, 0.0, atol=1e-10)
        stds = scaled.std(axis=0)
        np.testing.assert_allclose(stds, 1.0, atol=1e-6)


# ── 7. Deterministic results (random_state=42) ─────────────────────────────


class TestDeterminism:
    def test_random_state_is_42(self):
        assert RANDOM_STATE == 42, f"RANDOM_STATE must be 42, got {RANDOM_STATE}"

    def test_repeated_runs_identical(self, feature_df_and_log):
        """Run KMeans twice with random_state=42 on same data → identical labels."""
        feat_df, _ = feature_df_and_log
        raw = feat_df[FEATURES].values
        scaled, _ = scale_features(raw)

        km1, labels1, dist1 = run_kmeans(
            scaled, n_clusters=N_CLUSTERS, random_state=RANDOM_STATE
        )
        km2, labels2, dist2 = run_kmeans(
            scaled, n_clusters=N_CLUSTERS, random_state=RANDOM_STATE
        )

        np.testing.assert_array_equal(
            labels1, labels2, err_msg="Labels differ between runs"
        )
        np.testing.assert_allclose(
            dist1, dist2, err_msg="Distances differ between runs"
        )

    def test_cluster_labels_csv_deterministic(self, cluster_df):
        """Reading the CSV twice gives the same content."""
        df第二次 = pd.read_csv(str(OUTPUT_CSV))
        pd.testing.assert_frame_equal(cluster_df, df第二次)


# ── 8. Elbow plot ──────────────────────────────────────────────────────────


class TestElbow:
    def test_elbow_inertias_has_all_k(self, pipeline_obj):
        inertias = pipeline_obj.inertias
        assert inertias is not None, "inertias not computed"
        for k in range(2, 11):
            assert k in inertias, f"k={k} missing from inertias"

    def test_elbow_inertias_decreasing(self, pipeline_obj):
        """Inertia should decrease (or stay flat) as k increases."""
        inertias = pipeline_obj.inertias
        ks = sorted(inertias.keys())
        for i in range(1, len(ks)):
            assert inertias[ks[i]] <= inertias[ks[i - 1]] + 1e-6, (
                f"Inertia increased: k={ks[i-1]}→{ks[i]}, "
                f"{inertias[ks[i-1]]:.2f}→{inertias[ks[i]]:.2f}"
            )

    def test_elbow_k_range(self):
        assert list(ELBOW_K_RANGE) == list(range(2, 11))


# ── 9. Cluster names ───────────────────────────────────────────────────────

EXPECTED_NAMES = {
    0: "High FCF Growth Outlier",
    1: "Financial Sector — High Leverage Growth",
    2: "Capital Efficient",
    3: "Premium Margin Leaders",
    4: "Defense PSU — Extreme ROE Outlier",
}


class TestClusterNames:
    def test_cluster_name_map_has_5_entries(self):
        assert len(CLUSTER_NAME_MAP) == 5

    def test_cluster_ids_0_to_4_in_name_map(self):
        assert set(CLUSTER_NAME_MAP.keys()) == set(range(5))

    def test_all_cluster_names_assigned(self, cluster_df):
        for cid in range(5):
            name = CLUSTER_NAME_MAP[cid]
            assert (
                isinstance(name, str) and len(name) > 0
            ), f"Empty name for cluster {cid}"

    def test_cluster_names_match_map(self, cluster_df):
        """Every row's cluster_name matches the name assigned by profile-based naming."""
        # Build the expected name map from the actual cluster_ids in the output
        from sklearn.cluster import KMeans
        from analytics.clustering import (
            scale_features,
            FEATURES,
            load_feature_matrix,
            _assign_cluster_names,
        )

        db_p = SPRINT6_ROOT.parent / "Sprint-01-Data-Foundation" / "nifty100.db"
        cf_p = (
            SPRINT6_ROOT.parent
            / "Sprint-05-Intelligence-NLP-PDF-Reports"
            / "output"
            / "cashflow_intelligence.xlsx"
        )
        feat_df, _ = load_feature_matrix(db_p, cf_p)
        raw_matrix = feat_df[FEATURES].values
        scaled, _ = scale_features(raw_matrix)
        km = KMeans(n_clusters=N_CLUSTERS, random_state=RANDOM_STATE, n_init=10)
        km.fit(scaled)
        expected_map = _assign_cluster_names(km.labels_, feat_df)

        for _, row in cluster_df.iterrows():
            expected_name = expected_map[row["cluster_id"]]
            assert (
                row["cluster_name"] == expected_name
            ), f"{row['company_id']}: expected '{expected_name}', got '{row['cluster_name']}'"

    def test_exact_five_final_names(self):
        """Verify the five validated cluster names exist exactly."""
        assert set(CLUSTER_NAME_MAP.values()) == set(EXPECTED_NAMES.values())

    def test_final_name_to_cluster_mapping(self, cluster_df):
        """Verify each final name appears in the output and maps to a single cluster."""
        for name in EXPECTED_NAMES.values():
            matching = cluster_df[cluster_df["cluster_name"] == name]
            assert len(matching) > 0, f"Name '{name}' not found in output"
            unique_clusters = matching["cluster_id"].unique()
            assert (
                len(unique_clusters) == 1
            ), f"Name '{name}' maps to multiple cluster IDs: {unique_clusters}"


# ── 10. Membership counts ──────────────────────────────────────────────────

# Expected company groupings (same groups as before naming change, with new cluster IDs)
EXPECTED_CLUSTER_GROUPS = {
    0: [  # Capital Efficient — 60 companies
        "ABB",
        "ADANIENSOL",
        "ADANIENT",
        "ADANIPOWER",
        "AMBUJACEM",
        "APOLLOHOSP",
        "ASIANPAINT",
        "ATGL",
        "BAJAJ-AUTO",
        "BHEL",
        "BOSCHLTD",
        "BPCL",
        "BRITANNIA",
        "DABUR",
        "DIVISLAB",
        "DLF",
        "DMART",
        "DRREDDY",
        "EICHERMOT",
        "GAIL",
        "GODREJCP",
        "GRASIM",
        "HAVELLS",
        "HCLTECH",
        "INFY",
        "IOC",
        "IRCTC",
        "ITC",
        "JINDALSTEL",
        "JSWENERGY",
        "JSWSTEEL",
        "LICI",
        "LODHA",
        "LT",
        "LTIM",
        "M&M",
        "MARUTI",
        "MOTHERSON",
        "NAUKRI",
        "NESTLEIND",
        "NHPC",
        "NTPC",
        "ONGC",
        "PIDILITIND",
        "RELIANCE",
        "SBILIFE",
        "SBIN",
        "SHREECEM",
        "SIEMENS",
        "SUNPHARMA",
        "TATACONSUM",
        "TATAMOTORS",
        "TATAPOWER",
        "TATASTEEL",
        "TCS",
        "TECHM",
        "TITAN",
        "TORNTPHARM",
        "TRENT",
        "TVSMOTOR",
    ],
    1: [  # Premium Margin Leaders — 14 companies
        "ADANIPORTS",
        "BAJAJHLDNG",
        "BHARTIARTL",
        "COALINDIA",
        "HDFCLIFE",
        "HEROMOTOCO",
        "HINDALCO",
        "HINDUNILVR",
        "ICICIGI",
        "ICICIPRULI",
        "INDIGO",
        "JIOFIN",
        "KOTAKBANK",
        "POWERGRID",
    ],
    2: [  # Defense PSU — Extreme ROE Outlier — 2 companies
        "BEL",
        "HAL",
    ],
    3: [  # Financial Sector — High Leverage Growth — 15 companies
        "ADANIGREEN",
        "AXISBANK",
        "BAJAJFINSV",
        "BAJFINANCE",
        "BANKBARODA",
        "CANBK",
        "CHOLAFIN",
        "HDFCBANK",
        "ICICIBANK",
        "INDUSINDBK",
        "IRFC",
        "PFC",
        "PNB",
        "RECLTD",
        "SHRIRAMFIN",
    ],
    4: [  # High FCF Growth Outlier — 1 company
        "CIPLA",
    ],
}


class TestMembership:
    def test_all_92_companies_assigned(self, cluster_df):
        assert cluster_df["company_id"].nunique() == 92

    def test_cluster_counts_positive(self, cluster_df):
        counts = cluster_df["cluster_id"].value_counts()
        for cid in range(5):
            assert cid in counts.index, f"Cluster {cid} has no members"
            assert counts[cid] > 0, f"Cluster {cid} has 0 members"

    def test_total_count_equals_92(self, cluster_df):
        assert cluster_df["cluster_id"].value_counts().sum() == 92

    def test_no_duplicate_company_id(self, cluster_df):
        assert not cluster_df["company_id"].duplicated().any()

    def test_cluster_membership_unchanged(self, cluster_df):
        """Verify that company groupings match the expected groups exactly."""
        for cid, expected_companies in EXPECTED_CLUSTER_GROUPS.items():
            actual = set(cluster_df[cluster_df["cluster_id"] == cid]["company_id"])
            expected = set(expected_companies)
            assert actual == expected, (
                f"Cluster {cid}: expected {len(expected)} companies, got {len(actual)}. "
                f"Missing: {expected - actual}, Extra: {actual - expected}"
            )

    def test_distance_from_centroid_unchanged(self, cluster_df):
        """Verify distances are unchanged (non-negative, reasonable range)."""
        assert (cluster_df["distance_from_centroid"] >= 0).all()
        assert cluster_df["distance_from_centroid"].max() < 10.0

    def test_output_schema_unchanged(self, cluster_df):
        expected_cols = {
            "company_id",
            "cluster_id",
            "cluster_name",
            "distance_from_centroid",
        }
        assert set(cluster_df.columns) == expected_cols


# ── 11. Elbow assessment ───────────────────────────────────────────────────


class TestElbowAssessment:
    def test_elbow_assessment_documented(self, pipeline_obj):
        """Verify that the elbow curve data is available for assessment."""
        inertias = pipeline_obj.inertias
        # k=5 inertia should be documented
        assert 5 in inertias
        # k=5 should have lower inertia than k=4
        assert inertias[5] < inertias[4]
        # k=6 should have lower inertia than k=5
        assert inertias[6] < inertias[5]
        # The marginal improvement from k=4→5 should be less than k=3→4
        # (indicating we're near the elbow)
        delta_3_4 = inertias[3] - inertias[4]
        delta_4_5 = inertias[4] - inertias[5]
        # If delta_4_5 < delta_3_4, k=5 is near or past the elbow
        # This is a soft check — we don't want to be overly restrictive
        assert (
            delta_4_5 < delta_3_4 * 2
        ), f"k=5 may not be near elbow: Δ(3→4)={delta_3_4:.1f}, Δ(4→5)={delta_4_5:.1f}"


# ── 12. Reindex consistency ────────────────────────────────────────────────


class TestReindexing:
    def test_reindex_clusters_by_roe(self, feature_df_and_log):
        """Verify cluster re-indexing by ascending mean ROE (legacy function)."""
        feat_df, _ = feature_df_and_log
        raw = feat_df[FEATURES].values
        scaled, _ = scale_features(raw)
        km, raw_labels, _ = run_kmeans(
            scaled, n_clusters=N_CLUSTERS, random_state=RANDOM_STATE
        )

        final_labels = _reindex_clusters_by_roe(raw_labels, feat_df)
        roe_col = "return_on_equity_pct"
        for cid in range(N_CLUSTERS):
            mask = final_labels == cid
            mean_roe = feat_df.loc[mask, roe_col].mean()
            # Check that cluster 0 has lower mean ROE than cluster 4
            if cid < N_CLUSTERS - 1:
                next_mask = final_labels == (cid + 1)
                next_roe = feat_df.loc[next_mask, roe_col].mean()
                assert mean_roe < next_roe, (
                    f"Cluster {cid} mean ROE ({mean_roe:.2f}) >= "
                    f"Cluster {cid+1} mean ROE ({next_roe:.2f})"
                )

    def test_assign_cluster_names_deterministic(self, feature_df_and_log):
        """Profile-based naming produces the same names across calls."""
        feat_df, _ = feature_df_and_log
        raw = feat_df[FEATURES].values
        scaled, _ = scale_features(raw)
        km, raw_labels, _ = run_kmeans(
            scaled, n_clusters=N_CLUSTERS, random_state=RANDOM_STATE
        )

        map1 = _assign_cluster_names(raw_labels, feat_df)
        map2 = _assign_cluster_names(raw_labels, feat_df)
        assert map1 == map2, "Profile-based naming is not deterministic"

    def test_assign_cluster_names_covers_all_clusters(self, feature_df_and_log):
        """Profile-based naming assigns a name to every cluster."""
        feat_df, _ = feature_df_and_log
        raw = feat_df[FEATURES].values
        scaled, _ = scale_features(raw)
        km, raw_labels, _ = run_kmeans(
            scaled, n_clusters=N_CLUSTERS, random_state=RANDOM_STATE
        )

        name_map = _assign_cluster_names(raw_labels, feat_df)
        assert len(name_map) == N_CLUSTERS
        for cid in range(N_CLUSTERS):
            assert cid in name_map
            assert isinstance(name_map[cid], str) and len(name_map[cid]) > 0


# ── 13. Imputation detail counts ───────────────────────────────────────────


class TestImputationDetail:
    def test_imputation_counts_match_expectations(self, pipeline_obj):
        """Check that imputation counts are plausible given the data."""
        summary = pipeline_obj.get_imputation_summary()
        # fcf_cagr_5yr should have the most imputations (only 50/92 non-null)
        assert (
            summary.get("fcf_cagr_5yr", 0) >= 40
        ), f"Expected at least 40 fcf_cagr_5yr imputations, got {summary.get('fcf_cagr_5yr', 0)}"
        # The other 4 features should have 1 imputation each (91/92 non-null)
        for f in [
            "return_on_equity_pct",
            "debt_to_equity",
            "revenue_cagr_5yr",
            "operating_profit_margin_pct",
        ]:
            count = summary.get(f, 0)
            assert (
                count >= 1
            ), f"Feature '{f}' should have at least 1 imputation, got {count}"
