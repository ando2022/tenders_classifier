"""
Track the last fetch date to enable incremental data collection.
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

TRACKER_FILE = 'mvp/data/last_fetch.json'

def get_last_fetch_date():
    """Get the date of the last successful fetch"""
    if os.path.exists(TRACKER_FILE):
        try:
            with open(TRACKER_FILE, 'r') as f:
                data = json.load(f)
                return datetime.fromisoformat(data['last_fetch_date'])
        except:
            pass
    
    # Default: 7 days ago if no previous fetch
    return datetime.now() - timedelta(days=7)

def update_last_fetch_date(fetch_date=None):
    """Update the last fetch date"""
    if fetch_date is None:
        fetch_date = datetime.now()
    
    os.makedirs(os.path.dirname(TRACKER_FILE), exist_ok=True)
    
    data = {
        'last_fetch_date': fetch_date.isoformat(),
        'last_fetch_timestamp': datetime.now().isoformat(),
        'tenders_fetched': 0  # Will be updated after fetch
    }
    
    with open(TRACKER_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    return fetch_date

def get_fetch_date_range():
    """Get the date range for next fetch"""
    last_fetch = get_last_fetch_date()
    today = datetime.now()
    
    return {
        'start_date': last_fetch.strftime('%Y-%m-%d'),
        'end_date': today.strftime('%Y-%m-%d'),
        'last_fetch': last_fetch,
        'today': today,
        'days_since_last': (today - last_fetch).days
    }

def update_fetch_stats(tenders_count):
    """Update the statistics after a successful fetch"""
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, 'r') as f:
            data = json.load(f)
    else:
        data = {}
    
    data['tenders_fetched'] = tenders_count
    data['last_fetch_timestamp'] = datetime.now().isoformat()
    
    with open(TRACKER_FILE, 'w') as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    # Test the tracker
    date_range = get_fetch_date_range()
    print("📅 Fetch Date Range:")
    print(f"  Last fetch: {date_range['start_date']}")
    print(f"  Today: {date_range['end_date']}")
    print(f"  Days since last fetch: {date_range['days_since_last']}")

