"""
SIMAP tender scraper - based on Damlina's implementation.
"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List, Dict, Optional
from datetime import datetime
from time import sleep
from .base_scraper import BaseScraper


class SimapScraper(BaseScraper):
    """Scraper for Swiss SIMAP public procurement platform"""
    
    def __init__(self):
        super().__init__("simap")
        self.base_url = "https://prod.simap.ch/api/publications/v2/project/project-search"
        self.details_url_template = "https://prod.simap.ch/api/publications/v1/project/{}/publication-details/{}"
        
        # Setup robust session with retries
        self.session = requests.Session()
        self.session.headers.update({"accept": "application/json"})
        self.session.mount("https://", HTTPAdapter(max_retries=Retry(
            total=6, connect=6, read=6, status=6,
            backoff_factor=0.7,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )))
    
    def fetch_tenders(self, date_from: datetime = None, date_to: datetime = None) -> List[Dict]:
        """
        Fetch tenders from SIMAP API.
        
        Args:
            date_from: Start date for filtering (optional)
            date_to: End date for filtering (optional)
            
        Returns:
            List of normalized tender dictionaries
        """
        # Base query parameters
        params = {
            "processTypes": ["open"],
            "pubTypes": ["call_for_bids"],
            "projectSubTypes": ["service"],
            "cpvCodes": [
                "72000000", "79300000", "73100000", "79311400", "72314000",
                "79416000", "72320000", "98300000", "79310000", "79000000", "79311410"
            ],
            "pageSize": 100,
        }
        
        # Add date filters if provided
        if date_from:
            params["pubDateFrom"] = date_from.strftime("%Y-%m-%d")
        if date_to:
            params["pubDateTo"] = date_to.strftime("%Y-%m-%d")
        
        all_results = []
        seen_ids = set()
        last_item = None
        page = 1
        
        self.logger.info(f"🔍 Starting SIMAP scrape (date_from={date_from}, date_to={date_to})")
        
        while True:
            current_params = dict(params)
            if last_item:
                current_params["lastItem"] = last_item
            
            try:
                r = self.session.get(self.base_url, params=current_params, timeout=30)
                r.raise_for_status()
                data = r.json()
                
                projects = data.get("projects", [])
                if not projects:
                    break
                
                # Collect & dedupe by project id
                for p in projects:
                    pid = p.get("id")
                    if pid and pid not in seen_ids:
                        seen_ids.add(pid)
                        all_results.append(p)
                
                # Handle pagination
                paging = data.get("pagination") or data.get("paging") or {}
                last_item = paging.get("lastItem")
                if not last_item:
                    break
                
                page += 1
                sleep(0.2)  # Be polite to the API
                
            except requests.RequestException as e:
                self.logger.error(f"Error fetching page {page}: {e}")
                break
        
        self.logger.info(f"✅ Found {len(all_results)} tenders from SIMAP")
        
        # Normalize all tenders
        normalized_tenders = []
        for tender in all_results:
            normalized = self.normalize_tender(tender)
            if self.validate_tender(normalized):
                normalized_tenders.append(normalized)
        
        return normalized_tenders
    
    def fetch_tender_details(self, tender_id: str, publication_id: str = None) -> Dict:
        """
        Fetch detailed information for a specific tender.
        
        Args:
            tender_id: Project ID
            publication_id: Publication ID (if available)
            
        Returns:
            Dictionary with detailed tender information
        """
        if not publication_id:
            self.logger.warning(f"No publication_id provided for {tender_id}")
            return {}
        
        details_url = self.details_url_template.format(tender_id, publication_id)
        
        try:
            response = self.session.get(details_url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Extract orderDescription from procurement
            if isinstance(data.get("procurement"), dict):
                data["orderDescription"] = data["procurement"].get("orderDescription", "")
            
            return data
            
        except requests.RequestException as e:
            self.logger.error(f"Error fetching details for {tender_id}: {e}")
            return {}
    
    def normalize_tender(self, raw_data: Dict) -> Dict:
        """Normalize SIMAP tender to standard format"""
        
        # Extract publication date
        pub_date = None
        if raw_data.get("publicationDate"):
            try:
                pub_date = datetime.fromisoformat(raw_data["publicationDate"].replace('Z', '+00:00'))
            except:
                pass
        
        # Extract deadline
        deadline = None
        if raw_data.get("submissionDeadline"):
            try:
                deadline = datetime.fromisoformat(raw_data["submissionDeadline"].replace('Z', '+00:00'))
            except:
                pass
        
        normalized = {
            'tender_id': raw_data.get('id', ''),
            'source': self.source_name,
            'title': raw_data.get('title', ''),
            'description': raw_data.get('description', ''),  # Will be enriched with details
            'publication_date': pub_date,
            'deadline': deadline,
            'cpv_codes': raw_data.get('cpvs', []),
            'contracting_authority': raw_data.get('organisationName', ''),
            'estimated_value': None,  # Extract if available
            'publication_id': raw_data.get('publicationId', ''),  # Keep for fetching details
            'raw_data': raw_data
        }
        
        return normalized
    
    def enrich_with_details(self, tenders: List[Dict]) -> List[Dict]:
        """Fetch and add detailed descriptions to tenders"""
        enriched = []
        
        self.logger.info(f"📝 Enriching {len(tenders)} tenders with full details...")
        
        for tender in tenders:
            publication_id = tender.get('publication_id')
            if publication_id:
                details = self.fetch_tender_details(tender['tender_id'], publication_id)
                if details and 'orderDescription' in details:
                    tender['description'] = details['orderDescription']
            enriched.append(tender)
            sleep(0.1)  # Rate limiting
        
        self.logger.info("✅ Enrichment complete")
        return enriched

