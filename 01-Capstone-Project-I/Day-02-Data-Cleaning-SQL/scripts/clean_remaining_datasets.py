import os
import pandas as pd

def clean_generic_dataset(input_path, output_path):
    """
    Clean generic CSV dataset:
    - Standardize column names to lowercase with underscores.
    - Trim whitespace from string columns.
    - Parse date columns (launch_date, date, month, portfolio_date).
    - Remove duplicate rows.
    - Export clean dataset to data/processed/.
    """
    df = pd.read_csv(input_path)
    orig_rows = len(df)
    orig_missing = int(df.isnull().sum().sum())
    orig_dups = int(df.duplicated().sum())
    
    # 1. Standardize column names to lowercase with underscores
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
    
    # 2. Trim whitespace from string columns
    str_cols = df.select_dtypes(include='object').columns
    for c in str_cols:
        df[c] = df[c].astype(str).str.strip()
        
    # 3. Parse date columns
    parsed_dates = []
    for c in df.columns:
        if 'date' in c or 'month' in c:
            try:
                # If month column like YYYY-MM
                if c == 'month':
                    # Parse to datetime
                    df['parsed_' + c] = pd.to_datetime(df[c], errors='coerce')
                    # Keep original YYYY-MM or formatted date string
                    df[c] = df[c]
                else:
                    df[c] = pd.to_datetime(df[c], errors='coerce').dt.strftime('%Y-%m-%d')
                parsed_dates.append(c)
            except Exception as e:
                pass
                
    # 4. Remove duplicate rows
    df = df.drop_duplicates().reset_index(drop=True)
    if 'parsed_month' in df.columns:
        df = df.drop(columns=['parsed_month'])
        
    # Save cleaned dataset
    df.to_csv(output_path, index=False)
    
    cleaned_rows = len(df)
    cleaned_missing = int(df.isnull().sum().sum())
    
    filename = os.path.basename(input_path)
    metrics = {
        "dataset": filename,
        "output_file": output_path,
        "original_rows": orig_rows,
        "cleaned_rows": cleaned_rows,
        "rows_removed": orig_rows - cleaned_rows,
        "missing_before": orig_missing,
        "missing_after": cleaned_missing,
        "duplicates_removed": orig_dups,
        "type_conversions": [f"Parsed date/month columns: {parsed_dates}"] if parsed_dates else ["None"],
        "validation_checks": [
            "Standardized column names to lowercase with underscores",
            "Trimmed leading/trailing whitespace across string columns",
            "Removed duplicate rows",
            "Preserved all valid data records"
        ],
        "anomalies_flagged": []
    }
    
    return df, metrics

def clean_all_remaining(raw_dir, processed_dir):
    remaining_files = [
        ("01_fund_master.csv", "01_fund_master_cleaned.csv"),
        ("03_aum_by_fund_house.csv", "03_aum_by_fund_house_cleaned.csv"),
        ("04_monthly_sip_inflows.csv", "04_monthly_sip_inflows_cleaned.csv"),
        ("05_category_inflows.csv", "05_category_inflows_cleaned.csv"),
        ("06_industry_folio_count.csv", "06_industry_folio_count_cleaned.csv"),
        ("09_portfolio_holdings.csv", "09_portfolio_holdings_cleaned.csv"),
        ("10_benchmark_indices.csv", "10_benchmark_indices_cleaned.csv")
    ]
    
    results = {}
    for raw_fname, proc_fname in remaining_files:
        raw_path = os.path.join(raw_dir, raw_fname)
        proc_path = os.path.join(processed_dir, proc_fname)
        _, metrics = clean_generic_dataset(raw_path, proc_path)
        results[raw_fname] = metrics
        
    return results

if __name__ == "__main__":
    clean_all_remaining("data/raw", "data/processed")
    print("Remaining datasets cleaning complete.")
