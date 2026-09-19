from pathlib import Path
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BRAIN_FEATURES = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "brain_features.csv"
)

CLINICAL_DATA = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "clinical_labeled.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "neurotrace_ml_dataset.csv"
)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("NeuroTrace - ML Dataset Merge")
    print("=" * 60)

    # --------------------------------------------------------
    # Check files
    # --------------------------------------------------------

    if not BRAIN_FEATURES.exists():
        print("\nERROR: brain_features.csv not found.")
        print(BRAIN_FEATURES)
        return

    if not CLINICAL_DATA.exists():
        print("\nERROR: clinical_labeled.csv not found.")
        print(CLINICAL_DATA)
        return

    # --------------------------------------------------------
    # Load datasets
    # --------------------------------------------------------

    print("\nLoading brain features...")
    brain = pd.read_csv(BRAIN_FEATURES)

    print(f"Brain feature rows: {len(brain)}")
    print(f"Brain feature columns: {len(brain.columns)}")

    print("\nLoading clinical data...")
    clinical = pd.read_csv(CLINICAL_DATA)

    print(f"Clinical rows: {len(clinical)}")

    # --------------------------------------------------------
    # Keep only necessary clinical columns for now
    # --------------------------------------------------------

    clinical_columns = [
        "Subject_ID",
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

    available_columns = [
        col for col in clinical_columns
        if col in clinical.columns
    ]

    clinical = clinical[available_columns].copy()

    # --------------------------------------------------------
    # Remove duplicate Subject_ID
    # --------------------------------------------------------

    clinical = clinical.drop_duplicates(
        subset=["Subject_ID"]
    )

    brain = brain.drop_duplicates(
        subset=["Subject_ID"]
    )

    # --------------------------------------------------------
    # Merge
    # --------------------------------------------------------

    print("\nMerging datasets...")

    merged = brain.merge(
        clinical,
        on="Subject_ID",
        how="inner"
    )

    # --------------------------------------------------------
    # Remove rows without Dxo
    # --------------------------------------------------------

    merged["Dxo"] = (
        merged["Dxo"]
        .astype("string")
        .str.strip()
    )

    merged = merged[
        merged["Dxo"].isin(
            ["Control", "BD", "AD", "DCL"]
        )
    ].copy()

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    merged.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("MERGE COMPLETE")
    print("=" * 60)

    print(f"\nFinal subjects: {len(merged)}")
    print(f"Final columns : {len(merged.columns)}")

    print("\nClass distribution:")

    print(
        merged["Dxo"]
        .value_counts()
        .to_string()
    )

    print("\nSaved to:")
    print(OUTPUT_FILE)

    print("\nSubjects included:")

    print(
        merged["Subject_ID"]
        .tolist()
    )


if __name__ == "__main__":
    main()