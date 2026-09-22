from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "neurotrace_ml_dataset.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "neurotrace_alzheimer_kaggle.csv"
)


def main():

    print("=" * 60)
    print("NEUROTRACE ALZHEIMER'S DATASET BUILDER")
    print("=" * 60)

    df = pd.read_csv(INPUT_FILE)

    # ---------------------------------------------------------
    # Keep only subjects with a documented Dxo value
    # ---------------------------------------------------------

    df = df[df["Dxo"].notna()].copy()

    # ---------------------------------------------------------
    # Create Alzheimer's binary target
    # ---------------------------------------------------------

    df["Alzheimer_Target"] = (
        df["Dxo"]
        .astype(str)
        .str.strip()
        .str.upper()
        .eq("AD")
        .astype(int)
    )

    # ---------------------------------------------------------
    # Keep MRI features + demographics + target
    # ---------------------------------------------------------

    mri_columns = [
        column
        for column in df.columns
        if column != "Subject_ID"
        and (
            column.endswith("_volume_mm3")
            or column.endswith("_total_volume_mm3")
            or column.endswith("_asymmetry_mm3")
        )
    ]

    selected_columns = [
        "Subject_ID",
        "Age",
        "gender",
    ] + mri_columns + [
        "Alzheimer_Target"
    ]

    output = df[selected_columns].copy()

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    print()
    print("DATASET VALIDATION")
    print("-" * 60)

    print("Rows:", len(output))
    print("Columns:", len(output.columns))

    print()
    print("Target distribution:")
    print(
        output["Alzheimer_Target"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print()
    print("Missing values:")
    print(output.isna().sum().sum())

    print()
    print("MRI features:", len(mri_columns))

    # ---------------------------------------------------------
    # Save
    # ---------------------------------------------------------

    output.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print("=" * 60)
    print("ALZHEIMER'S DATASET CREATED")
    print("=" * 60)

    print("Output:")
    print(OUTPUT_FILE)

    print("=" * 60)


if __name__ == "__main__":
    main()