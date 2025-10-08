"""
Enhanced prompt builder with optional negative examples.
Set environment variable INCLUDE_NEGATIVES=1 to add hard negative examples.
"""
import os
import pandas as pd
from pathlib import Path
from textwrap import dedent

# Config
MAX_POS_EXAMPLES = 93
MAX_NEG_EXAMPLES = 93
INCLUDE_NEGATIVES = os.getenv("INCLUDE_NEGATIVES", "0") == "1"

def main():
    base_dir = Path(".")
    processed_dir = base_dir / "data/processed"
    raw_dir = base_dir / "data/raw"
    prompts_dir = base_dir / "prompts"
    prompts_dir.mkdir(exist_ok=True)
    
    # Load clean data
    df = pd.read_parquet(processed_dir / "tenders_clean.parquet")
    
    # Load train IDs
    train_ids = set(open(processed_dir / "train_ids.txt", "r", encoding="utf-8").read().splitlines())
    
    # Load services
    services_path = raw_dir / "services.md"
    services = open(services_path, "r", encoding="utf-8").read().strip() if services_path.exists() else "(none provided)"
    
    # Load keywords
    keywords_path = raw_dir / "keywords.csv"
    kw_text = ""
    if keywords_path.exists():
        kw_df = pd.read_csv(keywords_path)
        if not kw_df.empty:
            if "category" in kw_df.columns:
                for cat, group in kw_df.groupby(kw_df["category"].fillna("general")):
                    words = ", ".join(sorted(group["keyword"].astype(str).unique()))
                    kw_text += f"- {cat}: {words}\n"
            else:
                words = ", ".join(sorted(kw_df["keyword"].astype(str).unique()))
                kw_text = words
    
    if not kw_text:
        kw_text = "(none provided)"
    
    # Build positive examples from TRAIN
    train_pos = df[df["id"].astype(str).isin(train_ids) & (df["label"] == 1)]
    pos_examples = train_pos["title_clean"].dropna().unique().tolist()
    pos_examples = pos_examples[:MAX_POS_EXAMPLES]
    
    # Build negative examples (optional)
    neg_examples = []
    if INCLUDE_NEGATIVES:
        train_neg = df[df["id"].astype(str).isin(train_ids) & (df["label"] == 0)]
        
        # Strategy: pick "hard negatives" - negatives that contain keywords or similar words
        # Simple heuristic: negatives with longest titles (often more detailed/confusing)
        train_neg = train_neg.copy()
        train_neg["title_len"] = train_neg["title_clean"].str.len()
        train_neg = train_neg.sort_values("title_len", ascending=False)
        
        neg_examples = train_neg["title_clean"].dropna().unique().tolist()
        neg_examples = neg_examples[:MAX_NEG_EXAMPLES]
    
    # Build examples section
    examples_section = f"## Examples of Previously Selected Tender Titles\n"
    examples_section += f"{chr(10).join('✓ ' + e for e in pos_examples)}\n"
    
    if INCLUDE_NEGATIVES and neg_examples:
        examples_section += f"\n## Examples of Previously REJECTED Tender Titles (outside scope)\n"
        examples_section += f"{chr(10).join('✗ ' + e for e in neg_examples)}\n"
    
    # Build prompt template
    template = dedent(f"""
    You are an expert consultant specializing in public-sector tenders for economic research and analysis.
    Your goal is to review a new tender title (and optionally a short summary) and determine if it is a likely match
    for the client based on the services, keywords, and past selections below.
    
    ## Client Services
    {services}
    
    ## Known Keywords (non-exhaustive)
    {kw_text}
    
    {examples_section}
    
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
    
    # Save prompt
    suffix = "_with_negatives" if INCLUDE_NEGATIVES else ""
    out_path = prompts_dir / f"classify_tender{suffix}.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(template)
    
    print(f"Wrote prompt to {out_path}")
    print(f"  Services: {len(services)} chars")
    print(f"  Keywords: {len(kw_text)} chars")
    print(f"  Positive examples: {len(pos_examples)}")
    if INCLUDE_NEGATIVES:
        print(f"  Negative examples: {len(neg_examples)}")
    print(f"  Total prompt length: {len(template)} chars")

if __name__ == "__main__":
    main()

