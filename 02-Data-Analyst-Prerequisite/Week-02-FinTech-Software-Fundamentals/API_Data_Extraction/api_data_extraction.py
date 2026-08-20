"""
Bluestock Data Analyst Internship - Week 2 Deliverable 3
API Data Extraction Assignment

Description:
    This script demonstrates programmatic data extraction from a public REST API,
    specifically the European Central Bank (ECB) Data Portal SDMX REST API.
    It retrieves official monthly foreign exchange rates (EUR against USD, GBP, JPY, INR),
    validates the HTTP response, parses the SDMX-JSON payload, structures the observations
    into a tabular pandas DataFrame, and exports the clean dataset to CSV.

Target API:
    European Central Bank (ECB) Data Portal - SDMX REST Web Service
    Endpoint: https://data-api.ecb.europa.eu/service/data/EXR/M.USD+GBP+JPY+INR.EUR.SP00.A
    Documentation: https://data.ecb.europa.eu/help/api/overview
"""

import sys
import logging
from pathlib import Path
import requests
import pandas as pd

# Configure logging for clear pipeline traceability
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("ECB_Data_Extractor")

# Constants & Endpoint Configuration
BASE_URL = "https://data-api.ecb.europa.eu/service/data/EXR/M.USD+GBP+JPY+INR.EUR.SP00.A"
REQUEST_PARAMS = {
    "format": "jsondata",
    "startPeriod": "2023-01",
    "endPeriod": "2024-06",
    "detail": "dataonly"
}
REQUEST_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Bluestock-Internship-Data-Pipeline/1.0"
}
OUTPUT_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = OUTPUT_DIR / "api_data.csv"


def fetch_ecb_exchange_rates(url: str, params: dict, headers: dict) -> dict:
    """
    Executes an HTTP GET request to the ECB SDMX REST API and validates the JSON response.
    
    Args:
        url: Base endpoint URL.
        params: Query parameters including format and date ranges.
        headers: Request headers specifying accepted MIME types.
        
    Returns:
        dict: Parsed JSON response payload from the ECB API.
    """
    logger.info("Initiating HTTP GET request to ECB API: %s", url)
    logger.info("Query parameters: %s", params)
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=20)
        
        # Check HTTP Status Code
        logger.info("HTTP Response Status: %s (%s)", response.status_code, response.reason)
        response.raise_for_status()
        
        # Parse JSON
        payload = response.json()
        logger.info("Successfully retrieved and parsed JSON payload (%d bytes).", len(response.content))
        return payload

    except requests.exceptions.HTTPError as http_err:
        logger.error("HTTP error occurred during API extraction: %s", http_err)
        raise
    except requests.exceptions.ConnectionError as conn_err:
        logger.error("Connection error occurred while connecting to ECB endpoint: %s", conn_err)
        raise
    except requests.exceptions.Timeout as timeout_err:
        logger.error("Request timed out: %s", timeout_err)
        raise
    except requests.exceptions.RequestException as req_err:
        logger.error("An unexpected error occurred during the request: %s", req_err)
        raise
    except ValueError as json_err:
        logger.error("Failed to decode JSON response: %s", json_err)
        raise


def parse_sdmx_json_to_dataframe(payload: dict) -> pd.DataFrame:
    """
    Parses ECB SDMX-JSON structured dimensions and series observations into a flat DataFrame.
    
    Args:
        payload: Decoded JSON dictionary from ECB SDMX REST API.
        
    Returns:
        pd.DataFrame: Tabular DataFrame containing normalized exchange rate records.
    """
    logger.info("Transforming SDMX-JSON structure into tabular DataFrame...")
    
    if "structure" not in payload or "dataSets" not in payload:
        raise KeyError("Invalid SDMX-JSON payload: missing 'structure' or 'dataSets' keys.")

    structure = payload["structure"]
    datasets = payload["dataSets"]
    
    if not datasets or "series" not in datasets[0]:
        raise ValueError("No series data available in the retrieved dataset.")

    # Extract Series and Observation dimension mappings
    series_dims = structure["dimensions"]["series"]
    obs_dims = structure["dimensions"]["observation"]
    
    # Locate CURRENCY dimension index
    curr_dim_idx = next(
        (i for i, dim in enumerate(series_dims) if dim.get("id") == "CURRENCY"),
        None
    )
    if curr_dim_idx is None:
        raise ValueError("Could not find 'CURRENCY' dimension in series metadata.")
        
    currencies = [item["id"] for item in series_dims[curr_dim_idx]["values"]]
    time_periods = [item["id"] for item in obs_dims[0]["values"]]
    
    records = []
    series_data = datasets[0]["series"]
    
    for series_key, series_content in series_data.items():
        # Series key is colon-separated dimension indices, e.g. "0:1:0:0:0"
        key_indices = [int(idx) for idx in series_key.split(":")]
        target_currency = currencies[key_indices[curr_dim_idx]]
        
        observations = series_content.get("observations", {})
        for obs_idx_str, obs_values in observations.items():
            obs_idx = int(obs_idx_str)
            period = time_periods[obs_idx]
            exchange_rate = float(obs_values[0]) if obs_values and obs_values[0] is not None else None
            
            records.append({
                "period": period,
                "base_currency": "EUR",
                "target_currency": target_currency,
                "exchange_rate": exchange_rate,
                "frequency": "Monthly",
                "rate_type": "Foreign Exchange Reference Rate (Spot Average)",
                "source": "European Central Bank (ECB)"
            })
            
    df = pd.DataFrame(records)
    
    # Sort and clean
    df = df.sort_values(by=["period", "target_currency"]).reset_index(drop=True)
    logger.info("Extraction complete. Generated %d records across %d currencies.", len(df), df["target_currency"].nunique())
    return df


def main():
    """Main execution entrypoint."""
    print("=" * 70)
    print("Bluestock Data Analyst Internship - API Data Extraction Assignment")
    print("Target: European Central Bank (ECB) Foreign Exchange Rates API")
    print("=" * 70)
    
    try:
        # Step 1: HTTP Request & Response Validation
        payload = fetch_ecb_exchange_rates(BASE_URL, REQUEST_PARAMS, REQUEST_HEADERS)
        
        # Step 2: Parse SDMX-JSON to pandas DataFrame
        df = parse_sdmx_json_to_dataframe(payload)
        
        # Step 3: Inspect DataFrame summary
        print("\n--- Extracted Dataset Preview (First 8 Rows) ---")
        print(df.head(8).to_string(index=False))
        
        print("\n--- Summary Statistics by Currency ---")
        stats = df.groupby("target_currency")["exchange_rate"].agg(
            Count="count",
            Min="min",
            Mean="mean",
            Max="max"
        ).round(4)
        print(stats)
        
        # Step 4: Export to CSV
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        df.to_csv(OUTPUT_FILE, index=False)
        logger.info("Saved clean dataset to %s", OUTPUT_FILE)
        print(f"\n[SUCCESS] Successfully saved {len(df)} records to: {OUTPUT_FILE.name}")
        print("=" * 70)
        
    except Exception as err:
        logger.critical("API extraction pipeline failed: %s", err, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
