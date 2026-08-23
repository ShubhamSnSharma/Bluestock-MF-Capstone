"""
Financial Ratio Orchestration Engine.
Sprint 2 — Financial Ratio Engine
"""

import os
import shutil
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

from src.analytics.ratios import (
    compute_net_profit_margin,
    compute_operating_profit_margin,
    compute_return_on_equity,
    compute_return_on_capital_employed,
    compute_return_on_assets,
    compute_debt_to_equity,
    compute_interest_coverage,
    compute_net_debt,
    compute_asset_turnover,
)
from src.analytics.cagr import compute_series_cagr
from src.analytics.cashflow_kpis import (
    compute_free_cash_flow,
    compute_cfo_quality_score,
    compute_capex_intensity,
    compute_fcf_conversion_rate,
    classify_capital_allocation,
)


class RatioEngine:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Default to Sprint 1 database
            base_dir = Path(__file__).resolve().parent.parent.parent.parent
            self.db_path = base_dir / "Sprint-01-Data-Foundation" / "nifty100.db"
        else:
            self.db_path = Path(db_path)

        self.sprint2_root = Path(__file__).resolve().parent.parent.parent
        self.output_dir = self.sprint2_root / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.edge_cases: List[Dict[str, Any]] = []
        self.capital_allocations: List[Dict[str, Any]] = []

    def backup_database(self) -> Path:
        backup_path = Path("/tmp/nifty100_backup_sprint2.db")
        if self.db_path.exists():
            shutil.copy2(self.db_path, backup_path)
        return backup_path

    def ensure_financial_ratios_schema(self, conn: sqlite3.Connection):
        """Adds any required computed KPI columns to financial_ratios if missing."""
        cursor = conn.cursor()
        existing_cols = {c[1] for c in cursor.execute("PRAGMA table_info(financial_ratios)").fetchall()}

        new_cols = {
            "return_on_capital_employed_pct": "REAL",
            "return_on_assets_pct": "REAL",
            "icr_label": "TEXT",
            "high_leverage_flag": "INTEGER",
            "icr_warning_flag": "INTEGER",
            "net_debt": "REAL",
            "cfo_quality_score": "REAL",
            "cfo_quality_label": "TEXT",
            "capex_intensity_pct": "REAL",
            "capex_intensity_label": "TEXT",
            "fcf_conversion_pct": "REAL",
            "revenue_cagr_3yr": "REAL",
            "revenue_cagr_3yr_flag": "TEXT",
            "revenue_cagr_5yr": "REAL",
            "revenue_cagr_5yr_flag": "TEXT",
            "revenue_cagr_10yr": "REAL",
            "revenue_cagr_10yr_flag": "TEXT",
            "pat_cagr_3yr": "REAL",
            "pat_cagr_3yr_flag": "TEXT",
            "pat_cagr_5yr": "REAL",
            "pat_cagr_5yr_flag": "TEXT",
            "pat_cagr_10yr": "REAL",
            "pat_cagr_10yr_flag": "TEXT",
            "eps_cagr_3yr": "REAL",
            "eps_cagr_3yr_flag": "TEXT",
            "eps_cagr_5yr": "REAL",
            "eps_cagr_5yr_flag": "TEXT",
            "eps_cagr_10yr": "REAL",
            "eps_cagr_10yr_flag": "TEXT",
            "composite_quality_score": "REAL"
        }

        for col_name, col_type in new_cols.items():
            if col_name not in existing_cols:
                cursor.execute(f"ALTER TABLE financial_ratios ADD COLUMN {col_name} {col_type};")

        conn.commit()

    def run(self) -> Dict[str, Any]:
        """Runs the complete ratio engine and populates computed KPIs."""
        self.backup_database()

        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")

        self.ensure_financial_ratios_schema(conn)

        # 1. Load source datasets from SQLite
        companies_df = pd.read_sql_query("SELECT * FROM companies", conn)
        sectors_df = pd.read_sql_query("SELECT * FROM sectors", conn)
        pnl_df = pd.read_sql_query("SELECT * FROM profitandloss", conn)
        bs_df = pd.read_sql_query("SELECT * FROM balancesheet", conn)
        cf_df = pd.read_sql_query("SELECT * FROM cashflow", conn)
        fr_df = pd.read_sql_query("SELECT * FROM financial_ratios", conn)

        # Build sector lookup
        financial_companies = set(sectors_df[sectors_df["broad_sector"].str.strip() == "Financials"]["company_id"].tolist())

        # Master companies static snapshots
        comp_lookup = companies_df.set_index("id").to_dict(orient="index")

        # 2. Synchronize all valid company-year combinations from profitandloss (1,164 rows)
        existing_fr_keys = set(zip(fr_df["company_id"], fr_df["year"]))
        all_pnl_keys = set(zip(pnl_df["company_id"], pnl_df["year"]))

        missing_keys = all_pnl_keys - existing_fr_keys
        if missing_keys:
            cursor = conn.cursor()
            for cid, yr in sorted(missing_keys):
                cursor.execute(
                    "INSERT INTO financial_ratios (company_id, year) VALUES (?, ?);",
                    (cid, yr)
                )
            conn.commit()
            # Reload fr_df
            fr_df = pd.read_sql_query("SELECT * FROM financial_ratios", conn)

        # Index financial statement records by (company_id, year)
        pnl_map = pnl_df.set_index(["company_id", "year"]).to_dict(orient="index")
        bs_map = bs_df.set_index(["company_id", "year"]).to_dict(orient="index")
        cf_map = cf_df.set_index(["company_id", "year"]).to_dict(orient="index")

        # Precompute multi-year series per company for CAGR and CFO Quality
        companies_list = companies_df["id"].tolist()
        sales_series_by_comp: Dict[str, Dict[str, float]] = {c: {} for c in companies_list}
        pat_series_by_comp: Dict[str, Dict[str, float]] = {c: {} for c in companies_list}
        eps_series_by_comp: Dict[str, Dict[str, float]] = {c: {} for c in companies_list}
        cfo_series_by_comp: Dict[str, Dict[str, float]] = {c: {} for c in companies_list}

        for _, row in pnl_df.iterrows():
            cid = row["company_id"]
            yr = str(row["year"])
            if yr != "TTM":
                if pd.notnull(row.get("sales")):
                    sales_series_by_comp[cid][yr] = float(row["sales"])
                if pd.notnull(row.get("net_profit")):
                    pat_series_by_comp[cid][yr] = float(row["net_profit"])
                if pd.notnull(row.get("eps")):
                    eps_series_by_comp[cid][yr] = float(row["eps"])

        for _, row in cf_df.iterrows():
            cid = row["company_id"]
            yr = str(row["year"])
            if yr != "TTM":
                if pd.notnull(row.get("operating_activity")):
                    cfo_series_by_comp[cid][yr] = float(row["operating_activity"])

        # Compute all records
        computed_records = []
        raw_quality_scores = []

        for _, fr_row in fr_df.iterrows():
            cid = fr_row["company_id"]
            yr = str(fr_row["year"])
            key = (cid, yr)
            is_financial = (cid in financial_companies)

            pnl = pnl_map.get(key, {})
            bs = bs_map.get(key, {})
            cf = cf_map.get(key, {})

            # 1. Profitability Ratios
            sales = pnl.get("sales")
            operating_profit = pnl.get("operating_profit")
            other_income = pnl.get("other_income")
            net_profit = pnl.get("net_profit")
            reported_opm = pnl.get("opm_percentage")
            interest = pnl.get("interest")
            eps = pnl.get("eps")
            dividend_payout = pnl.get("dividend_payout")

            equity_capital = bs.get("equity_capital")
            reserves = bs.get("reserves")
            borrowings = bs.get("borrowings")
            total_assets = bs.get("total_assets")
            investments = bs.get("investments")

            cfo = cf.get("operating_activity")
            cfi = cf.get("investing_activity")
            cff = cf.get("financing_activity")

            npm = compute_net_profit_margin(net_profit, sales)
            opm, opm_anomaly = compute_operating_profit_margin(operating_profit, sales, reported_opm)
            if opm_anomaly:
                opm_anomaly["company_id"] = cid
                opm_anomaly["year"] = yr
                self.edge_cases.append(opm_anomaly)

            roe = compute_return_on_equity(net_profit, equity_capital, reserves)
            roce = compute_return_on_capital_employed(operating_profit, other_income, equity_capital, reserves, borrowings)
            roa = compute_return_on_assets(net_profit, total_assets)

            # Cross-check snapshot ROE / ROCE against master table for latest fiscal year
            if yr in ("2024", "TTM") and cid in comp_lookup:
                src_roce = comp_lookup[cid].get("roce_percentage")
                if roce is not None and src_roce is not None and pd.notnull(src_roce):
                    roce_diff = abs(roce - float(src_roce))
                    if roce_diff > 5.0:
                        self.edge_cases.append({
                            "company_id": cid,
                            "year": yr,
                            "metric": "ROCE",
                            "calculated_value": roce,
                            "source_value": float(src_roce),
                            "difference": roce_diff,
                            "category": "VERSION_DIFFERENCE" if not is_financial else "DATA_SOURCE_ISSUE",
                            "explanation": f"Calculated ROCE ({roce:.2f}%) differs from companies snapshot ({float(src_roce):.2f}%) by {roce_diff:.2f}% (snapshot based on TTM/different methodology)"
                        })

                src_roe = comp_lookup[cid].get("roe_percentage")
                if roe is not None and src_roe is not None and pd.notnull(src_roe):
                    src_roe_val = float(src_roe)
                    # Detect known anomalous source values (e.g. TCS 0.52% vs ~50% calculated)
                    if src_roe_val < 5.0 and roe > 25.0:
                        self.edge_cases.append({
                            "company_id": cid,
                            "year": yr,
                            "metric": "ROE",
                            "calculated_value": roe,
                            "source_value": src_roe_val,
                            "difference": abs(roe - src_roe_val),
                            "category": "DATA_SOURCE_ISSUE",
                            "explanation": f"Source snapshot ROE ({src_roe_val:.2f}%) appears corrupted/scaled in companies.xlsx; calculated ROE ({roe:.2f}%) is verified from audited statements"
                        })

            # 2. Leverage & Efficiency
            de_ratio, high_lev_flag = compute_debt_to_equity(borrowings, equity_capital, reserves, is_financial)
            icr, icr_label, icr_warning = compute_interest_coverage(operating_profit, other_income, interest)
            net_debt = compute_net_debt(borrowings, investments)
            asset_turnover = compute_asset_turnover(sales, total_assets)

            # 3. Cash Flow KPIs
            fcf = compute_free_cash_flow(cfo, cfi)

            # Compute 5-year rolling CFO Quality score
            cfo_pat_pairs = []
            if yr != "TTM" and yr.isdigit():
                current_yr_int = int(yr)
                for past_yr_int in range(current_yr_int - 4, current_yr_int + 1):
                    past_yr_str = str(past_yr_int)
                    cfo_val = cfo_series_by_comp[cid].get(past_yr_str)
                    pat_val = pat_series_by_comp[cid].get(past_yr_str)
                    if cfo_val is not None and pat_val is not None:
                        cfo_pat_pairs.append((cfo_val, pat_val))

            cfo_q_score, cfo_q_label = compute_cfo_quality_score(cfo_pat_pairs)
            capex_intensity, capex_label = compute_capex_intensity(cfi, sales)
            fcf_conv = compute_fcf_conversion_rate(fcf, operating_profit)

            # 4. Capital Allocation Classification
            s_cfo, s_cfi, s_cff, cap_alloc_label = classify_capital_allocation(cfo, cfi, cff, cfo_q_score)
            self.capital_allocations.append({
                "company_id": cid,
                "year": yr,
                "cfo_sign": s_cfo,
                "cfi_sign": s_cfi,
                "cff_sign": s_cff,
                "pattern_label": cap_alloc_label
            })

            # 5. CAGR Calculations
            rev_cagr_3, rev_flag_3 = compute_series_cagr(sales_series_by_comp[cid], yr, 3)
            rev_cagr_5, rev_flag_5 = compute_series_cagr(sales_series_by_comp[cid], yr, 5)
            rev_cagr_10, rev_flag_10 = compute_series_cagr(sales_series_by_comp[cid], yr, 10)

            pat_cagr_3, pat_flag_3 = compute_series_cagr(pat_series_by_comp[cid], yr, 3)
            pat_cagr_5, pat_flag_5 = compute_series_cagr(pat_series_by_comp[cid], yr, 5)
            pat_cagr_10, pat_flag_10 = compute_series_cagr(pat_series_by_comp[cid], yr, 10)

            eps_cagr_3, eps_flag_3 = compute_series_cagr(eps_series_by_comp[cid], yr, 3)
            eps_cagr_5, eps_flag_5 = compute_series_cagr(eps_series_by_comp[cid], yr, 5)
            eps_cagr_10, eps_flag_10 = compute_series_cagr(eps_series_by_comp[cid], yr, 10)

            # 6. Fallback line items if missing from source financial_ratios
            book_val_share = fr_row.get("book_value_per_share")
            if (pd.isnull(book_val_share) or book_val_share == 0) and equity_capital and reserves and cid in comp_lookup:
                fv = comp_lookup[cid].get("face_value")
                if fv and float(fv) > 0:
                    shares_cr = equity_capital / float(fv)
                    if shares_cr > 0:
                        book_val_share = (equity_capital + reserves) / shares_cr

            rec = {
                "id": fr_row["id"],
                "company_id": cid,
                "year": yr,
                "net_profit_margin_pct": npm if npm is not None else fr_row.get("net_profit_margin_pct"),
                "operating_profit_margin_pct": opm if opm is not None else fr_row.get("operating_profit_margin_pct"),
                "return_on_equity_pct": roe if roe is not None else fr_row.get("return_on_equity_pct"),
                "return_on_capital_employed_pct": roce,
                "return_on_assets_pct": roa,
                "debt_to_equity": de_ratio if de_ratio is not None else fr_row.get("debt_to_equity"),
                "interest_coverage": icr if icr is not None else fr_row.get("interest_coverage"),
                "icr_label": icr_label,
                "high_leverage_flag": 1 if high_lev_flag else 0,
                "icr_warning_flag": 1 if icr_warning else 0,
                "net_debt": net_debt,
                "asset_turnover": asset_turnover if asset_turnover is not None else fr_row.get("asset_turnover"),
                "free_cash_flow_cr": fcf if fcf is not None else fr_row.get("free_cash_flow_cr"),
                "capex_cr": abs(cfi) if cfi is not None else fr_row.get("capex_cr"),
                "earnings_per_share": eps if eps is not None else fr_row.get("earnings_per_share"),
                "book_value_per_share": book_val_share,
                "dividend_payout_ratio_pct": dividend_payout if dividend_payout is not None else fr_row.get("dividend_payout_ratio_pct"),
                "total_debt_cr": borrowings if borrowings is not None else fr_row.get("total_debt_cr"),
                "cash_from_operations_cr": cfo if cfo is not None else fr_row.get("cash_from_operations_cr"),
                "cfo_quality_score": cfo_q_score,
                "cfo_quality_label": cfo_q_label,
                "capex_intensity_pct": capex_intensity,
                "capex_intensity_label": capex_label,
                "fcf_conversion_pct": fcf_conv,
                "revenue_cagr_3yr": rev_cagr_3,
                "revenue_cagr_3yr_flag": rev_flag_3,
                "revenue_cagr_5yr": rev_cagr_5,
                "revenue_cagr_5yr_flag": rev_flag_5,
                "revenue_cagr_10yr": rev_cagr_10,
                "revenue_cagr_10yr_flag": rev_flag_10,
                "pat_cagr_3yr": pat_cagr_3,
                "pat_cagr_3yr_flag": pat_flag_3,
                "pat_cagr_5yr": pat_cagr_5,
                "pat_cagr_5yr_flag": pat_flag_5,
                "pat_cagr_10yr": pat_cagr_10,
                "pat_cagr_10yr_flag": pat_flag_10,
                "eps_cagr_3yr": eps_cagr_3,
                "eps_cagr_3yr_flag": eps_flag_3,
                "eps_cagr_5yr": eps_cagr_5,
                "eps_cagr_5yr_flag": eps_flag_5,
                "eps_cagr_10yr": eps_cagr_10,
                "eps_cagr_10yr_flag": eps_flag_10,
            }
            computed_records.append(rec)

        res_df = pd.DataFrame(computed_records)

        # 7. Compute Composite Quality Score (25% ROE + 25% Inv D/E + 25% CFO Quality + 25% 5Y Rev CAGR)
        # Calculate percentiles across dataset
        roe_clean = res_df["return_on_equity_pct"].fillna(res_df["return_on_equity_pct"].median())
        de_clean = res_df["debt_to_equity"].fillna(res_df["debt_to_equity"].median())
        inv_de = 1.0 / (1.0 + np.maximum(0.0, de_clean))
        cfo_q_clean = res_df["cfo_quality_score"].fillna(res_df["cfo_quality_score"].median())
        rev_cagr_clean = res_df["revenue_cagr_5yr"].fillna(res_df["revenue_cagr_5yr"].median())

        p_roe = roe_clean.rank(pct=True) * 100.0
        p_de = inv_de.rank(pct=True) * 100.0
        p_cfo = cfo_q_clean.rank(pct=True) * 100.0
        p_cagr = rev_cagr_clean.rank(pct=True) * 100.0

        res_df["composite_quality_score"] = (0.25 * p_roe + 0.25 * p_de + 0.25 * p_cfo + 0.25 * p_cagr).round(2)

        # 8. Update database financial_ratios table
        update_cols = [c for c in res_df.columns if c not in ("id", "company_id", "year")]
        set_clause = ", ".join([f"{col} = ?" for col in update_cols])
        sql = f"UPDATE financial_ratios SET {set_clause} WHERE id = ?;"

        cursor = conn.cursor()
        for _, row in res_df.iterrows():
            params = [row[col] if pd.notnull(row[col]) else None for col in update_cols] + [row["id"]]
            cursor.execute(sql, params)

        conn.commit()

        # 9. Generate output/capital_allocation.csv
        cap_alloc_df = pd.DataFrame(self.capital_allocations).drop_duplicates(subset=["company_id", "year"])
        cap_alloc_path = self.output_dir / "capital_allocation.csv"
        cap_alloc_df.to_csv(cap_alloc_path, index=False)

        # 10. Generate output/ratio_edge_cases.log
        log_path = self.output_dir / "ratio_edge_cases.log"
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("================================================================================\n")
            f.write("N100 FINANCIAL INTELLIGENCE PLATFORM — SPRINT 2 RATIO EDGE CASES & ANOMALIES LOG\n")
            f.write("================================================================================\n\n")
            f.write(f"Total Logged Anomalies: {len(self.edge_cases)}\n\n")
            f.write(f"{'Company':<12} | {'Year':<6} | {'Metric':<6} | {'Calculated':<10} | {'Source':<10} | {'Diff':<8} | {'Category':<22} | {'Explanation'}\n")
            f.write("-" * 120 + "\n")
            for ec in self.edge_cases:
                calc_s = f"{ec.get('calculated_value', 0):.2f}" if ec.get('calculated_value') is not None else "None"
                src_s = f"{ec.get('source_value', 0):.2f}" if ec.get('source_value') is not None else "None"
                diff_s = f"{ec.get('difference', 0):.2f}" if ec.get('difference') is not None else "N/A"
                f.write(f"{ec.get('company_id',''):<12} | {str(ec.get('year','')):<6} | {ec.get('metric',''):<6} | {calc_s:<10} | {src_s:<10} | {diff_s:<8} | {ec.get('category',''):<22} | {ec.get('explanation','')}\n")

        # 11. Final verification checks
        fk_errors = conn.execute("PRAGMA foreign_key_check").fetchall()
        fr_final_count = conn.execute("SELECT COUNT(*) FROM financial_ratios").fetchone()[0]
        comp_final_count = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]

        conn.close()

        return {
            "financial_ratios_count": fr_final_count,
            "companies_count": comp_final_count,
            "foreign_key_errors": len(fk_errors),
            "capital_allocation_rows": len(cap_alloc_df),
            "edge_case_log_count": len(self.edge_cases),
            "capital_allocation_path": str(cap_alloc_path),
            "ratio_edge_cases_path": str(log_path)
        }


if __name__ == "__main__":
    engine = RatioEngine()
    summary = engine.run()
    print("Sprint 2 Ratio Engine Execution Summary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
