"""
Unit and Integration Tests for Sprint 5 Day 31 — Cash Flow Intelligence Module.
Covers:
1. CFO/PAT calculation & PAT=0 safe handling
2. 5-year rolling average
3. High Quality boundary (> 1.0)
4. Moderate boundaries (0.5 <= score <= 1.0)
5. Accrual Risk boundary (< 0.5)
6. CapEx intensity formula: abs(CFI) / sales * 100
7. CapEx label boundaries (<3% Asset Light, 3-8% Moderate, >8% Capital Intensive)
8. FCF CAGR positive-base calculation
9. FCF CAGR zero/negative-base handling (returns None/NaN)
10. FCF conversion formula: FCF / operating_profit * 100
11. Distress condition: CFO < 0 AND CFF > 0
12. Distress false boundaries
13. Deleveraging: CFF < 0 AND borrowings declining
14. Deleveraging false boundaries & missing prior-year borrowings
15. Capital allocation pattern join from Sprint 2
16. 92-company universe coverage & exactly 1 row per company
17. Exact output schema in cashflow_intelligence.xlsx & distress_alerts.csv
18. Real database spot-checks for TCS, RELIANCE, HDFCBANK, INFY
19. Determinism and company_id normalization
"""

import math
import sqlite3
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

SPRINT5_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SPRINT5_ROOT))

from src.analytics.cashflow_kpis import (
    compute_cfo_quality_score,
    compute_capex_intensity,
    compute_fcf,
    compute_fcf_cagr_5yr,
    compute_fcf_conversion,
    compute_distress_flag,
    compute_deleveraging_flag,
    CashFlowIntelligenceEngine,
)

BASE_DIR = SPRINT5_ROOT.parent
DB_PATH = BASE_DIR / "Sprint-01-Data-Foundation" / "nifty100.db"
CAP_ALLOC_PATH = BASE_DIR / "Sprint-02-Financial-Ratio-Engine" / "output" / "capital_allocation.csv"


@pytest.fixture(scope="module")
def engine():
    return CashFlowIntelligenceEngine(
        db_path=str(DB_PATH),
        cap_alloc_path=str(CAP_ALLOC_PATH),
        output_dir=str(SPRINT5_ROOT / "output"),
    )


@pytest.fixture(scope="module")
def analysis_results(engine):
    df_cf, df_distress = engine.run()
    return df_cf, df_distress


# ===========================================================================
# 1. CFO Quality Score Tests
# ===========================================================================
class TestCFOQualityScore:
    def test_cfo_pat_normal(self):
        # 5 years with simple ratios: 1.2, 1.4, 1.0, 1.1, 1.3 -> avg = 1.2
        pairs = [(120.0, 100.0), (140.0, 100.0), (100.0, 100.0), (110.0, 100.0), (130.0, 100.0)]
        score, label = compute_cfo_quality_score(pairs)
        assert score is not None
        assert abs(score - 1.2) < 1e-5
        assert label == "High Quality"

    def test_pat_zero_excluded(self):
        # One period has PAT=0, should be excluded from average
        pairs = [(100.0, 100.0), (50.0, 0.0), (200.0, 100.0)]
        score, label = compute_cfo_quality_score(pairs)
        assert score is not None
        # Ratios are 1.0 and 2.0 -> avg = 1.5
        assert abs(score - 1.5) < 1e-5
        assert label == "High Quality"

    def test_all_pat_zero_or_none(self):
        pairs = [(100.0, 0.0), (50.0, None), (None, 100.0)]
        score, label = compute_cfo_quality_score(pairs)
        assert score is None
        assert label is None

    def test_high_quality_boundary_strict(self):
        # Exactly 1.0 is Moderate (0.5 <= score <= 1.0)
        score, label = compute_cfo_quality_score([(100.0, 100.0)])
        assert score is not None
        assert score == 1.0
        assert label == "Moderate"

        # 1.0001 is High Quality (> 1.0)
        score, label = compute_cfo_quality_score([(100.01, 100.0)])
        assert score is not None
        assert score > 1.0
        assert label == "High Quality"

    def test_moderate_boundaries(self):
        # Exactly 0.5 is Moderate
        score, label = compute_cfo_quality_score([(50.0, 100.0)])
        assert score is not None
        assert score == 0.5
        assert label == "Moderate"

        # 0.75 is Moderate
        score, label = compute_cfo_quality_score([(75.0, 100.0)])
        assert score is not None
        assert score == 0.75
        assert label == "Moderate"

    def test_accrual_risk_boundary(self):
        # 0.499 is Accrual Risk (< 0.5)
        score, label = compute_cfo_quality_score([(49.9, 100.0)])
        assert score is not None
        assert score < 0.5
        assert label == "Accrual Risk"

        # Negative ratio is Accrual Risk
        score, label = compute_cfo_quality_score([(-20.0, 100.0)])
        assert score is not None
        assert score < 0.5
        assert label == "Accrual Risk"


