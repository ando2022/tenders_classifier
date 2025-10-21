"""
Fast Evergabe scraper with Playwright
- Reads date range from time.config or parameters
- Filters by CPV codes from cpv_config.py
- Filters by keywords from cpv_config.py
- Gets complete descriptions, titles, deadlines, CPV codes
- Callable from Streamlit with proper date handling
"""

import csv
import time
import re
import json
import datetime
import unicodedata
import os
import sys
import uuid
from urllib.parse import quote
from collections import defaultdict
from playwright.sync_api import sync_playwright

# -------- Load CPV Config --------
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from cpv_config import OPTIMIZED_CPV_CODES, EVERGABE_KEYWORDS
    print(f"✅ Loaded {len(OPTIMIZED_CPV_CODES)} CPV codes")
    print(f"✅ Loaded {len(EVERGABE_KEYWORDS)} keywords")
except Exception as e:
    print(f"❌ Error loading cpv_config.py: {e}")
    print("⚠️  Continuing without CPV/keyword filtering")
    OPTIMIZED_CPV_CODES = []
    EVERGABE_KEYWORDS = []

# -------- Settings --------
BASE_URL = "https://www.evergabe-online.de/search.html"
HEADLESS = True
MAX_PAGES = None  # None = scrape all pages
PER_PAGE_DELAY = 0.15
TIME_CONFIG_FILE = "time.config"

def build_search_url(start_date, end_date, cpv_code=None):
    """Build Evergabe search URL with date filters and optional CPV code."""
    # Convert to datetime for formatting
    if start_date and isinstance(start_date, datetime.date):
        start_dt = datetime.datetime.combine(start_date, datetime.time(0, 0, 0))
    elif start_date:
        start_dt = _parse_date_str(str(start_date))
        if start_dt:
            start_dt = datetime.datetime.combine(start_dt, datetime.time(0, 0, 0))
    else:
        start_dt = None
    
    if end_date and isinstance(end_date, datetime.date):
        end_dt = datetime.datetime.combine(end_date, datetime.time(23, 59, 59))
    elif end_date:
        end_dt = _parse_date_str(str(end_date))
        if end_dt:
            end_dt = datetime.datetime.combine(end_dt, datetime.time(23, 59, 59))
    else:
        end_dt = None
    
    # Build URL parameters
    params = []
    
    if start_dt and end_dt:
        # Format: "Day Mon DD HH:MM:SS TZ YYYY" (German format with timezone)
        start_formatted = start_dt.strftime("%a %b %d %H:%M:%S CET %Y")
        end_formatted = end_dt.strftime("%a %b %d %H:%M:%S CET %Y")
        
        params.append(f"publishedFrom={quote(start_formatted)}")
        params.append(f"publishedTo={quote(end_formatted)}")
        params.append("publishDateRange=USER_SELECTION")
    
    if cpv_code:
        # Add CPV code filter (format: 12345678-9)
        params.append(f"cpv={cpv_code}-9")
    
    if params:
        return f"{BASE_URL}?{'&'.join(params)}"
    else:
        return BASE_URL + "?4"

# -------- Load Time Config --------
def load_time_config(config_file=TIME_CONFIG_FILE):
    """Load date range from time.config JSON file."""
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            start_date = config.get('from')
            end_date = config.get('to')
            mode = config.get('mode', 'absolute')
            
            print(f"📋 Loaded time.config:")
            print(f"   Mode: {mode}")
            print(f"   From: {start_date}")
            print(f"   To: {end_date}")
            
            return start_date, end_date
        else:
            print(f"⚠️  {config_file} not found, proceeding without date filter")
            return None, None
    except Exception as e:
        print(f"⚠️  Error reading {config_file}: {e}")
        return None, None

# -------- Helper Functions --------
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
        "veröffentlicht": "Published",
        "Verfahrensart": "Procedure_Type",
        "Auftragsart": "Contract_Type",
    }
    return translations.get(german_name, german_name)

def _parse_date_str(s):
    """Parse common German/ISO date strings into a date object."""
    s = (s or "").strip()
    if not s:
        return None
    
    # Remove any time component
    s = re.sub(r'\s+\d{1,2}:\d{2}.*$', '', s)
    s = re.sub(r"\s+", " ", s).strip()
    
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
    
    # Try regex extraction
    m = re.search(r"(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})", s)
    if m:
        d, mth, y = m.groups()
        y = y if len(y) == 4 else ("20" + y)
        try:
            return datetime.date(int(y), int(mth), int(d))
        except Exception:
            return None
    return None

