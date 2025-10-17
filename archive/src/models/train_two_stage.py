"""
Two-stage baseline training on standardized SIMAP dataset.

Stage 1: kw_hit_selected
Stage 2: kw_hit_selected_by_sales (on subset where stage1==1)
"""

import argparse
import joblib
import os
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


def build_pipeline(text_col: str, cat_cols: list[str], num_cols: list[str]):
    transformers = [
        ("tfidf", TfidfVectorizer(max_features=2000, ngram_range=(1, 2), min_df=2), text_col),
    ]
    if cat_cols:
        transformers.append(("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols))
    if num_cols:
        transformers.append(("num", "passthrough", num_cols))

    pre = ColumnTransformer(transformers, remainder="drop")
    clf = LogisticRegression(max_iter=2000, class_weight="balanced")
    return Pipeline([("pre", pre), ("clf", clf)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to cleaned parquet/csv")
    ap.add_argument("--outdir", required=True, help="Directory to save models and oof")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    # Load data
    if args.input.endswith(".parquet"):
        df = pd.read_parquet(args.input)
    else:
        df = pd.read_csv(args.input)

    text_col = "Topic"
    cat_cols = [c for c in ["Source"] if c in df.columns]
    num_cols = [c for c in ["Budget_numeric", "Year"] if c in df.columns]

    # Stage 1
    if "kw_hit_selected" not in df.columns:
        raise ValueError("Column 'kw_hit_selected' not found. Add it or populate from your sheet.")

    d1 = df.dropna(subset=[text_col, "kw_hit_selected"]).copy()
    y1 = d1["kw_hit_selected"].astype(int)
    X1 = d1[[text_col] + cat_cols + num_cols]

    pipe1 = build_pipeline(text_col, cat_cols, num_cols)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    oof1 = cross_val_predict(pipe1, X1, y1, cv=skf, method="predict_proba")[:, 1]
    pipe1.fit(X1, y1)

    # Stage 2
    oof2 = None
    p2_global = None
    if "kw_hit_selected_by_sales" in df.columns:
        d2 = df[(df["kw_hit_selected"] == 1) & df["kw_hit_selected_by_sales"].notna()].copy()
        if d2["kw_hit_selected_by_sales"].nunique() > 1 and len(d2) >= 10:
            y2 = d2["kw_hit_selected_by_sales"].astype(int)
            X2 = d2[[text_col] + cat_cols + num_cols]
            pipe2 = build_pipeline(text_col, cat_cols, num_cols)
            oof2 = cross_val_predict(pipe2, X2, y2, cv=skf, method="predict_proba")[:, 1]
            pipe2.fit(X2, y2)
        else:
            pipe2 = None
            p2_global = float(d2["kw_hit_selected_by_sales"].mean()) if len(d2) else 0.5
    else:
        pipe2 = None
        p2_global = 0.5

    # Save artifacts
    joblib.dump({"model": pipe1, "text": text_col, "cats": cat_cols, "nums": num_cols}, os.path.join(args.outdir, "stage1_kw_hit_selected.pkl"))
    if pipe2 is not None:
        joblib.dump({"model": pipe2, "text": text_col, "cats": cat_cols, "nums": num_cols}, os.path.join(args.outdir, "stage2_sales.pkl"))
    else:
        with open(os.path.join(args.outdir, "stage2_sales_prior.txt"), "w") as f:
            f.write(str(p2_global))

    # Save OOF predictions if available
    d1_out = d1[[text_col]].copy()
    d1_out["p_select_oof"] = oof1
    d1_out.to_csv(os.path.join(args.outdir, "oof_stage1.csv"), index=False)
    if oof2 is not None:
        d2_out = d2[[text_col]].copy()
        d2_out["p_sales_oof"] = oof2
        d2_out.to_csv(os.path.join(args.outdir, "oof_stage2.csv"), index=False)

    print("Saved models and OOF predictions to:", args.outdir)


if __name__ == "__main__":
    main()