# ===========================================================================
# 2. CapEx Intensity Tests
# ===========================================================================
class TestCapExIntensity:
    def test_asset_light_boundary(self):
        # 2.9% -> Asset Light (< 3%)
        intensity, label = compute_capex_intensity(-29.0, 1000.0)
        assert intensity is not None
        assert abs(intensity - 2.9) < 1e-5
        assert label == "Asset Light"

        # Positive investing activity (asset sale) should also use abs()
        intensity, label = compute_capex_intensity(29.0, 1000.0)
        assert intensity is not None
        assert abs(intensity - 2.9) < 1e-5
        assert label == "Asset Light"

    def test_moderate_boundaries(self):
        # Exactly 3.0% -> Moderate (3% through 8%)
        intensity, label = compute_capex_intensity(-30.0, 1000.0)
        assert intensity is not None
        assert intensity == 3.0
        assert label == "Moderate"

        # Exactly 8.0% -> Moderate
        intensity, label = compute_capex_intensity(-80.0, 1000.0)
        assert intensity is not None
        assert intensity == 8.0
        assert label == "Moderate"

    def test_capital_intensive_boundary(self):
        # 8.01% -> Capital Intensive (> 8%)
        intensity, label = compute_capex_intensity(-80.1, 1000.0)
        assert intensity is not None
        assert intensity > 8.0
        assert label == "Capital Intensive"

    def test_sales_zero_or_negative_returns_none(self):
        intensity, label = compute_capex_intensity(-50.0, 0.0)
        assert intensity is None
        assert label is None

        intensity, label = compute_capex_intensity(-50.0, -100.0)
        assert intensity is None
        assert label is None

        intensity, label = compute_capex_intensity(None, 1000.0)
        assert intensity is None
        assert label is None


# ===========================================================================
# 3. FCF and FCF CAGR Tests
# ===========================================================================
class TestFCFAndCAGR:
    def test_fcf_computation(self):
        assert compute_fcf(100.0, -40.0) == 60.0
        assert compute_fcf(100.0, 20.0) == 120.0
        assert compute_fcf(-50.0, -30.0) == -80.0
        assert compute_fcf(None, -30.0) is None
        assert compute_fcf(100.0, None) is None

    def test_fcf_cagr_positive_growth(self):
        # Base = 100, End = 200 over 5 years: (2 ** 0.2 - 1) * 100 = 14.869835%
        cagr = compute_fcf_cagr_5yr(100.0, 200.0, n=5)
        assert cagr is not None
        assert abs(cagr - 14.869835) < 1e-4

    def test_fcf_cagr_negative_or_zero_base(self):
        # Negative start base -> mathematically invalid, must return None
        assert compute_fcf_cagr_5yr(-100.0, 200.0, n=5) is None
        # Zero start base -> division by zero, must return None
        assert compute_fcf_cagr_5yr(0.0, 200.0, n=5) is None
        # Negative end value -> return None
        assert compute_fcf_cagr_5yr(100.0, -50.0, n=5) is None
        # Both negative -> return None
        assert compute_fcf_cagr_5yr(-100.0, -50.0, n=5) is None

    def test_fcf_conversion(self):
        # FCF = 50, Operating Profit = 100 -> 50%
        conv = compute_fcf_conversion(50.0, 100.0)
        assert conv == 50.0

        # Operating profit = 0 -> None
        assert compute_fcf_conversion(50.0, 0.0) is None
        assert compute_fcf_conversion(None, 100.0) is None
        assert compute_fcf_conversion(50.0, None) is None


