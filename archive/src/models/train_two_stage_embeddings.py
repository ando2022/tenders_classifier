"""
Train Stage-1 (kw_hit_selected) using multilingual sentence embeddings
and compare with the TF-IDF baseline via out-of-fold metrics.

Saves:
- models/stage1_embeddings.pkl
- models/metrics_comparison.json
"""

import argparse
import json
import os
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score, classification_report
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import cross_val_predict
import joblib


def evaluate_oof(y_true: np.ndarray, oof_probs: np.ndarray) -> dict:
    pred = (oof_probs >= 0.5).astype(int)
    return {
        "auc": float(roc_auc_score(y_true, oof_probs)),
        "ap": float(average_precision_score(y_true, oof_probs)),
        "report@0.5": classification_report(y_true, pred, digits=3)
    }


def run_tfidf_baseline(texts: pd.Series, y: np.ndarray, n_splits: int = 5) -> dict:
    pre = ColumnTransformer([
        ("tfidf", TfidfVectorizer(max_features=20000, ngram_range=(1, 2), min_df=2), 0)
    ])
    clf = LogisticRegression(max_iter=2000, class_weight="balanced")
    pipe = Pipeline([("prep", pre), ("clf", clf)])
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    oof = cross_val_predict(pipe, texts.values.reshape(-1, 1), y, cv=skf, method="predict_proba")[:, 1]
    pipe.fit(texts.values.reshape(-1, 1), y)
    return {
        "oof": oof,
        "model": pipe
    }


def run_embeddings(texts: pd.Series, y: np.ndarray, n_splits: int = 5) -> dict:
    from sentence_transformers import SentenceTransformer
    model_name = "paraphrase-multilingual-MiniLM-L12-v2"
    st_model = SentenceTransformer(model_name)
    X = st_model.encode(texts.fillna("").tolist(), normalize_embeddings=True)
    clf = LogisticRegression(max_iter=2000, class_weight="balanced")
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    # For OOF, we need to avoid leakage: produce fold-wise preds
    oof = np.zeros(len(y))
    for train_idx, test_idx in skf.split(X, y):
        clf_fold = LogisticRegression(max_iter=2000, class_weight="balanced")
        clf_fold.fit(X[train_idx], y[train_idx])
        oof[test_idx] = clf_fold.predict_proba(X[test_idx])[:, 1]
    clf.fit(X, y)  # final model
    return {
        "oof": oof,
        "model": {"encoder": model_name, "clf": clf}
    }


def run_tfidf_char(texts: pd.Series, y: np.ndarray, n_splits: int = 5) -> dict:
    pre = ColumnTransformer([
        ("tfidf_char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, max_features=60000), 0)
    ])
    clf = LogisticRegression(max_iter=2000, class_weight="balanced")
    pipe = Pipeline([("prep", pre), ("clf", clf)])
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    oof = cross_val_predict(pipe, texts.values.reshape(-1, 1), y, cv=skf, method="predict_proba")[:, 1]
    pipe.fit(texts.values.reshape(-1, 1), y)
    return {"oof": oof, "model": pipe}


def run_blended(texts: pd.Series, y: np.ndarray, n_splits: int = 5) -> dict:
    # Build embeddings once
    from sentence_transformers import SentenceTransformer
    model_name = "paraphrase-multilingual-MiniLM-L12-v2"
    st_model = SentenceTransformer(model_name)
    X_emb = st_model.encode(texts.fillna("").tolist(), normalize_embeddings=True)

    # TF-IDF char features
    tfidf = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, max_features=60000)
    X_tfidf = tfidf.fit_transform(texts.fillna("").tolist())

    # Concatenate (sparse + dense) -> convert dense to sparse
    from scipy import sparse
    X_blend = sparse.hstack([X_tfidf, sparse.csr_matrix(X_emb)])

    clf = LogisticRegression(max_iter=2000, class_weight="balanced")
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    oof = np.zeros(len(y))
    for train_idx, test_idx in skf.split(X_blend, y):
        clf_fold = LogisticRegression(max_iter=2000, class_weight="balanced")
        clf_fold.fit(X_blend[train_idx], y[train_idx])
        oof[test_idx] = clf_fold.predict_proba(X_blend[test_idx])[:, 1]

    clf.fit(X_blend, y)
    return {"oof": oof, "model": {"tfidf": tfidf, "encoder": model_name, "clf": clf}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    if args.input.endswith(".parquet"):
        df = pd.read_parquet(args.input)
    else:
        df = pd.read_csv(args.input)

    text_col = "Topic"
    if text_col not in df.columns:
        raise ValueError(f"Missing text column '{text_col}' in input")
    if "kw_hit_selected" not in df.columns:
        raise ValueError("Missing target 'kw_hit_selected'")

    texts = df[text_col].fillna("").astype(str)
    y = df["kw_hit_selected"].astype(int).values

    # Baseline TF-IDF (word/bigram)
    base = run_tfidf_baseline(texts, y)
    base_metrics = evaluate_oof(y, base["oof"]) 

    # Character n-gram TF-IDF
    charm = run_tfidf_char(texts, y)
    char_metrics = evaluate_oof(y, charm["oof"]) 

    # Embeddings
    emb = run_embeddings(texts, y)
    emb_metrics = evaluate_oof(y, emb["oof"]) 

    # Blended
    blend = run_blended(texts, y)
    blend_metrics = evaluate_oof(y, blend["oof"]) 

    # Save models
    joblib.dump(base["model"], os.path.join(args.outdir, "stage1_tfidf.pkl"))
    joblib.dump(charm["model"], os.path.join(args.outdir, "stage1_tfidf_char.pkl"))
    joblib.dump(emb["model"], os.path.join(args.outdir, "stage1_embeddings.pkl"))
    joblib.dump(blend["model"], os.path.join(args.outdir, "stage1_blended.pkl"))

    # Save metrics
    metrics = {"tfidf_word": base_metrics, "tfidf_char": char_metrics, "embeddings": emb_metrics, "blended": blend_metrics}
    with open(os.path.join(args.outdir, "metrics_comparison.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    print("TFIDF-W AUC:", round(metrics["tfidf_word"]["auc"], 4), "AP:", round(metrics["tfidf_word"]["ap"], 4))
    print("TFIDF-C AUC:", round(metrics["tfidf_char"]["auc"], 4), "AP:", round(metrics["tfidf_char"]["ap"], 4))
    print("EMB    AUC:", round(metrics["embeddings"]["auc"], 4), "AP:", round(metrics["embeddings"]["ap"], 4))
    print("BLEND  AUC:", round(metrics["blended"]["auc"], 4), "AP:", round(metrics["blended"]["ap"], 4))


if __name__ == "__main__":
    main()


