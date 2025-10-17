#!/usr/bin/env python3
"""
Test classification with and without API key
Shows how the 92% title-only approach works
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mvp.optimized_classifier import OptimizedTenderClassifier

def test_classifier():
    print("🧪 Testing Optimized Classifier (Title-Only, 92% Accuracy)")
    print("=" * 70)
    
    classifier = OptimizedTenderClassifier()
    
    if not classifier.has_api:
        print("\n⚠️  No OpenAI API key found!")
        print("Set OPENAI_API_KEY environment variable to test LLM classification")
        print("\nExample: export OPENAI_API_KEY='sk-...'")
        print("\nWithout API key, the system will use:")
        print("  → Emergency Classifier (cosine similarity with positive cases)")
        print("  → Or manual review of tenders")
        return
    
    # Test cases
    test_tenders = [
        {
            'title': 'Regulierungsfolgenabschätzungen (RFA)',
            'description': 'Die volkswirtschaftlichen Auswirkungen von Vorlagen des Bundes werden im Rahmen der Regulierungsfolgenabschätzung (RFA) untersucht und dargestellt.',
            'expected': 'Yes'
        },
        {
            'title': 'Economic Impact Assessment of Transport Infrastructure',
            'description': 'Conduct comprehensive economic analysis of proposed transport infrastructure projects.',
            'expected': 'Yes'
        },
        {
            'title': 'IT Infrastructure Services',
            'description': 'Provide IT support and infrastructure maintenance for government offices.',
            'expected': 'No'
        },
        {
            'title': 'Office Furniture Procurement',
            'description': 'Supply and installation of office furniture for administrative buildings.',
            'expected': 'No'
        }
    ]
    
    print(f"\n✅ API Key configured - Testing {len(test_tenders)} cases:")
    print("=" * 70)
    
    correct = 0
    for i, tender in enumerate(test_tenders, 1):
        print(f"\n{i}. Title: {tender['title']}")
        print(f"   Expected: {tender['expected']}")
        
        result = classifier.classify_title_only(tender['title'])
        
        print(f"   Prediction: {result['prediction']} (confidence: {result['confidence_score']}%)")
        print(f"   Reasoning: {result['reasoning']}")
        
        if result['prediction'] == tender['expected']:
            print(f"   ✅ CORRECT!")
            correct += 1
        else:
            print(f"   ❌ WRONG - Expected {tender['expected']}")
    
    print(f"\n📊 Accuracy: {correct}/{len(test_tenders)} ({correct/len(test_tenders)*100:.0f}%)")
    
    # Test translation
    print(f"\n🌐 Testing Translation & Summary:")
    print("=" * 70)
    
    enriched = classifier.classify_and_enrich(
        title=test_tenders[0]['title'],
        description=test_tenders[0]['description']
    )
    
    print(f"Original: {test_tenders[0]['title']}")
    print(f"English:  {enriched.get('title_en', 'N/A')}")
    print(f"Summary:  {enriched.get('summary', 'N/A')}")

if __name__ == "__main__":
    test_classifier()

