# Historical Experiments - Migration Status

## Current Status: ❌ NOT MIGRATED YET

Your previous experiments are **not yet in MLflow**. They exist only as:

1. **JSON files** in `results/`
2. **Manual documentation** in `EXPERIMENT_LOG.md`
3. **Prompt archives** in `prompts/archive/`

---

## What Exists Now

### ✅ Documented Historical Experiments

From `EXPERIMENT_LOG.md`:

| Exp # | Date | Description | Test Size | Accuracy | Precision | Recall | Status |
|-------|------|-------------|-----------|----------|-----------|--------|--------|
| 1 | 2024-10-08 | v1 Conservative | 10 (2p/8n) | 80% | N/A | 0% | ❌ Failed |
| 2 | 2024-10-08 | v2 Balanced | 50 (23p/27n) | 92% | 95% | 87% | ✅ Best |
| 3a | 2024-10-09 | v2 Title Only | 50 (23p/27n) | 90% | 95% | 83% | ✅ Good |
| 3b | 2024-10-09 | v2 Full Text | 50 (23p/27n) | 88% | 91% | 83% | ⚠️ Worse |

### ✅ Stored Results

```
results/
└── prompt_comparison_20251009_090604.json  ← Experiments 3a & 3b
```

**Contents:**
- Experiment 3a: v2 (Title Only) - Acc 90%, Prec 95%, Rec 83%
- Experiment 3b: v3 (Full Text) - Acc 88%, Prec 91%, Rec 83%

### ❌ Missing Data

The following were NOT saved:
- ❌ Prediction files (`preds_val.jsonl`, `preds_test.jsonl`)
- ❌ PR curve images
- ❌ Dataset metadata (what data was used)
- ❌ Exact prompt versions used
- ❌ Services/keywords versions

**Why this matters:**
Without this data, you can't fully reproduce the experiments or know what changed between runs.

---

## Migration Options

### Option 1: Migrate What Exists (Partial) ⭐ RECOMMENDED

```bash
# Run migration script
python scripts/migrate_historical_experiments.py
```

**This will import:**
- ✅ Metrics (accuracy, precision, recall, F1)
- ✅ Basic parameters (use_full_text, prompt_path)
- ✅ Timestamps
- ✅ Confusion matrix values (TP, FP, TN, FN)

**Limitations:**
- ⚠️ No data version tracking (data_hash unknown)
- ⚠️ No services version tracking (services_hash unknown)
- ⚠️ No prompt snapshots (lost to history)
- ⚠️ No prediction files (not saved originally)

**Result:**
You'll see all 4 historical experiments in MLflow UI, but with limited detail. They'll be tagged with `migrated=true` to distinguish them from new experiments.

### Option 2: Start Fresh (Clean Slate)

Don't migrate - just start tracking from now on:

```bash
# Your first properly tracked experiment
export EXPERIMENT_NAME="exp_baseline_with_tracking"
export EXPERIMENT_DESCRIPTION="First experiment with full MLflow tracking"
python scripts/05_eval_with_mlflow.py
```

**Pros:**
- Clean start
- All future experiments fully tracked
- No confusion about incomplete historical data

**Cons:**
- Lose historical comparison
- Can't reference "best ever" from Oct 2024

### Option 3: Recreate Historical Experiments (Time-Intensive)

Manually re-run the historical experiments with full tracking:

```bash
# 1. Restore v2 balanced prompt
cp prompts/archive/v2_classify_tender_balanced_2024-10-08.md prompts/classify_tender.md

# 2. Run with tracking
export EXPERIMENT_NAME="exp_v2_balanced_recreated"
export EXPERIMENT_DESCRIPTION="Recreation of successful Oct 2024 experiment"
python scripts/04_llm_predict.py
python scripts/05_eval_with_mlflow.py

# 3. Test full text version
export EXPERIMENT_NAME="exp_v2_fulltext_recreated"
export USE_FULL_TEXT="1"
python scripts/04_llm_predict.py
python scripts/05_eval_with_mlflow.py
```

**Pros:**
- ✅ Full tracking (data hash, services hash, etc.)
- ✅ All artifacts saved
- ✅ Reproducible
- ✅ Can validate original results