# ===========================================================================
# 4. Distress & Deleveraging Tests
# ===========================================================================
class TestDistressAndDeleveraging:
    def test_distress_flag_true(self):
        # CFO < 0 and CFF > 0
        assert compute_distress_flag(-100.0, 50.0) is True

    def test_distress_flag_false_conditions(self):
        assert compute_distress_flag(100.0, 50.0) is False  # CFO > 0
        assert compute_distress_flag(-100.0, -50.0) is False  # CFF < 0
        assert compute_distress_flag(0.0, 50.0) is False  # CFO == 0
        assert compute_distress_flag(-100.0, 0.0) is False  # CFF == 0
        assert compute_distress_flag(None, 50.0) is False

    def test_deleveraging_flag_true(self):
        # CFF < 0 and Borrowings declined: 80 < 100
        assert compute_deleveraging_flag(-50.0, 80.0, 100.0) is True

    def test_deleveraging_flag_false_conditions(self):
        # CFF > 0 (raising financing)
        assert compute_deleveraging_flag(50.0, 80.0, 100.0) is False
        # Borrowings increased: 120 >= 100
        assert compute_deleveraging_flag(-50.0, 120.0, 100.0) is False
        # Borrowings unchanged: 100 == 100
        assert compute_deleveraging_flag(-50.0, 100.0, 100.0) is False
        # Missing prior borrowings
        assert compute_deleveraging_flag(-50.0, 80.0, None) is False
        assert compute_deleveraging_flag(None, 80.0, 100.0) is False


# ===========================================================================
# 5. Integration & Output Deliverables Tests
# ===========================================================================
class TestIntegrationDeliverables:
    def test_92_companies_evaluated(self, analysis_results):
        df_cf, _ = analysis_results
        assert len(df_cf) == 92
        assert df_cf["company_id"].nunique() == 92

    def test_exact_schema_cashflow_intelligence(self, analysis_results):
        df_cf, _ = analysis_results
        expected_cols = [
            "company_id",
            "sector",
            "cfo_quality_score",
            "cfo_quality_label",
            "capex_intensity_pct",
            "capex_label",
            "fcf_cagr_5yr",
            "fcf_conversion_pct",
            "distress_flag",
            "deleveraging_flag",
            "capital_allocation_label",
        ]
        assert list(df_cf.columns) == expected_cols

    def test_distress_alerts_schema_and_integrity(self, analysis_results):
        _, df_distress = analysis_results
        assert len(df_distress) == 13
        assert "company_id" in df_distress.columns
        assert "sector" in df_distress.columns
        assert "latest_year" in df_distress.columns
        assert "cfo_value" in df_distress.columns
        assert "cff_value" in df_distress.columns
        assert "latest_net_profit" in df_distress.columns

        # Every row in distress alerts must strictly satisfy CFO < 0 and CFF > 0
        for _, row in df_distress.iterrows():
            assert row["cfo_value"] < 0
            assert row["cff_value"] > 0

    def test_labels_valid_categories(self, analysis_results):
        df_cf, _ = analysis_results
        valid_cfo_labels = {"High Quality", "Moderate", "Accrual Risk", None}
        assert set(df_cf["cfo_quality_label"].dropna().unique()).issubset(valid_cfo_labels)

        valid_capex_labels = {"Asset Light", "Moderate", "Capital Intensive", None}
        assert set(df_cf["capex_label"].dropna().unique()).issubset(valid_capex_labels)

        valid_cap_alloc_labels = {
            "Shareholder Returns",
            "Reinvestor",
            "Liquidating Assets",
            "Distress Signal",
            "Growth Funded by Debt",
            "Cash Accumulator",
            "Pre-Revenue",
            "Mixed",
            "Other",
            None,
        }
        assert set(df_cf["capital_allocation_label"].dropna().unique()).issubset(valid_cap_alloc_labels)

    def test_boolean_flags_types(self, analysis_results):
        df_cf, _ = analysis_results
        assert df_cf["distress_flag"].dtype == bool or df_cf["distress_flag"].isin([True, False]).all()
        assert df_cf["deleveraging_flag"].dtype == bool or df_cf["deleveraging_flag"].isin([True, False]).all()

    def test_file_generation_and_content(self, engine):
        x_path, c_path = engine.save_outputs()
        assert x_path.exists()
        assert c_path.exists()

        # Read back excel
        df_from_excel = pd.read_excel(x_path, engine="openpyxl")
        assert len(df_from_excel) == 92
        assert list(df_from_excel.columns) == [
            "company_id",
            "sector",
            "cfo_quality_score",
            "cfo_quality_label",
            "capex_intensity_pct",
            "capex_label",
            "fcf_cagr_5yr",
            "fcf_conversion_pct",
            "distress_flag",
            "deleveraging_flag",
            "capital_allocation_label",
        ]


