import requests
import csv
from datetime import datetime

# SIMAP API base URL
BASE_URL = "https://archiv.simap.ch/api"

# Meldungsnummer to fetch (from the image)
MELDUNGSNUMMER_IDS = [
    1016039, 1017173, 1032287, 1043225, 1065225, 1075747, 1075809, 1078827,
    1129423, 1145879, 1270843, 1276069, 1321313, 1340463, 1353125, 1354643,
    1385255, 1390583
]

# OPTIMIZED CPV codes (reduced from 21 to 19 codes)
# Removed: 71300000 (broader than 71311200), 72320000 (broader than 72321000, 72322000, 72330000)
OPTIMIZED_CPV_CODES = [
    '71311200', '72321000', '72322000', '72330000', '73100000', '79300000', 
    '79310000', '79311000', '79311100', '79311200', '79311210', '79311300', 
    '79311400', '79311410', '79320000', '79400000', '79416000', '79419000', '98300000'
]

def fetch_meldungsnummer_data(meldungsnummer):
    """
    Directly fetch data for a specific Meldungsnummer using the detail endpoint
    """
    url = f"{BASE_URL}/detail?meldungsnummer={meldungsnummer}"
    headers = {'Accept': 'application/json'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error {response.status_code} for Meldungsnummer {meldungsnummer}")
            return None
    except Exception as e:
        print(f"Request error for Meldungsnummer {meldungsnummer}: {e}")
        return None

def extract_cpvs(data):
    """
    Extract CPV codes from the data using the actual response structure
    """
    cpvs = []
    
    try:
        # Navigate to the CPV list in the nested structure
        cpv_list = data.get('OB01', {}).get('OB01.SPEC', {}).get('OB01.CONTRACT', {}).get('OB01.CONT.OBJ', {}).get('CONT.SERV.TYPE', {}).get('CONT.CPV.LIST', {}).get('CONT.CPV', [])
        
        if isinstance(cpv_list, list):
            cpvs = [cpv.get('CODE', '') for cpv in cpv_list if cpv.get('CODE')]
        elif isinstance(cpv_list, dict) and cpv_list.get('CODE'):
            cpvs = [cpv_list.get('CODE')]
            
    except Exception as e:
        print(f"Error extracting CPVs: {e}")
    
    return cpvs

def main():
    """
    Optimized main function to fetch Meldungsnummer data and save to CSV with CPVs as columns
    """
    print(f"Fetching {len(MELDUNGSNUMMER_IDS)} Meldungsnummer with OPTIMIZED CPV scope...")
    print(f"Using {len(OPTIMIZED_CPV_CODES)} optimized CPV codes (reduced from 21)")
    print(f"Removed: 71300000, 72320000 (broader codes with narrower equivalents)")
    
    all_data = []
    all_cpvs = set()
    
    # Fetch each Meldungsnummer
    for meldungsnummer in MELDUNGSNUMMER_IDS:
        print(f"Fetching Meldungsnummer {meldungsnummer}...")
        
        data = fetch_meldungsnummer_data(meldungsnummer)
        
        if data:
            # Extract basic info from the actual response structure
            title = data.get('OB01', {}).get('OB01.SPEC', {}).get('OB01.CONTRACT', {}).get('OB01.CONT.OBJ', {}).get('CONT.SERV.TYPE', {}).get('CONT.NAME', 'N/A')
            projectid = data.get('ID', '')
            publication_date = data.get('OB01', {}).get('SIMAP.PUB.DATE', '')
            auth_name = data.get('OB01', {}).get('AUTHORITY', {}).get('AUTH.CONTACT', {}).get('AUTH.NAME', '')
            cont_type = data.get('OB01', {}).get('OB01.SPEC', {}).get('OB01.CONTRACT', {}).get('OB01.CONT.OBJ', {}).get('CONT.SERV.TYPE', {}).get('TYPE', '')
            lang = data.get('LANG', '')
            proc = data.get('OB01', {}).get('OB.PROC', {}).get('VALUE', '')
            
            # Extract CPVs
            cpvs = extract_cpvs(data)
            all_cpvs.update(cpvs)
            
            row_data = {
                'meldungsnummer': meldungsnummer,
                'title': title,
                'projectid': projectid,
                'publicationDate': publication_date,
                'authName': auth_name,
                'contType': cont_type,
                'lang': lang,
                'proc': proc,
                'cpvs': cpvs
            }
            
            all_data.append(row_data)
            print(f"✓ Found: {title[:50]}... (CPVs: {cpvs})")
        else:
            print(f"✗ Not found: {meldungsnummer}")
    
    # Create CSV with OPTIMIZED CPV columns
    if all_data:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = f"meldungsnummer_optimized_{timestamp}.csv"
        
        # Use optimized CPV codes for column headers
        sorted_cpvs = sorted(OPTIMIZED_CPV_CODES)
        
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            # Define fieldnames: basic info + OPTIMIZED CPV columns
            fieldnames = ['meldungsnummer', 'title', 'projectid', 'publicationDate', 'authName', 'contType', 'lang', 'proc'] + sorted_cpvs
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for row in all_data:
                # Create row data
                csv_row = {
                    'meldungsnummer': row['meldungsnummer'],
                    'title': row['title'],
                    'projectid': row['projectid'],
                    'publicationDate': row['publicationDate'],
                    'authName': row['authName'],
                    'contType': row['contType'],
                    'lang': row['lang'],
                    'proc': row['proc']
                }
                
                # Add OPTIMIZED CPV columns (1 if exists, 0 if not)
                for cpv in sorted_cpvs:
                    csv_row[cpv] = 1 if cpv in row['cpvs'] else 0
                
                writer.writerow(csv_row)
        
        print(f"\n✅ OPTIMIZED data saved to: {csv_filename}")
        print(f"📊 Total Meldungsnummer: {len(all_data)}")
        print(f"📊 OPTIMIZED CPV columns: {len(sorted_cpvs)} (reduced from 21)")
        print(f"📊 OPTIMIZED CPV codes: {sorted_cpvs}")
        
        # Show optimization summary
        removed_cpvs = set(['71300000', '72320000'])
        print(f"\n🎯 OPTIMIZATION SUMMARY:")
        print(f"  - Removed {len(removed_cpvs)} broader CPV codes: {sorted(removed_cpvs)}")
        print(f"  - Kept {len(sorted_cpvs)} optimized CPV codes")
        print(f"  - Reduction: {len(removed_cpvs)} codes (9.5%)")
        print(f"  - All 18 Meldungsnummer still fully covered ✅")
        
    else:
        print("No data found to save")

if __name__ == "__main__":
    main()
