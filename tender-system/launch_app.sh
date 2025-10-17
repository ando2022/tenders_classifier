#!/bin/bash

# 🚀 Launch Script for BAK Economics Tender Management System
echo "🎯 BAK Economics - Tender Management System"
echo "============================================="

# Check if we're in the right directory
if [ ! -f "ui/app.py" ]; then
    echo "❌ Error: ui/app.py not found. Please run this script from the tender-system directory."
    exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
echo "🐍 Python version: $python_version"

# Check if Streamlit is available
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "❌ Streamlit not found. Installing..."
    pip3 install streamlit
fi

# Check if required packages are installed
echo "📦 Checking dependencies..."
python3 -c "import pandas, sqlalchemy, sklearn" 2>/dev/null || {
    echo "❌ Missing dependencies. Installing..."
    pip3 install pandas sqlalchemy scikit-learn
}

# Initialize database if needed
if [ ! -f "db/tenders.db" ]; then
    echo "🗄️ Initializing database..."
    python3 main.py --init-db
fi

# Add sample data if database is empty
tender_count=$(python3 -c "
import sys
sys.path.insert(0, '.')
from database.models import get_session, Tender
try:
    session = get_session()
    count = session.query(Tender).count()
    print(count)
except:
    print(0)
" 2>/dev/null || echo "0")

if [ "$tender_count" -eq 0 ]; then
    echo "📚 Adding sample data..."
    python3 add_sample_data.py
fi

echo ""
echo "🚀 Launching Streamlit application..."
echo "📍 URL: http://localhost:8501"
echo "🔄 Press Ctrl+C to stop the application"
echo ""

# Launch Streamlit
python3 -m streamlit run ui/app.py --server.port 8501 --server.address 0.0.0.0

