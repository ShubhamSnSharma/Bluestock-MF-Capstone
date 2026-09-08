"""
Analytics module for Sprint 5 — Intelligence, NLP & PDF Reports.
Contains Cash Flow Intelligence KPI engine and Capital Allocation reporter.
"""

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
from src.analytics.capital_allocation import (
    CapitalAllocationReporter,
    EXPECTED_PATTERNS,
)

__all__ = [
    "compute_cfo_quality_score",
    "compute_capex_intensity",
    "compute_fcf",
    "compute_fcf_cagr_5yr",
    "compute_fcf_conversion",
    "compute_distress_flag",
    "compute_deleveraging_flag",
    "CashFlowIntelligenceEngine",
    "CapitalAllocationReporter",
    "EXPECTED_PATTERNS",
]
