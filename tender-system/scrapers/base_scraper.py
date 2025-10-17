"""
Base scraper class for tender sources.
"""
from abc import ABC, abstractmethod
from typing import List, Dict
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for tender scrapers"""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.logger = logger
    
    @abstractmethod
    def fetch_tenders(self, date_from: datetime = None, date_to: datetime = None) -> List[Dict]:
        """
        Fetch tenders from the source.
        
        Args:
            date_from: Start date for filtering
            date_to: End date for filtering
            
        Returns:
            List of tender dictionaries with standardized fields
        """
        pass
    
    @abstractmethod
    def fetch_tender_details(self, tender_id: str) -> Dict:
        """
        Fetch detailed information for a specific tender.
        
        Args:
            tender_id: Unique identifier for the tender
            
        Returns:
            Dictionary with detailed tender information
        """
        pass
    
    def normalize_tender(self, raw_data: Dict) -> Dict:
        """
        Normalize raw tender data to standard format.
        
        Returns:
            {
                'tender_id': str,
                'source': str,
                'title': str,
                'description': str,
                'publication_date': datetime,
                'deadline': datetime,
                'cpv_codes': list,
                'contracting_authority': str,
                'estimated_value': float,
                'raw_data': dict
            }
        """
        # Override in subclass if needed
        return raw_data
    
    def validate_tender(self, tender: Dict) -> bool:
        """Check if tender has required fields"""
        required = ['tender_id', 'title', 'source']
        return all(field in tender and tender[field] for field in required)

