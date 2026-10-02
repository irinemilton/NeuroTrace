from pathlib import Path
from typing import Optional
import json

import joblib
import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.features.measurements import measure_subject
from backend.config import settings
from backend.live_demo import router as live_demo_router
from backend.care import router as care_router


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

CLINICAL_FILE = (
    settings.CLINICAL_CLEANED_CSV
)

BRAIN_FEATURES_FILE = (
    settings.PROCESSED_DATA_DIR
    / "brain_features.csv"
)

ML_DATASET_FILE = (
    settings.PROCESSED_DATA_DIR
    / "neurotrace_ml_dataset.csv"
)


# ============================================================
# ALZHEIMER ML MODEL
# ============================================================

ALZHEIMER_MODEL_DIR = (
    PROJECT_ROOT
    / "models"
    / "alzheimer"
)

ALZHEIMER_MODEL_PATH = (
    ALZHEIMER_MODEL_DIR
    / "neurotrace_alzheimer_model.joblib"
)

ALZHEIMER_METADATA_PATH = (
    ALZHEIMER_MODEL_DIR
    / "neurotrace_feature_metadata.json"
)

ALZHEIMER_MODEL = None

ALZHEIMER_FEATURES: list[str] = []


# ============================================================
# PROGRESSION MODELS (12M / 24M / 36M)
# ============================================================

PROGRESSION_MODEL_DIR = PROJECT_ROOT / "models" / "progression"
PROGRESSION_HORIZONS  = (12, 24, 36)

# Populated by load_progression_models() at startup.
PROGRESSION_MODELS: dict[int, object] = {}


def load_alzheimer_model() -> None:
    """
    Load the trained Alzheimer classifier and
    its exact feature metadata.
    """

    global ALZHEIMER_MODEL
    global ALZHEIMER_FEATURES

    if not ALZHEIMER_MODEL_PATH.exists():

        print(
            "WARNING: Alzheimer model not found:"
        )

        print(
            ALZHEIMER_MODEL_PATH
        )

        return


    try:

        ALZHEIMER_MODEL = joblib.load(
            ALZHEIMER_MODEL_PATH
        )


        if not ALZHEIMER_METADATA_PATH.exists():

            raise RuntimeError(
                "Alzheimer feature metadata file "
                "was not found."
            )


        with open(
            ALZHEIMER_METADATA_PATH,
            "r",
            encoding="utf-8",
        ) as file:

            metadata = json.load(file)


        ALZHEIMER_FEATURES = metadata.get(
            "features",
            [],
        )


        if len(ALZHEIMER_FEATURES) != 141:

            raise RuntimeError(
                "Expected 141 MRI features, "
                f"but metadata contains "
                f"{len(ALZHEIMER_FEATURES)}."
            )


        print(
            "Alzheimer ML model loaded successfully."
        )

        print(
            f"Model path: {ALZHEIMER_MODEL_PATH}"
        )

        print(
            "Expected MRI features: "
            f"{len(ALZHEIMER_FEATURES)}"
        )


    except Exception as exc:

        ALZHEIMER_MODEL = None

        ALZHEIMER_FEATURES = []

        print(
            "WARNING: Failed to load "
            "Alzheimer model:"
        )

        print(exc)


# Load once when backend starts.
load_alzheimer_model()


def load_progression_models() -> None:
    """Load the 12M / 24M / 36M progression joblib models at startup."""
    global PROGRESSION_MODELS
    PROGRESSION_MODELS = {}
    for months in PROGRESSION_HORIZONS:
        path = PROGRESSION_MODEL_DIR / f"neurotrace_progression_{months}M.joblib"
        if path.exists():
            try:
                PROGRESSION_MODELS[months] = joblib.load(path)
                print(f"Progression model {months}M loaded: {path}")
            except Exception as exc:
                print(f"WARNING: Failed to load progression {months}M model: {exc}")
        else:
            print(f"WARNING: Progression model not found: {path}")


load_progression_models()


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Backend API for NeuroTrace MRI "
        "analysis, UNesT brain segmentation, "
        "quantitative measurements, and "
        "Alzheimer ML classification."
    ),
    version=settings.VERSION,
)
app.include_router(care_router)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


