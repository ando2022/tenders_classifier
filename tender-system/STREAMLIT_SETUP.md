# 🚀 Streamlit Setup Guide

Complete instructions for pulling the repository and launching the Streamlit application.

## 📋 Prerequisites

- **Python 3.9+** (tested with Python 3.9.6)
- **Git** for pulling the repository
- **OpenAI API Key** (optional, for AI classification features)

## 🔧 Step-by-Step Setup

### 1. Pull the Repository

```bash
# Clone the repository
git clone git@gitlab.propulsion-home.ch:datascience/bootcamp/final-projects/ds-2025-08/bak-economics.git

# Navigate to the tender system directory
cd bak-economics/tender-system
```

### 2. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

**If you encounter permission issues:**
```bash
# Use user installation
pip install --user -r requirements.txt
```

**If you're using conda:**
```bash
# Create a new environment
conda create -n tender-system python=3.9
conda activate tender-system
pip install -r requirements.txt
```

### 3. Set Up Environment Variables (Optional)

Create a `.env` file in the `tender-system` directory:

```bash
# Create .env file
touch .env
```

Add your OpenAI API key (optional - system works without it):
```env
# OpenAI API Key for AI classification (optional)
OPENAI_API_KEY=your_openai_api_key_here

# Database path (optional - uses default)
DB_PATH=database/tenders.db
```

### 4. Initialize the Database

```bash
# Initialize the database with tables
python main.py --init-db
```

You should see:
```
✅ Database initialized at database/tenders.db
```

### 5. Launch Streamlit

```bash
# Launch the Streamlit application
streamlit run ui/app.py
```

**Alternative launch commands:**
```bash
# Launch on a specific port
streamlit run ui/app.py --server.port 8501

# Launch with specific host
streamlit run ui/app.py --server.address 0.0.0.0

# Launch with browser auto-open disabled
streamlit run ui/app.py --server.headless true
```

### 6. Access the Application

- **Local URL**: http://localhost:8501
- **Network URL**: http://[your-ip]:8501 (if using --server.address 0.0.0.0)

## 🔧 Troubleshooting

### Issue: "File does not exist: ui/app.py"

**Solution**: Make sure you're in the correct directory:
```bash
pwd  # Should show: .../bak-economics/tender-system
ls ui/  # Should show app.py
```

### Issue: "ModuleNotFoundError: No module named 'streamlit'"

**Solutions**:
```bash
# Option 1: Reinstall streamlit
pip install streamlit

# Option 2: Use specific Python version
python3 -m streamlit run ui/app.py

# Option 3: Check Python version
python --version  # Should be 3.9+
```

### Issue: "Unable to open database file"

**Solutions**:
```bash
# Option 1: Initialize database
python main.py --init-db

# Option 2: Check file permissions
ls -la database/
chmod 644 database/tenders.db

# Option 3: Create database directory
mkdir -p database
```

### Issue: Streamlit won't start

**Solutions**:
```bash
# Check if port is already in use
lsof -i :8501

# Kill existing Streamlit processes
pkill -f streamlit

# Try a different port
streamlit run ui/app.py --server.port 8502
```

### Issue: Python environment conflicts

**Solution**: Use virtual environment:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Launch Streamlit
streamlit run ui/app.py
```

## 🎯 Quick Demo (No Database Required)

If you encounter database issues, you can use the HTML demo:

```bash
# Open the demo file in your browser
open demo.html
# Or double-click demo.html in Finder/Explorer
```

## 📊 Application Features

Once launched, you'll have access to:

### 📊 Dashboard
- Overview statistics
- Recent activity
- Performance metrics

### 📋 All Tenders
- Browse all collected tenders
- Filter by source and relevance
- View detailed information

### ✅ Relevant Tenders
- High-confidence matches only
- Export to Excel functionality
- German translations and summaries

### 🔍 Search
- Search tenders by keywords
- Real-time results
- Full-text search

### 🚀 Run Scraper
- Manual scraper execution
- Configuration options
- Real-time progress

### 📈 Analytics
- Classification performance
- Trends and charts
- Statistics

## 🔄 Development Workflow

### Making Changes

1. **Edit files** in your preferred editor
2. **Streamlit auto-reloads** when you save changes
3. **Refresh browser** to see updates

### Adding New Features

1. **Edit `ui/app.py`** for UI changes
2. **Edit `database/models.py`** for data structure changes
3. **Run migrations** if database schema changes:
   ```bash
   python migrate_db.py
   ```

### Testing Changes

```bash
# Test database connection
python -c "from database.models import init_db; init_db(); print('✅ Database OK')"

# Test scraper
python main.py --scrape simap --days-back 1 --no-classify

# Test classifier (requires OpenAI API key)
python -c "from classifier.llm_classifier import LLMClassifier; print('✅ Classifier OK')"
```

## 📞 Support

If you encounter issues:

1. **Check this troubleshooting guide**
2. **Verify Python version** (3.9+ required)
3. **Check file permissions** in the tender-system directory
4. **Ensure all dependencies are installed**

## 🎉 Success!

Once everything is working, you should see:
- Streamlit running on http://localhost:8501
- Database initialized with proper tables
- All 6 pages accessible in the web interface
- Sample data or ability to scrape new data

**Your tender management system is ready to use! 🚀**
