#!/usr/bin/env python3
"""
Script to add sample positive cases and test data for the emergency classifier.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database.models import get_session, Tender, init_db
from classifier.similarity_classifier import SimilarityClassifier
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_sample_positive_cases():
    """Add sample positive cases to the emergency classifier."""
    classifier = SimilarityClassifier()
    
    # Sample positive cases (these would typically come from your real data)
    positive_cases = [
        {
            'title': 'Economic Analysis of Regional Development Patterns',
            'description': 'Comprehensive economic analysis of regional development patterns and growth opportunities in target regions. The study will involve data collection, econometric modeling, and stakeholder interviews to provide insights into future economic developments.',
            'confidence': 0.95
        },
        {
            'title': 'Statistical Survey on Employment Trends and Labor Market Dynamics',
            'description': 'Large-scale statistical survey to analyze employment trends and labor market dynamics. The research project will collect primary data through surveys and analyze secondary data sources to understand employment patterns, wage trends, and labor market segmentation.',
            'confidence': 0.92
        },
        {
            'title': 'Cost-Benefit Analysis for Infrastructure Investment Projects',
            'description': 'Economic evaluation and cost-benefit analysis for major infrastructure development projects. The analysis will assess economic impacts, social benefits, and financial viability of proposed infrastructure investments using established economic modeling techniques.',
            'confidence': 0.88
        },
        {
            'title': 'Labor Market Research and Employment Statistics Analysis',
            'description': 'Research project focusing on labor market conditions and employment statistics. The study will analyze employment data, unemployment trends, job creation patterns, and labor force participation rates to inform policy recommendations.',
            'confidence': 0.90
        },
        {
            'title': 'Economic Impact Assessment of Policy Changes',
            'description': 'Study to assess economic impacts of policy changes and market interventions. The research will evaluate the economic consequences of regulatory changes, fiscal policies, and market interventions using quantitative analysis methods.',
            'confidence': 0.87
        },
        {
            'title': 'Regional Economic Development Strategy Research',
            'description': 'Development of regional economic development strategies based on comprehensive economic analysis. The project will identify growth opportunities, analyze competitive advantages, and recommend policy measures for regional economic development.',
            'confidence': 0.85
        },
        {
            'title': 'Productivity Analysis and Economic Growth Studies',
            'description': 'Analysis of productivity trends and their impact on economic growth. The research will examine productivity measures, innovation indicators, and their relationship to economic performance across different sectors and regions.',
            'confidence': 0.89
        }
    ]
    
    print("📚 Adding positive cases to emergency classifier...")
    
    for i, case in enumerate(positive_cases, 1):
        classifier.add_positive_case(
            title=case['title'],
            description=case['description'],
            confidence=case['confidence'],
            source='sample'
        )
        print(f"  {i}. Added: {case['title'][:50]}...")
    
    # Build and save the model
    classifier.build_model()
    classifier.save_model()
    
    print(f"\n✅ Added {len(positive_cases)} positive cases to emergency classifier")
    return classifier

def add_sample_tenders_to_database():
    """Add sample tenders to the database for testing."""
    session = get_session()
    
    # Sample tenders for testing
    sample_tenders = [
        {
            'tender_id': 'SIMAP-001',
            'source': 'simap',
            'title': 'Economic Analysis of Regional Development Patterns',
            'description': 'Comprehensive economic analysis of regional development patterns and growth opportunities in target regions.',
            'publication_date': datetime.now() - timedelta(days=5),
            'deadline': datetime.now() + timedelta(days=30),
            'contracting_authority': 'Federal Office for Regional Development',
            'estimated_value': 150000,
            'is_relevant': True,
            'confidence_score': 95.0,
            'reasoning': 'Direct economic analysis project - perfect match for research capabilities'
        },
        {
            'tender_id': 'SIMAP-002',
            'source': 'simap',
            'title': 'Statistical Survey on Employment Trends',
            'description': 'Large-scale statistical survey to analyze employment trends and labor market dynamics.',
            'publication_date': datetime.now() - timedelta(days=3),
            'deadline': datetime.now() + timedelta(days=25),
            'contracting_authority': 'Ministry of Labor',
            'estimated_value': 200000,
            'is_relevant': True,
            'confidence_score': 92.0,
            'reasoning': 'Statistical analysis and employment research - core expertise area'
        },
        {
            'tender_id': 'SIMAP-003',
            'source': 'simap',
            'title': 'IT Infrastructure Maintenance Contract',
            'description': 'Technical maintenance and support for existing IT infrastructure systems.',
            'publication_date': datetime.now() - timedelta(days=7),
            'deadline': datetime.now() + timedelta(days=20),
            'contracting_authority': 'IT Department',
            'estimated_value': 50000,
            'is_relevant': False,
            'confidence_score': 15.0,
            'reasoning': 'Pure IT maintenance - no economic research component'
        },
        {
            'tender_id': 'EVERGABE-001',
            'source': 'evergabe',
            'title': 'Cost-Benefit Analysis for Infrastructure Projects',
            'description': 'Economic evaluation and cost-benefit analysis for major infrastructure development projects.',
            'publication_date': datetime.now() - timedelta(days=2),
            'deadline': datetime.now() + timedelta(days=35),
            'contracting_authority': 'Infrastructure Planning Office',
            'estimated_value': 180000,
            'is_relevant': True,
            'confidence_score': 88.0,
            'reasoning': 'Economic analysis and evaluation - relevant for research capabilities'
        },
        {
            'tender_id': 'EVERGABE-002',
            'source': 'evergabe',
            'title': 'Office Furniture Procurement',
            'description': 'Procurement of office furniture and equipment for government offices.',
            'publication_date': datetime.now() - timedelta(days=1),
            'deadline': datetime.now() + timedelta(days=15),
            'contracting_authority': 'Procurement Office',
            'estimated_value': 25000,
            'is_relevant': False,
            'confidence_score': 5.0,
            'reasoning': 'Pure procurement - no research or analysis component'
        }
    ]
    
    print("📥 Adding sample tenders to database...")
    
    for tender_data in sample_tenders:
        tender = Tender(
            tender_id=tender_data['tender_id'],
            source=tender_data['source'],
            title=tender_data['title'],
            description=tender_data['description'],
            publication_date=tender_data['publication_date'],
            deadline=tender_data['deadline'],
            contracting_authority=tender_data['contracting_authority'],
            estimated_value=tender_data['estimated_value'],
            is_relevant=tender_data['is_relevant'],
            confidence_score=tender_data['confidence_score'],
            reasoning=tender_data['reasoning'],
            classified_at=datetime.now()
        )
        session.add(tender)
        print(f"  Added: {tender_data['title'][:50]}...")
    
    session.commit()
    print(f"\n✅ Added {len(sample_tenders)} sample tenders to database")

def test_emergency_classifier():
    """Test the emergency classifier with sample data."""
    print("\n🧪 Testing Emergency Classifier:")
    print("=" * 60)
    
    classifier = SimilarityClassifier()
    
    # Test cases
    test_cases = [
        {
            'title': 'Economic Impact Study of Climate Policy',
            'description': 'Comprehensive study analyzing the economic impacts of climate change policies on regional development and employment'
        },
        {
            'title': 'Statistical Analysis of Digital Economy Trends',
            'description': 'Research project examining digital transformation impacts on economic growth and labor market dynamics'
        },
        {
            'title': 'Office Cleaning Services Contract',
            'description': 'Procurement of cleaning services for government office buildings'
        },
        {
            'title': 'Regional Development Strategy Research',
            'description': 'Development of comprehensive regional development strategies based on economic analysis and stakeholder consultation'
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        result = classifier.classify_tender(case['title'], case['description'])
        
        print(f"\n{i}. Title: {case['title']}")
        print(f"   Description: {case['description']}")
        print(f"   Relevant: {'✅ YES' if result['is_relevant'] else '❌ NO'}")
        print(f"   Confidence: {result['confidence_score']:.1f}%")
        print(f"   Similarity: {result['similarity_score']:.3f}")
        print(f"   Best Match: {result['best_match']}")
        print(f"   Reasoning: {result['reasoning']}")

def main():
    """Main function to set up sample data and test emergency classifier."""
    print("🚀 Setting up sample data for testing...")
    
    # Initialize database
    init_db()
    
    # Add positive cases to emergency classifier
    classifier = add_sample_positive_cases()
    
    # Add sample tenders to database
    add_sample_tenders_to_database()
    
    # Test the emergency classifier
    test_emergency_classifier()
    
    # Show statistics
    print(f"\n📊 Emergency Classifier Statistics:")
    stats = classifier.get_stats()
    print(f"   Positive Cases: {stats['positive_cases_count']}")
    print(f"   Model Fitted: {stats['model_fitted']}")
    print(f"   Similarity Threshold: {stats['similarity_threshold']}")
    print(f"   Sources: {', '.join(stats['sources'])}")
    
    print(f"\n📊 Database Statistics:")
    session = get_session()
    total = session.query(Tender).count()
    relevant = session.query(Tender).filter(Tender.is_relevant == True).count()
    print(f"   Total Tenders: {total}")
    print(f"   Relevant Tenders: {relevant}")
    
    print(f"\n✅ Setup complete! You can now:")
    print(f"   1. Export tenders: python export_client_report.py --relevant")
    print(f"   2. Test emergency classifier: python manage_emergency_classifier.py test")
    print(f"   3. View statistics: python manage_emergency_classifier.py stats")

if __name__ == "__main__":
    main()
