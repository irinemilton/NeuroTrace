import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Tuple, Dict, List, Optional
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
import warnings
warnings.filterwarnings("ignore")

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False


TARGET_MAP = {0: "Control", 1: "BD", 2: "DCL", 3: "AD"}
TARGET_NAMES = ["Control", "BD", "DCL", "AD"]


def load_features(feature_csv: str) -> Tuple[pd.DataFrame, pd.Series]:
    """Load feature matrix and separate features/target."""
    df = pd.read_csv(feature_csv)
    if "subject_id" in df.columns:
        df = df.drop(columns=["subject_id"])
    if "Codigo" in df.columns:
        df = df.drop(columns=["Codigo"])

    target_col = "Dxo_label"
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in features")

    y = df[target_col].astype(int)
    X = df.drop(columns=[target_col])

    X = X.select_dtypes(include=[np.number])

    return X, y


def get_models() -> Dict[str, Pipeline]:
    """Get dictionary of model pipelines to evaluate."""
    models = {
        "logistic_regression": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
        ]),
        "random_forest": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", RandomForestClassifier(n_estimators=500, class_weight="balanced", random_state=42, n_jobs=-1)),
        ]),
        "svm": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", SVC(kernel="rbf", class_weight="balanced", probability=True, random_state=42)),
        ]),
    }
    if HAS_XGB:
        models["xgboost"] = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", XGBClassifier(
                n_estimators=300,
                max_depth=5,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1,
                eval_metric="mlogloss",
            )),
        ])
    return models


def evaluate_model(model: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> Dict:
    """Evaluate model and return metrics."""
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test) if hasattr(model, "predict_proba") else None

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_test, y_pred),
        "macro_f1": f1_score(y_test, y_pred, average="macro"),
        "weighted_f1": f1_score(y_test, y_pred, average="weighted"),
        "classification_report": classification_report(y_test, y_pred, target_names=TARGET_NAMES, output_dict=True),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
    }

    if y_proba is not None:
        try:
            metrics["roc_auc_ovr"] = roc_auc_score(y_test, y_proba, multi_class="ovr")
            metrics["roc_auc_ovo"] = roc_auc_score(y_test, y_proba, multi_class="ovo")
        except ValueError:
            metrics["roc_auc_ovr"] = None
            metrics["roc_auc_ovo"] = None

    return metrics


def cross_validate_model(model: Pipeline, X: pd.DataFrame, y: pd.Series, cv: int = 5) -> Dict:
    """Perform stratified cross-validation."""
    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)

    scoring = ["accuracy", "balanced_accuracy", "f1_macro", "f1_weighted"]
    cv_results = {}

    for score_name in scoring:
        scores = cross_val_score(model, X, y, cv=skf, scoring=score_name, n_jobs=-1)
        cv_results[score_name] = {
            "mean": float(np.mean(scores)),
            "std": float(np.std(scores)),
            "scores": scores.tolist(),
        }

    return cv_results


def train_best_model(
    feature_csv: str,
    output_dir: str,
    test_size: float = 0.2,
    cv: int = 5,
) -> Tuple[Pipeline, Dict]:
    """Train and evaluate multiple models, save the best one."""
    X, y = load_features(feature_csv)
    print(f"Loaded features: {X.shape[0]} samples, {X.shape[1]} features")
    print(f"Class distribution:\n{y.value_counts().sort_index()}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=42
    )

    models = get_models()
    results = {}

    print("\n" + "=" * 60)
    print("MODEL EVALUATION")
    print("=" * 60)

    for name, model in models.items():
        print(f"\nTraining {name}...")
        model.fit(X_train, y_train)

        cv_results = cross_validate_model(model, X_train, y_train, cv=cv)
        test_metrics = evaluate_model(model, X_test, y_test)

        results[name] = {
            "cv": cv_results,
            "test": test_metrics,
        }

        print(f"  CV Balanced Acc: {cv_results['balanced_accuracy']['mean']:.4f} (+/- {cv_results['balanced_accuracy']['std']:.4f})")
        print(f"  Test Balanced Acc: {test_metrics['balanced_accuracy']:.4f}")
        print(f"  Test Macro F1: {test_metrics['macro_f1']:.4f}")

    best_model_name = max(results.keys(), key=lambda k: results[k]["test"]["balanced_accuracy"])
    best_model = models[best_model_name]
    best_model.fit(X, y)

    print(f"\n{'=' * 60}")
    print(f"BEST MODEL: {best_model_name}")
    print(f"{'=' * 60}")

    final_metrics = evaluate_model(best_model, X_test, y_test)
    print(f"Test Accuracy: {final_metrics['accuracy']:.4f}")
    print(f"Test Balanced Accuracy: {final_metrics['balanced_accuracy']:.4f}")
    print(f"Test Macro F1: {final_metrics['macro_f1']:.4f}")
    print(f"\nClassification Report:\n{classification_report(y_test, best_model.predict(X_test), target_names=TARGET_NAMES)}")

    os.makedirs(output_dir, exist_ok=True)
    model_path = os.path.join(output_dir, "best_model.joblib")
    joblib.dump(best_model, model_path)
    print(f"\nBest model saved to {model_path}")

    results_path = os.path.join(output_dir, "evaluation_results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Evaluation results saved to {results_path}")

    feature_names = X.columns.tolist()
    feature_names_path = os.path.join(output_dir, "feature_names.json")
    with open(feature_names_path, "w") as f:
        json.dump(feature_names, f, indent=2)
    print(f"Feature names saved to {feature_names_path}")

    return best_model, results


def predict_subject(
    model_path: str,
    feature_csv: str,
    subject_id: str,
) -> Dict:
    """Predict diagnosis for a single subject."""
    model = joblib.load(model_path)

    with open(os.path.join(os.path.dirname(model_path), "feature_names.json")) as f:
        feature_names = json.load(f)

    df = pd.read_csv(feature_csv)
    subj_row = df[df["subject_id"] == subject_id] if "subject_id" in df.columns else df[df["Codigo"] == int(subject_id)]

    if subj_row.empty:
        raise ValueError(f"Subject {subject_id} not found in features")

    X = subj_row[feature_names]
    pred = model.predict(X)[0]
    proba = model.predict_proba(X)[0]

    return {
        "subject_id": subject_id,
        "predicted_label": int(pred),
        "predicted_class": TARGET_MAP[pred],
        "probabilities": {TARGET_MAP[i]: float(p) for i, p in enumerate(proba)},
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Train classification models")
    parser.add_argument("--features", default="data/processed/features.csv")
    parser.add_argument("--output-dir", default="models/classification")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--cv", type=int, default=5)
    args = parser.parse_args()

    train_best_model(args.features, args.output_dir, args.test_size, args.cv)