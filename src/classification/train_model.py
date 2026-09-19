from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "neurotrace_ml_dataset.csv"
)

MODEL_DIR = PROJECT_ROOT / "models" / "classification"

MODEL_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# SETTINGS
# ============================================================

TARGET = "Dxo"

RANDOM_STATE = 42

TEST_SIZE = 0.20


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print("=" * 60)
    print("NeuroTrace - ML Training")
    print("=" * 60)

    if not DATA_FILE.exists():

        raise FileNotFoundError(
            f"Dataset not found:\n{DATA_FILE}"
        )

    df = pd.read_csv(DATA_FILE)

    print(f"\nDataset shape: {df.shape}")

    if TARGET not in df.columns:

        raise ValueError(
            f"Target column '{TARGET}' not found."
        )

    return df


# ============================================================
# PREPARE FEATURES
# ============================================================

def prepare_features(df):

    # --------------------------------------------------------
    # Remove identifiers and target
    # --------------------------------------------------------

    columns_to_remove = [
        "Subject_ID",
        TARGET,
        "Codigo_clean",
        "MRI_Group",
    ]

    columns_to_remove = [
        col
        for col in columns_to_remove
        if col in df.columns
    ]

    X = df.drop(
        columns=columns_to_remove
    ).copy()

    y = df[TARGET].copy()

    # --------------------------------------------------------
    # Convert categorical columns
    # --------------------------------------------------------

    categorical_columns = X.select_dtypes(
        include=["object", "string", "category"]
    ).columns.tolist()

    if categorical_columns:

        print(
            "\nCategorical columns detected:"
        )

        print(categorical_columns)

        X = pd.get_dummies(
            X,
            columns=categorical_columns,
            drop_first=True
        )

    # --------------------------------------------------------
    # Force numeric
    # --------------------------------------------------------

    X = X.apply(
        pd.to_numeric,
        errors="coerce"
    )

    # --------------------------------------------------------
    # Remove columns that are completely empty
    # --------------------------------------------------------

    empty_columns = X.columns[
        X.isna().all()
    ].tolist()

    if empty_columns:

        print(
            f"\nRemoving {len(empty_columns)} "
            "completely empty columns."
        )

        X = X.drop(
            columns=empty_columns
        )

    print(
        f"\nFeature count: {X.shape[1]}"
    )

    print(
        f"Samples: {X.shape[0]}"
    )

    return X, y


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

def split_data(X, y):

    print("\nCreating stratified train/test split...")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    print(
        f"Training samples: {len(X_train)}"
    )

    print(
        f"Testing samples : {len(X_test)}"
    )

    print("\nTraining distribution:")

    print(
        y_train.value_counts()
    )

    print("\nTesting distribution:")

    print(
        y_test.value_counts()
    )

    return (
        X_train,
        X_test,
        y_train,
        y_test,
    )


# ============================================================
# BUILD MODELS
# ============================================================

def build_models():

    models = {

        "LogisticRegression": Pipeline(
            steps=[
                (
                    "imputer",
                    SimpleImputer(
                        strategy="median"
                    ),
                ),
                (
                    "scaler",
                    StandardScaler(),
                ),
                (
                    "classifier",
                    LogisticRegression(
                        max_iter=5000,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),

        "RandomForest": Pipeline(
            steps=[
                (
                    "imputer",
                    SimpleImputer(
                        strategy="median"
                    ),
                ),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=300,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
    }

    return models


# ============================================================
# EVALUATE MODEL
# ============================================================

def evaluate_model(
    name,
    model,
    X_test,
    y_test,
):

    predictions = model.predict(X_test)

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    f1 = f1_score(
        y_test,
        predictions,
        average="macro",
        zero_division=0,
    )

    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    print(
        f"\nAccuracy: {accuracy:.4f}"
    )

    print(
        f"Macro F1: {f1:.4f}"
    )

    print("\nClassification report:")

    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0,
        )
    )

    print("Confusion matrix:")

    print(
        confusion_matrix(
            y_test,
            predictions
        )
    )

    return accuracy, f1


# ============================================================
# MAIN
# ============================================================

def main():

    df = load_data()

    # --------------------------------------------------------
    # Safety check
    # --------------------------------------------------------

    print("\nClass distribution:")

    print(
        df[TARGET]
        .value_counts()
    )

    if len(df) < 20:

        print(
            "\nWARNING:"
            "\nThe dataset currently contains too few "
            "subjects for meaningful ML training."
        )

        print(
            "\nThis is expected while MRI processing "
            "is still running."
        )

        return

    # --------------------------------------------------------
    # Prepare
    # --------------------------------------------------------

    X, y = prepare_features(
        df
    )

    # --------------------------------------------------------
    # Split
    # --------------------------------------------------------

    (
        X_train,
        X_test,
        y_train,
        y_test,
    ) = split_data(
        X,
        y
    )

    # --------------------------------------------------------
    # Models
    # --------------------------------------------------------

    models = build_models()

    results = []

    # --------------------------------------------------------
    # Train
    # --------------------------------------------------------

    for name, model in models.items():

        print(
            f"\nTraining {name}..."
        )

        model.fit(
            X_train,
            y_train
        )

        accuracy, f1 = evaluate_model(
            name,
            model,
            X_test,
            y_test,
        )

        results.append(
            {
                "Model": name,
                "Accuracy": accuracy,
                "Macro_F1": f1,
            }
        )

        # Save model
        model_file = (
            MODEL_DIR
            / f"{name}.joblib"
        )

        joblib.dump(
            model,
            model_file
        )

        print(
            f"\nSaved model:"
            f"\n{model_file}"
        )

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    results_df = pd.DataFrame(
        results
    )

    results_file = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "model_results.csv"
    )

    results_df.to_csv(
        results_file,
        index=False
    )

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)

    print(
        results_df.to_string(
            index=False
        )
    )

    print(
        f"\nResults saved to:"
        f"\n{results_file}"
    )


if __name__ == "__main__":
    main()