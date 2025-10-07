"""
Step 4: LLM Prediction
Batch classify test tenders using OpenAI API or local LLM.
"""

import os
import json
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from openai import OpenAI
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def classify_tender(prompt: str) -> dict:
    """Call LLM and parse JSON response."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a tender evaluation expert. Respond only with valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        max_tokens=500
    )
    
    content = response.choices[0].message.content.strip()
    # Try to extract JSON if wrapped in markdown
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    
    return json.loads(content)

def main():
    base = Path(__file__).parent.parent
    processed_dir = base / "data" / "processed"
    reports_dir = base / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Load test set
    test = pd.read_parquet(processed_dir / "test.parquet")
    
    # Load prompt base
    prompt_base = (processed_dir / "prompt_base.txt").read_text(encoding="utf-8")
    
    # Predict
    results = []
    for _, row in tqdm(test.iterrows(), total=len(test), desc="Classifying"):
        prompt = prompt_base.replace("{TENDER_ID}", str(row["id"])) \
                            .replace("{TENDER_TITLE}", str(row.get("title_clean", row["title"]))) \
                            .replace("{TENDER_SOURCE}", str(row.get("source", "N/A"))) \
                            .replace("{TENDER_DATE}", str(row.get("date", "N/A"))) \
                            .replace("{TENDER_FULL_TEXT}", str(row.get("full_text_clean", row["full_text"])))
        
        try:
            pred = classify_tender(prompt)
            results.append({
                "id": row["id"],
                "label_true": row["label"],
                "label_pred": int(pred.get("relevant", False)),
                "confidence": pred.get("confidence", 0.5),
                "reasoning": pred.get("reasoning", ""),
                "matched_keywords": ",".join(pred.get("matched_keywords", [])),
                "service_alignment": pred.get("service_alignment", "")
            })
        except Exception as e:
            print(f"Error on {row['id']}: {e}")
            results.append({
                "id": row["id"],
                "label_true": row["label"],
                "label_pred": 0,
                "confidence": 0.0,
                "reasoning": f"Error: {e}",
                "matched_keywords": "",
                "service_alignment": ""
            })
    
    # Save
    out_df = pd.DataFrame(results)
    out_path = reports_dir / "predictions.csv"
    out_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\nSaved predictions: {out_path}")
    print(f"Predicted positive: {out_df['label_pred'].sum()} / {len(out_df)}")

if __name__ == "__main__":
    main()

