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
- Text used: full tender content (Excel column `Order Description` → standardized as `Topic`).
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
Below each step is the rationale for why it is critical now.

1. Collect labels (highest priority)
   - What: Increase positives for Stage 1; especially gather Stage 2 (sales-accepted) outcomes.
   - Why: Current Stage 2 has only 2 positives → cannot train; without more labels we can’t optimize downstream selection thresholds or learn sales preferences.
   - Target: ≥50 positives total for Stage 1; ≥20–30 positives for Stage 2.

2. Keep using full content; improve robustness
   - What: Continue training on full tender content; maintain char n‑gram TF‑IDF as default.
   - Why: Char n‑grams are language-robust; they reached perfect OOF on current data and scale with more labels.

3. Add lightweight structured signals (when available)
   - What: CPV label (top‑k one‑hot), presence of budget, log(budget), buyer type, country, year/week.
   - Why: These orthogonal signals help generalize beyond lexical matches and reduce brittleness.

4. Probability calibration (after more data)
   - What: Apply Platt or isotonic calibration on a validation fold.
   - Why: Turn raw scores into trustworthy probabilities to set business thresholds (auto‑select, sales handoff).

5. Model comparison and selection (ongoing)
   - What: Re‑evaluate TF‑IDF char, embeddings, and blended models as labels grow.
   - Why: Embeddings often surpass TF‑IDF once data and text length increase; pick by OOF PR‑AUC/lift.

6. Deployment and feedback
   - What: Produce ranked CSV for each batch; capture reviewer/sales outcomes back into the dataset.
   - Why: Creates the continuous labeling loop needed to improve Stage 2 and calibrate operating points.

### Data Collection Template (to enable richer features)

| Field | Example | Extraction method | Required? | Notes |
|---|---|---|---|---|
| Full text (content) | Full description | Already present (`Order Description`) | Yes | Primary signal for models |
| CPV code/label | 73200000-4 Research services | Regex + CPV lookup | Nice‑to‑have | Top‑k one‑hot |
| Budget value | 300'000 CHF | Regex currency + number | Nice‑to‑have | Also store currency; add log(budget) |
| Buyer/authority | Federal Office X | From sheet or text | Nice‑to‑have | Map to buyer_type buckets |
| Country | Switzerland | From buyer/text | Nice‑to‑have | Normalize names/ISO |
| Publication date | 2024‑09‑15 | From sheet | Nice‑to‑have | Derive year/week |
| Selection label | kw_hit_selected ∈ {0,1} | Business label | Yes | Stage 1 target |
| Sales label | kw_hit_selected_by_sales ∈ {0,1} | Business label | Critical | Stage 2 target |


### Risks
- Extremely imbalanced and tiny positive set; OOF metrics may be optimistic. Prioritize collecting more positives, especially for Stage 2.


