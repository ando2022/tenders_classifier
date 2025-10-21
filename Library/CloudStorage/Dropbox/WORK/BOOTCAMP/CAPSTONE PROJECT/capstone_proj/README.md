# Tender Management System

A comprehensive web scraping and AI-powered classification system for public tenders from Swiss (SIMAP) and German (Evergabe) sources.

## Features

- 🔍 **Multi-Source Scraping**: Extract tenders from SIMAP (Swiss) and Evergabe (German) platforms
- 🤖 **AI Classification**: Automatic tender classification using OpenAI GPT-4
- 🌐 **Translation**: Automatic translation of tenders to English
- 📊 **Database Management**: SQLite storage with full tender lifecycle management
- 📋 **Interactive UI**: Streamlit-based web interface

## Local Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up Environment Variables

Create a `time.config` file in the project root with your OpenAI API key:

```json
{
  "openai_api_key": "your_openai_api_key_here",
  "mode": "absolute",
  "from": "2025-01-01",
  "to": "2025-01-31"
}
```

**Important**: Never commit your API keys to version control.

### 3. Run the Application

```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`

## Streamlit Cloud Deployment

### 1. Prepare for Deployment

The project is already configured for Streamlit Cloud deployment with:
- ✅ `.streamlit/config.toml` - Streamlit configuration
- ✅ `requirements.txt` - Dependencies with versions
- ✅ Proper project structure

### 2. Deploy to Streamlit Cloud

1. **Push to GitHub**: Ensure your code is in a GitHub repository
2. **Go to Streamlit Cloud**: Visit [share.streamlit.io](https://share.streamlit.io)
3. **Sign in**: Use your GitHub account
4. **Deploy New App**: Click "New app"
5. **Configure**:
   - **Repository**: Select your GitHub repository
   - **Branch**: `main` (or your default branch)
   - **Main file path**: `app.py`
6. **Add Secrets**: In the app settings, add:
   - `OPENAI_API_KEY`: Your OpenAI API key
7. **Deploy**: Click "Deploy!"

### 3. Environment Variables for Production

In Streamlit Cloud, add these environment variables in your app settings:

```
OPENAI_API_KEY=your_openai_api_key_here
```

## Project Structure

- `app.py` - Main Streamlit application
- `classifier.py` - AI-powered tender classification
- `evergabe_scraper.py` - German tender scraper
- `simap_scraper.py` - Swiss tender scraper
- `cpv_config.py` - CPV code and keyword configuration
- `time.config` - Date range and API configuration
- `.streamlit/` - Streamlit deployment configuration

## Usage

### Scraping Tenders
1. Navigate to "🔍 Scrape Tenders"
2. Select date range and sources (SIMAP/Evergabe)
3. Click "🚀 Start Scraping"
4. Tenders are automatically translated and stored

### Viewing & Classification
1. Navigate to "📋 View & Classify"
2. Filter by classification status, source, or view mode
3. Use "🤖 Classify All Unclassified" for bulk AI classification
4. Provide feedback on classifications

## Security

- API keys are stored in environment variables
- Sensitive files are excluded from version control
- Production secrets are managed through Streamlit Cloud
- Never commit API keys to the repository

## Troubleshooting

### Common Issues

1. **Playwright Installation**: If Playwright fails, run:
   ```bash
   playwright install
   ```

2. **OpenAI API Errors**: Ensure your API key is valid and has sufficient credits

3. **Scraping Timeouts**: The scrapers include retry logic, but large date ranges may take time

### Support

For issues or questions, check the application logs in Streamlit Cloud or local terminal output.

