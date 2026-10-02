"""Build the longitudinal progression training table.

The outcome file must contain one row per Subject_ID and real follow-up
targets, for example: outcome_12M, outcome_24M, and outcome_36M. Targets
may be binary (0/1) or categorical labels. This script intentionally does
not infer future outcomes from baseline diagnosis.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BRAIN = PROJECT_ROOT / "data" / "processed" / "brain_features.csv"
DEFAULT_CLINICAL = PROJECT_ROOT / "data" / "processed" / "clinical_labeled.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "progression_training.csv"

DEFAULT_CLINICAL_COLUMNS = [
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


def _read_required(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")
    frame = pd.read_csv(path)
    if "Subject_ID" not in frame.columns:
        raise ValueError(f"{label} must contain a Subject_ID column: {path}")
    return frame


def build_dataset(
    brain_path: Path,
    clinical_path: Path,
    outcomes_path: Path,
    output_path: Path,
) -> pd.DataFrame:
    brain = _read_required(brain_path, "MRI feature file")
    clinical = _read_required(clinical_path, "baseline clinical file")
    outcomes = _read_required(outcomes_path, "longitudinal outcome file")

    target_columns = [
        column
        for column in outcomes.columns
        if column.lower() in {
            "outcome_12m", "outcome_24m", "outcome_36m",
            "progression_12m", "progression_24m", "progression_36m",
            "target_12m", "target_24m", "target_36m",
            "synthetic_progression_12m", "synthetic_progression_24m",
            "synthetic_progression_36m",
        }
    ]
    if not target_columns:
        raise ValueError(
            "The outcome file must contain real 12M/24M/36M target columns "
            "(for example outcome_12M, outcome_24M, outcome_36M)."
        )

    brain = brain.drop_duplicates("Subject_ID")
    clinical = clinical.drop_duplicates("Subject_ID")
    outcomes = outcomes.drop_duplicates("Subject_ID")
    clinical_columns = [
        column for column in DEFAULT_CLINICAL_COLUMNS if column in clinical.columns
    ]
    result = brain.merge(
        clinical[["Subject_ID", *clinical_columns]],
        on="Subject_ID",
        how="left",
        validate="one_to_one",
    ).merge(
        outcomes[["Subject_ID", *target_columns]],
        on="Subject_ID",
        how="inner",
        validate="one_to_one",
    )
    if result.empty:
        raise ValueError("No Subject_ID values are shared by MRI and outcome files.")
    result.to_csv(output_path, index=False)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brain", type=Path, default=DEFAULT_BRAIN)
    parser.add_argument("--clinical", type=Path, default=DEFAULT_CLINICAL)
    parser.add_argument("--outcomes", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    dataset = build_dataset(args.brain, args.clinical, args.outcomes, args.output)
    print(f"Saved {len(dataset)} subjects and {len(dataset.columns)} columns to {args.output}")


if __name__ == "__main__":
    main()
