# Tenders LLM Classification Pipeline

Minimal LLM-based pipeline to classify tenders as relevant/irrelevant based on service descriptions and keywords.

## Project Structure

```
tenders-llm/
  data/
    raw/
      tenders.csv            # id,title,full_text,date,source
      selected_ids.csv       # human-selected tender IDs (one per line)
      services.md            # service descriptions (markdown/plain text)
      keywords.csv           # keyword,lang,weight,category
    processed/               # generated train/test splits, embeddings
  prompts/
    classify_tender.md       # LLM prompt template
  reports/                   # metrics, confusion matrices, logs
  scripts/
    01_prepare_data.py       # load raw data, clean text
    02_make_splits.py        # stratified train/test split
    03_build_prompt.py       # inject services/keywords into prompt template
    04_llm_predict.py        # batch predict with OpenAI/local LLM
    05_eval.py               # compute metrics, save reports
  utils/
    text_clean.py            # text preprocessing utilities
  .env.example
  requirements.txt
```

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Prepare `.env` from `.env.example` (add OpenAI key if needed).

3. Place your data in `data/raw/`:
   - `tenders.csv`: columns `id,title,full_text,date,source`
   - `selected_ids.csv`: one tender ID per line
   - `services.md`: your service descriptions
   - `keywords.csv`: columns `keyword,lang,weight,category`

4. Run pipeline:
   ```bash
   python scripts/01_prepare_data.py
   python scripts/02_make_splits.py
   python scripts/03_build_prompt.py
   python scripts/04_llm_predict.py
   python scripts/05_eval.py
   ```

5. Check `reports/` for metrics and predictions.

## Pipeline Steps

- **01_prepare_data.py**: Load raw CSVs, clean text, create binary labels from `selected_ids.csv`.
- **02_make_splits.py**: Stratified 80/20 train/test split; save to `processed/`.
- **03_build_prompt.py**: Build LLM prompt by injecting services and keywords into template.
- **04_llm_predict.py**: Batch classify test set via LLM API; save predictions.
- **05_eval.py**: Compute AUC, PR-AUC, confusion matrix, classification report; save to `reports/`.

## Notes

- Use local models (e.g., Ollama) or OpenAI API; adjust `04_llm_predict.py` accordingly.
- For production, consider caching embeddings and batching API calls to reduce cost.

