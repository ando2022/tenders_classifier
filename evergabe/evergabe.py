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
MAX_PAGES = None               # set an int (e.g., 5) for quick testing
PER_PAGE_DELAY = 0.15          # seconds; be polite but fast

# -------- Keywords (DE/FR/IT/EN) --------
RAW_INCLUDE = [
    # Study / Studie
    "study","studie","étude","etude","studio",
    # Analysis / Analyse
    "analysis","analyse","analisi",
    # Economy / Wirtschaft / Ökonomie
    "economy","economics","wirtschaft","ökonomie","economie","economia",
    # Benchmarking
    "benchmark","benchmarking",
    # Wirtschaftsberatung / consulting
    "wirtschaftsberatung","consulting","conseil","consulenza",
    # CPV & categories
    "72000000","79300000",
    "it-dienste",
    "beratung, software-entwicklung, internet und hilfestellung",
    "markt- und wirtschaftsforschung","umfragen und statistiken",
    # Dienstleistung / services
    "dienstleistung","service","prestation","prestazione",
    # Ausschreibung / tender
    "ausschreibung","appel d'offres","appels d'offres","gara","procurement",
    # Offenes Verfahren / open procedure
    "offenes verfahren","procédure ouverte","procedure ouverte","procedura aperta",
    # BKS / Bundesamt für Statistik / OFS
    "bks","bundesamt für statistik","office fédéral de la statistique",
    "office federal de la statistique","ufficio federale di statistica",
    "federal statistical office","ofs","bfs",
    # SECO
    "seco","staatssekretariat für wirtschaft",
    "secrétariat d'état à l'économie","secretariat d'etat a l'economie",
    "segretariato di stato dell'economia",
    # Cantons / regions
    "kanton zürich","kanton zuerich","canton de zurich","cantone zurigo",
    "kanton luzern","canton de lucerne","cantone lucerna",
    "kanton","canton","cantone",
    "region","regionen","région","regione",
    # Bundesamt für.. (generic)
    "bundesamt für","bundesamt fuer",
    # BBL
    "bundesamt für bauten und logistik","bundesamt fuer bauten und logistik","bbl",
    # Index
    "index","verbraucherindex","price index","indice des prix","indice dei prezzi",
    # Wirtschaftsforschung
    "wirtschaftsforschung","economic research","recherche économique",
    "recherche economique","ricerca economica",
]

RAW_EXCLUDE = [
    "construction","bau","bâtiment","batiment","costruzioni",
    "health care","gesundheit","santé","sante","sanità","sanita",
    "transport","verkehr","transports","trasporti",
    "mobility","mobilität","mobilite","mobilité","mobilita",
    "sport",
    "culture","kultur","cultura",
    "street","strasse","straße","rue","strada",
    "infrastructure","infrastruktur","infrastruttura",
    "process","prozess","processus","processo",
    "it","informatik","informatique","informatica",
]

def _norm(s: str) -> str:
    """Lowercase, strip accents, collapse whitespace."""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", s.strip().lower())

INCLUDE = {_norm(k) for k in RAW_INCLUDE if k.strip()}
EXCLUDE = {_norm(k) for k in RAW_EXCLUDE if k.strip()}

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
    return unique_headers([h.strip() for h in headers])

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

def fetch_detail_text(driver, detail_url):
    """Open detail page and extract visible main text. Returns string (may be empty)."""
    try:
        driver.get(detail_url)
        WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
        time.sleep(0.5)
    except Exception:
        return ""
    # Try likely main content containers first
    for sel in [
        "main", "article", "#content", ".content", ".main", ".container",
        ".detail", ".panel-body", ".modul-detailansicht"
    ]:
        els = driver.find_elements(By.CSS_SELECTOR, sel)
        if els:
            t = els[0].get_attribute("innerText").strip()
            if len(t) > 50:
                return t
    try:
        return driver.find_element(By.TAG_NAME, "body").get_attribute("innerText").strip()
    except Exception:
        return ""

# -------- Helper to find the 'last publication date' column --------
def find_last_publication_header(headers):
    """Try to identify the column that represents the last publication date.
    Looks for German/English variants in header labels.
    """
    candidates = []
    for h in headers:
        norm_h = _norm(h)
        if any(key in norm_h for key in ("veroffentlich", "veröffentlich", "publication")):
            candidates.append(h)
    # Prefer the most explicit German phrasing if multiple found
    for pref in ("Letzte Veröffentlichung", "Zuletzt veröffentlicht"):
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
    # Pagination disabled: collect only the first page
    print(f"📄 Page {page} …", end="", flush=True)
    page_rows = row_dicts_all_columns(driver, headers)
    rows.extend(page_rows)
    print(f" kept {len(page_rows)}")

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

    # Enrich with detail page text (no PDFs)
    total = len(rows)
    for i, r in enumerate(rows, 1):
        durl = r.get("detail_url", "")
        if not durl:
            r["detail_content"] = ""
            print(f"   ↪ [{i}/{total}] no detail_url")
            continue
        print(f"   ↪ [{i}/{total}] details: {durl}")
        r["detail_content"] = fetch_detail_text(driver, durl)

    driver.quit()

    # Save CSV
    all_keys = set(headers + [f"{h}_link" for h in headers] + ["uid","matched_keywords","detail_url","detail_content"])
    for r in rows:
        all_keys.update(r.keys())

    preferred = [
        "uid","Bezeichnung","Geschäftszeichen","Vergabestelle","Ort der Leistung",
        "matched_keywords","detail_url","detail_content"
    ]
    header = [k for k in preferred if k in all_keys] + [k for k in sorted(all_keys) if k not in preferred]

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = f"evergabe_filtered_with_details_{ts}.csv"
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows)

    print(f"\n✅ Saved {len(rows)} rows to {out}")

if __name__ == "__main__":
    crawl_all_once()


