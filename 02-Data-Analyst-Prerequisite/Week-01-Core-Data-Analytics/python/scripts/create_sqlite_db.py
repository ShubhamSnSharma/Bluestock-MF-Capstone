import sqlite3
import pandas as pd
from pathlib import Path

# Project root
ROOT = Path(__file__).resolve().parents[2]

csv_path = ROOT / "data" / "cleaned" / "superstore_cleaned.csv"
db_path = ROOT / "sql" / "superstore.db"

# Read CSV
df = pd.read_csv(csv_path)

# Create SQLite database
conn = sqlite3.connect(db_path)

# Write table
df.to_sql("superstore", conn, if_exists="replace", index=False)

conn.close()

print("Database created successfully!")
print(f"Rows imported: {len(df)}")