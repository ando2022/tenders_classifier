# Tenders-LLM Architecture with Experiment Tracking

## Overview

Complete MLOps-ready architecture for tracking experiments, managing data dependencies, and deploying to production.

---

## System Components

```
┌─────────────────────────────────────────────────────────────┐
│ DATA SOURCES                                                │
└─────────────────────────────────────────────────────────────┘
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
    ▼                    ▼                    ▼
┌─────────┐      ┌─────────────┐      ┌──────────────┐
│ SIMAP   │      │  Services   │      │  Keywords    │
│ Tenders │      │  (37 items) │      │  (Optional)  │
│ 4,748   │      └─────────────┘      └──────────────┘
└─────────┘              │                    │
    │                    │                    │
    │                    ▼                    ▼
    │            ┌──────────────────────────────┐
    │            │ EXPERIMENT TRACKER           │
    │            │ - Compute hashes             │
    │            │ - Detect changes             │
    │            │ - Version metadata           │
    │            └──────────────────────────────┘
    │                    │
    ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│ MLFLOW TRACKING                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Parameters Logged:                                         │
│  ✓ data.total_tenders         = 4748                       │
│  ✓ data.positive_tenders      = 162                        │
│  ✓ data.data_hash             = a3f5c2...                  │
│  ✓ services.services_count    = 37                         │
│  ✓ services.services_hash     = b8d4e1...                  │
│  ✓ keywords.keywords_count    = 12                         │
│  ✓ keywords.keywords_hash     = c7a3f2...                  │
│  ✓ prompt.prompt_hash         = e4f1a8...                  │
│  ✓ input.use_full_text        = False                      │
│  ✓ model.model_name           = gpt-4o-mini                │
│  ✓ model.temperature          = 0.1                        │
│                                                             │
│  Metrics Logged:                                            │
│  ✓ val.accuracy              = 0.92                        │
│  ✓ val.precision             = 0.95                        │
│  ✓ val.recall                = 0.87                        │
│  ✓ val.f1_score              = 0.909                       │
│  ✓ val.pr_auc                = 0.91                        │
│  ✓ test.accuracy             = ...                         │
│  ✓ api_cost_usd              = 5.50                        │
│                                                             │
│  Artifacts Logged:                                          │
│  ✓ prompts/classify_tender.md                              │
│  ✓ data/raw/services.md                                    │
│  ✓ data/raw/keywords.csv                                   │
│  ✓ data/processed/preds_val.jsonl                          │
│  ✓ reports/pr_curve_val.png                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
            ┌───────────────────────┐
            │  MLflow UI            │
            │  http://localhost:5000│
            │                       │
            │  - Compare experiments│
            │  - View artifacts     │
            │  - Track costs        │
            │  - Promote to prod    │
            └───────────────────────┘
```

---

## Data Tracking Details

### What Triggers "Data Changed"

The `data_hash` parameter changes when:

✅ **New tenders added** (SIMAP updates)
```bash
# Before: 4,748 tenders, hash: a3f5c2...
python scripts/00_reload_data_with_fulltext.py
# After:  5,000 tenders, hash: d7e9f1... ← CHANGED
```

✅ **Labels updated** (manual corrections)
```bash
# Someone updates selected_ids.csv
# Hash changes: a3f5c2... → b4g6d3...
```

✅ **Splits changed** (re-run 02_make_splits.py)
```bash
# Train/val/test IDs change
# Hash changes because split composition changed
```

### What Triggers "Services Changed"

The `services_hash` changes when:

✅ **Services.xlsx updated**
```bash
# Add new service or edit description
# Hash changes: b8d4e1... → c9f2d3...
```

✅ **services.md created/updated**
```bash
# Convert from Excel or manually edit
# Hash changes: b8d4e1... → c9f2d3...
```

### What Triggers "Keywords Changed"

The `keywords_hash` changes when:

✅ **keywords.csv updated**
```bash
# Add/remove/edit keywords
# Hash changes: c7a3f2... → d8g4h4...
```

### What Triggers "Prompt Changed"

The `prompt_hash` changes when:

✅ **Services change** → Prompt rebuilt
✅ **Keywords change** → Prompt rebuilt
✅ **Training data changes** → Different few-shot examples
✅ **Manual prompt edits**

