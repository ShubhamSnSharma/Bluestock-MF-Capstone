"""
Validation Script for Sprint 3 SQL Queries.
"""

import sqlite3
from pathlib import Path


def run_validation():
    sprint3_root = Path(__file__).resolve().parent.parent.parent
    db_path = sprint3_root.parent / "Sprint-01-Data-Foundation" / "nifty100.db"
    sql_path = sprint3_root / "notebooks" / "screener_validation.sql"

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at: {db_path}")
    if not sql_path.exists():
        raise FileNotFoundError(f"Validation SQL not found at: {sql_path}")

    conn = sqlite3.connect(db_path)
    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Split on semicolon, ignoring pure comment blocks
    queries = [q.strip() for q in sql_content.split(";") if q.strip()]

    print(f"Executing {len(queries)} Validation Queries from {sql_path.name}:")
    for idx, query in enumerate(queries, 1):
        try:
            cur = conn.execute(query)
            rows = cur.fetchall()
            print(f"  [Query {idx:02d}] PASS — {len(rows):3d} rows returned")
        except Exception as e:
            print(f"  [Query {idx:02d}] FAIL — Error: {e}")
            raise e

    conn.close()
    print("\nAll SQL validation queries executed successfully.")


if __name__ == "__main__":
    run_validation()
