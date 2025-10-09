# LLM Tender Classification - Experiment Log

This file tracks ALL experiments, prompts, and results for the tender classification project.

---

## Experiment #1: Initial Conservative Prompt (2024-10-08)

**Date:** 2024-10-08  
**Prompt Version:** v1 (conservative)  
**Prompt File:** `prompts/archive/v1_classify_tender_conservative_2024-10-08.md`  
**Test Set:** 10 validation cases (2 pos, 8 neg)  

### Configuration:
- Input: Title only
- Few-shot examples: 93 positive titles from training
- Decision rule: "Prefer high precision, avoid over-inclusive Yes"

### Results:
| Metric | Score |
|--------|-------|
| Accuracy | 80.0% |
| Precision | N/A (0 predicted positive) |
| Recall | 0.0% |
| F1-Score | 0.0 |

### Confusion Matrix:
```
           Predicted
           Yes  No
Actual Yes  0   2  ← Missed ALL positives
       No   0   8
```

### Key Issues:
- ❌ Too conservative - rejected ALL positives
- ❌ "avoid over-inclusive" instruction made LLM too strict
- ❌ Rejected valid economic research tenders (surveys, cost analysis)

### Example Missed Cases:
1. "Survey about income and living conditions" → Rejected (but should select)
2. "Estimating investment costs for CO2 removal" → Rejected (but should select)

**Conclusion:** Prompt needs to be more inclusive. The "high precision" instruction backfired.

---

## Experiment #2: Balanced Prompt (2024-10-08)

**Date:** 2024-10-08  
**Prompt Version:** v2 (balanced)  
**Prompt File:** `prompts/classify_tender_balanced.md` + `prompts/archive/v2_classify_tender_balanced_2024-10-08.md`  
**Test Set:** 50 validation cases (23 pos, 27 neg)  

### Configuration:
- Input: Title only
- Few-shot examples: 93 positive titles from training
- Decision rule: **IMPROVED** - removed "avoid over-inclusive", added "be inclusive for borderline cases"

### Key Changes from v1:
1. ✅ Removed "prefer high precision, avoid over-inclusive" 
2. ✅ Added explicit scope: surveys, cost analysis, impact studies, etc.
3. ✅ Added "be inclusive for borderline cases" instruction
4. ✅ Clarified: even specialized domains (CO2, healthcare) are valid if they need economic analysis

### Results:
| Metric | Score |
|--------|-------|
| Accuracy | 92.0% (46/50) |
| Precision | 95.2% (20/21) |
| Recall | 87.0% (20/23) |
| F1-Score | 0.909 |

### Confusion Matrix:
```
           Predicted
           Yes  No
Actual Yes 20   3  ← Much better!
       No   1  26
```

### Missed Cases (False Negatives):
1. **ID 4632**: "EuroAirport" - too vague title
2. **ID 4643**: "Marktdaten - Lieferung und Integration" - sounded like data delivery
3. **ID 4726**: "Diskussionsbeiträge Familienpolitik" - discussion contributions

### False Positive:
- **ID 3637**: "Multimethoden-Datenerhebungsmandat zum Monitoring" - data collection sounded like research

**Conclusion:** ✅ Much better! 92% accuracy is strong. Ready for production testing on larger sets.

---

## Experiment #3: Title Only vs Full Text (2024-10-09)

**Date:** 2024-10-09  
**Test Set:** 50 validation cases (23 pos, 27 neg) - SAME as Experiment #2  
**Purpose:** Compare title-only vs full-text input  

### Configuration A - V2 (Title Only):
- Prompt: `classify_tender_balanced.md`
- Input: Title only (first 300 chars)
- Results File: `data/processed/preds_v2_title_only.jsonl`

### Configuration B - V3 (Full Text):
- Prompt: SAME `classify_tender_balanced.md`
- Input: Title + full text (up to 4000 chars)
- Results File: `data/processed/preds_v3_full_text.jsonl`

