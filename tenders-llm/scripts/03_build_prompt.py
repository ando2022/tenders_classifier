"""
Step 3: Build LLM Prompt
Inject services and keywords into prompt template.
"""

import pandas as pd
from pathlib import Path

def main():
    base = Path(__file__).parent.parent
    raw_dir = base / "data" / "raw"
    prompts_dir = base / "prompts"
    processed_dir = base / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Load services
    services_path = raw_dir / "services.md"
    if services_path.exists():
        services = services_path.read_text(encoding="utf-8")
    else:
        services = "(No services file provided)"
    
    # Load keywords
    keywords_path = raw_dir / "keywords.csv"
    if keywords_path.exists():
        kw_df = pd.read_csv(keywords_path)
        keywords_list = kw_df["keyword"].tolist()
        keywords_str = ", ".join([f'"{k}"' for k in keywords_list[:50]])  # limit to 50
    else:
        keywords_str = "(No keywords file provided)"
    
    # Load prompt template
    template_path = prompts_dir / "classify_tender.md"
    template = template_path.read_text(encoding="utf-8")
    
    # Inject services and keywords
    prompt_base = template.replace("{SERVICES}", services).replace("{KEYWORDS}", keywords_str)
    
    # Save
    out_path = processed_dir / "prompt_base.txt"
    out_path.write_text(prompt_base, encoding="utf-8")
    print(f"Saved prompt base: {out_path}")
    print(f"Services: {len(services)} chars")
    print(f"Keywords: {keywords_str[:100]}...")

if __name__ == "__main__":
    main()

