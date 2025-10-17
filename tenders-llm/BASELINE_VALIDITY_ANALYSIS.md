# Baseline Validity Analysis

## 🚨 CRITICAL ISSUE: Incomplete Evaluation

### What the Code Says

**From `02_make_splits.py`:**
```python
Expected splits:
- Train: 75% = ~3,561 tenders (~121 positives)
- Val:   10% = ~475 tenders (~16 positives)  
- Test:  15% = ~712 tenders (~24 positives)
Total: 4,748 tenders (162 positives)
```

### What Was Actually Evaluated

**From `EXPERIMENT_LOG.md`:**
```
Experiment #1: 10 validation cases (2 pos, 8 neg)   ← 2% of val set!
Experiment #2: 50 validation cases (23 pos, 27 neg) ← 11% of val set!
Experiment #3: 50 validation cases (23 pos, 27 neg) ← Same 50!
```

### ❌ The Problem

| What Should Happen | What Actually Happened | Issue |
|-------------------|----------------------|-------|
| Evaluate on 475 val cases | Evaluated on 50 cases | **Only 11% coverage** |
| ~16 val positives | 23 positives in subset | **Not representative!** |
| Test on 712 cases | **Not tested yet!** | **No final evaluation** |
| All 162 positives used | Only subset seen | **Incomplete coverage** |

---

## 🔍 Detailed Analysis

### Issue #1: Small Sample Size (Selection Bias)

**The 50-case test set:**
```
23 positives / 50 total = 46% positive rate

Expected validation set:
~16 positives / 475 total = 3.4% positive rate
```

**This is HIGHLY UNREPRESENTATIVE!**

The test set is:
- ✅ Easier than reality (46% positive vs 3.4% baseline)
- ✅ Biased toward positives (13.5x over-represented)
- ✅ Not testing edge cases (missing 452 negatives)
- ✅ Not generalizable to production

**Real-world impact:**
```
On 50-case subset: 95% precision (19/20 predictions)
On full 475 val set: Could be 70% precision (many more FPs)
```

### Issue #2: Cherry-Picking

**Where did the 50 cases come from?**

Looking at the code, I don't see explicit creation of `val_ids_test50_fulltext.txt`.

Possibilities:
1. **Manually selected** → High risk of bias
2. **First 50 from val set** → Temporal bias (older tenders)
3. **Random sample** → Better, but still too small

**Problem:** You're tuning on this subset, which means:
- Prompt optimized for these 50 cases
- May not generalize to other 425 val cases
- Definitely won't generalize to 712 test cases

### Issue #3: Train/Val/Test Contamination Risk

**Where are the positives?**

Expected split of 162 positives:
```
Train: ~121 positives (75%)
Val:   ~16 positives (10%)
Test:  ~24 positives (15%)
```

But the 50-case test has 23 positives!

**This means:**
- Either: The 50 cases include almost ALL validation positives (23/16)
- Or: The split wasn't stratified properly
- Or: Test cases are leaking into validation

**Risk:** If positives are similar, you might be testing on cases too similar to training!

### Issue #4: No Final Test Evaluation

**From EXPERIMENT_LOG:**
```
Experiment #2: Val set (50 cases) → 92% accuracy
Experiment #3: Val set (50 cases) → 88-90% accuracy

Test set (712 cases): NOT EVALUATED YET!
```

**This is CRITICAL:**
- You've tuned the prompt on validation set
- You changed from "conservative" to "balanced" based on val performance
- You haven't tested if this generalizes to unseen test data!

**The "92% accuracy" might be:**
- ✅ Real performance: 92%
- ❌ Overfit to 50 cases: Actually 75% on test
- ❌ Biased by easy subset: Actually 80% on full val

---

## 📊 What You Should Have

### Proper Evaluation Strategy

