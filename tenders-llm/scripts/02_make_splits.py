"""
Step 2: Make Train/Val/Test Splits
Either time-based (if dates available) or stratified random splits.
"""

import os
import sys
import pandas as pd
from pathlib import Path
from sklearn.model_selection import StratifiedShuffleSplit

def save_ids(ids, path):
    """Save list of IDs to a text file (one per line)."""
    with open(path, "w", encoding="utf-8") as f:
        for i in ids:
            f.write(str(i) + "\n")
    print(f"-> {path} ({len(ids)})")

def main():
    base = Path(__file__).parent.parent
    processed_dir = base / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    in_path = processed_dir / "tenders_clean.parquet"
    df = pd.read_parquet(in_path)
    df = df.copy()
    df["label"] = df["label"].astype(int)
    
    # Time-based split if dates available
    if "date" in df.columns and df["date"].notna().any():
        print("Using time-based split (75% train, 10% val, 15% test)")
        df = df.sort_values("date", na_position="first")
        n = len(df)
        train_end = int(n * 0.75)
        val_end = int(n * 0.85)
        train_ids = df.iloc[:train_end]["id"].tolist()
        val_ids = df.iloc[train_end:val_end]["id"].tolist()
        test_ids = df.iloc[val_end:]["id"].tolist()
    else:
        print("Using stratified random split (75% train, 10% val, 15% test)")
        # First split: 80% temp / 20% test
        splitter = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
        y = df["label"].values
        for tr_idx, te_idx in splitter.split(df, y):
            tr_df = df.iloc[tr_idx]
            te_df = df.iloc[te_idx]
        
        # Second split: 80% temp -> 93.75% train / 6.25% val (relative to temp)
        # which gives 75% train, 5% val of original
        splitter2 = StratifiedShuffleSplit(n_splits=1, test_size=0.125, random_state=42)
        y2 = tr_df["label"].values
        for tr2_idx, va_idx in splitter2.split(tr_df, y2):
            tr2_df = tr_df.iloc[tr2_idx]
            va_df = tr_df.iloc[va_idx]
        
        train_ids = tr2_df["id"].tolist()
        val_ids = va_df["id"].tolist()
        test_ids = te_df["id"].tolist()
    
    # Save ID lists
    save_ids(train_ids, processed_dir / "train_ids.txt")
    save_ids(val_ids, processed_dir / "val_ids.txt")
    save_ids(test_ids, processed_dir / "test_ids.txt")
    
    print(f"\nSplit summary:")
    print(f"  Train: {len(train_ids)}")
    print(f"  Val:   {len(val_ids)}")
    print(f"  Test:  {len(test_ids)}")

if __name__ == "__main__":
    main()

