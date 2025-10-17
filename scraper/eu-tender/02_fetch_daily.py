import requests
import json
import time
import pandas as pd
import os
import sys
from datetime import datetime

# Import CPV configuration
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from cpv_config import OPTIMIZED_CPV_CODES

# EU TENDER FETCHER - USING VERIFIED OPTIMIZED CPV CODES
# Fetches EU tenders with optimized CPV codes and language filtering (DE, FR, EN, IT)
# Uses shared CPV configuration for consistency across scrapers

API_URL = "https://api.ted.europa.eu/v3/notices/search"
headers = {
    "accept": "application/json",
    "Content-Type": "application/json"
}

# Use optimized CPV codes from shared configuration
cpv_codes = OPTIMIZED_CPV_CODES

# Query for business opportunities (competition notices - subtype 16)
cpv_conditions = " OR ".join([f'classification-cpv = "{code}"' for code in cpv_codes])
query = f"""
publication-date = today() AND 
({cpv_conditions}) AND 
procedure-type = "Open" AND 
contract-nature = "Services" AND
notice-subtype = 16
"""

json_payload = {
    "query": query,
    "fields": [
        "classification-cpv",
        "title-part",
        "publication-date",
        "procedure-type",
        "contract-nature",
        "deadline",
        "buyer-name",
        "buyer-country",
        "notice-subtype",
        "title-proc",
        "description-proc",
        "submission-language",
        "links"
    ],
    "limit": 50,
    "scope": "ACTIVE",
    "paginationMode": "ITERATION"
}

all_notices = []
iteration_token = None
page_count = 0

while True:
    if iteration_token:
        json_payload["iterationNextToken"] = iteration_token
    elif "iterationNextToken" in json_payload:
        # Remove the token for the first request
        del json_payload["iterationNextToken"]

    page_count += 1
    print(f"Fetching page {page_count}...")

    response = requests.post(API_URL, headers=headers, json=json_payload)

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        break

    data = response.json()
    notices = data.get("notices", [])
    print(f"Fetched {len(notices)} notices from page {page_count}.")

    # Add the current page notices to the list
    all_notices.extend(notices)

    # Stop after collecting 50 tenders
    if len(all_notices) >= 50:
        print(f"Reached limit of 50 tenders. Stopping fetch.")
        break

    # Get the next iteration token
    iteration_token = data.get("iterationNextToken")

    # If there is no next token or no notices in the current page, break the loop
    if not iteration_token or not notices:
        print("No more pages or notices to fetch.")
        break

    # Add a small delay to avoid overwhelming the API
    time.sleep(1)

print(f"\nTotal notices collected across all pages: {len(all_notices)}")

# Filter for tenders with target languages (DE, FR, EN, IT)
target_languages = ['DEU', 'FRA', 'ENG', 'ITA']
filtered_notices = []

for notice in all_notices:
    submission_lang = notice.get('submission-language', [])
    
    # Check if submission language includes target languages
    if isinstance(submission_lang, list) and any(lang in target_languages for lang in submission_lang):
        filtered_notices.append(notice)

print(f"Tenders with target languages (DE, FR, EN, IT): {len(filtered_notices)}")

# If no filtered tenders, save all tenders for analysis
if not filtered_notices:
    print("No tenders with target languages found. Saving all tenders for analysis.")
    filtered_notices = all_notices