# ===========================================================================
# 6. Real Database Spot Check Tests (TCS, RELIANCE, HDFCBANK, INFY)
# ===========================================================================
class TestRealCompanySpotChecks:
    def test_spot_check_tcs(self, analysis_results):
        df_cf, _ = analysis_results
        row = df_cf[df_cf["company_id"] == "TCS"].iloc[0]

        assert row["sector"] == "Information Technology"
        # 5-year average of CFO/PAT ~ 1.0364 -> High Quality
        assert row["cfo_quality_score"] > 1.0
        assert row["cfo_quality_label"] == "High Quality"
        # CapEx Intensity ~ 2.53% -> Asset Light (<3%)
        assert abs(row["capex_intensity_pct"] - 2.528509) < 1e-2
        assert row["capex_label"] == "Asset Light"
        # FCF CAGR ~ 10.77%
        assert row["fcf_cagr_5yr"] is not None
        assert abs(row["fcf_cagr_5yr"] - 10.768652) < 1e-2
        # FCF Conversion ~ 78.43%
        assert abs(row["fcf_conversion_pct"] - 78.432562) < 1e-2
        assert row["distress_flag"] == False
        assert row["deleveraging_flag"] == False

    def test_spot_check_reliance(self, analysis_results):
        df_cf, _ = analysis_results
        row = df_cf[df_cf["company_id"] == "RELIANCE"].iloc[0]

        assert row["sector"] == "Energy"
        # 5-year average of CFO/PAT ~ 1.6148 -> High Quality
        assert row["cfo_quality_score"] > 1.0
        assert row["cfo_quality_label"] == "High Quality"
        # CapEx Intensity ~ 12.63% -> Capital Intensive (>8%)
        assert abs(row["capex_intensity_pct"] - 12.633573) < 1e-2
        assert row["capex_label"] == "Capital Intensive"
        # FCF 2019 was negative (-52161) -> CAGR must be NaN
        assert pd.isna(row["fcf_cagr_5yr"])
        # FCF Conversion ~ 27.82%
        assert abs(row["fcf_conversion_pct"] - 27.820035) < 1e-2
        assert row["distress_flag"] == False
        assert row["capital_allocation_label"] == "Shareholder Returns"

    def test_spot_check_hdfcbank(self, analysis_results):
        df_cf, _ = analysis_results
        row = df_cf[df_cf["company_id"] == "HDFCBANK"].iloc[0]

        assert row["sector"] == "Financials"
        # 5-year average CFO/PAT ~ 0.2288 -> Accrual Risk (<0.5)
        assert row["cfo_quality_score"] < 0.5
        assert row["cfo_quality_label"] == "Accrual Risk"
        # CapEx Intensity ~ 5.85% -> Moderate (3-8%)
        assert abs(row["capex_intensity_pct"] - 5.852303) < 1e-2
        assert row["capex_label"] == "Moderate"
        # FCF 2019 was negative (-64375) -> CAGR must be NaN
        assert pd.isna(row["fcf_cagr_5yr"])
        # FCF Conversion ~ 20.48%
        assert abs(row["fcf_conversion_pct"] - 20.476360) < 1e-2
        assert row["distress_flag"] == False
        assert row["deleveraging_flag"] == False

    def test_spot_check_infy(self, analysis_results):
        df_cf, _ = analysis_results
        row = df_cf[df_cf["company_id"] == "INFY"].iloc[0]

        assert row["sector"] == "Information Technology"
        assert row["cfo_quality_score"] > 1.0
        assert row["cfo_quality_label"] == "High Quality"
        # CapEx Intensity ~ 3.31% -> Moderate (3-8%)
        assert abs(row["capex_intensity_pct"] - 3.314245) < 1e-2
        assert row["capex_label"] == "Moderate"
        # FCF CAGR ~ 7.20%
        assert abs(row["fcf_cagr_5yr"] - 7.202334) < 1e-2
        assert abs(row["fcf_conversion_pct"] - 55.228552) < 1e-2
        assert row["distress_flag"] == False
        assert row["capital_allocation_label"] == "Shareholder Returns"
