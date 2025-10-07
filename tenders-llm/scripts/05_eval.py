"""
Step 5: Evaluation
Compute metrics and save report.
"""

import pandas as pd
from pathlib import Path
from sklearn.metrics import (
    classification_report, 
    confusion_matrix, 
    roc_auc_score, 
    average_precision_score
)

def main():
    base = Path(__file__).parent.parent
    reports_dir = base / "reports"
    
    # Load predictions
    preds = pd.read_csv(reports_dir / "predictions.csv")
    
    y_true = preds["label_true"]
    y_pred = preds["label_pred"]
    y_conf = preds["confidence"]
    
    # Metrics
    cm = confusion_matrix(y_true, y_pred)
    report = classification_report(y_true, y_pred, digits=3)
    
    # AUC/AP if we have confidence scores
    try:
        auc = roc_auc_score(y_true, y_conf)
        ap = average_precision_score(y_true, y_conf)
    except:
        auc = ap = None
    
    # Print
    print("=== EVALUATION RESULTS ===\n")
    print(f"Total samples: {len(preds)}")
    print(f"Positive (true): {y_true.sum()}")
    print(f"Positive (pred): {y_pred.sum()}")
    
    print("\nConfusion Matrix:")
    print(cm)
    
    print("\nClassification Report:")
    print(report)
    
    if auc:
        print(f"\nAUC: {auc:.4f}")
        print(f"AP (PR-AUC): {ap:.4f}")
    
    # Save report
    report_path = reports_dir / "evaluation_report.txt"
    with open(report_path, "w") as f:
        f.write("=== EVALUATION RESULTS ===\n\n")
        f.write(f"Total samples: {len(preds)}\n")
        f.write(f"Positive (true): {y_true.sum()}\n")
        f.write(f"Positive (pred): {y_pred.sum()}\n\n")
        f.write("Confusion Matrix:\n")
        f.write(str(cm) + "\n\n")
        f.write("Classification Report:\n")
        f.write(report + "\n")
        if auc:
            f.write(f"\nAUC: {auc:.4f}\n")
            f.write(f"AP (PR-AUC): {ap:.4f}\n")
    
    print(f"\nSaved: {report_path}")

if __name__ == "__main__":
    main()

