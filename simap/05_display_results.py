"""Display essential SIMAP data in a clean format"""
import pandas as pd
import sys
import os

# Determine which file to read
if len(sys.argv) > 1:
    input_file = sys.argv[1]
else:
    # Default: try weekly first, then daily, then final
    if os.path.exists('unlabeled/simap_weekly_essential.csv'):
        input_file = 'unlabeled/simap_weekly_essential.csv'
    elif os.path.exists('unlabeled/simap_essential.csv'):
        input_file = 'unlabeled/simap_essential.csv'
    elif os.path.exists('unlabeled/simap_final_essential.csv'):
        input_file = 'unlabeled/simap_final_essential.csv'
    else:
        print("[ERROR] No essential data file found!")
        sys.exit(1)

print(f"Reading: {input_file}\n")
df = pd.read_csv(input_file)

print("="*80)
print("ESSENTIAL SIMAP DATA - 11 KEY FIELDS")
print("="*80 + "\n")
print(f"\nTotal tenders: {len(df)}\n")

try:
    for i in range(len(df)):
        print(f"{i+1}. ID: {df.iloc[i]['tender_id']}")
        print(f"   Title: {df.iloc[i]['title']}")
        print(f"   URL: {df.iloc[i]['url'] if 'url' in df.columns else 'N/A'}")
        print(f"   Organization: {str(df.iloc[i]['organization'])[:70]}{'...' if pd.notna(df.iloc[i]['organization']) and len(str(df.iloc[i]['organization'])) > 70 else ''}")
        print(f"   CPV: {df.iloc[i]['cpv_code']} - {df.iloc[i]['cpv_label']}")
        print(f"   Additional CPVs: {df.iloc[i]['additional_cpv_codes']}")
        print(f"   Deadline: {df.iloc[i]['deadline']}")
        print(f"   Publication: {df.iloc[i]['publication_date']}")
        print(f"   Languages: {df.iloc[i]['languages']}")
        eligibility = str(df.iloc[i]['eligibility_criteria'])
        print(f"   Eligibility: {eligibility[:60]}{'...' if len(eligibility) > 60 else ''}")
        print()
except UnicodeEncodeError:
    print(f"\n[INFO] {len(df)} tenders found - view data in Streamlit app or CSV file")
    print(f"       (Console display skipped due to special characters)\n")

print("="*80)
print(f"[SUCCESS] Data saved to: {input_file}")
print(f"[INFO] View in Streamlit: python -m streamlit run app.py")
print("="*80)

