from pathlib import Path
from typing import Optional
from src.features.measurements import measure_subject
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import settings


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_MRI_DIR = (
    settings.RAW_DATA_DIR
    / "mri"
    / "T1_original"
)

UNEST_EVAL_DIR = (
    settings.UNEST_MODEL_DIR
    / "eval"
)

CLINICAL_FILE = settings.CLINICAL_CLEANED_CSV

BRAIN_FEATURES_FILE = (
    settings.PROCESSED_DATA_DIR
    / "brain_features.csv"
)

ML_DATASET_FILE = (
    settings.PROCESSED_DATA_DIR
    / "neurotrace_ml_dataset.csv"
)


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Backend API for NeuroTrace MRI analysis, "
        "brain segmentation, quantitative features, "
        "and ML classification."
    ),
    version=settings.VERSION,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST MODELS
# ============================================================

class AnalysisRequest(BaseModel):
    subject_id: str


# ============================================================
# DATA HELPERS
# ============================================================

def load_csv(path: Path) -> pd.DataFrame:
    """
    Safely load a CSV file.

    Returns an empty DataFrame when the file does not exist
    or cannot be read.
    """

    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except Exception as exc:
        print(
            f"Warning: failed to read {path}: {exc}"
        )
        return pd.DataFrame()


def convert_value(value):
    """
    Convert pandas / NumPy values into JSON-safe values.
    """

    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass

    return value


def get_subject_row(
    df: pd.DataFrame,
    column: str,
    subject_id: str,
):
    """
    Return the first matching row for a subject.
    """

    if df.empty:
        return None

    if column not in df.columns:
        return None

    matches = df[
        df[column].astype(str).str.strip()
        == subject_id
    ]

    if matches.empty:
        return None

    return matches.iloc[0]


def row_to_dict(
    row,
    columns,
    exclude: Optional[set[str]] = None,
) -> dict:
    """
    Convert a pandas row into a JSON-safe dictionary.
    """

    exclude = exclude or set()

    result = {}

    for column in columns:

        if column in exclude:
            continue

        result[column] = convert_value(
            row[column]
        )

    return result


# ============================================================
# SUBJECT HELPERS
# ============================================================

def get_raw_subjects() -> list[str]:
    """
    Return subject IDs for available raw MRI files.
    """

    if not RAW_MRI_DIR.exists():
        return []

    subjects = []

    for file in RAW_MRI_DIR.glob("*.nii.gz"):

        subject_id = file.name.removesuffix(
            ".nii.gz"
        )

        subjects.append(subject_id)

    return sorted(subjects)


def get_segmentation_path(
    subject_id: str,
) -> Optional[Path]:
    """
    Find the actual UNesT segmentation output
    for a subject.
    """

    path = (
        UNEST_EVAL_DIR
        / subject_id
        / f"{subject_id}_trans.nii.gz"
    )

    if path.exists():
        return path

    return None


def get_subject_status(
    subject_id: str,
) -> dict:
    """
    Return processing status for one subject.
    """

    mri_path = (
        RAW_MRI_DIR
        / f"{subject_id}.nii.gz"
    )

    segmentation_path = (
        get_segmentation_path(subject_id)
    )

    return {
        "subject_id": subject_id,
        "mri_available": mri_path.exists(),
        "segmentation_available": (
            segmentation_path is not None
        ),
        "segmentation_path": (
            str(segmentation_path)
            if segmentation_path
            else None
        ),
    }


# ============================================================
# CLINICAL DATA
# ============================================================

def get_clinical_data(
    subject_id: str,
) -> Optional[dict]:
    """
    Return cleaned clinical information for a subject.
    """

    df = load_csv(
        CLINICAL_FILE
    )

    row = get_subject_row(
        df,
        "Codigo",
        subject_id,
    )

    if row is None:
        return None

    return row_to_dict(
        row,
        df.columns,
    )


# ============================================================
# BRAIN FEATURES
# ============================================================

def get_brain_features(
    subject_id: str,
) -> Optional[dict]:
    """
    Return extracted MRI brain features for a subject.

    Source:
        data/processed/brain_features.csv

    This contains:
        - 132 anatomical regional volumes
        - derived bilateral volumes
        - hippocampal asymmetry
    """

    df = load_csv(
        BRAIN_FEATURES_FILE
    )

    row = get_subject_row(
        df,
        "Subject_ID",
        subject_id,
    )

    if row is None:
        return None

    return row_to_dict(
        row,
        df.columns,
        exclude={"Subject_ID"},
    )


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "NeuroTrace API",
        "version": settings.VERSION,
    }


# ============================================================
# PROJECT STATUS
# ============================================================

