"""
Step 1: Prepare Data
Load raw tenders, selected IDs, clean text, create binary labels.
"""

import os
import sys
import pandas as pd
from pathlib import Path

# Add utils to path
sys.path.append(str(Path(__file__).parent.parent / "utils"))
from text_clean import clean_text

def main():
    base = Path(__file__).parent.parent
    raw_dir = base / "data" / "raw"
    processed_dir = base / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Load tenders
    tenders_path = raw_dir / "tenders.csv"
    if not tenders_path.exists():
        raise FileNotFoundError(f"Missing {tenders_path}")
    
    df = pd.read_csv(tenders_path)
    required_cols = ["id", "title", "full_text"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    print(f"Loaded {len(df)} tenders")
    
    # Load selected IDs
    selected_path = raw_dir / "selected_ids.csv"
    if selected_path.exists():
        selected_ids = pd.read_csv(selected_path, header=None)[0].tolist()
        df["label"] = df["id"].isin(selected_ids).astype(int)
        print(f"Labeled {df['label'].sum()} as selected (positive)")
    else:
        print("Warning: selected_ids.csv not found; labels not created")
        df["label"] = 0
    
    # Clean text
    df["title_clean"] = df["title"].apply(clean_text)
    df["full_text_clean"] = df["full_text"].apply(clean_text)
    
    # Save
    out_path = processed_dir / "tenders_labeled.parquet"
    df.to_parquet(out_path, index=False)
    print(f"Saved: {out_path}")
    
    # Summary
    print("\nDataset summary:")
    print(f"  Total: {len(df)}")
    print(f"  Positive: {df['label'].sum()} ({df['label'].mean():.1%})")
    print(f"  Negative: {(df['label']==0).sum()}")

if __name__ == "__main__":
    main()

