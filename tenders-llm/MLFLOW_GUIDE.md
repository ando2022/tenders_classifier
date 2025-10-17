# MLflow Experiment Tracking Guide

This guide explains how to use the comprehensive experiment tracking system for tenders-llm.

## What Gets Tracked

Every experiment automatically tracks:

### 📊 Data Characteristics
- Total number of tenders
- Number of positives/negatives
- Positive rate (class imbalance)
- Train/val/test split sizes
- Date range of tenders
- Language distribution
- **Data hash** (detects if dataset changed)

### 📝 Services Configuration
- Services file path
- Number of services
- Services version/hash
- Whether services.md exists

### 🔑 Keywords Configuration
- Keywords file path
- Number of keywords
- Keyword categories
- Languages
- Keywords version/hash

### 💬 Prompt Configuration
- Prompt file path
- Prompt length (chars/tokens)
- Number of few-shot examples
- **Prompt hash** (detects if prompt changed)

### ⚙️ Input Configuration
- Whether full text is used
- Max title/text characters
- Summarization settings

### 🤖 Model Configuration
- Model provider (OpenAI)
- Model name (gpt-4o-mini)
- Temperature
- Other model parameters

### 📈 Results
- Accuracy, Precision, Recall, F1-Score
- PR-AUC
- Precision@K, Recall@K for various K
- Confusion matrix (TP, FP, TN, FN)
- API costs
- Number of requests

---

## Setup (One-Time)

### 1. Install MLflow

```bash
pip install mlflow
```

Or update your environment:

```bash
pip install -r requirements.txt
```

### 2. Start MLflow UI

```bash
# From tenders-llm directory
mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db
```

Then open browser to: http://localhost:5000

The UI will show:
- List of all experiments
- Comparison table
- Parameter/metric search
- Artifact browser

---

## Running Experiments

### Method 1: Use Environment Variables

```bash
# Set experiment details
export EXPERIMENT_NAME="exp_services_v2"
export EXPERIMENT_DESCRIPTION="Updated services with new Datenportal description"
export USE_FULL_TEXT="0"

# Run evaluation (this tracks everything)
python scripts/05_eval_with_mlflow.py
```

### Method 2: Programmatic (In Your Scripts)

```python
from pathlib import Path
from utils.mlflow_wrapper import TenderMLflowTracker

base_dir = Path(__file__).parent.parent
tracker = TenderMLflowTracker(base_dir)

with tracker.start_run(
    experiment_name="exp_services_v2",
    description="Updated services with new Datenportal description",
    use_full_text=False,
    model_config={
        "provider": "openai",
        "model_name": "gpt-4o-mini",
        "temperature": 0.1
    }
):
    # Log artifacts (prompt, services, keywords)
    tracker.log_artifacts()
    
    # Run your predictions...
    # ...
    
    # Log metrics
    tracker.log_metrics({
        "val.accuracy": 0.92,
        "val.precision": 0.95,
        "val.recall": 0.87,
        "val.f1_score": 0.909
    })
    
    # Log predictions file
    tracker.log_predictions(Path("data/processed/preds_val.jsonl"))
    
    # Log costs
    tracker.log_cost(api_cost_usd=5.50, n_requests=500)
```

---

## Example Workflow

### Experiment 1: Baseline

```bash
export EXPERIMENT_NAME="exp_baseline"
export EXPERIMENT_DESCRIPTION="Baseline with current prompt"

# Run pipeline
python scripts/03_build_prompt.py
python scripts/04_llm_predict.py
python scripts/05_eval_with_mlflow.py
```

**Results logged:**
- Data: 4748 tenders, 162 positives (hash: a3f5c2...)
- Services: 37 services (hash: b8d4e1...)
- Prompt: 45000 chars, 100 examples (hash: e4f1a8...)
- Metrics: Acc=92%, Prec=95%, Rec=87%

### Experiment 2: Updated Services

```bash
# 1. Update services.md file manually
nano data/raw/services.md

# 2. Rebuild prompt
python scripts/03_build_prompt.py

export EXPERIMENT_NAME="exp_services_v2"
export EXPERIMENT_DESCRIPTION="Updated Datenportal service description"

# 3. Run predictions and evaluation
python scripts/04_llm_predict.py
python scripts/05_eval_with_mlflow.py
```

**Results logged:**
- Data: 4748 tenders, 162 positives (hash: a3f5c2...) ← Same
- Services: 37 services (hash: **c9f2d3...**) ← **Changed!**
- Prompt: 46200 chars, 100 examples (hash: **f5b2c9...**) ← **Changed!**
- Metrics: Acc=93%, Prec=96%, Rec=88% ← **Improved!**

### Experiment 3: Use Full Text

```bash
export EXPERIMENT_NAME="exp_fulltext"
export EXPERIMENT_DESCRIPTION="Testing with full tender text instead of title only"
export USE_FULL_TEXT="1"

python scripts/04_llm_predict.py
python scripts/05_eval_with_mlflow.py
```

**Results logged:**
- Data: 4748 tenders (hash: a3f5c2...) ← Same
- Services: 37 services (hash: c9f2d3...) ← Same
- Prompt: 46200 chars (hash: f5b2c9...) ← Same
- **Input config: use_full_text=TRUE** ← **Changed!**
- Metrics: Acc=88%, Prec=91%, Rec=83% ← **Worse!**

---

## Comparing Experiments

### In MLflow UI

1. Open http://localhost:5000
2. Select multiple experiments (checkboxes)
3. Click "Compare" button
4. View side-by-side:
   - All parameters
   - All metrics
   - Difference highlighting
   - Charts and plots

