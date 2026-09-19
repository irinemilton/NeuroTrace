from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = ROOT / "data" / "processed"

BRAIN_FEATURES_FILE = (
    PROCESSED_DIR / "brain_features.csv"
)

CLINICAL_FILE = (
    PROCESSED_DIR / "clinical_labeled.csv"
)

ML_DATASET_FILE = (
    PROCESSED_DIR / "neurotrace_ml_dataset.csv"
)


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="NeuroTrace API",
    description=(
        "Backend API for AI-assisted multimodal "
        "brain MRI analysis and research classification."
    ),
    version="0.1.0",
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
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "NeuroTrace API",
        "version": "0.1.0",
    }


# ============================================================
# PROJECT STATUS
# ============================================================

@app.get("/api/status")
def project_status():

    return {
        "brain_features_available":
            BRAIN_FEATURES_FILE.exists(),

        "clinical_data_available":
            CLINICAL_FILE.exists(),

        "ml_dataset_available":
            ML_DATASET_FILE.exists(),

        "model_available":
            (
                ROOT
                / "models"
                / "classification"
                / "RandomForest.joblib"
            ).exists(),
    }


# ============================================================
# SUBJECTS
# ============================================================

@app.get("/api/subjects")
def get_subjects():

    if not ML_DATASET_FILE.exists():

        return {
            "count": 0,
            "subjects": [],
            "message": (
                "ML dataset is not available yet. "
                "UNesT segmentation may still be running."
            ),
        }

    import pandas as pd

    df = pd.read_csv(
        ML_DATASET_FILE
    )

    if "Subject_ID" not in df.columns:

        return {
            "count": 0,
            "subjects": [],
        }

    subjects = (
        df["Subject_ID"]
        .dropna()
        .astype(str)
        .tolist()
    )

    return {
        "count": len(subjects),
        "subjects": subjects,
    }


# ============================================================
# SUBJECT DETAILS
# ============================================================

@app.get("/api/subjects/{subject_id}")
def get_subject(subject_id: str):

    if not ML_DATASET_FILE.exists():

        raise HTTPException(
            status_code=404,
            detail="ML dataset is not available yet.",
        )

    import pandas as pd

    df = pd.read_csv(
        ML_DATASET_FILE
    )

    if "Subject_ID" not in df.columns:

        raise HTTPException(
            status_code=500,
            detail="Subject_ID column missing.",
        )

    matches = df[
        df["Subject_ID"].astype(str)
        == subject_id
    ]

    if matches.empty:

        raise HTTPException(
            status_code=404,
            detail=f"Subject '{subject_id}' not found.",
        )

    row = matches.iloc[0]

    data = {}

    for column in df.columns:

        value = row[column]

        if pd.isna(value):
            data[column] = None
        else:
            try:
                data[column] = float(value)
            except (ValueError, TypeError):
                data[column] = str(value)

    return {
        "subject_id": subject_id,
        "data": data,
    }


# ============================================================
# ANALYSIS
# ============================================================

@app.post("/api/analyze")
def analyze_subject(
    request: AnalysisRequest
):

    subject_id = request.subject_id

    if not ML_DATASET_FILE.exists():

        return {
            "status": "pending",
            "subject_id": subject_id,
            "message": (
                "Analysis model is not available yet."
            ),
        }

    # The actual trained model will be connected here.
    #
    # For now, return the subject data so the
    # frontend/backend pipeline can be tested.

    import pandas as pd

    df = pd.read_csv(
        ML_DATASET_FILE
    )

    matches = df[
        df["Subject_ID"].astype(str)
        == subject_id
    ]

    if matches.empty:

        raise HTTPException(
            status_code=404,
            detail=f"Subject '{subject_id}' not found.",
        )

    return {
        "status": "ready",
        "subject_id": subject_id,
        "message": (
            "Subject loaded. "
            "ML prediction will be connected "
            "after model training."
        ),
    }