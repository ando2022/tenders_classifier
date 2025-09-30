"""
SIMAP.ch API Client

This module provides a Python client for interacting with the SIMAP.ch API.
SIMAP (Système d'information pour les marchés publics) is the Swiss public procurement platform.

API Documentation: https://int.simap.ch/api-doc
Version: 1.3.0 (as of March 2025)
"""

import logging
from typing import Dict, Optional, Any
import os
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    print("Error: requests library not found. Please install it with: pip install requests")
    requests = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimapAPI:
    """
    Client for SIMAP.ch API
    
    This class handles authentication and provides methods to interact with
    the SIMAP.ch public procurement API.
    """
    
    def __init__(self, base_url: str = "https://int.simap.ch/api", api_key: Optional[str] = None):
        """
        Initialize the SIMAP API client
        
        Args:
            base_url: Base URL for the SIMAP API
            api_key: API key for authentication (can also be set via environment variable)
        """
        if requests is None:
            raise ImportError("requests library is required. Please install it with: pip install requests")
            
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key or os.getenv('SIMAP_API_KEY')
        self.session = requests.Session()
        
        # Set up default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'BAK-Economics-SIMAP-Client/1.0'
        })
        
        # Add API key to headers if provided
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}'
            })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make a request to the SIMAP API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments for requests
            
        Returns:
            JSON response as dictionary
            
        Raises:
            requests.RequestException: If the request fails
        """
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        
        try:
            logger.info(f"Making {method} request to {url}")
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
    
    def get_tenders(self, 
                   limit: int = 100, 
                   offset: int = 0,
                   search_term: Optional[str] = None,
                   date_from: Optional[str] = None,
                   date_to: Optional[str] = None,
                   **filters) -> Dict[str, Any]:
        """
        Retrieve tenders from SIMAP
        
        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip
            search_term: Search term for tender content
            date_from: Start date for filtering (YYYY-MM-DD format)
            date_to: End date for filtering (YYYY-MM-DD format)
            **filters: Additional filters to apply
            
        Returns:
            Dictionary containing tender data and metadata
        """
        params = {
            'limit': limit,
            'offset': offset
        }
        
        if search_term:
            params['search'] = search_term
        if date_from:
            params['dateFrom'] = date_from
        if date_to:
            params['dateTo'] = date_to
            
        # Add any additional filters
        params.update(filters)
        
        return self._make_request('GET', '/tenders', params=params)
    
    def get_tender_by_id(self, tender_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific tender by its ID
        
        Args:
            tender_id: Unique identifier for the tender
            
        Returns:
            Dictionary containing tender details
        """
        return self._make_request('GET', f'/tenders/{tender_id}')
    
    def search_tenders(self, 
                      query: str,
                      limit: int = 100,
                      offset: int = 0,
                      **filters) -> Dict[str, Any]:
        """
        Search for tenders using a query string
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            offset: Number of results to skip
            **filters: Additional filters to apply
            
        Returns:
            Dictionary containing search results
        """
        params = {
            'q': query,
            'limit': limit,
            'offset': offset
        }
        params.update(filters)
        
        return self._make_request('GET', '/search/tenders', params=params)
    
    def get_organizations(self, 
                         limit: int = 100,
                         offset: int = 0,
                         **filters) -> Dict[str, Any]:
        """
        Retrieve organizations from SIMAP
        
        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip
            **filters: Additional filters to apply
            
        Returns:
            Dictionary containing organization data
        """
        params = {
            'limit': limit,
            'offset': offset
        }
        params.update(filters)
        
        return self._make_request('GET', '/organizations', params=params)
    
    def get_organization_by_id(self, org_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific organization by its ID
        
        Args:
            org_id: Unique identifier for the organization
            
        Returns:
            Dictionary containing organization details
        """
        return self._make_request('GET', f'/organizations/{org_id}')
    
    def get_categories(self) -> Dict[str, Any]:
        """
        Retrieve available tender categories
        
        Returns:
            Dictionary containing category data
        """
        return self._make_request('GET', '/categories')
    
    def get_locations(self) -> Dict[str, Any]:
        """
        Retrieve available locations
        
        Returns:
            Dictionary containing location data
        """
        return self._make_request('GET', '/locations')
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check API health and connectivity
        
        Returns:
            Dictionary containing API status information
        """
        return self._make_request('GET', '/health')


# Example usage and testing functions
def test_connection():
    """
    Test the SIMAP API connection
    """
    try:
        # Initialize the client
        client = SimapAPI()
        
        # Test basic connectivity
        health = client.health_check()
        logger.info(f"API Health Check: {health}")
        
        # Test retrieving some tenders
        tenders = client.get_tenders(limit=5)
        logger.info(f"Retrieved {len(tenders.get('data', []))} tenders")
        
        return True
        
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False


def main():
    """
    Main function for testing the SIMAP API client
    """
    print("Testing SIMAP.ch API Connection...")
    
    if test_connection():
        print("✅ SIMAP API connection successful!")
    else:
        print("❌ SIMAP API connection failed!")
        print("Please check your API key and network connection.")


if __name__ == "__main__":
    main()
