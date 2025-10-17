#!/usr/bin/env python3
"""
Step 2: Classify consolidated tenders using optimized approach
- Title-only for classification (92% accuracy)
- Full text for summary
- Emergency classifier as fallback
"""
import pandas as pd
import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))

from mvp.optimized_classifier import OptimizedTenderClassifier

# Import emergency classifier
try:
    from tender_system.classifier.similarity_classifier import SimilarityClassifier
except:
    # Fallback if tender-system not in path
    sys.path.insert(0, str(Path(__file__).parent.parent / 'tender-system'))
    from classifier.similarity_classifier import SimilarityClassifier

def classify_all_tenders(input_file=None, output_file=None):
    """
    Classify all tenders from consolidated file
    
    Args:
        input_file: Path to consolidated CSV (auto-detect if None)
        output_file: Path for output CSV (auto-generate if None)
    """
    print("🤖 Tender Classification Pipeline")
    print("=" * 60)
    
    # Find input file if not specified
    if input_file is None:
        data_dir = Path(__file__).parent / 'data'
        csv_files = list(data_dir.glob('consolidated_tenders_*.csv'))
        if not csv_files:
            print("❌ No consolidated tender files found!")
            return None
        input_file = sorted(csv_files)[-1]
    
    print(f"📂 Input: {input_file}")
    
    # Load consolidated data
    df = pd.read_csv(input_file)
    print(f"📊 Loaded {len(df)} tenders")
    
    # Initialize classifiers
    print("\n🔧 Initializing classifiers...")
    
    # Primary: LLM with title-only (92% accuracy)
    llm_classifier = OptimizedTenderClassifier()
    
    # Fallback: Emergency classifier (cosine similarity)
    emergency_classifier = SimilarityClassifier()
    emergency_classifier.load_model()
    
    print(f"   ✅ LLM Classifier: {'Ready' if llm_classifier.has_api else 'No API key'}")
    print(f"   ✅ Emergency Classifier: Ready ({len(emergency_classifier.positive_cases)} positive cases)")
    
    # Classify each tender
    print(f"\n🔍 Classifying {len(df)} tenders...")
    results = []
    
    for idx, row in df.iterrows():
        tender_id = row['tender_id']
        title = row['title_original']
        description = row.get('description_original', '')
        
        # Primary: LLM classification (title-only)
        if llm_classifier.has_api:
            llm_result = llm_classifier.classify_and_enrich(title, description)
            
            classification = {
                'llm_prediction': llm_result['prediction'],
                'llm_confidence': llm_result['confidence_score'],
                'llm_reasoning': llm_result['reasoning'],
                'title_en': llm_result.get('title_en', ''),
                'summary': llm_result.get('summary', ''),
                'classification_method': 'llm_title_only'
            }
        else:
            # No LLM, use emergency
            classification = {
                'llm_prediction': None,
                'llm_confidence': None,
                'llm_reasoning': 'No API key',
                'title_en': title,
                'summary': '',
                'classification_method': 'no_llm'
            }
        
        # Emergency classifier (always run for comparison)
        emergency_result = emergency_classifier.classify_tender(title, description)
        
        classification.update({
            'emergency_prediction': emergency_result['is_relevant'],
            'emergency_confidence': emergency_result['confidence_score'],
            'emergency_similarity': emergency_result.get('max_similarity', 0),
            'emergency_best_match': emergency_result.get('best_match_title', 'N/A')
        })
        
        # Final prediction (use LLM if available, otherwise emergency)
        if llm_classifier.has_api:
            classification['final_prediction'] = classification['llm_prediction']
            classification['final_confidence'] = classification['llm_confidence']
        else:
            classification['final_prediction'] = classification['emergency_prediction']
            classification['final_confidence'] = classification['emergency_confidence']
        
        results.append(classification)
        
        # Progress
        if (idx + 1) % 5 == 0 or idx == len(df) - 1:
            print(f"   Processed {idx + 1}/{len(df)} tenders...")
    
    # Add results to dataframe
    results_df = pd.DataFrame(results)
    df_classified = pd.concat([df, results_df], axis=1)
    
    # Generate output filename
    if output_file is None:
        output_dir = Path(__file__).parent / 'data'
        output_file = output_dir / f'classified_tenders_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    # Save classified tenders
    df_classified.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n✅ Saved classified tenders to: {output_file}")
    
    # Statistics
    print("\n📊 Classification Statistics:")
    print("=" * 60)
    
    if llm_classifier.has_api:
        llm_relevant = df_classified[df_classified['llm_prediction'] == 'Yes']
        print(f"LLM Classifier (Title-Only, 92% accuracy):")
        print(f"  ✅ Relevant: {len(llm_relevant)} ({len(llm_relevant)/len(df)*100:.1f}%)")
        print(f"  ❌ Not Relevant: {len(df) - len(llm_relevant)} ({(len(df)-len(llm_relevant))/len(df)*100:.1f}%)")
        print(f"  📊 Avg Confidence: {df_classified['llm_confidence'].mean():.1f}%")
    
    emergency_relevant = df_classified[df_classified['emergency_prediction'] == True]
    print(f"\nEmergency Classifier (Cosine Similarity):")
    print(f"  ✅ Relevant: {len(emergency_relevant)} ({len(emergency_relevant)/len(df)*100:.1f}%)")
    print(f"  ❌ Not Relevant: {len(df) - len(emergency_relevant)} ({(len(df)-len(emergency_relevant))/len(df)*100:.1f}%)")
    print(f"  📊 Avg Confidence: {df_classified['emergency_confidence'].mean():.1f}%")
    print(f"  📊 Avg Similarity: {df_classified['emergency_similarity'].mean():.3f}")
    
    # Show relevant tenders
    relevant_df = df_classified[df_classified['final_prediction'].isin(['Yes', True])]
    
    if len(relevant_df) > 0:
        print(f"\n🎯 Relevant Tenders Found: {len(relevant_df)}")
        print("=" * 60)
        
        for idx, tender in relevant_df.head(5).iterrows():
            print(f"\n{idx + 1}. {tender['title_original'][:80]}...")
            if llm_classifier.has_api:
                print(f"   Title (EN): {tender.get('title_en', 'N/A')[:80]}...")
                print(f"   LLM: {tender['llm_prediction']} ({tender['llm_confidence']:.1f}%)")
            print(f"   Emergency: {'Yes' if tender['emergency_prediction'] else 'No'} ({tender['emergency_confidence']:.1f}%, sim: {tender['emergency_similarity']:.3f})")
            print(f"   Source: {tender['source']}")
            print(f"   Deadline: {tender.get('deadline', 'N/A')}")
        
        if len(relevant_df) > 5:
            print(f"\n   ... and {len(relevant_df) - 5} more")
    
    return df_classified, output_file


if __name__ == "__main__":
    # Run classification
    df_classified, output_file = classify_all_tenders()
    
    if df_classified is not None:
        print(f"\n🎉 Classification complete!")
        print(f"📁 Results saved to: {output_file}")
        print(f"\nNext steps:")
        print(f"  1. Review classified tenders in {output_file}")
        print(f"  2. Launch UI: streamlit run mvp/ui_app.py")
        print(f"  3. Export selected tenders for client")

