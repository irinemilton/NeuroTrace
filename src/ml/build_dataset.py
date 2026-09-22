from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

BRAIN_FEATURES = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "brain_features.csv"
)

CLINICAL_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "Clinical_data"
    / "clinical_data_corrected.csv"
)

ID_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "Clinical_data"
    / "clinical_data_id_age_gender.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "neurotrace_ml_dataset.csv"
)


def main():

    print("=" * 60)
    print("NEUROTRACE ML DATASET BUILDER")
    print("=" * 60)

    # ---------------------------------------------------------
    # 1. Load MRI features
    # ---------------------------------------------------------

    brain = pd.read_csv(BRAIN_FEATURES)

    print(f"MRI feature rows : {len(brain)}")
    print(f"MRI feature cols : {len(brain.columns)}")

    # ---------------------------------------------------------
    # 2. Load clinical files
    # ---------------------------------------------------------

    clinical = pd.read_csv(CLINICAL_FILE)
    ids = pd.read_csv(ID_FILE)

    print(f"Clinical rows     : {len(clinical)}")
    print(f"ID mapping rows   : {len(ids)}")

    # ---------------------------------------------------------
    # 3. Normalize IDs
    # ---------------------------------------------------------

    ids["Subject_ID"] = (
        ids["Subject"].astype(str).str.strip()
        + "_"
        + ids["id"].astype(str).str.strip()
    )

    clinical["Codigo"] = pd.to_numeric(
        clinical["Codigo"],
        errors="coerce",
    )

    ids["id"] = pd.to_numeric(
        ids["id"],
        errors="coerce",
    )

    # ---------------------------------------------------------
    # 4. Prepare clinical lookup
    # ---------------------------------------------------------

    clinical_lookup = clinical.drop_duplicates(
        subset="Codigo",
        keep="first",
    ).copy()

    # Rename clinical Age so there is no collision
    if "Age" in clinical_lookup.columns:
        clinical_lookup = clinical_lookup.rename(
            columns={"Age": "Clinical_Age"}
        )

    # ---------------------------------------------------------
    # 5. MRI -> demographic information
    # ---------------------------------------------------------

    demographic_columns = [
        "Subject_ID",
        "id",
        "Age",
        "gender",
    ]

    merged = brain.merge(
        ids[demographic_columns],
        on="Subject_ID",
        how="left",
        validate="one_to_one",
    )

    # ---------------------------------------------------------
    # 6. Demographics -> clinical record
    # ---------------------------------------------------------

    merged = merged.merge(
        clinical_lookup,
        left_on="id",
        right_on="Codigo",
        how="left",
        validate="one_to_one",
    )

    # ---------------------------------------------------------
    # 7. Merge validation
    # ---------------------------------------------------------

    print()
    print("MERGE VALIDATION")
    print("-" * 60)

    print("Final rows:", len(merged))

    print(
        "Missing clinical matches:",
        merged["Codigo"].isna().sum(),
    )

    print(
        "Missing demographic age:",
        merged["Age"].isna().sum(),
    )

    print(
        "Missing gender:",
        merged["gender"].isna().sum(),
    )

    # ---------------------------------------------------------
    # 8. Candidate targets
    # ---------------------------------------------------------

    print()
    print("CANDIDATE TARGETS")
    print("-" * 60)

    for column in [
        "Diagnostico",
        "Dxo",
        "dxcog",
        "Detcog",
    ]:

        if column in merged.columns:

            print(f"\n{column}:")

            print(
                merged[column]
                .value_counts(dropna=False)
                .to_string()
            )

    # ---------------------------------------------------------
    # 9. Save
    # ---------------------------------------------------------

    merged.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print("=" * 60)
    print("DATASET CREATED")
    print("=" * 60)

    print(f"Rows    : {len(merged)}")
    print(f"Columns : {len(merged.columns)}")
    print(f"Output  : {OUTPUT_FILE}")

    print("=" * 60)


if __name__ == "__main__":
    main()