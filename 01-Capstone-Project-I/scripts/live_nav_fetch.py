import pandas as pd
import requests
from pathlib import Path

# Folder to save API-fetched CSV files
output_folder = Path("data/api")
output_folder.mkdir(parents=True, exist_ok=True)

# Required schemes
schemes = {
    "SBI_Bluechip": 119551,
    "ICICI_Bluechip": 120503,
    "Nippon_Large_Cap": 118632,
    "Axis_Bluechip": 119092,
    "Kotak_Bluechip": 120841
}

for file_name, amfi_code in schemes.items():

    url = f"https://api.mfapi.in/mf/{amfi_code}"

    try:
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()

        nav_df = pd.DataFrame(data["data"])

        output_file = output_folder / f"{file_name}_NAV.csv"

        nav_df.to_csv(output_file, index=False)

        print("=" * 60)
        print(f"Scheme : {data['meta']['scheme_name']}")
        print(f"AMFI Code : {amfi_code}")
        print(f"Records : {len(nav_df)}")
        print(f"Saved to : {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {amfi_code}")
        print(e)

    except KeyError:
        print(f"Unexpected response for {amfi_code}")

print("\n" + "=" * 60)
print("All requested NAV datasets have been fetched successfully.")
print(f"Saved in: {output_folder}")


