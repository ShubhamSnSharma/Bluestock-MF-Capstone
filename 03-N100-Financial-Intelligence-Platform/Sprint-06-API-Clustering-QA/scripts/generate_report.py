#!/usr/bin/env python3
"""
Sprint 6 — Day 42: HTML Test Report Generator.

Runs all tests and produces a self-contained HTML report.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SPRINT6_ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = SPRINT6_ROOT / "reports" / "sprint6_test_report.html"


def run_tests() -> dict:
    """Run pytest and capture JSON output."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(SPRINT6_ROOT / "tests"),
            "-v",
            "--tb=short",
            "-q",
            "--json-report",
            f"--json-report-file={SPRINT6_ROOT / 'reports' / 'pytest_results.json'}",
        ],
        capture_output=True,
        text=True,
        cwd=str(SPRINT6_ROOT),
    )
    return result


def load_results() -> dict:
    path = SPRINT6_ROOT / "reports" / "pytest_results.json"
    if path.exists():
        return json.loads(path.read_text())
    return {}


def build_html(results: dict) -> str:
    summary = results.get("summary", {})
    total = summary.get("total", 0)
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    skipped = summary.get("skipped", 0)
    duration = results.get("duration", 0)
    tests = results.get("tests", [])

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pass_rate = (passed / total * 100) if total else 0

    status_color = "#3fb950" if failed == 0 else "#f85149"
    status_text = "ALL PASS" if failed == 0 else f"{failed} FAILED"

    test_rows = []
    for t in tests:
        name = t.get("nodeid", "unknown")
        outcome = t.get("outcome", "unknown")
        dur = t.get("duration", 0)
        markers = t.get("markers", [])
        marker_str = ", ".join(str(mk) for mk in markers) if markers else "-"

        if outcome == "passed":
            badge = '<span style="color:#3fb950;font-weight:600;">PASS</span>'
        elif outcome == "failed":
            badge = '<span style="color:#f85149;font-weight:600;">FAIL</span>'
        elif outcome == "skipped":
            badge = '<span style="color:#e3b341;font-weight:600;">SKIP</span>'
        else:
            badge = f'<span style="color:#8b949e;">{outcome.upper()}</span>'

        # Extract suite name from path
        parts = name.split("::")
        suite = (
            parts[0].replace("tests/", "").replace(".py", "") if len(parts) > 0 else ""
        )
        test_name = parts[-1] if len(parts) > 1 else name

        test_rows.append(
            f"""
        <tr>
            <td style="font-size:0.82rem;">{suite}</td>
            <td style="font-size:0.82rem;">{test_name}</td>
            <td>{badge}</td>
            <td style="font-size:0.82rem;">{dur:.3f}s</td>
            <td style="font-size:0.78rem;color:#8b949e;">{marker_str}</td>
        </tr>"""
        )

    test_rows_html = "\n".join(test_rows)

    # Suite summary
    suite_map: dict[str, dict] = {}
    for t in tests:
        parts = t.get("nodeid", "").split("::")
        suite = (
            parts[0].replace("tests/", "").replace(".py", "") if parts else "unknown"
        )
        if suite not in suite_map:
            suite_map[suite] = {"passed": 0, "failed": 0, "skipped": 0, "total": 0}
        suite_map[suite]["total"] += 1
        outcome = t.get("outcome", "unknown")
        if outcome in suite_map[suite]:
            suite_map[suite][outcome] += 1

    suite_rows = []
    for suite, counts in sorted(suite_map.items()):
        s_color = "#3fb950" if counts["failed"] == 0 else "#f85149"
        suite_rows.append(
            f"""
        <tr>
            <td style="font-size:0.85rem;font-weight:500;">{suite}</td>
            <td style="text-align:center;">{counts["total"]}</td>
            <td style="text-align:center;color:#3fb950;">{counts["passed"]}</td>
            <td style="text-align:center;color:#f85149;">{counts["failed"]}</td>
            <td style="text-align:center;color:#e3b341;">{counts["skipped"]}</td>
            <td style="text-align:center;font-weight:600;color:{s_color};">{"PASS" if counts["failed"] == 0 else "FAIL"}</td>
        </tr>"""
        )

    suite_rows_html = "\n".join(suite_rows)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sprint 6 — Test Report</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Inter', -apple-system, sans-serif; background: #0d1117; color: #e6edf3; padding: 2rem; }}
  .header {{ text-align: center; margin-bottom: 2rem; }}
  .header h1 {{ font-size: 1.8rem; color: #58a6ff; margin-bottom: 0.3rem; }}
  .header p {{ color: #8b949e; font-size: 0.85rem; }}
  .summary {{ display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; margin-bottom: 2rem; }}
  .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 1.2rem 1.8rem; text-align: center; min-width: 140px; }}
  .card .value {{ font-size: 2rem; font-weight: 700; }}
  .card .label {{ font-size: 0.72rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.2rem; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 2rem; }}
  th {{ background: #161b22; color: #8b949e; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; padding: 0.6rem 0.8rem; text-align: left; border-bottom: 1px solid #30363d; }}
  td {{ padding: 0.5rem 0.8rem; border-bottom: 1px solid #21262d; }}
  tr:hover {{ background: #161b22; }}
  h2 {{ font-size: 1.1rem; color: #e6edf3; border-left: 3px solid #58a6ff; padding-left: 0.75rem; margin: 2rem 0 1rem 0; }}
  .footer {{ text-align: center; color: #484f58; font-size: 0.7rem; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #21262d; }}
</style>
</head>
<body>
<div class="header">
  <h1>Sprint 6 — Test Report</h1>
  <p>N100 Financial Intelligence Platform · API Integration & Data Quality · Day 42</p>
  <p style="margin-top:0.3rem;">Generated: {now}</p>
</div>

<div class="summary">
  <div class="card"><div class="value">{total}</div><div class="label">Total Tests</div></div>
  <div class="card"><div class="value" style="color:#3fb950;">{passed}</div><div class="label">Passed</div></div>
  <div class="card"><div class="value" style="color:#f85149;">{failed}</div><div class="label">Failed</div></div>
  <div class="card"><div class="value" style="color:#e3b341;">{skipped}</div><div class="label">Skipped</div></div>
  <div class="card"><div class="value">{pass_rate:.1f}%</div><div class="label">Pass Rate</div></div>
  <div class="card"><div class="value" style="color:{status_color};">{status_text}</div><div class="label">Overall Status</div></div>
  <div class="card"><div class="value">{duration:.1f}s</div><div class="label">Duration</div></div>
</div>

<h2>Suite Summary</h2>
<table>
  <thead><tr><th>Suite</th><th style="text-align:center;">Total</th><th style="text-align:center;">Pass</th><th style="text-align:center;">Fail</th><th style="text-align:center;">Skip</th><th style="text-align:center;">Status</th></tr></thead>
  <tbody>{suite_rows_html}</tbody>
</table>

<h2>All Tests ({total})</h2>
<table>
  <thead><tr><th>Suite</th><th>Test</th><th>Status</th><th>Duration</th><th>Markers</th></tr></thead>
  <tbody>{test_rows_html}</tbody>
</table>

<div class="footer">
  Sprint 6 Day 42 · N100 Financial Intelligence Platform · {total} tests · {pass_rate:.1f}% pass rate
</div>
</body>
</html>"""


def main():
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    print("Running tests...")
    run_tests()
    print("Loading results...")
    results = load_results()
    print("Building report...")
    html = build_html(results)
    REPORT_PATH.write_text(html)
    total = results.get("summary", {}).get("total", 0)
    passed = results.get("summary", {}).get("passed", 0)
    failed = results.get("summary", {}).get("failed", 0)
    print(f"Report: {REPORT_PATH}")
    print(f"  Total: {total}  Passed: {passed}  Failed: {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
