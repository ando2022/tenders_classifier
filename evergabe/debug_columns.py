#!/usr/bin/env python3
"""
Debug script to check what columns are available in the Evergabe data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evergabe.evergabe import make_driver, accept_cookies, wait_for_table, set_page_size_max, get_table_headers, row_dicts_all_columns

def debug_columns():
    print("🔍 Starting debug to check available columns...")
    
    driver = make_driver(headless=True)
    try:
        driver.get("https://www.evergabe-online.de/search.html?4")
        accept_cookies(driver)
        wait_for_table(driver)
        set_page_size_max(driver)
        
        # Get headers
        headers = get_table_headers(driver)
        print(f"📋 Available columns: {headers}")
        
        # Get first few rows to see what data is available
        rows = row_dicts_all_columns(driver, headers)
        if rows:
            print(f"\n📊 First row data:")
            for key, value in rows[0].items():
                print(f"  {key}: {value}")
        else:
            print("❌ No rows found")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_columns()
