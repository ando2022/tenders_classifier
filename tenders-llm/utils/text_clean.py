"""
Text cleaning utilities
"""

import re
import unicodedata
import pandas as pd

_ZW = dict.fromkeys([0x200B, 0x200C, 0x200D, 0xFEFF], None)

def normalize_text(s: str) -> str:
    """Advanced text normalization: NFKC, zero-width removal, control chars."""
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = s.translate(_ZW)  # remove zero-width
    # remove control chars (except newline)
    s = re.sub(r"[\x00-\x08\x0B-\x1F\x7F]", " ", s)
    # normalize whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s

def clean_text(text: str) -> str:
    """Basic text cleaning: normalize, strip, clean whitespace."""
    if pd.isna(text):
        return ""
    
    text = str(text)
    text = normalize_text(text)
    
    return text

def remove_html(text: str) -> str:
    """Remove HTML tags."""
    return re.sub(r'<[^>]+>', '', text)

def normalize_quotes(text: str) -> str:
    """Normalize quotes to ASCII."""
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace("'", "'").replace("'", "'")
    return text

