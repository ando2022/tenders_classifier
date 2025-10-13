"""
Master script to run the complete WEEKLY SIMAP pipeline
Executes all steps from fetching to displaying results
"""

import subprocess
import sys
import os

def run_command(description, command):
    """Run a command and handle errors"""
    print("\n" + "="*80)
    print(f"⏳ {description}")
    print("="*80)
    
    result = subprocess.run(command, shell=True)
    
    if result.returncode != 0:
        print(f"\n❌ Error in step: {description}")
        sys.exit(1)
    
    print(f"✅ {description} - Complete!")
    return result.returncode

def main():
    print("\n" + "="*80)
    print("🚀 WEEKLY SIMAP PIPELINE - STARTING")
    print("="*80)
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Step 1: Fetch last 7 days of data
    run_command(
        "Step 1/4: Fetching SIMAP data (last 7 days)",
        "python 02b_fetch_weekly.py"
    )
    
    # Step 2: Flatten nested data
    run_command(
        "Step 2/4: Flattening nested data structures",
        "python 03_flatten_data.py unlabeled/simap_weekly.csv unlabeled/simap_weekly_flat.csv"
    )
    
    # Step 3: Extract essential fields
    run_command(
        "Step 3/4: Extracting essential fields",
        "python 04_extract_fields.py unlabeled/simap_weekly_flat.csv unlabeled/simap_weekly_essential.csv"
    )
    
    # Step 4: Display results
    run_command(
        "Step 4/4: Displaying results",
        "python 05_display_results.py"
    )
    
    print("\n" + "="*80)
    print("🎉 WEEKLY PIPELINE COMPLETE!")
    print("="*80)
    print("\n📁 Output files:")
    print("   - unlabeled/simap_weekly.csv (raw data)")
    print("   - unlabeled/simap_weekly_flat.csv (flattened data)")
    print("   - unlabeled/simap_weekly_essential.csv (11 essential fields)")
    print("\n")

if __name__ == "__main__":
    main()

