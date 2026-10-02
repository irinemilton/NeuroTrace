"""Generate 12-, 24-, and 36-month progression probabilities."""

from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODELS = PROJECT_ROOT / "models" / "progression"
HORIZONS = (12, 24, 36)


def predict(features_path: Path, models_dir: Path, output_path: Path) -> pd.DataFrame:
    frame = pd.read_csv(features_path)
    if "Subject_ID" not in frame.columns:
        raise ValueError("Features must contain Subject_ID.")
    result = frame[["Subject_ID"]].copy()
    for months in HORIZONS:
        model_path = models_dir / f"neurotrace_progression_{months}M.joblib"
        if not model_path.exists():
            raise FileNotFoundError(f"Progression model not found: {model_path}")
        model = joblib.load(model_path)
        probabilities = model.predict_proba(frame)
        classes = list(model.classes_)
        positive = 1 if 1 in classes else classes[-1]
        result[f"progression_{months}M_probability"] = probabilities[
            :, classes.index(positive)
        ]
        result[f"progression_{months}M_class"] = model.predict(frame)
    result.to_csv(output_path, index=False)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--models-dir", type=Path, default=DEFAULT_MODELS)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    predict(args.features, args.models_dir, args.output)
    print(f"Saved progression predictions to {args.output}")


if __name__ == "__main__":
    main()
