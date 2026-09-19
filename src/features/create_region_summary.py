from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

EVAL_DIR = (
    ROOT
    / "models"
    / "wholeBrainSeg_Large_UNEST_segmentation"
    / "eval"
)

OUTPUT_DIR = ROOT / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = OUTPUT_DIR / "brain_region_summary.csv"


# Important anatomical regions from the UNesT label map
REGIONS = {
    5: "Right_Amygdala",
    6: "Left_Amygdala",

    8: "Right_Caudate",
    9: "Left_Caudate",

    16: "Right_Hippocampus",
    17: "Left_Hippocampus",

    20: "Right_Lateral_Ventricle",
    21: "Left_Lateral_Ventricle",

    22: "Right_Pallidum",
    23: "Left_Pallidum",

    24: "Right_Putamen",
    25: "Left_Putamen",

    26: "Right_Thalamus",
    27: "Left_Thalamus",

    18: "Right_Inferior_Lateral_Ventricle",
    19: "Left_Inferior_Lateral_Ventricle",
}


rows = []


segmentation_files = list(
    EVAL_DIR.glob("*/*_trans.nii.gz")
)

print(f"Found {len(segmentation_files)} segmentations")


for seg_path in segmentation_files:

    subject_id = seg_path.name.replace(
        "_trans.nii.gz", ""
    )

    img = nib.load(seg_path)

    data = np.asarray(
        img.dataobj,
        dtype=np.int16
    )

    voxel_volume = abs(
        np.linalg.det(
            img.affine[:3, :3]
        )
    )

    row = {
        "Subject_ID": subject_id
    }

    for label, region_name in REGIONS.items():

        voxel_count = np.sum(data == label)

        volume_mm3 = voxel_count * voxel_volume

        row[f"{region_name}_mm3"] = volume_mm3


    # Bilateral totals
    bilateral_pairs = [
        ("Amygdala", 5, 6),
        ("Caudate", 8, 9),
        ("Hippocampus", 16, 17),
        ("Lateral_Ventricle", 20, 21),
        ("Pallidum", 22, 23),
        ("Putamen", 24, 25),
        ("Thalamus", 26, 27),
        ("Inferior_Lateral_Ventricle", 18, 19),
    ]


    for name, right_label, left_label in bilateral_pairs:

        right_volume = (
            np.sum(data == right_label)
            * voxel_volume
        )

        left_volume = (
            np.sum(data == left_label)
            * voxel_volume
        )

        total = right_volume + left_volume

        asymmetry = (
            (right_volume - left_volume) / total
            if total > 0
            else 0
        )

        row[f"{name}_Total_mm3"] = total
        row[f"{name}_Asymmetry"] = asymmetry


    rows.append(row)


df = pd.DataFrame(rows)

df.to_csv(
    OUTPUT_PATH,
    index=False
)


print()
print("Created:")
print(OUTPUT_PATH)

print()
print(f"Subjects: {len(df)}")
print(f"Features: {len(df.columns) - 1}")

print()
print(df.head())