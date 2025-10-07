"""
Step 2: Make Train/Test Splits
Stratified 80/20 split by label.
"""

import os
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from dotenv import load_dotenv

load_dotenv()

def main():
    base = Path(__file__).parent.parent
    processed_dir = base / "data" / "processed"
    
    df = pd.read_parquet(processed_dir / "tenders_labeled.parquet")
    
    seed = int(os.getenv("RANDOM_SEED", 42))
    
    # Stratified split
    train, test = train_test_split(
        df, 
        test_size=0.2, 
        random_state=seed, 
        stratify=df["label"]
    )
    
    train.to_parquet(processed_dir / "train.parquet", index=False)
    test.to_parquet(processed_dir / "test.parquet", index=False)
    
    print(f"Train: {len(train)} ({train['label'].sum()} pos)")
    print(f"Test:  {len(test)} ({test['label'].sum()} pos)")
    print(f"Saved to {processed_dir}")

if __name__ == "__main__":
    main()

