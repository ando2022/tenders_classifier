"""
Fetch a single SIMAP tender by ID and save to CSV
"""

import requests
import json
import pandas as pd
import sys
import os

def fetch_single_tender(tender_id, output_file):
    """
    Fetches a single SIMAP tender by its ID and saves the raw JSON data to a CSV file.
    """
    print(f"[RUNNING] Fetching tender ID: {tender_id}")

    base_url = "https://www.simap.ch/api/v1/projects/"
    url = f"{base_url}{tender_id}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()

        if data:
            # Convert the single JSON object into a list for DataFrame creation
            df = pd.DataFrame([data])
            df.to_csv(output_file, index=False, encoding='utf-8')
            print(f"[SUCCESS] Tender '{tender_id}' fetched and saved to {output_file}")
        else:
            print(f"[INFO] No data found for tender ID: {tender_id}")
            # Create an empty CSV if no data is found
            pd.DataFrame().to_csv(output_file, index=False, encoding='utf-8')

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to fetch tender ID {tender_id}: {e}")
        # Create an empty CSV on error
        pd.DataFrame().to_csv(output_file, index=False, encoding='utf-8')
    except json.JSONDecodeError:
        print(f"[ERROR] Failed to decode JSON response for tender ID: {tender_id}")
        # Create an empty CSV on error
        pd.DataFrame().to_csv(output_file, index=False, encoding='utf-8')
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")
        # Create an empty CSV on error
        pd.DataFrame().to_csv(output_file, index=False, encoding='utf-8')

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python 02c_fetch_single_tender.py <tender_id> <output_file>")
        sys.exit(1)

    tender_id = sys.argv[1]
    output_file = sys.argv[2]

    # Ensure the output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    fetch_single_tender(tender_id, output_file)
