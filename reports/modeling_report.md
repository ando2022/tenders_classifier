## Tender Modeling Progress Report

Date: 2025-10-03

### Dataset
- Source file: `My Drive/BAK-Economics/Data/raw/test set/simap/kw hits/tenders_details.xlsx`
- Clean output: `data/processed/tenders_clean.parquet` and `.csv`
- Rows used: 306
- Labels (derived from `Status`):
  - Stage 1 `kw_hit_selected`: 8 positives, 298 negatives (2.6% pos)
  - Stage 2 `kw_hit_selected_by_sales` within selected: 2 positives, 6 negatives

### Approach
- Two-stage funnel modeling:
  - M1: Predict `kw_hit_selected` for all items.
  - M2: Predict `kw_hit_selected_by_sales` among items with M1=1.
  - Current final score: `p_final = p_select × prior_sales`, with prior_sales=0.25 (2/8), because M2 lacks data to train.
- Evaluation: Out-of-Fold (OOF) CV (5-fold). Each row is predicted by a model that did not see it, giving honest metrics without a held-out set.

### Implemented Models (Stage 1)
All models trained with class_weight='balanced'. Metrics reported are OOF.

| Model | Description | AUC | PR-AUC |
|---|---|---:|---:|
| TF‑IDF word/bigram | `TfidfVectorizer(1–2-gram)` + Logistic Regression | 0.9996 | 0.9861 |
| TF‑IDF char 3–5 | `analyzer=char_wb, ngram(3–5)` + Logistic Regression | 1.0000 | 1.0000 |
| Multilingual embeddings | `paraphrase-multilingual-MiniLM-L12-v2` + Logistic Regression | 0.9975 | 0.9284 |
| Blended | TF‑IDF char + embeddings concatenated | 1.0000 | 1.0000 |

Notes:
- Perfect OOF for char TF‑IDF and blended likely reflects tiny positive count and strong lexical cues. Treat probabilities mainly as ranking signals; generalization should be re-checked as more positives arrive.

### Artifacts
- Data prep: `src/data_prep/load_and_clean.py`
- Baseline trainer (two-stage): `src/models/train_two_stage.py`
- Embeddings and comparisons: `src/models/train_two_stage_embeddings.py`
- Saved models: `models/stage1_tfidf.pkl`, `models/stage1_tfidf_char.pkl`, `models/stage1_embeddings.pkl`, `models/stage1_blended.pkl`
- OOF predictions: `models/oof_stage1.csv`
- Metrics JSON: `models/metrics_comparison.json`
- Stage 2 prior: `models/stage2_sales_prior.txt` (0.25)

### How to Use Now
- Score new tenders with the recommended model `stage1_tfidf_char.pkl` to get `p_select`.
- Use `p_final = p_select × 0.25` to prioritize for sales until we can train M2.

### Next Steps (Data & Modeling)
1. Collect labels
   - Grow Stage 1 positives; aim ≥50 positives in total.
   - Critically, collect Stage 2 labels; aim ≥20–30 sales-accepted positives to train M2.
2. Enrich text
   - If available, switch from titles to full tender content (requirements/description).
3. Features (optional when data available)
   - CPV labels (top-k one-hot), simple budget extraction (log value), buyer type, country, year/week.
4. Modeling
   - Calibrate probabilities (isotonic/Platt) once label counts increase.
   - Re-evaluate TF‑IDF char vs embeddings vs blended on expanded data.
5. Deployment
   - Generate and ship a ranked CSV (Topic, p_select, p_final) on each new batch.

### Risks
- Extremely imbalanced and tiny positive set; OOF metrics may be optimistic. Prioritize collecting more positives, especially for Stage 2.


