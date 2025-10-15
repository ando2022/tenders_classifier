"""
Filter SIMAP data to keep only essential fields specified by user
"""

import pandas as pd
import re

def filter_to_essential(input_file, output_file):
    """
    Filter to only the essential fields requested:
    - ID / Publication Number
    - Title
    - Organization
    - Eligibility criteria
    - CPV code and label
    - Additional CPV codes
    - Submission deadline (offerDeadline)
    - Publication date
    - Public offer opening date
    - Language of procedure
    - Description (procurement order description)
    - URL (SIMAP project detail link)
    """
    print(f"Loading data from {input_file}...")
    df = pd.read_csv(input_file, encoding='utf-8')
    print(f"Original shape: {df.shape}")
    
    # Define the exact columns we need (in order) - using standard naming conventions
    essential_columns = {}
    id_x_col = None
    
    # Find matching columns from the flattened data
    for col in df.columns:
        # Publication Number / ID
        if col == 'base_publicationNumber':
            essential_columns['tender_id'] = col
        
        # Title (primary)
        if col == 'base_title_primary':
            essential_columns['title'] = col
        
        # Organization (procurement office)
        if col == 'project-info_procOfficeAddress_name_primary':
            essential_columns['organization'] = col
        
        # Eligibility criteria (French) - clean version preferred
        if col == 'criteria_qualificationCriteriaNote_fr':
            essential_columns['eligibility_criteria'] = col
        
        # CPV Code
        if col == 'base_cpvCode_code':
            essential_columns['cpv_code'] = col
        
        # CPV Label (German)
        if col == 'base_cpvCode_label_de':
            essential_columns['cpv_label'] = col
        
        # Additional CPV Codes
        if col == 'procurement_additionalCpvCodes':
            essential_columns['additional_cpv_codes'] = col
        
        # Submission Deadline (offerDeadline)
        if col == 'dates_offerDeadline':
            essential_columns['offer_deadline'] = col
        
        # Publication Date
        if col == 'base_publicationDate':
            essential_columns['publication_date'] = col
        
        # Public Offer Opening Date
        if col == 'dates_publicOfferOpening':
            essential_columns['public_offer_opening_date'] = col
        
        # Language of Procedure
        if col == 'project-info_offerLanguages':
            essential_columns['languages'] = col
        
        # Description (procurement order description)
        if col == 'procurement_orderDescription_primary':
            essential_columns['description'] = col
        
        # ID for URL construction
        if col == 'id_x':
            id_x_col = col
    
    print(f"\n[SUCCESS] Found {len(essential_columns)} essential fields:")
    for display_name, col_name in essential_columns.items():
        print(f"   {display_name}: {col_name}")
    
    # Create filtered dataframe
    df_filtered = pd.DataFrame()
    for display_name, col_name in essential_columns.items():
        if col_name in df.columns:
            df_filtered[display_name] = df[col_name]
    
    # Add URL field constructed from id_x
    if id_x_col and id_x_col in df.columns:
        df_filtered['url'] = df[id_x_col].apply(
            lambda x: f"https://www.simap.ch/en/project-detail/{x}" if pd.notna(x) else None
        )
        print(f"   url: constructed from {id_x_col}")
    
    # Save filtered data (UTF-8 encoding is already correct from API)
    print(f"\nSaving filtered data to {output_file}...")
    df_filtered.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"\n[SUCCESS] Filtering complete!")
    print(f"   Original columns: {df.shape[1]}")
    print(f"   Essential columns: {df_filtered.shape[1]}")
    print(f"   Rows: {df_filtered.shape[0]}")
    
    # Show sample
    print(f"\nSample data:")
    try:
        print(df_filtered.head(3).to_string())
    except UnicodeEncodeError:
        print("   (Data preview skipped due to special characters)")
        print(f"   {len(df_filtered)} rows x {len(df_filtered.columns)} columns")
    
    return df_filtered

if __name__ == "__main__":
    import sys
    
    # Allow command-line arguments
    if len(sys.argv) >= 3:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
    else:
        # Default to weekly data
        input_file = "unlabeled/simap_weekly_flat.csv"
        output_file = "unlabeled/simap_essential_clean.csv"
    
    df_filtered = filter_to_essential(input_file, output_file)
