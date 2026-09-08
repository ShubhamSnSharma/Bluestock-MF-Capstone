r"""
src/nlp/parser.py
=================
Day 29 — NLP Analysis Text Parser

SOURCE: Sprint-01-Data-Foundation/core datasets/analysis.xlsx  (NOT the DB table)

Reads the four free-text CAGR/ROE columns from analysis.xlsx and parses
each cell into a typed numeric row using the mandated regex:

    r"(\d+)\s*Years?:?\s*([\d.]+)%"

Extended to also match TTM / "Last Year" / "1 Year" entries.

OUTPUT SCHEMA — output/analysis_parsed.csv
------------------------------------------
company_id   : str   — trimmed + uppercased ticker
metric_type  : str   — one of:
                        compounded_sales_growth
                        compounded_profit_growth
                        stock_price_cagr
                        roe
period_years : int   — numeric period: 10, 5, 3
                        TTM / "Last Year" / "1 Year" → period_years = 0
                        (documented: TTM cannot be a meaningful multi-year CAGR)
value_pct    : float — the parsed percentage

OUTPUT SCHEMA — output/parse_failures.csv
-----------------------------------------
company_id   : str
metric_type  : str
raw_value    : str
reason       : str

Every unmatched cell is logged here.
"""

from __future__ import annotations

import re
import warnings
from pathlib import Path
from typing import Optional

import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# parents[0]=src/nlp, [1]=src, [2]=Sprint-05, [3]=platform, [4]=repo
_SPRINT5   = Path(__file__).resolve().parents[2]
_PLATFORM  = Path(__file__).resolve().parents[3]
_XLSX_PATH = _PLATFORM / "Sprint-01-Data-Foundation" / "core datasets" / "analysis.xlsx"
_DB_PATH   = _PLATFORM / "Sprint-01-Data-Foundation" / "nifty100.db"
_OUTPUT    = _SPRINT5 / "output"

# ---------------------------------------------------------------------------
# Mandated regex (from spec) + extensions for TTM / Last Year / 1 Year
# ---------------------------------------------------------------------------
# Mandated base:  r"(\d+)\s*Years?:?\s*([\d.]+)%"
# Extended to handle negative values and TTM variants.
_MULTI_YEAR_RE = re.compile(
    r"(?P<n>\d+)\s*Years?:?\s*(?P<pct>-?[\d.]+)\s*%",
    re.IGNORECASE,
)
_TTM_RE = re.compile(
    r"(?:TTM|Last\s+Year|1\s+Year)\s*:?\s*(?P<pct>-?[\d.]+)\s*%",
    re.IGNORECASE,
)

# Source columns → metric_type name
_METRIC_COLS = [
    ("compounded_sales_growth",  "compounded_sales_growth"),
    ("compounded_profit_growth", "compounded_profit_growth"),
    ("stock_price_cagr",         "stock_price_cagr"),
    ("roe",                      "roe"),
]


