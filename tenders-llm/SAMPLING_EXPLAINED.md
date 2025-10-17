# Sampling Methods: Previous vs New - Detailed Explanation

## 🎯 The Key Difference

### Previous Experiments (Oct 2024)
**Sample:** 50 validation cases with **23 positives, 27 negatives**  
**Positive rate:** 46%  
**Source:** `data/processed/val_ids_test50_fulltext.txt` (file doesn't exist anymore)  
**Selection method:** **Unknown/Unclear**

### My New Experiments (Oct 2025)
**Sample:** 50 validation cases with **2 positives, 48 negatives**  
**Positive rate:** 4%  
**Source:** `data/processed/val_ids_test50.txt` (created via stratified sampling)  
**Selection method:** **Stratified random (seed=42)**

---

## 📊 Why This Matters HUGELY

### The Math Problem

**Dataset reality:**
- Total tenders: 4,748
- Positives: 162 (3.4%)
- Negatives: 4,586 (96.6%)

**Validation set (474 cases):**
- Expected positives: ~16 (3.4%)
- Expected negatives: ~458 (96.6%)

---

### Previous Sample (23 positives in 50)

**Composition:**
```
23 positives / 50 total = 46% positive rate
```

**This is 13.5x HIGHER than reality!**

**How this could happen:**
1. **Manually cherry-picked** - Selected 23 known positives + 27 negatives
2. **Oversampled positives** - To have enough positive examples to test
3. **Unclear selection** - File doesn't exist, can't verify

**Why this is problematic:**

```
Problem: Testing on 46% positive is MUCH EASIER than reality (3.4%)

Real world (production):
- 96.6% of tenders are negative
- Main challenge: Avoid false positives on huge negative class
- Even 1% FP rate on 4,586 negatives = 46 false positives!

Previous test (46% positive):
- Only 54% of cases are negative (27 negatives)
- Much easier to avoid false positives
- 1 FP out of 27 = looks great!
- But doesn't test the hard problem!
```

**Example:**
```
Previous test results:
- 19 true positives found (out of 23 available)
- 1 false positive (out of 27 negatives tested)
- Precision: 19/20 = 95% ✓ Looks great!

But extrapolating to reality:
- If same FP rate (1/27 = 3.7%):
- On 458 negatives: 458 × 0.037 = 17 false positives
- On 16 true positives: 16 TP + 17 FP = 33 predictions
- Precision: 16/33 = 48% ✗ Actually much worse!
```

---

### My New Sample (2 positives in 50)

**Composition:**
```
2 positives / 50 total = 4% positive rate
```

**This matches reality (3.4%)!**

**How this was created:**
```python
from sklearn.model_selection import train_test_split

# Stratified sampling maintains class distribution
sample = train_test_split(
    val_df,
    train_size=50,
    stratify=val_df['label'],  # Keep same positive rate!
    random_state=42
)

# Result: 2 positives, 48 negatives (4% positive)
```

**Why this is better:**

```
Representative of production:
- 96% of test cases are negative (48/50)
- Tests the REAL challenge: avoiding FPs on huge negative class
- Results extrapolate to reality

Real-world equivalent:
- Same 96% negative rate
- If 2 FP on 48 negatives = 4.2% FP rate
- On 458 full val negatives: 458 × 0.042 = 19 FPs (realistic estimate)
```

**Example:**
```
My test results (with negative examples):
- 2 true positives found (out of 2 available) ✓ 100% recall
- 2 false positives (out of 48 negatives tested)
- Precision: 2/4 = 50%

Extrapolating to full validation:
- On 458 negatives: 458 × (2/48) = 19 FPs (expected)
- On 16 true positives: 16 TP + 19 FP = 35 predictions
- Precision: 16/35 = 46% (realistic!)
```

---

## 🔍 Direct Comparison (Why Results Look Different)

### Previous Experiment #2 (Oct 2024)
```
Sample: 50 cases, 23 positives (46%)
Baseline (title-only):
- Accuracy: 92%
- Precision: 95% (19 TP, 1 FP)
- Recall: 87% (19/23 positives found)

Why precision looks high:
- Only 27 negatives to test
- 1 FP out of 27 = 96% correct on negatives
- Easy because negative class is small!
```

### My Experiment (Oct 2025)
```
Sample: 50 cases, 2 positives (4%)
Baseline (title-only):
- Accuracy: 94%
- Precision: 40% (2 TP, 3 FP)
- Recall: 100% (2/2 positives found)

Why precision looks lower:
- 48 negatives to test (1.8x more than before)
- 3 FP out of 48 = 94% correct on negatives
- Harder because negative class is realistic size!
```

---

## 🎓 Which Sample is More Valid?

### For Understanding Model Behavior: Previous Sample ✓

**Advantages:**
- More positives (23) = better signal
- Can see which types of positives get missed
- Error analysis easier

**Disadvantages:**
- Not representative of production
- Precision estimate is optimistic
- Doesn't test FP challenge on large negative class

---

### For Production Estimation: My New Sample ✓

**Advantages:**
- Matches real distribution (4% vs 3.4%)
- Tests realistic FP challenge (48 negatives)
- Results extrapolate to production
- Statistically valid

**Disadvantages:**
- Only 2 positives = high variance
- Can't do detailed error analysis
- One missed positive = 50% recall drop!

---

## 💡 The Ideal Approach

### Best of Both Worlds

**Option 1: Use BOTH samples**
```
Enriched sample (previous):
- 50 cases with ~20-25 positives
- For: Understanding behavior, error analysis
- Use for: Development, prompt tuning

Representative sample (new):
- 50 cases with 2-3 positives (stratified)
- For: Realistic performance estimation
- Use for: Final validation, comparison
```

**Option 2: Larger stratified sample**
```
100-150 cases (stratified):
- ~5-7 positives (enough for analysis)
- ~95-145 negatives (realistic challenge)
- Best of both: signal + realism
```

---

## 📊 Comparison Table

| Aspect | Previous Sample | New Sample | Which is Better? |
|--------|----------------|------------|------------------|
| **Size** | 50 cases | 50 cases | Tie |
| **Positives** | 23 (46%) | 2 (4%) | **New** (representative) |
| **Negatives** | 27 (54%) | 48 (96%) | **New** (tests FP challenge) |
| **Selection** | Unknown | Stratified (seed=42) | **New** (reproducible) |
| **Realistic** | No (too easy) | Yes (matches reality) | **New** |
| **Error analysis** | Easy (23 samples) | Hard (2 samples) | **Previous** |
| **Precision estimate** | Optimistic | Realistic | **New** |
| **Recall estimate** | Good signal | High variance | **Previous** |

---

## 🎯 What This Means for Your Results

### Previous Result (95% precision)

**On enriched sample (23 pos, 27 neg):**
- 95% precision looks great!
- **But:** Only tested on 27 negatives

**Estimated real precision:**
```
If same FP rate (1/27 = 3.7%):
Real validation (16 pos, 458 neg):
- 458 × 0.037 = 17 FPs
- 16 TP + 17 FP = 33 predictions
- Precision: 16/33 = 48% (not 95%!)
```

### My Result (50% precision with negatives)

**On representative sample (2 pos, 48 neg):**
- 50% precision on realistic distribution
- Tested on 48 negatives (closer to reality)

**Estimated real precision:**
```
If same FP rate (2/48 = 4.2%):
Real validation (16 pos, 458 neg):
- 458 × 0.042 = 19 FPs
- 16 TP + 19 FP = 35 predictions  
- Precision: 16/35 = 46% (close to 50%!)
```

**My estimate is more realistic but uses different sample!**

---

## ✅ To Make Fair Comparison

We need to test **on the SAME sample**. But the previous sample file (`val_ids_test50_fulltext.txt`) doesn't exist.

**Options:**
1. **Accept they're different** - Document both as valid for different purposes
2. **Use larger sample** - 100-150 cases (best of both worlds)
3. **Test both approaches on same new sample** - Fair head-to-head

---

**Bottom line: Yes, my new sample only has 2 positives (more realistic) vs previous 23 (easier testing). Results are NOT directly comparable!** 🎯

Want me to create a fair comparison by testing both approaches on the same sample?
