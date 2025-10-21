"""
SIMAP Scraper - FIXED VERSION with Streamlit wrapper
Works correctly with title, description, and date filtering
"""

import datetime
import json
import os
import sys
import time
import re
from typing import Dict, Any, List, Tuple, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Import CPV configuration
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
try:
    from cpv_config import OPTIMIZED_CPV_CODES
except ImportError:
    print("⚠️  Warning: cpv_config not found, using empty CPV list")
    OPTIMIZED_CPV_CODES = []

# API endpoints
BASE_URL = "https://prod.simap.ch/api/publications/v2/project/project-search"
DETAIL_URL_TMPL = "https://prod.simap.ch/api/publications/v1/project/{project_id}/publication-details/{publication_id}"

# Base query parameters (NO date params here - we'll add them later)
BASE_PARAMS = {
    "processTypes": ["open"],
    "pubTypes": ["call_for_bids"],
    "projectSubTypes": ["service"],
    "cpvCodes": OPTIMIZED_CPV_CODES,
    "pageSize": 100,
    "newestPubTypes": ["tender"],
}


def resolve_date_window() -> Tuple[str, str]:
    """Resolve date window from env vars or config"""
    env_from = os.environ.get('SIMAP_PUB_DATE_FROM', '').strip()
    env_to = os.environ.get('SIMAP_PUB_DATE_TO', '').strip()
    
    if env_from and env_to:
        print(f"📅 Using dates from environment: {env_from} to {env_to}")
        return env_from, env_to
    
    config_paths = [
        os.path.join(os.path.dirname(__file__), "..", "..", "time.config"),
        os.path.join(os.path.dirname(__file__), "..", "time.config"),
        os.path.join(os.getcwd(), "time.config"),
    ]
    
    for cfg_path in config_paths:
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                
                mode = str(cfg.get("mode", "relative")).lower()
                
                if mode == "absolute":
                    from_date = str(cfg.get("from", "")).strip()
                    to_date = str(cfg.get("to", "")).strip()
                    if from_date and to_date:
                        print(f"📅 Using absolute dates from config: {from_date} to {to_date}")
                        return from_date, to_date
                
                elif mode == "relative":
                    days = int(cfg.get("days", 7))
                    today = datetime.date.today()
                    start = today - datetime.timedelta(days=days)
                    from_date = start.strftime("%Y-%m-%d")
                    to_date = today.strftime("%Y-%m-%d")
                    print(f"📅 Using relative dates: last {days} days ({from_date} to {to_date})")
                    return from_date, to_date
            except Exception as e:
                print(f"⚠️  Error reading {cfg_path}: {e}")
                continue
    
    # Default
    today = datetime.date.today()
    start = today - datetime.timedelta(days=7)
    from_date = start.strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")
    print(f"📅 Using default: last 7 days ({from_date} to {to_date})")
    return from_date, to_date


