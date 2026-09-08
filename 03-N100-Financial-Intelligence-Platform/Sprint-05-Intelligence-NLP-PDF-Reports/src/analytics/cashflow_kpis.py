"""
Cash Flow Intelligence Module — Sprint 5 Day 31.
Calculates CFO Quality, CapEx Intensity, FCF Growth & Conversion,
Distress Signals, Deleveraging Trends, and integrates Capital Allocation patterns.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
import pandas as pd


def compute_cfo_quality_score(
    cfo_pat_pairs: Sequence[Tuple[Optional[float], Optional[float]]]
) -> Tuple[Optional[float], Optional[str]]:
    """
    Computes CFO Quality Score as the 5-year average of (CFO / PAT).

    Parameters:
        cfo_pat_pairs: Sequence of (CFO, PAT) pairs over historical years (up to 5 years).

    Rules:
        - Ratio = CFO / PAT for each year.
        - If PAT == 0, the period is excluded to prevent division by zero.
        - Only valid numeric observations are averaged.
        - If no valid observations exist, returns (None, None).

    Labels:
        - score > 1.0: "High Quality"
        - 0.5 <= score <= 1.0: "Moderate"
        - score < 0.5: "Accrual Risk"
    """
    valid_ratios: List[float] = []
    for cfo, pat in cfo_pat_pairs:
        if (
            cfo is not None
            and pat is not None
            and pd.notna(cfo)
            and pd.notna(pat)
            and float(pat) != 0.0
        ):
            valid_ratios.append(float(cfo) / float(pat))

    if not valid_ratios:
        return None, None

    avg_score = sum(valid_ratios) / float(len(valid_ratios))

    if avg_score > 1.0:
        label = "High Quality"
    elif avg_score >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"

    return avg_score, label


def compute_capex_intensity(
    investing_activity: Optional[float],
    sales: Optional[float]
) -> Tuple[Optional[float], Optional[str]]:
    """
    Computes CapEx Intensity percentage: (abs(investing_activity) / sales) * 100.

    Parameters:
        investing_activity: Cash flow from investing activities (INR Cr).
        sales: Net sales / revenue from P&L (INR Cr).

    Labels:
        - < 3%: "Asset Light"
        - 3% through 8%: "Moderate"
        - > 8%: "Capital Intensive"

    Returns (None, None) if sales is missing or sales <= 0.
    """
    if (
        investing_activity is None
        or sales is None
        or pd.isna(investing_activity)
        or pd.isna(sales)
        or float(sales) <= 0.0
    ):
        return None, None

    intensity = (abs(float(investing_activity)) / float(sales)) * 100.0

    if intensity < 3.0:
        label = "Asset Light"
    elif intensity <= 8.0:
        label = "Moderate"
    else:
        label = "Capital Intensive"

    return intensity, label


def compute_fcf(
    cfo: Optional[float],
    cfi: Optional[float]
) -> Optional[float]:
    """
    Computes Free Cash Flow (FCF) in INR Cr: operating_activity + investing_activity.
    Returns None if either component is missing.
    """
    if cfo is None or cfi is None or pd.isna(cfo) or pd.isna(cfi):
        return None
    return float(cfo) + float(cfi)


def compute_fcf_cagr_5yr(
    fcf_base: Optional[float],
    fcf_latest: Optional[float],
    n: int = 5
) -> Optional[float]:
    """
    Computes 5-year Compound Annual Growth Rate for Free Cash Flow:
        ((FCF_latest / FCF_base) ** (1 / n) - 1) * 100

    Edge Cases:
        - Returns None (NaN) if fcf_base is <= 0 (non-positive starting base is mathematically invalid for CAGR).
        - Returns None (NaN) if fcf_latest is <= 0 or either value is missing/None.
    """
    if (
        fcf_base is None
        or fcf_latest is None
        or pd.isna(fcf_base)
        or pd.isna(fcf_latest)
        or n <= 0
    ):
        return None

    fcf_b = float(fcf_base)
    fcf_l = float(fcf_latest)

    if fcf_b <= 0.0 or fcf_l <= 0.0:
        return None

    return (((fcf_l / fcf_b) ** (1.0 / float(n))) - 1.0) * 100.0


def compute_fcf_conversion(
    fcf: Optional[float],
    operating_profit: Optional[float]
) -> Optional[float]:
    """
    Computes FCF Conversion Rate percentage: (FCF / operating_profit) * 100.
    Returns None if operating_profit is missing or operating_profit == 0.
    """
    if (
        fcf is None
        or operating_profit is None
        or pd.isna(fcf)
        or pd.isna(operating_profit)
        or float(operating_profit) == 0.0
    ):
        return None

    return (float(fcf) / float(operating_profit)) * 100.0


def compute_distress_flag(
    cfo: Optional[float],
    cff: Optional[float]
) -> bool:
    """
    Computes distress signal for latest available year:
        distress_flag = True when CFO < 0 AND CFF > 0.
    Interpretation: company is raising financing cash while operating activities consume cash.
    """
    if cfo is None or cff is None or pd.isna(cfo) or pd.isna(cff):
        return False
    return bool(float(cfo) < 0.0 and float(cff) > 0.0)


def compute_deleveraging_flag(
    cff: Optional[float],
    borrowings_latest: Optional[float],
    borrowings_prev: Optional[float]
) -> bool:
    """
    Computes deleveraging flag for latest available year:
        deleveraging_flag = True when CFF < 0 AND borrowings_latest < borrowings_prev.
    If prior borrowings value is unavailable or any value is missing: returns False.
    """
    if (
        cff is None
        or borrowings_latest is None
        or borrowings_prev is None
        or pd.isna(cff)
        or pd.isna(borrowings_latest)
        or pd.isna(borrowings_prev)
    ):
        return False

    return bool(float(cff) < 0.0 and float(borrowings_latest) < float(borrowings_prev))


class CashFlowIntelligenceEngine:
    """
    Orchestrates Cash Flow Intelligence KPI generation across the 92-company N100 universe.
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

    def run(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Executes Cash Flow Intelligence KPI analysis and returns:
            (cashflow_intelligence_df, distress_alerts_df)
        """
        conn = sqlite3.connect(str(self.db_path))

        # 1. Load source datasets
        companies_df = pd.read_sql("SELECT id, company_name FROM companies", conn)
        sectors_df = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
        pnl_df = pd.read_sql(
            "SELECT company_id, year, sales, operating_profit, net_profit FROM profitandloss",
            conn,
        )
        bs_df = pd.read_sql(
            "SELECT company_id, year, borrowings FROM balancesheet", conn
        )
        cf_df = pd.read_sql(
            "SELECT company_id, year, operating_activity, investing_activity, financing_activity, net_cash_flow FROM cashflow",
            conn,
        )
        conn.close()

        # 2. Normalize company IDs
        for df in [companies_df, sectors_df, pnl_df, bs_df, cf_df]:
            id_col = "id" if "id" in df.columns and "company_id" not in df.columns else "company_id"
            df[id_col] = df[id_col].astype(str).str.strip().str.upper()

        # Build sector map
        sector_map = sectors_df.set_index("company_id")["broad_sector"].to_dict()

        # 3. Capital allocation lookup from Sprint 2
        cap_alloc_map: Dict[Tuple[str, str], str] = {}
        if self.cap_alloc_path.exists():
            cap_df = pd.read_csv(self.cap_alloc_path)
            cap_df["company_id"] = cap_df["company_id"].astype(str).str.strip().str.upper()
            cap_df["year"] = cap_df["year"].astype(str).str.strip()
            # Prefer numeric fiscal years
            cap_df_num = cap_df[cap_df["year"].str.isdigit()].copy()
            cap_alloc_map = cap_df_num.set_index(["company_id", "year"])[
                "pattern_label"
            ].to_dict()

        # 4. Multi-year mappings
        pnl_map = pnl_df.set_index(["company_id", "year"]).to_dict(orient="index")
        bs_map = bs_df.set_index(["company_id", "year"]).to_dict(orient="index")
        cf_map = cf_df.set_index(["company_id", "year"]).to_dict(orient="index")

        # 5. Compute KPIs for all 92 companies
        all_companies = sorted(companies_df["id"].unique().tolist())
        rows: List[Dict[str, Any]] = []
        distress_rows: List[Dict[str, Any]] = []

        for cid in all_companies:
            sector = sector_map.get(cid)

            # Determine available fiscal years for this company in cashflow
            cf_years = sorted(
                [int(y) for (c, y) in cf_map.keys() if c == cid and str(y).isdigit()]
            )
            if not cf_years:
                latest_yr_int = 2024
                latest_yr_str = "2024"
            else:
                latest_yr_int = max(cf_years)
                latest_yr_str = str(latest_yr_int)

            # 5.1 CFO Quality Score: 5-year average of CFO / PAT up to latest_yr_int
            cfo_pat_pairs: List[Tuple[Optional[float], Optional[float]]] = []
            for y_int in range(latest_yr_int - 4, latest_yr_int + 1):
                y_str = str(y_int)
                cfo_val = cf_map.get((cid, y_str), {}).get("operating_activity")
                pat_val = pnl_map.get((cid, y_str), {}).get("net_profit")
                cfo_pat_pairs.append((cfo_val, pat_val))

            cfo_quality_score, cfo_quality_label = compute_cfo_quality_score(cfo_pat_pairs)

            # 5.2 CapEx Intensity (latest available fiscal year)
            latest_cf = cf_map.get((cid, latest_yr_str), {})
            latest_pnl = pnl_map.get((cid, latest_yr_str), {})

            inv_act = latest_cf.get("investing_activity")
            sales_val = latest_pnl.get("sales")
            capex_intensity_pct, capex_label = compute_capex_intensity(inv_act, sales_val)

            # 5.3 FCF CAGR 5-yr (latest year t vs t-5)
            base_yr_str = str(latest_yr_int - 5)
            cf_base = cf_map.get((cid, base_yr_str), {})
            fcf_base = compute_fcf(
                cf_base.get("operating_activity"),
                cf_base.get("investing_activity"),
            )
            fcf_latest = compute_fcf(
                latest_cf.get("operating_activity"),
                latest_cf.get("investing_activity"),
            )
            fcf_cagr_5yr = compute_fcf_cagr_5yr(fcf_base, fcf_latest, n=5)

            # 5.4 FCF Conversion % (latest available fiscal year)
            op_profit = latest_pnl.get("operating_profit")
            fcf_conversion_pct = compute_fcf_conversion(fcf_latest, op_profit)

            # 5.5 Distress Flag
            cfo_latest = latest_cf.get("operating_activity")
            cff_latest = latest_cf.get("financing_activity")
            distress_flag = compute_distress_flag(cfo_latest, cff_latest)

            if distress_flag:
                distress_rows.append({
                    "company_id": cid,
                    "sector": sector,
                    "latest_year": latest_yr_str,
                    "cfo_value": cfo_latest,
                    "cff_value": cff_latest,
                    "latest_net_profit": latest_pnl.get("net_profit"),
                    "reason": "Operating cash flow is negative while financing cash flow is positive (operations consuming cash funded via external financing)",
                })

            # 5.6 Deleveraging Flag
            # Compare latest year borrowings with immediately preceding available year
            bs_years = sorted(
                [int(y) for (c, y) in bs_map.keys() if c == cid and str(y).isdigit()]
            )
            borrowings_latest = bs_map.get((cid, latest_yr_str), {}).get("borrowings")
            # Immediately preceding available year <= latest_yr_int - 1
            prev_bs_years = [y for y in bs_years if y < latest_yr_int]
            borrowings_prev = None
            if prev_bs_years:
                prev_yr_str = str(max(prev_bs_years))
                borrowings_prev = bs_map.get((cid, prev_yr_str), {}).get("borrowings")

            deleveraging_flag = compute_deleveraging_flag(
                cff_latest, borrowings_latest, borrowings_prev
            )

            # 5.7 Capital Allocation Label
            capital_allocation_label = cap_alloc_map.get((cid, latest_yr_str))

            rows.append({
                "company_id": cid,
                "sector": sector,
                "cfo_quality_score": cfo_quality_score,
                "cfo_quality_label": cfo_quality_label,
                "capex_intensity_pct": capex_intensity_pct,
                "capex_label": capex_label,
                "fcf_cagr_5yr": fcf_cagr_5yr,
                "fcf_conversion_pct": fcf_conversion_pct,
                "distress_flag": distress_flag,
                "deleveraging_flag": deleveraging_flag,
                "capital_allocation_label": capital_allocation_label,
            })

        cf_intel_df = pd.DataFrame(rows)
        distress_df = pd.DataFrame(distress_rows)

        return cf_intel_df, distress_df

    def save_outputs(self) -> Tuple[Path, Path]:
        """
        Executes analysis and writes outputs to disk:
            - output/cashflow_intelligence.xlsx
            - output/distress_alerts.csv
        """
        cf_intel_df, distress_df = self.run()

        xlsx_path = self.output_dir / "cashflow_intelligence.xlsx"
        csv_path = self.output_dir / "distress_alerts.csv"

        # Save Excel with formatting
        cf_intel_df.to_excel(xlsx_path, index=False, engine="openpyxl")
        distress_df.to_csv(csv_path, index=False)

        return xlsx_path, csv_path


if __name__ == "__main__":
    engine = CashFlowIntelligenceEngine()
    x_path, c_path = engine.save_outputs()
    df, d_df = engine.run()
    print(f"Generated {x_path} ({len(df)} rows)")
    print(f"Generated {c_path} ({len(d_df)} rows)")