```
Step 1: Initial Split (DONE)
├─ Train: 3,561 tenders (121 pos) ✓
├─ Val:   475 tenders (16 pos)     ✓ Created but not fully used!
└─ Test:  712 tenders (24 pos)     ✓ Created but never used!

Step 2: Prompt Development (PARTIALLY DONE)
├─ Extract few-shot examples from train ✓
├─ Build initial prompt ✓
└─ Test on SMALL val subset (10 cases) ✓ Sanity check only!

Step 3: Prompt Tuning (PROBLEMATIC)
├─ Experiment #1: 10 cases (sanity check) ✓
├─ Experiment #2: 50 cases ← STOPPED HERE
└─ Should evaluate on FULL val (475) ✗ MISSING!

Step 4: Final Evaluation (NOT DONE)
└─ Test on full test set (712) ✗ NEVER RUN!
```

### What's Missing

**1. Full Validation Evaluation**
```bash
# Should have run:
python scripts/04_llm_predict.py  # On ALL 475 val cases
python scripts/05_eval.py

# Results:
preds_val.jsonl → 475 predictions
Metrics on full distribution (3.4% positive, not 46%)
```

**2. Final Test Evaluation**
```bash
# Should run ONCE, after finalizing prompt:
python scripts/04_llm_predict.py  # On ALL 712 test cases
python scripts/05_eval.py

# Results:
preds_test.jsonl → 712 predictions
True unbiased performance estimate
```

**3. Stratified Validation**
```bash
# If using subset, must stratify:
- Keep 3.4% positive rate (not 46%!)
- Random sample, not first N
- Document how subset was created
```

---

## ⚠️ Impact on Your Conclusions

### Conclusion #1: "Full text hurt performance"
**Status:** ⚠️ **Partially Valid**

- Evidence: 50-case test shows decline (90% → 88%)
- Concern: Might not hold on full 475 val set
- Risk: Different result on 712 test cases

**Recommendation:** Re-run on full val/test before concluding

### Conclusion #2: "Title-only gets 92% accuracy"
**Status:** ⚠️ **Uncertain**

- Evidence: 92% on 50 cases (23 pos, 27 neg)
- Reality: 50 cases are EASIER (46% positive vs 3.4%)
- Prediction: Likely lower on full val set (more negatives)

**Expected adjustment:**
```
50-case subset: 92% accuracy (easy, balanced)
Full 475 val:   85-90% accuracy (harder, imbalanced)
Full 712 test:  80-88% accuracy (realistic)
```

### Conclusion #3: "95% precision is excellent"
**Status:** ⚠️ **HIGHLY Uncertain**

```
On 50 cases (23 pos, 27 neg):
  Predicted 20 "Yes" → 19 correct = 95% precision
  1 FP out of 27 negatives = 96% of negatives classified correctly

On full 475 val (~16 pos, ~459 neg):
  If same FP rate (4%): 459 * 0.04 = 18 FPs!
  If 16 TP + 18 FP = 34 predicted Yes
  Precision: 16/34 = 47%! ← MUCH WORSE!
```

**This is the BIGGEST RISK!**

With highly imbalanced data (3.4% positive):
- **Hard part:** Avoiding false positives on 96.6% negatives
- **Your test:** Only had 27 negatives (54% of test set)
- **Reality:** Will face 459 negatives (96.6% of val set)

Even with 1% FP rate:
```
459 negatives * 0.01 FP rate = 5 FPs
16 true positives found
Precision: 16 / (16 + 5) = 76% (not 95%!)
```

---

## 🎯 What This Means for Your Next Steps

### Before Adding XML Extraction

**You MUST establish a true baseline:**

```bash
# 1. Run on FULL validation set
export EXPERIMENT_NAME="exp_20251009_baseline_full_val"
export EXPERIMENT_DESCRIPTION="Baseline (title-only) on FULL 475 validation cases"
python scripts/04_llm_predict.py --split val
python scripts/05_eval_with_mlflow.py

# 2. Reserve test set for final evaluation
# (Don't touch test until you've finalized approach)

# 3. Compare:
#    - 50-case subset: 92% accuracy, 95% precision
#    - Full 475 val:   ??% accuracy, ??% precision
```

### Expected Reality Check

