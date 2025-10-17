# Quick Experimentation Guide

You already have scripts optimized for fast iteration! No need to run the full expensive pipeline.

---

## 🚀 Fast Iteration Scripts (ALREADY EXIST)

### 1️⃣ `test_pipeline_quick.py` - Sanity Check

**Use when:** "Does my change break anything?"

```bash
python scripts/test_pipeline_quick.py
```

**What it does:**
- ✅ Tests on **10 validation cases** (first 10 from val_ids.txt)
- ✅ **Time: ~5 minutes** (10 × 25 sec)
- ✅ **Cost: ~$0.20**
- ✅ Shows sample results + summary

**Perfect for:**
- Quick sanity check after changing prompt
- Verifying pipeline still works
- Debugging issues

---

### 2️⃣ `test_prompt_versions.py` - Compare Approaches

**Use when:** "Which approach works better?"

```bash
python scripts/test_prompt_versions.py
```

**What it does:**
- ✅ Tests on **50 validation cases** (same set each time)
- ✅ Compares **2 versions** side-by-side
- ✅ **Time: ~20 minutes** (50 × 2 × 3 sec)
- ✅ **Cost: ~$2**
- ✅ Saves comparison to `results/prompt_comparison_TIMESTAMP.json`

**Currently compares:**
- v2: Title only
- v3: Full text

**Perfect for:**
- Comparing two approaches fairly
- Title vs full text vs XML extraction
- Different prompts
- Different extraction methods

---

### 3️⃣ `test_xml_extraction.py` - **NEW!** Compare XML Methods

**Use when:** "Which XML extraction method works best?"

```bash
python scripts/test_xml_extraction.py
```

**What it does:**
- ✅ Creates **20-case dev sample** (stratified)
- ✅ Tests **3 extraction methods**:
  1. Baseline (title only)
  2. XML description only
  3. XML description + deliverables
- ✅ **Time: ~10 minutes** (20 × 3 × 3 sec)
- ✅ **Cost: ~$1**
- ✅ Compares all three approaches

**Perfect for:**
- Testing XML extraction ideas quickly
- Comparing multiple approaches in one run
- Before committing to expensive full evaluation

---

## 📊 Comparison: Scripts Overview

| Script | Cases | Versions | Time | Cost | Use Case |
|--------|-------|----------|------|------|----------|
| `test_pipeline_quick.py` | 10 | 1 | 5 min | $0.20 | Sanity check |
| `test_xml_extraction.py` | 20 | 3 | 10 min | $1.00 | Compare XML methods |
| `test_prompt_versions.py` | 50 | 2 | 20 min | $2.00 | Compare 2 approaches |
| **Full pipeline** | 475 | 1 | 3 hrs | $10 | Final validation |

---

## ⚡ Recommended Workflow

### Phase 1: Quick Iteration (Use Dev Scripts!)

```bash
# Day 1: Try idea #1
# 1. Implement XML extraction
# 2. Quick test
python scripts/test_pipeline_quick.py  # 5 min
# 3. Looks good? Test 3 methods
python scripts/test_xml_extraction.py  # 10 min

# Day 2: Try idea #2
# 1. Modify extraction
# 2. Quick test again
python scripts/test_pipeline_quick.py  # 5 min
python scripts/test_xml_extraction.py  # 10 min

# Try 5-10 ideas in one week!
# Total: 50-100 minutes, $5-10
```

### Phase 2: Validation (Use Full Scripts)

```bash
# After finding winner in Phase 1:
# Run winner on larger validation set

export EXPERIMENT_NAME="exp_xml_winner_validation"
python scripts/04_llm_predict.py  # 100 cases, 40 min, $2
python scripts/05_eval_with_mlflow.py
```

### Phase 3: Final Test (Once)

```bash
# Only after finalizing approach:
export EXPERIMENT_NAME="exp_final_test"
python scripts/04_llm_predict.py --split test  # 200 cases, 1 hr, $4
python scripts/05_eval_with_mlflow.py
```

---

## 🎯 Your Current Situation

### What You Have (Already Built!)

✅ **Quick sanity check:** `test_pipeline_quick.py` (10 cases, 5 min)
✅ **Comparison tool:** `test_prompt_versions.py` (50 cases, 20 min)
✅ **Full pipeline:** Individual scripts (475 cases, 3 hrs)
✅ **NEW: XML tester:** `test_xml_extraction.py` (20 cases, 10 min)

### What You Should Use for Experimentation

```bash
# For rapid testing: test_pipeline_quick.py (5 min)
# For comparing 2-3 methods: test_xml_extraction.py (10 min)
# For validation: Use full pipeline (when ready)
```

---

## 💡 How to Modify for Your Experiments

### Example: Test New Extraction Method

**Edit `test_xml_extraction.py`:**

```python
# Add new extraction method
elif extraction_method == "my_new_method":
    # Your custom extraction logic
    context = extract_my_way(row['full_text'])

# Then in main(), add test:
metrics_new = run_test(
    prompt_path="prompts/classify_tender.md",
    test_ids_path=dev_sample_path,
    output_path="data/processed/preds_new_method_dev.jsonl",
    extraction_method="my_new_method",
    version_name="My New Method"
)
```

Run it:
```bash
python scripts/test_xml_extraction.py
# Now compares 4 methods instead of 3!
```

---

## 🎯 Bottom Line

**You don't need a "main" script for experimentation!**

**Use these instead:**
- 🏃 **Quick tests:** `test_pipeline_quick.py` (5 min)
- 🔬 **Experiments:** `test_xml_extraction.py` (10 min) ← **Use this!**
- 🎯 **Comparisons:** `test_prompt_versions.py` (20 min)
- 🚀 **Full eval:** `run_pipeline.py --llm-only` (3 hrs) ← Only when finalizing

**For your XML extraction experiments, use `test_xml_extraction.py`** - it runs 3 methods on 20 cases in 10 minutes for $1. Perfect for rapid iteration!

---

**Next step: Implement actual XML extraction logic** (parsing the XML to get relevant sections only)

