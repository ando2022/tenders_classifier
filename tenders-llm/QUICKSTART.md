# Tenders-LLM Quick Start

## 🚀 Fast Experimentation (No MLflow Needed!)

You have everything you need for rapid testing already built.

---

## ⚡ 3-Step Workflow

### Step 1: Sanity Check (5 min, $0.20)

After making any change to your code:

```bash
python scripts/test_pipeline_quick.py
```

**Tests:** 10 validation cases  
**Shows:** Sample predictions + accuracy summary  
**Cost:** ~$0.20

**Use when:**
- Changed prompt
- Modified extraction logic  
- Want to verify nothing broke

---

### Step 2: Compare Approaches (10 min, $1)

Test different XML extraction methods:

```bash
python scripts/test_xml_extraction.py
```

**Tests:** 20 cases × 3 extraction methods
- Method 1: Title only (baseline)
- Method 2: XML description only (clean)
- Method 3: XML description + deliverables

**Shows:** Side-by-side comparison of all 3  
**Cost:** ~$1

**Use when:**
- Testing new extraction approach
- Comparing multiple strategies
- Daily experimentation

---

### Step 3: Validate Winner (Optional, 40 min, $2)

Once you find a promising approach:

```bash
python scripts/test_prompt_versions.py
```

**Tests:** 50 cases × 2 versions  
**Shows:** Detailed comparison with metrics  
**Cost:** ~$2

**Use when:**
- You have a winner from Step 2
- Want higher confidence
- Need more data points

---

## 📊 What's Available

| Script | Cases | Time | Cost | Purpose |
|--------|-------|------|------|---------|
| `test_pipeline_quick.py` | 10 | 5 min | $0.20 | ✅ **Daily sanity check** |
| `test_xml_extraction.py` | 20×3 | 10 min | $1 | ✅ **Compare methods** |
| `test_prompt_versions.py` | 50×2 | 20 min | $2 | Validate finalists |
| Full pipeline | 475 | 3 hrs | $10 | Final evaluation (once) |

---

## 🎯 Example: Testing XML Extraction

### Monday Morning (10 min total)

```bash
# 1. Quick sanity check (5 min)
python scripts/test_pipeline_quick.py

Output:
  Total: 10
  Actual positives: 1
  Predicted Yes: 2
  ✓ Looks reasonable!

# 2. Compare XML methods (10 min)
python scripts/test_xml_extraction.py

Output:
  ============================================================
  XML EXTRACTION COMPARISON
  ============================================================
  Method                      Accuracy  Precision  Recall    
  ------------------------------------------------------------
  Baseline (Title Only)       85.0%     80.0%      75.0%     
  XML Description Only        90.0%     90.0%      80.0%  ← Better!
  XML Desc + Deliverables     88.0%     85.0%      82.0%     
  
  🏆 Best: XML Description Only (F1=0.848)

Decision: Use "description_only" method!
```

---

## 📝 Output Files

Results are saved to simple JSON files:

```bash
data/processed/
├── preds_quick_test.jsonl           # From test_pipeline_quick
├── preds_baseline_dev.jsonl         # From test_xml_extraction  
├── preds_xml_desc_dev.jsonl         # From test_xml_extraction
└── preds_xml_full_dev.jsonl         # From test_xml_extraction

results/
└── xml_extraction_comparison_TIMESTAMP.json  # Metrics comparison
```

**View results:**
```bash
# See predictions
cat data/processed/preds_xml_desc_dev.jsonl | head -3

# See comparison
cat results/xml_extraction_comparison_20251009_150000.json
```

---

## 🛠️ What I Built For You

### New Components

**1. XML Extractor** (`utils/xml_extractor.py`)
```python
from utils.xml_extractor import smart_extract

# Extract only project description
text = smart_extract(xml_text, method="description_only")

# Extract description + deliverables
text = smart_extract(xml_text, method="desc_deliverables")
```

**2. XML Test Script** (`scripts/test_xml_extraction.py`)
- Tests 3 extraction methods on 20 cases
- Creates stratified dev sample automatically
- Compares all methods side-by-side

**3. Pipeline Orchestrator** (`run_pipeline.py`)
- Run full pipeline when needed
- Can run individual steps

---

## 🎯 Recommended Daily Workflow

### Morning: Test Your Ideas

```bash
# Implement something new
nano utils/xml_extractor.py

# Test it (5 min)
python scripts/test_pipeline_quick.py
```

### Afternoon: Compare Approaches

```bash
# Compare 3 methods (10 min)
python scripts/test_xml_extraction.py

# See winner, iterate
```

### End of Week: Pick Winner

```bash
# Review all results
cat results/xml_extraction_comparison_*.json

# Note best approach
echo "## Week 1: Winner = XML description only (90%)" >> EXPERIMENT_LOG.md
```

---

## 💰 Cost Tracking

### Typical Week of Experimentation

```
Monday:    5 quick tests × $0.20 = $1.00
Tuesday:   3 XML tests × $1.00 = $3.00
Wednesday: 2 quick tests × $0.20 = $0.40
Thursday:  2 XML tests × $1.00 = $2.00
Friday:    1 validation × $2.00 = $2.00

Total: ~$8.50 for ~15 experiments
```

**Much cheaper than running full pipeline every time!**

---

## 🚀 Next Steps

1. **Try the quick test:**
   ```bash
   python scripts/test_pipeline_quick.py
   ```

2. **Test XML extraction:**
   ```bash
   python scripts/test_xml_extraction.py
   ```

3. **Compare results** and iterate!

---

**No MLflow needed for experimentation - the simple scripts are perfect!** 🎯

Use MLflow later when you're ready to deploy to production.

