"""Train 12-, 24-, and 36-month cognitive-progression models.

Uses a Gradient Boosting classifier (scikit-learn GradientBoostingClassifier)
which outperforms plain logistic regression on small tabular neuroimaging
datasets. Falls back gracefully to logistic regression when sample count is
very low for a given horizon.

Input
-----
data/processed/progression_training.csv
    One row per subject. Must contain:
      - Subject_ID
      - outcome_12M, outcome_24M, outcome_36M  (binary 0/1)
      - All remaining columns are treated as features.

Output
------
models/progression/
    neurotrace_progression_12M.joblib
    neurotrace_progression_24M.joblib
    neurotrace_progression_36M.joblib
    training_report.json

Usage
-----
    python -m src.ml.train_progression
    python -m src.ml.train_progression --data data/processed/progression_training.csv
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, roc_auc_score, classification_report
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

PROJECT_ROOT  = Path(__file__).resolve().parents[2]
DEFAULT_DATA  = PROJECT_ROOT / "data" / "processed" / "progression_training.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "models" / "progression"
HORIZONS = (12, 24, 36)

# Minimum samples-per-class required to use GradientBoosting; below this we
# fall back to logistic regression.
GB_MIN_SAMPLES_PER_CLASS = 5


def _target_column(frame: pd.DataFrame, months: int) -> str:
    candidates = (
        f"outcome_{months}M",
        f"progression_{months}M",
        f"target_{months}M",
        f"synthetic_progression_{months}M",
    )
    matches = [c for c in candidates if c in frame.columns]
    if not matches:
        raise ValueError(
            f"Missing {months}M target. Expected one of: {', '.join(candidates)}"
        )
    return matches[0]


def _build_preprocessor(numeric: list[str], categorical: list[str]) -> ColumnTransformer:
    return ColumnTransformer(
        [
            (
                "numeric",
                Pipeline([
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scale",   StandardScaler()),
                ]),
                numeric,
            ),
            (
                "categorical",
                Pipeline([
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    ("onehot",  OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                ]),
                categorical,
            ),
        ],
        remainder="drop",
    )


def train(data_path: Path, output_dir: Path) -> dict:
    if not data_path.exists():
        raise FileNotFoundError(
            f"Training data not found: {data_path}\n"
            "Run:  python -m src.ml.build_preventad_outcomes"
        )

    frame = pd.read_csv(data_path)
    if "Subject_ID" not in frame.columns:
        raise ValueError("Training data must contain Subject_ID.")

    print(f"Loaded {len(frame)} subjects, {len(frame.columns)} columns")

    excluded = {"Subject_ID", "target_source", "baseline_stage"}
    target_columns = {_target_column(frame, m) for m in HORIZONS}
    feature_columns = [
        c for c in frame.columns
        if c not in excluded and c not in target_columns
    ]
    if not feature_columns:
        raise ValueError("No baseline MRI/clinical features were found.")

    numeric    = frame[feature_columns].select_dtypes(include="number").columns.tolist()
    categorical = [c for c in feature_columns if c not in numeric]

    preprocessor = _build_preprocessor(numeric, categorical)
    output_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "subjects":  len(frame),
        "features":  feature_columns,
        "horizons":  {},
    }

    for months in HORIZONS:
        target  = _target_column(frame, months)
        usable  = frame[frame[target].notna()].copy()
        y       = usable[target].astype(int)
        X       = usable[feature_columns]
        counts  = y.value_counts()

        if y.nunique() < 2:
            print(f"  [{months}M] WARNING: only one class present — skipping.")
            continue
        if counts.min() < 2:
            print(f"  [{months}M] WARNING: fewer than 2 samples in minority class — skipping.")
            continue

        print(f"\n--- {months}M horizon ---")
        print(f"  Subjects: {len(usable)}   Class distribution: {counts.to_dict()}")

        min_class_n = int(counts.min())

        # Choose classifier based on sample size
        if min_class_n >= GB_MIN_SAMPLES_PER_CLASS:
            classifier = GradientBoostingClassifier(
                n_estimators=200,
                max_depth=3,
                learning_rate=0.05,
                subsample=0.8,
                min_samples_leaf=2,
                random_state=42,
            )
            clf_name = "GradientBoosting"
        else:
            classifier = LogisticRegression(
                max_iter=2000, class_weight="balanced", random_state=42
            )
            clf_name = "LogisticRegression (fallback)"

        model = Pipeline([
            ("features",    preprocessor),
            ("classifier",  classifier),
        ])

        folds = min(5, min_class_n)
        cv    = StratifiedKFold(n_splits=folds, shuffle=True, random_state=42)

        proba_cv = cross_val_predict(model, X, y, cv=cv, method="predict_proba")
        pred_cv  = cross_val_predict(model, X, y, cv=cv)

        # Fit on full data
        model.fit(X, y)
        labels         = model.classes_
        positive       = 1 if 1 in labels else labels[-1]
        positive_index = list(labels).index(positive)

        bal_acc_cv = balanced_accuracy_score(y, pred_cv)

        metrics: dict = {
            "classifier":        clf_name,
            "cv_balanced_accuracy": round(float(bal_acc_cv), 4),
            "classes":           [str(v) for v in labels],
            "samples":           len(usable),
            "class_distribution": counts.to_dict(),
        }

        if len(labels) == 2:
            auc = roc_auc_score(y, proba_cv[:, positive_index])
            metrics["cv_roc_auc"] = round(float(auc), 4)
            print(f"  Classifier: {clf_name}")
            print(f"  CV Balanced Accuracy: {bal_acc_cv:.3f}")
            print(f"  CV ROC-AUC:           {auc:.3f}")
        else:
            print(f"  Classifier: {clf_name}")
            print(f"  CV Balanced Accuracy: {bal_acc_cv:.3f}")

        path = output_dir / f"neurotrace_progression_{months}M.joblib"
        joblib.dump(model, path)
        print(f"  Saved -> {path}")
        report["horizons"][f"{months}M"] = {"model": str(path), **metrics}

    report_path = output_dir / "training_report.json"
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"\nTraining report -> {report_path}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data",       type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = train(args.data, args.output_dir)
    print("\n=== Summary ===")
    for horizon, metrics in report["horizons"].items():
        auc_str = f"  ROC-AUC={metrics.get('cv_roc_auc', 'N/A')}" if "cv_roc_auc" in metrics else ""
        print(
            f"  {horizon}: {metrics['samples']} subjects | "
            f"BalAcc={metrics['cv_balanced_accuracy']:.3f}{auc_str}"
        )


if __name__ == "__main__":
    main()
