"""
SIMAP.ch API Client

This module provides a Python client for interacting with the SIMAP.ch API.
SIMAP (Système d'information pour les marchés publics) is the Swiss public procurement platform.

API Documentation: https://int.simap.ch/api-doc
Version: 1.3.0 (as of March 2025)

Authentication: OAuth 2.0 with PKCE (Proof Key for Code Exchange)
"""

import logging
from typing import Dict, Optional, Any
import os
import base64
import hashlib
import secrets
import webbrowser
from urllib.parse import urljoin, urlencode

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
    Client for SIMAP.ch API with OAuth 2.0 + PKCE authentication
    
    This class handles OAuth 2.0 authentication and provides methods to interact with
    the SIMAP.ch public procurement API.
    """
    
    # OAuth 2.0 endpoints
    AUTH_BASE_URL = "https://www.simap.ch/auth/realms/simap/protocol/openid-connect"
    TOKEN_ENDPOINT = f"{AUTH_BASE_URL}/token"
    AUTH_ENDPOINT = f"{AUTH_BASE_URL}/auth"
    
    def __init__(self, 
                 base_url: str = "https://int.simap.ch/api", 
                 client_id: Optional[str] = None,
                 redirect_uri: str = "http://localhost:8080/callback",
                 scope: str = "openid profile"):
        """
        Initialize the SIMAP API client with OAuth 2.0
        
        Args:
            base_url: Base URL for the SIMAP API
            client_id: OAuth client ID (can also be set via environment variable)
            redirect_uri: Redirect URI for OAuth flow
            scope: OAuth scope
        """
        if requests is None:
            raise ImportError("requests library is required. Please install it with: pip install requests")
            
        self.base_url = base_url.rstrip('/')
        self.client_id = client_id or os.getenv('SIMAP_CLIENT_ID')
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.session = requests.Session()
        self.access_token = None
        self.refresh_token = None
        
        # Set up default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'BAK-Economics-SIMAP-Client/1.0'
        })
        
        # Load existing tokens if available
        self._load_tokens()
    
    def _load_tokens(self):
        """Load tokens from environment variables or file"""
        self.access_token = os.getenv('SIMAP_ACCESS_TOKEN')
        self.refresh_token = os.getenv('SIMAP_REFRESH_TOKEN')
        
        # Update headers if we have a token
        if self.access_token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}'
            })
    
    def _save_tokens(self, access_token: str, refresh_token: str = None):
        """Save tokens to environment variables"""
        os.environ['SIMAP_ACCESS_TOKEN'] = access_token
        if refresh_token:
            os.environ['SIMAP_REFRESH_TOKEN'] = refresh_token
        
        # Update headers
        self.session.headers.update({
            'Authorization': f'Bearer {access_token}'
        })
    
    def _generate_pkce_pair(self) -> tuple[str, str]:
        """Generate PKCE code verifier and challenge"""
        # Generate code verifier (43-128 characters)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # Generate code challenge
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        return code_verifier, code_challenge
    
    def get_authorization_url(self) -> tuple[str, str]:
        """
        Generate authorization URL for OAuth flow
        
        Returns:
            tuple: (authorization_url, code_verifier)
        """
        if not self.client_id:
            raise ValueError("Client ID is required. Set SIMAP_CLIENT_ID environment variable or pass client_id parameter.")
        
        code_verifier, code_challenge = self._generate_pkce_pair()
        
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'scope': self.scope
        }
        
        auth_url = f"{self.AUTH_ENDPOINT}?{urlencode(params)}"
        return auth_url, code_verifier
    
    def start_authorization_flow(self) -> str:
        """
        Start the OAuth authorization flow by opening the browser
        
        Returns:
            str: Authorization URL
        """
        auth_url, code_verifier = self.get_authorization_url()
        
        print("Opening browser for SIMAP authentication...")
        print(f"Authorization URL: {auth_url}")
        
        # Store code verifier for later use
        self._code_verifier = code_verifier
        
        # Open browser
        webbrowser.open(auth_url)
        
        return auth_url
    
    def exchange_code_for_token(self, authorization_code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token
        
        Args:
            authorization_code: Authorization code from callback
            
        Returns:
            dict: Token response
        """
        if not hasattr(self, '_code_verifier'):
            raise ValueError("No code verifier found. Please start authorization flow first.")
        
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'code': authorization_code,
            'redirect_uri': self.redirect_uri,
            'code_verifier': self._code_verifier
        }
        
        response = requests.post(self.TOKEN_ENDPOINT, data=token_data)
        response.raise_for_status()
        
        token_response = response.json()
        
        # Save tokens
        self.access_token = token_response['access_token']
        if 'refresh_token' in token_response:
            self.refresh_token = token_response['refresh_token']
        
        self._save_tokens(self.access_token, self.refresh_token)
        
        return token_response
    
    def refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh the access token using refresh token
        
        Returns:
            dict: New token response
        """
        if not self.refresh_token:
            raise ValueError("No refresh token available")
        
        token_data = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'refresh_token': self.refresh_token
        }
        
        response = requests.post(self.TOKEN_ENDPOINT, data=token_data)
        response.raise_for_status()
        
        token_response = response.json()
        
        # Update tokens
        self.access_token = token_response['access_token']
        if 'refresh_token' in token_response:
            self.refresh_token = token_response['refresh_token']
        
        self._save_tokens(self.access_token, self.refresh_token)
        
        return token_response
    
    def is_authenticated(self) -> bool:
        """Check if client is authenticated"""
        return self.access_token is not None
    
    def authenticate(self) -> bool:
        """
        Complete OAuth authentication flow
        
        Returns:
            bool: True if authentication successful
        """
        try:
            if not self.client_id:
                print("Error: Client ID is required.")
                print("Please set SIMAP_CLIENT_ID environment variable or contact SIMAP support for client registration.")
                return False
            
            # Start authorization flow
            self.start_authorization_flow()
            
            print("\n" + "="*60)
            print("OAUTH AUTHENTICATION FLOW")
            print("="*60)
            print("1. A browser window should have opened with the SIMAP login page")
            print("2. Log in with your SIMAP account credentials")
            print("3. Complete the 2FA process (check your email for the code)")
            print("4. After successful login, you'll be redirected to a callback URL")
            print("5. Copy the 'code' parameter from the callback URL")
            print("\nExample callback URL:")
            print(f"{self.redirect_uri}?code=AUTHORIZATION_CODE_HERE")
            print("\nEnter the authorization code below:")
            
            # Get authorization code from user
            auth_code = input("Authorization code: ").strip()
            
            if not auth_code:
                print("No authorization code provided. Authentication cancelled.")
                return False
            
            # Exchange code for token
            token_response = self.exchange_code_for_token(auth_code)
            
            print("✅ Authentication successful!")
            print(f"Access token expires in: {token_response.get('expires_in', 'unknown')} seconds")
            
            return True
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
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
        # Check if authenticated
        if not self.is_authenticated():
            raise ValueError("Not authenticated. Please call authenticate() first.")
        
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        
        try:
            logger.info(f"Making {method} request to {url}")
            response = self.session.request(method, url, **kwargs)
            
            # Handle 401 Unauthorized - try to refresh token
            if response.status_code == 401 and self.refresh_token:
                logger.info("Access token expired, attempting to refresh...")
                try:
                    self.refresh_access_token()
                    # Retry the request with new token
                    response = self.session.request(method, url, **kwargs)
                except Exception as refresh_error:
                    logger.error(f"Token refresh failed: {refresh_error}")
                    raise ValueError("Authentication expired and refresh failed. Please re-authenticate.")
            
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
        
        # Check if already authenticated
        if client.is_authenticated():
            logger.info("Already authenticated, testing API calls...")
            
            # Test basic connectivity
            health = client.health_check()
            logger.info(f"API Health Check: {health}")
            
            # Test retrieving some tenders
            tenders = client.get_tenders(limit=5)
            logger.info(f"Retrieved {len(tenders.get('data', []))} tenders")
            
            return True
        else:
            logger.info("Not authenticated. Starting OAuth flow...")
            return client.authenticate()
        
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False


def main():
    """
    Main function for testing the SIMAP API client
    """
    print("Testing SIMAP.ch API Connection...")
    print("Note: This requires OAuth 2.0 authentication with SIMAP.ch")
    
    if test_connection():
        print("✅ SIMAP API connection successful!")
    else:
        print("❌ SIMAP API connection failed!")
        print("Please check your client ID and complete the OAuth flow.")


if __name__ == "__main__":
    main()
