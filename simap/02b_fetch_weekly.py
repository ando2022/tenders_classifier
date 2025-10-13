"""
Fetch SIMAP tenders from the last 7 days and save to CSV
Based on Simap_scraper_damlina.ipynb
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from time import sleep
from datetime import datetime, timedelta
import pandas as pd

# Date range: last 7 days
today = datetime.now()
week_ago = today - timedelta(days=7)
pub_date_from = week_ago.strftime("%Y-%m-%d")
pub_date_to = today.strftime("%Y-%m-%d")

print(f"Fetching SIMAP data from {pub_date_from} to {pub_date_to} (last 7 days)")

# Base API endpoint (public/prod)
base_url = "https://prod.simap.ch/api/publications/v2/project/project-search"

# Query parameters (corrected API parameters)
base_params = {
    "processTypes": ["open"],           # Offenes Verfahren
    "newestPubTypes": ["tender"],       # Ausschreibung (corrected parameter name)
    "projectSubTypes": ["service"],     # Dienstleistung
    # CPV codes - economic research and related services
    "cpvCodes": [
        "72000000",  # IT services (all)
        "79300000",  # Market research
        "73100000",  # Research services
        "79311400",  # Feasibility studies
        "72314000",  # Data warehousing
        "79416000",  # Public relations
        "72320000",  # Database services
        "98300000",  # Diverse services
        "79310000",  # Survey services
        "79000000",  # Business services (all)
        "79311410",  # Economic research
    ],
    "pageSize": 100,
    "newestPublicationFrom": pub_date_from,  # Corrected parameter name
    "newestPublicationUntil": pub_date_to,   # Corrected parameter name
}

headers = {"accept": "application/json"}

# Robust session (retries/backoff)
session = requests.Session()
session.headers.update(headers)
session.mount("https://", HTTPAdapter(max_retries=Retry(
    total=6, connect=6, read=6, status=6,
    backoff_factor=0.7,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)))

# Fetch all results with pagination
all_results = []
seen_ids = set()
last_item = None
page = 1

print("Fetching project summaries...")
while True:
    params = dict(base_params)
    if last_item:
        params["lastItem"] = last_item

    r = session.get(base_url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    projects = data.get("projects", [])
    if not projects:
        break

    # Collect & dedupe by project id
    for p in projects:
        pid = p.get("id")
        if pid and pid not in seen_ids:
            seen_ids.add(pid)
            all_results.append(p)

    # paging tokens vary by env; handle both "pagination" and "paging"
    paging = data.get("pagination") or data.get("paging") or {}
    last_item = paging.get("lastItem")
    if not last_item:
        break

    print(f"  Page {page}: {len(projects)} projects")
    page += 1
    sleep(0.2)  # be polite to the API

print(f"Total project summaries fetched: {len(all_results)}")

# Create initial DataFrame
result_df = pd.DataFrame(all_results)

if len(result_df) == 0:
    print("No results found for the specified date range.")
    result_df.to_csv("simap_weekly.csv", index=False)
    print("Empty simap_weekly.csv created.")
    exit(0)

# Fetch detailed data for each project
print("\nFetching detailed data for each project...")
detailed_data = []

for idx, row in result_df.drop_duplicates(subset=["id", "publicationId"]).iterrows():
    project_id = row.get("id")
    publication_id = row.get("publicationId")

    if not project_id or not publication_id:
        continue

    details_url = f"https://prod.simap.ch/api/publications/v1/project/{project_id}/publication-details/{publication_id}"

    try:
        response = session.get(details_url, headers=headers, timeout=30)
        response.raise_for_status()
        detail_data = response.json()
        detail_data["project_id"] = project_id
        detail_data["publication_id"] = publication_id
        detailed_data.append(detail_data)
        
        if len(detailed_data) % 10 == 0:
            print(f"  Fetched {len(detailed_data)} details...")
            
    except requests.RequestException as e:
        print(f"  Warning: Failed to fetch details for {project_id}/{publication_id}: {e}")
        continue

print(f"Total detailed records fetched: {len(detailed_data)}")

# Merge summary and details
detail_df = pd.DataFrame(detailed_data)
merged_df = result_df.drop_duplicates(subset=["id", "publicationId"]).merge(
    detail_df, 
    left_on=["id", "publicationId"], 
    right_on=["project_id", "publication_id"],
    how="left"
)

# Extract orderDescription from procurement field
if "procurement" in merged_df.columns:
    merged_df["orderDescription"] = merged_df["procurement"].apply(
        lambda x: x.get("orderDescription") if isinstance(x, dict) and "orderDescription" in x else None
    )

# Save to CSV in unlabeled folder
import os
os.makedirs("unlabeled", exist_ok=True)
output_file = "unlabeled/simap_weekly.csv"
merged_df.to_csv(output_file, index=False, encoding='utf-8')
print(f"\n✅ Data saved to {output_file}")
print(f"   Total records: {len(merged_df)}")
print(f"   Date range: {pub_date_from} to {pub_date_to} (last 7 days)")
print(f"   Columns: {len(merged_df.columns)}")
