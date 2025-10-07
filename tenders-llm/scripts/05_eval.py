"""
Step 5: Evaluation
Compute PR-AUC, precision@K, recall@K, and save PR curves.
"""

import json
import os
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import average_precision_score, precision_recall_curve
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

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
    plt.savefig(reports_dir / f"pr_curve_{name}.png", dpi=200)
    plt.close()
    
    # Top-K analysis
    df_sorted = df.sort_values("score", ascending=False).reset_index(drop=True)
    print(f"\nTop-K Analysis ({name.upper()}):")
    for K in [50, 100, 170, 200, 300]:
        if K <= len(df_sorted):
            topk = df_sorted.head(K)
            prec_at_k = topk["y_true"].mean()
            recall_at_k = topk["y_true"].sum() / df_sorted["y_true"].sum() if df_sorted["y_true"].sum() > 0 else 0.0
            print(f"  K={K:>3}: Precision@K={prec_at_k:.3f} | Recall@K={recall_at_k:.3f}")

def main():
    base = Path(__file__).parent.parent
    processed_dir = base / "data" / "processed"
    reports_dir = base / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    val_path = processed_dir / "preds_val.jsonl"
    test_path = processed_dir / "preds_test.jsonl"
    
    if val_path.exists():
        dfv = load_preds(val_path)
        pr_report(dfv, "val", reports_dir)
    
    if test_path.exists():
        dft = load_preds(test_path)
        pr_report(dft, "test", reports_dir)
    
    print(f"\nReports saved to: {reports_dir}")

if __name__ == "__main__":
    main()

