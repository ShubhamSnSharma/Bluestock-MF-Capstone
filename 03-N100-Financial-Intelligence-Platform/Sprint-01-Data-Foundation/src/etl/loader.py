"""
N100 Financial Intelligence Platform — ETL Loader Pipeline
Orchestrates full ingestion across all 12 source files, applying normalization,
deduplication, DQ validation, strict foreign-key verification, and audit logging.
"""

import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import numpy as np

from src.etl.normaliser import (
    normalize_ticker,
    normalize_year,
    clean_company_name,
    clean_url,
    clean_numeric,
    deduplicate_dataframe
)
from src.etl.validator import DataQualityValidator


def resolve_base_dir(custom_base: Optional[str] = None) -> Path:
    """Dynamically resolves project base directory whether executed from repo root or sprint directory."""
    if custom_base:
        p = Path(custom_base)
        if p.exists():
            return p

    # Check current working directory
    if Path("core datasets").exists() and Path("db/schema.sql").exists():
        return Path(".")

    # Check Sprint 1 path from repo root
    sprint_path = Path("03-N100-Financial-Intelligence-Platform/Sprint-01-Data-Foundation")
    if (sprint_path / "core datasets").exists():
        return sprint_path

    # Check platform root fallback
    platform_path = Path("03-N100-Financial-Intelligence-Platform")
    if (platform_path / "core datasets").exists():
        return platform_path

    return Path(".")


