"""
Configuration settings for the BAK Economics project

This module contains configuration settings for the SIMAP API and other project components.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for the BAK Economics project"""
    
    # SIMAP API Configuration
    SIMAP_API_BASE_URL = "https://int.simap.ch/api"
    SIMAP_API_KEY = os.getenv('SIMAP_API_KEY')
    SIMAP_API_VERSION = "1.3.0"
    
    # API Request Settings
    DEFAULT_REQUEST_TIMEOUT = 30  # seconds
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds
    
    # Data Processing Settings
    DEFAULT_PAGE_SIZE = 100
    MAX_PAGE_SIZE = 1000
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Data Storage
    DATA_DIR = "data"
    RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
    PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
    
    # Output Settings
    OUTPUT_DIR = "reports"
    
    @classmethod
    def validate_config(cls) -> bool:
        """
        Validate that all required configuration is present
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        required_settings = [
            'SIMAP_API_BASE_URL',
        ]
        
        for setting in required_settings:
            if not getattr(cls, setting):
                print(f"Warning: {setting} is not configured")
                return False
        
        return True
    
    @classmethod
    def get_api_key(cls) -> Optional[str]:
        """
        Get the SIMAP API key from environment variables
        
        Returns:
            str or None: API key if available
        """
        return cls.SIMAP_API_KEY
    
    @classmethod
    def setup_directories(cls):
        """
        Create necessary directories if they don't exist
        """
        directories = [
            cls.DATA_DIR,
            cls.RAW_DATA_DIR,
            cls.PROCESSED_DATA_DIR,
            cls.OUTPUT_DIR
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)


# BAK Economics specific configuration
class BAKConfig:
    """BAK Economics specific configuration"""
    
    # Keywords for opportunity identification
    KEYWORDS = [
        "economics", "economic", "economy",
        "policy", "policies", "analysis",
        "research", "study", "studies",
        "consulting", "advisory",
        "data", "statistics", "statistical",
        "forecasting", "modeling", "models",
        "evaluation", "assessment",
        "strategy", "strategic",
        "market", "markets",
        "financial", "finance",
        "budget", "budgetary",
        "public", "government",
        "federal", "cantonal", "municipal"
    ]
    
    # Company fit criteria
    COMPANY_FIT_CRITERIA = {
        "sector": ["public", "government", "federal", "cantonal", "municipal"],
        "size": ["large", "medium"],
        "budget": ["high", "medium"],
        "timeline": ["short", "medium"]
    }
    
    # Opportunity scoring weights
    SCORING_WEIGHTS = {
        "keyword_match": 0.3,
        "company_fit": 0.4,
        "budget_size": 0.2,
        "timeline": 0.1
    }
