# Tenders-LLM Quick Reference

## 📁 Where Everything Is Stored

### 1. **Prompts** (All versions tracked)
```
prompts/
├── classify_tender_balanced.md          ← CURRENT BEST (v2)
├── classify_tender.md                   ← Old conservative version
├── PROMPT_CHANGELOG.md                  ← Detailed version history
└── archive/
    ├── v1_classify_tender_conservative_2024-10-08.md
    └── v2_classify_tender_balanced_2024-10-08.md
```

### 2. **Experiment Results** (Every trial recorded)
```
results/
└── prompt_comparison_20251009_090604.json    ← Latest comparison
```

### 3. **Prediction Files** (Every test run saved)
```
data/processed/
├── preds_v2_title_only.jsonl         ← Title-only results (90% acc)
├── preds_v3_full_text.jsonl          ← Full-text results (88% acc)
├── preds_test10.jsonl                ← Initial 10-case test
└── preds_test50_improved.jsonl       ← 50-case improved test
```

### 4. **Experiment Log** (Complete history)
```
EXPERIMENT_LOG.md    ← ALL experiments documented here
```

---

## 📊 Latest Results (Experiment #3)

**Test Set:** 50 validation cases (23 positives, 27 negatives)  
**Date:** 2024-10-09

| Version | Input Type | Accuracy | Precision | Recall | F1 | Winner |
|---------|-----------|----------|-----------|--------|-----|---------|
| **v2** | **Title only** | **90%** | **95%** | **83%** | **0.884** | ✅ **BEST** |
| v3 | Full text | 88% | 91% | 83% | 0.864 | ❌ Worse |

### Key Finding:
**Title-only is BETTER than full-text!**
- Higher precision (95% vs 91%)
- Same recall (83%)
- Simpler and more reliable

---

## 🎯 Current Best Prompt (v2 Balanced)

**File:** `prompts/classify_tender_balanced.md`

**Key Decision Rules:**
1. ✅ Broad economic research scope (analysis, forecasts, surveys, impact studies)
2. ✅ Be inclusive for borderline cases
3. ✅ Even specialized domains (CO2, healthcare) are valid if they need economic analysis
4. ❌ Reject pure IT, construction, logistics without research component

**Performance:**
- 90% accuracy
- 95% precision (when it says "Yes", 95% correct)
- 83% recall (catches 83% of actual positives)
- Only 1 false positive out of 27 negatives
- Missed 4 out of 23 positives

**Missed Cases:**
1. "EuroAirport" (too vague)
2. "Marktdaten - Lieferung und Integration" (sounded like data delivery)
3. "Diskussionsbeiträge Familienpolitik" (discussion, not study)
4. "Auswirkungen zivilstandsunabhängige Altersvorsorge" (policy focus unclear)

---

## 📈 Complete Experiment History

| # | Date | Version | Input | Cases | Acc | Prec | Rec | F1 | Status |
|---|------|---------|-------|-------|-----|------|-----|-----|--------|
| 1 | Oct 8 | v1 conservative | Title | 10 | 80% | N/A | 0% | 0.0 | ❌ Failed |
| 2 | Oct 8 | v2 balanced | Title | 50 | 92% | 95% | 87% | 0.909 | ✅ Excellent |
| 3a | Oct 9 | v2 balanced | Title | 50 | 90% | 95% | 83% | 0.884 | ✅ Best |
| 3b | Oct 9 | v2 balanced | Full text | 50 | 88% | 91% | 83% | 0.864 | ⚠️  Worse |

---

## 🔄 How to Track New Experiments

### Step 1: Run experiment
```bash
python scripts/test_prompt_versions.py
```

### Step 2: Results auto-saved to:
- `results/prompt_comparison_YYYYMMDD_HHMMSS.json`
- `data/processed/preds_vX_description.jsonl`

### Step 3: Update EXPERIMENT_LOG.md
Add entry with:
- Date, version, configuration
- Metrics (accuracy, precision, recall, F1)
- Confusion matrix
- Key findings
- Missed cases

### Step 4: If new prompt created
```bash
# Archive it
cp prompts/new_prompt.md prompts/archive/vX_description_YYYY-MM-DD.md

# Update PROMPT_CHANGELOG.md
```

### Step 5: Commit
```bash
git add tenders-llm/
git commit -m "tenders-llm: experiment #N - [description] - [key metric]"
git push
```

---

## 📝 Current Best Prompt Decision Rules

**What to SELECT:**
- Economic/statistical **analysis, studies, research, evaluation**
- Surveys or data collection for economic purposes
- Impact studies (economic, social, employment)
- Cost-benefit analysis and feasibility studies
- Regional/sectoral economic development
- Policy evaluation and recommendations
- Even specialized domains (CO2, healthcare, transport) if they need economic analysis

**What to REJECT:**
- Pure IT development/software without research
- Construction, infrastructure without economic analysis
- Legal services, translations, logistics
- Training, education delivery (not evaluation)
- Goods procurement without analysis

**Borderline cases:** Lean toward "Yes" with moderate confidence (60-75)

---

## 🎓 Training Data

**Train set:** 3,561 tenders (96 positives)  
**Validation set:** 474 tenders (23 positives)  
**Test set:** 713 tenders (43 positives)

**Few-shot examples in prompt:** 93 positive titles from training set

---

## 💡 Key Insights

1. ✅ **Prompt engineering is critical** - Decision rules changed recall from 0% → 87%
2. ✅ **Title-only works best** - Full text adds noise, not signal
3. ✅ **Few-shot learning effective** - 93 examples provide strong signal
4. ⚠️  **Some positives have vague titles** - Hard to catch without full tender context
5. ✅ **High precision achieved** - 95% precision means very few false alarms

---

*Last Updated: 2024-10-09*


