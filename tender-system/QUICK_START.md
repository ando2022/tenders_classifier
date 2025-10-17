# 🚀 Quick Start Guide

## Setup (First Time)

```bash
# 1. Navigate to tender-system
cd tender-system

# 2. Run setup script
./setup.sh

# 3. Edit .env and add your OpenAI API key
nano .env  # or use your preferred editor
```

## Daily Usage

### View Dashboard

```bash
streamlit run ui/app.py
```

Then open: http://localhost:8501

### Run Scraper Manually

```bash
# Scrape last 7 days with classification
python main.py --scrape simap --days-back 7

# Scrape last 30 days (no classification - faster)
python main.py --scrape simap --days-back 30 --no-classify

# Check database stats
python main.py --stats
```

### Start Weekly Automation

```bash
# Run every Monday at 9:00 AM
python scheduler/weekly_scheduler.py

# Custom schedule (Wednesday at 2:30 PM)
python scheduler/weekly_scheduler.py --day wed --hour 14 --minute 30

# Test run immediately
python scheduler/weekly_scheduler.py --now
```

## Common Tasks

### Export Relevant Tenders

```python
from database.models import get_session, Tender
import pandas as pd

session = get_session()

# Get relevant tenders with high confidence
tenders = session.query(Tender).filter(
    Tender.is_relevant == True,
    Tender.confidence_score >= 75
).all()

# Convert to DataFrame
df = pd.DataFrame([{
    'Title': t.title,
    'Description': t.description,
    'Source': t.source,
    'Date': t.publication_date,
    'Confidence': t.confidence_score,
    'Reasoning': t.reasoning
} for t in tenders])

# Export to Excel
df.to_excel('relevant_tenders.xlsx', index=False)
```

### Classify Existing Unclassified Tenders

```python
from database.models import get_session, Tender
from classifier.llm_classifier import TenderClassifier
from datetime import datetime

session = get_session()
classifier = TenderClassifier()

# Get unclassified tenders
unclassified = session.query(Tender).filter(
    Tender.is_relevant.is_(None)
).all()

# Classify them
for tender in unclassified:
    is_relevant, confidence, reasoning = classifier.classify_tender(
        tender.title, 
        tender.description
    )
    
    tender.is_relevant = is_relevant
    tender.confidence_score = confidence
    tender.reasoning = reasoning
    tender.classified_at = datetime.now()

session.commit()
```

### Add New Scraper Source

1. Create scraper file: `scrapers/my_source_scraper.py`
2. Inherit from `BaseScraper`
3. Implement required methods
4. Add to `main.py` scrapers dict

See README.md for detailed example.

## Troubleshooting

**Problem:** `ModuleNotFoundError: No module named 'openai'`  
**Solution:** Run `pip install -r requirements.txt`

**Problem:** `ValueError: OPENAI_API_KEY environment variable not set`  
**Solution:** Add your API key to `.env` file

**Problem:** Database is locked  
**Solution:** Close any other programs accessing the database

**Problem:** Scraper times out  
**Solution:** Try with fewer days: `--days-back 3`

## Architecture Overview

```
[SIMAP API] → [Scraper] → [Database] → [Classifier] → [Database]
                                           ↓
                                    [Dashboard UI]
                                           ↑
                                    [Weekly Scheduler]
```

## Key Files

- `main.py` - Main orchestrator (CLI entry point)
- `ui/app.py` - Streamlit dashboard
- `database/models.py` - Database schema
- `scrapers/simap_scraper.py` - SIMAP data collection
- `classifier/llm_classifier.py` - LLM classification
- `scheduler/weekly_scheduler.py` - Automation

## Performance

- **Scraping**: ~1000 tenders in ~2-3 minutes
- **Classification**: ~10 tenders/minute (OpenAI API dependent)
- **Database**: Handles 10,000+ tenders efficiently

## Next Steps

1. ✅ Set up and test the system
2. ✅ Run initial scrape and classification
3. ✅ Review results in dashboard
4. 📅 Set up weekly automation
5. 🔄 Add more data sources as needed
6. 📊 Export and analyze relevant tenders

**Happy tender hunting! 🎯**