class N100DataLoader:
    """
    Manages complete ETL lifecycle from raw Excel files to SQLite database.
    """

    def __init__(
        self,
        base_dir: Optional[str] = None,
        db_filename: str = "nifty100.db"
    ):
        self.base_dir = resolve_base_dir(base_dir)
        self.core_dir = self.base_dir / "core datasets"
        self.supp_dir = self.base_dir / "supporting datasets"
        self.db_path = self.base_dir / db_filename
        self.schema_path = self.base_dir / "db" / "schema.sql"
        self.output_dir = self.base_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.validator = DataQualityValidator()
        self.audit_log: List[Dict[str, Any]] = []
        self.valid_company_ids: set = set()

    def init_database(self) -> sqlite3.Connection:
        """Initializes SQLite database with foreign keys enabled and applies schema."""
        if self.db_path.exists():
            self.db_path.unlink()

        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON;")

        with open(self.schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
        conn.commit()
        return conn

    def load_companies(self, conn: sqlite3.Connection) -> pd.DataFrame:
        """Loads, cleans, and inserts master companies table."""
        file_path = self.core_dir / "companies.xlsx"
        raw_df = pd.read_excel(file_path, header=1)
        raw_count = len(raw_df)

        clean_rows = []
        for idx, row in raw_df.iterrows():
            cid = normalize_ticker(row.get("id"))
            cname = clean_company_name(row.get("company_name"))
            logo = clean_url(row.get("company_logo"))
            chart = clean_url(row.get("chart_link"))
            about = str(row.get("about_company", "")).strip()
            web = clean_url(row.get("website"))
            nse = clean_url(row.get("nse_profile"))
            bse = clean_url(row.get("bse_profile"))
            fv = clean_numeric(row.get("face_value"))
            bv = clean_numeric(row.get("book_value"))
            roce = clean_numeric(row.get("roce_percentage"))
            roe = clean_numeric(row.get("roe_percentage"))

            clean_rows.append({
                "id": cid,
                "company_name": cname,
                "company_logo": logo,
                "chart_link": chart,
                "about_company": about,
                "website": web,
                "nse_profile": nse,
                "bse_profile": bse,
                "face_value": fv,
                "book_value": bv,
                "roce_percentage": roce,
                "roe_percentage": roe
            })

        df = pd.DataFrame(clean_rows)
        # Validate DQ
        self.validator.validate_dq01_primary_key_uniqueness(df, "companies", "id")
        self.validator.validate_dq10_url_syntax(df, "companies", ["website", "company_logo", "chart_link"])

        # Insert into database
        df.to_sql("companies", conn, if_exists="append", index=False)
        conn.commit()

        self.valid_company_ids = set(df["id"].dropna().tolist())
        accepted_count = len(df)

        self.audit_log.append({
            "table_name": "companies",
            "raw_source_records": raw_count,
            "normalized_records": len(clean_rows),
            "accepted_db_records": accepted_count,
            "orphan_rejected_records": 0,
            "duplicate_rejected_records": 0,
            "total_rejected_records": 0,
            "status": "SUCCESS"
        })
        return df

    def _process_child_table(
        self,
        conn: sqlite3.Connection,
        table_name: str,
        file_path: Path,
        header_row: int,
        transform_fn,
        natural_keys: List[str]
    ):
        """Generic processor for child tables handling normalization, DQ, filtering, and insertion."""
        raw_df = pd.read_excel(file_path, header=header_row)
        raw_count = len(raw_df)

        # Apply transformation
        clean_df = transform_fn(raw_df)
        norm_count = len(clean_df)

        # 1. Foreign Key Validation & Orphan Identification
        orphan_mask = ~clean_df["company_id"].isin(self.valid_company_ids)
        orphans_df = clean_df[orphan_mask]
        orphan_count = len(orphans_df)

        for idx, row in orphans_df.iterrows():
            self.validator.log_failure(
                "DQ-03", table_name, f"ID:{row.get('id', idx)}", "company_id",
                row.get("company_id"), "CRITICAL",
                f"Rejected orphan record: company_id '{row.get('company_id')}' not found in companies table."
            )

        valid_fk_df = clean_df[~orphan_mask].copy()

        # 2. Deduplication on composite natural keys
        dup_count = 0
        if natural_keys:
            dedup_df, dup_audit = deduplicate_dataframe(valid_fk_df, natural_keys, table_name)
            dup_count = len(dup_audit)
            for item in dup_audit:
                self.validator.log_failure(
                    "DQ-02", table_name, item["row_identifier"], "+".join(natural_keys),
                    item["row_identifier"], "CRITICAL", item["rejection_reason"]
                )
        else:
            dedup_df = valid_fk_df

        # 3. Table-Specific Data Quality Validation
        self.validator.validate_dq01_primary_key_uniqueness(dedup_df, table_name, "id")

        if table_name == "profitandloss":
            self.validator.validate_dq05_opm_cross_check(dedup_df)
            self.validator.validate_dq06_positive_sales(dedup_df)
            self.validator.validate_dq08_tax_rate_sanity(dedup_df)
            self.validator.validate_dq09_dividend_payout_bounds(dedup_df, table_name, "dividend_payout")
            self.validator.validate_dq11_eps_sign_consistency(dedup_df)
            self.validator.validate_dq14_year_coverage_continuity(dedup_df, table_name)
        elif table_name == "balancesheet":
            self.validator.validate_dq04_balancesheet_balance(dedup_df)
            self.validator.validate_dq12_asset_components(dedup_df)
            self.validator.validate_dq13_liability_components(dedup_df)
        elif table_name == "cashflow":
            self.validator.validate_dq07_net_cash_flow_sum(dedup_df)
        elif table_name == "stock_prices":
            self.validator.validate_dq15_stock_prices_range(dedup_df)
        elif table_name == "sectors":
            self.validator.validate_dq16_sector_index_weight_bounds(dedup_df)
        elif table_name == "documents":
            self.validator.validate_dq10_url_syntax(dedup_df, table_name, ["annual_report"])

        # 4. Insert accepted records into SQLite
        dedup_df.to_sql(table_name, conn, if_exists="append", index=False)
        conn.commit()

        accepted_count = len(dedup_df)
        total_rejected = orphan_count + dup_count

        self.audit_log.append({
            "table_name": table_name,
            "raw_source_records": raw_count,
            "normalized_records": norm_count,
            "accepted_db_records": accepted_count,
            "orphan_rejected_records": orphan_count,
            "duplicate_rejected_records": dup_count,
            "total_rejected_records": total_rejected,
            "status": "SUCCESS"
        })

    def run_pipeline(self) -> sqlite3.Connection:
        """Executes full ETL pipeline across all 12 source files."""
        conn = self.init_database()

        # 1. Master Table: Companies
        self.load_companies(conn)

        # 2. Child Table: Profit & Loss
        def transform_pnl(df):
            rows = []
            for idx, r in df.iterrows():
                rows.append({
                    "id": int(r["id"]),
                    "company_id": normalize_ticker(r["company_id"]),
                    "year": normalize_year(r["year"]),
                    "sales": clean_numeric(r["sales"]),
                    "expenses": clean_numeric(r["expenses"]),
                    "operating_profit": clean_numeric(r["operating_profit"]),
                    "opm_percentage": clean_numeric(r["opm_percentage"]),
                    "other_income": clean_numeric(r["other_income"]),
                    "interest": clean_numeric(r["interest"]),
                    "depreciation": clean_numeric(r["depreciation"]),
                    "profit_before_tax": clean_numeric(r["profit_before_tax"]),
                    "tax_percentage": clean_numeric(r["tax_percentage"]),
                    "net_profit": clean_numeric(r["net_profit"]),
                    "eps": clean_numeric(r["eps"]),
                    "dividend_payout": clean_numeric(r["dividend_payout"])
                })
            return pd.DataFrame(rows)
        self._process_child_table(conn, "profitandloss", self.core_dir / "profitandloss.xlsx", 1, transform_pnl, ["company_id", "year"])

        # 3. Child Table: Balance Sheet
        def transform_bs(df):
            rows = []
            for idx, r in df.iterrows():
                rows.append({
                    "id": int(r["id"]),
                    "company_id": normalize_ticker(r["company_id"]),
                    "year": normalize_year(r["year"]),
                    "equity_capital": clean_numeric(r["equity_capital"]),
                    "reserves": clean_numeric(r["reserves"]),
                    "borrowings": clean_numeric(r["borrowings"]),
                    "other_liabilities": clean_numeric(r["other_liabilities"]),
                    "total_liabilities": clean_numeric(r["total_liabilities"]),
                    "fixed_assets": clean_numeric(r["fixed_assets"]),
                    "cwip": clean_numeric(r["cwip"]),
                    "investments": clean_numeric(r["investments"]),
                    "other_asset": clean_numeric(r["other_asset"]),
                    "total_assets": clean_numeric(r["total_assets"])
                })
            return pd.DataFrame(rows)
        self._process_child_table(conn, "balancesheet", self.core_dir / "balancesheet.xlsx", 1, transform_bs, ["company_id", "year"])

        # 4. Child Table: Cash Flow
        def transform_cf(df):
            rows = []
            for idx, r in df.iterrows():
                rows.append({
                    "id": int(r["id"]),
                    "company_id": normalize_ticker(r["company_id"]),
                    "year": normalize_year(r["year"]),
                    "operating_activity": clean_numeric(r["operating_activity"]),
                    "investing_activity": clean_numeric(r["investing_activity"]),
                    "financing_activity": clean_numeric(r["financing_activity"]),
                    "net_cash_flow": clean_numeric(r["net_cash_flow"])
                })
            return pd.DataFrame(rows)
        self._process_child_table(conn, "cashflow", self.core_dir / "cashflow.xlsx", 1, transform_cf, ["company_id", "year"])

        # 5. Child Table: Analysis
        def transform_analysis(df):
            rows = []
            for idx, r in df.iterrows():
                rows.append({
                    "id": int(r["id"]),
                    "company_id": normalize_ticker(r["company_id"]),
                    "compounded_sales_growth": str(r.get("compounded_sales_growth", "")).strip(),
                    "compounded_profit_growth": str(r.get("compounded_profit_growth", "")).strip(),
                    "stock_price_cagr": str(r.get("stock_price_cagr", "")).strip(),
                    "roe": str(r.get("roe", "")).strip()
                })
            return pd.DataFrame(rows)
        self._process_child_table(conn, "analysis", self.core_dir / "analysis.xlsx", 1, transform_analysis, [])

        # 6. Child Table: Documents
        def transform_docs(df):
            rows = []
            for idx, r in df.iterrows():
                rows.append({
                    "id": int(r["id"]),
                    "company_id": normalize_ticker(r["company_id"]),
                    "year": normalize_year(r["Year"]),
                    "annual_report": clean_url(r.get("Annual_Report"))
                })
            return pd.DataFrame(rows)
        self._process_child_table(conn, "documents", self.core_dir / "documents.xlsx", 1, transform_docs, ["company_id", "year"])

        # 7. Child Table: Pros & Cons
        def transform_pc(df):
            rows = []
            for idx, r in df.iterrows():
                rows.append({
                    "id": int(r["id"]),
                    "company_id": normalize_ticker(r["company_id"]),
                    "pros": str(r.get("pros", "")).strip() if pd.notna(r.get("pros")) else None,
                    "cons": str(r.get("cons", "")).strip() if pd.notna(r.get("cons")) else None
                })
            return pd.DataFrame(rows)
        self._process_child_table(conn, "prosandcons", self.core_dir / "prosandcons.xlsx", 1, transform_pc, [])

        # 8. Child Table: Financial Ratios
        def transform_fr(df):
            rows = []
            for idx, r in df.iterrows():
                rows.append({
                    "id": int(r["id"]),
                    "company_id": normalize_ticker(r["company_id"]),
                    "year": normalize_year(r["year"]),
                    "net_profit_margin_pct": clean_numeric(r.get("net_profit_margin_pct")),
                    "operating_profit_margin_pct": clean_numeric(r.get("operating_profit_margin_pct")),
                    "return_on_equity_pct": clean_numeric(r.get("return_on_equity_pct")),
                    "debt_to_equity": clean_numeric(r.get("debt_to_equity")),
                    "interest_coverage": clean_numeric(r.get("interest_coverage")),
                    "asset_turnover": clean_numeric(r.get("asset_turnover")),
                    "free_cash_flow_cr": clean_numeric(r.get("free_cash_flow_cr")),
                    "capex_cr": clean_numeric(r.get("capex_cr")),
                    "earnings_per_share": clean_numeric(r.get("earnings_per_share")),
                    "book_value_per_share": clean_numeric(r.get("book_value_per_share")),
                    "dividend_payout_ratio_pct": clean_numeric(r.get("dividend_payout_ratio_pct")),
                    "total_debt_cr": clean_numeric(r.get("total_debt_cr")),
                    "cash_from_operations_cr": clean_numeric(r.get("cash_from_operations_cr"))
                })
            return pd.DataFrame(rows)
        self._process_child_table(conn, "financial_ratios", self.supp_dir / "financial_ratios.xlsx", 0, transform_fr, ["company_id", "year"])

        # 9. Child Table: Market Cap
        def transform_mc(df):
            rows = []
            for idx, r in df.iterrows():
                rows.append({
                    "id": int(r["id"]),
                    "company_id": normalize_ticker(r["company_id"]),
                    "year": normalize_year(r["year"]),
                    "market_cap_crore": clean_numeric(r.get("market_cap_crore")),
                    "enterprise_value_crore": clean_numeric(r.get("enterprise_value_crore")),
                    "pe_ratio": clean_numeric(r.get("pe_ratio")),
                    "pb_ratio": clean_numeric(r.get("pb_ratio")),
                    "ev_ebitda": clean_numeric(r.get("ev_ebitda")),
                    "dividend_yield_pct": clean_numeric(r.get("dividend_yield_pct"))
                })
            return pd.DataFrame(rows)
        self._process_child_table(conn, "market_cap", self.supp_dir / "market_cap.xlsx", 0, transform_mc, ["company_id", "year"])

        # 10. Child Table: Peer Groups
        def transform_pg(df):
            rows = []
            for idx, r in df.iterrows():
                rows.append({
                    "id": int(r["id"]),
                    "peer_group_name": str(r.get("peer_group_name", "")).strip(),
                    "company_id": normalize_ticker(r["company_id"]),
                    "is_benchmark": bool(r.get("is_benchmark", False))
                })
            return pd.DataFrame(rows)
        self._process_child_table(conn, "peer_groups", self.supp_dir / "peer_groups.xlsx", 0, transform_pg, ["peer_group_name", "company_id"])

        # 11. Child Table: Sectors
        def transform_sec(df):
            rows = []
            for idx, r in df.iterrows():
                rows.append({
                    "id": int(r["id"]),
                    "company_id": normalize_ticker(r["company_id"]),
                    "broad_sector": str(r.get("broad_sector", "")).strip(),
                    "sub_sector": str(r.get("sub_sector", "")).strip(),
                    "index_weight_pct": clean_numeric(r.get("index_weight_pct")),
                    "market_cap_category": str(r.get("market_cap_category", "")).strip()
                })
            return pd.DataFrame(rows)
        self._process_child_table(conn, "sectors", self.supp_dir / "sectors.xlsx", 0, transform_sec, ["company_id"])

        # 12. Child Table: Stock Prices
        def transform_sp(df):
            rows = []
            for idx, r in df.iterrows():
                rows.append({
                    "id": int(r["id"]),
                    "company_id": normalize_ticker(r["company_id"]),
                    "date": str(r["date"]).strip()[:10],
                    "open_price": clean_numeric(r.get("open_price")),
                    "high_price": clean_numeric(r.get("high_price")),
                    "low_price": clean_numeric(r.get("low_price")),
                    "close_price": clean_numeric(r.get("close_price")),
                    "volume": int(r.get("volume", 0) or 0),
                    "adjusted_close": clean_numeric(r.get("adjusted_close"))
                })
            return pd.DataFrame(rows)
        self._process_child_table(conn, "stock_prices", self.supp_dir / "stock_prices.xlsx", 0, transform_sp, ["company_id", "date"])

        # Write Audit Outputs
        audit_df = pd.DataFrame(self.audit_log)
        audit_path = self.output_dir / "load_audit.csv"
        audit_df.to_csv(audit_path, index=False)

        failures_df = self.validator.get_failures_dataframe()
        failures_path = self.output_dir / "validation_failures.csv"
        failures_df.to_csv(failures_path, index=False)

        return conn


if __name__ == "__main__":
    loader = N100DataLoader()
    conn = loader.run_pipeline()
    cursor = conn.cursor()

    # Check companies count
    comp_count = cursor.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    print(f"Loaded companies count: {comp_count}")

    # Check foreign keys
    fk_errors = cursor.execute("PRAGMA foreign_key_check").fetchall()
    print(f"PRAGMA foreign_key_check result (should be 0 rows): {len(fk_errors)} errors")
    conn.close()
