# OpenAI Tender Classification Script

This script automates the classification of new business tenders using OpenAI's GPT-3.5-turbo model. It analyzes historical winning tenders to build a "winning DNA" profile and uses this to predict whether new tenders are likely to be successful wins.

## Features

- **Data Loading**: Reads from `tenders.xlsx` and `Prompt_data.xlsx` files
- **Winning DNA Analysis**: Creates a comprehensive profile from historical winning tenders (N2=TRUE)
- **OpenAI Integration**: Uses GPT-3.5-turbo for intelligent tender classification
- **Comprehensive Output**: Generates predictions with confidence scores and detailed justifications
- **Excel Export**: Saves results to a multi-sheet Excel file

## Requirements

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Ensure your data files are in the correct location:
   - `../data/raw/tenders.xlsx` - Historical tender data
   - `../data/raw/Prompt_data.xlsx` - New tenders to classify (with sheets: simap, keywords, services)

2. Run the script:

```bash
python tender_classification_openai.py
```

## Output

The script generates `prompt_data_with_predictions_openai.xlsx` with three sheets:

- **simap**: Original tender data with added prediction columns:
  - `Prediction`: True/False (likely win or not)
  - `Confidence_Score`: 0-100% confidence level
  - `Justification`: Detailed reasoning for the prediction

- **keywords**: Original keywords data (unchanged)
- **services**: Original services data (unchanged)

## How It Works

1. **Data Processing**: Filters historical tenders where N2=TRUE to identify winning patterns
2. **Winning DNA Creation**: Combines winning tender examples with keywords and services
3. **AI Classification**: Uses OpenAI to analyze each new tender against the winning DNA
4. **Smart Prompting**: Creates detailed prompts that include context, examples, and specific instructions
5. **JSON Response Parsing**: Extracts structured predictions from OpenAI's responses

## Configuration

The script uses the following settings:
- **Model**: GPT-3.5-turbo
- **Temperature**: 0.3 (for consistent results)
- **Max Tokens**: 300 (for concise responses)
- **Rate Limiting**: 0.5 second delay between API calls

## Error Handling

The script includes robust error handling for:
- Missing or invalid data files
- OpenAI API errors
- JSON parsing failures
- Network connectivity issues

## API Key

The OpenAI API key is embedded in the script. For production use, consider using environment variables for security.
