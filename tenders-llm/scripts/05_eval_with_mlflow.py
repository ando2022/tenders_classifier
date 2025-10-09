"""
Step 5: Evaluation with MLflow Tracking
Compute PR-AUC, precision@K, recall@K, and save PR curves.
Now with comprehensive experiment tracking!
"""

import json
import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import average_precision_score, precision_recall_curve
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

# Add utils to path
sys.path.append(str(Path(__file__).parent.parent))
from utils.mlflow_wrapper import TenderMLflowTracker


def load_preds(path: Path) -> pd.DataFrame:
    """Load predictions from JSONL file."""
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))
    df = pd.DataFrame(rows)
    
    # Convert predicted label to probability-ish score:
    # use confidence_score with sign for Yes/No
    conf = pd.to_numeric(df["confidence_score"], errors="coerce").fillna(0)
    is_yes = (df["prediction"].astype(str).str.lower() == "yes").astype(int)
    
    # Simple score: confidence * 1 if yes else 0
    score = conf * is_yes
    df["score"] = score
    df["y_true"] = df["label"].astype(int)
    
    return df


def pr_report(df: pd.DataFrame, name: str, reports_dir: Path):
    """Generate PR curve and top-K metrics."""
    ap = average_precision_score(df["y_true"], df["score"])
    print(f"\n{name.upper()}: PR-AUC (Average Precision) = {ap:.4f}")
    
    # PR curve
    precision, recall, thresh = precision_recall_curve(df["y_true"], df["score"])
    
    plt.figure(figsize=(8, 6))
    plt.plot(recall, precision, linewidth=2)
    plt.xlabel("Recall", fontsize=12)
    plt.ylabel("Precision", fontsize=12)
    plt.title(f"PR Curve - {name.upper()} (AP={ap:.3f})", fontsize=14)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    
    pr_curve_path = reports_dir / f"pr_curve_{name}.png"
    plt.savefig(pr_curve_path, dpi=200)
    plt.close()
    
    # Top-K analysis
    df_sorted = df.sort_values("score", ascending=False).reset_index(drop=True)
    print(f"\nTop-K Analysis ({name.upper()}):")
    
    topk_metrics = {}
    for K in [50, 100, 170, 200, 300]:
        if K <= len(df_sorted):
            topk = df_sorted.head(K)
            prec_at_k = topk["y_true"].mean()
            recall_at_k = topk["y_true"].sum() / df_sorted["y_true"].sum() if df_sorted["y_true"].sum() > 0 else 0.0
            print(f"  K={K:>3}: Precision@K={prec_at_k:.3f} | Recall@K={recall_at_k:.3f}")
            
            topk_metrics[f"precision@{K}"] = prec_at_k
            topk_metrics[f"recall@{K}"] = recall_at_k
    
    # Overall metrics
    y_pred = (df["prediction"].astype(str).str.lower() == "yes").astype(int)
    tp = ((df["y_true"] == 1) & (y_pred == 1)).sum()
    fp = ((df["y_true"] == 0) & (y_pred == 1)).sum()
    tn = ((df["y_true"] == 0) & (y_pred == 0)).sum()
    fn = ((df["y_true"] == 1) & (y_pred == 0)).sum()
    
    accuracy = (tp + tn) / len(df) if len(df) > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    metrics = {
        "pr_auc": ap,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
        **topk_metrics
    }
    
    return metrics, pr_curve_path


def main():
    base = Path(__file__).parent.parent
    processed_dir = base / "data" / "processed"
    reports_dir = base / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Get experiment name from environment or use default
    experiment_name = os.getenv("EXPERIMENT_NAME", f"exp_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}")
    description = os.getenv("EXPERIMENT_DESCRIPTION", "Automated evaluation run")
    
    # Determine configuration
    use_full_text = os.getenv("USE_FULL_TEXT", "0") == "1"
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temperature = float(os.getenv("TEMPERATURE", "0.1"))
    
    # Initialize MLflow tracker
    tracker = TenderMLflowTracker(base)
    
    with tracker.start_run(
        experiment_name=experiment_name,
        description=description,
        use_full_text=use_full_text,
        model_config={
            "provider": "openai",
            "model_name": model_name,
            "temperature": temperature
        }
    ):
        # Log artifacts (prompt, services, etc.)
        tracker.log_artifacts()
        
        # Evaluate validation set
        val_path = processed_dir / "preds_val.jsonl"
        if val_path.exists():
            print("\n" + "="*80)
            print("VALIDATION SET EVALUATION")
            print("="*80)
            
            dfv = load_preds(val_path)
            val_metrics, val_pr_curve = pr_report(dfv, "val", reports_dir)
            
            # Log to MLflow
            tracker.log_metrics({f"val.{k}": v for k, v in val_metrics.items() if isinstance(v, (int, float))})
            tracker.log_predictions(val_path, "predictions_val")
            tracker.log_pr_curve(val_pr_curve)
            
            print(f"\n📊 Validation Metrics:")
            print(f"  Accuracy:  {val_metrics['accuracy']:.1%}")
            print(f"  Precision: {val_metrics['precision']:.1%}")
            print(f"  Recall:    {val_metrics['recall']:.1%}")
            print(f"  F1-Score:  {val_metrics['f1_score']:.3f}")
            print(f"  PR-AUC:    {val_metrics['pr_auc']:.3f}")
        
        # Evaluate test set
        test_path = processed_dir / "preds_test.jsonl"
        if test_path.exists():
            print("\n" + "="*80)
            print("TEST SET EVALUATION")
            print("="*80)
            
            dft = load_preds(test_path)
            test_metrics, test_pr_curve = pr_report(dft, "test", reports_dir)
            
            # Log to MLflow
            tracker.log_metrics({f"test.{k}": v for k, v in test_metrics.items() if isinstance(v, (int, float))})
            tracker.log_predictions(test_path, "predictions_test")
            tracker.log_pr_curve(test_pr_curve)
            
            print(f"\n📊 Test Metrics:")
            print(f"  Accuracy:  {test_metrics['accuracy']:.1%}")
            print(f"  Precision: {test_metrics['precision']:.1%}")
            print(f"  Recall:    {test_metrics['recall']:.1%}")
            print(f"  F1-Score:  {test_metrics['f1_score']:.3f}")
            print(f"  PR-AUC:    {test_metrics['pr_auc']:.3f}")
        
        # Estimate costs (if available in predictions)
        if val_path.exists():
            n_requests = len(dfv)
            # Rough estimate: gpt-4o-mini ~ $0.15 per 1M input tokens, $0.60 per 1M output tokens
            # Assume ~1000 input tokens, ~100 output tokens per request
            estimated_cost = n_requests * (1000 * 0.15/1e6 + 100 * 0.60/1e6)
            tracker.log_cost(api_cost_usd=estimated_cost, n_requests=n_requests)
            print(f"\n💰 Estimated API Cost: ${estimated_cost:.2f} ({n_requests} requests)")
        
        print(f"\n✅ Experiment '{experiment_name}' tracked successfully!")
        print(f"\nView results:")
        print(f"  MLflow UI: mlflow ui --backend-store-uri sqlite:///{base}/mlruns/mlflow.db")
        print(f"  Then open: http://localhost:5000")
        print(f"\nReports saved to: {reports_dir}")


if __name__ == "__main__":
    main()

