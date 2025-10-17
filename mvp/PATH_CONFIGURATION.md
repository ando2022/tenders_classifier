# 📂 Path Configuration - Universal Setup

**All paths are relative to the project root. Works anywhere you clone the repo!**

---

## ✅ **How Paths Are Configured**

### **Project Root = bak-economics/**

No matter where you clone the repository, all paths are relative to this root:

```
YOUR_MACHINE/
└── any/directory/structure/
    └── bak-economics/          ← Project root (this is your reference point)
        ├── mvp/
        ├── scraper/
        ├── tender-system/
        └── .env
```

---

## 🔧 **Code Implementation**

### **1. Database Path (SQLite)**

```python
# mvp/consolidated_schema.py

# ✅ CORRECT: Relative to file location
DB_PATH = os.getenv('SQLITE_PATH', 
    os.path.abspath(os.path.join(os.path.dirname(__file__), 'database/tenders.db'))
)

# This resolves to: mvp/database/tenders.db (from project root)
```

**How it works:**
- `__file__` = current script location
- `os.path.dirname(__file__)` = directory containing the script
- Joins with `database/tenders.db`
- Result: Always correct, regardless of clone location!

---

### **2. Scraper Paths**

```python
# mvp/01_consolidate_scraped_data.py

# ✅ CORRECT: Relative paths from project root
simap_dir = 'scraper/scraper/simap'
eu_dir = 'scraper/scraper/eu-tender'

# Works when you run: python mvp/01_consolidate_scraped_data.py
# From project root: bak-economics/
```

---

### **3. Output Paths**

```python
# mvp/01_consolidate_scraped_data.py

# ✅ CORRECT: Creates directory if needed
output_dir = 'mvp/data'
os.makedirs(output_dir, exist_ok=True)

# Output file with timestamp
output_file = f'{output_dir}/consolidated_tenders_{timestamp}.csv'
```

---

## 🚀 **Running from Different Locations**

### **Scenario 1: Running from Project Root**

```bash
# You are here: bak-economics/
pwd  # → /home/user/projects/bak-economics

python mvp/01_consolidate_scraped_data.py    # ✅ Works
python scraper/01_calls_scrapers.py          # ✅ Works
```

### **Scenario 2: Running from MVP Directory**

```bash
# You are here: bak-economics/mvp/
pwd  # → /home/user/projects/bak-economics/mvp

cd ..                                         # Go back to root
python mvp/01_consolidate_scraped_data.py    # ✅ Works
```

### **Scenario 3: After Fresh Clone**

```bash
# Clone anywhere
git clone git@gitlab.propulsion-home.ch:...

# Navigate to root
cd bak-economics

# Everything works!
python mvp/01_consolidate_scraped_data.py    # ✅ Works
python scraper/01_calls_scrapers.py          # ✅ Works
```

---

## 📝 **Environment Variables (.env)**

Create `.env` in **project root**:

```bash
# .env (in bak-economics/)

# ✅ Relative path (from project root)
SQLITE_PATH=mvp/database/tenders.db

# ✅ Or use default (no config needed)
# Defaults to: mvp/database/tenders.db
```

---

## 🎯 **Path Resolution Examples**

### **Example 1: Consolidation Script**

```python
# When you run: python mvp/01_consolidate_scraped_data.py

# Current working directory: /any/path/bak-economics/
# Script location: /any/path/bak-economics/mvp/01_consolidate_scraped_data.py

# Paths used:
simap_files = 'scraper/scraper/simap/*.csv'
# Resolves to: /any/path/bak-economics/scraper/scraper/simap/*.csv ✅

output_file = 'mvp/data/consolidated.csv'
# Resolves to: /any/path/bak-economics/mvp/data/consolidated.csv ✅
```

### **Example 2: Database Schema**

```python
# When you run: python mvp/consolidated_schema.py

# __file__ = /any/path/bak-economics/mvp/consolidated_schema.py
# os.path.dirname(__file__) = /any/path/bak-economics/mvp/

DB_PATH = os.path.join(os.path.dirname(__file__), 'database/tenders.db')
# Result: /any/path/bak-economics/mvp/database/tenders.db ✅
```

---

## ✅ **Verification Checklist**

Run this to verify paths work correctly:

```bash
# 1. Go to project root
cd bak-economics

# 2. Check paths
python3 << 'EOF'
import os

print("Current directory:", os.getcwd())
print("Should end with: bak-economics")
print()

paths = [
    'mvp/consolidated_schema.py',
    'mvp/01_consolidate_scraped_data.py',
    'scraper/01_calls_scrapers.py',
    'tender-system/demo.html'
]

for p in paths:
    exists = "✅" if os.path.exists(p) else "❌"
    print(f"{exists} {p}")
EOF
```

Expected output:
```
Current directory: /your/path/bak-economics
Should end with: bak-economics

✅ mvp/consolidated_schema.py
✅ mvp/01_consolidate_scraped_data.py
✅ scraper/01_calls_scrapers.py
✅ tender-system/demo.html
```

---

## 🐛 **Common Issues & Solutions**

### **Issue: "File not found"**

**Cause:** Running from wrong directory

**Solution:**
```bash
# Check where you are
pwd

# Should end with: /bak-economics
# If not, navigate to project root:
cd path/to/bak-economics
```

---

### **Issue: "Database file not found"**

**Cause:** Database directory doesn't exist

**Solution:**
```bash
# Create directory
mkdir -p mvp/database

# Initialize database
python mvp/consolidated_schema.py
```

---

### **Issue: "No such file or directory: scraper/scraper/..."**

**Cause:** Running from wrong directory

**Solution:**
```bash
# Always run from project root
cd bak-economics
python mvp/01_consolidate_scraped_data.py
```

---

## 📚 **Summary**

✅ **All paths are relative to `bak-economics/` root**  
✅ **No hardcoded `/Users/...` paths**  
✅ **Works on any machine, any OS**  
✅ **Just clone and run!**

**Golden Rule:** Always run scripts from the `bak-economics/` directory!

```bash
cd bak-economics           # Your reference point
python mvp/...             # All scripts from here
python scraper/...         # All paths relative
```

**That's it! 🎉**

