# Experiment Tracking - Quick Start

## 30-Second Setup

```bash
# Install MLflow
pip install mlflow

# Start UI (keep running in separate terminal)
mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db

# Open browser
http://localhost:5000
```

## Run Your First Tracked Experiment

```bash
# Set experiment details
export EXPERIMENT_NAME="exp_my_first_test"
export EXPERIMENT_DESCRIPTION="Testing the new tracking system"

# Run evaluation (automatically tracks everything!)
python scripts/05_eval_with_mlflow.py
```

## What Just Got Tracked?

✅ **Data:** 4,748 tenders, 162 positives, hash: `a3f5c2...`  
✅ **Services:** 37 services, hash: `b8d4e1...`  
✅ **Keywords:** Count, categories, hash  
✅ **Prompt:** Length, examples, hash: `e4f1a8...`  
✅ **Model:** gpt-4o-mini, temp=0.1  
✅ **Metrics:** Accuracy, Precision, Recall, F1, PR-AUC  
✅ **Costs:** Estimated $X.XX for Y requests  
✅ **Files:** Prompt, services, predictions, PR curves

## View Results

Go to http://localhost:5000 and see:
- All experiments in a table
- Click experiment → see all details
- Select multiple → compare side-by-side

## Change Something & Re-run

```bash
# 1. Update services.md
nano data/raw/services.md

# 2. Rebuild prompt
python scripts/03_build_prompt.py

# 3. New experiment
export EXPERIMENT_NAME="exp_updated_services"
export EXPERIMENT_DESCRIPTION="Updated Datenportal description"

python scripts/04_llm_predict.py
python scripts/05_eval_with_mlflow.py
```

## Compare Changes

In MLflow UI:
1. Select both experiments (checkboxes)
2. Click "Compare"
3. See **exactly what changed**:
   - Services hash: `b8d4e1...` → `c9f2d3...` ✓ CHANGED
   - Data hash: `a3f5c2...` → `a3f5c2...` ✓ Same
   - Metrics: Accuracy 92% → 93% ✓ Improved!

## Key Files

| File | Purpose |
|------|---------|
| `utils/experiment_tracker.py` | Tracks data, services, keywords changes |
| `utils/mlflow_wrapper.py` | MLflow integration |
| `scripts/05_eval_with_mlflow.py` | Example usage |
| `MLFLOW_GUIDE.md` | Full documentation |

## What Happens When You Update...

### ✏️ Services File
```bash
nano data/raw/services.md  # Edit
python scripts/03_build_prompt.py  # Rebuild
python scripts/05_eval_with_mlflow.py  # Track
# MLflow shows: services_hash CHANGED, prompt_hash CHANGED
```

### 📊 Dataset
```bash
python scripts/00_reload_data_with_fulltext.py  # New data
python scripts/01_prepare_data.py
python scripts/05_eval_with_mlflow.py  # Track
# MLflow shows: data_hash CHANGED, tenders_total CHANGED
```

### 🔑 Keywords
```bash
nano data/raw/keywords.csv  # Edit
python scripts/03_build_prompt.py  # Rebuild
python scripts/05_eval_with_mlflow.py  # Track
# MLflow shows: keywords_hash CHANGED, prompt_hash CHANGED
```

### ⚙️ Model Config
```bash
export OPENAI_MODEL="gpt-4"  # Change model
export TEMPERATURE="0.2"     # Change temp
python scripts/04_llm_predict.py
python scripts/05_eval_with_mlflow.py
# MLflow shows: model.model_name CHANGED, model.temperature CHANGED
```

## Pro Tips

1. **Always name experiments descriptively:**
   ```bash
   EXPERIMENT_NAME="exp_20251009_fulltext_vs_title"
   ```

2. **Add descriptions:**
   ```bash
   EXPERIMENT_DESCRIPTION="Testing whether full text improves recall"
   ```

3. **Check the UI regularly:**
   - See which experiments performed best
   - Understand what changed between runs
   - Track costs over time

4. **Use for production:**
   ```python
   # Load best model
   model = mlflow.pyfunc.load_model("models:/tender_classifier/Production")
   ```

## Common Scenarios

### "Did my services update help?"
1. Run baseline experiment
2. Update services.md
3. Run new experiment
4. Compare in UI → see if metrics improved

### "Which prompt version was best?"
1. Check MLflow UI
2. Sort by `val.f1_score` descending
3. See associated prompt hash
4. Retrieve from artifacts

### "What was the data when we got 95% precision?"
1. Find experiment in UI
2. Check `data.data_hash` parameter
3. Match to archived data version

## Need Help?

- Full docs: `MLFLOW_GUIDE.md`
- Example code: `scripts/05_eval_with_mlflow.py`
- MLflow docs: https://mlflow.org/docs/latest/