app.include_router(live_demo_router, prefix="/api")


# ============================================================
# REQUEST MODELS
# ============================================================

class AnalysisRequest(BaseModel):

    subject_id: str


# ============================================================
# DATA HELPERS
# ============================================================

def load_csv(
    path: Path,
) -> pd.DataFrame:
    """
    Safely load a CSV file.
    """

    if not path.exists():

        return pd.DataFrame()


    try:

        return pd.read_csv(path)

    except Exception as exc:

        print(
            f"Warning: failed to read "
            f"{path}: {exc}"
        )

        return pd.DataFrame()


def convert_value(value):

    """
    Convert pandas / NumPy values into
    JSON-safe values.
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
    Return the first matching subject row.
    """

    if df.empty:
        return None


    if column not in df.columns:
        return None


    matches = df[
        df[column]
        .astype(str)
        .str.strip()
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
    Return subject IDs for available raw
    T1 MRI files.
    """

    if not RAW_MRI_DIR.exists():

        return []


    subjects = []

    for file in RAW_MRI_DIR.glob(
        "*.nii.gz"
    ):

        subject_id = file.name.removesuffix(
            ".nii.gz"
        )

        subjects.append(
            subject_id
        )


    return sorted(subjects)


def get_segmentation_path(
    subject_id: str,
) -> Optional[Path]:

    """
    Find the UNesT segmentation output.
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
    Return processing status for a subject.
    """

    mri_path = (
        RAW_MRI_DIR
        / f"{subject_id}.nii.gz"
    )

    segmentation_path = (
        get_segmentation_path(
            subject_id
        )
    )


    return {

        "subject_id":
            subject_id,

        "mri_available":
            mri_path.exists(),

        "segmentation_available":
            segmentation_path is not None,

        "segmentation_path":
            (
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
    Return the extracted MRI brain features
    for one subject.
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
        exclude={
            "Subject_ID"
        },
    )


# ============================================================
# MODEL FEATURE DATAFRAME
# ============================================================

def get_model_features(
    subject_id: str,
) -> pd.DataFrame:

    """
    Build the exact 141-feature dataframe
    required by the trained model.
    """

    if ALZHEIMER_MODEL is None:

        raise RuntimeError(
            "Alzheimer ML model is not loaded."
        )


    if len(ALZHEIMER_FEATURES) != 141:

        raise RuntimeError(
            "Expected 141 Alzheimer MRI "
            "features, but found "
            f"{len(ALZHEIMER_FEATURES)}."
        )


    df = load_csv(
        BRAIN_FEATURES_FILE
    )


    if df.empty:

        raise RuntimeError(
            "brain_features.csv could "
            "not be loaded."
        )


    row = get_subject_row(
        df,
        "Subject_ID",
        subject_id,
    )


    if row is None:

        raise RuntimeError(
            "No MRI feature row found "
            f"for subject {subject_id}."
        )


    missing_features = [

        feature

        for feature in
        ALZHEIMER_FEATURES

        if feature not in df.columns

    ]


    if missing_features:

        raise RuntimeError(
            "Missing required MRI "
            "features: "
            + ", ".join(
                missing_features
            )
        )


    feature_values = pd.DataFrame(
        [
            [
                row[feature]
                for feature
                in ALZHEIMER_FEATURES
            ]
        ],
        columns=ALZHEIMER_FEATURES,
    )


    if feature_values.isnull().any().any():

        raise RuntimeError(
            "Required MRI features "
            "contain missing values."
        )


    return feature_values


# ============================================================
# ALZHEIMER PREDICTION
# ============================================================

def predict_alzheimer(
    subject_id: str,
) -> dict:

    """
    Run the trained Alzheimer classifier
    using the exact 141 MRI features.
    """

    feature_values = get_model_features(
        subject_id
    )


    prediction = int(
        ALZHEIMER_MODEL.predict(
            feature_values
        )[0]
    )


    probabilities = (
        ALZHEIMER_MODEL.predict_proba(
            feature_values
        )[0]
    )


    classifier = (
        ALZHEIMER_MODEL
        .named_steps[
            "classifier"
        ]
    )


    classes = list(
        classifier.classes_
    )


    probability_non_ad = float(
        probabilities[
            classes.index(0)
        ]
    )


    probability_ad = float(
        probabilities[
            classes.index(1)
        ]
    )


    model_c = float(
        getattr(
            classifier,
            "C",
            0.01,
        )
    )


    return {

        "prediction":
            prediction,

        "classification":
            (
                "AD"
                if prediction == 1
                else "Non-AD"
            ),

        "probability_ad":
            probability_ad,

        "probability_non_ad":
            probability_non_ad,

        "model":
            "Logistic Regression",

        "model_C":
            model_c,

        "features_used":
            len(ALZHEIMER_FEATURES),
    }


# ============================================================
# MODEL EXPLANATION
# ============================================================

def get_alzheimer_explanation(
    subject_id: str,
) -> dict:

    """
    Calculate model feature contributions.

    The saved pipeline contains:

        StandardScaler
              ↓
        LogisticRegression

    For each standardized feature:

        contribution =
            standardized_value
            × logistic_coefficient

    Positive contribution:
        pushes the model toward AD.

    Negative contribution:
        pushes the model toward Non-AD.

    These are model associations, not
    causal medical explanations.
    """

    if ALZHEIMER_MODEL is None:

        raise RuntimeError(
            "Alzheimer ML model is not loaded."
        )


    feature_values = get_model_features(
        subject_id
    )


    try:

        scaler = (
            ALZHEIMER_MODEL
            .named_steps[
                "scaler"
            ]
        )

        classifier = (
            ALZHEIMER_MODEL
            .named_steps[
                "classifier"
            ]
        )

    except KeyError as exc:

        raise RuntimeError(
            "The saved Alzheimer model "
            "does not contain the expected "
            f"pipeline step: {exc}"
        )


    scaled_values = (
        scaler.transform(
            feature_values
        )
    )


    coefficients = (
        classifier.coef_[0]
    )


    contributions = (
        scaled_values[0]
        * coefficients
    )


    explanation = []


    for feature, contribution in zip(
        ALZHEIMER_FEATURES,
        contributions,
    ):

        contribution_value = float(
            contribution
        )


        explanation.append({

            "feature":
                feature,

            "contribution":
                contribution_value,

            "direction":
                (
                    "AD"
                    if contribution_value > 0
                    else "Non-AD"
                ),
        })


    explanation.sort(
        key=lambda item:
            abs(
                item["contribution"]
            ),
        reverse=True,
    )


    return {
        "features":
            explanation[:10]
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {

        "status":
            "ok",

        "service":
            "NeuroTrace API",

        "version":
            settings.VERSION,
    }


# ============================================================
# PROJECT STATUS
# ============================================================

@app.get("/api/status")
def project_status():

    raw_subjects = (
        get_raw_subjects()
    )


    segmented_subjects = [

        subject_id

        for subject_id
        in raw_subjects

        if get_segmentation_path(
            subject_id
        )

    ]


    return {

        "project":
            settings.PROJECT_NAME,

        "raw_mri_available":
            RAW_MRI_DIR.exists(),

        "total_mri_subjects":
            len(raw_subjects),

        "segmented_subjects":
            len(segmented_subjects),

        "segmentation_running":
            (
                len(segmented_subjects)
                < len(raw_subjects)
            ),

        "clinical_data_available":
            CLINICAL_FILE.exists(),

        "ml_dataset_available":
            ML_DATASET_FILE.exists(),

        "model_available":
            (
                ALZHEIMER_MODEL is not None
                and
                ALZHEIMER_MODEL_PATH.exists()
            ),
    }


# ============================================================
# SEGMENTATION STATUS
# ============================================================

@app.get(
    "/api/segmentation/status"
)
def segmentation_status():

    subjects = (
        get_raw_subjects()
    )


    results = [

        get_subject_status(
            subject_id
        )

        for subject_id
        in subjects

    ]


    completed = sum(

        item[
            "segmentation_available"
        ]

        for item in results

    )


    return {

        "total":
            len(results),

        "completed":
            completed,

        "remaining":
            len(results) - completed,

        "subjects":
            results,
    }


# ============================================================
# SUBJECTS
# ============================================================

@app.get("/api/subjects")
def get_subjects():

    subjects = (
        get_raw_subjects()
    )


    result = []


    for subject_id in subjects:

        status = (
            get_subject_status(
                subject_id
            )
        )


        result.append({

            "subject_id":
                subject_id,

            "mri_available":
                status[
                    "mri_available"
                ],

            "segmentation_available":
                status[
                    "segmentation_available"
                ],
        })


    return {

        "count":
            len(result),

        "subjects":
            result,
    }


# ============================================================
# SUBJECT DETAILS
# ============================================================

@app.get(
    "/api/subjects/{subject_id}"
)
def get_subject(
    subject_id: str,
):

    subject_id = (
        subject_id.strip()
    )


    subject_status = (
        get_subject_status(
            subject_id
        )
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


    clinical_data = (
        get_clinical_data(
            subject_id
        )
    )


    imaging_features = (
        get_brain_features(
            subject_id
        )
    )


    return {

        **subject_status,

        "clinical_data":
            clinical_data,

        "imaging_features":
            imaging_features,
    }


# ============================================================
# QUANTITATIVE MEASUREMENTS
# ============================================================

@app.get(
    "/api/subjects/{subject_id}/measurements"
)
def get_subject_measurements(
    subject_id: str,
):

    subject_id = (
        subject_id.strip()
    )


    segmentation_path = (
        get_segmentation_path(
            subject_id
        )
    )


    if segmentation_path is None:

        raise HTTPException(

            status_code=404,

            detail=(
                "Segmentation not found "
                f"for subject: {subject_id}"
            ),
        )


    try:

        measurements = (
            measure_subject(
                segmentation_path
            )
        )


        return {

            "subject_id":
                subject_id,

            "status":
                "success",

            "measurements":
                measurements,
        }


    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=(
                "Measurement failed "
                f"for {subject_id}: {exc}"
            ),
        )


# ============================================================
# SEGMENTATION FILE
# ============================================================

@app.get(
    "/api/subjects/{subject_id}/segmentation"
)
def get_segmentation(
    subject_id: str,
):

    subject_id = (
        subject_id.strip()
    )


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

        "subject_id":
            subject_id,

        "available":
            True,

        "path":
            str(segmentation_path),

        "filename":
            segmentation_path.name,

        "size_bytes":
            segmentation_path.stat().st_size,
    }


# ============================================================
# MODEL EXPLANATION ENDPOINT
# ============================================================

@app.get(
    "/api/subjects/{subject_id}/explanation"
)
def subject_explanation(
    subject_id: str,
):

    subject_id = (
        subject_id.strip()
    )


    status = (
        get_subject_status(
            subject_id
        )
    )


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


    if not status[
        "segmentation_available"
    ]:

        raise HTTPException(

            status_code=404,

            detail=(
                "UNesT segmentation is "
                "not available for this "
                "subject."
            ),
        )


    if ALZHEIMER_MODEL is None:

        raise HTTPException(

            status_code=503,

            detail=(
                "Alzheimer ML model "
                "is not loaded."
            ),
        )


    try:

        return (
            get_alzheimer_explanation(
                subject_id
            )
        )


    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=(
                "Model explanation failed "
                f"for {subject_id}: {exc}"
            ),
        )


# ============================================================
# PROGRESSION ENDPOINT
# ============================================================

CLINICAL_FEATURES_FOR_PROGRESSION = [
    "Age", "MMSE", "GDS", "FAST", "KATZ", "Barthel", "Lawton", "Camcog",
]
GENDER_MAP_BACKEND = {
    "mujer": 0, "hombre": 1, "female": 0, "male": 1, "f": 0, "m": 1,
}


@app.get("/api/subjects/{subject_id}/progression")
def subject_progression(subject_id: str):
    """Return 12M, 24M, and 36M cognitive-progression risk probabilities.

    Merges MRI brain features + clinical data (Age, MMSE, GDS, FAST, etc.)
    to match the feature set used during model training.
    The pipeline's median imputer handles any missing clinical values.
    """
    import math
    subject_id = subject_id.strip()

    if not PROGRESSION_MODELS:
        raise HTTPException(
            status_code=503,
            detail="Progression models are not loaded. Run src.ml.train_progression first.",
        )

    # --- MRI features ---
    brain_df = load_csv(BRAIN_FEATURES_FILE)
    if brain_df.empty:
        raise HTTPException(status_code=503, detail="brain_features.csv is not available.")

    row_brain = get_subject_row(brain_df, "Subject_ID", subject_id)
    if row_brain is None:
        raise HTTPException(
            status_code=404,
            detail="Subject '" + "{}" + "' not found in brain_features.csv.".format(subject_id),
        )

    mri_cols = [c for c in brain_df.columns if c != "Subject_ID"]
    input_data: dict = {col: row_brain[col] for col in mri_cols}

    # --- Clinical features (optional merge) ---
    clinical_df = load_csv(PROJECT_ROOT / "data" / "processed" / "clinical_labeled.csv")
    row_clinical = None
    if not clinical_df.empty:
        row_clinical = get_subject_row(clinical_df, "Subject_ID", subject_id)

    for feat in CLINICAL_FEATURES_FOR_PROGRESSION:
        if row_clinical is not None and feat in clinical_df.columns:
            input_data[feat] = row_clinical[feat]
        else:
            input_data[feat] = math.nan

    if row_clinical is not None and "Gender" in clinical_df.columns:
        gender_raw = str(row_clinical.get("Gender", "")).strip().lower()
        input_data["Gender"] = GENDER_MAP_BACKEND.get(gender_raw, 0)
    else:
        input_data["Gender"] = 0

    X = pd.DataFrame([input_data])

    # --- Predict for each horizon ---
    horizons_result = {}
    for months, model in sorted(PROGRESSION_MODELS.items()):
        try:
            proba  = model.predict_proba(X)[0]
            pred   = int(model.predict(X)[0])
            labels = list(model.classes_)
            pos_label = 1 if 1 in labels else labels[-1]
            pos_idx   = labels.index(pos_label) if pos_label in labels else -1
            horizons_result[str(months) + "M"] = {
                "progression_probability": round(float(proba[pos_idx]), 4),
                "progression_class":       int(pred),
                "risk_label":              "High" if pred == 1 else "Low",
            }
        except Exception as exc:
            horizons_result[str(months) + "M"] = {"error": str(exc)}

    return {
        "subject_id":            subject_id,
        "progression_available": True,
        "horizons":              horizons_result,
        "model_type":            "GradientBoosting",
        "features_used":         len(input_data),
        "clinical_merged":       row_clinical is not None,
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


    status = (
        get_subject_status(
            subject_id
        )
    )


    # --------------------------------------------------------
    # SUBJECT VALIDATION
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
    # SEGMENTATION
    # --------------------------------------------------------

    if not status[
        "segmentation_available"
    ]:

        return {

            "status":
                "processing",

            "subject_id":
                subject_id,

            "segmentation_available":
                False,

            "prediction_available":
                False,

            "message":
                (
                    "MRI exists, but "
                    "UNesT segmentation "
                    "has not completed yet."
                ),
        }


    # --------------------------------------------------------
    # MODEL AVAILABILITY
    # --------------------------------------------------------

    if ALZHEIMER_MODEL is None:

        return {

            "status":
                "ready",

            "subject_id":
                subject_id,

            "segmentation_available":
                True,

            "prediction_available":
                False,

            "message":
                (
                    "UNesT segmentation "
                    "completed, but the "
                    "Alzheimer ML model "
                    "is not available."
                ),
        }


    # --------------------------------------------------------
    # PREDICTION
    # --------------------------------------------------------

    try:

        prediction = (
            predict_alzheimer(
                subject_id
            )
        )


    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=(
                "Alzheimer prediction "
                f"failed for {subject_id}: "
                f"{exc}"
            ),
        )


    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    return {

        "status":
            "ready",

        "subject_id":
            subject_id,

        "segmentation_available":
            True,

        "prediction_available":
            True,

        "prediction":
            prediction,

        "message":
            (
                "UNesT segmentation and "
                "Alzheimer ML analysis "
                "completed."
            ),
    }
