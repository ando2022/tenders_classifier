"""
Example usage of the SIMAP API client

This script demonstrates how to use the SimapAPI class to interact with the SIMAP.ch API.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simap import SimapAPI
from config import Config, BAKConfig


def example_basic_usage():
    """
    Example of basic SIMAP API usage
    """
    print("=== Basic SIMAP API Usage Example ===\n")
    
    # Initialize the API client
    client = SimapAPI()
    
    try:
        # Test connection
        print("1. Testing API connection...")
        health = client.health_check()
        print(f"   API Status: {health}")
        
        # Get recent tenders
        print("\n2. Retrieving recent tenders...")
        tenders = client.get_tenders(limit=5)
        print(f"   Found {len(tenders.get('data', []))} tenders")
        
        # Search for economics-related tenders
        print("\n3. Searching for economics-related tenders...")
        search_results = client.search_tenders(
            query="economics OR economic OR policy",
            limit=10
        )
        print(f"   Found {len(search_results.get('data', []))} economics-related tenders")
        
        # Get organizations
        print("\n4. Retrieving organizations...")
        organizations = client.get_organizations(limit=5)
        print(f"   Found {len(organizations.get('data', []))} organizations")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False


def example_advanced_search():
    """
    Example of advanced search with filters
    """
    print("\n=== Advanced Search Example ===\n")
    
    client = SimapAPI()
    
    try:
        # Search with date filters
        date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        date_to = datetime.now().strftime('%Y-%m-%d')
        
        print(f"Searching for tenders from {date_from} to {date_to}...")
        
        filtered_tenders = client.get_tenders(
            limit=20,
            date_from=date_from,
            date_to=date_to,
            search_term="research OR study OR analysis"
        )
        
        print(f"Found {len(filtered_tenders.get('data', []))} filtered tenders")
        
        # Display some results
        if filtered_tenders.get('data'):
            print("\nSample results:")
            for i, tender in enumerate(filtered_tenders['data'][:3]):
                print(f"  {i+1}. {tender.get('title', 'No title')}")
                print(f"     Organization: {tender.get('organization', {}).get('name', 'Unknown')}")
                print(f"     Date: {tender.get('publication_date', 'Unknown')}")
                print()
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False


def example_opportunity_identification():
    """
    Example of identifying BAK Economics opportunities
    """
    print("\n=== BAK Economics Opportunity Identification ===\n")
    
    client = SimapAPI()
    
    try:
        # Search for tenders matching BAK Economics keywords
        print("Searching for tenders matching BAK Economics criteria...")
        
        # Combine keywords for search
        keywords = " OR ".join(BAKConfig.KEYWORDS[:10])  # Use first 10 keywords
        search_results = client.search_tenders(
            query=keywords,
            limit=20
        )
        
        opportunities = search_results.get('data', [])
        print(f"Found {len(opportunities)} potential opportunities")
        
        # Analyze opportunities
        print("\nAnalyzing opportunities for BAK Economics fit...")
        
        scored_opportunities = []
        for tender in opportunities:
            score = calculate_opportunity_score(tender)
            if score > 0.5:  # Only consider high-scoring opportunities
                scored_opportunities.append((tender, score))
        
        # Sort by score
        scored_opportunities.sort(key=lambda x: x[1], reverse=True)
        
        print(f"\nFound {len(scored_opportunities)} high-potential opportunities:")
        for i, (tender, score) in enumerate(scored_opportunities[:5]):
            print(f"\n{i+1}. Score: {score:.2f}")
            print(f"   Title: {tender.get('title', 'No title')}")
            print(f"   Organization: {tender.get('organization', {}).get('name', 'Unknown')}")
            print(f"   Description: {tender.get('description', 'No description')[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False


def calculate_opportunity_score(tender: dict) -> float:
    """
    Calculate opportunity score for BAK Economics
    
    Args:
        tender: Tender data from SIMAP API
        
    Returns:
        float: Score between 0 and 1
    """
    score = 0.0
    
    # Check for keyword matches
    title = tender.get('title', '').lower()
    description = tender.get('description', '').lower()
    content = f"{title} {description}"
    
    keyword_matches = sum(1 for keyword in BAKConfig.KEYWORDS if keyword in content)
    keyword_score = min(keyword_matches / len(BAKConfig.KEYWORDS), 1.0)
    
    # Check organization type
    org_name = tender.get('organization', {}).get('name', '').lower()
    org_score = 0.0
    if any(term in org_name for term in ['federal', 'cantonal', 'municipal', 'government']):
        org_score = 1.0
    elif any(term in org_name for term in ['public', 'state', 'canton']):
        org_score = 0.7
    
    # Combine scores
    score = (
        keyword_score * BAKConfig.SCORING_WEIGHTS['keyword_match'] +
        org_score * BAKConfig.SCORING_WEIGHTS['company_fit']
    )
    
    return score


def main():
    """
    Main function to run all examples
    """
    print("SIMAP API Client Examples")
    print("=" * 50)
    
    # Check configuration
    if not Config.validate_config():
        print("Warning: Some configuration settings are missing")
        print("Make sure to set SIMAP_API_KEY environment variable if required")
    
    # Run examples
    examples = [
        example_basic_usage,
        example_advanced_search,
        example_opportunity_identification
    ]
    
    for example in examples:
        try:
            success = example()
            if not success:
                print(f"Example {example.__name__} failed")
        except Exception as e:
            print(f"Example {example.__name__} failed with error: {e}")
    
    print("\n" + "=" * 50)
    print("Examples completed!")


if __name__ == "__main__":
    main()
