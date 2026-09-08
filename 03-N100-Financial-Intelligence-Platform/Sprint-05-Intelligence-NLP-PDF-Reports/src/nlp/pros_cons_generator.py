"""
src/nlp/pros_cons_generator.py
================================
Day 30 — Auto Pros/Cons Generator

Implements EXACTLY the 24 required rules from the Sprint 5 specification.
Uses the full 92-company universe from the ``companies`` master table.

Data sources (all read-only from Sprint-01 DB):
    financial_ratios, profitandloss, balancesheet, market_cap, sectors, companies

REQUIRED OUTPUT SCHEMA — output/pros_cons_generated.csv
--------------------------------------------------------
company_id    : str
type          : "pro" or "con"
rule_id       : "P01"–"P12"  /  "C01"–"C12"
text          : exact rule text from specification
confidence_pct: int in range [61, 99]  (>60 threshold, never 100)

Only rows with confidence_pct > 60 are emitted.
If a company has no qualifying signal: it is NOT fabricated.
A coverage_failures.csv is written for any company with <1 pro or <1 con.

Confidence methodology
-----------------------
    conf = 70 + floor(min(|magnitude| / scale, 29))

    Range: [70, 99].  Never 100.  Always > 60.
    For consecutive-year rules:  base = 70 + (n_years - min_years) * 5
    For binary rules with no magnitude:  conf = 72 (fixed ≡ signal present)

PRO RULES
---------
P01  ROE > 20% sustained for 3+ years
P02  FCF positive for 5+ consecutive years
P03  D/E = 0 in latest year
P04  Revenue CAGR > 15% over 5 years
P05  OPM > 25% in latest year
P06  PAT CAGR > 20% over 5 years
P07  ICR > 10 OR Debt Free
P08  Dividend Yield > 2% AND FCF positive
P09  EPS CAGR > 15% over 5 years
P10  ROE improving for 3 consecutive years
P11  Revenue CAGR > PAT CAGR (5-year)
     [NOTE: The supplied text says "Revenue growing slower than profits …"
      which is mathematically INCONSISTENT with the condition.
      The CONDITION is implemented as stated; the TEXT is preserved verbatim
      per specification.  This inconsistency is documented in README.]
P12  Balance sheet assets growing AND debt declining (latest 3 years)

CON RULES
---------
C01  D/E > 2.0 for NON-financial companies
C02  FCF negative for 3 consecutive years
C03  OPM declining for 3 consecutive years
C04  Net profit negative in latest year
C05  Revenue declining for 2+ consecutive years
C06  ICR < 1.5
C07  Dividend payout > 100%
C08  D/E rising for 3 consecutive years
C09  EPS declining for 3 consecutive years
C10  ROCE < 10%
C11  Net Debt > 3× EBITDA (EBITDA ≡ operating_profit in Screener.in format)
C12  Revenue CAGR < 5% over 5 years (revenue_cagr_5yr)
"""

from __future__ import annotations

import math
import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_SPRINT5  = Path(__file__).resolve().parents[2]
_PLATFORM = Path(__file__).resolve().parents[3]
_DB_PATH  = _PLATFORM / "Sprint-01-Data-Foundation" / "nifty100.db"
_OUTPUT   = _SPRINT5 / "output"

_FINANCIAL_SECTOR = "Financials"


# ---------------------------------------------------------------------------
# Confidence helpers
# ---------------------------------------------------------------------------
def _conf(magnitude: float, scale: float, base: int = 70) -> int:
    """
    Deterministic confidence.  Range [base, base+29] = [70, 99].
    Never returns 100.  Always > 60.
    """
    return base + math.floor(min(abs(magnitude) / scale, 29))


def _conf_consec(n_actual: int, n_min: int) -> int:
    """
    Confidence for consecutive-year rules.
    base = 70 + (extra years beyond minimum) * 5, capped at 99.
    """
    return min(70 + (n_actual - n_min) * 5, 99)


