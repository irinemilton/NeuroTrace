from pathlib import Path

import joblib
import pandas as pd
import shap


ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = ROOT / "models" / "classification" / "RandomForest.joblib"
DATA_PATH = ROOT / "data" / "processed" / "neurotrace_ml_dataset.csv"

OUTPUT_DIR = ROOT / "data" / "processed" / "explanations"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = OUTPUT_DIR / "global_feature_importance.csv"


print("Loading model...")
model = joblib.load(MODEL_PATH)

print("Loading dataset...")
df = pd.read_csv(DATA_PATH)

target = "Dxo"

drop_columns = [
    "Subject_ID",
    "Dxo",
    "Codigo_clean",
    "MRI_Group",
]

X = df.drop(
    columns=[c for c in drop_columns if c in df.columns],
    errors="ignore"
)

# Convert categorical columns using the same approach
# used during model training.
X = pd.get_dummies(X, drop_first=False)

# Convert everything to numeric
X = X.apply(pd.to_numeric, errors="coerce")

# Align with the features used by the trained model
feature_names = model.feature_names_in_

X = X.reindex(columns=feature_names, fill_value=0)

X = X.fillna(X.median(numeric_only=True))
X = X.fillna(0)

print(f"Samples: {len(X)}")
print(f"Features: {X.shape[1]}")

# Get the Random Forest classifier from the pipeline
classifier = model.named_steps["classifier"]

print("Creating SHAP explainer...")

explainer = shap.TreeExplainer(classifier)

shap_values = explainer.shap_values(X)

print("Calculating feature importance...")

# SHAP output can differ depending on SHAP version.
if isinstance(shap_values, list):
    importance = sum(
        abs(values).mean(axis=0)
        for values in shap_values
    ) / len(shap_values)

elif hasattr(shap_values, "values"):
    values = shap_values.values

    if values.ndim == 3:
        importance = abs(values).mean(axis=(0, 2))
    else:
        importance = abs(values).mean(axis=0)

else:
    values = shap_values

    if values.ndim == 3:
        importance = abs(values).mean(axis=(0, 2))
    else:
        importance = abs(values).mean(axis=0)


result = pd.DataFrame({
    "Feature": feature_names,
    "Mean_Absolute_SHAP": importance,
})

result = result.sort_values(
    "Mean_Absolute_SHAP",
    ascending=False
)

result.to_csv(
    OUTPUT_PATH,
    index=False
)

print()
print("Top 20 features:")
print(result.head(20).to_string(index=False))

print()
print(f"Saved to:")
print(OUTPUT_PATH)