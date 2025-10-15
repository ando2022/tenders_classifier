"""
SIMAP scraper (script version) exported from Simap_scraper_damlina.ipynb

- Queries prod SIMAP project search with filters
- Paginates using lastItem token
- Fetches publication details per (project_id, publication_id)
- Merges summary and detail JSON
- Saves timestamped CSV
"""

import datetime
import json
import sys
import time
from typing import Dict, Any, List, Tuple, Optional
import re

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


BASE_URL = "https://prod.simap.ch/api/publications/v2/project/project-search"
DETAIL_URL_TMPL = "https://prod.simap.ch/api/publications/v1/project/{project_id}/publication-details/{publication_id}"

# Default query params (align with the notebook)
BASE_PARAMS = {
    "processTypes": ["open"],              # Offenes Verfahren
    "pubTypes": ["call_for_bids"],        # Ausschreibung
    "projectSubTypes": ["service"],       # Dienstleistung
    "cpvCodes": [
        "72000000","79300000","73100000","79311400","72314000",
        "79416000","72320000","98300000","79310000","79000000","79311410"
    ],
    "pageSize": 100,
    "newestPublicationFrom": "2025-10-01",
    "newestPublicationUntil": "2025-10-15",
    # Date window will be injected dynamically in main() for the last 7 days
}


def make_session() -> requests.Session:
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


