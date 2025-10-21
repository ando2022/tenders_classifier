# Tenders Classifier

A web scraping and classification system for public tenders from various sources.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up Environment Variables

Create a `.env` file in the project root with your OpenAI API key:

```bash
# .env
OPENAI_API_KEY=your_openai_api_key_here
```

**Important**: Never commit your `.env` file to version control. It's already included in `.gitignore`.

### 3. Alternative: Set Environment Variable

You can also set the environment variable directly:

```bash
export OPENAI_API_KEY=your_openai_api_key_here
```

## Usage

Run the main application:

```bash
python app.py
```

## Project Structure

- `app.py` - Main Streamlit application
- `classifier.py` - Tender classification logic
- `evergabe_scraper.py` - Evergabe.ch scraper
- `simap_scraper.py` - Simap.ch scraper
- `cpv_config.py` - CPV code configuration
- `time.config` - Time range configuration

## Security

- API keys are stored in environment variables
- `.env` files are excluded from version control
- Never commit sensitive information to the repository
