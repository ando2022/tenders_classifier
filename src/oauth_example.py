"""
OAuth 2.0 Authentication Example for SIMAP.ch API

This script demonstrates how to authenticate with the SIMAP.ch API using OAuth 2.0 + PKCE.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simap import SimapAPI
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def oauth_authentication_example():
    """
    Example of OAuth 2.0 authentication with SIMAP.ch
    """
    print("SIMAP.ch OAuth 2.0 Authentication Example")
    print("=" * 50)
    
    # Initialize the client
    client = SimapAPI()
    
    # Check if we have a client ID
    if not client.client_id:
        print("❌ No client ID found!")
        print("\nTo get a client ID:")
        print("1. Contact SIMAP support to register your application")
        print("2. Provide your company details and intended use")
        print("3. Set the SIMAP_CLIENT_ID environment variable")
        print("\nExample:")
        print("export SIMAP_CLIENT_ID='your_client_id_here'")
        return False
    
    print(f"✅ Client ID found: {client.client_id}")
    
    # Check if already authenticated
    if client.is_authenticated():
        print("✅ Already authenticated!")
        print("Testing API access...")
        
        try:
            # Test API call
            health = client.health_check()
            print(f"API Health: {health}")
            return True
        except Exception as e:
            print(f"❌ API test failed: {e}")
            print("You may need to re-authenticate.")
            return False
    
    # Start OAuth flow
    print("\nStarting OAuth 2.0 authentication flow...")
    print("This will open a browser window for you to log in.")
    
    try:
        success = client.authenticate()
        if success:
            print("✅ Authentication successful!")
            print("You can now use the API client.")
            return True
        else:
            print("❌ Authentication failed!")
            return False
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False


def test_api_after_auth():
    """
    Test API calls after successful authentication
    """
    print("\nTesting API calls after authentication...")
    
    client = SimapAPI()
    
    if not client.is_authenticated():
        print("❌ Not authenticated. Please run authentication first.")
        return False
    
    try:
        # Test health check
        print("1. Testing health check...")
        health = client.health_check()
        print(f"   Health status: {health}")
        
        # Test getting tenders
        print("2. Testing tender retrieval...")
        tenders = client.get_tenders(limit=3)
        print(f"   Retrieved {len(tenders.get('data', []))} tenders")
        
        # Test search
        print("3. Testing search functionality...")
        search_results = client.search_tenders(
            query="economics OR policy",
            limit=3
        )
        print(f"   Found {len(search_results.get('data', []))} search results")
        
        print("✅ All API tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False


def main():
    """
    Main function to run OAuth authentication example
    """
    print("SIMAP.ch OAuth 2.0 Authentication Demo")
    print("=" * 60)
    
    # Step 1: OAuth Authentication
    print("\nSTEP 1: OAuth Authentication")
    print("-" * 30)
    
    if not oauth_authentication_example():
        print("\n❌ Authentication failed. Please check your client ID and try again.")
        return
    
    # Step 2: Test API calls
    print("\nSTEP 2: API Testing")
    print("-" * 30)
    
    if test_api_after_auth():
        print("\n🎉 OAuth authentication and API testing completed successfully!")
        print("\nYou can now use the SIMAP API client in your applications.")
    else:
        print("\n❌ API testing failed. Please check your authentication.")


if __name__ == "__main__":
    main()
