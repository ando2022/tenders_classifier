# 👥 Colleague Setup Guide

**Complete instructions for setting up the BAK Economics Tender Management System from Git.**

## 🎯 **What You'll Get**

- **Complete tender management system** with web interface
- **Emergency classifier** (cosine similarity fallback)
- **Export functionality** (Excel/CSV downloads)
- **Sample data** for immediate testing
- **Comprehensive documentation**

---

## 🚀 **Quick Setup (5 minutes)**

### **1. Clone the Repository**
```bash
git clone git@gitlab.propulsion-home.ch:datascience/bootcamp/final-projects/ds-2025-08/bak-economics.git
cd bak-economics/tender-system
```

### **2. Run Automated Setup**
```bash
./setup_streamlit.sh
```

### **3. Add Sample Data**
```bash
python add_sample_data.py
```

### **4. Launch the Application**
```bash
streamlit run ui/app.py
```

### **5. Open in Browser**
- **URL**: http://localhost:8501
- **Username**: (no login required)

---

## 📋 **Detailed Setup Instructions**

### **Prerequisites**
- **Python 3.9+** (tested with Python 3.9.6)
- **Git** for cloning the repository
- **Internet connection** (for initial package installation)

### **Step 1: Clone Repository**
```bash
# Clone the repository
git clone git@gitlab.propulsion-home.ch:datascience/bootcamp/final-projects/ds-2025-08/bak-economics.git

# Navigate to the tender system directory
cd bak-economics/tender-system

# Verify you're in the right directory
ls -la
# You should see: ui/, database/, classifier/, main.py, requirements.txt, etc.
```

### **Step 2: Install Dependencies**
```bash
# Install all required packages
pip install -r requirements.txt

# If you encounter permission issues:
pip install --user -r requirements.txt

# If you're using conda:
conda create -n tender-system python=3.9
conda activate tender-system
pip install -r requirements.txt
```

### **Step 3: Initialize Database**
```bash
# Initialize the database with tables
python main.py --init-db
```

You should see:
```
✅ Database initialized at database/tenders.db
```

### **Step 4: Add Sample Data (Optional but Recommended)**
```bash
# Add sample tenders and positive cases for testing
python add_sample_data.py
```

This will add:
- 5 sample tenders to the database
- 12 positive cases to the emergency classifier
- Test the emergency classifier functionality

### **Step 5: Launch Streamlit Application**
```bash
# Launch the web application
streamlit run ui/app.py
```

**Alternative launch commands:**
```bash
# Launch on a specific port
streamlit run ui/app.py --server.port 8501

# Launch with specific host (for network access)
streamlit run ui/app.py --server.address 0.0.0.0

# Launch without auto-opening browser
streamlit run ui/app.py --server.headless true
```

### **Step 6: Access the Application**
- **Local URL**: http://localhost:8501
- **Network URL**: http://[your-ip]:8501 (if using --server.address 0.0.0.0)

---

## 🎯 **What You Can Do Immediately**

### **📊 Dashboard**
- View system overview and statistics
- See recent activity and performance metrics

### **📋 All Tenders**
- Browse all collected tenders
- Filter by source and relevance
- View detailed tender information

### **✅ Relevant Tenders**
- See only high-confidence relevant tenders
- **Export to Excel/CSV** with German titles and summaries
- View AI-generated reasoning

### **🔍 Search**
- Search tenders by keywords
- Real-time results
- Full-text search capability

### **🚨 Emergency Classifier** (NEW!)
- **Test classification** with sample tenders
- **Add positive cases** for better matching
- **Load cases from database**
- **Adjust similarity thresholds**
- **View statistics** and model status

### **🚀 Run Scraper**
- Manual scraper execution
- Configuration options
- Real-time progress monitoring

### **📈 Analytics**
- Classification performance metrics
- Trends and charts
- Statistical analysis

---

## 🚨 **Emergency Classifier Features**

The emergency classifier is a **cost-effective fallback** that automatically activates when OpenAI is unavailable or too expensive.

