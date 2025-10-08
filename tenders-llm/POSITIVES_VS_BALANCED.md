# Positives-Only vs Balanced Few-Shot Examples

## Current Approach: Positives-Only (93 examples)

### What the LLM sees:
```
## Examples of Previously Selected Tender Titles
✓ Regulierungsfolgenabschätzung zum Umsatzschwellenwert...
✓ Analyse der Preise und der Qualität in der Hörgeräteversorgung
✓ Erwerbstätigkeit über das ordentliche Rentenalter hinaus
✓ [90 more positive examples]
```

### Characteristics:
- **Prompt tokens:** ~30k
- **Cost per call:** ~$0.0045
- **Total cost (1,187 calls):** ~$5.34
- **LLM learns:** "Select tenders that look like these"

### When this works well:
- When positives have clear common themes
- When negatives are obviously different (e.g., construction vs economic research)
- With strong models like GPT-4 that can infer boundaries

### When this might fail:
- If there are "near-miss" negatives (economic topics but wrong type)
- If the LLM is too permissive and selects too many

---

## Alternative: Balanced Few-Shot (93 pos + 93 neg)

### What the LLM sees:
```
## Examples of Previously Selected Tender Titles
✓ Regulierungsfolgenabschätzung zum Umsatzschwellenwert...
✓ Analyse der Preise und der Qualität in der Hörgeräteversorgung
✓ [91 more positive examples]

## Examples of Previously REJECTED Tender Titles (outside scope)
✗ IT-Dienstleistungen im Projekt DaZu
✗ Projektunterstützung Workplace 2024
✗ [91 more negative examples]
```

### Characteristics:
- **Prompt tokens:** ~50k (+67%)
- **Cost per call:** ~$0.0075 (+67%)
- **Total cost (1,187 calls):** ~$8.90 (+67%)
- **LLM learns:** "Select these, NOT these"

### When this works well:
- When there are hard-to-distinguish negatives
- When you need higher precision (fewer false positives)
- When the decision boundary is subtle

### When this might fail:
- If negatives are poorly chosen (not representative)
- If the LLM becomes too conservative (too many false negatives)
- Higher cost without guarantee of better performance

---

## Recommendation: Test Both on Validation Set

### Step 1: Run positives-only (current)
```bash
# Already done - prompt is built
python scripts/04_llm_predict.py  # uses prompts/classify_tender.md
python scripts/05_eval.py
```

### Step 2: Check validation results
- If **Precision < 0.5**: Too many false positives → try adding negatives
- If **Recall < 0.5**: Too many false negatives → keep positives-only or add more positives
- If **both are good**: Keep positives-only (cheaper, simpler)

### Step 3: If needed, run with negatives
```bash
# Rebuild prompt with negatives
INCLUDE_NEGATIVES=1 python scripts/03_build_prompt_with_negatives.py

# Update 04_llm_predict.py to use new prompt path
# Then re-run predictions on validation set
```

### Step 4: Compare on validation
| Metric | Positives-Only | Balanced | Winner |
|--------|---------------|----------|--------|
| Precision@100 | ? | ? | ? |
| Recall@100 | ? | ? | ? |
| PR-AUC | ? | ? | ? |
| Cost | $2.13 (val only) | $3.56 | Positives-only |

### Step 5: Use best on test set

---

## Summary

**Start with positives-only** because:
1. It's the standard approach for GPT-4 models
2. It's 40% cheaper
3. You can always add negatives later if precision is poor
4. Most successful few-shot systems use positives-only

**Add negatives only if**:
1. Validation shows too many false positives
2. There are clear "hard negative" patterns you want to teach
3. The extra cost (~$3.50) is justified by improved precision

---

## Quick Test (Optional)

Want to see the difference? Run a quick A/B test on 20 validation items:

```bash
# Test 1: Positives-only (current)
head -n 20 data/processed/val_ids.txt > data/processed/val_ids_test20.txt
python scripts/04_llm_predict.py  # modify to use val_ids_test20
# Check precision/recall

# Test 2: With negatives
INCLUDE_NEGATIVES=1 python scripts/03_build_prompt_with_negatives.py
# Update 04_llm_predict.py to use prompts/classify_tender_with_negatives.md
python scripts/04_llm_predict.py  # run again on same 20
# Compare results
```

Cost: ~$0.18 total (20 × 2 approaches × $0.0045)
Time: ~20 minutes (with rate limits)

