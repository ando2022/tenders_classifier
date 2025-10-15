"""
Master script to run both SIMAP and EU Tender daily scrapers
Calls both pipelines and provides summary of results
"""

import os
import sys
import subprocess
import time
from datetime import datetime

# Set UTF-8 encoding for subprocess calls
os.environ['PYTHONIOENCODING'] = 'utf-8'

def run_simap_scraper():
    """Run the SIMAP scraper and return results"""
    print("=" * 60)
    print("🔄 RUNNING SIMAP SCRAPER")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Run the SIMAP scraper
        simap_script = os.path.join(os.getcwd(), "simap", "simap_scraper_damlina.py")
        result = subprocess.run([
            sys.executable, simap_script
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print("✅ SIMAP scraper completed successfully")
            print(f"⏱️  Duration: {duration:.2f} seconds")
            print("\n📋 SIMAP Output:")
            print(result.stdout)
            
            # Extract key information from output
            if result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if "Saved" in line and "rows to" in line:
                        print(f"📊 {line}")
                        break
            
            return True, result.stdout
        else:
            print("❌ SIMAP scraper failed")
            print(f"Error: {result.stderr}")
            return False, result.stderr
            
    except Exception as e:
        print(f"❌ Error running SIMAP scraper: {e}")
        return False, str(e)

def run_eu_tender_scraper():
    """Run the EU Tender scraper and return results"""
    print("\n" + "=" * 60)
    print("🔄 RUNNING EU TENDER SCRAPER")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Run the EU Tender scraper
        eu_tender_script = os.path.join(os.getcwd(), "eu-tender", "02_fetch_daily.py")
        result = subprocess.run([
            sys.executable, eu_tender_script
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print("✅ EU Tender scraper completed successfully")
            print(f"⏱️  Duration: {duration:.2f} seconds")
            print("\n📋 EU Tender Output:")
            print(result.stdout)
            
            # Extract key information from output
            if result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if "Tenders with target languages" in line:
                        print(f"📊 {line}")
                    elif "Data saved to:" in line:
                        print(f"💾 {line}")
            
            return True, result.stdout
        else:
            print("❌ EU Tender scraper failed")
            print(f"Error: {result.stderr}")
            return False, result.stderr
            
    except Exception as e:
        print(f"❌ Error running EU Tender scraper: {e}")
        return False, str(e)

def check_output_files():
    """Check what output files were created"""
    print("\n" + "=" * 60)
    print("📁 CHECKING OUTPUT FILES")
    print("=" * 60)
    
    # Check SIMAP files
    simap_dir = "simap"
    if os.path.exists(simap_dir):
        simap_files = [f for f in os.listdir(simap_dir) if f.endswith('.csv')]
        if simap_files:
            print(f"📊 SIMAP files found: {len(simap_files)}")
            for file in sorted(simap_files)[-3:]:  # Show last 3 files
                file_path = os.path.join(simap_dir, file)
                size = os.path.getsize(file_path)
                print(f"   📄 {file} ({size:,} bytes)")
        else:
            print("⚠️  No SIMAP CSV files found")
    
    # Check EU Tender files
    eu_tender_dir = "eu-tender"
    if os.path.exists(eu_tender_dir):
        eu_tender_files = [f for f in os.listdir(eu_tender_dir) if f.endswith('.csv')]
        if eu_tender_files:
            print(f"📊 EU Tender files found: {len(eu_tender_files)}")
            for file in sorted(eu_tender_files)[-3:]:  # Show last 3 files
                file_path = os.path.join(eu_tender_dir, file)
                size = os.path.getsize(file_path)
                print(f"   📄 {file} ({size:,} bytes)")
        else:
            print("⚠️  No EU Tender CSV files found")

def main():
    """Main function to run both scrapers"""
    print("🚀 STARTING DAILY SCRAPER PIPELINE")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 Working directory: {os.getcwd()}")
    
    # Change to scraper directory
    if not os.path.exists("scraper"):
        print("❌ Error: scraper directory not found")
        return
    
    os.chdir("scraper")
    print(f"📂 Changed to: {os.getcwd()}")
    
    # Run both scrapers
    simap_success, simap_output = run_simap_scraper()
    eu_tender_success, eu_tender_output = run_eu_tender_scraper()
    
    # Check output files
    check_output_files()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 PIPELINE SUMMARY")
    print("=" * 60)
    
    print(f"🔄 SIMAP Scraper: {'✅ SUCCESS' if simap_success else '❌ FAILED'}")
    print(f"🔄 EU Tender Scraper: {'✅ SUCCESS' if eu_tender_success else '❌ FAILED'}")
    
    if simap_success and eu_tender_success:
        print("\n🎉 ALL SCRAPERS COMPLETED SUCCESSFULLY!")
        print("📁 Check the respective directories for output files:")
        print("   📂 scraper/simap/ - SIMAP data")
        print("   📂 scraper/eu-tender/ - EU Tender data")
    else:
        print("\n⚠️  SOME SCRAPERS FAILED - Check the output above for details")
    
    print(f"\n⏱️  Pipeline completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
