#!/bin/bash

# 🚀 Streamlit Setup Script
# This script automates the setup process for the Tender Management System

set -e  # Exit on any error

echo "🎯 BAK Economics - Tender Management System Setup"
echo "=================================================="

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "✅ Python version $python_version is compatible"
else
    echo "❌ Python 3.9+ required. Current version: $python_version"
    echo "Please upgrade Python and try again."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found. Please run this script from the tender-system directory."
    exit 1
fi

echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

echo "🗄️  Initializing database..."
python3 main.py --init-db

echo "🔧 Checking Streamlit installation..."
python3 -c "import streamlit; print('✅ Streamlit is available')"

echo ""
echo "🎉 Setup complete! You can now launch the application:"
echo ""
echo "   streamlit run ui/app.py"
echo ""
echo "📖 For detailed instructions, see STREAMLIT_SETUP.md"
echo ""
echo "🌐 The application will be available at: http://localhost:8501"
echo ""
echo "💡 Tip: If you encounter issues, check the troubleshooting section in STREAMLIT_SETUP.md"
