"""
XML/HTML Content Extractor for Swiss SIMAP Tenders

Extracts relevant sections from tender full text while filtering out boilerplate.
"""
import re
from typing import Dict, Optional
import xml.etree.ElementTree as ET


def extract_text_from_xml_tags(text: str, tags: list) -> str:
    """
    Extract text content from specific XML tags.
    
    Args:
        text: Full XML/HTML text
        tags: List of tag names to extract (e.g., ['CONT.DESCR', 'LOT.DESCR'])
    
    Returns:
        Extracted text combined from all matching tags
    """
    if not isinstance(text, str) or not text:
        return ""
    
    extracted = []
    
    for tag in tags:
        # Use regex to find content between tags
        # Handles both <TAG>content</TAG> and <TAG>content with nested tags</TAG>
        pattern = f'<{re.escape(tag)}>(.*?)</{re.escape(tag)}>'
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            # Remove any remaining XML tags from the content
            clean = re.sub(r'<[^>]+>', ' ', match)
            # Decode HTML entities
            clean = clean.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
            clean = clean.replace('&quot;', '"').replace('&apos;', "'").replace('&nbsp;', ' ')
            # Remove excessive whitespace
            clean = re.sub(r'\s+', ' ', clean).strip()
            
            if len(clean) > 20:  # Only add if meaningful
                extracted.append(clean)
    
    return ' '.join(extracted)


def extract_project_description(xml_text: str) -> str:
    """
    Extract the project description from SIMAP tender XML.
    
    Focuses on relevant sections per SIMAP structure:
    - 2.6 Gegenstand und Umfang des Auftrags (Subject and scope)
    - CONT.DESCR: Project description
    - CONT.NAME: Contract name
    """
    return extract_text_from_xml_tags(xml_text, ['CONT.DESCR', 'CONT.NAME'])


def extract_simap_relevant_sections(xml_text: str) -> str:
    """
    Extract ONLY the relevant SIMAP tender sections for BAK Economics.
    
    Per domain expert guidance, focuses on:
    - 2.6 Gegenstand und Umfang des Auftrags (Subject and scope of contract)
      → CONT.DESCR, CONT.NAME, LOT.DESCR
    - 3.7 Eignungskriterien (Suitability criteria)
      → OB01.COND.TECHNICAL
    - 3.8 Geforderte Nachweise (Required evidence/qualifications)
      → OB01.COND.PROOF
    
    Excludes:
    - Legal boilerplate (OB01.INFO.LEGAL)
    - Payment terms (OB01.COND.PAYMENT)
    - Administrative details (AUTH.CONTACT, addresses)
    """
    return extract_text_from_xml_tags(xml_text, [
        # 2.6 Subject and scope
        'CONT.DESCR',
        'CONT.NAME',
        'LOT.DESCR',
        # 3.7 Suitability criteria  
        'OB01.COND.TECHNICAL',
        # 3.8 Required evidence
        'OB01.COND.PROOF'
    ])

def extract_description_and_deliverables(xml_text: str) -> str:
    """
    Alias for extract_simap_relevant_sections.
    Kept for backwards compatibility.
    """
    return extract_simap_relevant_sections(xml_text)


def extract_all_project_content(xml_text: str) -> str:
    """
    Extract all project-related content, excluding pure administrative/legal sections.
    
    Includes:
    - Project description
    - Contract details
    - Deliverables
    - Requirements
    
    Excludes:
    - Legal text (OB01.INFO.LEGAL)
    - Proof requirements (OB01.COND.PROOF)
    - Payment conditions (detailed legal)
    """
    return extract_text_from_xml_tags(xml_text, [
        'CONT.DESCR',
        'CONT.NAME',
        'LOT.DESCR',
        'OB01.COND.TECHNICAL',
        'CONT.LOC'
    ])