# -------- Playwright Functions --------
def accept_cookies(page):
    """Accept cookies if dialog appears."""
    labels = ["Alle akzeptieren", "Akzeptieren", "Zustimmen", "Einverstanden", "OK"]
    for label in labels:
        try:
            page.click(f"button:has-text('{label}')", timeout=3000)
            time.sleep(0.2)
            break
        except:
            pass

def wait_for_table(page, timeout=25000):
    """Wait for table to load."""
    page.wait_for_selector("table tbody tr", timeout=timeout)

def set_page_size_max(page):
    """Set page size to maximum available."""
    try:
        # Try to find and click the largest page size option
        for size in ["200", "100", "Alle"]:
            try:
                page.click(f"button:has-text('{size}')", timeout=2000)
                time.sleep(1)
                return
            except:
                pass
        
        # Try select dropdown
        try:
            select = page.locator("select").first
            if select.is_visible():
                options = select.locator("option").all()
                if options:
                    # Select last option (usually largest)
                    last_option = options[-1]
                    value = last_option.get_attribute("value")
                    select.select_option(value)
                    time.sleep(1)
        except:
            pass
    except Exception as e:
        print(f"⚠️  Could not set page size: {e}")

# -------- Table Extraction --------
def unique_headers(headers):
    counts = defaultdict(int)
    out = []
    for h in headers:
        key = h or "col"
        counts[key] += 1
        out.append(key if counts[key] == 1 else f"{key}_{counts[key]}")
    return out

def get_table_headers(page):
    """Extract table headers using JavaScript."""
    headers = page.evaluate("""
        () => {
            const ths = document.querySelectorAll('table thead th');
            return Array.from(ths).map(th => 
                th.innerText.trim() || th.title || th.getAttribute('aria-label') || ''
            );
        }
    """)
    
    if not any(h for h in headers):
        # Fallback to first row data-title
        try:
            headers = page.evaluate("""
                () => {
                    const tds = document.querySelectorAll('table tbody tr:first-child td');
                    return Array.from(tds).map(td => 
                        td.getAttribute('data-title') || td.getAttribute('aria-label') || ''
                    );
                }
            """)
        except:
            pass
    
    if not headers:
        # Count columns and create generic headers
        try:
            col_count = page.evaluate("""
                () => document.querySelectorAll('table tbody tr:first-child td').length
            """)
            headers = [f"col_{i+1}" for i in range(col_count)]
        except:
            headers = []
    
    translated_headers = [translate_column_name(h.strip()) for h in headers]
    return unique_headers(translated_headers)

def extract_table_rows(page, headers):
    """Extract all rows from table using JavaScript for speed."""
    rows = page.evaluate("""
        (headers) => {
            const table = document.querySelector('table');
            const trs = table.querySelectorAll('tbody tr');
            const rows = [];
            
            for (const tr of trs) {
                const tds = tr.querySelectorAll('td');
                if (tds.length === 0) continue;
                
                const row = {};
                
                for (let i = 0; i < tds.length; i++) {
                    const key = headers[i] || `col_${i+1}`;
                    const text = tds[i].innerText.trim();
                    row[key] = text;
                    
                    // Capture first link in cell
                    const link = tds[i].querySelector('a[href]');
                    if (link) {
                        row[key + '_link'] = link.href;
                        if (i === 0 && !row.detail_url) {
                            row.detail_url = link.href;
                        }
                    }
                }
                
                rows.push(row);
            }
            
            return rows;
        }
    """, headers)
    
    return rows

def go_next_page(page):
    """Navigate to next page."""
    try:
        next_link = page.locator("a[rel='next']").first
        
        # Check if disabled
        if next_link.get_attribute("aria-disabled") == "true":
            return False
        
        # Get first cell text before clicking
        old_text = page.locator("table tbody tr td").first.inner_text()
        
        # Click next
        next_link.click()
        
        # Wait for content to change
        page.wait_for_function(
            f"document.querySelector('table tbody tr td').innerText !== '{old_text}'",
            timeout=15000
        )
        
        return True
    except:
        return False

