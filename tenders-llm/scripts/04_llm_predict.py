"""
Step 4: LLM Prediction
Batch classify val/test/all tenders with summarization for long texts.
"""

import os
import json
from typing import Dict, Any, Optional

import pandas as pd
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
SUMMARY_MODEL = os.getenv("OPENAI_SUMMARY_MODEL", MODEL)
TEMP = float(os.getenv("TEMPERATURE", "0.1"))

MAX_TITLE_CHARS = 300
MAX_TEXT_FOR_CLASS = 1200   # characters for classification context
MAX_TEXT_FOR_SUMMARY = 5000 # summarization cutoff

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def read_ids(path: str) -> set:
    """Read IDs from text file (one per line)."""
    return set(open(path, "r", encoding="utf-8").read().splitlines())

def load_prompt(path: Path) -> str:
    """Load prompt template."""
    return path.read_text(encoding="utf-8")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def summarize_text(text: str) -> str:
    """Summarize long text for classification."""
    if not text or len(text) <= MAX_TEXT_FOR_CLASS:
        return text
    text = text[:MAX_TEXT_FOR_SUMMARY]
    system = "You are a precise analyst. Summarize the tender text for classification in <= 200 words. Preserve key scope."
    user = f"Text:\n{text}"
    r = client.chat.completions.create(
        model=SUMMARY_MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.0,
    )
    return r.choices[0].message.content.strip()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def classify(title: str, summary_or_text: str, base_prompt: str) -> Dict[str, Any]:
    """Classify tender using LLM."""
    user_block = f"""
NEW TENDER
Title: {title[:MAX_TITLE_CHARS]}

Short context (optional): {summary_or_text[:MAX_TEXT_FOR_CLASS]}
"""
    messages = [
        {"role": "system", "content": "Follow the provided instructions and return strict JSON only."},
        {"role": "user", "content": base_prompt + "\n\n" + user_block}
    ]
    r = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=TEMP,
        response_format={"type": "json_object"},
    )
    try:
        return json.loads(r.choices[0].message.content)
    except Exception:
        # fallback: try to extract json
        content = r.choices[0].message.content
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(content[start:end+1])
        raise

def run_split(split_name: str, ids: Optional[set], df: pd.DataFrame, base_prompt: str, out_path: Path):
    """Run predictions on a data split."""
    if ids is not None:
        df = df[df["id"].astype(str).isin(ids)].copy()
    
    print(f"Running {split_name}: {len(df)} rows")
    with open(out_path, "w", encoding="utf-8") as outf:
        for _, row in tqdm(df.iterrows(), total=len(df), desc=split_name):
            title = (row.get("title_clean") or row.get("title") or "").strip()
            text = (row.get("text_clean") or row.get("full_text") or "").strip()
            
            # Summarize if long
            summary = summarize_text(text)
            
            # Classify
            try:
                pred = classify(title, summary, base_prompt)
                record = {
                    "id": str(row["id"]),
                    "lang": row.get("lang", ""),
                    "label": int(row.get("label", 0)),
                    "prediction": pred.get("prediction"),
                    "confidence_score": pred.get("confidence_score"),
                    "reasoning": pred.get("reasoning"),
                }
            except Exception as e:
                print(f"Error on {row['id']}: {e}")
                record = {
                    "id": str(row["id"]),
                    "lang": row.get("lang", ""),
                    "label": int(row.get("label", 0)),
                    "prediction": "No",
                    "confidence_score": 0,
                    "reasoning": f"Error: {e}",
                }
            
            outf.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    print(f"Wrote {out_path}")

def main():
    base = Path(__file__).parent.parent
    processed_dir = base / "data" / "processed"
    prompts_dir = base / "prompts"
    
    # Load data
    df = pd.read_parquet(processed_dir / "tenders_clean.parquet")
    base_prompt = load_prompt(prompts_dir / "classify_tender.md")
    
    # Load split IDs
    val_ids_path = processed_dir / "val_ids.txt"
    test_ids_path = processed_dir / "test_ids.txt"
    
    ids_val = read_ids(val_ids_path) if val_ids_path.exists() else None
    ids_test = read_ids(test_ids_path) if test_ids_path.exists() else None
    
    # Run predictions
    if ids_val:
        run_split("VAL", ids_val, df, base_prompt, processed_dir / "preds_val.jsonl")
    if ids_test:
        run_split("TEST", ids_test, df, base_prompt, processed_dir / "preds_test.jsonl")
    
    # Optionally run on all data
    run_split("ALL", None, df, base_prompt, processed_dir / "preds_all.jsonl")

if __name__ == "__main__":
    main()

