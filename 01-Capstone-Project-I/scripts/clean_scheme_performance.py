import pandas as pd

def clean_scheme_performance(input_path, output_path):
    """
    Clean 07_scheme_performance.csv dataset:
    - Convert return & risk metric columns to numeric (strip % if present).
    - Validate expense_ratio_pct (0.1 to 2.5).
    - Create expense_ratio_flag (True if outside [0.1, 2.5], False otherwise). Do not delete anomalies.
    - Trim whitespace across text fields.
    - Remove duplicates.
    """
    df = pd.read_csv(input_path)
    orig_rows = len(df)
    orig_missing = int(df.isnull().sum().sum())
    orig_dups = int(df.duplicated().sum())
    
    # 1. Trim whitespace from string columns
    str_cols = df.select_dtypes(include='object').columns
    for c in str_cols:
        df[c] = df[c].astype(str).str.strip()
        
    # 2. Convert all return & risk metric columns to numeric
    numeric_cols = [
        'return_1yr_pct', 'return_3yr_pct', 'return_5yr_pct',
        'benchmark_3yr_pct', 'alpha', 'beta', 'sharpe_ratio',
        'sortino_ratio', 'std_dev_ann_pct', 'max_drawdown_pct',
        'expense_ratio_pct', 'aum_crore', 'morningstar_rating'
    ]
    
    for c in numeric_cols:
        if c in df.columns:
            if df[c].dtype == 'object':
                df[c] = df[c].astype(str).str.replace('%', '').str.strip()
            df[c] = pd.to_numeric(df[c], errors='coerce')
            
    # 3. Validate expense_ratio_pct between 0.1 and 2.5 & create flag
    # True if outside range [0.1, 2.5], False if inside
    df['expense_ratio_flag'] = (df['expense_ratio_pct'] < 0.1) | (df['expense_ratio_pct'] > 2.5)
    flagged_anomalies_count = int(df['expense_ratio_flag'].sum())
    
    # 4. Remove exact duplicate rows
    df = df.drop_duplicates().reset_index(drop=True)
    dups_removed = orig_rows - len(df)
    
    # Save cleaned file
    df.to_csv(output_path, index=False)
    
    cleaned_rows = len(df)
    cleaned_missing = int(df.isnull().sum().sum())
    
    metrics = {
        "dataset": "07_scheme_performance.csv",
        "output_file": output_path,
        "original_rows": orig_rows,
        "cleaned_rows": cleaned_rows,
        "rows_removed": orig_rows - cleaned_rows,
        "missing_before": orig_missing,
        "missing_after": cleaned_missing,
        "duplicates_removed": orig_dups,
        "type_conversions": [f"Converted {len(numeric_cols)} return and risk metric columns to numeric float/int types"],
        "validation_checks": [
            f"Validated expense_ratio_pct range [0.1, 2.5]",
            f"Added expense_ratio_flag column without deleting anomalous rows",
            "Validated risk metric columns (Alpha, Beta, Sharpe, Sortino, Std Dev) as numeric"
        ],
        "anomalies_flagged": [f"Expense ratio outside [0.1, 2.5] range count: {flagged_anomalies_count}"]
    }
    
    return df, metrics

if __name__ == "__main__":
    clean_scheme_performance(
        "data/raw/07_scheme_performance.csv",
        "data/processed/07_scheme_performance_cleaned.csv"
    )
    print("Scheme performance cleaning complete.")