---

## Experiment Tracking Workflow

### 1. Development Loop

```bash
# A. Update something (services, keywords, data)
nano data/raw/services.md

# B. Rebuild dependencies
python scripts/03_build_prompt.py

# C. Run experiment with tracking
export EXPERIMENT_NAME="exp_$(date +%Y%m%d_%H%M%S)"
export EXPERIMENT_DESCRIPTION="Updated Datenportal service"

python scripts/04_llm_predict.py
python scripts/05_eval_with_mlflow.py
```

**MLflow automatically logs:**
- What changed (hashes)
- New metrics
- All configuration
- Artifacts (files)

### 2. Comparison

```bash
# In MLflow UI
# Select: exp_baseline + exp_services_v2
# Click: Compare
```

**See exactly what differs:**
```
Parameters:
  services.services_hash:  b8d4e1... → c9f2d3...  [CHANGED]
  data.data_hash:          a3f5c2... → a3f5c2...  [SAME]
  
Metrics:
  val.accuracy:            0.92 → 0.93  [+1%]
  val.precision:           0.95 → 0.96  [+1%]
  val.recall:              0.87 → 0.88  [+1%]
```

### 3. Production Deployment

```python
# Promote best experiment to production
import mlflow

client = mlflow.tracking.MlflowClient()

# Register model
mlflow.register_model(
    f"runs:/{run_id}/model",
    "tender_classifier"
)

# Transition to production
client.transition_model_version_stage(
    name="tender_classifier",
    version=3,  # The best experiment
    stage="Production"
)
```

### 4. Production Monitoring

```python
# Daily batch job
with mlflow.start_run(run_name=f"production_{date}"):
    # Track what's running
    mlflow.log_param("deployed_version", "v3")
    mlflow.log_param("deployed_prompt_hash", "e4f1a8...")
    mlflow.log_param("deployed_services_hash", "c9f2d3...")
    
    # Track performance
    mlflow.log_metric("daily_predictions", 150)
    mlflow.log_metric("daily_positives", 8)
    mlflow.log_metric("precision_estimated", 0.94)
    mlflow.log_metric("api_cost_usd", 12.50)
```

---

## Complete Example: Dataset Update Scenario

### Scenario: SIMAP delivers new October 2025 tenders

#### Step 1: Baseline (Before New Data)

```bash
export EXPERIMENT_NAME="exp_baseline_sept2025"
python scripts/05_eval_with_mlflow.py
```

**Tracked:**
```yaml
data:
  tenders_total: 4748
  tenders_positive: 162
  positive_rate: 0.034
  data_hash: a3f5c2abc...
  date_range: "2008-10-30 to 2025-09-30"
  
services:
  services_count: 37
  services_hash: b8d4e1def...
  
metrics:
  val.accuracy: 0.92
  val.precision: 0.95
  val.recall: 0.87
```

#### Step 2: New Data Arrives

```bash
# Download new SIMAP data
# Update tenders_content.xlsx with Oct 2025 tenders

python scripts/00_reload_data_with_fulltext.py
# Output: Loaded 5000 tenders (was 4748)

python scripts/01_prepare_data.py
# Output: 180 positives (was 162)

python scripts/02_make_splits.py
# Output: New train/val/test splits
```

#### Step 3: Re-run with New Data

```bash
export EXPERIMENT_NAME="exp_with_oct2025_data"
export EXPERIMENT_DESCRIPTION="Re-ran with October 2025 SIMAP data (252 new tenders)"

python scripts/03_build_prompt.py  # Rebuilds with new train examples
python scripts/04_llm_predict.py
python scripts/05_eval_with_mlflow.py
```

**Tracked:**
```yaml
data:
  tenders_total: 5000  ← CHANGED
  tenders_positive: 180  ← CHANGED
  positive_rate: 0.036  ← CHANGED
  data_hash: d7e9f1ghi...  ← CHANGED (different data!)
  date_range: "2008-10-30 to 2025-10-31"  ← CHANGED
  train_size: 3750  ← CHANGED
  
services:
  services_count: 37  ← SAME
  services_hash: b8d4e1def...  ← SAME
  
prompt:
  prompt_hash: f5b2c9jkl...  ← CHANGED (new few-shot examples)
  
metrics:
  val.accuracy: 0.91  ← Slightly worse
  val.precision: 0.94  ← Slightly worse
  val.recall: 0.88  ← Improved!
```