# Convert notices to DataFrame and save as CSV
if filtered_notices:
    # Flatten the notices data for CSV output
    flattened_notices = []
    
    for notice in filtered_notices:
        # Extract publication number for URL construction
        pub_number = notice.get('publication-number', '')
        ted_url = f"https://ted.europa.eu/en/notice/-/detail/{pub_number}" if pub_number else ''
        
        # Extract buyer name in German if available, otherwise English
        buyer_name_data = notice.get('buyer-name', {})
        buyer_name = ''
        if isinstance(buyer_name_data, dict):
            if 'de' in buyer_name_data and buyer_name_data['de']:
                buyer_name = ', '.join(buyer_name_data['de'])
            elif 'eng' in buyer_name_data and buyer_name_data['eng']:
                buyer_name = ', '.join(buyer_name_data['eng'])
            elif buyer_name_data:
                # If no German or English, take the first available language
                first_lang = list(buyer_name_data.keys())[0]
                buyer_name = ', '.join(buyer_name_data[first_lang])
        
        # Extract procedure title and description in German if available, otherwise English
        title_proc_data = notice.get('title-proc', {})
        title_proc = ''
        if isinstance(title_proc_data, dict):
            if 'de' in title_proc_data and title_proc_data['de']:
                title_proc = ' '.join(title_proc_data['de']) if isinstance(title_proc_data['de'], list) else str(title_proc_data['de'])
            elif 'eng' in title_proc_data and title_proc_data['eng']:
                title_proc = ' '.join(title_proc_data['eng']) if isinstance(title_proc_data['eng'], list) else str(title_proc_data['eng'])
            elif title_proc_data:
                first_lang = list(title_proc_data.keys())[0]
                title_proc = ' '.join(title_proc_data[first_lang]) if isinstance(title_proc_data[first_lang], list) else str(title_proc_data[first_lang])
        
        description_proc_data = notice.get('description-proc', {})
        description_proc = ''
        if isinstance(description_proc_data, dict):
            if 'de' in description_proc_data and description_proc_data['de']:
                description_proc = ' '.join(description_proc_data['de']) if isinstance(description_proc_data['de'], list) else str(description_proc_data['de'])
            elif 'eng' in description_proc_data and description_proc_data['eng']:
                description_proc = ' '.join(description_proc_data['eng']) if isinstance(description_proc_data['eng'], list) else str(description_proc_data['eng'])
            elif description_proc_data:
                first_lang = list(description_proc_data.keys())[0]
                description_proc = ' '.join(description_proc_data[first_lang]) if isinstance(description_proc_data[first_lang], list) else str(description_proc_data[first_lang])
        
        flattened_notice = {
            'publication_number': pub_number,
            'publication_date': notice.get('publication-date', ''),
            'title': notice.get('title-part', {}).get('text', ''),
            'buyer_name': buyer_name,
            'organization': buyer_name,  # Map buyer_name to organization for consistency
            'description': description_proc,
            'cpv_code': ', '.join(list(set(notice.get('classification-cpv', [])))),
            'title_language': notice.get('title-part', {}).get('language', ''),
            'procedure_type': notice.get('procedure-type', ''),
            'contract_nature': notice.get('contract-nature', ''),
            'deadline': notice.get('deadline', ''),
            'buyer_country': notice.get('buyer-country', ''),
            'notice_subtype': notice.get('notice-subtype', ''),
            'title_proc': title_proc,
            'language_submission': ', '.join(notice.get('submission-language', [])),
            'url': ted_url,
            'xml_url': notice.get('links', {}).get('xml', {}).get('MUL', ''),
            'pdf_url': notice.get('links', {}).get('pdf', {}).get('ENG', ''),
            'fetched_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        flattened_notices.append(flattened_notice)
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(flattened_notices)
    
    # Generate filename with timestamp and save in scraper/eu-tender directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Ensure the directory exists
    os.makedirs("scraper/eu-tender", exist_ok=True)
    
    filename = f"scraper/eu-tender/eu_tenders_daily_{timestamp}.csv"
    
    # Save to CSV
    df.to_csv(filename, index=False, encoding='utf-8')
    
    print(f"\n✅ Data saved to: {filename}")
    print(f"📊 File contains {len(df)} notices with {len(df.columns)} columns")
    
    # Display sample data
    print(f"\n📋 Sample data (first 3 rows):")
    print(df.head(3).to_string(index=False))
    
    # Display column info
    print(f"\n📈 Data summary:")
    print(f"   - Total notices: {len(df)}")
    print(f"   - Date range: {df['publication_date'].min()} to {df['publication_date'].max()}")
    print(f"   - Languages: {df['title_language'].value_counts().to_dict()}")
    
else:
    print("\n⚠️ No notices found to save.")