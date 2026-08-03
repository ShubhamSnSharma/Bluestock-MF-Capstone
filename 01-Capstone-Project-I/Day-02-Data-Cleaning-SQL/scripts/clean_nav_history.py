import pandas as pd

def clean_nav_history(input_path, output_path):
    """
    Clean 02_nav_history.csv dataset:
    - Parse date into datetime.
    - Sort by amfi_code then date.
    - Remove duplicate rows.
    - Validate nav > 0.
    - Forward-fill missing NAV values within each amfi_code.
    - Ensure no duplicate (amfi_code, date) combinations remain.
    """
    df = pd.read_csv(input_path)
    orig_rows = len(df)
    orig_missing = int(df.isnull().sum().sum())
    orig_dups = int(df.duplicated().sum())
    
    # 1. Parse date column to datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # 2. Sort by amfi_code then date
    df = df.sort_values(by=['amfi_code', 'date']).reset_index(drop=True)
    
    # 3. Remove duplicate rows
    df = df.drop_duplicates().reset_index(drop=True)
    dups_removed = orig_rows - len(df)
    
    # 4. Forward-fill missing NAV values within each amfi_code only
    df['nav'] = df.groupby('amfi_code')['nav'].ffill()
    
    # 5. Validate nav > 0
    invalid_nav_count = int((df['nav'] <= 0).sum())
    if invalid_nav_count > 0:
        df = df[df['nav'] > 0].reset_index(drop=True)
        
    # 6. Ensure no duplicate (amfi_code, date) combinations remain
    dup_keys = int(df[['amfi_code', 'date']].duplicated().sum())
    if dup_keys > 0:
        df = df.drop_duplicates(subset=['amfi_code', 'date'], keep='last').reset_index(drop=True)
        
    # Format date back to ISO string YYYY-MM-DD
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    
    # Save cleaned file
    df.to_csv(output_path, index=False)
    
    cleaned_rows = len(df)
    cleaned_missing = int(df.isnull().sum().sum())
    
    metrics = {
        "dataset": "02_nav_history.csv",
        "output_file": output_path,
        "original_rows": orig_rows,
        "cleaned_rows": cleaned_rows,
        "rows_removed": orig_rows - cleaned_rows,
        "missing_before": orig_missing,
        "missing_after": cleaned_missing,
        "duplicates_removed": orig_dups,
        "type_conversions": ["date -> datetime64[ns] -> YYYY-MM-DD"],
        "validation_checks": [
            f"nav > 0 validated (invalid count: {invalid_nav_count})",
            f"Sorted by amfi_code, date",
            f"Forward-filled missing NAV per amfi_code",
            f"Composite key (amfi_code, date) uniqueness enforced (duplicate keys removed: {dup_keys})"
        ],
        "anomalies_flagged": []
    }
    
    return df, metrics

if __name__ == "__main__":
    clean_nav_history(
        "data/raw/02_nav_history.csv",
        "data/processed/02_nav_history_cleaned.csv"
    )
    print("NAV history cleaning complete.")
