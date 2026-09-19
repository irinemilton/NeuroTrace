from pathlib import Path
import shutil
import subprocess
import sys


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MRI_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "mri"
    / "T1_original"
)

BUNDLE_DIR = (
    PROJECT_ROOT
    / "models"
    / "wholeBrainSeg_Large_UNEST_segmentation"
)

DATASET_DIR = BUNDLE_DIR / "dataset" / "images"

EVAL_DIR = BUNDLE_DIR / "eval"

META_FILE = BUNDLE_DIR / "configs" / "metadata.json"

CONFIG_FILE = BUNDLE_DIR / "configs" / "inference.json"


# ============================================================
# SETTINGS
# ============================================================

# Set to True if you want to delete temporary dataset images
# after each subject is processed.
CLEANUP_DATASET = True


# ============================================================
# CHECK PATHS
# ============================================================

def check_paths():

    print("Checking NeuroTrace paths...")

    if not MRI_DIR.exists():
        raise FileNotFoundError(
            f"MRI directory not found:\n{MRI_DIR}"
        )

    if not BUNDLE_DIR.exists():
        raise FileNotFoundError(
            f"MONAI bundle not found:\n{BUNDLE_DIR}"
        )

    if not META_FILE.exists():
        raise FileNotFoundError(
            f"metadata.json not found:\n{META_FILE}"
        )

    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"inference.json not found:\n{CONFIG_FILE}"
        )

    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    print("All paths OK.\n")


# ============================================================
# CHECK WHETHER SUBJECT IS ALREADY PROCESSED
# ============================================================

def is_completed(subject_name):

    output_file = (
        EVAL_DIR
        / subject_name
        / f"{subject_name}_trans.nii.gz"
    )

    return output_file.exists()


# ============================================================
# COPY MRI INTO MONAI DATASET DIRECTORY
# ============================================================

def prepare_subject(mri_file):

    destination = DATASET_DIR / mri_file.name

    # Remove old temporary file if present
    if destination.exists():
        destination.unlink()

    shutil.copy2(mri_file, destination)

    return destination


# ============================================================
# RUN MONAI UNEST
# ============================================================

def run_segmentation():

    command = [
        sys.executable,
        "-m",
        "monai.bundle",
        "run",
        "--meta_file",
        "configs\\metadata.json",
        "--config_file",
        "configs\\inference.json",
        "--run_id",
        "evaluating",
    ]

    print("\nRunning UNesT...")
    print(" ".join(command))

    # --------------------------------------------------------
    # MONAI bundle requires the bundle's scripts directory
    # on PYTHONPATH so that "networks" can be imported.
    # --------------------------------------------------------

    env = dict()

    # Copy current environment
    import os
    env.update(os.environ)

    scripts_dir = str(BUNDLE_DIR / "scripts")

    existing_pythonpath = env.get("PYTHONPATH", "")

    if existing_pythonpath:
        env["PYTHONPATH"] = (
            scripts_dir
            + os.pathsep
            + existing_pythonpath
        )
    else:
        env["PYTHONPATH"] = scripts_dir

    print(f"PYTHONPATH: {env['PYTHONPATH']}")

    result = subprocess.run(
        command,
        cwd=BUNDLE_DIR,
        env=env,
    )

    return result.returncode
# ============================================================
# CLEAN TEMPORARY INPUT
# ============================================================

def cleanup_subject(mri_file):

    temporary_file = DATASET_DIR / mri_file.name

    if CLEANUP_DATASET and temporary_file.exists():
        temporary_file.unlink()


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("NeuroTrace - Batch UNesT Brain Segmentation")
    print("=" * 60)

    check_paths()

    # --------------------------------------------------------
    # Find MRI files
    # --------------------------------------------------------

    mri_files = sorted(
        MRI_DIR.glob("*.nii.gz")
    )

    print(f"Found {len(mri_files)} MRI files.")

    if not mri_files:
        print("\nERROR: No .nii.gz MRI files found.")
        return

    # --------------------------------------------------------
    # Process subjects sequentially
    # --------------------------------------------------------

    completed = 0
    skipped = 0
    failed = 0

    for index, mri_file in enumerate(mri_files, start=1):

        subject_name = mri_file.name.replace(
            ".nii.gz",
            ""
        )

        print("\n")
        print("=" * 60)
        print(
            f"[{index}/{len(mri_files)}] "
            f"Subject: {subject_name}"
        )
        print("=" * 60)

        # ----------------------------------------------------
        # Skip completed subjects
        # ----------------------------------------------------

        if is_completed(subject_name):

            print("STATUS: Already completed - SKIPPING")

            skipped += 1
            completed += 1

            continue

        # ----------------------------------------------------
        # Prepare MRI
        # ----------------------------------------------------

        print("Copying MRI into MONAI dataset...")

        try:

            prepare_subject(mri_file)

        except Exception as e:

            print(f"ERROR copying MRI: {e}")

            failed += 1
            continue

        # ----------------------------------------------------
        # Run UNesT
        # ----------------------------------------------------

        return_code = run_segmentation()

        # ----------------------------------------------------
        # Check result
        # ----------------------------------------------------

        output_file = (
            EVAL_DIR
            / subject_name
            / f"{subject_name}_trans.nii.gz"
        )

        if return_code == 0 and output_file.exists():

            print("\nSTATUS: SUCCESS")
            print(f"Output: {output_file}")

            completed += 1

        else:

            print("\nSTATUS: FAILED")

            if return_code != 0:
                print(
                    f"MONAI returned exit code: {return_code}"
                )

            if not output_file.exists():
                print(
                    "Expected segmentation file was not found:"
                )
                print(output_file)

            failed += 1

        # ----------------------------------------------------
        # Remove temporary input
        # ----------------------------------------------------

        cleanup_subject(mri_file)

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print("\n")
    print("=" * 60)
    print("BATCH SEGMENTATION COMPLETE")
    print("=" * 60)

    print(f"Total MRI files : {len(mri_files)}")
    print(f"Completed       : {completed}")
    print(f"Skipped         : {skipped}")
    print(f"Failed          : {failed}")

    print("\nSegmentation directory:")
    print(EVAL_DIR)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()