"""
N100 Financial Intelligence Platform — Schema & Data Quality Validator Module
Implements all 16 Data Quality Rules (DQ-01 to DQ-16) across the 12 normalized datasets.
"""

from typing import Dict, List, Any, Optional
import re
import pandas as pd
import numpy as np


class DataQualityValidator:
    """
    Validates normalized DataFrames against DQ-01 through DQ-16 rules.
    Collects validation violations with structured severity and details.
    """

    def __init__(self):
        self.failures: List[Dict[str, Any]] = []

    def log_failure(
        self,
        rule_id: str,
        table_name: str,
        row_identifier: str,
        field_name: str,
        observed_value: Any,
        severity: str,
        description: str
    ):
        self.failures.append({
            "rule_id": rule_id,
            "table_name": table_name,
            "row_identifier": str(row_identifier),
            "field_name": field_name,
            "observed_value": str(observed_value),
            "severity": severity,
            "description": description
        })

    def validate_dq01_primary_key_uniqueness(self, df: pd.DataFrame, table_name: str, pk_col: str = "id") -> bool:
        """DQ-01 [CRITICAL]: Validates that primary key is unique and non-null."""
        if pk_col not in df.columns:
            self.log_failure("DQ-01", table_name, "SCHEMA", pk_col, "MISSING", "CRITICAL", f"Primary key column '{pk_col}' missing.")
            return False

        null_mask = df[pk_col].isnull()
        for idx, row in df[null_mask].iterrows():
            self.log_failure("DQ-01", table_name, f"Index:{idx}", pk_col, "NULL", "CRITICAL", "Primary key contains null value.")

        dup_mask = df.duplicated(subset=[pk_col], keep=False)
        for idx, row in df[dup_mask].iterrows():
            self.log_failure("DQ-01", table_name, f"PK:{row[pk_col]}", pk_col, row[pk_col], "CRITICAL", "Duplicate primary key value.")

        return not (null_mask.any() or dup_mask.any())

    def validate_dq02_natural_key_uniqueness(self, df: pd.DataFrame, table_name: str, natural_keys: List[str]) -> bool:
        """DQ-02 [CRITICAL]: Validates table-specific composite natural key uniqueness."""
        missing = [k for k in natural_keys if k not in df.columns]
        if missing:
            self.log_failure("DQ-02", table_name, "SCHEMA", str(missing), "MISSING", "CRITICAL", f"Natural key columns {missing} missing.")
            return False

        dup_mask = df.duplicated(subset=natural_keys, keep=False)
        for idx, row in df[dup_mask].iterrows():
            row_id = {k: row[k] for k in natural_keys}
            self.log_failure("DQ-02", table_name, str(row_id), "+".join(natural_keys), str(row_id), "CRITICAL", f"Duplicate composite natural key {natural_keys}.")

        return not dup_mask.any()

    def validate_dq03_foreign_key_integrity(self, df: pd.DataFrame, table_name: str, valid_company_ids: set, fk_col: str = "company_id") -> List[str]:
        """DQ-03 [CRITICAL]: Validates that foreign key exists in parent master table."""
        if fk_col not in df.columns:
            return []

        orphan_ids = set()
        for idx, row in df.iterrows():
            val = row[fk_col]
            if val is not None and pd.notna(val):
                c_id = str(val).strip()
                if c_id not in valid_company_ids:
                    orphan_ids.add(c_id)
                    row_id = f"ID:{row.get('id', idx)}"
                    self.log_failure("DQ-03", table_name, row_id, fk_col, c_id, "CRITICAL", f"Orphan company_id '{c_id}' not found in companies table.")
        return list(orphan_ids)

    def validate_dq04_balancesheet_balance(self, df: pd.DataFrame, table_name: str = "balancesheet", tolerance_pct: float = 1.0) -> bool:
        """DQ-04 [WARNING]: Checks that Total Assets equals Total Liabilities within tolerance %."""
        if "total_assets" not in df.columns or "total_liabilities" not in df.columns:
            return False

        for idx, row in df.iterrows():
            assets = float(row.get("total_assets", 0) or 0)
            liab = float(row.get("total_liabilities", 0) or 0)
            if assets > 0:
                diff_pct = abs(assets - liab) / assets * 100.0
                if diff_pct > tolerance_pct:
                    row_id = f"{row.get('company_id')}_{row.get('year')}"
                    self.log_failure("DQ-04", table_name, row_id, "total_assets vs total_liabilities", f"Assets:{assets} != Liab:{liab} (Diff: {diff_pct:.2f}%)", "WARNING", "Balance Sheet assets and liabilities balance mismatch > 1%.")
        return True

    def validate_dq05_opm_cross_check(self, df: pd.DataFrame, table_name: str = "profitandloss", tolerance_pct: float = 2.0) -> bool:
        """DQ-05 [WARNING]: Checks operating_profit / sales * 100 against reported opm_percentage."""
        if not {"operating_profit", "sales", "opm_percentage"}.issubset(df.columns):
            return False

        for idx, row in df.iterrows():
            sales = float(row.get("sales", 0) or 0)
            op = row.get("operating_profit")
            opm = row.get("opm_percentage")
            if sales > 0 and pd.notna(op) and pd.notna(opm):
                calc_opm = (float(op) / sales) * 100.0
                diff = abs(calc_opm - float(opm))
                if diff > tolerance_pct:
                    row_id = f"{row.get('company_id')}_{row.get('year')}"
                    self.log_failure("DQ-05", table_name, row_id, "opm_percentage", f"Calc:{calc_opm:.1f}% vs Reported:{opm}% (Diff: {diff:.1f}%)", "WARNING", "Operating profit margin calculation discrepancy.")
        return True

    def validate_dq06_positive_sales(self, df: pd.DataFrame, table_name: str = "profitandloss") -> bool:
        """DQ-06 [WARNING]: Validates that sales revenue is positive (>0)."""
        if "sales" not in df.columns:
            return False

        for idx, row in df.iterrows():
            sales = row.get("sales")
            if pd.notna(sales) and float(sales) <= 0:
                row_id = f"{row.get('company_id')}_{row.get('year')}"
                self.log_failure("DQ-06", table_name, row_id, "sales", sales, "WARNING", "Non-positive sales revenue recorded.")
        return True

    def validate_dq07_net_cash_flow_sum(self, df: pd.DataFrame, table_name: str = "cashflow", tolerance: float = 1.0) -> bool:
        """DQ-07 [WARNING]: Checks CFO + CFI + CFF equals net_cash_flow."""
        required = {"operating_activity", "investing_activity", "financing_activity", "net_cash_flow"}
        if not required.issubset(df.columns):
            return False

        for idx, row in df.iterrows():
            cfo = float(row.get("operating_activity", 0) or 0)
            cfi = float(row.get("investing_activity", 0) or 0)
            cff = float(row.get("financing_activity", 0) or 0)
            ncf = float(row.get("net_cash_flow", 0) or 0)
            calc_sum = cfo + cfi + cff
            diff = abs(calc_sum - ncf)
            if diff > tolerance:
                row_id = f"{row.get('company_id')}_{row.get('year')}"
                self.log_failure("DQ-07", table_name, row_id, "net_cash_flow", f"Sum:{calc_sum} vs Reported:{ncf} (Diff: {diff:.1f})", "WARNING", "Cash flow statement component sum mismatch.")
        return True

    def validate_dq08_tax_rate_sanity(self, df: pd.DataFrame, table_name: str = "profitandloss") -> bool:
        """DQ-08 [WARNING]: Checks tax rate percentage within standard 0-100% bounds."""
        if "tax_percentage" not in df.columns:
            return False

        for idx, row in df.iterrows():
            tax = row.get("tax_percentage")
            if pd.notna(tax):
                tax_f = float(tax)
                if tax_f < 0 or tax_f > 100:
                    row_id = f"{row.get('company_id')}_{row.get('year')}"
                    self.log_failure("DQ-08", table_name, row_id, "tax_percentage", tax, "WARNING", "Effective tax rate outside standard [0, 100]% range.")
        return True

    def validate_dq09_dividend_payout_bounds(self, df: pd.DataFrame, table_name: str, col_name: str = "dividend_payout") -> bool:
        """DQ-09 [WARNING]: Checks dividend payout ratio within reasonable bounds [0, 200]%."""
        if col_name not in df.columns:
            return False

        for idx, row in df.iterrows():
            div = row.get(col_name)
            if pd.notna(div):
                div_f = float(div)
                if div_f < 0 or div_f > 200:
                    row_id = f"{row.get('company_id')}_{row.get('year')}"
                    self.log_failure("DQ-09", table_name, row_id, col_name, div, "WARNING", "Dividend payout ratio outside expected [0, 200]% bounds.")
        return True

    def validate_dq10_url_syntax(self, df: pd.DataFrame, table_name: str, url_cols: List[str]) -> bool:
        """DQ-10 [WARNING]: Validates URL syntax and web protocols."""
        url_regex = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)
        for ucol in url_cols:
            if ucol in df.columns:
                for idx, row in df.iterrows():
                    val = row.get(ucol)
                    if pd.notna(val) and str(val).strip():
                        u_str = str(val).strip()
                        if not url_regex.match(u_str):
                            row_id = f"ID:{row.get('id', idx)}"
                            self.log_failure("DQ-10", table_name, row_id, ucol, u_str, "WARNING", "Invalid URL syntax or missing protocol prefix.")
        return True

    def validate_dq11_eps_sign_consistency(self, df: pd.DataFrame, table_name: str = "profitandloss") -> bool:
        """DQ-11 [WARNING]: Checks EPS sign consistency with Net Profit."""
        if not {"net_profit", "eps"}.issubset(df.columns):
            return False

        for idx, row in df.iterrows():
            np_val = row.get("net_profit")
            eps_val = row.get("eps")
            if pd.notna(np_val) and pd.notna(eps_val):
                np_f, eps_f = float(np_val), float(eps_val)
                if (np_f > 0 and eps_f < 0) or (np_f < 0 and eps_f > 0):
                    row_id = f"{row.get('company_id')}_{row.get('year')}"
                    self.log_failure("DQ-11", table_name, row_id, "eps vs net_profit", f"NP:{np_f} vs EPS:{eps_f}", "WARNING", "Sign discrepancy between Net Profit and EPS.")
        return True

    def validate_dq12_asset_components(self, df: pd.DataFrame, table_name: str = "balancesheet", tolerance: float = 1.0) -> bool:
        """DQ-12 [WARNING]: Checks fixed_assets + cwip + investments + other_asset equals total_assets."""
        required = {"fixed_assets", "cwip", "investments", "other_asset", "total_assets"}
        if not required.issubset(df.columns):
            return False

        for idx, row in df.iterrows():
            fa = float(row.get("fixed_assets", 0) or 0)
            cwip = float(row.get("cwip", 0) or 0)
            inv = float(row.get("investments", 0) or 0)
            oa = float(row.get("other_asset", 0) or 0)
            ta = float(row.get("total_assets", 0) or 0)
            calc_sum = fa + cwip + inv + oa
            diff = abs(calc_sum - ta)
            if diff > tolerance:
                row_id = f"{row.get('company_id')}_{row.get('year')}"
                self.log_failure("DQ-12", table_name, row_id, "total_assets", f"CalcSum:{calc_sum} vs Reported:{ta} (Diff: {diff:.1f})", "WARNING", "Asset component sum mismatch against Total Assets.")
        return True

    def validate_dq13_liability_components(self, df: pd.DataFrame, table_name: str = "balancesheet", tolerance: float = 1.0) -> bool:
        """DQ-13 [WARNING]: Checks equity_capital + reserves + borrowings + other_liabilities equals total_liabilities."""
        required = {"equity_capital", "reserves", "borrowings", "other_liabilities", "total_liabilities"}
        if not required.issubset(df.columns):
            return False

        for idx, row in df.iterrows():
            eq = float(row.get("equity_capital", 0) or 0)
            res = float(row.get("reserves", 0) or 0)
            borr = float(row.get("borrowings", 0) or 0)
            ol = float(row.get("other_liabilities", 0) or 0)
            tl = float(row.get("total_liabilities", 0) or 0)
            calc_sum = eq + res + borr + ol
            diff = abs(calc_sum - tl)
            if diff > tolerance:
                row_id = f"{row.get('company_id')}_{row.get('year')}"
                self.log_failure("DQ-13", table_name, row_id, "total_liabilities", f"CalcSum:{calc_sum} vs Reported:{tl} (Diff: {diff:.1f})", "WARNING", "Liability component sum mismatch against Total Liabilities.")
        return True

    def validate_dq14_year_coverage_continuity(self, df: pd.DataFrame, table_name: str, min_years: int = 5) -> bool:
        """DQ-14 [WARNING]: Checks companies have at least min_years of financial records."""
        if not {"company_id", "year"}.issubset(df.columns):
            return False

        counts = df.groupby("company_id")["year"].nunique()
        for cid, yr_cnt in counts.items():
            if yr_cnt < min_years:
                self.log_failure("DQ-14", table_name, str(cid), "year_coverage", f"{yr_cnt} years", "WARNING", f"Company has fewer than {min_years} reporting periods.")
        return True

    def validate_dq15_stock_prices_range(self, df: pd.DataFrame, table_name: str = "stock_prices") -> bool:
        """DQ-15 [WARNING]: Validates that low <= open, close <= high and volume >= 0."""
        required = {"open_price", "high_price", "low_price", "close_price", "volume"}
        if not required.issubset(df.columns):
            return False

        for idx, row in df.iterrows():
            o = float(row.get("open_price", 0) or 0)
            h = float(row.get("high_price", 0) or 0)
            l = float(row.get("low_price", 0) or 0)
            c = float(row.get("close_price", 0) or 0)
            v = int(row.get("volume", 0) or 0)

            invalid = False
            details = []
            if l > h:
                invalid = True
                details.append(f"Low ({l}) > High ({h})")
            if o > h or o < l:
                invalid = True
                details.append(f"Open ({o}) outside [Low:{l}, High:{h}]")
            if c > h or c < l:
                invalid = True
                details.append(f"Close ({c}) outside [Low:{l}, High:{h}]")
            if v < 0:
                invalid = True
                details.append(f"Volume ({v}) < 0")

            if invalid:
                row_id = f"{row.get('company_id')}_{row.get('date')}"
                self.log_failure("DQ-15", table_name, row_id, "OHLCV", "; ".join(details), "WARNING", "Stock price boundary anomaly.")
        return True

    def validate_dq16_sector_index_weight_bounds(self, df: pd.DataFrame, table_name: str = "sectors") -> bool:
        """DQ-16 [WARNING]: Validates sector weight ranges (0 < weight <= 100%)."""
        if "index_weight_pct" not in df.columns:
            return False

        for idx, row in df.iterrows():
            w = row.get("index_weight_pct")
            if pd.notna(w):
                w_f = float(w)
                if w_f <= 0 or w_f > 100:
                    row_id = str(row.get("company_id", idx))
                    self.log_failure("DQ-16", table_name, row_id, "index_weight_pct", w, "WARNING", "Sector index weight outside valid (0, 100]% range.")
        return True

    def get_failures_dataframe(self) -> pd.DataFrame:
        """Returns collected failures as a standardized DataFrame."""
        if not self.failures:
            return pd.DataFrame(columns=[
                "rule_id", "table_name", "row_identifier", "field_name",
                "observed_value", "severity", "description"
            ])
        return pd.DataFrame(self.failures)
