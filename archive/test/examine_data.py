#!/usr/bin/env python3
"""
Quick script to examine the data structure of the Excel files
"""

import pandas as pd
import os

def examine_data():
    """Examine the structure of the Excel files."""
    
    # File paths
    tenders_file = "../data/raw/tenders.xlsx"
    prompt_data_file = "../data/raw/Prompt_data.xlsx"
    
    print("=== EXAMINING TENDERS.XLSX ===")
    if os.path.exists(tenders_file):
        tenders_df = pd.read_excel(tenders_file)
        print(f"Shape: {tenders_df.shape}")
        print(f"Columns: {list(tenders_df.columns)}")
        print("\nFirst few rows:")
        print(tenders_df.head())
        print("\nData types:")
        print(tenders_df.dtypes)
    else:
        print(f"File not found: {tenders_file}")
    
    print("\n" + "="*50)
    print("=== EXAMINING PROMPT_DATA.XLSX ===")
    if os.path.exists(prompt_data_file):
        # Check available sheets
        xl_file = pd.ExcelFile(prompt_data_file)
        print(f"Available sheets: {xl_file.sheet_names}")
        
        for sheet_name in xl_file.sheet_names:
            print(f"\n--- SHEET: {sheet_name} ---")
            df = pd.read_excel(prompt_data_file, sheet_name=sheet_name)
            print(f"Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            print("First few rows:")
            print(df.head())
    else:
        print(f"File not found: {prompt_data_file}")

if __name__ == "__main__":
    examine_data()
