# Summary: What You Requested and What We Found

## ✅ What I Did

### 1. **Showed you the current prompt**
**Location:** `prompts/classify_tender_balanced.md`

**Key sections:**
- Client Services (your full BAK Economics service descriptions)
- Keywords (Analyse, BBL, BFS, Benchmarking, Wirtschaft, etc.)
- 93 positive tender titles from training set as examples
- **Decision rules** (the critical part):
  ```
  1. Broad economic research scope (analysis, forecasts, surveys, impact studies)
  2. What to SELECT: economic/statistical analysis, studies, research, evaluation
  3. What to REJECT: pure IT, construction, legal, logistics without research
  4. Be inclusive for borderline cases
  5. Language-agnostic
  ```

### 2. **Showed you the validation set results**
**50 validation cases** (23 positives, 27 negatives)

**Detailed breakdown:**
- ✅ **Found 19/23 positives** (82.6% recall)
- ❌ **Missed 4 positives:**
  1. "EuroAirport" - too vague title
  2. "Marktdaten - Lieferung und Integration" - sounded like data delivery
  3. "Diskussionsbeiträge Familienpolitik" - discussion contributions
  4. "Auswirkungen zivilstandsunabhängige Altersvorsorge" - pension policy, unclear

- ✅ **Correctly rejected 26/27 negatives**
- ❌ **1 false positive:** "Multimethoden-Datenerhebungsmandat" - data collection sounded like research

### 3. **Showed you where experiments are tracked**

**All experiment tracking in these files:**

#### A. **EXPERIMENT_LOG.md** (Complete history)
```
Location: tenders-llm/EXPERIMENT_LOG.md

Contains:
- All 3 experiments run so far
- Configuration for each (prompt version, input type)
- Full metrics (accuracy, precision, recall, F1, confusion matrix)
- Missed cases with reasoning
- Key insights and conclusions
```

#### B. **PROMPT_CHANGELOG.md** (Prompt versions)
```
Location: tenders-llm/prompts/PROMPT_CHANGELOG.md

Contains:
- Version history of all prompts
- Performance metrics for each version
- What changed between versions
- Quick reference table
```

#### C. **Results JSON** (Machine-readable)
```
Location: tenders-llm/results/prompt_comparison_TIMESTAMP.json

Contains:
- Structured results from each experiment
- Can be loaded for visualization or further analysis
```

#### D. **Prediction Files** (Detailed predictions)
```
Location: tenders-llm/data/processed/preds_*.jsonl

Files:
- preds_v2_title_only.jsonl (title-only results)
- preds_v3_full_text.jsonl (full-text results)
- preds_test10.jsonl (initial 10-case test)
- preds_test50_improved.jsonl (50-case test)

Each line contains:
{
  "id": "3811",
  "title": "...",
  "lang": "de",
  "true_label": 1,
  "prediction": "Yes",
  "confidence_score": 85,
  "reasoning": "..."
}
```

#### E. **Prompt Archive** (All versions saved)
```
Location: tenders-llm/prompts/archive/

Files:
- v1_classify_tender_conservative_2024-10-08.md (0% recall - deprecated)
- v2_classify_tender_balanced_2024-10-08.md (87% recall - current best)
```

---

## 📊 Key Findings

### **Title-Only is BETTER than Full-Text**

| Metric | Title Only (v2) | Full Text (v3) | Winner |
|--------|----------------|----------------|--------|
| Accuracy | **90%** | 88% | Title ✅ |
| Precision | **95%** | 91% | Title ✅ |
| Recall | 83% | 83% | Tie |
| F1-Score | **0.884** | 0.864 | Title ✅ |
| False Positives | **1** | 2 | Title ✅ |

**Why title-only wins:**
1. Selected tenders have short/missing full text (mean=878 chars)
2. Not-selected tenders have longer full text (mean=7215 chars)
3. Full text adds noise for selected cases
4. Title contains the key signal

**Recommendation:** ✅ **Use title-only approach (v2)**

---

## 📂 Complete File Structure

```
tenders-llm/
├── EXPERIMENT_LOG.md              ← 🎯 ALL experiments documented here
├── QUICK_REFERENCE.md              ← Quick lookup of results
├── SUMMARY_FOR_USER.md             ← This file (answers your questions)
│
├── prompts/
│   ├── classify_tender_balanced.md      ← CURRENT BEST (v2)
│   ├── PROMPT_CHANGELOG.md              ← Version history
│   └── archive/
│       ├── v1_classify_tender_conservative_2024-10-08.md
│       └── v2_classify_tender_balanced_2024-10-08.md
│
├── results/
│   └── prompt_comparison_20251009_090604.json    ← Latest experiment
│
├── data/
│   ├── processed/
│   │   ├── tenders_clean.parquet                 ← Clean data with full text
│   │   ├── train_ids.txt (3,561)                 ← Training split
│   │   ├── val_ids.txt (474)                     ← Validation split
│   │   ├── test_ids.txt (713)                    ← Test split
│   │   ├── preds_v2_title_only.jsonl             ← Title-only predictions
│   │   ├── preds_v3_full_text.jsonl              ← Full-text predictions
│   │   └── val_ids_test50_fulltext.txt           ← 50-case test set
│   └── raw/
│       ├── tenders_content.xlsx                  ← Source data with full text
│       ├── case_studies/ (222 PDFs)              ← BAK case study reports
│       ├── services.md                           ← Service descriptions
│       └── keywords.csv                          ← Keywords
│
└── scripts/
    ├── 00_reload_data_with_fulltext.py          ← Load data with full text
    ├── 01_prepare_data.py                        ← Clean & detect language
    ├── 02_make_splits.py                         ← Create train/val/test
    ├── 03_build_prompt.py                        ← Build prompt with examples
    ├── test_prompt_versions.py                   ← Compare prompt versions
    └── 00_extract_case_studies.py                ← Extract PDF case studies
```

---

## 🎯 Where to Find Each Item You Asked For

### 1. "Show me the results"
→ **results/prompt_comparison_20251009_090604.json**  
→ **EXPERIMENT_LOG.md** (with interpretation)

### 2. "Show me the validation items"
→ **data/processed/preds_v2_title_only.jsonl** (all 50 cases with predictions)  
→ Run: `cat data/processed/preds_v2_title_only.jsonl | python -m json.tool`

### 3. "Show me the prompt"
→ **prompts/classify_tender_balanced.md** (current best)  
→ See decision rules at the end of the file

### 4. "Show me where you record trials"
→ **EXPERIMENT_LOG.md** (human-readable history)  
→ **results/*.json** (machine-readable)  
→ **PROMPT_CHANGELOG.md** (prompt-specific changes)

---

## 🔄 Next Steps (Optional)

### Experiment #4: With Case Studies
- Extract text from 222 PDF case studies
- Add summaries to prompt as "types of work we do"
- Test on same 50 validation cases
- Compare vs title-only

### Experiment #5: Full Pipeline
- Run on entire validation set (474 cases)
- Run on test set (713 cases)
- Generate PR curves and precision@K charts

---

## 💡 Key Insights So Far

1. ✅ **Prompt engineering is critical** - Changed recall from 0% → 83%
2. ✅ **Title-only works best** - Full text doesn't help
3. ✅ **95% precision achieved** - Very few false alarms
4. ⚠️  **83% recall** - Still missing ~17% of positives
5. ✅ **All experiments tracked** - Easy to compare and reproduce

---

*Generated: 2024-10-09*