def smart_extract(xml_text: str, method: str = "description_only", max_chars: int = 2000) -> str:
    """
    Smart extraction dispatcher.
    
    Args:
        xml_text: Full XML/HTML text from tender
        method: Extraction method:
            - "description_only": Just CONT.DESCR (cleanest)
            - "desc_deliverables": Description + LOT.DESCR
            - "all_project": All project-related sections
            - "cleaned_full": Full text with tags removed (baseline)
        max_chars: Maximum characters to return
    
    Returns:
        Extracted and cleaned text, truncated to max_chars
    """
    if not isinstance(xml_text, str) or not xml_text:
        return ""
    
    if method == "description_only":
        extracted = extract_project_description(xml_text)
    elif method == "desc_deliverables" or method == "simap_relevant":
        # Sections 2.6, 3.7, 3.8 from SIMAP
        extracted = extract_simap_relevant_sections(xml_text)
    elif method == "all_project":
        extracted = extract_all_project_content(xml_text)
    elif method == "cleaned_full":
        # Fallback: just remove all tags
        extracted = re.sub(r'<[^>]+>', ' ', xml_text)
        extracted = re.sub(r'<!DOCTYPE[^>]*>', '', extracted)
        extracted = re.sub(r'<\?xml[^>]*\?>', '', extracted)
    else:
        extracted = ""
    
    # Clean up
    extracted = re.sub(r'\s+', ' ', extracted).strip()
    
    # Truncate if needed
    if len(extracted) > max_chars:
        extracted = extracted[:max_chars]
    
    return extracted


def analyze_xml_coverage(xml_text: str) -> Dict[str, any]:
    """
    Analyze what content is available in the XML.
    Useful for debugging and understanding data quality.
    """
    if not isinstance(xml_text, str):
        return {"has_xml": False}
    
    analysis = {
        "has_xml": xml_text.startswith('<?xml') or '<' in xml_text,
        "total_length": len(xml_text),
        "has_cont_descr": 'CONT.DESCR' in xml_text or 'CONT.NAME' in xml_text,
        "has_lot_descr": 'LOT.DESCR' in xml_text,
        "has_technical": 'COND.TECHNICAL' in xml_text,
        "has_legal": 'INFO.LEGAL' in xml_text,
    }
    
    # Count what we can extract
    if analysis["has_cont_descr"]:
        desc = extract_project_description(xml_text)
        analysis["description_length"] = len(desc)
    else:
        analysis["description_length"] = 0
    
    if analysis["has_lot_descr"]:
        lots = extract_text_from_xml_tags(xml_text, ['LOT.DESCR'])
        analysis["deliverables_length"] = len(lots)
    else:
        analysis["deliverables_length"] = 0
    
    return analysis


# Example usage and testing
if __name__ == "__main__":
    import pandas as pd
    from pathlib import Path
    
    # Test on real data
    base_dir = Path(__file__).parent.parent
    excel_path = base_dir / "data" / "raw" / "tenders_content.xlsx"
    
    if excel_path.exists():
        print("Testing XML extraction on sample tender...\n")
        
        df = pd.read_excel(excel_path, sheet_name="TITLES", nrows=5)
        
        for i, row in df.iterrows():
            print(f"\n{'='*80}")
            print(f"Tender #{i+1}: {row['title'][:60]}...")
            print(f"{'='*80}")
            
            full_text = row['full text']
            
            # Analyze
            analysis = analyze_xml_coverage(full_text)
            print(f"\nAnalysis:")
            print(f"  Has XML: {analysis['has_xml']}")
            print(f"  Has description: {analysis['has_cont_descr']}")
            print(f"  Has deliverables: {analysis['has_lot_descr']}")
            print(f"  Total length: {analysis['total_length']:,} chars")
            print(f"  Description length: {analysis.get('description_length', 0):,} chars")
            print(f"  Deliverables length: {analysis.get('deliverables_length', 0):,} chars")
            
            # Extract with different methods
            print(f"\nExtraction results:")
            
            desc_only = smart_extract(full_text, method="description_only", max_chars=500)
            print(f"\n  Description only ({len(desc_only)} chars):")
            print(f"  {desc_only[:200]}...")
            
            desc_deliv = smart_extract(full_text, method="desc_deliverables", max_chars=500)
            print(f"\n  Desc + Deliverables ({len(desc_deliv)} chars):")
            print(f"  {desc_deliv[:200]}...")
            
            if i >= 2:  # Just show first 3
                break
    else:
        print(f"Error: {excel_path} not found")
        print("\nExample usage:")
        print("  from utils.xml_extractor import smart_extract")
        print("  text = smart_extract(xml_text, method='description_only')")

