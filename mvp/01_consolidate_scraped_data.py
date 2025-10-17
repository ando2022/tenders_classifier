#!/usr/bin/env python3
"""
Step 1: Consolidate scraped data from SIMAP and EU Tender into unified format.
Shows the consolidated table structure and how both sources populate it.
"""
import pandas as pd
from datetime import datetime
import os
import sys

def consolidate_simap_data(simap_file):
    """Convert SIMAP data to consolidated format"""
    df = pd.read_csv(simap_file)
    
    consolidated = []
    for _, row in df.iterrows():
        tender = {
            # IDs and source
            'tender_id': f"SIMAP-{row.get('publication_id', '')}",
            'source': 'simap',
            'source_url': row.get('url', ''),
            
            # Original content
            'title_original': row.get('title', ''),
            'description_original': row.get('Description', ''),
            'original_language': row.get('languages', 'DE'),  # Default to German for SIMAP
            
            # Dates
            'publication_date': pd.to_datetime(row.get('publication_date')) if pd.notna(row.get('publication_date')) else None,
            'deadline': pd.to_datetime(row.get('deadline')) if pd.notna(row.get('deadline')) else None,
            'fetched_at': datetime.now(),
            
            # Metadata
            'contracting_authority': row.get('organization', ''),
            'buyer_country': 'CHE',  # Switzerland for SIMAP
            'cpv_codes': [row.get('cpv_code')] if pd.notna(row.get('cpv_code')) else [],
            'cpv_labels': [row.get('cpv_label')] if pd.notna(row.get('cpv_label')) else [],
            'procedure_type': None,
            'contract_nature': None,
        }
        consolidated.append(tender)
    
    return pd.DataFrame(consolidated)


def parse_date_safe(date_str):
    """Safely parse date handling various formats"""
    if pd.isna(date_str) or not date_str:
        return None
    try:
        # Handle formats like "2025-10-16+02:00" or "[2025-11-14T00:00:00+01:00]"
        date_str = str(date_str).replace('[', '').replace(']', '').replace("'", "")
        date_str = date_str.split('+')[0].split('T')[0]
        return pd.to_datetime(date_str)
    except:
        return None


def consolidate_eu_tender_data(eu_file):
    """Convert EU Tender data to consolidated format"""
    df = pd.read_csv(eu_file)
    
    consolidated = []
    for _, row in df.iterrows():
        tender = {
            # IDs and source
            'tender_id': f"EU-{row.get('publication_number', '')}",
            'source': 'eu-tender',
            'source_url': row.get('url', ''),
            
            # Original content
            'title_original': row.get('title', '') or row.get('title_proc', ''),
            'description_original': row.get('description', ''),
            'original_language': row.get('title_language', 'EN'),
            
            # Dates
            'publication_date': parse_date_safe(row.get('publication_date')),
            'deadline': parse_date_safe(row.get('deadline')),
            'fetched_at': parse_date_safe(row.get('fetched_at')) or datetime.now(),
            
            # Metadata
            'contracting_authority': row.get('buyer_name', '') or row.get('organization', ''),
            'buyer_country': row.get('buyer_country', ''),
            'cpv_codes': [row.get('cpv_code')] if pd.notna(row.get('cpv_code')) else [],
            'cpv_labels': [],
            'procedure_type': row.get('procedure_type', ''),
            'contract_nature': row.get('contract_nature', ''),
        }
        consolidated.append(tender)
    
    return pd.DataFrame(consolidated)


def consolidate_all_sources():
    """Consolidate data from all available sources"""
    print("🔄 Consolidating data from all sources...")
    print("=" * 60)
    
    all_data = []
    
    # Find latest SIMAP file
    simap_dir = 'scraper/scraper/simap'
    if os.path.exists(simap_dir):
        simap_files = [f for f in os.listdir(simap_dir) if f.endswith('.csv')]
        if simap_files:
            latest_simap = sorted(simap_files)[-1]
            simap_path = os.path.join(simap_dir, latest_simap)
            print(f"📥 SIMAP: {latest_simap}")
            df_simap = consolidate_simap_data(simap_path)
            all_data.append(df_simap)
            print(f"   Rows: {len(df_simap)}")
    
    # Find latest EU Tender file
    eu_dir = 'scraper/scraper/eu-tender'
    if os.path.exists(eu_dir):
        eu_files = [f for f in os.listdir(eu_dir) if f.endswith('.csv')]
        if eu_files:
            latest_eu = sorted(eu_files)[-1]
            eu_path = os.path.join(eu_dir, latest_eu)
            print(f"📥 EU Tender: {latest_eu}")
            df_eu = consolidate_eu_tender_data(eu_path)
            all_data.append(df_eu)
            print(f"   Rows: {len(df_eu)}")
    
    if not all_data:
        print("❌ No data found from scrapers")
        return None
    
    # Combine all sources
    df_consolidated = pd.concat(all_data, ignore_index=True)
    
    print(f"\n✅ Consolidated {len(df_consolidated)} tenders from {len(all_data)} sources")
    print(f"\n📋 Consolidated Table Structure:")
    print("=" * 60)
    print(df_consolidated.head(3).to_string())
    
    # Save to CSV
    output_dir = 'mvp/data'
    os.makedirs(output_dir, exist_ok=True)
    output_file = f'{output_dir}/consolidated_tenders_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    df_consolidated.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n✅ Saved to: {output_file}")
    
    # Show column summary
    print(f"\n📊 Column Summary:")
    print(f"   Total columns: {len(df_consolidated.columns)}")
    print(f"   Columns: {list(df_consolidated.columns)}")
    
    return df_consolidated, output_file


if __name__ == "__main__":
    df, file_path = consolidate_all_sources()
    
    if df is not None:
        print(f"\n📈 Data Summary:")
        print(f"   Total tenders: {len(df)}")
        print(f"   Sources: {df['source'].value_counts().to_dict()}")
        print(f"   Languages: {df['original_language'].value_counts().to_dict()}")
        print(f"   With deadlines: {df['deadline'].notna().sum()}")
        print(f"\n🎯 Ready for classification pipeline!")