# -------- Detail Page Extraction --------
def fetch_detail_info(page, detail_url):
    """Extract description, CPV codes, and submission deadline from detail page."""
    try:
        page.goto(detail_url, wait_until='load', timeout=25000)
        time.sleep(0.5)
    except Exception as e:
        print(f"⚠️  Failed to load {detail_url}: {e}")
        return "", "", ""
    
    # Extract main text/description
    detail_text = ""
    selectors = ["main", "article", "#content", ".content", ".main", ".container",
                 ".detail", ".panel-body", ".modul-detailansicht"]
    
    for sel in selectors:
        try:
            element = page.locator(sel).first
            if element.is_visible():
                t = element.inner_text().strip()
                if len(t) > 50:
                    detail_text = t
                    break
        except:
            pass
    
    if not detail_text:
        try:
            detail_text = page.locator("body").inner_text().strip()
        except:
            detail_text = ""
    
    # Extract CPV codes and deadline
    cpv_codes = []
    submission_deadline = ""
    
    try:
        page_text = page.locator("body").inner_text()
        
        # Extract CPV codes (format: 12345678 or 12345678-9)
        cpv_pattern = re.compile(r'\b(\d{8}(?:-\d{1,3})?)\b')
        found_codes = cpv_pattern.findall(page_text)
        cpv_codes = sorted(list(set(found_codes)))
        
        # Extract submission deadline
        deadline_patterns = [
            r'Abgabefrist\s+Angebot[:\s]*(.*?)(?=\n|$)',
            r'Angebotsfrist[:\s]*(.*?)(?=\n|$)',
            r'Bewerbungsfrist[:\s]*(.*?)(?=\n|$)',
            r'Einreichungsfrist[:\s]*(.*?)(?=\n|$)',
        ]
        
        for pattern in deadline_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE | re.DOTALL)
            if match:
                deadline_text = match.group(1).strip()
                deadline_text = re.sub(r'\s+', ' ', deadline_text)
                
                # Extract date
                date_match = re.search(
                    r'(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{4}[./-]\d{1,2}[./-]\d{1,2})', 
                    deadline_text
                )
                if date_match:
                    submission_deadline = date_match.group(1)
                    break
    
    except Exception as e:
        print(f"   ⚠️  Error extracting details: {e}")
    
    return detail_text, cpv_codes, submission_deadline

def find_publication_date_column(headers):
    """Find the column containing publication date."""
    candidates = [
        "Published", "Publication_Date", "Last_Publication", "Last_Published",
        "Veröffentlichungsdatum", "Letzte Veröffentlichung"
    ]
    
    for candidate in candidates:
        if candidate in headers:
            return candidate
    
    # Fallback: find any column with "pub" or "veröffentlich"
    for h in headers:
        if "pub" in h.lower() or "veröffentlich" in h.lower():
            return h
    
    return None

# -------- Keyword Filtering --------
def matches_keywords(row, keywords):
    """Check if row matches any of the keywords."""
    if not keywords:
        return True  # No filtering if no keywords
    
    # Combine all text fields for matching
    text_fields = []
    for key, value in row.items():
        if isinstance(value, str) and not key.endswith('_link'):
            text_fields.append(value)
    
    combined_text = " | ".join(text_fields)
    normalized = _norm(combined_text)
    
    # Check if any keyword matches
    for keyword in keywords:
        if _norm(str(keyword)) in normalized:
            return True
    
    return False

