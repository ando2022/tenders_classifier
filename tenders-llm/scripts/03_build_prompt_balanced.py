"""
Build an improved prompt with better decision rules.
"""
import pandas as pd
from pathlib import Path

MAX_EXAMPLES = 100

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
    examples = train_pos["title_clean"].dropna().unique().tolist()
    examples = examples[:MAX_EXAMPLES]
    
    # NEW: Improved prompt with better decision rules
    template = f"""You are an expert consultant specializing in public-sector tenders for economic research and analysis.
Your goal is to review a new tender title (and optionally a short summary) and determine if it is a likely match
for the client based on the services, keywords, and past selections below.

## Client Services
{services}

## Known Keywords (non-exhaustive)
{kw_text}

## Examples of Previously Selected Tender Titles
{chr(10).join('- ' + e for e in examples)}

## Output format (strict JSON):
{{
  "prediction": "Yes" or "No",
  "confidence_score": <0..100>,
  "reasoning": "<brief one-sentence explanation>"
}}

## Decision rules:
1. **Broad economic research scope**: The client works on:
   - Economic analysis, forecasts, and modeling
   - Surveys, data collection, and statistical analysis
   - Impact studies (economic, social, employment)
   - Cost-benefit analysis and feasibility studies
   - Regional/sectoral economic development
   - Policy evaluation and recommendations
   
2. **What to SELECT (predict "Yes")**:
   - Tenders about economic/statistical **analysis, studies, research, evaluation**
   - Topics like: labor markets, income, costs, investments, productivity, growth, sectors, regions
   - Surveys or data collection for economic purposes
   - Even if the domain is specialized (e.g., CO2, healthcare, transport), if it requires **economic analysis**, select it

3. **What to REJECT (predict "No")**:
   - Pure IT development/software without research component
   - Construction, infrastructure works without economic analysis
   - Legal services, translations, logistics
   - Training, education delivery (not evaluation)
   - Goods procurement without analysis component

4. **Be inclusive for borderline cases**: If a tender could involve economic research or analysis, lean toward "Yes" with moderate confidence (60-75).

5. **Language-agnostic**: Focus on meaning, not keywords. Tenders in German, French, English, Italian are all valid."""

    # Save prompt
    out_path = prompts_dir / "classify_tender_balanced.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(template)
    
    print(f"✓ Wrote improved prompt to {out_path}")
    print(f"  Services: {len(services)} chars")
    print(f"  Keywords: {len(kw_text)} chars")
    print(f"  Examples: {len(examples)} positive titles")
    print(f"  Total prompt length: {len(template)} chars")

if __name__ == "__main__":
    main()

