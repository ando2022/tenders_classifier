"""
Master script to run the complete DAILY SIMAP pipeline
Executes all steps from fetching to displaying results
"""

import subprocess
import sys
import os

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

def main():
    print("\n" + "="*80)
    print("DAILY SIMAP PIPELINE - STARTING")
    print("="*80)
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Step 1: Fetch today's data
    run_command(
        "Step 1/4: Fetching today's SIMAP data",
        "python 02a_fetch_today.py"
    )
    
    # Step 2: Flatten nested data
    run_command(
        "Step 2/4: Flattening nested data structures",
        "python 03_flatten_data.py unlabeled/simap.csv unlabeled/simap_flat.csv"
    )
    
    # Step 3: Extract essential fields
    run_command(
        "Step 3/4: Extracting essential fields",
        "python 04_extract_fields.py unlabeled/simap_flat.csv unlabeled/simap_essential.csv"
    )
    
    # Step 4: Display results
    run_command(
        "Step 4/4: Displaying results",
        "python 05_display_results.py"
    )
    
    print("\n" + "="*80)
    print("DAILY PIPELINE COMPLETE!")
    print("="*80)
    print("\nOutput files:")
    print("   - unlabeled/simap.csv (raw data)")
    print("   - unlabeled/simap_flat.csv (flattened data)")
    print("   - unlabeled/simap_essential.csv (11 essential fields)")
    print("\n")

if __name__ == "__main__":
    main()

