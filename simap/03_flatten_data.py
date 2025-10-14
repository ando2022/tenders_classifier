"""
ROBUST, SIMPLE approach - recursively flatten ALL nested data automatically
No field definitions needed - handles everything generically
"""

import pandas as pd
import ast
import re
from bs4 import BeautifulSoup

def parse_dict_string(s):
    """Safely parse string representation of dictionary"""
    if pd.isna(s) or str(s).strip() in ['', 'None']:
        return None
    try:
        return ast.literal_eval(str(s))
    except:
        return None

def clean_html(text):
    """Clean HTML from text"""
    if pd.isna(text) or text is None:
        return None
    soup = BeautifulSoup(str(text), 'html.parser')
    return soup.get_text(separator=' ', strip=True)

def is_language_dict(d):
    """Check if dict is a language dict (has de, en, fr, it keys)"""
    if not isinstance(d, dict):
        return False
    keys = set(d.keys())
    lang_keys = {'de', 'en', 'fr', 'it'}
    return len(keys.intersection(lang_keys)) >= 2 and len(keys) <= 6

def flatten_recursive(obj, prefix='', max_depth=5, current_depth=0):
    """
    Recursively flatten ANY nested structure
    Handles: dicts, lists, language dicts, simple values
    """
    if current_depth > max_depth:
        return {}
    
    result = {}
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_key = f"{prefix}_{key}" if prefix else key
            
            if is_language_dict(value):
                # Handle language dicts specially
                for lang in ['de', 'en', 'fr', 'it']:
                    result[f"{new_key}_{lang}"] = value.get(lang)
                
                # Create primary (first non-None value)
                primary = None
                for lang in ['en', 'de', 'fr', 'it']:
                    if value.get(lang) not in [None, 'None', '']:
                        primary = value.get(lang)
                        break
                result[f"{new_key}_primary"] = primary
                
            elif isinstance(value, dict):
                # Recursively flatten other dicts
                result.update(flatten_recursive(value, new_key, max_depth, current_depth + 1))
                
            elif isinstance(value, list):
                if len(value) == 0:
                    # Empty list -> None
                    result[new_key] = None
                elif all(isinstance(item, dict) for item in value):
                    # List of dicts -> flatten each with index
                    for i, item in enumerate(value):
                        result.update(flatten_recursive(item, f"{new_key}_{i}", max_depth, current_depth + 1))
                else:
                    # Simple list -> string representation
                    result[new_key] = str(value)
                
            else:
                # Simple value
                result[new_key] = value
                
    elif isinstance(obj, list):
        if len(obj) == 0:
            result[prefix] = None
        elif all(isinstance(item, dict) for item in obj):
            for i, item in enumerate(obj):
                result.update(flatten_recursive(item, f"{prefix}_{i}", max_depth, current_depth + 1))
        else:
            result[prefix] = str(obj)
    else:
        # Simple value
        result[prefix] = obj
    
    return result

def process_dataframe_robust(df):
    """Process DataFrame with robust recursive flattening"""
    print("Starting robust recursive flattening...")
    original_cols = df.shape[1]
    
    # Process each row
    all_flattened_data = []
    
    for idx, row in df.iterrows():
        print(f"Processing row {idx + 1}/{len(df)}")
        row_data = {}
        
        # Process each column
        for col in df.columns:
            if pd.notna(row[col]):
                parsed_data = parse_dict_string(row[col])
                if parsed_data is not None:
                    # Flatten this data with column name as prefix
                    flattened = flatten_recursive(parsed_data, col)
                    row_data.update(flattened)
                else:
                    # Keep simple values as-is
                    row_data[col] = row[col]
            else:
                row_data[col] = row[col]
        
        all_flattened_data.append(row_data)
    
    # Create new DataFrame
    df_new = pd.DataFrame(all_flattened_data)
    
    # Clean HTML from description-like columns
    print("Cleaning HTML from description columns...")
    desc_cols = [col for col in df_new.columns if any(keyword in col.lower() for keyword in 
                ['description', 'note', 'comment', 'text', 'content']) and '_clean' not in col]
    
    for col in desc_cols:
        if df_new[col].dtype == 'object':
            clean_col = f"{col}_clean"
            df_new[clean_col] = df_new[col].apply(clean_html)
            print(f"  Created: {clean_col}")
    
    # Remove original nested columns (keep only simple ones)
    print("Removing original nested columns...")
    original_nested_cols = ['title', 'orderDescription', 'orderAddress', 'procurement', 
                           'project-info', 'dates', 'terms', 'criteria', 'lots_x', 'lots_y',
                           'orderAddressOnlyDescription', 'base', 'publishers', 'procOfficeName']
    
    for col in original_nested_cols:
        if col in df_new.columns:
            df_new = df_new.drop(columns=[col])
            print(f"  Removed: {col}")
    
    # Remove any remaining columns that still contain nested dict strings
    print("Removing any remaining nested columns...")
    cols_to_remove = []
    for col in df_new.columns:
        if df_new[col].dtype == 'object':
            sample_val = df_new[col].iloc[0]
            if pd.notna(sample_val) and isinstance(sample_val, str) and sample_val.startswith('{'):
                try:
                    parsed = ast.literal_eval(sample_val)
                    if isinstance(parsed, dict):
                        cols_to_remove.append(col)
                except:
                    pass
    
    for col in cols_to_remove:
        df_new = df_new.drop(columns=[col])
        print(f"  Removed nested: {col}")
    
    print(f"[SUCCESS] Robust flattening complete!")
    print(f"   Original columns: {original_cols}")
    print(f"   Final columns: {df_new.shape[1]}")
    print(f"   New columns added: {df_new.shape[1] - original_cols + len(original_nested_cols)}")
    
    return df_new

if __name__ == "__main__":
    import sys
    
    # Allow command-line arguments for input/output files
    if len(sys.argv) >= 3:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
    else:
        input_file = "unlabeled/simap.csv"
        output_file = "unlabeled/simap_robust_flat.csv"
    
    print(f"Loading data from {input_file}...")
    df = pd.read_csv(input_file, encoding='utf-8')
    print(f"Original shape: {df.shape}")
    
    # Process with robust recursive flattening
    df_processed = process_dataframe_robust(df)
    
    # Save result
    print(f"Saving to {output_file}...")
    df_processed.to_csv(output_file, index=False, encoding='utf-8')
    
    print("[SUCCESS] Complete! All nested data robustly flattened.")
    
    # Show sample of key extracted fields
    print("\nSample extracted fields:")
    key_cols = [col for col in df_processed.columns if any(keyword in col.lower() for keyword in 
                ['cpv', 'title', 'description', 'address', 'city', 'country', 'canton', 'name', 'email', 'phone', 'contract', 'period'])]
    
    if key_cols:
        sample_cols = key_cols[:10]  # Show first 10 relevant columns
        print(df_processed[sample_cols].head(1))
