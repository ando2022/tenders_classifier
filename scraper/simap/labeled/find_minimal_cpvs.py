import pandas as pd
import csv
from datetime import datetime

def analyze_cpv_coverage():
    """
    Analyze the CSV to find the minimal set of CPVs needed to cover all tenders
    """
    print("=== ANALYZING CPV COVERAGE ===")
    
    # Read the CSV
    df = pd.read_csv('meldungsnummer_data_20251015_145738.csv')
    
    print(f"Total tenders: {len(df)}")
    print(f"Total CPV columns: {len([col for col in df.columns if col.startswith(('71', '72', '73', '79', '98'))])}")
    
    # Get CPV columns (exclude basic info columns)
    cpv_columns = [col for col in df.columns if col.startswith(('71', '72', '73', '79', '98'))]
    print(f"CPV columns: {cpv_columns}")
    
    # Analyze which CPVs each tender has
    tender_cpvs = {}
    for idx, row in df.iterrows():
        meldungsnummer = row['meldungsnummer']
        tender_cpvs[meldungsnummer] = [cpv for cpv in cpv_columns if row[cpv] == 1]
        print(f"Meldungsnummer {meldungsnummer}: {tender_cpvs[meldungsnummer]}")
    
    return tender_cpvs, cpv_columns

def find_minimal_cpv_set(tender_cpvs, cpv_columns):
    """
    Find the minimal set of CPVs that covers all tenders
    """
    print(f"\n=== FINDING MINIMAL CPV SET ===")
    
    # Create a coverage matrix
    coverage_matrix = {}
    for cpv in cpv_columns:
        coverage_matrix[cpv] = []
        for meldungsnummer, cpvs in tender_cpvs.items():
            if cpv in cpvs:
                coverage_matrix[cpv].append(meldungsnummer)
    
    print(f"Coverage analysis:")
    for cpv, covered_tenders in coverage_matrix.items():
        print(f"  {cpv}: covers {len(covered_tenders)} tenders {covered_tenders}")
    
    # Find minimal set using greedy algorithm
    all_tenders = set(tender_cpvs.keys())
    covered_tenders = set()
    minimal_cpvs = []
    
    print(f"\nGreedy algorithm to find minimal set:")
    
    while covered_tenders != all_tenders:
        # Find CPV that covers the most uncovered tenders
        best_cpv = None
        best_coverage = 0
        best_new_tenders = set()
        
        for cpv, covered_by_cpv in coverage_matrix.items():
            if cpv not in minimal_cpvs:  # Don't repeat CPVs
                new_tenders = set(covered_by_cpv) - covered_tenders
                if len(new_tenders) > best_coverage:
                    best_coverage = len(new_tenders)
                    best_cpv = cpv
                    best_new_tenders = new_tenders
        
        if best_cpv:
            minimal_cpvs.append(best_cpv)
            covered_tenders.update(best_new_tenders)
            print(f"  Added {best_cpv}: covers {len(best_new_tenders)} new tenders {sorted(best_new_tenders)}")
            print(f"  Total covered: {len(covered_tenders)}/{len(all_tenders)}")
        else:
            print("  No more CPVs can cover additional tenders")
            break
    
    print(f"\n🎯 MINIMAL CPV SET FOUND:")
    print(f"  Minimal CPVs: {minimal_cpvs}")
    print(f"  Count: {len(minimal_cpvs)}")
    print(f"  All {len(all_tenders)} tenders covered: {covered_tenders == all_tenders}")
    
    return minimal_cpvs, covered_tenders

def verify_minimal_set(tender_cpvs, minimal_cpvs):
    """
    Verify that the minimal set actually covers all tenders
    """
    print(f"\n=== VERIFICATION ===")
    
    all_tenders = set(tender_cpvs.keys())
    covered_by_minimal = set()
    
    for cpv in minimal_cpvs:
        for meldungsnummer, cpvs in tender_cpvs.items():
            if cpv in cpvs:
                covered_by_minimal.add(meldungsnummer)
    
    print(f"Tenders covered by minimal set: {len(covered_by_minimal)}/{len(all_tenders)}")
    
    if covered_by_minimal == all_tenders:
        print("✅ All tenders covered by minimal CPV set!")
        
        # Show which CPV covers which tender
        print(f"\nCoverage mapping:")
        for meldungsnummer in sorted(all_tenders):
            covering_cpvs = [cpv for cpv in minimal_cpvs if cpv in tender_cpvs[meldungsnummer]]
            print(f"  Meldungsnummer {meldungsnummer}: covered by {covering_cpvs}")
        
        return True
    else:
        missing = all_tenders - covered_by_minimal
        print(f"❌ Missing tenders: {missing}")
        return False

def save_minimal_results(tender_cpvs, minimal_cpvs, cpv_columns):
    """
    Save the minimal CPV analysis results
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f"minimal_cpv_analysis_{timestamp}.csv"
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['meldungsnummer', 'all_cpvs', 'minimal_cpvs_covering', 'coverage_status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        
        for meldungsnummer, cpvs in tender_cpvs.items():
            minimal_covering = [cpv for cpv in minimal_cpvs if cpv in cpvs]
            status = "covered" if minimal_covering else "not_covered"
            
            writer.writerow({
                'meldungsnummer': meldungsnummer,
                'all_cpvs': ', '.join(cpvs),
                'minimal_cpvs_covering': ', '.join(minimal_covering),
                'coverage_status': status
            })
    
    # Also save the minimal CPV summary
    summary_filename = f"minimal_cpv_summary_{timestamp}.csv"
    
    with open(summary_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['cpv_code', 'status', 'tenders_covered']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        
        # Count how many tenders each CPV covers
        for cpv in cpv_columns:
            covered_count = sum(1 for cpvs in tender_cpvs.values() if cpv in cpvs)
            status = "minimal" if cpv in minimal_cpvs else "redundant"
            
            writer.writerow({
                'cpv_code': cpv,
                'status': status,
                'tenders_covered': covered_count
            })
    
    print(f"\n✅ Results saved to:")
    print(f"  - {csv_filename}")
    print(f"  - {summary_filename}")

def main():
    """
    Main function to find minimal CPV set
    """
    print("Finding minimal CPV set to cover all tenders...")
    
    # Analyze CPV coverage
    tender_cpvs, cpv_columns = analyze_cpv_coverage()
    
    # Find minimal set
    minimal_cpvs, covered_tenders = find_minimal_cpv_set(tender_cpvs, cpv_columns)
    
    # Verify
    is_valid = verify_minimal_set(tender_cpvs, minimal_cpvs)
    
    if is_valid:
        print(f"\n🎯 OPTIMIZATION SUCCESSFUL!")
        print(f"Original CPV codes: {len(cpv_columns)}")
        print(f"Minimal CPV codes: {len(minimal_cpvs)}")
        print(f"Reduction: {len(cpv_columns) - len(minimal_cpvs)} codes ({((len(cpv_columns) - len(minimal_cpvs))/len(cpv_columns)*100):.1f}%)")
        print(f"Minimal CPV codes: {minimal_cpvs}")
        
        # Save results
        save_minimal_results(tender_cpvs, minimal_cpvs, cpv_columns)
    else:
        print(f"\n❌ Optimization failed - not all tenders covered")

if __name__ == "__main__":
    main()
