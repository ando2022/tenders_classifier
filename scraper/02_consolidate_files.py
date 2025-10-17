"""
Consolidate CSV files from SIMAP and EU Tender scrapers
Combines all CSV files into a single file with source column
"""

import os
import pandas as pd
import glob
from datetime import datetime

def find_latest_csv_files():
    """Find the latest CSV files from each scraper"""
    simap_files = glob.glob("simap/simap_export_*.csv")
    eu_tender_files = glob.glob("eu-tender/eu_tenders_daily_*.csv")
    
    # Get the most recent files
    latest_simap = max(simap_files, key=os.path.getctime) if simap_files else None
    latest_eu_tender = max(eu_tender_files, key=os.path.getctime) if eu_tender_files else None
    
    return latest_simap, latest_eu_tender

def standardize_columns(df, source):
    """Standardize column names and add source column"""
    # Add source column
    df['source'] = source
    
    # Create a standardized column mapping
    column_mapping = {
        # Common fields that might exist in both datasets
        'title': 'title',
        'description': 'description', 
        'publication_date': 'publication_date',
        'deadline': 'deadline',
        'organization': 'organization',
        'buyer_name': 'buyer_name',
        'cpv_code': 'cpv_code',
        'classification_cpv': 'cpv_code',
        'url': 'url',
        'ted_url': 'url',
        'publication_id': 'publication_id',
        'publication_number': 'publication_number',
        'language_submission': 'language_submission',
        'submission_language': 'language_submission',
        'languages': 'languages',
        'procedure_type': 'procedure_type',
        'contract_nature': 'contract_nature',
        'buyer_country': 'buyer_country',
        'notice_subtype': 'notice_subtype',
        'title_proc': 'title_proc',
        'cpv_label': 'cpv_label',
        'xml_url': 'xml_url',
        'pdf_url': 'pdf_url',
        'fetched_at': 'fetched_at'
    }
    
    # Rename columns to standardized names
    df_renamed = df.rename(columns=column_mapping)
    
    return df_renamed

def consolidate_simap_data(simap_file):
    """Load and process SIMAP data"""
    print(f"📂 Loading SIMAP data from: {simap_file}")
    
    try:
        df = pd.read_csv(simap_file, encoding='utf-8')
        print(f"   📊 Loaded {len(df)} rows from SIMAP")
        
        # Standardize columns
        df_std = standardize_columns(df, 'simap')
        
        # Show available columns
        print(f"   📋 SIMAP columns: {list(df_std.columns)}")
        
        return df_std
        
    except Exception as e:
        print(f"   ❌ Error loading SIMAP file: {e}")
        return None

def consolidate_eu_tender_data(eu_tender_file):
    """Load and process EU Tender data"""
    print(f"📂 Loading EU Tender data from: {eu_tender_file}")
    
    try:
        df = pd.read_csv(eu_tender_file, encoding='utf-8')
        print(f"   📊 Loaded {len(df)} rows from EU Tender")
        
        # Standardize columns
        df_std = standardize_columns(df, 'eu-tender')
        
        # Show available columns
        print(f"   📋 EU Tender columns: {list(df_std.columns)}")
        
        return df_std
        
    except Exception as e:
        print(f"   ❌ Error loading EU Tender file: {e}")
        return None

def merge_dataframes(df_simap, df_eu_tender):
    """Merge SIMAP and EU Tender dataframes"""
    print("\n🔄 Merging datasets...")
    
    if df_simap is None and df_eu_tender is None:
        print("❌ No data to merge")
        return None
    
    if df_simap is None:
        print("📊 Only EU Tender data available")
        return df_eu_tender
    
    if df_eu_tender is None:
        print("📊 Only SIMAP data available")
        return df_simap
    
    # Find common columns
    simap_cols = set(df_simap.columns)
    eu_tender_cols = set(df_eu_tender.columns)
    common_cols = simap_cols.intersection(eu_tender_cols)
    
    print(f"📋 Common columns: {len(common_cols)}")
    print(f"   {sorted(common_cols)}")
    
    # Select common columns for both dataframes
    simap_common = df_simap[list(common_cols)]
    eu_tender_common = df_eu_tender[list(common_cols)]
    
    # Combine dataframes
    combined_df = pd.concat([simap_common, eu_tender_common], ignore_index=True)
    
    print(f"✅ Combined dataset: {len(combined_df)} rows")
    print(f"   📊 SIMAP rows: {len(simap_common)}")
    print(f"   📊 EU Tender rows: {len(eu_tender_common)}")
    
    return combined_df

