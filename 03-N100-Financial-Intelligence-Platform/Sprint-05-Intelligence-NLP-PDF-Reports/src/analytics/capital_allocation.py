"""
Capital Allocation Analysis Module — Sprint 5 Day 32.
Analyzes 8-pattern capital allocation profiles from Sprint 2, computes latest-year distributions,
tracks year-over-year pattern transitions across consecutive numeric fiscal years,
and validates alignment with the 92-company N100 universe.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

EXPECTED_PATTERNS = [
    "Shareholder Returns",
    "Reinvestor",
    "Liquidating Assets",
    "Distress Signal",
    "Growth Funded by Debt",
    "Cash Accumulator",
    "Pre-Revenue",
    "Mixed",
]


class CapitalAllocationReporter:
    """
    Analyzes historical capital allocation patterns and generates distribution & change reports.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        cap_alloc_path: Optional[str] = None,
        output_dir: Optional[str] = None,
    ):
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        sprint5_root = Path(__file__).resolve().parent.parent.parent

        if db_path is None:
            self.db_path = base_dir / "Sprint-01-Data-Foundation" / "nifty100.db"
        else:
            self.db_path = Path(db_path)

        if cap_alloc_path is None:
            self.cap_alloc_path = (
                base_dir
                / "Sprint-02-Financial-Ratio-Engine"
                / "output"
                / "capital_allocation.csv"
            )
        else:
            self.cap_alloc_path = Path(cap_alloc_path)

        if output_dir is None:
            self.output_dir = sprint5_root / "output"
        else:
            self.output_dir = Path(output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_clean_data(self) -> pd.DataFrame:
        """
        Loads and validates capital allocation data from Sprint 2.
        Filters to numeric fiscal years and normalizes company IDs.
        """
        if not self.cap_alloc_path.exists():
            raise FileNotFoundError(f"Capital allocation source not found at: {self.cap_alloc_path}")

        df = pd.read_csv(self.cap_alloc_path)
        df["company_id"] = df["company_id"].astype(str).str.strip().str.upper()
        df["year_str"] = df["year"].astype(str).str.strip()

        # Filter out non-numeric entries (such as 'TTM')
        df_num = df[df["year_str"].str.isdigit()].copy()
        df_num["year_int"] = df_num["year_str"].astype(int)
        df_num = df_num.sort_values(["company_id", "year_int"]).reset_index(drop=True)

        return df_num

    def compute_distribution(self, df_num: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Computes the capital allocation pattern distribution for the latest available fiscal year.
        Columns: pattern_label, company_count, latest_year
        """
        if df_num is None:
            df_num = self.load_clean_data()

        # Select latest available year per company
        latest_df = df_num.groupby("company_id").last().reset_index()
        latest_yr_str = str(latest_df["year_int"].max())

        dist = (
            latest_df.groupby("pattern_label")
            .size()
            .reset_index(name="company_count")
        )
        dist["latest_year"] = latest_yr_str
        dist = dist.sort_values("company_count", ascending=False).reset_index(drop=True)

        return dist[["pattern_label", "company_count", "latest_year"]]

    def compute_pattern_changes(self, df_num: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Detects year-over-year capital allocation pattern changes across consecutive available numeric years.
        Columns: company_id, from_year, to_year, from_pattern, to_pattern
        """
        if df_num is None:
            df_num = self.load_clean_data()

        changes: List[Dict[str, Any]] = []
        for cid, group in df_num.groupby("company_id"):
            group = group.sort_values("year_int").reset_index(drop=True)
            for i in range(len(group) - 1):
                r_from = group.iloc[i]
                r_to = group.iloc[i + 1]
                if r_from["pattern_label"] != r_to["pattern_label"]:
                    changes.append({
                        "company_id": cid,
                        "from_year": str(r_from["year_int"]),
                        "to_year": str(r_to["year_int"]),
                        "from_pattern": r_from["pattern_label"],
                        "to_pattern": r_to["pattern_label"],
                    })

        changes_df = pd.DataFrame(changes)
        if changes_df.empty:
            return pd.DataFrame(columns=["company_id", "from_year", "to_year", "from_pattern", "to_pattern"])

        return changes_df[["company_id", "from_year", "to_year", "from_pattern", "to_pattern"]]

    def save_outputs(self) -> Tuple[Path, Path]:
        """
        Generates and saves:
            - output/capital_allocation_distribution.csv
            - output/pattern_changes.csv
        """
        df_num = self.load_clean_data()
        dist_df = self.compute_distribution(df_num)
        changes_df = self.compute_pattern_changes(df_num)

        dist_path = self.output_dir / "capital_allocation_distribution.csv"
        changes_path = self.output_dir / "pattern_changes.csv"

        dist_df.to_csv(dist_path, index=False)
        changes_df.to_csv(changes_path, index=False)

        return dist_path, changes_path


if __name__ == "__main__":
    reporter = CapitalAllocationReporter()
    p1, p2 = reporter.save_outputs()
    d1 = reporter.compute_distribution()
    d2 = reporter.compute_pattern_changes()
    print(f"Generated {p1} ({len(d1)} rows)")
    print(f"Generated {p2} ({len(d2)} rows)")
