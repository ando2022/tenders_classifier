# 🎯 Tender Management System

Automated tender collection, classification, and management system for BAK Economics.

## 🌟 Features

- **📥 Multi-Source Scraping**: Collect tenders from SIMAP (and future sources)
- **🤖 AI Classification**: 92% accuracy LLM-based tender relevance classification
- **💾 Database Storage**: SQLite database for tender data and metadata
- **⏰ Weekly Automation**: Scheduled weekly scraping and classification
- **📊 Web Dashboard**: Simple Streamlit UI for viewing and managing tenders
- **🔍 Search & Filter**: Find relevant tenders quickly

## 🏗️ Architecture

```
tender-system/
├── database/           # Database models and SQLAlchemy setup
│   ├── models.py      # Tender and ScraperLog models
│   └── tenders.db     # SQLite database (auto-created)
├── scrapers/          # Data collection modules
│   ├── base_scraper.py    # Abstract base class
│   └── simap_scraper.py   # SIMAP implementation
├── classifier/        # LLM classification
│   └── llm_classifier.py  # OpenAI-based classifier (92% accuracy)
├── scheduler/         # Automation
│   └── weekly_scheduler.py  # APScheduler-based weekly runs
├── ui/               # User interface
│   └── app.py        # Streamlit dashboard
├── main.py           # Main orchestrator
└── requirements.txt  # Dependencies
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd tender-system
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:

```bash
# OpenAI API Key (required for classification)
OPENAI_API_KEY=your_api_key_here

# Optional: Override defaults
OPENAI_MODEL=gpt-4o-mini
TEMPERATURE=0.1
DB_PATH=tender-system/database/tenders.db
```

### 3. Initialize Database

```bash
python main.py --init-db
```

### 4. Run Your First Scrape

```bash
# Scrape SIMAP for last 7 days with classification
python main.py --scrape simap --days-back 7
```

### 5. Launch Dashboard

```bash
streamlit run ui/app.py
```

Open http://localhost:8501 in your browser!

## 📋 Usage

### Command Line Interface

```bash
# Initialize database
python main.py --init-db

# Scrape tenders
python main.py --scrape simap --days-back 7

# Scrape without classification (faster)
python main.py --scrape simap --days-back 7 --no-classify

# Show database statistics
python main.py --stats
```

### Weekly Automation

```bash
# Start scheduler (runs every Monday at 9:00 AM)
python scheduler/weekly_scheduler.py

# Custom schedule (every Wednesday at 14:30)
python scheduler/weekly_scheduler.py --day wed --hour 14 --minute 30

# Run immediately (for testing)
python scheduler/weekly_scheduler.py --now
```

### Web Dashboard

```bash
streamlit run ui/app.py
```

Features:
- 📊 Dashboard with statistics
- 📋 View all tenders with filters
- ✅ Browse relevant tenders by confidence
- 🔍 Search functionality
- 🚀 Run scrapers from UI
- 📈 Analytics and trends

## 🔧 System Components

### 1. Database Schema

**Tenders Table:**
- `tender_id`: Unique external ID
- `source`: Data source (simap, evergabe, etc.)
- `title`, `description`: Tender content
- `publication_date`, `deadline`: Important dates
- `is_relevant`, `confidence_score`, `reasoning`: LLM classification
- `cpv_codes`, `contracting_authority`: Metadata
- `raw_data`: Original API response (JSON)

**ScraperLog Table:**
- Track scraper runs, success/errors, duration

### 2. Scrapers

**Base Scraper Interface:**
- `fetch_tenders()`: Get list of tenders
- `fetch_tender_details()`: Get full details
- `normalize_tender()`: Convert to standard format

**SIMAP Scraper:**
- Fetches from Swiss public procurement platform
- Filters by CPV codes, service type
- Enriches with full tender descriptions
- Robust error handling and retries

### 3. Classifier

**LLM Classifier:**
- Uses BAK Economics' 92% accuracy balanced prompt
- OpenAI GPT-4o-mini model
- Structured JSON output
- Returns: prediction (Yes/No), confidence (0-100), reasoning

### 4. Orchestrator

**Main Pipeline:**
1. Fetch tenders from source
2. Enrich with details
3. Classify with LLM
4. Store in database
5. Log the run

## 📊 Database Queries

```python
from database.models import get_session, Tender

session = get_session()

# Get all relevant tenders
relevant = session.query(Tender).filter_by(is_relevant=True).all()

# Get tenders above 80% confidence
high_confidence = session.query(Tender).filter(
    Tender.is_relevant == True,
    Tender.confidence_score >= 80
).all()

# Get recent tenders
from datetime import datetime, timedelta
recent = session.query(Tender).filter(
    Tender.created_at >= datetime.now() - timedelta(days=7)
).all()
```

## 🔄 Adding New Data Sources

1. Create new scraper class inheriting from `BaseScraper`:

```python
from scrapers.base_scraper import BaseScraper

class MyNewScraper(BaseScraper):
    def __init__(self):
        super().__init__("my_source_name")
    
    def fetch_tenders(self, date_from=None, date_to=None):
        # Implement scraping logic
        pass
    
    def fetch_tender_details(self, tender_id):
        # Implement detail fetching
        pass
    
    def normalize_tender(self, raw_data):
        # Convert to standard format
        return {
            'tender_id': ...,
            'source': self.source_name,
            'title': ...,
            # ... other fields
        }
```

2. Register in `main.py`:

```python
self.scrapers = {
    'simap': SimapScraper(),
    'my_source': MyNewScraper()  # Add here
}
```

## 🎯 Classification Model

Uses the **v2 Balanced Prompt** with 92% accuracy:
- Precision: 95%
- Recall: 87%
- Optimized for economic research tenders

Prompt location: `tenders-llm/prompts/classify_tender_balanced.md`

## 📈 Monitoring

**View Stats:**
```bash
python main.py --stats
```

**Check Scraper Logs:**
```sql
SELECT * FROM scraper_logs ORDER BY run_date DESC LIMIT 10;
```

**Dashboard Analytics:**
- Open Streamlit UI → Analytics tab

## 🐛 Troubleshooting

**Database locked error:**
- Close any other sessions using the DB
- Use `--init-db` to reset if needed

**Classification errors:**
- Check `OPENAI_API_KEY` in `.env`
- Verify API quota/credits

**Scraper timeout:**
- Increase timeout in scraper config
- Check internet connection

## 🚀 Production Deployment

### Option 1: Cron Job (Linux/Mac)

```bash
# Add to crontab: Run every Monday at 9 AM
0 9 * * 1 cd /path/to/tender-system && python main.py --scrape simap --days-back 7
```

### Option 2: Systemd Service (Linux)

Create `/etc/systemd/system/tender-scheduler.service`:

```ini
[Unit]
Description=Tender Scraping Scheduler
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/tender-system
ExecStart=/usr/bin/python3 scheduler/weekly_scheduler.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable tender-scheduler
sudo systemctl start tender-scheduler
```

### Option 3: Docker (Coming Soon)

## 📝 License

Internal BAK Economics tool - All rights reserved

## 👥 Contributors

- Ana Dobson - System Architecture & LLM Integration
- Damlina - SIMAP Scraper Implementation
- Team BAK Economics

---

**Questions?** Contact the BAK Economics Data Science team

