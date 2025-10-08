"""
Reload data from the correct Google Drive source and prepare it for the LLM pipeline.
"""
import os
import pandas as pd
from pathlib import Path

# Paths
SOURCE_EXCEL = "/Users/anastasiiadobson/Library/CloudStorage/GoogleDrive-mybestdayistoday@gmail.com/.shortcut-targets-by-id/1Z7_7yHHWe-c-2QxwpkKB7i9KO3i9dwsR/BAK-Economics/Data/data_for_modelling/tenders.xlsx"
OUT_CSV = "data/raw/tenders.csv"
OUT_SELECTED = "data/raw/selected_ids.csv"

def main():
    # Read the TITLES sheet
    df = pd.read_excel(SOURCE_EXCEL, sheet_name="TITLES")
    
    print(f"Loaded {len(df)} tenders from TITLES sheet")
    print(f"Columns: {df.columns.tolist()}")
    print(f"Label distribution:\n{df['N2'].value_counts()}")
    
    # Create a clean dataframe for the pipeline
    # We need: id, title, full_text (title for now), date, label
    df_clean = pd.DataFrame({
        'id': range(1, len(df) + 1),  # Create sequential IDs
        'title': df['title'].astype(str),
        'full_text': df['title'].astype(str),  # Use title as full_text for now
        'date': pd.to_datetime(df['deadline'], errors='coerce'),
        'label': df['N2'].astype(int)
    })
    
    # Save tenders.csv
    os.makedirs("data/raw", exist_ok=True)
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
    print(f"  Date range: {df_clean['date'].min()} to {df_clean['date'].max()}")
    print(f"  Missing dates: {df_clean['date'].isna().sum()}")

if __name__ == "__main__":
    main()

