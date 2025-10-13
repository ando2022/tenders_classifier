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
        print(f"{i+1}. ID: {df.iloc[i]['ID']}")
        print(f"   Title: {df.iloc[i]['Title']}")
        print(f"   CPV: {df.iloc[i]['CPV Code']} - {df.iloc[i]['CPV Label (DE)']}")
        print(f"   Additional CPVs: {df.iloc[i]['Additional CPV Codes']}")
        print(f"   Deadline: {df.iloc[i]['Tender Submission Deadline']}")
        print(f"   Publication: {df.iloc[i]['Publication Date']}")
        office = str(df.iloc[i]['Procurement Office (FR)'])
        print(f"   Office: {office[:70]}{'...' if len(office) > 70 else ''}")
        requesting = str(df.iloc[i]['Requesting Unit (FR)'])
        print(f"   Requesting Unit: {requesting[:70]}{'...' if len(requesting) > 70 else ''}")
        print(f"   Language: {df.iloc[i]['Language of Procedure']}")
        print(f"   Eligibility: {str(df.iloc[i]['Eligibility Criteria (FR)'])[:60]}...")
        print()
except UnicodeEncodeError:
    print(f"\n[INFO] {len(df)} tenders found - view data in Streamlit app or CSV file")
    print(f"       (Console display skipped due to special characters)\n")

print("="*80)
print(f"[SUCCESS] Data saved to: {input_file}")
print(f"[INFO] View in Streamlit: python -m streamlit run app.py")
print("="*80)

