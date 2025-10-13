"""
Extract text from case study PDFs and prepare them for use in the prompt.

INSTRUCTIONS:
1. Place your case study PDFs in: data/raw/case_studies/
2. Run this script: python scripts/00_extract_case_studies.py
3. Output will be saved to: data/raw/case_studies_text.md
"""

import os
from pathlib import Path
import PyPDF2
import pdfplumber

# Configuration
CASE_STUDIES_DIR = Path("data/raw/case_studies")
OUTPUT_FILE = Path("data/raw/case_studies_text.md")

def extract_text_pypdf2(pdf_path):
    """Extract text using PyPDF2."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
    except Exception as e:
        print(f"  PyPDF2 failed: {e}")
        return None

def extract_text_pdfplumber(pdf_path):
    """Extract text using pdfplumber (better for tables)."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
            return text.strip()
    except Exception as e:
        print(f"  pdfplumber failed: {e}")
        return None

def clean_text(text):
    """Clean extracted text."""
    if not text:
        return ""
    
    # Remove excessive whitespace
    import re
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    
    return text.strip()

def main():
    # Create case studies directory if it doesn't exist
    CASE_STUDIES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if directory has PDFs
    pdf_files = list(CASE_STUDIES_DIR.glob("*.pdf"))
    
    if not pdf_files:
        print(f"⚠️  No PDF files found in {CASE_STUDIES_DIR}")
        print(f"\nPlease add your case study PDFs to: {CASE_STUDIES_DIR.absolute()}")
        print("\nExample structure:")
        print("  data/raw/case_studies/")
        print("    ├── case_study_1.pdf")
        print("    ├── case_study_2.pdf")
        print("    └── case_study_3.pdf")
        return
    
    print(f"Found {len(pdf_files)} PDF files in {CASE_STUDIES_DIR}")
    print()
    
    # Extract text from each PDF
    case_studies = []
    
    for pdf_path in sorted(pdf_files):
        print(f"Processing: {pdf_path.name}")
        
        # Try pdfplumber first (better quality)
        text = extract_text_pdfplumber(pdf_path)
        
        # Fallback to PyPDF2
        if not text or len(text) < 100:
            print(f"  Trying PyPDF2 as fallback...")
            text = extract_text_pypdf2(pdf_path)
        
        if text and len(text) > 100:
            text = clean_text(text)
            case_studies.append({
                'filename': pdf_path.name,
                'text': text,
                'length': len(text)
            })
            print(f"  ✓ Extracted {len(text):,} characters")
        else:
            print(f"  ✗ Failed to extract meaningful text")
        
        print()
    
    if not case_studies:
        print("❌ No case studies extracted successfully")
        return
    
    # Write to markdown file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("# BAK Economics Case Studies\n\n")
        f.write(f"Extracted from {len(case_studies)} PDF documents.\n\n")
        f.write("These are examples of successful projects completed by BAK Economics after winning tenders.\n")
        f.write("Use these to understand the type of work, methodology, and deliverables.\n\n")
        f.write("---\n\n")
        
        for i, study in enumerate(case_studies, 1):
            f.write(f"## Case Study {i}: {study['filename']}\n\n")
            f.write(f"**Length:** {study['length']:,} characters\n\n")
            
            # Include first 5000 chars (rest can be truncated for prompt)
            text_preview = study['text'][:5000]
            if len(study['text']) > 5000:
                text_preview += f"\n\n[... truncated {len(study['text']) - 5000:,} more characters ...]"
            
            f.write(f"**Content:**\n\n{text_preview}\n\n")
            f.write("---\n\n")
    
    print(f"✓ Saved case studies to: {OUTPUT_FILE}")
    print(f"\nSummary:")
    print(f"  Total case studies: {len(case_studies)}")
    print(f"  Total characters: {sum(s['length'] for s in case_studies):,}")
    print(f"  Average length: {sum(s['length'] for s in case_studies) // len(case_studies):,} chars")
    print()
    print("Next steps:")
    print("1. Review the extracted text in data/raw/case_studies_text.md")
    print("2. Run 00_reload_data_with_fulltext.py to prepare the full dataset")
    print("3. Run 03_build_prompt_v3_with_cases.py to build the new prompt")

if __name__ == "__main__":
    main()