#### Step 4: Analysis

**In MLflow UI, compare the two experiments:**

**What Changed:**
- ✅ Data: 252 new tenders added
- ✅ Training set: 189 new training examples
- ✅ Few-shot examples: Different mix due to new train set
- ❌ Services: No change
- ❌ Keywords: No change
- ❌ Model config: No change

**Performance Impact:**
- Accuracy: 92% → 91% (-1%)
- Precision: 95% → 94% (-1%)
- Recall: 87% → 88% (+1%)

**Conclusion:**
- Slight performance degradation acceptable
- New data brings different distribution
- Consider rebalancing or updating prompt

**Decision:**
- Keep new data
- Update EXPERIMENT_LOG.md
- Monitor next batch

---

## File Structure

```
tenders-llm/
├── utils/
│   ├── __init__.py
│   ├── experiment_tracker.py       # Hash computation, metadata extraction
│   └── mlflow_wrapper.py           # MLflow integration
│
├── scripts/
│   ├── 00_reload_data_with_fulltext.py
│   ├── 01_prepare_data.py
│   ├── 02_make_splits.py
│   ├── 03_build_prompt.py
│   ├── 04_llm_predict.py
│   ├── 05_eval.py                  # Original (no tracking)
│   └── 05_eval_with_mlflow.py      # NEW: With full tracking
│
├── experiments/                     # JSON configs
│   ├── exp_baseline/
│   │   └── experiment_config.json  # Complete snapshot
│   ├── exp_services_v2/
│   │   └── experiment_config.json
│   └── ...
│
├── mlruns/                          # MLflow data
│   ├── mlflow.db                    # SQLite database
│   └── 0/                           # Experiment artifacts
│       ├── abc123.../               # Run ID
│       │   ├── artifacts/
│       │   │   ├── prompt/
│       │   │   ├── services/
│       │   │   ├── predictions_val/
│       │   │   └── plots/
│       │   └── meta.yaml
│       └── ...
│
├── MLFLOW_GUIDE.md                  # Full documentation
├── EXPERIMENT_TRACKING_QUICKSTART.md # Quick start guide
└── ARCHITECTURE_WITH_TRACKING.md    # This file
```

---

## Benefits Summary

### For Development

✅ **Know exactly what changed** between experiments
✅ **Reproduce any experiment** using config snapshots
✅ **Track costs** over time
✅ **Compare prompts** side-by-side
✅ **Detect data drift** via hash changes

### For Production

✅ **Model registry** (version control for prompts)
✅ **Staging → Production** promotion workflow
✅ **Rollback capability** if new version underperforms
✅ **Performance monitoring** over time
✅ **Cost tracking** for budget management
✅ **A/B testing** (route 50% to v1, 50% to v2)

### For Team Collaboration

✅ **Shared experiment database**
✅ **Documented changes** (not just in heads)
✅ **Onboarding** (new team members see history)
✅ **Auditing** (who ran what, when)

---

## Next Steps

1. **Install MLflow:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start UI:**
   ```bash
   mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db
   ```

3. **Run first tracked experiment:**
   ```bash
   export EXPERIMENT_NAME="exp_first_test"
   python scripts/05_eval_with_mlflow.py
   ```

4. **View in UI:**
   Open http://localhost:5000

5. **Read guides:**
   - Quick start: `EXPERIMENT_TRACKING_QUICKSTART.md`
   - Full docs: `MLFLOW_GUIDE.md`

---

**You now have production-grade experiment tracking that monitors:**
- ✅ Dataset changes (new tenders, label updates)
- ✅ Services changes (description updates)
- ✅ Keywords changes (keyword additions/removals)
- ✅ Prompt changes (any modifications)
- ✅ Input config changes (full text vs title)
- ✅ Model config changes (model, temperature)
- ✅ Performance metrics (accuracy, precision, recall)
- ✅ Costs (API usage tracking)

**Ready for production deployment with full traceability!** 🚀

