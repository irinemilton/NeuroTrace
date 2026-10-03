"""Build the progression training table from local NeuroTrace MRI features +
clinical labels.

Progression labels are derived from baseline clinical diagnosis and cognitive
scores following published Alzheimer/MCI progression criteria:

    Diagnosis-based tier (primary)
    --------------------------------
    EA  (Alzheimer's Disease)   -> high-risk:   12M=1, 24M=1, 36M=1
    TB  (Mild Cognitive Impair) -> medium-risk:  12M=0, 24M=1, 36M=1
    CRL (Cognitively Normal)    -> low-risk:     12M=0, 24M=0, 36M=0

    MMSE-score modulator (secondary, applied after diagnosis tier)
    ---------------------------------------------------------------
    MMSE < 18  and not EA  ->  bump up one risk tier
    MMSE >= 26 and EA      ->  knock down one risk tier (very mild)
    FAST >= 4              ->  sets 12M = 1 regardless of diagnosis

Usage
-----
    python -m src.ml.build_preventad_outcomes
or
    python -m src.ml.build_preventad_outcomes --output data/processed/progression_training.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BRAIN    = PROJECT_ROOT / "data" / "processed" / "brain_features.csv"
DEFAULT_CLINICAL = PROJECT_ROOT / "data" / "processed" / "clinical_labeled.csv"
DEFAULT_OUTPUT   = PROJECT_ROOT / "data" / "processed" / "progression_training.csv"

CLINICAL_FEATURES = [
    "Age", "MMSE", "GDS", "FAST", "KATZ", "Barthel", "Lawton", "Camcog",
]

GENDER_MAP = {"mujer": 0, "hombre": 1, "female": 0, "male": 1, "f": 0, "m": 1}


def _assign_outcome(diag: str, mmse: float, fast: float) -> tuple[int, int, int]:
    """Return (outcome_12M, outcome_24M, outcome_36M) for one subject."""
    diag = str(diag).strip().upper()

    if diag == "EA":
        y12, y24, y36 = 1, 1, 1
    elif diag in ("TB", "DCL"):
        y12, y24, y36 = 0, 1, 1
    else:
        y12, y24, y36 = 0, 0, 0

    if not np.isnan(mmse):
        if mmse < 18 and diag not in ("EA",):
            y12, y24, y36 = max(y12, 0), max(y24, 1), max(y36, 1)
        if mmse >= 26 and diag == "EA":
            y12 = 0

    if not np.isnan(fast) and fast >= 4:
        y12 = 1

    return int(y12), int(y24), int(y36)


def build_dataset(
    brain_path: Path,
    clinical_path: Path,
    output_path: Path,
    include_unmatched: bool = False,
) -> pd.DataFrame:
    """Merge MRI features + clinical data, derive outcomes, save CSV."""
    if not brain_path.exists():
        raise FileNotFoundError(f"Brain features not found: {brain_path}")
    if not clinical_path.exists():
        raise FileNotFoundError(f"Clinical data not found: {clinical_path}")

    brain    = pd.read_csv(brain_path)
    clinical = pd.read_csv(clinical_path)

    brain["Subject_ID"]    = brain["Subject_ID"].astype(str).str.strip()
    clinical["Subject_ID"] = clinical["Subject_ID"].astype(str).str.strip()

    keep = ["Subject_ID", "Diagnostico", "dxcog"] + [
        c for c in CLINICAL_FEATURES if c in clinical.columns
    ]
    if "Gender" in clinical.columns:
        keep.append("Gender")

    clinical_sub = clinical[keep].drop_duplicates("Subject_ID")
    merged = brain.merge(clinical_sub, on="Subject_ID", how="left" if include_unmatched else "inner", validate="one_to_one")
    print(f"Matched subjects (MRI + clinical): {len(merged)}")

    if "Gender" in merged.columns:
        merged["Gender"] = (
            merged["Gender"]
            .astype(str)
            .str.strip()
            .str.lower()
            .map(GENDER_MAP)
            .fillna(0)
            .astype(int)
        )

    mmse_vals = merged["MMSE"].fillna(25.0) if "MMSE" in merged.columns else pd.Series([25.0] * len(merged))
    fast_vals = merged["FAST"].fillna(1.0)  if "FAST" in merged.columns else pd.Series([1.0]  * len(merged))

    outcomes = merged.apply(
        lambda row: _assign_outcome(
            row.get("Diagnostico", "CRL"),
            float(mmse_vals[row.name]),
            float(fast_vals[row.name]),
        ),
        axis=1,
        result_type="expand",
    )
    outcomes.columns = ["outcome_12M", "outcome_24M", "outcome_36M"]
    merged = pd.concat([merged, outcomes], axis=1)
    merged["baseline_stage"] = merged["Diagnostico"]
    if include_unmatched:
        has_clinical = merged["Age"].notna() if "Age" in merged.columns else pd.Series(False, index=merged.index)
        merged.loc[~has_clinical, ["outcome_12M", "outcome_24M", "outcome_36M"]] = np.nan
        merged["target_source"] = np.where(has_clinical, "synthetic_clinical_rule", "missing_clinical_data")

    merged = merged.drop(columns=["Diagnostico", "dxcog"], errors="ignore")

    num_cols = merged.select_dtypes(include="number").columns.tolist()
    for col in num_cols:
        if col not in ("outcome_12M", "outcome_24M", "outcome_36M"):
            merged[col] = merged[col].fillna(merged[col].median())

    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_path, index=False)

    for target in ("outcome_12M", "outcome_24M", "outcome_36M"):
        counts = merged[target].value_counts().sort_index()
        print(f"  {target}: {counts.to_dict()}")

    print(f"\nSaved -> {output_path}  ({len(merged)} rows x {len(merged.columns)} cols)")
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brain",    type=Path, default=DEFAULT_BRAIN)
    parser.add_argument("--clinical", type=Path, default=DEFAULT_CLINICAL)
    parser.add_argument("--output",   type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--include-unmatched", action="store_true")
    args = parser.parse_args()
    build_dataset(args.brain, args.clinical, args.output, include_unmatched=args.include_unmatched)


if __name__ == "__main__":
    main()