def _parse_cell(
    raw: object,
    company_id: str,
    metric_type: str,
) -> tuple[Optional[int], Optional[float], Optional[str]]:
    """
    Returns (period_years, value_pct, reason_on_failure).
    period_years = 0 for TTM/1-Year entries.
    reason_on_failure is None on success.
    """
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None, None, "null_cell"

    text = str(raw).strip()
    if not text:
        return None, None, "empty_cell"

    # Try multi-year match first (mandated regex)
    m = _MULTI_YEAR_RE.search(text)
    if m:
        n   = int(m.group("n"))
        pct = float(m.group("pct"))
        if n == 1:
            # 1-year treated as TTM
            return 0, pct, None
        return n, pct, None

    # Try TTM / Last Year
    m2 = _TTM_RE.search(text)
    if m2:
        return 0, float(m2.group("pct")), None

    return None, None, "regex_no_match"


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------
class AnalysisParser:
    """
    Parse the analysis.xlsx workbook into tidy long-format rows.

    Source: ``analysis.xlsx`` (Sprint-01/core datasets/).
    NOT the SQLite analysis table — the task explicitly names the workbook.
    """

    def __init__(
        self,
        xlsx_path: Path = _XLSX_PATH,
        db_path: Path = _DB_PATH,
    ):
        self.xlsx_path = xlsx_path
        self.db_path   = db_path
        self._df_parsed:  pd.DataFrame | None = None
        self._df_failures: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    def _load_xlsx(self) -> pd.DataFrame:
        """Read workbook. Title row 0, real header row 1 → header=1."""
        df = pd.read_excel(self.xlsx_path, sheet_name="Analysis", header=1)
        df["company_id"] = df["company_id"].str.strip().str.upper()
        return df

    # ------------------------------------------------------------------
    def parse(self) -> pd.DataFrame:
        """
        Parse all metric cells into long-format rows.

        Returns parsed DataFrame; also stores failures.
        """
        raw = self._load_xlsx()
        parsed_rows  = []
        failure_rows = []

        for _, row in raw.iterrows():
            cid = row["company_id"]
            for src_col, metric_name in _METRIC_COLS:
                cell = row.get(src_col)
                period, pct, reason = _parse_cell(cell, cid, metric_name)

                if reason is None:
                    parsed_rows.append(
                        {
                            "company_id":  cid,
                            "metric_type": metric_name,
                            "period_years": period,
                            "value_pct":   pct,
                        }
                    )
                else:
                    failure_rows.append(
                        {
                            "company_id":  cid,
                            "metric_type": metric_name,
                            "raw_value":   str(cell),
                            "reason":      reason,
                        }
                    )

        self._df_parsed   = pd.DataFrame(parsed_rows)
        self._df_failures = pd.DataFrame(failure_rows)
        return self._df_parsed

    # ------------------------------------------------------------------
    def cross_validate(self) -> pd.DataFrame:
        """
        Cross-validate 5-year CAGR values from analysis.xlsx against
        Sprint-02 financial_ratios:

            compounded_sales_growth  ↔  revenue_cagr_5yr
            compounded_profit_growth ↔  pat_cagr_5yr

        Returns a DataFrame of divergences with columns:
            company_id, metric_type, xlsx_value, db_value,
            divergence_pct, flag_for_review
        """
        import sqlite3

        if self._df_parsed is None:
            self.parse()

        uri = f"file:{self.db_path}?mode=ro"
        con = sqlite3.connect(uri, uri=True)
        rat = pd.read_sql_query(
            "SELECT company_id, year, revenue_cagr_5yr, pat_cagr_5yr "
            "FROM financial_ratios WHERE year != 'TTM' "
            "ORDER BY company_id, year DESC",
            con,
        )
        con.close()
        rat["company_id"] = rat["company_id"].str.strip().str.upper()
        # Latest non-TTM year per company
        rat_latest = rat.groupby("company_id").first().reset_index()

        metric_map = {
            "compounded_sales_growth":  "revenue_cagr_5yr",
            "compounded_profit_growth": "pat_cagr_5yr",
        }

        rows = []
        df_parsed = self._df_parsed if self._df_parsed is not None else self.parse()
        xlsx_5yr = df_parsed[df_parsed["period_years"] == 5]
        for metric_xlsx, metric_db in metric_map.items():
            sub = xlsx_5yr[xlsx_5yr["metric_type"] == metric_xlsx]
            for _, r in sub.iterrows():
                cid = r["company_id"]
                rat_row = rat_latest[rat_latest["company_id"] == cid]
                if rat_row.empty or pd.isna(rat_row.iloc[0].get(metric_db)):
                    continue
                db_val   = float(rat_row.iloc[0][metric_db])
                xlsx_val = float(r["value_pct"])
                div      = abs(xlsx_val - db_val)
                rows.append(
                    {
                        "company_id":     cid,
                        "metric_type":    metric_xlsx,
                        "xlsx_value":     round(xlsx_val, 2),
                        "db_value":       round(db_val, 2),
                        "divergence_pct": round(div, 2),
                        "flag_for_review": div > 5.0,
                    }
                )
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    def save_outputs(self, output_dir: Path = _OUTPUT) -> dict[str, Path]:
        """Write analysis_parsed.csv and parse_failures.csv."""
        if self._df_parsed is None:
            self.parse()

        df_parsed = self._df_parsed if self._df_parsed is not None else pd.DataFrame()
        output_dir.mkdir(parents=True, exist_ok=True)
        parsed_path  = output_dir / "analysis_parsed.csv"
        failure_path = output_dir / "parse_failures.csv"

        df_parsed.to_csv(parsed_path, index=False)

        if self._df_failures is not None and not self._df_failures.empty:
            self._df_failures.to_csv(failure_path, index=False)
        else:
            pd.DataFrame(
                columns=["company_id", "metric_type", "raw_value", "reason"]
            ).to_csv(failure_path, index=False)

        return {
            "analysis_parsed":  parsed_path,
            "parse_failures":   failure_path,
        }

    # ------------------------------------------------------------------
    @property
    def parsed_df(self) -> pd.DataFrame:
        if self._df_parsed is None:
            self.parse()
        return self._df_parsed if self._df_parsed is not None else pd.DataFrame()

    @property
    def failures_df(self) -> pd.DataFrame:
        if self._df_failures is None:
            self.parse()
        return self._df_failures if self._df_failures is not None else pd.DataFrame()

    @property
    def company_coverage(self) -> int:
        return self.parsed_df["company_id"].nunique()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    p = AnalysisParser()
    p.parse()
    paths = p.save_outputs()

    print(f"[parser] Source: {p.xlsx_path}")
    print(f"[parser] Workbook companies: {p.company_coverage}")
    print(f"[parser] Parsed rows        : {len(p.parsed_df)}")
    print(f"[parser] Parse failures     : {len(p.failures_df)}")
    print(f"[parser] Output             : {paths['analysis_parsed']}")
    if not p.failures_df.empty:
        print(f"[parser] Failures           : {paths['parse_failures']}")
        print(p.failures_df.to_string(index=False))

    print()
    print("[parser] Cross-validation (5-yr CAGR vs financial_ratios):")
    cv = p.cross_validate()
    if cv.empty:
        print("  No comparable 5-year values found.")
    else:
        print(cv.to_string(index=False))
        flagged = cv[cv["flag_for_review"]]
        if not flagged.empty:
            print(f"\n  ⚠  {len(flagged)} divergence(s) >5pp flagged for review:")
            print(flagged.to_string(index=False))


if __name__ == "__main__":
    main()
