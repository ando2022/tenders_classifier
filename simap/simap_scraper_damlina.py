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
    # Optional window
    # "pubDateFrom": "2025-01-01",
    # "pubDateTo":   "2025-12-31",
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

    # ---------- Curate only requested fields ----------
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

    curated_rows = []
    for _, row in merged.iterrows():
        order_desc = extract_order_description(row.get("procurement"))
        ttitle = extract_title(row.get("title"))
        buyer = row.get("procOfficeName")
        # dates may exist in detail payload
        dd = row.get("dates")
        deadline_sub = extract_deadline_submission(dd)
        deadline_add = extract_deadline_additional_info(dd)
        val, cur = extract_procurement_value(row.get("procurement"))

        curated_rows.append({
            "id": row.get("id"),
            "project_id": row.get("project_id"),
            "publication_date": row.get("publicationDate"),
            "buyer_official_name": buyer,
            "deadline_submission": deadline_sub,
            "deadline_additional_information": deadline_add,
            "procurement_value": val,
            "procurement_currency": cur,
            "title": ttitle,
            "order_description": order_desc,
        })

    curated_df = pd.DataFrame(curated_rows)

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = f"simap_curated_{ts}.csv"
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
    print("Fetching SIMAP projects …")
    projects = fetch_all_projects(session, BASE_PARAMS)
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

