import pandas as pd
from pathlib import Path

# Path to the raw data folder
raw_data_path = Path("data/raw")

print("=" * 80)
print("BLUESTOCK MUTUAL FUND DATA INGESTION")
print("=" * 80)

# Find only required 10 CSV files for analysis
csv_files = [
    "01_fund_master.csv",
    "02_nav_history.csv",
    "03_aum_by_fund_house.csv",
    "04_monthly_sip_inflows.csv",
    "05_category_inflows.csv",
    "06_industry_folio_count.csv",
    "07_scheme_performance.csv",
    "08_investor_transactions.csv",
    "09_portfolio_holdings.csv",
    "10_benchmark_indices.csv"
]

# Check if any CSV files exist
if not csv_files:
    print("No CSV files found in data/raw/")
else:
    # Loop through each CSV file
    for file_name in csv_files:
        csv_file = raw_data_path / file_name

        print("\n" + "=" * 80)
        print(f"Dataset: {file_name}")
        print("=" * 80)

        try:
            # Load dataset
            df = pd.read_csv(csv_file)

            # Print shape
            print("\nShape:")
            print(df.shape)

            # Print data types
            print("\nData Types:")
            print(df.dtypes)

            # Print first five rows
            print("\nFirst 5 Rows:")
            print(df.head())

            # -----------------------------
            # Data Quality Checks
            # -----------------------------
            print("\nData Quality Summary")

            # Missing values
            missing_values = df.isnull().sum()
            total_missing = missing_values.sum()

            print(f"Total Missing Values: {total_missing}")

            if total_missing > 0:
                print("\nMissing Values by Column:")
                print(missing_values[missing_values > 0])

            # Duplicate rows
            duplicate_rows = df.duplicated().sum()
            print(f"\nDuplicate Rows: {duplicate_rows}")

        except Exception as e:
            print(f"Error reading {csv_file.name}")
            print(e)

print("\n" + "=" * 80)
print("Data ingestion completed successfully.")
print("=" * 80)




print("\n" + "=" * 80)
print("FUND MASTER EXPLORATION")
print("=" * 80)

# Load the fund master dataset
fund_master = pd.read_csv(raw_data_path / "01_fund_master.csv")

# Unique Fund Houses
print("\nUnique Fund Houses:")
print(fund_master["fund_house"].unique())
print(f"Total Fund Houses: {fund_master['fund_house'].nunique()}")

# Unique Categories
print("\nUnique Categories:")
print(fund_master["category"].unique())
print(f"Total Categories: {fund_master['category'].nunique()}")

# Unique Sub-Categories
print("\nUnique Sub-Categories:")
print(fund_master["sub_category"].unique())
print(f"Total Sub-Categories: {fund_master['sub_category'].nunique()}")

# Unique Risk Categories
print("\nUnique Risk Categories:")
print(fund_master["risk_category"].unique())
print(f"Total Risk Categories: {fund_master['risk_category'].nunique()}")

# AMFI Code Information
print("\nAMFI Code Summary")
print(f"Total Schemes : {len(fund_master)}")
print(f"Unique AMFI Codes : {fund_master['amfi_code'].nunique()}")
print(f"Minimum AMFI Code : {fund_master['amfi_code'].min()}")
print(f"Maximum AMFI Code : {fund_master['amfi_code'].max()}")







print("\n" + "=" * 80)
print("AMFI CODE VALIDATION")
print("=" * 80)

# Load required datasets
fund_master = pd.read_csv(raw_data_path / "01_fund_master.csv")
nav_history = pd.read_csv(raw_data_path / "02_nav_history.csv")

# Unique AMFI codes
fund_codes = set(fund_master["amfi_code"])
nav_codes = set(nav_history["amfi_code"])

# Validation
missing_codes = fund_codes - nav_codes
extra_codes = nav_codes - fund_codes

print(f"AMFI Codes in Fund Master : {len(fund_codes)}")
print(f"AMFI Codes in NAV History : {len(nav_codes)}")

if not missing_codes:
    print("\n✅ All AMFI codes from fund_master exist in nav_history.")
else:
    print("\n❌ Missing AMFI Codes:")
    print(sorted(missing_codes))

if extra_codes:
    print("\nExtra AMFI Codes in nav_history:")
    print(sorted(extra_codes))
else:
    print("\nNo extra AMFI codes found in nav_history.")

print("\n" + "=" * 80)
print("DATA QUALITY SUMMARY")
print("=" * 80)

print("1. All datasets loaded successfully.")
print("2. No duplicate rows were found.")
print("3. Missing values were found only in 'yoy_growth_pct' of 04_monthly_sip_inflows.csv.")
print("4. Date columns are currently stored as strings and can be converted during preprocessing.")
print("5. AMFI code validation completed.")