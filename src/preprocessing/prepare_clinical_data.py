import os
import pandas as pd
import numpy as np

def clean_clinical_data(input_path: str, output_path: str) -> None:
    """Load, clean, and encode the clinical CSV data.

    Steps performed:
    1. Load CSV with low_memory=False to avoid dtype warnings.
    2. Strip whitespace from column names.
    3. Drop rows where the target label ``Dxo`` is missing or not one of the four
       diagnostic categories (Control, BD, DCL, AD).
    4. Select a core set of clinical features required for the ML pipeline.
    5. Encode categorical variables (currently ``Gender``).
    6. Convert numeric columns to proper numeric types and perform simple
       median imputation for missing values.
    7. Encode the target ``Dxo`` as an integer label.
    8. Save the cleaned dataframe to ``output_path``.
    """
    # 1. Load CSV
    print(f"Loading clinical data from {input_path}")
    df = pd.read_csv(input_path, low_memory=False)

    # 2. Clean column names
    df.columns = df.columns.str.strip()

    # 3. Keep only rows with a valid target label
    if "Dxo" not in df.columns:
        raise KeyError("Column 'Dxo' not found in the clinical CSV")
    df = df.dropna(subset=["Dxo"]).copy()
    df["Dxo"] = df["Dxo"].astype(str).str.strip()
    valid_targets = {"Control", "BD", "DCL", "AD"}
    df = df[df["Dxo"].isin(valid_targets)]

    # 4. Core clinical features (add/remove as needed later)
    core_features = [
        "Codigo",
        "Dxo",
        "Age",
        "Gender",
        "MMSE",
        "Camcog",
        "GDS",
        "FAST",
        "KATZ",
        "Barthel",
        "Lawton",
    ]
    missing = [c for c in core_features if c not in df.columns]
    if missing:
        print(f"Warning: missing expected columns {missing}")
    selected = [c for c in core_features if c in df.columns]
    df = df[selected].copy()

    # 5. Encode Gender (Spanish values from dataset)
    if "Gender" in df.columns:
        df["Gender"] = df["Gender"].astype(str).str.strip().str.lower()
        gender_map = {"hombre": 0, "mujer": 1}
        df["Gender"] = df["Gender"].map(gender_map)
        if df["Gender"].isna().any():
            median_gender = df["Gender"].median()
            df["Gender"] = df["Gender"].fillna(median_gender)

    # 6. Numeric conversion & median imputation
    numeric_cols = [c for c in ["Age", "MMSE", "Camcog", "GDS", "FAST", "KATZ", "Barthel", "Lawton"] if c in df.columns]
    for col in numeric_cols:
        df[col] = df[col].astype(str).str.replace(",", ".").str.replace(" ", "").str.strip()
        df[col] = pd.to_numeric(df[col], errors="coerce")
        median_val = df[col].median()
        df[col] = df[col].fillna(median_val)

    # 7. Encode target label
    target_map = {"Control": 0, "BD": 1, "DCL": 2, "AD": 3}
    df["Dxo_label"] = df["Dxo"].map(target_map)

    # 8. Save cleaned data
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Cleaned clinical data saved to {output_path}")
    print(f"Number of subjects after cleaning: {len(df)}")
    print(df["Dxo"].value_counts())

if __name__ == "__main__":
    INPUT_CSV = os.path.join("data", "raw", "Clinical_data", "clinical_data_corrected.csv")
    OUTPUT_CSV = os.path.join("data", "processed", "clinical_cleaned.csv")
    clean_clinical_data(INPUT_CSV, OUTPUT_CSV)
