"""
Text cleaning utilities
"""

import re
import pandas as pd

def clean_text(text: str) -> str:
    """Basic text cleaning: lowercase, strip, normalize whitespace."""
    if pd.isna(text):
        return ""
    
    text = str(text)
    
    # Remove excessive whitespace/newlines
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing
    text = text.strip()
    
    return text

def remove_html(text: str) -> str:
    """Remove HTML tags."""
    return re.sub(r'<[^>]+>', '', text)

def normalize_quotes(text: str) -> str:
    """Normalize quotes to ASCII."""
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace("'", "'").replace("'", "'")
    return text

