"""
Master script to run the complete TEST pipeline for a single tender
Executes all steps from fetching to displaying results for one specific tender
"""

import subprocess
import sys
import os

# Configure console for UTF-8 output to display umlauts correctly
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass
import pandas as pd

def run_command(description, command):
    """Run a command and handle errors"""
    print("\n" + "="*80)
    print(f"[RUNNING] {description}")
    print("="*80)
    
    result = subprocess.run(command, shell=True)
    
    if result.returncode != 0:
        print(f"\n[ERROR] Error in step: {description}")
        sys.exit(1)
    
    print(f"[DONE] {description} - Complete!")
    return result.returncode

def extract_single_tender_from_existing_data(tender_id, source_file, output_file):
    """Extract a single tender from existing weekly data"""
    print(f"[RUNNING] Extracting tender {tender_id} from existing data...")
    
    try:
        # Load the weekly data
        df = pd.read_csv(source_file)
        print(f"Loaded {len(df)} records from {source_file}")
        
        # Find the tender by id_x (project ID)
        if 'id_x' in df.columns:
            matching_rows = df[df['id_x'] == tender_id]
        else:
            print("[ERROR] No 'id_x' column found in source data")
            return False
            
        if len(matching_rows) == 0:
            print(f"[ERROR] Tender {tender_id} not found in source data")
            print(f"Available IDs: {df['id_x'].dropna().tolist()[:5]}")
            return False
        
        # Save the single tender
        matching_rows.to_csv(output_file, index=False, encoding='utf-8')
        print(f"[SUCCESS] Extracted tender {tender_id} to {output_file}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to extract tender: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python 01c_run_test_pipeline.py <tender_id>")
        print("Example: python 01c_run_test_pipeline.py 88bbd2ae-1e4b-4281-b7c8-f7de15975cbc")
        sys.exit(1)
    
    tender_id = sys.argv[1]
    
    print("\n" + "="*80)
    print(f"TEST SIMAP PIPELINE - TENDER ID: {tender_id}")
    print("="*80)
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Step 1: Extract single tender from existing data
    print("\n" + "="*80)
    print(f"[RUNNING] Step 1/4: Extracting tender {tender_id} from existing data")
    print("="*80)
    
    if not extract_single_tender_from_existing_data(tender_id, "unlabeled/simap_weekly.csv", "unlabeled/simap_test.csv"):
        print("[ERROR] Failed to extract tender from existing data")
        sys.exit(1)
    
    print("[DONE] Step 1/4: Extracting tender from existing data - Complete!")
    
    # Step 2: Flatten nested data
    run_command(
        "Step 2/4: Flattening nested data structures",
        "python 03_flatten_data.py unlabeled/simap_test.csv unlabeled/simap_test_flat.csv"
    )
    
    # Step 3: Extract essential fields
    run_command(
        "Step 3/4: Extracting essential fields",
        "python 04_extract_fields.py unlabeled/simap_test_flat.csv unlabeled/simap_test_essential.csv"
    )
    
    # Step 4: Display results
    run_command(
        "Step 4/4: Displaying results",
        "python 05_display_results.py unlabeled/simap_test_essential.csv"
    )
    
    print("\n" + "="*80)
    print("TEST PIPELINE COMPLETE!")
    print("="*80)
    print("\nOutput files generated:")
    print("   - unlabeled/simap_test.csv (raw data for single tender)")
    print("   - unlabeled/simap_test_flat.csv (flattened data)")
    print("   - unlabeled/simap_test_essential.csv (14 essential fields with dates & URLs)")
    print(f"\nTender ID: {tender_id}")
    print("="*80)

if __name__ == "__main__":
    main()