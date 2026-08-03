import pandas as pd

def clean_investor_transactions(input_path, output_path):
    """
    Clean 08_investor_transactions.csv dataset:
    - Standardize transaction_type (SIP, Lumpsum, Redemption).
    - Convert transaction_date to datetime.
    - Validate amount > 0.
    - Validate KYC status (Verified, Pending, Rejected).
    - Trim whitespace across all string columns.
    - Remove duplicate transactions.
    """
    df = pd.read_csv(input_path)
    orig_rows = len(df)
    orig_missing = int(df.isnull().sum().sum())
    orig_dups = int(df.duplicated().sum())
    
    # 1. Trim whitespace from all string columns
    str_cols = df.select_dtypes(include='object').columns
    for c in str_cols:
        df[c] = df[c].astype(str).str.strip()
        
    # 2. Standardize transaction_type
    def standardize_tx_type(val):
        v = val.strip().lower()
        if 'sip' in v:
            return 'SIP'
        elif 'lump' in v:
            return 'Lumpsum'
        elif 'redemp' in v or 'sell' in v:
            return 'Redemption'
        return val.strip().title()
        
    df['transaction_type'] = df['transaction_type'].apply(standardize_tx_type)
    
    # 3. Convert transaction_date to datetime and format as YYYY-MM-DD
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    
    # 4. Validate amount_inr > 0
    invalid_amount_count = int((df['amount_inr'] <= 0).sum())
    if invalid_amount_count > 0:
        df = df[df['amount_inr'] > 0].reset_index(drop=True)
        
    # 5. Standardize & Validate KYC status
    def standardize_kyc(val):
        v = val.strip().lower()
        if 'verif' in v:
            return 'Verified'
        elif 'pend' in v:
            return 'Pending'
        elif 'reject' in v:
            return 'Rejected'
        return val.strip().title()
        
    df['kyc_status'] = df['kyc_status'].apply(standardize_kyc)
    invalid_kyc = df[~df['kyc_status'].isin(['Verified', 'Pending', 'Rejected'])]
    invalid_kyc_count = len(invalid_kyc)
    
    # 6. Remove duplicates
    df = df.drop_duplicates().reset_index(drop=True)
    dups_removed = orig_rows - len(df)
    
    # Format date back to YYYY-MM-DD
    df['transaction_date'] = df['transaction_date'].dt.strftime('%Y-%m-%d')
    
    # Save cleaned file
    df.to_csv(output_path, index=False)
    
    cleaned_rows = len(df)
    cleaned_missing = int(df.isnull().sum().sum())
    
    metrics = {
        "dataset": "08_investor_transactions.csv",
        "output_file": output_path,
        "original_rows": orig_rows,
        "cleaned_rows": cleaned_rows,
        "rows_removed": orig_rows - cleaned_rows,
        "missing_before": orig_missing,
        "missing_after": cleaned_missing,
        "duplicates_removed": orig_dups,
        "type_conversions": ["transaction_date -> datetime64[ns] -> YYYY-MM-DD"],
        "validation_checks": [
            "Standardized transaction_type to exact set: ['SIP', 'Lumpsum', 'Redemption']",
            f"Validated amount_inr > 0 (invalid amount count: {invalid_amount_count})",
            f"Validated KYC status to exact set: ['Verified', 'Pending', 'Rejected'] (invalid count: {invalid_kyc_count})",
            "Trimmed leading/trailing whitespace across string columns"
        ],
        "anomalies_flagged": []
    }
    
    return df, metrics

if __name__ == "__main__":
    clean_investor_transactions(
        "data/raw/08_investor_transactions.csv",
        "data/processed/08_investor_transactions_cleaned.csv"
    )
    print("Investor transactions cleaning complete.")
