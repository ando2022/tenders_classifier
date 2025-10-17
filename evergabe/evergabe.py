"""
Exported from evergabe/evergabe.ipynb

Single-pass Evergabe scraper:
- Multilingual include/exclude keyword filters
- Full column extraction with per-cell links
- Stable UID per row
- Optionally visits each detail_url to capture page text (no PDF downloads)
- Saves CSV output
"""

import csv
import time
import re
import math
import datetime
import unicodedata
import os
import uuid
import pathlib
from collections import defaultdict
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# -------- Settings --------
START_URL = "https://www.evergabe-online.de/search.html?4"
DOWNLOAD_DIR = "downloads"     # PDFs will be saved here
HEADLESS = True                # set to False to watch the browser
MAX_PAGES = 3                  # set an int (e.g., 5) for quick testing
PER_PAGE_DELAY = 0.15          # seconds; be polite but fast

# -------- Load keywords from cpv_config.py --------
def _norm(s: str) -> str:
    """Lowercase, strip accents, collapse whitespace."""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", s.strip().lower())

def translate_column_name(german_name):
    """Translate German column names to English"""
    translations = {
        "Bezeichnung": "Title",
        "Geschäftszeichen": "Reference_Number", 
        "Vergabestelle": "Contracting_Authority",
        "Ort der Leistung": "Place_of_Performance",
        "Veröffentlichungsdatum": "Publication_Date",
        "Bewerbungsfrist": "Application_Deadline",
        "Letzte Veröffentlichung": "Last_Publication",
        "Zuletzt veröffentlicht": "Last_Published",
        "Verfahrensart": "Procedure_Type",
        "Auftragsart": "Contract_Type",
        "Geschätzte Kosten": "Estimated_Costs",
        "CPV-Code": "CPV_Code",
        "NUTS-Code": "NUTS_Code",
        "Zusätzliche Informationen": "Additional_Information",
        "Kurzbeschreibung": "Short_Description",
        "Beschreibung": "Description",
        "Leistungsbeschreibung": "Service_Description",
        "Ausschreibungsunterlagen": "Tender_Documents",
        "Ansprechpartner": "Contact_Person",
        "Telefon": "Phone",
        "E-Mail": "Email",
        "Internet": "Website",
        "Fax": "Fax",
        "Postleitzahl": "Postal_Code",
        "Ort": "City",
        "Land": "Country",
        "Strasse": "Street",
        "Hausnummer": "House_Number",
        "Adresse": "Address",
        "Name": "Name",
        "Firma": "Company",
        "Organisation": "Organization",
        "Institution": "Institution",
        "Behörde": "Authority",
        "Ministerium": "Ministry",
        "Amt": "Office",
        "Bundesamt": "Federal_Office",
        "Kanton": "Canton",
        "Gemeinde": "Municipality",
        "Stadt": "City",
        "Region": "Region",
        "Bereich": "Area",
        "Abteilung": "Department",
        "Referat": "Section",
        "Sachgebiet": "Subject_Area",
        "Fachbereich": "Field",
        "Bereich": "Area",
        "Sparte": "Division",
        "Zweig": "Branch",
        "Fachgebiet": "Specialty",
        "Tätigkeitsbereich": "Activity_Area",
        "Aufgabenbereich": "Task_Area",
        "Zuständigkeitsbereich": "Responsibility_Area",
        "Einzugsgebiet": "Catchment_Area",
        "Tätigkeitsfeld": "Field_of_Activity",
        "Arbeitsgebiet": "Work_Area",
        "Betätigungsfeld": "Field_of_Operation",
        "Geschäftsbereich": "Business_Area",
        "Fachbereich": "Department",
        "Ressort": "Ministry",
        "Referat": "Section",
        "Abteilung": "Department",
        "Bereich": "Area",
        "Sparte": "Division",
        "Zweig": "Branch",
        "Fachgebiet": "Specialty",
        "Tätigkeitsbereich": "Activity_Area",
        "Aufgabenbereich": "Task_Area",
        "Zuständigkeitsbereich": "Responsibility_Area",
        "Einzugsgebiet": "Catchment_Area",
        "Tätigkeitsfeld": "Field_of_Activity",
        "Arbeitsgebiet": "Work_Area",
        "Betätigungsfeld": "Field_of_Operation",
        "Geschäftsbereich": "Business_Area"
    }
    return translations.get(german_name, german_name)

