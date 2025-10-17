"""
Quick test of the LLM prediction pipeline on 10 items (5 val, 5 test).
This verifies the pipeline works before running on the full dataset.
"""
import os
import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set environment
os.environ["SKIP_ALL"] = "1"
os.environ["NO_SUMMARY"] = "1"
os.environ["REQUEST_SLEEP_SEC"] = "25"

import pandas as pd
import json
from scripts.llm_predict_04 import load_prompt, classify, summarize_text
from tqdm import tqdm
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def main():
    # Load data
    df = pd.read_parquet("data/processed/tenders_clean.parquet")
    
    # Load splits (take first 10 from each)
    val_ids = set(open("data/processed/val_ids.txt").read().splitlines()[:10])
    test_ids = set(open("data/processed/test_ids.txt").read().splitlines()[:10])
    
    # Load prompt
    base_prompt = open("prompts/classify_tender.md", "r", encoding="utf-8").read()
    
    print(f"Testing pipeline on 10 val + 10 test items...")
    print(f"Using NO_SUMMARY={os.getenv('NO_SUMMARY')}, SLEEP={os.getenv('REQUEST_SLEEP_SEC')}s\n")
    
    # Process VAL
    df_val = df[df["id"].astype(str).isin(val_ids)].copy()
    process_split("VAL", df_val, base_prompt, "data/processed/preds_val_test.jsonl")
    
    # Process TEST  
    df_test = df[df["id"].astype(str).isin(test_ids)].copy()
    process_split("TEST", df_test, base_prompt, "data/processed/preds_test_test.jsonl")
    
    print("\n✓ Pipeline test complete!")
    print("\nResults:")
    print("  data/processed/preds_val_test.jsonl")
    print("  data/processed/preds_test_test.jsonl")
    print("\nSample predictions:")
    show_sample("data/processed/preds_val_test.jsonl", 3)

def process_split(name, df, base_prompt, out_path):
    print(f"\n{name}: {len(df)} items")
    with open(out_path, "w", encoding="utf-8") as outf:
        for _, row in tqdm(df.iterrows(), total=len(df), desc=name):
            rid = str(row["id"])
            title = (row.get("title_clean") or row.get("title") or "").strip()
            text = (row.get("text_clean") or row.get("full_text") or "").strip()
            
            # Summarize if needed
            if os.getenv("NO_SUMMARY") == "1":
                summary = text[:1200]
            else:
                summary = text if len(text) <= 1200 else text[:5000]
            
            # Classify
            try:
                pred = classify(title, summary, base_prompt)
                record = {
                    "id": rid,
                    "title": title[:100],
                    "lang": row.get("lang", ""),
                    "label": int(row.get("label", 0)),
                    "prediction": pred.get("prediction"),
                    "confidence_score": pred.get("confidence_score", 0),
                    "reasoning": pred.get("reasoning"),
                }
            except Exception as e:
                print(f"  Error on {rid}: {e}")
                record = {
                    "id": rid,
                    "title": title[:100],
                    "lang": row.get("lang", ""),
                    "label": int(row.get("label", 0)),
                    "prediction": "No",
                    "confidence_score": 0,
                    "reasoning": f"Error: {e}",
                }
            
            outf.write(json.dumps(record, ensure_ascii=False) + "\n")
            outf.flush()
            
            # Sleep to respect rate limits
            import time
            time.sleep(int(os.getenv("REQUEST_SLEEP_SEC", "25")))

def show_sample(path, n=3):
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= n:
                break
            rec = json.loads(line)
            print(f"\n  #{i+1} ID={rec['id']} label={rec['label']} pred={rec['prediction']} conf={rec['confidence_score']}")
            print(f"      title: {rec['title'][:80]}...")
            print(f"      reasoning: {rec['reasoning'][:100]}...")

if __name__ == "__main__":
    main()