def save_consolidated_data(df, output_file):
    """Save consolidated data to CSV"""
    print(f"\n💾 Saving consolidated data to: {output_file}")
    
    try:
        # Ensure directory exists (only if output_file has a directory)
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Save to CSV
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        print(f"✅ Successfully saved {len(df)} rows to {output_file}")
        
        # Show file size
        file_size = os.path.getsize(output_file)
        print(f"📁 File size: {file_size:,} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return False

def show_data_summary(df):
    """Show summary of consolidated data"""
    print("\n📊 CONSOLIDATED DATA SUMMARY")
    print("=" * 50)
    
    if df is None:
        print("❌ No data available")
        return
    
    print(f"📈 Total rows: {len(df)}")
    print(f"📋 Total columns: {len(df.columns)}")
    
    # Show source distribution
    if 'source' in df.columns:
        source_counts = df['source'].value_counts()
        print(f"\n📊 Data by source:")
        for source, count in source_counts.items():
            print(f"   {source}: {count} rows")
    
    # Show column information
    print(f"\n📋 Available columns:")
    for i, col in enumerate(df.columns, 1):
        non_null_count = df[col].notna().sum()
        print(f"   {i:2d}. {col} ({non_null_count}/{len(df)} non-null)")
    
    # Show sample data
    print(f"\n📋 Sample data (first 3 rows):")
    print(df.head(3).to_string(index=False, max_cols=10))

def main():
    """Main consolidation function"""
    print("🔄 CONSOLIDATING SCRAPER DATA")
    print("=" * 50)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 Working directory: {os.getcwd()}")
    
    # Change to scraper directory if not already there
    if not os.path.exists("simap") and not os.path.exists("eu-tender"):
        if os.path.exists("scraper"):
            os.chdir("scraper")
            print(f"📂 Changed to: {os.getcwd()}")
        else:
            print("❌ Error: scraper directory not found")
            return
    
    # Find latest CSV files
    print("\n🔍 Finding latest CSV files...")
    simap_file, eu_tender_file = find_latest_csv_files()
    
    if simap_file:
        print(f"📂 Latest SIMAP file: {simap_file}")
    else:
        print("⚠️  No SIMAP files found")
    
    if eu_tender_file:
        print(f"📂 Latest EU Tender file: {eu_tender_file}")
    else:
        print("⚠️  No EU Tender files found")
    
    if not simap_file and not eu_tender_file:
        print("❌ No CSV files found to consolidate")
        return
    
    # Load and process data
    print("\n📂 Loading data...")
    df_simap = consolidate_simap_data(simap_file) if simap_file else None
    df_eu_tender = consolidate_eu_tender_data(eu_tender_file) if eu_tender_file else None
    
    # Merge datasets
    combined_df = merge_dataframes(df_simap, df_eu_tender)
    
    if combined_df is None:
        print("❌ No data to consolidate")
        return
    
    # Show data summary
    show_data_summary(combined_df)
    
    # Save consolidated data
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"consolidated_tenders_{timestamp}.csv"
    
    success = save_consolidated_data(combined_df, output_file)
    
    if success:
        print(f"\n🎉 CONSOLIDATION COMPLETED SUCCESSFULLY!")
        print(f"📁 Output file: {output_file}")
        print(f"📊 Total records: {len(combined_df)}")
    else:
        print(f"\n❌ CONSOLIDATION FAILED")

if __name__ == "__main__":
    main()
