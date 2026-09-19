from pathlib import Path

import joblib
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_DIR = (
    PROJECT_ROOT
    / "models"
    / "classification"
)

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "neurotrace_ml_dataset.csv"
)


# ============================================================
# SETTINGS
# ============================================================

MODEL_NAME = "RandomForest"

MODEL_FILE = (
    MODEL_DIR
    / f"{MODEL_NAME}.joblib"
)


# ============================================================
# LOAD MODEL
# ============================================================

def load_model():

    if not MODEL_FILE.exists():

        raise FileNotFoundError(
            f"\nTrained model not found:\n{MODEL_FILE}\n\n"
            "Train the model first using train_model.py."
        )

    print("Loading model...")
    model = joblib.load(MODEL_FILE)

    return model


# ============================================================
# PREPARE FEATURES
# ============================================================

def prepare_features(df):

    columns_to_remove = [
        "Subject_ID",
        "Dxo",
        "Codigo_clean",
        "MRI_Group",
    ]

    columns_to_remove = [
        column
        for column in columns_to_remove
        if column in df.columns
    ]

    X = df.drop(
        columns=columns_to_remove
    ).copy()

    # Convert categorical features
    categorical_columns = X.select_dtypes(
        include=["object", "string", "category"]
    ).columns.tolist()

    if categorical_columns:

        X = pd.get_dummies(
            X,
            columns=categorical_columns,
            drop_first=True,
        )

    X = X.apply(
        pd.to_numeric,
        errors="coerce",
    )

    return X


# ============================================================
# PREDICT
# ============================================================

def main():

    print("=" * 60)
    print("NeuroTrace - Prediction")
    print("=" * 60)

    # --------------------------------------------------------
    # Check dataset
    # --------------------------------------------------------

    if not DATA_FILE.exists():

        raise FileNotFoundError(
            f"Dataset not found:\n{DATA_FILE}"
        )

    df = pd.read_csv(DATA_FILE)

    print(
        f"\nLoaded dataset: "
        f"{len(df)} subjects"
    )

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    model = load_model()

    # --------------------------------------------------------
    # Prepare features
    # --------------------------------------------------------

    X = prepare_features(df)

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # The training script and prediction script must eventually
    # use exactly the same feature columns.
    #
    # For the current prototype dataset, this check prevents
    # silent feature mismatches.
    # --------------------------------------------------------

    expected_features = getattr(
        model,
        "feature_names_in_",
        None
    )

    if expected_features is not None:

        expected_features = list(
            expected_features
        )

        for column in expected_features:

            if column not in X.columns:
                X[column] = 0

        X = X[expected_features]

    # --------------------------------------------------------
    # Prediction
    # --------------------------------------------------------

    predictions = model.predict(X)

    df["Prediction"] = predictions

    # --------------------------------------------------------
    # Probability
    # --------------------------------------------------------

    if hasattr(model, "predict_proba"):

        probabilities = model.predict_proba(X)

        classes = model.classes_

        for index, class_name in enumerate(classes):

            df[
                f"Probability_{class_name}"
            ] = probabilities[:, index]

        df["Prediction_Confidence"] = (
            probabilities.max(axis=1)
        )

    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    print("\nPredictions:")
    print("-" * 60)

    display_columns = [
        "Subject_ID",
        "Prediction",
    ]

    if "Dxo" in df.columns:
        display_columns.append("Dxo")

    if "Prediction_Confidence" in df.columns:
        display_columns.append(
            "Prediction_Confidence"
        )

    print(
        df[display_columns]
        .to_string(index=False)
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    output_file = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "neurotrace_predictions.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    print("\nPredictions saved to:")
    print(output_file)


if __name__ == "__main__":
    main()