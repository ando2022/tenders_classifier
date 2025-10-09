"""
Reload data from tenders_content.xlsx which now includes full text column.
This replaces the previous 00_reload_data.py script.
"""
import os
import pandas as pd
from pathlib import Path
import re

# Get base directory (tenders-llm/)
BASE_DIR = Path(__file__).parent.parent

# Paths (relative to tenders-llm/)
SOURCE_EXCEL = BASE_DIR / "data" / "raw" / "tenders_content.xlsx"
OUT_CSV = BASE_DIR / "data" / "raw" / "tenders.csv"
OUT_SELECTED = BASE_DIR / "data" / "raw" / "selected_ids.csv"

def clean_html_xml(text):
    """Remove HTML/XML tags from text."""
    if not isinstance(text, str):
        return ""
    
    # Remove XML/HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Remove DOCTYPE declarations
    text = re.sub(r'<!DOCTYPE[^>]*>', '', text)
    
    # Remove XML declarations
    text = re.sub(r'<\?xml[^>]*\?>', '', text)
    
    # Decode common HTML entities
    text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    text = text.replace('&quot;', '"').replace('&apos;', "'")
    text = text.replace('&nbsp;', ' ')
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def main():
    # Read the TITLES sheet with full text
    df = pd.read_excel(SOURCE_EXCEL, sheet_name="TITLES")
    
    print(f"Loaded {len(df)} tenders from TITLES sheet")
    print(f"Columns: {df.columns.tolist()}")
    print(f"Label distribution:\n{df['N2'].value_counts()}")
    
    # Clean full text (remove HTML/XML)
    print("\nCleaning full text column...")
    df['full_text_clean'] = df['full text'].apply(clean_html_xml)
    
    # Check how many have meaningful full text
    df['has_full_text'] = df['full_text_clean'].str.len() > 100
    print(f"Tenders with full text (>100 chars): {df['has_full_text'].sum()} ({100*df['has_full_text'].sum()/len(df):.1f}%)")
    
    # Create a clean dataframe for the pipeline
    # IMPORTANT: Keep BOTH raw XML (for extraction) and cleaned text (for fallback)
    df_clean = pd.DataFrame({
        'id': range(1, len(df) + 1),
        'title': df['title'].astype(str),
        'full_text': df['full_text_clean'].fillna(df['title'].astype(str)),  # Cleaned version
        'full_text_raw': df['full text'].astype(str),  # Raw XML for extraction
        'date': pd.to_datetime(df['deadline'], errors='coerce'),
        'label': df['N2'].astype(int),
        'has_full_text': df['has_full_text']
    })
    
    # Save tenders.csv
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(OUT_CSV, index=False, encoding='utf-8')
    print(f"\nSaved {len(df_clean)} tenders to {OUT_CSV}")
    
    # Save selected IDs
    selected_ids = df_clean[df_clean['label'] == 1]['id'].tolist()
    with open(OUT_SELECTED, 'w', encoding='utf-8') as f:
        for sid in selected_ids:
            f.write(f"{sid}\n")
    print(f"Saved {len(selected_ids)} selected IDs to {OUT_SELECTED}")
    
    # Summary
    print(f"\nSummary:")
    print(f"  Total tenders: {len(df_clean)}")
    print(f"  Selected (N2=1): {len(selected_ids)} ({100*len(selected_ids)/len(df_clean):.1f}%)")
    print(f"  With full text: {df_clean['has_full_text'].sum()} ({100*df_clean['has_full_text'].sum()/len(df_clean):.1f}%)")
    print(f"  Date range: {df_clean['date'].min()} to {df_clean['date'].max()}")
    print(f"  Missing dates: {df_clean['date'].isna().sum()}")
    
    # Text length statistics
    df_clean['text_len'] = df_clean['full_text'].str.len()
    print(f"\nText length statistics:")
    print(f"  Mean: {df_clean['text_len'].mean():.0f} chars")
    print(f"  Median: {df_clean['text_len'].median():.0f} chars")
    print(f"  Max: {df_clean['text_len'].max():.0f} chars")
    print(f"  Min: {df_clean['text_len'].min():.0f} chars")
    
    # Compare positives vs negatives
    print(f"\nText length by label:")
    for label in [0, 1]:
        subset = df_clean[df_clean['label'] == label]
        label_name = "Selected" if label == 1 else "Not selected"
        print(f"  {label_name}: mean={subset['text_len'].mean():.0f}, median={subset['text_len'].median():.0f}")

if __name__ == "__main__":
    main()