# Load keywords from cpv_config.py
try:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from scraper.cpv_config import EVERGABE_KEYWORDS
    
    # Filter out CPV codes (keep only text-based keywords)
    CPV_PATTERN_FILTER = re.compile(r'^\d{8}(?:-\d)?$')
    FILTERED_KEYWORDS = [k for k in EVERGABE_KEYWORDS if not CPV_PATTERN_FILTER.match(str(k).strip())]
    INCLUDE = {_norm(k) for k in FILTERED_KEYWORDS if str(k).strip()}
    EXCLUDE = set()  # No exclusion filtering
    print(f"🔎 Loaded {len(INCLUDE)} keywords from cpv_config.py")
except Exception as e:
    print(f"⚠️  Could not import EVERGABE_KEYWORDS: {e}")
    INCLUDE = set()
    EXCLUDE = set()

# -------- Selenium setup --------
def make_driver(headless=True):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--lang=de-DE")
    # Reduce noisy Chrome logs on Windows (USB/GCM DEPRECATED_ENDPOINT, etc.)
    opts.add_argument("--log-level=3")
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])  # suppress USB/GCM warnings
    opts.add_experimental_option("useAutomationExtension", False)
    # Silence chromedriver logs as well
    try:
        service = Service(ChromeDriverManager().install(), log_output=open(os.devnull, "w"))
    except TypeError:
        # Older selenium versions don't support log_output
        service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)

def accept_cookies(driver):
    labels = ["Alle akzeptieren","Akzeptieren","Zustimmen","Einverstanden","OK","Okay","Ich stimme zu"]
    for label in labels:
        try:
            btn = WebDriverWait(driver, 4).until(
                EC.element_to_be_clickable((By.XPATH, f"//button[contains(., '{label}')]"))
            )
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(0.2)
            break
        except Exception:
            pass

def wait_for_table(driver, timeout=25):
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
    )

def first_cell_token(driver):
    try:
        return driver.find_element(By.CSS_SELECTOR, "table tbody tr td").get_attribute("innerText").strip()
    except Exception:
        return None

def set_page_size_max(driver):
    """Try to switch page size to the largest (100/200/Alle)."""
    tried = False
    for sel in ["select", "select.page-size", "select[name*='size' i]"]:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            s = Select(el)
            labels = [o.text.strip() or o.get_attribute("value") for o in s.options]
            target = None
            for want in ("200","100","Alle","Alles"):
                for lbl in labels:
                    if want in (lbl or ""):
                        target = lbl; break
                if target: break
            if not target and labels:
                target = labels[-1]
            if target:
                old = first_cell_token(driver)
                s.select_by_visible_text(target)
                WebDriverWait(driver, 15).until(lambda d: first_cell_token(d) != old)
                tried = True
                break
        except Exception:
            pass
    if not tried:
        for want in ("200","100"):
            try:
                btn = driver.find_element(By.XPATH, f"//button[normalize-space()='{want}']")
                old = first_cell_token(driver)
                driver.execute_script("arguments[0].click();", btn)
                WebDriverWait(driver, 15).until(lambda d: first_cell_token(d) != old)
                break
            except Exception:
                pass

# -------- Table header & row extraction --------
def unique_headers(headers):
    counts = defaultdict(int)
    out = []
    for h in headers:
        key = h or "col"
        counts[key] += 1
        out.append(key if counts[key] == 1 else f"{key}_{counts[key]}")
    return out

def get_table_headers(driver):
    table = driver.find_element(By.CSS_SELECTOR, "table")
    ths = table.find_elements(By.CSS_SELECTOR, "thead th")
    headers = [th.get_attribute("innerText").strip() or th.get_attribute("title") or th.get_attribute("aria-label") or "" for th in ths]
    if not any(h for h in headers):
        # fall back to data-title/aria-label on tds
        try:
            first_row = table.find_element(By.CSS_SELECTOR, "tbody tr")
            tds = first_row.find_elements(By.CSS_SELECTOR, "td")
            tmp = []
            for td in tds:
                label = td.get_attribute("data-title") or td.get_attribute("aria-label") or ""
                tmp.append(label)
            headers = tmp
        except Exception:
            pass
    if not headers:
        first_row = table.find_element(By.CSS_SELECTOR, "tbody tr")
        n = len(first_row.find_elements(By.CSS_SELECTOR, "td"))
        headers = [f"col_{i+1}" for i in range(n)]
    
    # Translate German headers to English
    translated_headers = [translate_column_name(h.strip()) for h in headers]
    return unique_headers(translated_headers)

