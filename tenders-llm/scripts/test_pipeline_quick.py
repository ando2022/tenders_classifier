"""
Quick pipeline test: Run LLM prediction on 10 items to verify everything works.
"""
import os
import json
import time
import pandas as pd
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

# Config
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TEMP = 0.1
SLEEP_SEC = int(os.getenv("REQUEST_SLEEP_SEC", "25"))

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def classify(title: str, text_snippet: str, base_prompt: str):
    user_block = f"""
NEW TENDER
Title: {title[:300]}
Short context (optional): {text_snippet[:1200]}
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
        content = r.choices[0].message.content
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(content[start:end+1])
        raise

def main():
    # Load data
    df = pd.read_parquet("data/processed/tenders_clean.parquet")
    
    # Load first 10 val IDs
    val_ids = set(open("data/processed/val_ids.txt").read().splitlines()[:10])
    df_test = df[df["id"].astype(str).isin(val_ids)].copy()
    
    # Load prompt
    base_prompt = open("prompts/classify_tender.md", "r", encoding="utf-8").read()
    
    print(f"\n=== PIPELINE TEST: {len(df_test)} items ===")
    print(f"Model: {MODEL}, Sleep: {SLEEP_SEC}s\n")
    
    results = []
    out_path = "data/processed/preds_quick_test.jsonl"
    
    with open(out_path, "w", encoding="utf-8") as outf:
        for _, row in tqdm(df_test.iterrows(), total=len(df_test), desc="Testing"):
            rid = str(row["id"])
            title = (row.get("title_clean") or row.get("title") or "").strip()
            text = (row.get("text_clean") or row.get("full_text") or "").strip()
            
            try:
                pred = classify(title, text, base_prompt)
                record = {
                    "id": rid,
                    "title": title[:100],
                    "lang": row.get("lang", ""),
                    "label": int(row.get("label", 0)),
                    "prediction": pred.get("prediction", "No"),
                    "confidence_score": pred.get("confidence_score", 0),
                    "reasoning": pred.get("reasoning", ""),
                }
            except Exception as e:
                print(f"\n  Error on {rid}: {e}")
                record = {
                    "id": rid,
                    "title": title[:100],
                    "lang": row.get("lang", ""),
                    "label": int(row.get("label", 0)),
                    "prediction": "No",
                    "confidence_score": 0,
                    "reasoning": f"Error: {str(e)[:100]}",
                }
            
            results.append(record)
            outf.write(json.dumps(record, ensure_ascii=False) + "\n")
            outf.flush()
            time.sleep(SLEEP_SEC)
    
    print(f"\n✓ Done! Results saved to: {out_path}\n")
    
    # Show sample results
    print("Sample predictions:")
    for i, rec in enumerate(results[:5]):
        print(f"\n  #{i+1} ID={rec['id']} label={rec['label']} → pred={rec['prediction']} (conf={rec['confidence_score']})")
        print(f"      {rec['title']}...")
        print(f"      reasoning: {rec['reasoning'][:80]}...")
    
    # Summary
    df_res = pd.DataFrame(results)
    print(f"\n=== SUMMARY ===")
    print(f"Total: {len(df_res)}")
    print(f"  Actual positives: {df_res['label'].sum()}")
    print(f"  Predicted Yes: {(df_res['prediction']=='Yes').sum()}")
    print(f"  Predicted No: {(df_res['prediction']=='No').sum()}")
    print(f"  Errors: {(df_res['confidence_score']==0).sum()}")

if __name__ == "__main__":
    main()

