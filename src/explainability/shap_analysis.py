import os
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False
    shap = None

from src.classification.train import load_features, TARGET_MAP, TARGET_NAMES


def compute_shap_values(
    model_path: str,
    feature_csv: str,
    max_samples: int = 100,
    output_dir: str = "results/explainability",
) -> Dict:
    """Compute SHAP values for the trained model."""
    if not HAS_SHAP:
        raise ImportError("SHAP not installed. Install with: pip install shap")

    model = joblib.load(model_path)

    with open(os.path.join(os.path.dirname(model_path), "feature_names.json")) as f:
        feature_names = json.load(f)

    X, y = load_features(feature_csv)
    X = X[feature_names]

    if len(X) > max_samples:
        idx = np.random.choice(len(X), max_samples, replace=False)
        X_sample = X.iloc[idx]
        y_sample = y.iloc[idx]
    else:
        X_sample = X
        y_sample = y

    print(f"Computing SHAP values for {len(X_sample)} samples...")
    print(f"Model type: {type(model.named_steps['clf']).__name__}")

    clf = model.named_steps["clf"]
    scaler = model.named_steps["scaler"]
    X_scaled = scaler.transform(X_sample)

    if hasattr(clf, "tree_"):
        explainer = shap.TreeExplainer(clf)
        shap_values = explainer.shap_values(X_scaled)
    elif hasattr(clf, "coef_"):
        masker = shap.maskers.Independent(X_scaled, max_samples=100)
        explainer = shap.LinearExplainer(clf, masker=masker)
        shap_values = explainer.shap_values(X_scaled)
    else:
        masker = shap.maskers.Independent(X_scaled, max_samples=100)
        explainer = shap.KernelExplainer(clf.predict_proba, masker, link="logit")
        shap_values = explainer.shap_values(X_scaled)

    os.makedirs(output_dir, exist_ok=True)

    np.save(os.path.join(output_dir, "shap_values.npy"), shap_values)
    X_sample.to_csv(os.path.join(output_dir, "shap_X_sample.csv"), index=False)
    y_sample.to_csv(os.path.join(output_dir, "shap_y_sample.csv"), index=False)
    with open(os.path.join(output_dir, "feature_names.json"), "w") as f:
        json.dump(feature_names, f)

    print(f"SHAP values saved to {output_dir}")
    return {
        "shap_values": shap_values,
        "X_sample": X_sample,
        "y_sample": y_sample,
        "feature_names": feature_names,
    }


def plot_shap_summary(
    shap_values,
    X_sample: pd.DataFrame,
    feature_names: List[str],
    output_dir: str,
    class_names: List[str] = TARGET_NAMES,
):
    """Generate SHAP summary plots."""
    os.makedirs(output_dir, exist_ok=True)

    if isinstance(shap_values, list):
        for i, class_name in enumerate(class_names):
            plt.figure(figsize=(10, 8))
            shap.summary_plot(
                shap_values[i],
                X_sample.values,
                feature_names=feature_names,
                show=False,
                plot_type="bar",
            )
            plt.title(f"SHAP Feature Importance - {class_name}")
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, f"shap_summary_bar_{class_name}.png"), dpi=150)
            plt.close()

            plt.figure(figsize=(10, 8))
            shap.summary_plot(
                shap_values[i],
                X_sample.values,
                feature_names=feature_names,
                show=False,
            )
            plt.title(f"SHAP Summary - {class_name}")
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, f"shap_summary_{class_name}.png"), dpi=150)
            plt.close()
    else:
        plt.figure(figsize=(10, 8))
        shap.summary_plot(
            shap_values,
            X_sample.values,
            feature_names=feature_names,
            show=False,
            plot_type="bar",
        )
        plt.title("SHAP Feature Importance")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "shap_summary_bar.png"), dpi=150)
        plt.close()

        plt.figure(figsize=(10, 8))
        shap.summary_plot(
            shap_values,
            X_sample.values,
            feature_names=feature_names,
            show=False,
        )
        plt.title("SHAP Summary")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "shap_summary.png"), dpi=150)
        plt.close()


def plot_shap_dependence(
    shap_values,
    X_sample: pd.DataFrame,
    feature_names: List[str],
    output_dir: str,
    top_k: int = 10,
    class_idx: int = 0,
):
    """Generate SHAP dependence plots for top features."""
    if not HAS_SHAP:
        return

    os.makedirs(output_dir, exist_ok=True)

    if isinstance(shap_values, list):
        vals = shap_values[class_idx]
    else:
        vals = shap_values

    mean_abs_shap = np.mean(np.abs(vals), axis=0)
    top_indices = np.argsort(mean_abs_shap)[-top_k:]

    for idx in top_indices:
        feature_name = feature_names[idx]
        safe_name = feature_name.replace("/", "_").replace("\\", "_")
        plt.figure(figsize=(8, 6))
        shap.dependence_plot(
            idx,
            vals,
            X_sample.values,
            feature_names=feature_names,
            show=False,
        )
        plt.title(f"SHAP Dependence: {feature_name} (Class: {TARGET_NAMES[class_idx] if isinstance(shap_values, list) else 'All'})")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f"shap_dependence_{safe_name}.png"), dpi=150)
        plt.close()


