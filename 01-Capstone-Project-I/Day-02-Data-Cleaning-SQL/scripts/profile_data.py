import os
import glob
import pandas as pd
import json

def profile_csvs(data_dir):
    csv_files = sorted(glob.glob(os.path.join(data_dir, "*.csv")))
    profiles = {}
    
    for filepath in csv_files:
        filename = os.path.basename(filepath)
        print(f"--- Profiling {filename} ---")
        df = pd.read_csv(filepath)
        
        # Basic info
        rows, cols = df.shape
        col_names = list(df.columns)
        dtypes = {col: str(df[col].dtype) for col in df.columns}
        missing = df.isnull().sum().to_dict()
        duplicates = int(df.duplicated().sum())
        
        # Detailed quality checks
        quality_issues = []
        
        # 1. Leading/Trailing spaces & Empty strings & Mixed Casing & Numeric strings
        str_cols_info = {}
        numeric_as_str = []
        date_issues = []
        neg_values = []
        whitespace_issues = []
        empty_str_counts = {}
        mixed_casing = []
        
        for col in df.columns:
            # Check missing
            m_count = df[col].isnull().sum()
            
            # If string / object column
            if df[col].dtype == 'object':
                # non-null values
                non_null_s = df[col].dropna().astype(str)
                
                # Check leading/trailing spaces
                has_space = non_null_s.apply(lambda x: len(x) != len(x.strip())).sum()
                if has_space > 0:
                    whitespace_issues.append((col, int(has_space)))
                
                # Check empty or whitespace-only strings
                empty_cnt = non_null_s.apply(lambda x: len(x.strip()) == 0).sum()
                if empty_cnt > 0:
                    empty_str_counts[col] = int(empty_cnt)
                
                # Check mixed casing
                cases = set()
                for val in non_null_s.head(500):
                    if val.isupper(): cases.add("UPPER")
                    elif val.islower(): cases.add("lower")
                    elif val.istitle(): cases.add("Title")
                    elif any(c.isupper() for c in val) and any(c.islower() for c in val): cases.add("Mixed")
                if len(cases) > 1:
                    mixed_casing.append((col, list(cases)))
                    
                # Check numeric stored as string (currency, commas, %, numeric chars)
                # Test removing commas, %, ₹, spaces
                sample_clean = non_null_s.str.replace(r'[\$,₹,% ,]', '', regex=True)
                numeric_converted = pd.to_numeric(sample_clean, errors='coerce')
                if numeric_converted.notnull().sum() > 0.8 * len(non_null_s) and not pd.to_numeric(non_null_s, errors='coerce').notnull().all():
                    numeric_as_str.append(col)
                elif not pd.to_numeric(non_null_s, errors='coerce').isnull().all():
                    # check if pure digits stored as object
                    numeric_as_str.append(col)

                # Check date formats
                if 'date' in col.lower() or 'month' in col.lower() or 'time' in col.lower() or 'launch' in col.lower():
                    # try parsing
                    parsed = pd.to_datetime(non_null_s, errors='coerce')
                    unparseable = parsed.isnull().sum()
                    date_issues.append((col, int(unparseable)))
            
            # Numeric column checks
            if pd.api.types.is_numeric_dtype(df[col]):
                neg_count = (df[col] < 0).sum()
                if neg_count > 0:
                    neg_values.append((col, int(neg_count)))
                    
        # Key candidates
        cardinality = {col: int(df[col].nunique()) for col in df.columns}
        pk_candidates = [col for col in df.columns if df[col].nunique() == rows and df[col].isnull().sum() == 0]
        
        profiles[filename] = {
            "shape": [rows, cols],
            "columns": col_names,
            "dtypes": dtypes,
            "missing": missing,
            "duplicates": duplicates,
            "head_5": df.head(5).to_dict(orient="records"),
            "describe_num": df.describe(include=['number']).to_dict() if len(df.select_dtypes(include=['number']).columns) > 0 else {},
            "describe_cat": df.describe(include=['object']).to_dict() if len(df.select_dtypes(include=['object']).columns) > 0 else {},
            "whitespace_issues": whitespace_issues,
            "empty_str_counts": empty_str_counts,
            "mixed_casing": mixed_casing,
            "numeric_as_str": numeric_as_str,
            "date_issues": date_issues,
            "neg_values": neg_values,
            "cardinality": cardinality,
            "pk_candidates": pk_candidates
        }
        
    return profiles

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    raw_dir = os.path.join(base_dir, "data", "raw")
    reports_dir = os.path.join(base_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    results = profile_csvs(raw_dir)
    out_json = os.path.join(reports_dir, "data_profile_summary.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Profiling complete. Summary written to {out_json}")