def row_dicts_all_columns(driver, headers):
    """
    Extract all visible columns and apply inclusion/exclusion filters.
    Adds <column>_link if a link exists in that cell.
    """
    table = driver.find_element(By.CSS_SELECTOR, "table")
    rows = []
    for tr in table.find_elements(By.CSS_SELECTOR, "tbody tr"):
        tds = tr.find_elements(By.CSS_SELECTOR, "td")
        if not tds:
            continue
        row = {}
        concat = []
        for i, td in enumerate(tds):
            key = headers[i] if i < len(headers) else f"col_{i+1}"
            text = td.get_attribute("innerText").strip()
            row[key] = text
            concat.append(text)
            # capture first link in cell
            try:
                a = td.find_element(By.CSS_SELECTOR, "a[href]")
                row[f"{key}_link"] = a.get_attribute("href")
                if i == 0 and "detail_url" not in row:
                    row["detail_url"] = a.get_attribute("href")  # likely the main detail link
            except Exception:
                pass
        norm = _norm(" | ".join(concat))
        hits_incl = sorted({kw for kw in INCLUDE if kw in norm})
        hits_excl = sorted({kw for kw in EXCLUDE if kw in norm})
        if hits_incl and not hits_excl:
            row["matched_keywords"] = ", ".join(hits_incl)
            rows.append(row)
    return rows

def go_next(driver):
    try:
        nxt = driver.find_element(By.CSS_SELECTOR, "a[rel='next']")
        if (nxt.get_attribute("aria-disabled") or "").lower() == "true":
            return False
        token = first_cell_token(driver)
        driver.execute_script("arguments[0].click();", nxt)
        WebDriverWait(driver, 15).until(lambda d: first_cell_token(d) != token)
        return True
    except Exception:
        return False

# -------- Detail page scraping (text only) --------
def ensure_dir(path):
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)

def selenium_cookies_to_requests(driver):
    raise NotImplementedError("PDF/download features removed for CSV-only export.")

def collect_pdf_links(driver, base_url):
    return []

def click_possible_docs_tabs(driver):
    return None

def fetch_detail_and_pdfs(driver, detail_url, uid, req_sess, max_pdfs=10, timeout=30):
    raise NotImplementedError("PDF/detail fetching removed for CSV-only export.")

def fetch_detail_text_and_cpv(driver, detail_url):
    """Open detail page and extract visible main text, CPV codes, and submission deadline. Returns tuple (text, cpv_codes, submission_deadline)."""
    try:
        driver.get(detail_url)
        WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
        time.sleep(0.5)
    except Exception:
        return "", "", ""
    
    # Extract main text
    detail_text = ""
    for sel in [
        "main", "article", "#content", ".content", ".main", ".container",
        ".detail", ".panel-body", ".modul-detailansicht"
    ]:
        els = driver.find_elements(By.CSS_SELECTOR, sel)
        if els:
            t = els[0].get_attribute("innerText").strip()
            if len(t) > 50:
                detail_text = t
                break
    
    if not detail_text:
        try:
            detail_text = driver.find_element(By.TAG_NAME, "body").get_attribute("innerText").strip()
        except Exception:
            detail_text = ""
    
    # Extract CPV codes from the page
    cpv_codes = []
    submission_deadline = ""
    
    try:
        page_text = driver.find_element(By.TAG_NAME, "body").get_attribute("innerText")
        
        # Extract CPV codes
        cpv_pattern = re.compile(r'\b(\d{8}(?:-\d{1,3})?)\b')
        found_codes = cpv_pattern.findall(page_text)
        
        # Also look for CPV codes in specific elements
        cpv_selectors = [
            "//*[contains(text(), 'CPV') or contains(text(), 'cpv')]",
            "//*[contains(@class, 'cpv') or contains(@id, 'cpv')]",
            "//*[contains(text(), '72000000') or contains(text(), '79300000')]"
        ]
        
        for selector in cpv_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    text = element.get_attribute("innerText")
                    codes = cpv_pattern.findall(text)
                    found_codes.extend(codes)
            except Exception:
                continue
        
        # Remove duplicates and sort
        cpv_codes = sorted(list(set(found_codes)))
        
        # Extract submission deadline (Abgabefrist Angebot)
        deadline_patterns = [
            r'Abgabefrist\s+Angebot[:\s]*(.*?)(?=\n|$)',
            r'Angebotsfrist[:\s]*(.*?)(?=\n|$)',
            r'Bewerbungsfrist[:\s]*(.*?)(?=\n|$)',
            r'Submission\s+deadline[:\s]*(.*?)(?=\n|$)',
            r'Deadline[:\s]*(.*?)(?=\n|$)',
            r'Einreichungsfrist[:\s]*(.*?)(?=\n|$)',
            r'Termin[:\s]*(.*?)(?=\n|$)'
        ]
        
        for pattern in deadline_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE | re.DOTALL)
            if match:
                deadline_text = match.group(1).strip()
                # Clean up the deadline text
                deadline_text = re.sub(r'\s+', ' ', deadline_text)
                # Extract just the date part if there's extra text
                date_match = re.search(r'(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}[./-]\d{1,2}[./-]\d{1,2})', deadline_text)
                if date_match:
                    submission_deadline = date_match.group(1)
                else:
                    submission_deadline = deadline_text
                break
        
        # Also try XPath selectors for deadline
        if not submission_deadline:
            deadline_selectors = [
                "//*[contains(text(), 'Abgabefrist') or contains(text(), 'Angebotsfrist') or contains(text(), 'Bewerbungsfrist')]",
                "//*[contains(text(), 'Submission deadline') or contains(text(), 'Deadline')]",
                "//*[contains(text(), 'Einreichungsfrist') or contains(text(), 'Termin')]"
            ]
            
            for selector in deadline_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        text = element.get_attribute("innerText").strip()
                        if text and len(text) < 200:  # Reasonable length for a deadline
                            # Extract date from the text
                            date_match = re.search(r'(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}[./-]\d{1,2}[./-]\d{1,2})', text)
                            if date_match:
                                submission_deadline = date_match.group(1)
                                break
                    if submission_deadline:
                        break
                except Exception:
                    continue
        
    except Exception as e:
        print(f"   ⚠️  Error extracting details: {e}")
    
    return detail_text, cpv_codes, submission_deadline

