#!/usr/bin/env python3
"""
CLI tool for managing the emergency similarity classifier.
Allows adding positive cases, testing classification, and managing the model.
"""
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from classifier.similarity_classifier import SimilarityClassifier
from database.models import get_session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_positive_case(args):
    """Add a positive case to the emergency classifier."""
    classifier = SimilarityClassifier()
    
    classifier.add_positive_case(
        title=args.title,
        description=args.description,
        confidence=args.confidence,
        source=args.source
    )
    
    classifier.build_model()
    classifier.save_model()
    
    print(f"✅ Added positive case: {args.title}")


def load_from_database(args):
    """Load positive cases from existing database."""
    classifier = SimilarityClassifier()
    session = get_session()
    
    success = classifier.add_positive_cases_from_database(
        session, 
        min_confidence=args.min_confidence
    )
    
    if success:
        print(f"✅ Loaded positive cases from database (min confidence: {args.min_confidence}%)")
        stats = classifier.get_stats()
        print(f"   Total cases: {stats['positive_cases_count']}")
    else:
        print("❌ Failed to load positive cases from database")


def test_classification(args):
    """Test classification on sample tenders."""
    classifier = SimilarityClassifier()
    
    if not classifier.positive_cases:
        print("❌ No positive cases available. Please add some first.")
        return
    
    # Load model if not already loaded
    if not classifier.vectorizer_fitted:
        classifier.build_model()
    
    test_cases = [
        {
            'title': args.title or 'Economic Analysis of Regional Development',
            'description': args.description or 'Comprehensive economic analysis of regional development patterns'
        },
        {
            'title': 'IT Infrastructure Maintenance Contract',
            'description': 'Technical maintenance and support for existing IT systems'
        },
        {
            'title': 'Statistical Research on Labor Market Trends',
            'description': 'Research project analyzing employment statistics and labor market dynamics'
        }
    ]
    
    print("🧪 Testing Emergency Classifier:")
    print("=" * 60)
    
    for i, case in enumerate(test_cases, 1):
        result = classifier.classify_tender(case['title'], case['description'])
        
        print(f"\n{i}. Title: {case['title']}")
        print(f"   Description: {case['description']}")
        print(f"   Relevant: {'✅ YES' if result['is_relevant'] else '❌ NO'}")
        print(f"   Confidence: {result['confidence_score']:.1f}%")
        print(f"   Similarity: {result['similarity_score']:.3f}")
        print(f"   Best Match: {result['best_match']}")
        print(f"   Reasoning: {result['reasoning']}")
    
    print(f"\n📊 Model Statistics:")
    stats = classifier.get_stats()
    print(f"   Positive Cases: {stats['positive_cases_count']}")
    print(f"   Model Fitted: {stats['model_fitted']}")
    print(f"   Similarity Threshold: {stats['similarity_threshold']}")
    print(f"   Sources: {', '.join(stats['sources'])}")


def show_stats(args):
    """Show statistics about the emergency classifier."""
    classifier = SimilarityClassifier()
    stats = classifier.get_stats()
    
    print("📊 Emergency Classifier Statistics:")
    print("=" * 40)
    print(f"Positive Cases: {stats['positive_cases_count']}")
    print(f"Model Fitted: {'✅ Yes' if stats['model_fitted'] else '❌ No'}")
    print(f"Similarity Threshold: {stats['similarity_threshold']}")
    print(f"Sources: {', '.join(stats['sources']) if stats['sources'] else 'None'}")
    
    if stats['latest_case']:
        print(f"Latest Case: {stats['latest_case']}")
    
    if classifier.positive_cases:
        print(f"\n📝 Recent Positive Cases:")
        for i, case in enumerate(classifier.positive_cases[-3:], 1):
            print(f"{i}. {case['title'][:50]}... (confidence: {case['confidence']:.2f})")


def list_cases(args):
    """List all positive cases."""
    classifier = SimilarityClassifier()
    
    if not classifier.positive_cases:
        print("❌ No positive cases available.")
        return
    
    print(f"📝 Positive Cases ({len(classifier.positive_cases)} total):")
    print("=" * 60)
    
    for i, case in enumerate(classifier.positive_cases, 1):
        print(f"{i}. Title: {case['title']}")
        print(f"   Description: {case['description'][:100]}{'...' if len(case['description']) > 100 else ''}")
        print(f"   Confidence: {case['confidence']:.2f}")
        print(f"   Source: {case['source']}")
        print(f"   Added: {case['added_at']}")
        print()


def run_emergency_classification(args):
    """Run classification using emergency classifier only."""
    from main import TenderOrchestrator
    
    orchestrator = TenderOrchestrator()
    
    print("🚨 Running with Emergency Classifier Only (No OpenAI)")
    print(f"   Source: {args.source}")
    print(f"   Days back: {args.days_back}")
    
    orchestrator.use_emergency_classifier_only(
        source=args.source,
        days_back=args.days_back
    )


def main():
    parser = argparse.ArgumentParser(
        description="Manage the emergency similarity classifier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add a positive case
  python manage_emergency_classifier.py add --title "Economic Analysis" --description "Analysis of economic trends"
  
  # Load positive cases from database
  python manage_emergency_classifier.py load-db --min-confidence 80
  
  # Test classification
  python manage_emergency_classifier.py test --title "Regional Development Study"
  
  # Show statistics
  python manage_emergency_classifier.py stats
  
  # Run scraper with emergency classifier only
  python manage_emergency_classifier.py run --source simap --days-back 7
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add positive case
    add_parser = subparsers.add_parser('add', help='Add a positive case')
    add_parser.add_argument('--title', required=True, help='Tender title')
    add_parser.add_argument('--description', help='Tender description')
    add_parser.add_argument('--confidence', type=float, default=1.0, help='Confidence score (0-1)')
    add_parser.add_argument('--source', default='manual', help='Source of the case')
    add_parser.set_defaults(func=add_positive_case)
    
    # Load from database
    load_parser = subparsers.add_parser('load-db', help='Load positive cases from database')
    load_parser.add_argument('--min-confidence', type=float, default=80.0, help='Minimum confidence score')
    load_parser.set_defaults(func=load_from_database)
    
    # Test classification
    test_parser = subparsers.add_parser('test', help='Test classification')
    test_parser.add_argument('--title', help='Custom title to test')
    test_parser.add_argument('--description', help='Custom description to test')
    test_parser.set_defaults(func=test_classification)
    
    # Show statistics
    stats_parser = subparsers.add_parser('stats', help='Show classifier statistics')
    stats_parser.set_defaults(func=show_stats)
    
    # List cases
    list_parser = subparsers.add_parser('list', help='List all positive cases')
    list_parser.set_defaults(func=list_cases)
    
    # Run emergency classification
    run_parser = subparsers.add_parser('run', help='Run scraper with emergency classifier only')
    run_parser.add_argument('--source', default='simap', help='Source to scrape')
    run_parser.add_argument('--days-back', type=int, default=7, help='Days back to fetch')
    run_parser.set_defaults(func=run_emergency_classification)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        args.func(args)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