def make_session() -> requests.Session:
    """Create session with retry logic"""
    session = requests.Session()
    session.headers.update({"accept": "application/json"})
    retries = Retry(
        total=6, connect=6, read=6, status=6,
        backoff_factor=0.7,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


def fetch_all_projects(session: requests.Session, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Fetch all project summaries using pagination"""
    all_results = []
    seen_ids = set()
    last_item = None
    page = 1

    print("\n📊 Fetching projects...", end="", flush=True)
    
    while True:
        current_params = dict(params)
        if last_item:
            current_params["lastItem"] = last_item

        try:
            r = session.get(BASE_URL, params=current_params, timeout=30)
            r.raise_for_status()
            data = r.json()
        except requests.RequestException as e:
            print(f"\n⚠️  Request failed on page {page}: {e}")
            break

        projects = data.get("projects", [])
        if not projects:
            break

        for p in projects:
            pid = p.get("id")
            if pid and pid not in seen_ids:
                seen_ids.add(pid)
                all_results.append(p)

        paging = data.get("pagination") or data.get("paging") or {}
        last_item = paging.get("lastItem")
        
        if not last_item:
            break

        if page % 5 == 0:
            print(f".", end="", flush=True)
        
        page += 1
        time.sleep(0.2)

    print(f" Done! ({len(all_results)} projects)")
    return all_results


def fetch_details_for_projects(session: requests.Session, projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Fetch detailed data for each project"""
    detailed_data = []
    seen_pairs = set()
    total = len(projects)
    
    print(f"\n🔍 Fetching details for {total} projects...", end="", flush=True)
    
    for idx, p in enumerate(projects, 1):
        project_id = p.get("id")
        publication_id = p.get("publicationId")
        
        if not project_id or not publication_id:
            continue
        
        pair = (project_id, publication_id)
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)

        url = DETAIL_URL_TMPL.format(project_id=project_id, publication_id=publication_id)
        
        try:
            resp = session.get(url, timeout=40)
            resp.raise_for_status()
            data = resp.json()
            data["project_id"] = project_id
            data["publication_id"] = publication_id
            detailed_data.append(data)
        except requests.RequestException as e:
            print(f"\n⚠️  Failed {project_id}/{publication_id}: {e}")
            continue
        
        if idx % 50 == 0:
            print(f" {idx}/{total}", end="", flush=True)
        
        time.sleep(0.05)
    
    print(f" Done! ({len(detailed_data)} details)")
    return detailed_data


def clean_text(text: Any) -> str:
    """Clean text - remove HTML and control characters"""
    if not isinstance(text, str):
        return str(text) if text else ""
    
    # Strip HTML
    try:
        from bs4 import BeautifulSoup
        if "<" in text and ">" in text:
            text = BeautifulSoup(text, "lxml").get_text(" ", strip=True)
    except:
        pass
    
    # Remove control characters
    text = re.sub(r"[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_language_value(data: Any, creation_lang: str = None) -> str:
    """Extract value from language dict"""
    if isinstance(data, str):
        return clean_text(data)
    
    if not isinstance(data, dict):
        return ""
    
    # Try creation language first
    if creation_lang:
        lang_map = {
            "de": "de", "german": "de", "deutsch": "de",
            "fr": "fr", "french": "fr", "français": "fr",
            "en": "en", "english": "en",
            "it": "it", "italian": "it", "italiano": "it"
        }
        key = lang_map.get(creation_lang.lower())
        if key and key in data and data[key]:
            return clean_text(data[key])
    
    # Fallback to priority order
    for key in ("de", "fr", "en", "it"):
        if key in data and data[key]:
            return clean_text(data[key])
    
    return ""


def curate_data_direct(projects: List[Dict], details: List[Dict]) -> List[Dict]:
    """
    Curate data WITHOUT pandas - direct dict processing
    This avoids the flattening issues
    """
    # Create lookup for details
    detail_map = {}
    for d in details:
        key = (d.get("project_id"), d.get("publication_id"))
        detail_map[key] = d
    
    curated_rows = []
    
    for project in projects:
        project_id = project.get("id")
        publication_id = project.get("publicationId")
        
        # Get corresponding detail
        detail = detail_map.get((project_id, publication_id), {})
        
        # Extract creation language
        base = detail.get("base", {})
        creation_lang = base.get("creationLanguage", "")
        
        # TITLE - from project summary
        title_dict = project.get("title", {})
        title = extract_language_value(title_dict, creation_lang)
        
        # DESCRIPTION - from detail under procurement.orderDescription
        procurement = detail.get("procurement", {})
        desc_dict = procurement.get("orderDescription", {})
        description = extract_language_value(desc_dict, creation_lang)
        
        # ORGANIZATION - from detail under project-info.procOfficeAddress.name
        project_info = detail.get("project-info", {})
        proc_office = project_info.get("procOfficeAddress", {})
        org_dict = proc_office.get("name", {})
        organization = extract_language_value(org_dict, creation_lang)
        
        # PUBLICATION DATE
        publication_date = project.get("publicationDate", "")
        
        # DEADLINE - from detail under dates.offerDeadline
        dates = detail.get("dates", {})
        deadline = dates.get("offerDeadline", "")
        if deadline:
            deadline = clean_text(deadline)
        
        # CPV CODE
        cpv_obj = procurement.get("cpvCode", {})
        cpv_code = cpv_obj.get("code", "") if isinstance(cpv_obj, dict) else ""
        
        # CPV LABEL - get in creation language
        cpv_label = ""
        if isinstance(cpv_obj, dict):
            label_dict = cpv_obj.get("label", {})
            cpv_label = extract_language_value(label_dict, creation_lang)
        
        # SUBMISSION LANGUAGES - from project-info.offerLanguages
        offer_langs = project_info.get("offerLanguages", [])
        if isinstance(offer_langs, list):
            submission_lang = ", ".join(clean_text(str(l)) for l in offer_langs if l)
        else:
            submission_lang = clean_text(str(offer_langs)) if offer_langs else ""
        
        # URL
        url = f"https://www.simap.ch/en/project-detail/{project_id}" if project_id else ""
        
        # Build row
        curated_rows.append({
            "organization": organization,
            "languages": clean_text(creation_lang),
            "submission_language": submission_lang,
            "deadline": deadline,
            "cpv_codes": cpv_code,  # Changed to cpv_codes (plural)
            "CPV_labels": cpv_label,  # Changed to CPV_labels
            "title": title,
            "publication_id": publication_id or "",
            "publication_date": publication_date,
            "url": url,
            "description": description,  # Changed to lowercase description
        })
    
    return curated_rows


def save_results(curated_rows: List[Dict]) -> str:
    """Save to CSV"""
    try:
        import pandas as pd
    except ImportError:
        print("❌ pandas required: pip install pandas")
        sys.exit(1)
    
    columns = [
        "organization",
        "languages",
        "submission_language",
        "deadline",
        "cpv_codes",
        "CPV_labels",
        "title",
        "publication_id",
        "publication_date",
        "url",
        "description",
    ]
    
    df = pd.DataFrame(curated_rows)
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    df = df[columns]
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.getcwd()
    output_path = os.path.join(output_dir, f"simap_export_{timestamp}.csv")
    
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    
    return output_path


def filter_by_date(projects: List[Dict], from_date: str, to_date: str) -> List[Dict]:
    """
    CLIENT-SIDE date filtering since API doesn't respect date params properly
    """
    from_dt = datetime.datetime.strptime(from_date, "%Y-%m-%d").date()
    to_dt = datetime.datetime.strptime(to_date, "%Y-%m-%d").date()
    
    filtered = []
    for p in projects:
        pub_date_str = p.get("publicationDate", "")
        if not pub_date_str:
            continue
        
        try:
            # Parse date - might be YYYY-MM-DD or DD.MM.YYYY
            if '.' in pub_date_str:
                pub_dt = datetime.datetime.strptime(pub_date_str, "%d.%m.%Y").date()
            else:
                pub_dt = datetime.datetime.strptime(pub_date_str, "%Y-%m-%d").date()
            
            # Check if within range
            if from_dt <= pub_dt <= to_dt:
                filtered.append(p)
        except:
            # If can't parse, include it
            filtered.append(p)
    
    return filtered


def scrape_simap_with_dates(from_date: str, to_date: str) -> str:
    """
    Main scraping logic - returns path to CSV file
    This is the function called by Streamlit
    """
    print("=" * 80)
    print("SIMAP SCRAPER")
    print("=" * 80)
    print(f"Started: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n")
    
    # Prepare params
    params = dict(BASE_PARAMS)
    params["pubDateFrom"] = from_date
    params["pubDateTo"] = to_date
    
    # Create session
    session = make_session()
    
    # Fetch data
    print(f"\n📊 Querying SIMAP API: {from_date} to {to_date}")
    projects = fetch_all_projects(session, params)
    
    if not projects:
        print("\n⚠️  No projects found")
        raise ValueError("No projects found for the specified date range")
    
    # CLIENT-SIDE FILTERING
    print(f"\n🔍 Filtering by date range...")
    projects_before = len(projects)
    projects = filter_by_date(projects, from_date, to_date)
    projects_after = len(projects)
    
    if projects_before != projects_after:
        print(f"   Filtered: {projects_before} → {projects_after} projects")
    
    if not projects:
        print("\n⚠️  No projects within the specified date range")
        raise ValueError("No projects within the specified date range")
    
    # Fetch details
    details = fetch_details_for_projects(session, projects)
    
    # Process WITHOUT pandas flattening
    print("\n📊 Processing data...")
    curated_rows = curate_data_direct(projects, details)
    
    # Save
    output_path = save_results(curated_rows)
    
    # Summary
    print("\n" + "=" * 80)
    print("✅ SCRAPING COMPLETE")
    print("=" * 80)
    print(f"Records saved:   {len(curated_rows)}")
    print(f"Output file:     {os.path.basename(output_path)}")
    print("=" * 80)
    
    return output_path


def simap_main(start_date=None, end_date=None) -> str:
    """
    Wrapper function for Streamlit integration
    
    Args:
        start_date: datetime.date, str (YYYY-MM-DD), or None
        end_date: datetime.date, str (YYYY-MM-DD), or None
    
    Returns:
        str: Path to the generated CSV file
    """
    # Convert dates to strings if needed
    if start_date is None or end_date is None:
        from_date, to_date = resolve_date_window()
    else:
        # Handle datetime.date objects from Streamlit
        if isinstance(start_date, datetime.date):
            from_date = start_date.strftime("%Y-%m-%d")
        else:
            from_date = str(start_date)
        
        if isinstance(end_date, datetime.date):
            to_date = end_date.strftime("%Y-%m-%d")
        else:
            to_date = str(end_date)
    
    return scrape_simap_with_dates(from_date, to_date)


def main():
    """Main execution for command-line usage"""
    try:
        output_path = simap_main()
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())