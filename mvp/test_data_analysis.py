#!/usr/bin/env python3
"""
Test Data Classification Analysis
Process the new test data and run classification to validate accuracy.
"""
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

# Add project paths
sys.path.insert(0, str(Path.cwd()))

# Import our optimized classifier
from mvp.optimized_classifier import OptimizedTenderClassifier

def create_test_data():
    """Create test data from the provided tender titles"""
    
    test_titles = [
        # Economic Studies & Surveys (EXPECTED: YES)
        "BKS-2050 Erhebung bei den Hochschulabsolventinnen und -absolventen 2027, 2029, 2031 (EHA)",
        "BKS-2049 Erhebung zur höheren Berufsbildung (eHBB) 2027, 2029 und 2031",
        "BKS-2099 Relevé de prix régional pour l'indice des prix à la consommation",
        "BKS-2106_Ausschreibung_Durchführung der Haushaltsbudgeterhebung (HABE) 2027-2031)",
        "BKS-2165 WTO - Schweizerische Gesundheitsbefragung 2027 - SGB27",
        "Enquête de profils TT Mobilis 2026",
        "Étude impact économique de Genève Aéroport sur la région",
        "704 SECO",
        "Kantonales",
        
        # IT Services (EXPECTED: NO)
        "Bug Bounty",
        "NUCLEO -",
        "CoC Mobile",
        "IT-",
        "Atlassian",
        "KI Chatbot-",
        "Rahmenvert",
        "Contrats-",
        "Outil",
        "Programm",
        "Programme",
        "Multi-",
        "Tennant-",
        "Plattform",
        "Chatbot",
        
        # General Procurement (EXPECTED: NO)
        "Attribution",
        "Beschaffung",
        "Obtention",
        "Modernisati",
        "Modernisier",
        "Einführung",
        "Introduction",
        "Remplacem",
        "Ablösung",
        "Zentrale",
        "AUSWAHL",
        "SELECTION",
        "SÉLECTION",
        "Appel",
        "Ausschreibu",
        "RFI-",
        "RFI-mise",
        "Public",
        
        # Language Services (EXPECTED: NO)
        "Englisch",
        "Produits et",
        
        # Incomplete/Partial (EXPECTED: NO)
        "(23147) 341",
        "(24106) 806",
    ]
    
    # Create DataFrame
    test_data = []
    for i, title in enumerate(test_titles):
        test_data.append({
            'tender_id': f'TEST-{i+1:03d}',
            'source': 'test-data',
            'source_url': '',
            'title_original': title,
            'description_original': '',
            'original_language': 'mixed',
            'publication_date': datetime.now(),
            'deadline': None,
            'fetched_at': datetime.now(),
            'contracting_authority': 'Test Authority',
            'buyer_country': 'CHE',
            'cpv_codes': [],
            'cpv_labels': [],
            'procedure_type': 'test',
            'contract_nature': 'test',
            'expected_result': 'YES' if any(keyword in title.lower() for keyword in [
                'erhebung', 'étude', 'impact économique', 'budgeterhebung', 
                'seco', 'kantonales', 'enquête', 'gesundheitsbefragung'
            ]) else 'NO'
        })
    
    return pd.DataFrame(test_data)

def run_classification_test():
    """Run classification on test data"""
    
    print("🧪 TEST DATA CLASSIFICATION ANALYSIS")
    print("=" * 80)
    
    # Create test data
    df = create_test_data()
    print(f"📊 Test Data Created: {len(df)} tenders")
    
    # Initialize classifier
    classifier = OptimizedTenderClassifier()
    print(f"🔧 Classifier: {'Ready' if classifier.has_api else 'No API key'}")
    
    # Run classifications
    results = []
    correct_predictions = 0
    total_predictions = 0
    
    print(f"\n🔍 CLASSIFICATION RESULTS:")
    print("=" * 80)
    
    for idx, row in df.iterrows():
        title = row['title_original']
        expected = row['expected_result']
        
        # Classify
        result = classifier.classify_and_enrich(title, "")
        
        prediction = result['prediction']
        confidence = result['confidence_score']
        reasoning = result['reasoning']
        
        # Check if correct
        is_correct = (prediction == expected)
        if is_correct:
            correct_predictions += 1
        total_predictions += 1
        
        # Store result
        results.append({
            'tender_id': row['tender_id'],
            'title': title,
            'expected': expected,
            'prediction': prediction,
            'confidence': confidence,
            'reasoning': reasoning,
            'correct': is_correct,
            'title_en': result.get('title_en', ''),
            'summary': result.get('summary', '')
        })
        
        # Display result
        status = "✅" if is_correct else "❌"
        print(f"\n{status} {row['tender_id']}: {title[:60]}...")
        print(f"   Expected: {expected} | Predicted: {prediction} ({confidence}%)")
        print(f"   Reasoning: {reasoning[:80]}...")
    
    # Calculate accuracy
    accuracy = (correct_predictions / total_predictions) * 100 if total_predictions > 0 else 0
    
    print(f"\n📊 OVERALL RESULTS:")
    print("=" * 80)
    print(f"Total Test Cases: {total_predictions}")
    print(f"Correct Predictions: {correct_predictions}")
    print(f"Accuracy: {accuracy:.1f}%")
    
    # Break down by expected result
    df_results = pd.DataFrame(results)
    
    print(f"\n📈 BREAKDOWN BY EXPECTED RESULT:")
    print("-" * 40)
    
    for expected in ['YES', 'NO']:
        subset = df_results[df_results['expected'] == expected]
        if len(subset) > 0:
            correct = len(subset[subset['correct'] == True])
            total = len(subset)
            accuracy_subset = (correct / total) * 100
            
            print(f"\nExpected {expected}:")
            print(f"  Total: {total}")
            print(f"  Correct: {correct}")
            print(f"  Accuracy: {accuracy_subset:.1f}%")
            
            # Show incorrect predictions
            incorrect = subset[subset['correct'] == False]
            if len(incorrect) > 0:
                print(f"  Incorrect predictions:")
                for _, row in incorrect.iterrows():
                    print(f"    - {row['title'][:50]}... (predicted {row['prediction']})")
    
    # Save results
    output_file = f'mvp/data/test_classification_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    df_results.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n💾 Results saved to: {output_file}")
    
    return df_results, accuracy

if __name__ == "__main__":
    results_df, accuracy = run_classification_test()
    
    print(f"\n🎯 TEST SUMMARY:")
    print("=" * 80)
    print(f"Overall Accuracy: {accuracy:.1f}%")
    
    if accuracy >= 90:
        print("✅ EXCELLENT: System performing as expected (90%+ accuracy)")
    elif accuracy >= 80:
        print("⚠️  GOOD: System performing well (80%+ accuracy)")
    else:
        print("❌ NEEDS IMPROVEMENT: Accuracy below 80%")
    
    print(f"\n🔍 Key Findings:")
    economic_studies = results_df[results_df['expected'] == 'YES']
    if len(economic_studies) > 0:
        economic_accuracy = (len(economic_studies[economic_studies['correct'] == True]) / len(economic_studies)) * 100
        print(f"  - Economic Studies Accuracy: {economic_accuracy:.1f}%")
    
    print(f"  - Total Test Cases: {len(results_df)}")
    print(f"  - Expected Relevant: {len(results_df[results_df['expected'] == 'YES'])}")
    print(f"  - Expected Not Relevant: {len(results_df[results_df['expected'] == 'NO'])}")