# -------- Helper to find the 'last publication date' column --------
def find_last_publication_header(headers):
    """Try to identify the column that represents the last publication date.
    Looks for German/English variants in header labels.
    """
    candidates = []
    for h in headers:
        norm_h = _norm(h)
        if any(key in norm_h for key in ("veroffentlich", "veröffentlich", "publication", "last_pub")):
            candidates.append(h)
    # Prefer the most explicit English phrasing if multiple found
    for pref in ("Last_Publication", "Last_Published", "Letzte Veröffentlichung", "Zuletzt veröffentlicht"):
        if pref in candidates:
            return pref
    # Otherwise return the first match if any
    return candidates[0] if candidates else None

def _parse_date_str(s):
    """Parse common German/ISO date strings into a date object. Returns None on failure.
    Examples: 01.10.2025, 1.10.2025, 2025-10-01, 01/10/2025
    """
    s = (s or "").strip()
    if not s:
        return None
    s = re.sub(r"\s+", " ", s)
    fmts = [
        "%d.%m.%Y", "%d.%m.%y",
        "%Y-%m-%d",
        "%d/%m/%Y", "%d/%m/%y",
        "%d-%m-%Y", "%d-%m-%y",
    ]
    for fmt in fmts:
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except Exception:
            pass
    m = re.search(r"(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})", s)
    if m:
        d, mth, y = m.groups()
        y = y if len(y) == 4 else ("20" + y)
        try:
            return datetime.date(int(y), int(mth), int(d))
        except Exception:
            return None
    return None