def fetch_all_projects(session: requests.Session, base_params: Dict[str, Any]) -> List[Dict[str, Any]]:
    all_results: List[Dict[str, Any]] = []
    seen_ids = set()
    last_item: Optional[str] = None
    page = 1

    while True:
        params = dict(base_params)
        if last_item:
            params["lastItem"] = last_item

        r = session.get(BASE_URL, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()

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

        page += 1
        time.sleep(0.2)

    return all_results


def fetch_details_for_projects(session: requests.Session, projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    detailed_data: List[Dict[str, Any]] = []
    # dedupe on (id, publicationId)
    seen_pairs = set()
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
            print(f"Request failed for {project_id}/{publication_id}: {e}")
            continue
        if idx % 50 == 0:
            print(f"… details fetched: {idx}")
        time.sleep(0.05)
    return detailed_data


def to_dataframe(records: List[Dict[str, Any]]):
    try:
        import pandas as pd
        return pd.json_normalize(records, sep=".")
    except ImportError:
        # Minimal fallback writer without pandas
        return None


def save_csv_with_pandas(projects: List[Dict[str, Any]], details: List[Dict[str, Any]]):
    import pandas as pd

    df_projects = pd.json_normalize(projects, sep=".")
    df_details = pd.json_normalize(details, sep=".")

    # Merge on (id == project_id, publicationId == publication_id)
    merged = df_projects.drop_duplicates(subset=["id", "publicationId"]).merge(
        df_details,
        left_on=["id", "publicationId"],
        right_on=["project_id", "publication_id"],
        how="left",
    )

    # ---------- Curate only requested fields (per user spec) ----------
    def strip_html(val):
        try:
            from bs4 import BeautifulSoup
            if isinstance(val, str) and ("<" in val and ">" in val):
                return BeautifulSoup(val, "lxml").get_text(" ", strip=True)
        except Exception:
            pass
        return val if isinstance(val, str) else val

    def pick_lang(ld):
        # title/orderDescription are often language dicts like { 'de': ..., 'fr': ..., 'en': ... }
        if isinstance(ld, dict):
            for key in ("de", "fr", "en"):
                v = ld.get(key)
                if v:
                    return v
        return ld

    def pick_lang_by_creation_language(ld, creation_lang):
        """Pick language variant based on base.creationLanguage"""
        if not isinstance(ld, dict) or not creation_lang:
            return pick_lang(ld)  # fallback to original logic
        
        # Map creation language to our language keys
        lang_map = {
            "de": "de", "german": "de", "deutsch": "de",
            "fr": "fr", "french": "fr", "français": "fr", "francais": "fr",
            "en": "en", "english": "en", "englisch": "en",
            "it": "it", "italian": "it", "italienisch": "it", "italiano": "it"
        }
        
        target_key = lang_map.get(creation_lang.lower())
        if target_key and target_key in ld:
            return ld[target_key]
        
        # Fallback to original priority if creation language not found
        return pick_lang(ld)

    def list_langs(ld):
        if isinstance(ld, dict):
            langs = [k for k in ("de","fr","it","en") if ld.get(k)]
            if langs:
                return ", ".join(langs)
        return ""

    def as_lang_dict(val):
        # normalize to {de/en/fr/it: str}
        if isinstance(val, dict):
            out = {}
            for k in ("de","en","fr","it"):
                v = val.get(k)
                if isinstance(v, str) and v.strip():
                    out[k] = strip_html(v)
            return out
        elif isinstance(val, str):
            # unknown language -> put under 'de' by default to keep a place
            return {"de": strip_html(val)}
        return {}

    def extract_order_description(proc):
        if isinstance(proc, dict):
            od = proc.get("orderDescription")
            od = pick_lang(od)
            od = strip_html(od)
            return od
        return None

    def extract_title(t):
        return strip_html(pick_lang(t))

    def find_in_dates(dates_obj, *key_parts):
        # attempt to find a date field whose key contains all parts (case-insensitive)
        if isinstance(dates_obj, dict):
            for k, v in dates_obj.items():
                nk = k.lower()
                if all(part in nk for part in key_parts):
                    return v
        return None

    def extract_deadline_submission(dates_obj):
        # try several plausible keys
        for parts in (
            ("submission", "end"), ("offer", "submission"), ("tender", "submission"),
            ("offer", "deadline"), ("submission", "deadline"),
        ):
            v = find_in_dates(dates_obj, *parts)
            if v:
                return v
        return None

    def extract_deadline_additional_info(dates_obj):
        for parts in (("qna", "end"), ("questions", "end"), ("questions", "deadline"), ("clarifications", "deadline")):
            v = find_in_dates(dates_obj, *parts)
            if v:
                return v
        return None

    def extract_procurement_value(proc):
        # search common spots for value + currency
        amount = None
        currency = None
        def walk(obj, parent_key=""):
            nonlocal amount, currency
            if isinstance(obj, dict):
                for k, v in obj.items():
                    nk = k.lower()
                    if amount is None and ("value" in nk or "amount" in nk or "sum" in nk):
                        # take numeric or string convertible
                        if isinstance(v, (int, float)):
                            amount = v
                        elif isinstance(v, str):
                            m = re.search(r"[-+]?[0-9]*\.?[0-9]+", v.replace(" ", ""))
                            if m:
                                try:
                                    amount = float(m.group(0))
                                except Exception:
                                    pass
                    if currency is None and ("currency" in nk or nk in ("cur",)) and isinstance(v, str):
                        currency = v
                    walk(v, nk)
            elif isinstance(obj, list):
                for it in obj:
                    walk(it, parent_key)
        if isinstance(proc, dict):
            walk(proc)
        return amount, currency

    def extract_eligibility(criteria_obj):
        # criteria may be list or dict; collect names/texts
        texts = []
        def walk(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, (dict, list)):
                        walk(v)
                    else:
                        nk = k.lower()
                        if any(t in nk for t in ("eligibility","requirement","qualificat","criterion","criteria","text","description","nachweis")):
                            if isinstance(v, str) and v.strip():
                                texts.append(strip_html(v))
            elif isinstance(obj, list):
                for it in obj:
                    walk(it)
        walk(criteria_obj)
        return "; ".join(dict.fromkeys([t for t in texts if t]))[:4000]

    def extract_cpv(row_dict):
        # Try to find a code and label in common places (lots, procurement)
        code = None
        label = None
        def walk(obj):
            nonlocal code, label
            if isinstance(obj, dict):
                for k, v in obj.items():
                    lk = k.lower()
                    if code is None and ("cpv" in lk and ("code" in lk or lk == "cpv")):
                        if isinstance(v, str):
                            code = v
                    if label is None and ("cpv" in lk and "label" in lk):
                        if isinstance(v, str):
                            label = v
                    walk(v)
            elif isinstance(obj, list):
                for it in obj:
                    walk(it)
        walk({"lots": row_dict.get("lots")})
        walk({"procurement": row_dict.get("procurement")})
        return code, label

    def clean_text_chars(s):
        if not isinstance(s, str):
            return s
        # Remove control chars except tab/newline; normalize spaces
        s = re.sub(r"[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]", "", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    curated_rows = []
    for _, row in merged.iterrows():
        # id_x comes from merged id_x (left id)
        id_x_val = row.get("id_x") if "id_x" in merged.columns else row.get("id")
        
        # Extract title from nested structure - try multiple paths
        title_obj = row.get("title") or row.get("title.de") or row.get("title.en") or row.get("title.fr") or row.get("title.it")
        if not title_obj and "title" in merged.columns:
            title_obj = row.get("title")
        
        # Extract title using creation language
        title_ld = as_lang_dict(title_obj)
        title_one = clean_text_chars(pick_lang_by_creation_language(title_ld, row.get("base.creationLanguage") or row.get("base.creationLanguage")))

        # Publication identifiers/dates
        publication_id = row.get("publicationId") or row.get("publication_id")
        publication_date = row.get("publicationDate")

        # Base creation language
        base_creation_language = (row.get("base.creationLanguage")
                                  if "base.creationLanguage" in merged.columns else
                                  (row.get("base") or {}).get("creationLanguage") if isinstance(row.get("base"), dict) else "")
        base_creation_language = clean_text_chars(base_creation_language or "")

        # Extract order description from nested procurement structure
        procurement_obj = row.get("procurement")
        order_desc_obj = None
        if isinstance(procurement_obj, dict):
            order_desc_obj = procurement_obj.get("orderDescription")
        elif isinstance(procurement_obj, str):
            order_desc_obj = procurement_obj
        
        # Try alternative paths for order description
        if not order_desc_obj:
            order_desc_obj = (row.get("procurement.orderDescription") or 
                            row.get("procurement.orderDescription.de") or 
                            row.get("procurement.orderDescription.en") or 
                            row.get("procurement.orderDescription.fr") or 
                            row.get("procurement.orderDescription.it"))
        
        order_ld = as_lang_dict(order_desc_obj)
        order_one = clean_text_chars(pick_lang_by_creation_language(order_ld, base_creation_language))

        # Extract deadline using the exact field names from archive
        offer_deadline = (row.get("dates.offerDeadline") or 
                         row.get("dates_offerDeadline") or 
                         row.get("offerDeadline"))
        offer_deadline = clean_text_chars(offer_deadline or "")

        # CPV - try multiple extraction paths
        cpv_code, cpv_label = extract_cpv(row)
        if not cpv_code:
            cpv_code = (row.get("procurement.cpvCode.code") or 
                       row.get("procurement.cpvCode") or 
                       row.get("cpvCode.code") or 
                       row.get("cpvCode"))
        if not cpv_label:
            cpv_label = (row.get("procurement.cpvCode.label") or 
                        row.get("procurement.cpvCode.label.de") or 
                        row.get("cpvCode.label") or 
                        row.get("cpvCode.label.de"))

        # Construct URL from id_x (same as archive)
        url = f"https://www.simap.ch/en/project-detail/{id_x_val}" if id_x_val else ""

        curated_rows.append({
            "title": title_one,
            "publication_id": publication_id,
            "publicationDate": publication_date,
            "base.creationLanguage": base_creation_language,
            "procurement.orderDescription": order_one,
            "procurement.cpvCode.code": cpv_code,
            "procurement.cpvCode.label": cpv_label,
            "dates.offerDeadline": offer_deadline,
            "url": url,
        })

    # Ensure requested column order exactly as specified - 9 columns (removed id_x)
    final_cols = [
        "title",
        "publication_id",
        "publicationDate",
        "base.creationLanguage",
        "procurement.orderDescription",
        "procurement.cpvCode.code",
        "procurement.cpvCode.label",
        "dates.offerDeadline",
        "url",
    ]
    curated_df = pd.DataFrame(curated_rows)
    for c in final_cols:
        if c not in curated_df.columns:
            curated_df[c] = ""
    curated_df = curated_df[final_cols]

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = f"simap_export_{ts}.csv"
    curated_df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"✅ Saved {len(curated_df)} rows to {out}")


def save_csv_without_pandas(projects: List[Dict[str, Any]], details: List[Dict[str, Any]]):
    import csv
    # Build map for details by (project_id, publication_id)
    key_to_detail: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for d in details:
        key = (d.get("project_id", ""), d.get("publication_id", ""))
        key_to_detail[key] = d

    # Compose merged records
    merged: List[Dict[str, Any]] = []
    seen_pairs = set()
    for p in projects:
        pair = (p.get("id", ""), p.get("publicationId", ""))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        row = dict(p)
        det = key_to_detail.get(pair)
        if det:
            for k, v in det.items():
                row[f"detail.{k}"] = v
        merged.append(row)

    # Collect headers
    headers = set()
    for r in merged:
        headers.update(r.keys())
    headers = sorted(headers)

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = f"simap_results_{ts}.csv"
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in merged:
            # Serialize non-scalars to JSON strings for CSV safety
            safe = {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v) for k, v in r.items()}
            w.writerow(safe)
    print(f"✅ Saved {len(merged)} rows to {out}")


def main():
    session = make_session()
    # Restrict to last 7 days (inclusive)
    today = datetime.date.today()
    start = today - datetime.timedelta(days=7)
    params = dict(BASE_PARAMS)
    params["pubDateFrom"] = start.strftime("%Y-%m-%d")
    params["pubDateTo"] = today.strftime("%Y-%m-%d")

    print(f"Fetching SIMAP projects for window {params['pubDateFrom']} .. {params['pubDateTo']} …")
    projects = fetch_all_projects(session, params)
    print(f"Got {len(projects)} project rows")

    print("Fetching details … this can take a few minutes …")
    details = fetch_details_for_projects(session, projects)
    print(f"Got {len(details)} details rows")

    try:
        import pandas as pd  # noqa: F401
        save_csv_with_pandas(projects, details)
    except Exception:
        print("pandas not available; writing CSV without pandas")
        save_csv_without_pandas(projects, details)


if __name__ == "__main__":
    main()

