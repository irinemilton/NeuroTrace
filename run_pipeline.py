#!/usr/bin/env python3
"""
NeuroTrace - Main Pipeline Orchestrator

This script runs the complete neuroimaging analysis pipeline:
1. Clinical data preprocessing
2. MRI preprocessing
3. Brain segmentation (UNesT)
4. Feature extraction
5. Classification training
6. SHAP explainability
"""
import os
import sys
import argparse
import subprocess
from pathlib import Path


def run_cmd(cmd: list, description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"CMD: {' '.join(cmd)}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"ERROR: {description} failed with return code {result.returncode}")
        return False
    print(f"SUCCESS: {description}")
    return True


def main():
    parser = argparse.ArgumentParser(description="NeuroTrace Pipeline")
    parser.add_argument("--skip-clinical", action="store_true", help="Skip clinical preprocessing")
    parser.add_argument("--skip-mri", action="store_true", help="Skip MRI preprocessing")
    parser.add_argument("--skip-seg", action="store_true", help="Skip segmentation")
    parser.add_argument("--skip-features", action="store_true", help="Skip feature extraction")
    parser.add_argument("--skip-train", action="store_true", help="Skip model training")
    parser.add_argument("--skip-shap", action="store_true", help="Skip SHAP analysis")
    parser.add_argument("--mri-input-dir", default="data/raw/MRI", help="Directory with raw MRI files")
    parser.add_argument("--mri-output-dir", default="data/processed/preprocessed_mri", help="Output for preprocessed MRI")
    parser.add_argument("--seg-output-dir", default="data/processed/segmentations", help="Output for segmentations")
    parser.add_argument("--features-output", default="data/processed/features.csv", help="Output feature matrix")
    parser.add_argument("--model-output-dir", default="models/classification", help="Output for trained models")
    parser.add_argument("--shap-output-dir", default="results/explainability", help="Output for SHAP results")
    parser.add_argument("--clinical-input", default="data/raw/Clinical_data/clinical_data_corrected.csv")
    parser.add_argument("--clinical-output", default="data/processed/clinical_cleaned.csv")
    args = parser.parse_args()

    print("NeuroTrace Pipeline Starting...")
    print(f"Working directory: {os.getcwd()}")

    # Step 1: Clinical data preprocessing
    if not args.skip_clinical:
        success = run_cmd([
            sys.executable, "-m", "src.preprocessing.prepare_clinical_data"
        ], "Clinical Data Preprocessing")
        if not success:
            return 1

    # Step 2: MRI preprocessing
    if not args.skip_mri:
        mri_files = list(Path(args.mri_input_dir).glob("*.nii*")) + list(Path(args.mri_input_dir).glob("*.nii.gz"))
        if not mri_files:
            print(f"WARNING: No MRI files found in {args.mri_input_dir}, skipping MRI preprocessing")
        else:
            os.makedirs(args.mri_output_dir, exist_ok=True)
            for mri_file in mri_files:
                output_file = Path(args.mri_output_dir) / f"{mri_file.stem}_preproc.nii.gz"
                success = run_cmd([
                    sys.executable, "-m", "src.preprocessing.mri",
                    str(mri_file), str(output_file)
                ], f"MRI Preprocessing: {mri_file.name}")
                if not success:
                    return 1

    # Step 3: Brain segmentation
    if not args.skip_seg:
        preproc_files = list(Path(args.mri_output_dir).glob("*_preproc.nii.gz"))
        if not preproc_files:
            print(f"WARNING: No preprocessed MRI files found in {args.mri_output_dir}, skipping segmentation")
        else:
            os.makedirs(args.seg_output_dir, exist_ok=True)
            for mri_file in preproc_files:
                success = run_cmd([
                    sys.executable, "-m", "src.segmentation.unest",
                    str(mri_file), args.seg_output_dir
                ], f"Segmentation: {mri_file.name}")
                if not success:
                    return 1

    # Step 4: Feature extraction
    if not args.skip_features:
        success = run_cmd([
            sys.executable, "-m", "src.features.brain_features",
            "--clinical", args.clinical_output,
            "--seg-dir", args.seg_output_dir,
            "--output", args.features_output,
        ], "Feature Extraction")
        if not success:
            return 1

    # Step 5: Model training
    if not args.skip_train:
        success = run_cmd([
            sys.executable, "-m", "src.classification.train",
            "--features", args.features_output,
            "--output-dir", args.model_output_dir,
        ], "Model Training")
        if not success:
            return 1

    # Step 6: SHAP explainability
    if not args.skip_shap:
        model_path = Path(args.model_output_dir) / "best_model.joblib"
        if model_path.exists():
            success = run_cmd([
                sys.executable, "-m", "src.explainability.shap_analysis",
                "--model", str(model_path),
                "--features", args.features_output,
                "--output-dir", args.shap_output_dir,
            ], "SHAP Explainability Analysis")
            if not success:
                return 1
        else:
            print(f"WARNING: Model not found at {model_path}, skipping SHAP analysis")

    print("\n" + "="*60)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("="*60)
    print(f"Clinical data: {args.clinical_output}")
    print(f"Preprocessed MRI: {args.mri_output_dir}")
    print(f"Segmentations: {args.seg_output_dir}")
    print(f"Features: {args.features_output}")
    print(f"Models: {args.model_output_dir}")
    print(f"SHAP results: {args.shap_output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())