#!/bin/bash
# Setup script for Tender Management System

echo "🎯 Setting up Tender Management System..."

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️  Creating .env file..."
    cat > .env << 'EOF'
# OpenAI Configuration (Required)
OPENAI_API_KEY=your_openai_api_key_here

# Model Settings (Optional)
OPENAI_MODEL=gpt-4o-mini
TEMPERATURE=0.1

# Database (Optional)
DB_PATH=tender-system/database/tenders.db
EOF
    echo "⚠️  Please edit .env and add your OpenAI API key!"
else
    echo "ℹ️  .env file already exists, skipping..."
fi

# Initialize database
echo "💾 Initializing database..."
python main.py --init-db

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your OPENAI_API_KEY"
echo "  2. Run: python main.py --scrape simap --days-back 7"
echo "  3. Launch UI: streamlit run ui/app.py"
echo ""

