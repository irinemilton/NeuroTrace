import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "NeuroTrace"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    MODELS_DIR: Path = BASE_DIR / "models"
    RESULTS_DIR: Path = BASE_DIR / "results"

    UPLOAD_DIR: Path = PROCESSED_DATA_DIR / "uploads"
    PREPROCESSED_MRI_DIR: Path = PROCESSED_DATA_DIR / "preprocessed_mri"
    SEGMENTATION_DIR: Path = PROCESSED_DATA_DIR / "segmentations"
    FEATURES_DIR: Path = PROCESSED_DATA_DIR / "features"
    CLASSIFICATION_MODELS_DIR: Path = MODELS_DIR / "classification"
    SHAP_RESULTS_DIR: Path = RESULTS_DIR / "explainability"

    CLINICAL_CLEANED_CSV: Path = PROCESSED_DATA_DIR / "clinical_cleaned.csv"
    FEATURES_CSV: Path = PROCESSED_DATA_DIR / "features.csv"
    BEST_MODEL_PATH: Path = CLASSIFICATION_MODELS_DIR / "best_model.joblib"
    FEATURE_NAMES_PATH: Path = CLASSIFICATION_MODELS_DIR / "feature_names.json"

    UNEST_MODEL_DIR: Path = MODELS_DIR / "wholeBrainSeg_Large_UNEST_segmentation"
    UNEST_CHECKPOINT: Path = UNEST_MODEL_DIR / "models" / "model.pt"

    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024
    ALLOWED_EXTENSIONS: set = {".nii", ".nii.gz", ".gz"}

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()

for path in [
    settings.UPLOAD_DIR,
    settings.PREPROCESSED_MRI_DIR,
    settings.SEGMENTATION_DIR,
    settings.FEATURES_DIR,
    settings.CLASSIFICATION_MODELS_DIR,
    settings.SHAP_RESULTS_DIR,
]:
    path.mkdir(parents=True, exist_ok=True)