@app.get("/api/status")
def project_status():

    raw_subjects = get_raw_subjects()

    segmented_subjects = [
        subject_id
        for subject_id in raw_subjects
        if get_segmentation_path(
            subject_id
        )
    ]

    return {
        "project": settings.PROJECT_NAME,

        "raw_mri_available": (
            RAW_MRI_DIR.exists()
        ),

        "total_mri_subjects": (
            len(raw_subjects)
        ),

        "segmented_subjects": (
            len(segmented_subjects)
        ),

        "segmentation_running": (
            len(segmented_subjects)
            < len(raw_subjects)
        ),

        "clinical_data_available": (
            CLINICAL_FILE.exists()
        ),

        "ml_dataset_available": (
            ML_DATASET_FILE.exists()
        ),

        "model_available": (
            settings.BEST_MODEL_PATH.exists()
        ),
    }


# ============================================================
# SEGMENTATION STATUS
# ============================================================

@app.get("/api/segmentation/status")
def segmentation_status():

    subjects = get_raw_subjects()

    results = [
        get_subject_status(
            subject_id
        )
        for subject_id in subjects
    ]

    completed = sum(
        item["segmentation_available"]
        for item in results
    )

    return {
        "total": len(results),
        "completed": completed,
        "remaining": (
            len(results) - completed
        ),
        "subjects": results,
    }


# ============================================================
# SUBJECTS
# ============================================================

@app.get("/api/subjects")
def get_subjects():

    subjects = get_raw_subjects()

    result = []

    for subject_id in subjects:

        status = get_subject_status(
            subject_id
        )

        result.append({
            "subject_id": subject_id,

            "mri_available": status[
                "mri_available"
            ],

            "segmentation_available": status[
                "segmentation_available"
            ],
        })

    return {
        "count": len(result),
        "subjects": result,
    }


# ============================================================
# SUBJECT DETAILS
# ============================================================

@app.get("/api/subjects/{subject_id}")
def get_subject(subject_id: str):

    subject_id = subject_id.strip()

    # --------------------------------------------------------
    # Verify subject
    # --------------------------------------------------------

    subject_status = get_subject_status(
        subject_id
    )

    if not subject_status[
        "mri_available"
    ]:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Subject '{subject_id}' "
                "not found."
            ),
        )


@app.get("/api/subjects/{subject_id}/measurements")
def get_subject_measurements(subject_id: str):
    segmentation_path = get_segmentation_path(subject_id)

    if not segmentation_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Segmentation not found for subject: {subject_id}",
        )

    try:
        measurements = measure_subject(segmentation_path)

        return {
            "subject_id": subject_id,
            "status": "success",
            "measurements": measurements,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Measurement failed for {subject_id}: {exc}",
        )
    # --------------------------------------------------------
    # Clinical data
    # --------------------------------------------------------

    clinical_data = get_clinical_data(
        subject_id
    )

    # --------------------------------------------------------
    # Real extracted MRI features
    # --------------------------------------------------------

    imaging_features = get_brain_features(
        subject_id
    )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {
        **subject_status,

        "clinical_data": clinical_data,

        "imaging_features": (
            imaging_features
        ),
    }


# ============================================================
# SEGMENTATION FILE
# ============================================================

@app.get(
    "/api/subjects/{subject_id}/segmentation"
)
def get_segmentation(
    subject_id: str,
):

    segmentation_path = (
        get_segmentation_path(
            subject_id
        )
    )

    if segmentation_path is None:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Segmentation for "
                f"'{subject_id}' is not "
                "available yet."
            ),
        )

    return {
        "subject_id": subject_id,
        "available": True,
        "path": str(
            segmentation_path
        ),
        "filename": (
            segmentation_path.name
        ),
        "size_bytes": (
            segmentation_path.stat().st_size
        ),
    }


# ============================================================
# ANALYSIS
# ============================================================

@app.post("/api/analyze")
def analyze_subject(
    request: AnalysisRequest,
):

    subject_id = (
        request.subject_id.strip()
    )

    status = get_subject_status(
        subject_id
    )

    # --------------------------------------------------------
    # Subject validation
    # --------------------------------------------------------

    if not status[
        "mri_available"
    ]:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Subject '{subject_id}' "
                "not found."
            ),
        )

    # --------------------------------------------------------
    # Segmentation status
    # --------------------------------------------------------

    if not status[
        "segmentation_available"
    ]:

        return {
            "status": "processing",

            "subject_id": subject_id,

            "message": (
                "MRI exists, but UNesT "
                "segmentation has not "
                "completed yet."
            ),
        }

    # --------------------------------------------------------
    # ML model will be connected here later.
    # --------------------------------------------------------

    if not settings.BEST_MODEL_PATH.exists():

        return {
            "status": "ready",

            "subject_id": subject_id,

            "segmentation_available": True,

            "prediction_available": False,

            "message": (
                "Segmentation completed. "
                "ML model is not trained yet."
            ),
        }

    # --------------------------------------------------------
    # ML model available
    # --------------------------------------------------------

    return {
        "status": "ready",

        "subject_id": subject_id,

        "segmentation_available": True,

        "prediction_available": True,

        "message": (
            "Segmentation completed and "
            "ML model is available."
        ),
    }