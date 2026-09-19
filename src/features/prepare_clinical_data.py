from pathlib import Path
import re
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CLINICAL_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "Clinical_data"
    / "clinical_data_corrected.csv"
)

MRI_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "mri"
    / "T1_original"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

OUTPUT_FILE = OUTPUT_DIR / "clinical_matched.csv"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("NeuroTrace - Clinical Data Preparation")
    print("=" * 60)

    # --------------------------------------------------------
    # Load clinical data
    # --------------------------------------------------------

    print("\nLoading clinical data...")

    clinical = pd.read_csv(CLINICAL_FILE)

    print(f"Clinical records: {len(clinical)}")

    # --------------------------------------------------------
    # Clean Codigo
    # --------------------------------------------------------

    clinical["Codigo_clean"] = pd.to_numeric(
        clinical["Codigo"].astype(str).str.strip(),
        errors="coerce"
    )

    # --------------------------------------------------------
    # Read MRI subject IDs
    # --------------------------------------------------------

    mri_files = sorted(MRI_DIR.glob("*.nii.gz"))

    print(f"MRI files found: {len(mri_files)}")

    mri_records = []

    for mri_file in mri_files:

        match = re.search(
            r"_(\d+)\.nii\.gz$",
            mri_file.name
        )

        if not match:
            print(
                f"WARNING: Could not extract ID from {mri_file.name}"
            )
            continue

        codigo = int(match.group(1))

        # Group prefix: crl, ea, etc.
        group = mri_file.name.split("_")[0]

        mri_records.append(
            {
                "Subject_ID": mri_file.name.replace(
                    ".nii.gz", ""
                ),
                "Codigo_clean": codigo,
                "MRI_Group": group,
            }
        )

    mri_df = pd.DataFrame(mri_records)

    # --------------------------------------------------------
    # Match MRI subjects with clinical records
    # --------------------------------------------------------

    matched = mri_df.merge(
        clinical,
        on="Codigo_clean",
        how="left",
        suffixes=("_MRI", "_Clinical")
    )

    # --------------------------------------------------------
    # Check duplicate matches
    # --------------------------------------------------------

    duplicates = matched[
        matched["Codigo_clean"].duplicated(keep=False)
    ]

    if len(duplicates) > 0:

        print("\nWARNING: Duplicate clinical matches found:")

        print(
            duplicates[
                ["Subject_ID", "Codigo_clean"]
            ].to_string(index=False)
        )

    # --------------------------------------------------------
    # Normalize Dxo
    # --------------------------------------------------------

    matched["Dxo"] = (
        matched["Dxo"]
        .astype("string")
        .str.strip()
    )

    # Standardize capitalization
    matched["Dxo"] = matched["Dxo"].replace(
        {
            "control": "Control",
            "CONTROL": "Control",
            "bd": "BD",
            "BD ": "BD",
            "ad": "AD",
            "AD ": "AD",
            "dcl": "DCL",
            "DCl": "DCL",
            "DCL ": "DCL",
        }
    )

    # --------------------------------------------------------
    # Show matching statistics
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("MATCHING RESULTS")
    print("=" * 60)

    print(
        f"\nMRI subjects: "
        f"{len(matched)}"
    )

    print(
        f"Clinical matches: "
        f"{matched['Dxo'].notna().sum()}"
    )

    print(
        f"Missing Dxo: "
        f"{matched['Dxo'].isna().sum()}"
    )

    print("\nDxo distribution:")

    print(
        matched["Dxo"]
        .value_counts(dropna=False)
        .to_string()
    )

    # --------------------------------------------------------
    # Save all matched subjects
    # --------------------------------------------------------

    matched.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\nSaved complete matched dataset:")

    print(OUTPUT_FILE)

    # --------------------------------------------------------
    # Save only labeled subjects
    # --------------------------------------------------------

    labeled = matched[
        matched["Dxo"].isin(
            ["Control", "BD", "AD", "DCL"]
        )
    ].copy()

    labeled_file = (
        OUTPUT_DIR
        / "clinical_labeled.csv"
    )

    labeled.to_csv(
        labeled_file,
        index=False
    )

    print("\nSaved labeled dataset:")

    print(labeled_file)

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)

    print(f"All MRI subjects : {len(matched)}")
    print(f"Labeled subjects  : {len(labeled)}")
    print(f"Unlabeled subjects: {len(matched) - len(labeled)}")

    print("\nLabeled class distribution:")

    print(
        labeled["Dxo"]
        .value_counts()
        .to_string()
    )

    print("\nFirst 10 matched subjects:")

    print(
        matched[
            [
                "Subject_ID",
                "Codigo_clean",
                "MRI_Group",
                "Dxo",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()