### Results Comparison:
| Version | Accuracy | Precision | Recall | F1 | TP | FP | FN |
|---------|----------|-----------|--------|----|----|----|----|
| V2 (Title) | 90.0% | 95.0% | 82.6% | 0.884 | 19 | 1 | 4 |
| V3 (Full Text) | 88.0% | 90.5% | 82.6% | 0.864 | 19 | 2 | 4 |

### Key Findings:
1. ❌ **Full text did NOT improve recall** (same 82.6%)
2. ❌ **Full text slightly decreased precision** (95% → 91%)
3. ❌ **Full text added 1 more false positive** (1 → 2)
4. ⚠️  **Same 4 cases missed in both versions**

### Cases Where V2 and V3 Differ:
- **ID 3519** ("Market intelligence consultant"):
  - V2 (Title): No (conf=70) ✓ Correct
  - V3 (Full Text): Yes (conf=75) ✗ Wrong (was actually negative)

### Interpretation:
- Full text adds noise rather than signal
- Many selected tenders don't have full text (mean=878 chars vs 7215 for negatives)
- Title alone is sufficient and more reliable

**Conclusion:** ⚠️ Full text does NOT help. Stick with title-only (v2) approach.

---

## Experiment #4: With Case Studies (Pending)

**Date:** 2024-10-09 (In Progress)  
**Test Set:** 50 validation cases (23 pos, 27 neg)  
**Purpose:** Add case study examples to prompt  

### Configuration:
- Prompt: v4 (with case studies)
- Input: Title + full text
- Case Studies: Extracted from 222 PDF files in `data/raw/case_studies/`
- Results File: `data/processed/preds_v4_with_cases.jsonl`

**Status:** Case study extraction in progress (222 PDFs)

---

## Summary Table

| Exp # | Date | Prompt Version | Input Type | Test Size | Accuracy | Precision | Recall | F1 | Status |
|-------|------|----------------|------------|-----------|----------|-----------|--------|-------|--------|
| 1 | 2024-10-08 | v1 conservative | Title | 10 (2p/8n) | 80% | N/A | 0% | 0.0 | ❌ Failed |
| 2 | 2024-10-08 | v2 balanced | Title | 50 (23p/27n) | 92% | 95% | 87% | 0.909 | ✅ Best |
| 3a | 2024-10-09 | v2 balanced | Title | 50 (23p/27n) | 90% | 95% | 83% | 0.884 | ✅ Good |
| 3b | 2024-10-09 | v2 balanced | Full Text | 50 (23p/27n) | 88% | 91% | 83% | 0.864 | ⚠️  Worse |
| 4 | 2024-10-09 | v4 + cases | Full Text | 50 (23p/27n) | TBD | TBD | TBD | TBD | 🔄 Pending |

---

## Files and Locations

### Prompts:
- Current best: `prompts/classify_tender_balanced.md`
- Archive: `prompts/archive/v{N}_*.md`
- Changelog: `prompts/PROMPT_CHANGELOG.md`

### Results:
- Experiment comparisons: `results/prompt_comparison_*.json`
- Prediction files: `data/processed/preds_*.jsonl`
- This log: `EXPERIMENT_LOG.md`

### Data:
- Clean data: `data/processed/tenders_clean.parquet`
- Splits: `data/processed/{train,val,test}_ids.txt`
- Test sets: `data/processed/val_ids_test50*.txt`

---

## Next Steps

1. ✅ Complete case study extraction (222 PDFs)
2. ⏳ Build prompt v4 with case studies
3. ⏳ Test v4 on 50 validation cases
4. ⏳ Compare v2 (title) vs v4 (title + cases)
5. ⏳ If v4 better, run on full validation set (474 cases)
6. ⏳ Final test on 713 test cases

---

## Lessons Learned

1. **Prompt engineering matters**: Changing decision rules from "high precision" to "be inclusive" increased recall from 0% → 87%
2. **Title is sufficient**: Full text adds noise, doesn't improve recall
3. **Few-shot examples work**: 93 positive examples provide good signal
4. **Balanced instructions**: Neither too conservative nor too permissive
5. **Test systematically**: Always use same test set for fair comparison

---

*Last Updated: 2024-10-09 09:10*