**Cons:**
- ❌ Costs money (OpenAI API calls)
- ❌ Time consuming (~50 tenders × 22 sec = 18+ minutes per experiment)
- ❌ Might get slightly different results (model updates, API changes)

---

## Recommended Approach

**Do Option 1 + Start Fresh**

1. **Migrate what you have** (5 minutes):
   ```bash
   python scripts/migrate_historical_experiments.py
   mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db
   # View historical experiments in UI
   ```

2. **Document the baseline** (2 minutes):
   ```bash
   # Note in EXPERIMENT_LOG.md that historical data is partial
   echo "Note: Experiments 1-3 migrated to MLflow with limited metadata" >> EXPERIMENT_LOG.md
   ```

3. **Start proper tracking** (now):
   ```bash
   export EXPERIMENT_NAME="exp_$(date +%Y%m%d)_baseline"
   export EXPERIMENT_DESCRIPTION="First experiment with complete tracking"
   python scripts/05_eval_with_mlflow.py
   ```

**Result:**
- You have historical context (4 past experiments)
- All future experiments fully tracked
- Clear distinction between old (partial) and new (complete) tracking

---

## After Migration: What You'll See in MLflow UI

### Historical Experiments (Tagged: migrated=true)

```
Run Name: historical_exp1_conservative
  Tags:
    migrated: true
    original_source: EXPERIMENT_LOG.md
    status: failed
  Params:
    prompt_version: v1_conservative
    test_cases: 10
  Metrics:
    accuracy: 0.80
    recall: 0.00  ← Too conservative!

Run Name: historical_exp2_balanced
  Tags:
    migrated: true
    original_source: EXPERIMENT_LOG.md
    status: success
  Params:
    prompt_version: v2_balanced
    test_cases: 50
  Metrics:
    accuracy: 0.92
    precision: 0.95
    recall: 0.87  ← Best historical result!

Run Name: historical_v2_title_only
  Tags:
    migrated: true
    original_source: prompt_comparison_20251009_090604.json
  Params:
    use_full_text: false
  Metrics:
    accuracy: 0.90
    precision: 0.95

Run Name: historical_v3_full_text
  Tags:
    migrated: true
    original_source: prompt_comparison_20251009_090604.json
  Params:
    use_full_text: true
  Metrics:
    accuracy: 0.88  ← Worse than title-only
```

### New Experiments (Full Tracking)

```
Run Name: exp_20251009_baseline
  Params:
    data.tenders_total: 4748
    data.data_hash: a3f5c2...
    services.services_hash: b8d4e1...
    prompt.prompt_hash: e4f1a8...
    [... 20+ more params ...]
  Metrics:
    val.accuracy: 0.92
    [... many more metrics ...]
  Artifacts:
    prompts/classify_tender.md
    services/Services.xlsx
    predictions_val/preds_val.jsonl
    plots/pr_curve_val.png
```

---

## Decision Time

Choose your path:

**A) Quick Migration (5 min)**
```bash
python scripts/migrate_historical_experiments.py
```

**B) Skip Migration (0 min)**
```bash
# Just start fresh from now
export EXPERIMENT_NAME="exp_first_tracked"
python scripts/05_eval_with_mlflow.py
```

**C) Full Recreation (2-4 hours + $$$)**
```bash
# Re-run historical experiments with full tracking
# See "Option 3" above
```

---

## Questions?

- **"Will I lose my historical data if I don't migrate?"**
  No! It's still in `EXPERIMENT_LOG.md` and `results/`. Migration just makes it easier to compare.

- **"Can I migrate later?"**
  Yes! The migration script can be run anytime.

- **"What if I run new experiments before migrating?"**
  No problem! Historical and new experiments will coexist in MLflow.

- **"Should I migrate even with incomplete data?"**
  Yes, if you want to compare new results against old baselines in one UI. Otherwise, start fresh.

---

## Next Steps

1. **Choose migration approach** (A, B, or C above)
2. **Run migration** (if chosen)
3. **Start MLflow UI:**
   ```bash
   mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db
   ```
4. **Run first properly tracked experiment:**
   ```bash
   export EXPERIMENT_NAME="exp_baseline_full_tracking"
   python scripts/05_eval_with_mlflow.py
   ```
5. **Compare in UI** and celebrate having full tracking! 🎉

---

**Updated:** 2025-10-09  
**Status:** Awaiting migration decision

