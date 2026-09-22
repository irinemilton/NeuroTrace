from pathlib import Path
import os, shutil, subprocess, sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUNDLE_DIR = PROJECT_ROOT / "models" / "wholeBrainSeg_Large_UNEST_segmentation"
DATASET_DIR = BUNDLE_DIR / "dataset" / "images"
EVAL_DIR = BUNDLE_DIR / "eval"
META_FILE = BUNDLE_DIR / "configs" / "metadata.json"
CONFIG_FILE = BUNDLE_DIR / "configs" / "inference.json"

def segment_single_mri(mri_path: Path, subject_id: str) -> Path:
    mri_path = Path(mri_path)
    for required in (BUNDLE_DIR, META_FILE, CONFIG_FILE):
        if not required.exists():
            raise FileNotFoundError(required)
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    if not mri_path.exists():
        raise FileNotFoundError(mri_path)
    if not (mri_path.name.endswith(".nii") or mri_path.name.endswith(".nii.gz")):
        raise ValueError("Only NIfTI files are supported.")
    output = EVAL_DIR / subject_id / f"{subject_id}_trans.nii.gz"
    if output.exists():
        return output
    temp_input = DATASET_DIR / f"{subject_id}.nii.gz"
    if temp_input.exists():
        temp_input.unlink()
    shutil.copy2(mri_path, temp_input)
    env = dict(os.environ)
    scripts = str(BUNDLE_DIR / "scripts")
    env["PYTHONPATH"] = scripts + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    command = [
        sys.executable, "-m", "monai.bundle", "run",
        "--meta_file", "configs\\metadata.json",
        "--config_file", "configs\\inference.json",
        "--run_id", "evaluating",
    ]
    try:
        result = subprocess.run(command, cwd=BUNDLE_DIR, env=env)
    finally:
        if temp_input.exists():
            try:
                temp_input.unlink()
            except Exception:
                pass
    if result.returncode != 0:
        raise RuntimeError(f"UNesT failed with exit code {result.returncode}")
    if not output.exists():
        raise RuntimeError(f"Expected segmentation not found: {output}")
    return output