_FIXED_CONF = 72  # for binary presence signals (no continuous magnitude)


# ---------------------------------------------------------------------------
# DB loader
# ---------------------------------------------------------------------------
def _db_connect(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)


def _load(db_path: Path, sql: str) -> pd.DataFrame:
    con = _db_connect(db_path)
    try:
        df = pd.read_sql_query(sql, con)
    finally:
        con.close()
    if "company_id" in df.columns:
        df["company_id"] = df["company_id"].str.strip().str.upper()
    return df


# ---------------------------------------------------------------------------
# Helper: get latest non-TTM value for a column
# ---------------------------------------------------------------------------
def _latest(ts: pd.DataFrame, company_id: str, col: str) -> Optional[float]:
    """Return the latest non-TTM value for a company-column pair."""
    sub = ts[
        (ts["company_id"] == company_id)
        & (ts["year"] != "TTM")
        & ts[col].notna()
    ]
    if sub.empty:
        return None
    try:
        return float(sub.sort_values("year", ascending=False).iloc[0][col])
    except (TypeError, ValueError):
        return None


def _series(ts: pd.DataFrame, company_id: str, col: str, n: int) -> list[float]:
    """
    Return the last n non-null, non-TTM values for a column, sorted ascending by year.
    """
    sub = ts[
        (ts["company_id"] == company_id)
        & (ts["year"] != "TTM")
        & ts[col].notna()
    ].sort_values("year", ascending=True)
    vals = sub[col].astype(float).tolist()
    return vals[-n:] if len(vals) >= n else []


# ---------------------------------------------------------------------------
# Consecutive-year helpers
# ---------------------------------------------------------------------------
def _n_consec_positive(ts: pd.DataFrame, company_id: str, col: str) -> int:
    """Count trailing consecutive positive years (most-recent first, reverse search)."""
    vals = _series(ts, company_id, col, 12)
    if not vals:
        return 0
    count = 0
    for v in reversed(vals):
        if v > 0:
            count += 1
        else:
            break
    return count


def _n_consec_negative(ts: pd.DataFrame, company_id: str, col: str) -> int:
    """Count trailing consecutive negative years."""
    vals = _series(ts, company_id, col, 12)
    if not vals:
        return 0
    count = 0
    for v in reversed(vals):
        if v < 0:
            count += 1
        else:
            break
    return count


def _n_consec_declining(ts: pd.DataFrame, company_id: str, col: str) -> int:
    """Count how many trailing consecutive years have the column strictly decreasing."""
    vals = _series(ts, company_id, col, 12)
    if len(vals) < 2:
        return 0
    count = 0
    for i in range(len(vals) - 1, 0, -1):
        if vals[i] < vals[i - 1]:
            count += 1
        else:
            break
    return count


def _n_consec_increasing(ts: pd.DataFrame, company_id: str, col: str) -> int:
    """Count how many trailing consecutive years have the column strictly increasing."""
    vals = _series(ts, company_id, col, 12)
    if len(vals) < 2:
        return 0
    count = 0
    for i in range(len(vals) - 1, 0, -1):
        if vals[i] > vals[i - 1]:
            count += 1
        else:
            break
    return count