### Programmatically

```python
from utils.mlflow_wrapper import compare_experiments
from pathlib import Path

compare_experiments(
    base_dir=Path("."),
    exp_name1="exp_baseline",
    exp_name2="exp_services_v2"
)
```

**Output:**
```
COMPARISON: exp_baseline vs exp_services_v2
========================================

🔍 Found 2 categories of changes:

--- SERVICES CHANGED ---
  services_hash:
    Old: b8d4e1...
    New: c9f2d3...

--- PROMPT CHANGED ---
  prompt_hash:
    Old: e4f1a8...
    New: f5b2c9...
```

---

## What Happens When Data Changes

### Scenario: SIMAP Delivers New Tenders

```bash
# 1. New data arrives
python scripts/00_reload_data_with_fulltext.py
# Output: Now 5000 tenders (was 4748)

# 2. Rebuild
python scripts/01_prepare_data.py
python scripts/02_make_splits.py

# 3. New experiment
export EXPERIMENT_NAME="exp_new_data_oct2025"
export EXPERIMENT_DESCRIPTION="Re-ran with October 2025 SIMAP data"

python scripts/03_build_prompt.py
python scripts/04_llm_predict.py
python scripts/05_eval_with_mlflow.py
```

**MLflow automatically detects:**
```
--- DATA CHANGED ---
  tenders_total:
    Old: 4748
    New: 5000
  tenders_positive:
    Old: 162
    New: 175
  data_hash:
    Old: a3f5c2...
    New: d7e9f1... ← Different hash = different data
  train_size:
    Old: 3561
    New: 3750
```

**Now you can compare:**
- Did performance change with new data?
- Is the model still calibrated?
- Do we need to retrain?

---

## Production Deployment

### 1. Promote Model to Production

After validating an experiment in MLflow UI:

```python
import mlflow

# Get the run ID from UI or programmatically
run_id = "abc123..."

# Register the model
mlflow.register_model(
    f"runs:/{run_id}/model",
    "tender_classifier"
)

# Promote to production
client = mlflow.tracking.MlflowClient()
client.transition_model_version_stage(
    name="tender_classifier",
    version=2,  # The version you want to promote
    stage="Production"
)
```

### 2. Load in Production

```python
import mlflow.pyfunc

# Load production model
model = mlflow.pyfunc.load_model("models:/tender_classifier/Production")

# Use it
prediction = model.predict(new_tender_data)
```

### 3. Monitor Production

```python
# Track production performance
with mlflow.start_run(run_name="production_2025_10_09"):
    mlflow.log_metric("daily_predictions", 150)
    mlflow.log_metric("daily_positives", 8)
    mlflow.log_metric("daily_cost_usd", 12.50)
    
    # Track precision (from human feedback)
    mlflow.log_metric("production_precision", 0.94)
```

---

## Directory Structure

```
tenders-llm/
├── mlruns/                          # MLflow tracking data
│   ├── mlflow.db                    # SQLite database
│   └── 0/                           # Experiment artifacts
│       ├── abc123.../               # Run ID
│       │   ├── artifacts/           # Stored files
│       │   │   ├── prompt/
│       │   │   ├── services/
│       │   │   ├── predictions_val/
│       │   │   └── plots/
│       │   └── meta.yaml
│       └── ...
│
├── experiments/                     # JSON configs for each experiment
│   ├── exp_baseline/
│   │   └── experiment_config.json  # Complete experiment snapshot
│   ├── exp_services_v2/
│   │   └── experiment_config.json
│   └── ...
│
└── utils/
    ├── experiment_tracker.py        # Data/config tracking
    └── mlflow_wrapper.py            # MLflow integration
```

---

## Best Practices

### 1. Name Experiments Descriptively

❌ Bad:
```bash
EXPERIMENT_NAME="test1"
EXPERIMENT_NAME="new"
```

✅ Good:
```bash
EXPERIMENT_NAME="exp_20251009_services_v2_datenportal_update"
EXPERIMENT_NAME="exp_fulltext_with_summarization"
EXPERIMENT_NAME="exp_gpt4_vs_gpt4o_mini"
```

### 2. Add Descriptions

Always add a description:
```bash
EXPERIMENT_DESCRIPTION="Testing whether full text improves recall on technical tenders"
```

### 3. Track Costs

Always log API costs to monitor budget:
```python
tracker.log_cost(api_cost_usd=estimated_cost, n_requests=n_requests)
```

### 4. Version Your Data

When data changes, create a new version:
```bash
cp data/raw/tenders_content.xlsx data/raw/archive/tenders_content_v1_20251009.xlsx
```

### 5. Document Major Changes

Update EXPERIMENT_LOG.md with:
- What changed
- Why
- Results
- Decision

---

## Troubleshooting

### MLflow UI won't start

```bash
# Check if port 5000 is already in use
mlflow ui --port 5001
```

### Can't find experiments

```bash
# Make sure you're in the right directory
cd tenders-llm/
mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db
```

### Experiments not showing up

Check that the script is using the tracker:
```python
from utils.mlflow_wrapper import TenderMLflowTracker
# Not just importing mlflow directly
```

---

## Next Steps

1. **Run your first experiment** with MLflow tracking
2. **Compare 2-3 experiments** in the UI
3. **Set up production** deployment when ready
4. **Monitor costs** over time

For questions, see:
- MLflow docs: https://mlflow.org/docs/latest/index.html
- Our example: `scripts/05_eval_with_mlflow.py`

