"""
Step 0b: Pre-extract XML Content

Extracts relevant sections from tender full text XML and saves to new columns.
This runs ONCE after loading raw data, then results are reused.

Output: Adds columns to tenders.csv:
  - xml_description (section 2.6 only)
  - xml_simap_relevant (sections 2.6 + 3.7 + 3.8)
"""
import pandas as pd
from pathlib import Path
import sys
from tqdm import tqdm

# Add utils to path
sys.path.append(str(Path(__file__).parent.parent))
from utils.xml_extractor import smart_extract

def main():
    base = Path(__file__).parent.parent
    raw_dir = base / "data" / "raw"
    
    # Load tenders.csv (output of 00_reload_data_with_fulltext.py)
    tenders_path = raw_dir / "tenders.csv"
    if not tenders_path.exists():
        print(f"❌ {tenders_path} not found!")
        print("Run scripts/00_reload_data_with_fulltext.py first")
        return
    
    print(f"Loading {tenders_path}...")
    df = pd.read_csv(tenders_path)
    
    if 'full_text_raw' not in df.columns:
        print("❌ Missing 'full_text_raw' column!")
        print("Make sure 00_reload_data_with_fulltext.py preserves raw XML")
        return
    
    print(f"Loaded {len(df)} tenders")
    print(f"\nExtracting XML content from {len(df)} tenders...")
    print("This will take ~30 seconds...\n")
    
    # Extract description only (Section 2.6: Subject and scope)
    tqdm.pandas(desc="Extracting descriptions (2.6)")
    df['xml_description'] = df['full_text_raw'].progress_apply(
        lambda x: smart_extract(x, method='description_only', max_chars=1500)
    )
    
    # Extract SIMAP relevant sections (2.6 + 3.7 + 3.8)
    tqdm.pandas(desc="Extracting SIMAP sections (2.6+3.7+3.8)")
    df['xml_simap_relevant'] = df['full_text_raw'].progress_apply(
        lambda x: smart_extract(x, method='desc_deliverables', max_chars=2000)
    )
    
    # Statistics
    print(f"\n{'='*80}")
    print("EXTRACTION STATISTICS")
    print(f"{'='*80}")
    
    # Description only
    desc_lengths = df['xml_description'].str.len()
    print(f"\nDescription only (Section 2.6):")
    print(f"  Tenders with content: {(desc_lengths > 50).sum()} ({100*(desc_lengths > 50).sum()/len(df):.1f}%)")
    print(f"  Mean length: {desc_lengths.mean():.0f} chars")
    print(f"  Median length: {desc_lengths.median():.0f} chars")
    
    # SIMAP relevant
    simap_lengths = df['xml_simap_relevant'].str.len()
    print(f"\nSIMAP relevant (Sections 2.6+3.7+3.8):")
    print(f"  Tenders with content: {(simap_lengths > 50).sum()} ({100*(simap_lengths > 50).sum()/len(df):.1f}%)")
    print(f"  Mean length: {simap_lengths.mean():.0f} chars")
    print(f"  Median length: {simap_lengths.median():.0f} chars")
    
    # By label
    print(f"\nBy label:")
    for label in [0, 1]:
        label_name = "Selected" if label == 1 else "Not selected"
        subset = df[df['label'] == label]
        desc_mean = subset['xml_description'].str.len().mean()
        simap_mean = subset['xml_simap_relevant'].str.len().mean()
        print(f"  {label_name}:")
        print(f"    Description: {desc_mean:.0f} chars avg")
        print(f"    SIMAP sections: {simap_mean:.0f} chars avg")
    
    # Save
    print(f"\n{'='*80}")
    out_path = raw_dir / "tenders_with_xml.csv"
    df.to_csv(out_path, index=False, encoding='utf-8')
    print(f"✓ Saved to: {out_path}")
    print(f"{'='*80}\n")
    
    # Show samples
    print("Sample extraction (first tender):")
    print(f"\nTitle: {df.iloc[0]['title'][:100]}...")
    print(f"\nXML Description ({len(df.iloc[0]['xml_description'])} chars):")
    print(f"{df.iloc[0]['xml_description'][:300]}...\n")
    print(f"XML SIMAP Relevant ({len(df.iloc[0]['xml_simap_relevant'])} chars):")
    print(f"{df.iloc[0]['xml_simap_relevant'][:300]}...\n")
    
    print("✓ Extraction complete!")
    print("\nNext steps:")
    print("  1. Review: data/raw/tenders_with_xml.csv")
    print("  2. Run: python scripts/01_prepare_data.py")
    print("  3. Test: python scripts/test_xml_extraction.py (will be MUCH faster!)")

if __name__ == "__main__":
    main()

