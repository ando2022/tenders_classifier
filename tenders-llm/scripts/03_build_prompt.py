"""
Step 3: Build LLM Prompt
Inject services, keywords, and few-shot examples from training set.
"""

import os
import sys
import pandas as pd
from pathlib import Path
from textwrap import dedent

MAX_EXAMPLES = 100  # cap few-shot positive examples

def main():
    base = Path(__file__).parent.parent
    raw_dir = base / "data" / "raw"
    processed_dir = base / "data" / "processed"
    prompts_dir = base / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    
    # Load cleaned tenders
    clean_path = processed_dir / "tenders_clean.parquet"
    df = pd.read_parquet(clean_path)
    
    # Load train IDs
    train_ids_path = processed_dir / "train_ids.txt"
    train_ids = set(open(train_ids_path, "r", encoding="utf-8").read().splitlines())
    
    # Load services
    services_path = raw_dir / "services.md"
    if services_path.exists():
        services = services_path.read_text(encoding="utf-8").strip()
    else:
        services = "(No services file provided)"
    
    # Load keywords
    keywords_path = raw_dir / "keywords.csv"
    kw_text = ""
    if keywords_path.exists():
        kw_df = pd.read_csv(keywords_path)
        if not kw_df.empty:
            # Group by category for readability
            if "category" in kw_df.columns:
                for cat, group in kw_df.groupby(kw_df["category"].fillna("general")):
                    words = ", ".join(sorted(group["keyword"].astype(str).unique()))
                    kw_text += f"- {cat}: {words}\n"
            else:
                words = ", ".join(sorted(kw_df["keyword"].astype(str).unique()))
                kw_text = words
    
    if not kw_text:
        kw_text = "(none provided)"
    
    # Build few-shot examples from TRAIN positives (titles only)
    train_pos = df[df["id"].astype(str).isin(train_ids) & (df["label"] == 1)]
    examples = train_pos["title_clean"].dropna().unique().tolist()
    examples = examples[:MAX_EXAMPLES]
    
    # Build prompt template
    template = dedent(f"""
    You are an expert consultant specializing in public-sector tenders for economic research and analysis.
    Your goal is to review a new tender title (and optionally a short summary) and determine if it is a likely match
    for the client based on the services, keywords, and past selections below.

    ## Client Services
    {services}

    ## Known Keywords (non-exhaustive)
    {kw_text}

    ## Examples of Previously Selected Tender Titles (training-only; do NOT reveal them back)
    {chr(10).join('- ' + e for e in examples)}

    ## Output format (strict JSON):
    {{
      "prediction": "Yes" or "No",
      "confidence_score": <0..100>,
      "reasoning": "<brief one-sentence explanation>"
    }}

    Decision rules:
    - Judge fitness based on thematic alignment with services and the spirit of examples, not just keyword overlap.
    - Prefer high precision among the top-K results; avoid over-inclusive "Yes".
    - If the text is outside scope (e.g., construction works, pure IT dev with no research), likely "No".
    - Be language-agnostic; focus on meaning, not vocabulary.
    """).strip()
    
    # Save
    out_path = prompts_dir / "classify_tender.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(template)
    
    print(f"Wrote prompt to {out_path}")
    print(f"  Services: {len(services)} chars")
    print(f"  Keywords: {len(kw_text)} chars")
    print(f"  Examples: {len(examples)} positive titles")

if __name__ == "__main__":
    main()