**Pessimistic scenario:**
```
50 cases: 92% acc, 95% prec, 83% rec
475 val:  85% acc, 75% prec, 85% rec ← More FPs on larger negative set
```

**Optimistic scenario:**
```
50 cases: 92% acc, 95% prec, 83% rec
475 val:  90% acc, 88% prec, 85% rec ← Small drop, still good
```

**Most likely:**
```
50 cases: 92% acc, 95% prec, 83% rec
475 val:  87% acc, 82% prec, 84% rec ← Moderate drop
```

---

## ✅ Proper Experiment Protocol Going Forward

### Phase 1: Establish True Baseline (NOW)

```bash
# Run on full validation set (475 cases)
EXPERIMENT_NAME="baseline_title_only_full_val"
python scripts/04_llm_predict.py  # All val cases
python scripts/05_eval_with_mlflow.py

# Track in MLflow:
# - data.val_size: 475
# - val.accuracy: ??
# - val.precision: ??
# - val.recall: ??
```

### Phase 2: XML Extraction Experiments (AFTER BASELINE)

```bash
# Only after knowing true baseline:
EXPERIMENT_NAME="xml_extraction_description_only"
python scripts/extract_xml.py --method description
python scripts/04_llm_predict.py
python scripts/05_eval_with_mlflow.py

# Compare against TRUE baseline
```

### Phase 3: Final Evaluation (ONCE)

```bash
# After selecting best approach:
# Run ONCE on test set (712 cases)
EXPERIMENT_NAME="final_test_evaluation"
python scripts/04_llm_predict.py --split test
python scripts/05_eval_with_mlflow.py

# This is your REAL performance estimate
```

---

## 📋 Action Items

### Immediate (Before Any XML Work)

- [ ] **Run baseline on full 475 validation cases**
  ```bash
  python scripts/04_llm_predict.py  # Ensure uses ALL val_ids.txt
  ```

- [ ] **Check for data leakage**
  ```bash
  # Verify splits are correct:
  python scripts/02_make_splits.py
  # Check outputs match expected sizes
  ```

- [ ] **Document 50-case subset creation**
  ```bash
  # How was val_ids_test50_fulltext.txt created?
  # Was it random? First 50? Cherry-picked?
  ```

- [ ] **Compare 50-case vs full val performance**
  ```bash
  # Are they similar? If not, which is representative?
  ```

### Before Production

- [ ] **Run final test evaluation** (once only)
  ```bash
  # After approach is finalized
  python scripts/04_llm_predict.py --split test
  ```

- [ ] **Reserve test set properly**
  ```bash
  # Never tune on test set
  # Only evaluate once at the end
  ```

---

## 🎓 Lessons

### What Went Wrong

1. **Premature optimization:** Tuning on tiny subset (50 cases)
2. **Unrepresentative sample:** 46% positive vs 3.4% baseline
3. **No test evaluation:** Never validated generalization
4. **Over-confidence:** "95% precision" may be artifact of small sample

### What To Do Differently

1. **Always use full validation set** for evaluation
2. **Keep class distribution** when sampling (stratified)
3. **Reserve test set** for final evaluation only
4. **Report confidence intervals** on metrics (small N = high variance)

---

## 🚨 Bottom Line

**Your "92% accuracy, 95% precision" baseline is UNCERTAIN because:**

1. ❌ Evaluated on only 50 cases (11% of validation set)
2. ❌ Sample is unrepresentative (46% positive vs 3.4% expected)
3. ❌ Never tested on full validation set (475 cases)
4. ❌ Never tested on test set (712 cases)
5. ❌ High risk of overoptimism due to small sample size

**Before adding XML extraction, you MUST:**
- ✅ Run on full 475 validation cases
- ✅ Get realistic performance estimate
- ✅ Understand true baseline
- ✅ Then compare XML approaches against TRUE baseline

**Cost:** ~$10-20 for 475 OpenAI API calls
**Value:** Knowing if your approach actually works!

---

**Status:** ⚠️ **Baseline NOT yet established**  
**Next Step:** Run full validation evaluation before proceeding

