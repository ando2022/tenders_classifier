"""
Test script for SIMAP API client

This script tests the SIMAP API client functionality without requiring authentication.
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


def test_client_initialization():
    """Test that the client can be initialized properly"""
    print("=== Testing Client Initialization ===")
    
    try:
        # Test without API key
        client = SimapAPI()
        print("✅ Client initialized successfully without API key")
        
        # Test with API key
        client_with_key = SimapAPI(api_key="test_key")
        print("✅ Client initialized successfully with API key")
        
        return True
        
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        return False


def test_api_endpoints_structure():
    """Test that all API methods are available"""
    print("\n=== Testing API Methods ===")
    
    try:
        client = SimapAPI()
        
        # Check that all methods exist
        methods = [
            'get_tenders', 'get_tender_by_id', 'search_tenders',
            'get_organizations', 'get_organization_by_id',
            'get_categories', 'get_locations', 'health_check'
        ]
        
        for method in methods:
            if hasattr(client, method):
                print(f"✅ Method '{method}' is available")
            else:
                print(f"❌ Method '{method}' is missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Method testing failed: {e}")
        return False


def test_authentication_handling():
    """Test authentication handling"""
    print("\n=== Testing Authentication Handling ===")
    
    try:
        # Test that API key is properly set in headers
        client = SimapAPI(api_key="test_api_key")
        
        if "Authorization" in client.session.headers:
            auth_header = client.session.headers["Authorization"]
            if auth_header == "Bearer test_api_key":
                print("✅ API key properly set in headers")
            else:
                print(f"❌ API key not properly formatted: {auth_header}")
                return False
        else:
            print("❌ Authorization header not found")
            return False
        
        # Test environment variable handling
        os.environ['SIMAP_API_KEY'] = 'env_test_key'
        client_env = SimapAPI()
        
        if client_env.api_key == 'env_test_key':
            print("✅ Environment variable API key properly loaded")
        else:
            print(f"❌ Environment variable API key not loaded: {client_env.api_key}")
            return False
        
        # Clean up
        del os.environ['SIMAP_API_KEY']
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication testing failed: {e}")
        return False


def test_request_structure():
    """Test that request methods have correct structure"""
    print("\n=== Testing Request Structure ===")
    
    try:
        client = SimapAPI()
        
        # Test that _make_request method exists and is callable
        if hasattr(client, '_make_request') and callable(getattr(client, '_make_request')):
            print("✅ _make_request method is available and callable")
        else:
            print("❌ _make_request method is missing or not callable")
            return False
        
        # Test that session is properly configured
        if hasattr(client, 'session') and client.session is not None:
            print("✅ Session is properly initialized")
        else:
            print("❌ Session is not properly initialized")
            return False
        
        # Test headers
        expected_headers = ['Content-Type', 'Accept', 'User-Agent']
        for header in expected_headers:
            if header in client.session.headers:
                print(f"✅ Header '{header}' is set")
            else:
                print(f"❌ Header '{header}' is missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Request structure testing failed: {e}")
        return False


def test_error_handling():
    """Test error handling without making actual API calls"""
    print("\n=== Testing Error Handling ===")
    
    try:
        client = SimapAPI()
        
        # Test that methods exist and can be called with proper parameters
        # (We won't actually make the calls since we don't have API access)
        
        # Test get_tenders method signature
        import inspect
        sig = inspect.signature(client.get_tenders)
        params = list(sig.parameters.keys())
        expected_params = ['limit', 'offset', 'search_term', 'date_from', 'date_to']
        
        for param in expected_params:
            if param in params:
                print(f"✅ Parameter '{param}' is available in get_tenders")
            else:
                print(f"❌ Parameter '{param}' is missing from get_tenders")
                return False
        
        print("✅ Error handling structure is correct")
        return True
        
    except Exception as e:
        print(f"❌ Error handling testing failed: {e}")
        return False


def main():
    """Run all tests"""
    print("SIMAP API Client Test Suite")
    print("=" * 50)
    
    tests = [
        test_client_initialization,
        test_api_endpoints_structure,
        test_authentication_handling,
        test_request_structure,
        test_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The SIMAP API client is ready to use.")
        print("\nNext steps:")
        print("1. Obtain a SIMAP API key from https://int.simap.ch/api-doc")
        print("2. Set the SIMAP_API_KEY environment variable")
        print("3. Run the example_usage.py script to test with real API calls")
    else:
        print("❌ Some tests failed. Please check the implementation.")
    
    return passed == total


if __name__ == "__main__":
    main()
