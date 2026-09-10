"""
Sprint 6 — Day 40: Portfolio statistics endpoints.

Endpoints:
  GET /api/v1/portfolio/stats   — Portfolio statistics from Day 37 analysis
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])

PORTFOLIO_STATS_CSV = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "Sprint-06-API-Clustering-QA"
    / "output"
    / "portfolio_stats.csv"
)

CLUSTER_LABELS_CSV = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "Sprint-06-API-Clustering-QA"
    / "output"
    / "cluster_labels.csv"
)


class PortfolioStat(BaseModel):
    """Portfolio statistic for a single KPI."""

    metric: str
    metric_label: str
    n_valid: int
    n_missing: int
    p10: Optional[float] = None
    p25: Optional[float] = None
    p50: Optional[float] = None
    p75: Optional[float] = None
    p90: Optional[float] = None
    mean: Optional[float] = None
    std: Optional[float] = None


class ClusterInfo(BaseModel):
    """Cluster assignment for a company."""

    company_id: str
    cluster_id: int
    cluster_name: str
    distance_from_centroid: Optional[float] = None


@router.get("/stats", response_model=List[PortfolioStat])
def portfolio_stats():
    """Return portfolio-level statistics for all 10 KPIs (from Day 37)."""
    df = pd.read_csv(str(PORTFOLIO_STATS_CSV))
    return [PortfolioStat(**row) for _, row in df.iterrows()]


@router.get("/clusters", response_model=List[ClusterInfo])
def portfolio_clusters():
    """Return cluster assignments for all 92 companies (from Day 36)."""
    df = pd.read_csv(str(CLUSTER_LABELS_CSV))
    result = []
    for _, row in df.iterrows():
        result.append(
            ClusterInfo(
                company_id=row["company_id"],
                cluster_id=int(row["cluster_id"]),
                cluster_name=row["cluster_name"],
                distance_from_centroid=row.get("distance_from_centroid"),
            )
        )
    return result
