# Prompt Version History

This document tracks all changes to the LLM classification prompt.

## Version 2: Balanced (2024-10-08) ✅ **CURRENT BEST**

**File:** `classify_tender_balanced.md`  
**Archive:** `archive/v2_classify_tender_balanced_2024-10-08.md`

### Performance (tested on 50 validation cases: 23 pos, 27 neg)
- **Accuracy:** 92.0% (46/50)
- **Precision:** 95.2% (20/21)
- **Recall:** 87.0% (20/23)
- **F1-Score:** 0.909

### Changes from v1:
1. ✅ Removed "prefer high precision, avoid over-inclusive" instruction (was too conservative)
2. ✅ Added explicit list of what economic research includes (surveys, cost analysis, impact studies, etc.)
3. ✅ Added "be inclusive for borderline cases" instruction
4. ✅ Clarified that even specialized domains (CO2, healthcare) are valid if they require economic analysis
5. ✅ Better structured decision rules with examples of what to select/reject

### Results:
- Caught 20/23 positives (vs 0/23 in v1)
- Only 1 false positive out of 27 negatives
- Much better balance between precision and recall

### Missed cases:
- "EuroAirport" (too vague title)
- "Marktdaten - Lieferung und Integration" (sounded like data delivery, not analysis)
- "Diskussionsbeiträge Familienpolitik" (discussion contributions, not study)

---

## Version 1: Conservative (2024-10-08) ❌ **DEPRECATED**

**File:** `classify_tender.md` (original)  
**Archive:** `archive/v1_classify_tender_conservative_2024-10-08.md`

### Performance (tested on 10 validation cases: 2 pos, 8 neg)
- **Accuracy:** 80.0% (8/10)
- **Precision:** N/A (no positives predicted)
- **Recall:** 0.0% (0/2)
- **F1-Score:** 0.0

### Issues:
- Too conservative - missed ALL positives
- Instruction to "prefer high precision, avoid over-inclusive Yes" made LLM reject valid economic research tenders
- Rejected tenders about surveys and cost analysis that should have been selected

### Why it failed:
- LLM interpreted "economic research" too narrowly
- Looked for exact keyword matches instead of understanding broader themes
- The "avoid over-inclusive" instruction biased it toward "No"

---

## How to Use This Changelog

### When creating a new prompt version:

1. **Copy the current best prompt:**
   ```bash
   cp prompts/classify_tender_balanced.md prompts/classify_tender_v3.md
   ```

2. **Make your changes** to the new file

3. **Test it** on validation cases:
   ```bash
   # Use your test script with the new prompt
   python scripts/test_new_prompt.py --prompt prompts/classify_tender_v3.md
   ```

4. **Archive the new version:**
   ```bash
   DATE=$(date +%Y-%m-%d)
   cp prompts/classify_tender_v3.md prompts/archive/v3_classify_tender_description_${DATE}.md
   ```

5. **Update this changelog** with:
   - Version number and date
   - Performance metrics (accuracy, precision, recall, F1)
   - What changed from previous version
   - Test results
   - Any issues or missed cases

6. **Commit to git:**
   ```bash
   git add prompts/
   git commit -m "tenders-llm: add prompt v3 with [describe changes] - [key metric]"
   git push
   ```

---

## Testing Protocol

Always test new prompts on the same validation set for fair comparison:

```bash
# Standard test set (50 cases: 23 pos, 27 neg)
python scripts/test_pipeline_quick.py --prompt prompts/YOUR_PROMPT.md --ids data/processed/val_ids_test50.txt
```

### Minimum metrics to report:
- Accuracy
- Precision (of predicted positives)
- Recall (of actual positives)
- F1-Score
- Number of false positives
- Number of false negatives
- Sample of missed cases with reasoning

---

## Quick Reference

| Version | Date | Accuracy | Precision | Recall | F1 | Status |
|---------|------|----------|-----------|--------|-------|--------|
| v1 (conservative) | 2024-10-08 | 80.0% | N/A | 0.0% | 0.0 | ❌ Deprecated |
| v2 (balanced) | 2024-10-08 | 92.0% | 95.2% | 87.0% | 0.909 | ✅ Current |

---

## Notes

- Always test on the same validation split to ensure fair comparison
- Archive old versions before making changes
- Document the reasoning behind each change
- Keep track of which prompt version was used for full pipeline runs

