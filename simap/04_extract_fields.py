"""
Filter SIMAP data to keep only essential fields specified by user
"""

import pandas as pd

def filter_to_essential(input_file, output_file):
    """
    Filter to only the essential fields requested:
    - ID / Publication Number
    - Title
    - Eligibility criteria
    - CPV code and label
    - Additional CPV codes
    - Submission deadline
    - Publication date
    - Procurement office
    - Requesting unit
    - Language of procedure
    """
    print(f"Loading data from {input_file}...")
    df = pd.read_csv(input_file)
    print(f"Original shape: {df.shape}")
    
    # Define the exact columns we need (in order)
    essential_columns = {}
    
    # Find matching columns from the flattened data
    for col in df.columns:
        # Publication Number / ID
        if col == 'base_publicationNumber':
            essential_columns['ID'] = col
        
        # Title (primary)
        if col == 'base_title_primary':
            essential_columns['Title'] = col
        
        # Eligibility criteria (French) - clean version preferred
        if col == 'criteria_qualificationCriteriaNote_fr':
            essential_columns['Eligibility Criteria (FR)'] = col
        
        # CPV Code
        if col == 'base_cpvCode_code':
            essential_columns['CPV Code'] = col
        
        # CPV Label (German)
        if col == 'base_cpvCode_label_de':
            essential_columns['CPV Label (DE)'] = col
        
        # Additional CPV Codes
        if col == 'procurement_additionalCpvCodes':
            essential_columns['Additional CPV Codes'] = col
        
        # Submission Deadline
        if col == 'dates_offerDeadline':
            essential_columns['Tender Submission Deadline'] = col
        
        # Publication Date
        if col == 'base_publicationDate':
            essential_columns['Publication Date'] = col
        
        # Procurement Office Name (French)
        if col == 'procOfficeName_fr':
            essential_columns['Procurement Office (FR)'] = col
        
        # Requesting Unit / Procurement Recipient (French)
        if col == 'project-info_procurementRecipientAddress_name_fr':
            essential_columns['Requesting Unit (FR)'] = col
        
        # Language of Procedure
        if col == 'project-info_offerLanguages':
            essential_columns['Language of Procedure'] = col
    
    print(f"\n[SUCCESS] Found {len(essential_columns)} essential fields:")
    for display_name, col_name in essential_columns.items():
        print(f"   {display_name}: {col_name}")
    
    # Create filtered dataframe
    df_filtered = pd.DataFrame()
    for display_name, col_name in essential_columns.items():
        if col_name in df.columns:
            df_filtered[display_name] = df[col_name]
    
    # Save filtered data
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