# -------- Main Crawl Function --------
def crawl_evergabe(start_date=None, end_date=None, headless=HEADLESS, max_pages=MAX_PAGES):
    """
    Scrape Evergabe tenders with Playwright for speed.
    Filters by CPV codes and keywords from cpv_config.py
    If no dates provided, attempts to load from time.config file.
    
    Args:
        start_date: datetime.date, str (DD.MM.YYYY or YYYY-MM-DD), or None
        end_date: datetime.date, str (DD.MM.YYYY or YYYY-MM-DD), or None
        headless: bool - run browser in headless mode
        max_pages: int or None - maximum pages to scrape per CPV (None = all)
    
    Returns:
        str: path to output CSV file
    """
    
    # If no dates provided, try to load from config file
    if start_date is None and end_date is None:
        config_start, config_end = load_time_config()
        if config_start:
            start_date = config_start
        if config_end:
            end_date = config_end
    
    # Parse date parameters - handle datetime.date objects from Streamlit
    if isinstance(start_date, datetime.date) and not isinstance(start_date, datetime.datetime):
        # Already a date object, keep as is
        pass
    elif isinstance(start_date, str):
        start_date = _parse_date_str(start_date)
    
    if isinstance(end_date, datetime.date) and not isinstance(end_date, datetime.datetime):
        # Already a date object, keep as is
        pass
    elif isinstance(end_date, str):
        end_date = _parse_date_str(end_date)
    
    print("="*60)
    print("🚀 EVERGABE SCRAPER - CPV + KEYWORD FILTERING")
    print("="*60)
    if start_date:
        print(f"📅 Start date: {start_date}")
    if end_date:
        print(f"📅 End date: {end_date}")
    print(f"🔎 CPV codes: {len(OPTIMIZED_CPV_CODES)}")
    print(f"🔎 Keywords: {len(EVERGABE_KEYWORDS)}")
    print("="*60)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
        )
        
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='de-DE'
        )
        
        page = context.new_page()
        
        # Add script to hide webdriver
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        try:
            all_rows = []
            seen_urls = set()
            headers = []  # Initialize headers
            pub_date_col = None  # Initialize pub_date_col
            
            # If we have CPV codes, search by each one
            if OPTIMIZED_CPV_CODES:
                print(f"\n🔎 Searching by {len(OPTIMIZED_CPV_CODES)} CPV codes...")
                
                for idx, cpv_code in enumerate(OPTIMIZED_CPV_CODES, 1):
                    search_url = build_search_url(start_date, end_date, cpv_code)
                    print(f"\n[{idx}/{len(OPTIMIZED_CPV_CODES)}] CPV {cpv_code}...", end="", flush=True)
                    
                    # Navigate to search page with CPV filter
                    page.goto(search_url, wait_until='load', timeout=30000)
                    
                    if idx == 1:
                        accept_cookies(page)
                    
                    try:
                        wait_for_table(page, timeout=10000)
                        
                        if idx == 1:
                            set_page_size_max(page)
                    except:
                        print(" no results")
                        continue
                    
                    # Get headers (only once, on first successful search)
                    if not headers:
                        headers = get_table_headers(page)
                        pub_date_col = find_publication_date_column(headers)
                        print(f"\n   📊 Columns: {headers}")
                        if pub_date_col:
                            print(f"   📅 Date column: '{pub_date_col}'")
                    
                    # Scrape pages for this CPV
                    cpv_rows = []
                    page_num = 1
                    
                    while True:
                        page_rows = extract_table_rows(page, headers)
                        
                        # Add CPV code to each row
                        for row in page_rows:
                            row['matched_cpv'] = cpv_code
                        
                        cpv_rows.extend(page_rows)
                        
                        if max_pages and page_num >= max_pages:
                            break
                        
                        if not go_next_page(page):
                            break
                        
                        page_num += 1
                        time.sleep(PER_PAGE_DELAY)
                    
                    # Deduplicate and add to results
                    new_count = 0
                    for row in cpv_rows:
                        detail_url = row.get('detail_url', '')
                        if detail_url and detail_url not in seen_urls:
                            all_rows.append(row)
                            seen_urls.add(detail_url)
                            new_count += 1
                        elif detail_url in seen_urls:
                            # Add CPV to existing row
                            for existing in all_rows:
                                if existing.get('detail_url') == detail_url:
                                    existing_cpvs = existing.get('matched_cpv', '')
                                    if cpv_code not in existing_cpvs:
                                        existing['matched_cpv'] = f"{existing_cpvs}, {cpv_code}"
                                    break
                    
                    print(f" {len(cpv_rows)} rows ({new_count} new)")
                    time.sleep(0.2)  # Be nice to server
            
            else:
                # No CPV codes - search without CPV filter
                print("\n🌐 Searching without CPV filter...")
                search_url = build_search_url(start_date, end_date)
                
                page.goto(search_url, wait_until='load', timeout=30000)
                accept_cookies(page)
                wait_for_table(page)
                set_page_size_max(page)
                
                headers = get_table_headers(page)
                pub_date_col = find_publication_date_column(headers)
                print(f"📊 Found {len(headers)} columns")
                if pub_date_col:
                    print(f"📅 Date column: '{pub_date_col}'")
                
                page_num = 1
                while True:
                    print(f"📄 Page {page_num}...", end="", flush=True)
                    page_rows = extract_table_rows(page, headers)
                    all_rows.extend(page_rows)
                    print(f" extracted {len(page_rows)} rows")
                    
                    if max_pages and page_num >= max_pages:
                        break
                    
                    time.sleep(PER_PAGE_DELAY)
                    
                    if not go_next_page(page):
                        print("✅ Reached last page")
                        break
                    
                    page_num += 1
            
            print(f"\n📊 Total unique rows: {len(all_rows)}")
            
            # Apply keyword filtering
            if EVERGABE_KEYWORDS:
                print(f"\n🔍 Applying keyword filter ({len(EVERGABE_KEYWORDS)} keywords)...")
                filtered_rows = []
                for row in all_rows:
                    if matches_keywords(row, EVERGABE_KEYWORDS):
                        filtered_rows.append(row)
                
                print(f"✅ Kept {len(filtered_rows)}/{len(all_rows)} rows matching keywords")
                all_rows = filtered_rows
            
            # Assign unique IDs
            for idx, r in enumerate(all_rows, 1):
                base = r.get("detail_url") or r.get("Title") or str(idx)
                r["uid"] = "EVG-" + uuid.uuid5(uuid.NAMESPACE_URL, base).hex[:12].upper()
            
            # Enrich with detail page information
            total = len(all_rows)
            print(f"\n🔍 Fetching detail pages for {total} tenders...")
            
            for i, r in enumerate(all_rows, 1):
                durl = r.get("detail_url", "")
                if not durl:
                    r["detail_content"] = ""
                    r["CPV_Codes"] = r.get("matched_cpv", "")
                    r["Deadline"] = ""
                    print(f"   [{i}/{total}] No detail URL")
                    continue
                
                print(f"   [{i}/{total}] {durl}")
                detail_text, cpv_codes, deadline = fetch_detail_info(page, durl)
                r["detail_content"] = detail_text
                
                # Combine CPV codes from search and detail page
                all_cpvs = set()
                if r.get("matched_cpv"):
                    all_cpvs.update(r["matched_cpv"].split(", "))
                if cpv_codes:
                    all_cpvs.update(cpv_codes)
                
                r["CPV_Codes"] = ", ".join(sorted(all_cpvs))
                r["Deadline"] = deadline
            
        finally:
            browser.close()
    
    # Transform to final output format
    transformed_rows = []
    for r in all_rows:
        new_row = {
            "organization": r.get("Contracting_Authority", ""),
            "languages": "de",
            "submission_language": "de",
            "deadline": r.get("Deadline", ""),
            "cpv_codes": r.get("CPV_Codes", ""),
            "CPV_labels": "",
            "title": r.get("Title", ""),
            "publication_id": r.get("uid", ""),
            "publication_date": r.get(pub_date_col, "") if pub_date_col else "",
            "url": r.get("detail_url", ""),
            "description": r.get("detail_content", "")
        }
        transformed_rows.append(new_row)
    
    print(f"\n✅ Scraped {len(transformed_rows)} tenders")
    print("\n📊 Summary:")
    print(f"   CPV codes searched: {len(OPTIMIZED_CPV_CODES) if OPTIMIZED_CPV_CODES else 'None'}")
    # Save to CSV in current working directory
    header = [
        "organization", "languages", "submission_language", "deadline", "cpv_codes",
        "CPV_labels", "title", "publication_id", "publication_date", "url", "description"
    ]
    
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = os.path.join(os.getcwd(), f"evergabe_filtered_{ts}.csv")
    
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(transformed_rows)
    
    print(f"\n✅ Saved {len(transformed_rows)} rows to {os.path.basename(out)}")
    print("\n📊 Summary:")
    print(f"   CPV codes searched: {len(OPTIMIZED_CPV_CODES) if OPTIMIZED_CPV_CODES else 'None'}")
    print(f"   Keywords applied: {len(EVERGABE_KEYWORDS) if EVERGABE_KEYWORDS else 'None'}")
    print(f"   Final tenders: {len(transformed_rows)}")
    
    return out


if __name__ == "__main__":
    # Automatically loads dates from time.config if present
    # Or you can manually specify dates:
    # crawl_evergabe(start_date="01.01.2025", end_date="31.12.2025")
    
    crawl_evergabe(
        headless=True,
        max_pages=None  # Set to None to scrape all pages, or a number for testing
    )