### **Key Features:**
- **Cosine similarity matching** against positive cases
- **Automatic activation** when OpenAI fails
- **Same output format** as OpenAI classifier
- **No API costs** for classification
- **Always available** (works offline)

### **How to Use:**
1. **Navigate to "🚨 Emergency Classifier"** in the sidebar
2. **View statistics** in the first tab
3. **Test classification** in the second tab
4. **Add positive cases** in the third tab
5. **Adjust settings** in the fourth tab

### **Adding Positive Cases:**
```bash
# Via command line
python manage_emergency_classifier.py add \
  --title "Economic Analysis Project" \
  --description "Comprehensive economic analysis" \
  --confidence 0.95

# Via web interface
# Go to Emergency Classifier → Manage Positive Cases → Add Positive Case
```

---

## 📥 **Export Functionality**

### **Export Relevant Tenders**
```bash
# Export relevant tenders to Excel
python export_client_report.py --relevant

# Export to CSV format
python export_client_report.py --relevant --format csv

# Export with custom confidence threshold
python export_client_report.py --relevant --min-confidence 80

# Export without full text (smaller files)
python export_client_report.py --relevant --no-fulltext
```

### **Via Web Interface**
1. Go to "✅ Relevant Tenders" page
2. Click "📥 Export to Excel" button
3. File downloads automatically

---

## 🔧 **Troubleshooting**

### **Issue: "File does not exist: ui/app.py"**
**Solution**: Make sure you're in the correct directory:
```bash
pwd  # Should show: .../bak-economics/tender-system
ls ui/  # Should show app.py
```

### **Issue: "ModuleNotFoundError: No module named 'streamlit'"**
**Solutions**:
```bash
# Option 1: Reinstall streamlit
pip install streamlit

# Option 2: Use specific Python version
python3 -m streamlit run ui/app.py

# Option 3: Check Python version
python --version  # Should be 3.9+
```

### **Issue: "Unable to open database file"**
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

### **Issue: Streamlit won't start**
**Solutions**:
```bash
# Check if port is already in use
lsof -i :8501

# Kill existing Streamlit processes
pkill -f streamlit

# Try a different port
streamlit run ui/app.py --server.port 8502
```

### **Issue: Emergency classifier not working**
**Solutions**:
```bash
# Add sample data
python add_sample_data.py

# Test emergency classifier
python manage_emergency_classifier.py test

# Check statistics
python manage_emergency_classifier.py stats
```

---

## 🎯 **Quick Test Commands**

```bash
# Test the emergency classifier
python manage_emergency_classifier.py test

# View emergency classifier statistics
python manage_emergency_classifier.py stats

# Export tenders
python export_client_report.py --relevant

# Check database status
python export_client_report.py --stats

# Run scraper (if you have OpenAI API key)
python main.py --scrape simap --days-back 7
```

---

## 📚 **Available Documentation**

- **`README.md`** - Main system overview
- **`STREAMLIT_SETUP.md`** - Detailed Streamlit setup
- **`EMERGENCY_CLASSIFIER_GUIDE.md`** - Emergency classifier guide
- **`CLIENT_OUTPUT_GUIDE.md`** - Export functionality guide
- **`START_HERE.md`** - Master overview document

---

## 🎉 **Success Indicators**

You'll know everything is working when:
- ✅ Streamlit launches without errors
- ✅ You can access http://localhost:8501
- ✅ All 7 pages load correctly
- ✅ Emergency classifier shows positive cases
- ✅ Export functionality works
- ✅ Sample data is visible

---

## 🆘 **Getting Help**

If you encounter issues:
1. **Check this troubleshooting section**
2. **Verify Python version** (3.9+ required)
3. **Check file permissions** in the tender-system directory
4. **Ensure all dependencies are installed**
5. **Try the automated setup script**: `./setup_streamlit.sh`

---

## 🚀 **Next Steps**

Once everything is working:
1. **Explore the interface** - try all the pages
2. **Test the emergency classifier** - add your own positive cases
3. **Export some data** - try the Excel/CSV export
4. **Add your own tenders** - use the scraper functionality
5. **Customize settings** - adjust thresholds and parameters

**Your tender management system is ready to use! 🎯**