# -------- Master crawl --------
def crawl_all_once(headless=HEADLESS, max_pages=MAX_PAGES, per_page_delay=PER_PAGE_DELAY):
    driver = make_driver(headless=headless)
    driver.get(START_URL)
    accept_cookies(driver)
    wait_for_table(driver)
    set_page_size_max(driver)

    # Build headers once (fastest for consistent table)
    headers = get_table_headers(driver)

    rows = []
    page = 1
    while True:
        print(f"📄 Page {page} …", end="", flush=True)
        page_rows = row_dicts_all_columns(driver, headers)
        rows.extend(page_rows)
        print(f" kept {len(page_rows)}")
        if max_pages and page >= max_pages:
            break
        time.sleep(per_page_delay)
        if not go_next(driver):
            break
        page += 1

    # Assign stable UID per row (based on detail_url, fallback to Bezeichnung)
    for idx, r in enumerate(rows, 1):
        base = r.get("detail_url") or r.get("Bezeichnung") or str(idx)
        r["uid"] = "EVG-" + uuid.uuid5(uuid.NAMESPACE_URL, base).hex[:12].upper()

    # Filter: keep only tenders with the very latest 'last publication date'
    last_pub_header = find_last_publication_header(headers)
    if last_pub_header:
        # parse dates
        dated = []
        for r in rows:
            d = _parse_date_str(r.get(last_pub_header, ""))
            if d:
                dated.append((d, r))
        if dated:
            max_date = max(d for d, _ in dated)
            rows = [r for d, r in dated if d == max_date]
            print(f"🧹 Keeping only rows with last publication date = {max_date.isoformat()} (kept {len(rows)})")
        else:
            print("⚠️ No parseable last publication dates found; no filtering applied.")
    else:
        print("⚠️ Could not find a 'last publication' column; no filtering applied.")

    # Enrich with detail page text, CPV codes, and submission deadline
    total = len(rows)
    for i, r in enumerate(rows, 1):
        durl = r.get("detail_url", "")
        if not durl:
            r["detail_content"] = ""
            r["CPV_Codes"] = ""
            r["Abgabefrist_Angebot"] = ""
            print(f"   ↪ [{i}/{total}] no detail_url")
            continue
        print(f"   ↪ [{i}/{total}] details: {durl}")
        detail_text, cpv_codes, submission_deadline = fetch_detail_text_and_cpv(driver, durl)
        r["detail_content"] = detail_text
        r["CPV_Codes"] = ", ".join(cpv_codes) if cpv_codes else ""
        r["Abgabefrist_Angebot"] = submission_deadline

    driver.quit()

    # Transform data to new column structure
    transformed_rows = []
    for r in rows:
        new_row = {}
        
        # Map columns to new names
        new_row["organization"] = r.get("Contracting_Authority", "")
        new_row["languages"] = "de"  # Fill with "de" for all rows
        new_row["submission_language"] = "de"  # Fill with "de" for all rows
        new_row["deadline"] = r.get("Abgabefrist_Angebot", "")
        new_row["cpv_codes"] = r.get("CPV_Codes", "")
        new_row["CPV_labels"] = ""  # Leave blank as requested
        new_row["title"] = r.get("Title", "")
        new_row["publication_id"] = r.get("uid", "")
        
        # Find publication date from various possible columns
        publication_date = ""
        # Debug: print available columns for first row
        if len(transformed_rows) == 0:
            print(f"🔍 Available columns in row: {list(r.keys())}")
        
        # Try multiple possible column names for publication date
        possible_pub_cols = [
            "veröffentlicht", "Veröffentlicht", "VERÖFFENTLICHT",  # The actual column name from the data
            "Publication_Date", "Last_Publication", "Last_Published", 
            "Veröffentlichungsdatum", "Letzte Veröffentlichung", "Zuletzt veröffentlicht",
            "Veröffentlichung", "Datum", "Date", "Published", "Publication"
        ]
        
        for col in possible_pub_cols:
            if col in r and r[col] and str(r[col]).strip():
                publication_date = str(r[col]).strip()
                if len(transformed_rows) == 0:
                    print(f"✅ Found publication date in column '{col}': {publication_date}")
                break
        
        # If still not found, try to find any column containing date-like patterns
        if not publication_date:
            for col, value in r.items():
                if value and isinstance(value, str):
                    # Look for date patterns in the value
                    if re.search(r'\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}[./-]\d{1,2}[./-]\d{1,2}', str(value)):
                        # Check if column name suggests it's a date
                        if any(word in col.lower() for word in ['date', 'datum', 'veröffentlich', 'publication', 'published']):
                            publication_date = str(value).strip()
                            if len(transformed_rows) == 0:
                                print(f"✅ Found date-like value in column '{col}': {publication_date}")
                            break
        
        new_row["publication_date"] = publication_date
        
        new_row["url"] = r.get("detail_url", "")
        new_row["description"] = r.get("detail_content", "")
        
        # Only keep the 11 specified columns - don't add any other columns
        transformed_rows.append(new_row)

    # Define exactly the 11 columns we want
    header = [
        "organization", "languages", "submission_language", "deadline", "cpv_codes", 
        "CPV_labels", "title", "publication_id", "publication_date", "url", "description"
    ]

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = f"evergabe_filtered_with_details_{ts}.csv"
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(transformed_rows)

    print(f"\n✅ Saved {len(transformed_rows)} rows to {out}")

if __name__ == "__main__":
    crawl_all_once()


