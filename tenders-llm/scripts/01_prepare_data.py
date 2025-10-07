"""
Step 1: Prepare Data
Load raw tenders, selected IDs, clean text, detect language, create binary labels.
"""

import os
import sys
import pandas as pd
from pathlib import Path
from langdetect import detect, DetectorFactory
from tqdm import tqdm

# Add utils to path
sys.path.append(str(Path(__file__).parent.parent))
from utils.text_clean import normalize_text

DetectorFactory.seed = 42

def detect_lang(text: str) -> str:
    """Detect language from text (first 1000 chars)."""
    try:
        return detect(text[:1000])
    except Exception:
        return "unknown"

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
    
    # Clean text
    tqdm.pandas(desc="Cleaning title")
    df["title_clean"] = df["title"].astype(str).progress_apply(normalize_text)
    
    tqdm.pandas(desc="Cleaning full_text")
    df["text_clean"] = df["full_text"].astype(str).progress_apply(normalize_text)
    
    # Language detection (on title + snippet of text)
    tqdm.pandas(desc="Detecting language")
    df["lang"] = (
        df["title_clean"].fillna("") + " " + df["text_clean"].fillna("").str[:1000]
    ).progress_apply(detect_lang)
    
    # Load selected IDs and create labels
    selected_path = raw_dir / "selected_ids.csv"
    if selected_path.exists():
        selected_ids = set(pd.read_csv(selected_path, header=None)[0].astype(str).tolist())
        df["label"] = df["id"].astype(str).isin(selected_ids).astype(int)
        print(f"Labeled {df['label'].sum()} as selected (positive)")
    else:
        print("Warning: selected_ids.csv not found; labels not created")
        df["label"] = 0
    
    # Parse dates if present
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    
    # Save
    out_path = processed_dir / "tenders_clean.parquet"
    df.to_parquet(out_path, index=False)
    print(f"\nSaved: {out_path}")
    
    # Summary
    print("\nDataset summary:")
    print(f"  Total: {len(df)}")
    print(f"  Positive: {df['label'].sum()} ({df['label'].mean():.1%})")
    print(f"  Negative: {(df['label']==0).sum()}")
    print(f"  Languages: {df['lang'].value_counts().to_dict()}")

if __name__ == "__main__":
    main()