def _n_roe_gt20_consec(ts: pd.DataFrame, company_id: str) -> int:
    """Count trailing consecutive years with ROE > 20%."""
    vals = _series(ts, company_id, "return_on_equity_pct", 12)
    if not vals:
        return 0
    count = 0
    for v in reversed(vals):
        if v > 20:
            count += 1
        else:
            break
    return count


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------
class ProsConsGenerator:
    """
    Evaluate all 92 companies against 12 pro + 12 con rules.
    Emit signals with confidence_pct > 60.
    """

    CONFIDENCE_THRESHOLD = 60

    def __init__(self, db_path: Path = _DB_PATH):
        self.db_path = db_path
        self._signals:  list[dict] = []
        self._coverage: list[dict] = []

        # Loaded tables
        self._rat:      pd.DataFrame = pd.DataFrame()
        self._pnl:      pd.DataFrame = pd.DataFrame()
        self._bs:       pd.DataFrame = pd.DataFrame()
        self._mc:       pd.DataFrame = pd.DataFrame()
        self._sectors:  pd.DataFrame = pd.DataFrame()
        self._companies: list[str] = []

    # ------------------------------------------------------------------
    def _load_data(self) -> None:
        q_rat = "SELECT * FROM financial_ratios WHERE year != 'TTM' ORDER BY company_id, year"
        q_pnl = "SELECT * FROM profitandloss    WHERE year != 'TTM' ORDER BY company_id, year"
        q_bs  = "SELECT * FROM balancesheet     WHERE year != 'TTM' ORDER BY company_id, year"
        q_mc  = "SELECT * FROM market_cap       WHERE year != 'TTM' ORDER BY company_id, year"
        q_sec = "SELECT company_id, broad_sector FROM sectors"
        q_co  = "SELECT id AS company_id FROM companies ORDER BY id"

        self._rat     = _load(self.db_path, q_rat)
        self._pnl     = _load(self.db_path, q_pnl)
        self._bs      = _load(self.db_path, q_bs)
        self._mc      = _load(self.db_path, q_mc)
        self._sectors = _load(self.db_path, q_sec)
        cos_df        = _load(self.db_path, q_co)
        self._companies = cos_df["company_id"].tolist()

    # ------------------------------------------------------------------
    def _is_financial(self, cid: str) -> bool:
        sub = self._sectors[self._sectors["company_id"] == cid]
        if sub.empty:
            return False
        return sub.iloc[0]["broad_sector"] == _FINANCIAL_SECTOR

    # ------------------------------------------------------------------
    def _emit(self, cid: str, sig_type: str, rule_id: str, text: str, conf: int) -> None:
        if conf > self.CONFIDENCE_THRESHOLD:
            self._signals.append(
                {
                    "company_id":    cid,
                    "type":          sig_type,
                    "rule_id":       rule_id,
                    "text":          text,
                    "confidence_pct": conf,
                }
            )

    # ------------------------------------------------------------------
    # PRO RULES
    # ------------------------------------------------------------------
    def _pro_rules(self, cid: str) -> None:

        # ── P01 ─ ROE > 20% sustained for 3+ years ──────────────────────
        n = _n_roe_gt20_consec(self._rat, cid)
        if n >= 3:
            self._emit(
                cid, "pro", "P01",
                "Consistently high return on equity above 20% demonstrates exceptional capital efficiency",
                _conf_consec(n, 3),
            )

        # ── P02 ─ FCF positive for 5+ consecutive years ──────────────────
        n = _n_consec_positive(self._rat, cid, "free_cash_flow_cr")
        if n >= 5:
            self._emit(
                cid, "pro", "P02",
                "Strong free cash flow generation over 5 years signals healthy business fundamentals",
                _conf_consec(n, 5),
            )

        # ── P03 ─ D/E = 0 in latest year ─────────────────────────────────
        de = _latest(self._rat, cid, "debt_to_equity")
        if de is not None and de == 0.0:
            self._emit(
                cid, "pro", "P03",
                "Debt-free balance sheet provides financial flexibility and eliminates interest burden",
                _FIXED_CONF,
            )

        # ── P04 ─ Revenue CAGR > 15% over 5 years ────────────────────────
        rev5 = _latest(self._rat, cid, "revenue_cagr_5yr")
        if rev5 is not None and rev5 > 15:
            self._emit(
                cid, "pro", "P04",
                "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum",
                _conf(rev5 - 15, scale=3),
            )

        # ── P05 ─ OPM > 25% in latest year ───────────────────────────────
        opm = _latest(self._rat, cid, "operating_profit_margin_pct")
        if opm is not None and opm > 25:
            self._emit(
                cid, "pro", "P05",
                "Operating profit margin above 25% indicates strong pricing power and cost discipline",
                _conf(opm - 25, scale=3),
            )

        # ── P06 ─ PAT CAGR > 20% over 5 years ───────────────────────────
        pat5 = _latest(self._rat, cid, "pat_cagr_5yr")
        if pat5 is not None and pat5 > 20:
            self._emit(
                cid, "pro", "P06",
                "Net profit compounding at above 20% over 5 years creates significant shareholder value",
                _conf(pat5 - 20, scale=3),
            )

        # ── P07 ─ ICR > 10 OR Debt Free ──────────────────────────────────
        icr = _latest(self._rat, cid, "interest_coverage")
        de7 = _latest(self._rat, cid, "debt_to_equity")
        debt_free = de7 is not None and de7 == 0.0
        if debt_free:
            self._emit(
                cid, "pro", "P07",
                "Very high interest coverage ratio reflects negligible financial stress from debt servicing",
                _FIXED_CONF,
            )
        elif icr is not None and icr > 10:
            self._emit(
                cid, "pro", "P07",
                "Very high interest coverage ratio reflects negligible financial stress from debt servicing",
                _conf(icr - 10, scale=5),
            )

        # ── P08 ─ Dividend Yield > 2% AND FCF positive ───────────────────
        dy  = _latest(self._mc,  cid, "dividend_yield_pct")
        fcf = _latest(self._rat, cid, "free_cash_flow_cr")
        if dy is not None and dy > 2 and fcf is not None and fcf > 0:
            self._emit(
                cid, "pro", "P08",
                "Consistent dividend yield above 2% backed by positive free cash flow",
                _conf(dy - 2, scale=1),
            )

        # ── P09 ─ EPS CAGR > 15% over 5 years ───────────────────────────
        eps5 = _latest(self._rat, cid, "eps_cagr_5yr")
        if eps5 is not None and eps5 > 15:
            self._emit(
                cid, "pro", "P09",
                "Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding",
                _conf(eps5 - 15, scale=3),
            )

        # ── P10 ─ ROE improving for 3 consecutive years ──────────────────
        n = _n_consec_increasing(self._rat, cid, "return_on_equity_pct")
        if n >= 3:
            self._emit(
                cid, "pro", "P10",
                "Return on equity improving for 3 consecutive years shows strengthening business quality",
                _conf_consec(n, 3),
            )

        # ── P11 ─ Revenue CAGR > PAT CAGR (5-year) ───────────────────────
        # NOTE: The condition "Revenue CAGR > PAT CAGR" is implemented as
        # stated.  The supplied text ("Revenue growing slower than profits
        # shows improving operating leverage") is mathematically INCONSISTENT
        # with this condition — revenue growing FASTER than profits is the
        # opposite of what the text describes.  Per specification instructions,
        # both the condition and the verbatim text are preserved unchanged.
        rev5p = _latest(self._rat, cid, "revenue_cagr_5yr")
        pat5p = _latest(self._rat, cid, "pat_cagr_5yr")
        if rev5p is not None and pat5p is not None and rev5p > pat5p:
            self._emit(
                cid, "pro", "P11",
                "Revenue growing slower than profits shows improving operating leverage and scale benefits",
                _conf(rev5p - pat5p, scale=2),
            )

        # ── P12 ─ Assets growing AND debt declining (latest 3 years) ─────
        assets = _series(self._bs, cid, "total_assets", 4)
        borr   = _series(self._bs, cid, "borrowings",   4)
        if len(assets) >= 3 and len(borr) >= 3:
            assets_growing  = all(assets[i] > assets[i-1] for i in range(len(assets)-2, len(assets)))
            debt_declining  = all(borr[i]   < borr[i-1]   for i in range(len(borr)-2,   len(borr)))
            if assets_growing and debt_declining:
                self._emit(
                    cid, "pro", "P12",
                    "Growing asset base funded by internal accruals reflects self-sustaining growth",
                    _FIXED_CONF,
                )

    # ------------------------------------------------------------------
    # CON RULES
    # ------------------------------------------------------------------
    def _con_rules(self, cid: str) -> None:

        # ── C01 ─ D/E > 2.0 for non-financial companies ──────────────────
        if not self._is_financial(cid):
            de = _latest(self._rat, cid, "debt_to_equity")
            if de is not None and de > 2.0:
                self._emit(
                    cid, "con", "C01",
                    f"Debt-to-equity ratio of {de:.2f} is elevated for a non-financial company and warrants monitoring",
                    _conf(de - 2.0, scale=0.5),
                )

        # ── C02 ─ FCF negative for 3 consecutive years ───────────────────
        n = _n_consec_negative(self._rat, cid, "free_cash_flow_cr")
        if n >= 3:
            self._emit(
                cid, "con", "C02",
                "Free cash flow negative for 3 consecutive years raises concern about cash generation quality",
                _conf_consec(n, 3),
            )

        # ── C03 ─ OPM declining for 3 consecutive years ──────────────────
        n = _n_consec_declining(self._rat, cid, "operating_profit_margin_pct")
        if n >= 3:
            self._emit(
                cid, "con", "C03",
                "Operating margins declining for 3 consecutive years suggest pricing or cost pressure",
                _conf_consec(n, 3),
            )

        # ── C04 ─ Net profit negative in latest year ──────────────────────
        np_val = _latest(self._pnl, cid, "net_profit")
        if np_val is not None and np_val < 0:
            self._emit(
                cid, "con", "C04",
                "Company reported a net loss in the most recent financial year",
                _conf(abs(np_val), scale=5000),
            )

        # ── C05 ─ Revenue declining for 2+ consecutive years ─────────────
        n = _n_consec_declining(self._pnl, cid, "sales")
        if n >= 2:
            self._emit(
                cid, "con", "C05",
                "Revenue contraction over 2 consecutive years indicates demand weakness or market share loss",
                _conf_consec(n, 2),
            )

        # ── C06 ─ ICR < 1.5 ──────────────────────────────────────────────
        icr = _latest(self._rat, cid, "interest_coverage")
        if icr is not None and icr < 1.5:
            self._emit(
                cid, "con", "C06",
                "Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations",
                _conf(1.5 - icr, scale=0.3),
            )

        # ── C07 ─ Dividend payout > 100% ─────────────────────────────────
        dp = _latest(self._rat, cid, "dividend_payout_ratio_pct")
        if dp is not None and dp > 100:
            self._emit(
                cid, "con", "C07",
                "Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable",
                _conf(dp - 100, scale=20),
            )

        # ── C08 ─ D/E rising for 3 consecutive years ─────────────────────
        n = _n_consec_increasing(self._rat, cid, "debt_to_equity")
        if n >= 3:
            self._emit(
                cid, "con", "C08",
                "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk",
                _conf_consec(n, 3),
            )

        # ── C09 ─ EPS declining for 3 consecutive years ──────────────────
        # Use earnings_per_share from financial_ratios (computed)
        n = _n_consec_declining(self._rat, cid, "earnings_per_share")
        if n >= 3:
            self._emit(
                cid, "con", "C09",
                "Earnings per share declining for 3 consecutive years reflects deteriorating profitability",
                _conf_consec(n, 3),
            )

        # ── C10 ─ ROCE < 10% ─────────────────────────────────────────────
        roce = _latest(self._rat, cid, "return_on_capital_employed_pct")
        if roce is not None and roce < 10:
            self._emit(
                cid, "con", "C10",
                "Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital",
                _conf(10 - roce, scale=2),
            )

        # ── C11 ─ Net Debt > 3× EBITDA ───────────────────────────────────
        # In Screener.in format: operating_profit = EBITDA (sales - expenses,
        # before subtracting depreciation/interest).
        net_debt = _latest(self._rat, cid, "net_debt")
        ebitda   = _latest(self._pnl, cid, "operating_profit")
        if (net_debt is not None and ebitda is not None
                and ebitda > 0 and net_debt > 3 * ebitda):
            ratio = net_debt / ebitda
            self._emit(
                cid, "con", "C11",
                "Net debt exceeding 3 times EBITDA is a high leverage ratio and limits financial flexibility",
                _conf(ratio - 3, scale=1),
            )

        # ── C12 ─ Revenue CAGR < 5% over 5 years ─────────────────────────
        rev5 = _latest(self._rat, cid, "revenue_cagr_5yr")
        if rev5 is not None and rev5 < 5:
            self._emit(
                cid, "con", "C12",
                "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum",
                _conf(5 - rev5, scale=1),
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Evaluate all companies against all 24 rules.

        Returns
        -------
        (signals_df, coverage_failures_df)
        """
        self._load_data()
        self._signals  = []
        self._coverage = []

        for cid in self._companies:
            self._pro_rules(cid)
            self._con_rules(cid)

        if self._signals:
            df = pd.DataFrame(self._signals).sort_values(
                ["company_id", "type", "rule_id"]
            ).reset_index(drop=True)
            # Final schema: exactly the 5 required columns
            df = df[["company_id", "type", "rule_id", "text", "confidence_pct"]]
        else:
            df = pd.DataFrame(
                columns=["company_id", "type", "rule_id", "text", "confidence_pct"]
            )

        # Coverage check — with enriched classification
        fail_rows = []
        for cid in self._companies:
            sub = df[df["company_id"] == cid]
            has_pro = not sub[sub["type"] == "pro"].empty
            has_con = not sub[sub["type"] == "con"].empty
            if not has_pro or not has_con:
                cls, reason = self._classify_coverage_failure(cid)
                fail_rows.append(
                    {
                        "company_id":        cid,
                        "missing_pro":       not has_pro,
                        "missing_con":       not has_con,
                        "classification":    cls,
                        "available_metrics": self._available_metrics(cid),
                        "reason":            reason,
                    }
                )

        cov_df = pd.DataFrame(fail_rows) if fail_rows else pd.DataFrame(
            columns=["company_id", "missing_pro", "missing_con",
                     "classification", "available_metrics", "reason"]
        )
        return df, cov_df

    # ------------------------------------------------------------------
    def _available_metrics(self, cid: str) -> str:
        parts = []
        if not self._rat[self._rat["company_id"] == cid].empty:
            parts.append("financial_ratios")
        if not self._pnl[self._pnl["company_id"] == cid].empty:
            parts.append("profitandloss")
        if not self._bs[self._bs["company_id"] == cid].empty:
            parts.append("balancesheet")
        if not self._mc[self._mc["company_id"] == cid].empty:
            parts.append("market_cap")
        return "|".join(parts) if parts else "none"

    # ------------------------------------------------------------------
    # Metric columns that feed each rule — used for classification only
    _METRIC_RULE_MAP = {
        "return_on_equity_pct":           "P01/P10",
        "free_cash_flow_cr":              "P02/C02",
        "debt_to_equity":                 "P03/P07/C01/C08",
        "revenue_cagr_5yr":               "P04/P11/C12",
        "operating_profit_margin_pct":    "P05/C03",
        "pat_cagr_5yr":                   "P06/P11",
        "interest_coverage":              "P07/C06",
        "eps_cagr_5yr":                   "P09",
        "earnings_per_share":             "C09",
        "return_on_capital_employed_pct": "C10",
        "net_debt":                       "C11",
        "dividend_payout_ratio_pct":      "C07",
    }

    def _classify_coverage_failure(self, cid: str) -> tuple[str, str]:
        """
        Classify why a company lacks full pro+con coverage.

        Returns (classification_code, human_readable_reason).

        Codes:
          A_GENUINE_NO_CON   — all rules evaluated; none triggered (or no pro)
          B_INSUFFICIENT_HISTORY — < 3 years of historical data
          C_MISSING_METRIC   — one or more required DB columns are null
        """
        yr_df   = self._rat[
            (self._rat["company_id"] == cid) & (self._rat["year"] != "TTM")
        ]
        n_years = len(yr_df)

        # B: insufficient history
        if n_years < 3:
            return (
                "B_INSUFFICIENT_HISTORY",
                f"Only {n_years} historical year(s) of data; consecutive-year rules "
                f"(C02/C03/C08/C09/P01/P02/P10) require >=3-5 years of data.",
            )

        # C: missing metric columns
        null_cols = []
        for col, rules in self._METRIC_RULE_MAP.items():
            v = _latest(self._rat, cid, col)
            if v is None:
                null_cols.append(f"{col} (used by {rules})")
        # Also check dividend_yield from market_cap
        if _latest(self._mc, cid, "dividend_yield_pct") is None:
            null_cols.append("dividend_yield_pct (used by P08)")
        # Also net_profit from profitandloss
        if _latest(self._pnl, cid, "net_profit") is None:
            null_cols.append("net_profit (used by C04)")

        if null_cols:
            # Limit to first 4 for readability
            listed = "; ".join(null_cols[:4])
            suffix = f" [+{len(null_cols)-4} more]" if len(null_cols) > 4 else ""
            return (
                "C_MISSING_METRIC",
                f"Required metric(s) absent/null in DB for this company: "
                f"{listed}{suffix}. Affected rules cannot be evaluated.",
            )

        # A: genuine result — thresholds not met
        return (
            "A_GENUINE_NO_CON",
            "All applicable C01-C12 rules were evaluated against available data; "
            "none of the con thresholds were legitimately triggered for this company. "
            "No signal is fabricated.",
        )

    # ------------------------------------------------------------------
    def save_outputs(
        self,
        output_dir: Path = _OUTPUT,
        signals_df: pd.DataFrame | None = None,
        coverage_df: pd.DataFrame | None = None,
    ) -> dict[str, Path]:
        if signals_df is None or coverage_df is None:
            signals_df, coverage_df = self.generate()

        output_dir.mkdir(parents=True, exist_ok=True)
        out_signals  = output_dir / "pros_cons_generated.csv"
        out_coverage = output_dir / "coverage_failures.csv"

        signals_df.to_csv(out_signals, index=False)
        coverage_df.to_csv(out_coverage, index=False)

        return {
            "pros_cons_generated": out_signals,
            "coverage_failures":   out_coverage,
        }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    gen = ProsConsGenerator()
    df, cov = gen.generate()
    paths = gen.save_outputs(signals_df=df, coverage_df=cov)

    pros = df[df["type"] == "pro"]
    cons = df[df["type"] == "con"]

    print(f"[pros_cons] Companies evaluated         : {len(gen._companies)}")
    print(f"[pros_cons] Companies with signals      : {df['company_id'].nunique()}")
    print(f"[pros_cons] Companies with ≥1 pro       : {pros['company_id'].nunique()}")
    print(f"[pros_cons] Companies with ≥1 con       : {cons['company_id'].nunique()}")
    print(f"[pros_cons] Total pro signals            : {len(pros)}")
    print(f"[pros_cons] Total con signals            : {len(cons)}")
    print(f"[pros_cons] Distinct rules triggered     : {df['rule_id'].nunique()}")
    print(f"[pros_cons] Coverage failures            : {len(cov)}")
    print(f"[pros_cons] Output                       : {paths['pros_cons_generated']}")

    # Rule trigger summary
    print("\n[pros_cons] Rule trigger counts:")
    for rid in sorted(df["rule_id"].unique()):
        n = len(df[df["rule_id"] == rid])
        print(f"  {rid}: {n}")

    if not cov.empty:
        print(f"\n[pros_cons] ⚠ Coverage failures logged to: {paths['coverage_failures']}")
        print(cov.to_string(index=False))


if __name__ == "__main__":
    main()
