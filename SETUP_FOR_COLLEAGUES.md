# 🚀 Setup Guide for Colleagues

**Works from ANY directory where you clone the repo!**

---

## 📥 **Step 1: Clone the Repository**

```bash
# Clone from GitLab
git clone git@gitlab.propulsion-home.ch:datascience/bootcamp/final-projects/ds-2025-08/bak-economics.git

# Navigate to project
cd bak-economics
```

---

## 🐍 **Step 2: Set Up Python Environment**

```bash
# Create virtual environment (recommended)
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r tender-system/requirements.txt
pip install pandas openpyxl
```

---

## 🔑 **Step 3: Configure Environment Variables**

Create a `.env` file in the project root:

```bash
# Create .env file
cat > .env << 'EOF'
# OpenAI API Key (required for LLM classification)
OPENAI_API_KEY=your_openai_api_key_here

# Database configuration (optional - defaults to SQLite)
USE_POSTGRES=false
# POSTGRES_URL=postgresql://user:pass@localhost/tenders

# SQLite path (relative to project root)
SQLITE_PATH=mvp/database/tenders.db

# Model configuration
OPENAI_MODEL=gpt-4o-mini
TEMPERATURE=0.1
EOF

# Edit the .env file with your actual API key
nano .env  # or use your preferred editor
```

---

## 🗄️ **Step 4: Initialize Database**

```bash
# Initialize the database
python mvp/consolidated_schema.py
```

---

## 🧪 **Step 5: Test the Setup**

```bash
# Test 1: Run scrapers (get fresh data)
python scraper/01_calls_scrapers.py

# Test 2: Consolidate data
python mvp/01_consolidate_scraped_data.py

# Test 3: View consolidated data
python -c "
import pandas as pd
df = pd.read_csv('mvp/data/consolidated_tenders_*.csv', encoding='utf-8')
print(f'Total tenders: {len(df)}')
print(df.head())
"

# Test 4: Emergency classifier
cd tender-system
python manage_emergency_classifier.py stats
cd ..
```

---

## 🌐 **Step 6: Launch the Interface**

```bash
# Option 1: View static demo
open tender-system/demo.html

# Option 2: Launch Streamlit (requires streamlit installed)
cd tender-system
streamlit run ui/app.py
```

---

## 📂 **Project Structure**

All paths are **relative to the project root** (`bak-economics/`):

```
bak-economics/              # ← Your current directory
├── mvp/                    # MVP implementation
│   ├── consolidated_schema.py
│   ├── 01_consolidate_scraped_data.py
│   └── data/               # Generated data files
│
├── scraper/                # Data collection
│   ├── 01_calls_scrapers.py
│   ├── simap/              # Swiss tenders
│   └── eu-tender/          # EU tenders
│
├── tender-system/          # Complete system
│   ├── database/
│   ├── classifier/
│   ├── ui/
│   └── demo.html
│
├── tenders-llm/            # 92% accuracy model
│   ├── prompts/
│   └── data/
│
└── .env                    # Your configuration (create this!)
```

---

## ⚙️ **Configuration Options**

### **Database**

By default, uses SQLite (no setup needed):
```bash
# SQLite (default)
SQLITE_PATH=mvp/database/tenders.db
```

To use PostgreSQL:
```bash
# PostgreSQL
USE_POSTGRES=true
POSTGRES_URL=postgresql://username:password@localhost:5432/tenders_db
```

### **API Keys**

Required only if you want to use LLM classification:
```bash
OPENAI_API_KEY=sk-...
```

Without API key, the **emergency classifier** (cosine similarity) still works!

---

## 🎯 **Quick Start Workflow**

```bash
# 1. Navigate to project
cd bak-economics

# 2. Activate virtual environment (if using one)
source venv/bin/activate

# 3. Run the complete pipeline
python scraper/01_calls_scrapers.py         # Collect data
python mvp/01_consolidate_scraped_data.py   # Consolidate

# 4. View results
ls -lh mvp/data/                             # See output files
```

---

## 🐛 **Troubleshooting**

### **Issue: "No module named 'pandas'"**
```bash
pip install pandas openpyxl scikit-learn
```

### **Issue: "Database file not found"**
```bash
# Create directory
mkdir -p mvp/database

# Initialize database
python mvp/consolidated_schema.py
```

### **Issue: "OPENAI_API_KEY not set"**
```bash
# Either set in .env file:
echo "OPENAI_API_KEY=sk-..." >> .env

# OR use emergency classifier (no API key needed):
cd tender-system
python manage_emergency_classifier.py test
```

### **Issue: Paths not working**
```bash
# Make sure you're in the project root:
pwd
# Should end with: /bak-economics

# If not, navigate there:
cd path/to/bak-economics
```

---

## ✅ **Success Checklist**

- [ ] Repository cloned
- [ ] Python environment set up
- [ ] `.env` file created (with or without API key)
- [ ] Database initialized
- [ ] Scrapers running successfully
- [ ] Consolidation working
- [ ] Data visible in `mvp/data/`
- [ ] Demo opens in browser

---

## 📚 **Next Steps**

Once setup is complete, read:

1. **`STEP_BY_STEP_GUIDE.md`** - Complete walkthrough
2. **`mvp/VISUAL_OVERVIEW.md`** - System architecture
3. **`mvp/MVP_STATUS.md`** - Current status
4. **`tender-system/START_HERE.md`** - Full system guide

---

## 💬 **Questions?**

All paths are **relative to the project root**. No matter where you clone the repo, it will work!

**Common commands pattern:**
```bash
cd bak-economics           # Always start here
python mvp/...             # Relative path
python scraper/...         # Relative path
cd tender-system && ...    # Change dir when needed
```

**Happy coding! 🎉**