def get_global_feature_importance(
    shap_values,
    feature_names: List[str],
    class_names: List[str] = TARGET_NAMES,
) -> pd.DataFrame:
    """Compute global feature importance from SHAP values."""
    if isinstance(shap_values, list):
        n_classes = len(shap_values)
        importance_data = {}
        for i, class_name in enumerate(class_names[:n_classes]):
            mean_abs = np.mean(np.abs(shap_values[i]), axis=0)
            importance_data[f"{class_name}_mean_abs_shap"] = mean_abs
        importance_data["overall_mean_abs_shap"] = np.mean([
            np.mean(np.abs(shap_values[i]), axis=0) for i in range(n_classes)
        ], axis=0)
    else:
        importance_data = {
            "mean_abs_shap": np.mean(np.abs(shap_values), axis=0),
        }

    importance_df = pd.DataFrame(importance_data, index=feature_names)
    importance_df = importance_df.sort_values(
        by=importance_df.columns[-1], ascending=False
    )
    return importance_df


def explain_subject(
    model_path: str,
    feature_csv: str,
    subject_id: str,
    output_dir: str = "results/explainability",
) -> Dict:
    """Generate SHAP explanation for a single subject."""
    if not HAS_SHAP:
        raise ImportError("SHAP not installed. Install with: pip install shap")

    model = joblib.load(model_path)

    with open(os.path.join(os.path.dirname(model_path), "feature_names.json")) as f:
        feature_names = json.load(f)

    df = pd.read_csv(feature_csv)
    subj_row = df[df["subject_id"] == subject_id] if "subject_id" in df.columns else df[df["Codigo"] == int(subject_id)]

    if subj_row.empty:
        raise ValueError(f"Subject {subject_id} not found")

    X_subj = subj_row[feature_names].values.reshape(1, -1)
    scaler = model.named_steps["scaler"]
    clf = model.named_steps["clf"]
    X_scaled = scaler.transform(X_subj)

    pred = clf.predict(X_scaled)[0]
    proba = clf.predict_proba(X_scaled)[0]

    if hasattr(clf, "tree_"):
        explainer = shap.TreeExplainer(clf)
        shap_vals = explainer.shap_values(X_scaled)
    elif hasattr(clf, "coef_"):
        masker = shap.maskers.Independent(X_scaled, max_samples=100)
        explainer = shap.LinearExplainer(clf, masker=masker)
        shap_vals = explainer.shap_values(X_scaled)
    else:
        X_bg = scaler.transform(df[feature_names].sample(min(100, len(df)), random_state=42))
        masker = shap.maskers.Independent(X_bg, max_samples=100)
        explainer = shap.KernelExplainer(clf.predict_proba, masker, link="logit")
        shap_vals = explainer.shap_values(X_scaled)

    os.makedirs(output_dir, exist_ok=True)

    if isinstance(shap_vals, list):
        shap_vals_class = shap_vals[pred][0]
    else:
        shap_vals_class = shap_vals[0]

    feature_impact = list(zip(feature_names, shap_vals_class))
    feature_impact.sort(key=lambda x: abs(x[1]), reverse=True)

    explanation = {
        "subject_id": subject_id,
        "predicted_class": TARGET_MAP[pred],
        "predicted_label": int(pred),
        "probabilities": {TARGET_MAP[i]: float(p) for i, p in enumerate(proba)},
        "top_features": [
            {"feature": f, "shap_value": float(v), "feature_value": float(X_subj[0][i])}
            for i, (f, v) in enumerate(feature_impact[:20])
        ],
    }

    with open(os.path.join(output_dir, f"explanation_{subject_id}.json"), "w") as f:
        json.dump(explanation, f, indent=2)

    if HAS_SHAP:
        plt.figure(figsize=(10, 6))
        shap.plots.force(
            explainer.expected_value[pred] if isinstance(explainer.expected_value, np.ndarray) else explainer.expected_value,
            shap_vals_class,
            X_subj[0],
            feature_names=feature_names,
            matplotlib=True,
            show=False,
        )
        plt.title(f"SHAP Force Plot - Subject {subject_id} (Predicted: {TARGET_MAP[pred]})")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f"shap_force_{subject_id}.png"), dpi=150)
        plt.close()

    print(f"Explanation saved for subject {subject_id}")
    return explanation


def run_full_explainability(
    model_path: str,
    feature_csv: str,
    output_dir: str = "results/explainability",
    max_samples: int = 100,
):
    """Run complete SHAP explainability analysis."""
    if not HAS_SHAP:
        print("SHAP not installed. Skipping explainability analysis.")
        return

    print("Running SHAP explainability analysis...")
    result = compute_shap_values(model_path, feature_csv, max_samples, output_dir)

    plot_shap_summary(
        result["shap_values"],
        result["X_sample"],
        result["feature_names"],
        output_dir,
    )

    if isinstance(result["shap_values"], list):
        for i in range(len(TARGET_NAMES)):
            plot_shap_dependence(
                result["shap_values"],
                result["X_sample"],
                result["feature_names"],
                output_dir,
                top_k=5,
                class_idx=i,
            )
    else:
        plot_shap_dependence(
            result["shap_values"],
            result["X_sample"],
            result["feature_names"],
            output_dir,
            top_k=10,
        )

    importance_df = get_global_feature_importance(
        result["shap_values"],
        result["feature_names"],
    )
    importance_df.to_csv(os.path.join(output_dir, "global_feature_importance.csv"))
    print(f"Global feature importance saved to {output_dir}/global_feature_importance.csv")
    print("\nTop 20 Global Features:")
    print(importance_df.head(20))

    return importance_df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SHAP explainability analysis")
    parser.add_argument("--model", default="models/classification/best_model.joblib")
    parser.add_argument("--features", default="data/processed/features.csv")
    parser.add_argument("--output-dir", default="results/explainability")
    parser.add_argument("--max-samples", type=int, default=100)
    parser.add_argument("--subject", type=str, help="Explain specific subject")
    args = parser.parse_args()

    if args.subject:
        explain_subject(args.model, args.features, args.subject, args.output_dir)
    else:
        run_full_explainability(args.model, args.features, args.output_dir, args.max_samples)