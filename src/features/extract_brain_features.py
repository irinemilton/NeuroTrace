from pathlib import Path
import nibabel as nib
import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SEGMENTATION_DIR = (
    PROJECT_ROOT
    / "models"
    / "wholeBrainSeg_Large_UNEST_segmentation"
    / "eval"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "brain_features.csv"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 133 UNesT LABELS
# ============================================================

LABELS = {
    1: "3rd_Ventricle",
    2: "4th_Ventricle",
    3: "Right_Accumbens",
    4: "Left_Accumbens",
    5: "Right_Amygdala",
    6: "Left_Amygdala",
    7: "Brain_Stem",
    8: "Right_Caudate",
    9: "Left_Caudate",
    10: "Right_Cerebellum_Exterior",
    11: "Left_Cerebellum_Exterior",
    12: "Right_Cerebellum_White_Matter",
    13: "Left_Cerebellum_White_Matter",
    14: "Right_Cerebral_White_Matter",
    15: "Left_Cerebral_White_Matter",
    16: "Right_Hippocampus",
    17: "Left_Hippocampus",
    18: "Right_Inf_Lat_Vent",
    19: "Left_Inf_Lat_Vent",
    20: "Right_Lateral_Ventricle",
    21: "Left_Lateral_Ventricle",
    22: "Right_Pallidum",
    23: "Left_Pallidum",
    24: "Right_Putamen",
    25: "Left_Putamen",
    26: "Right_Thalamus",
    27: "Left_Thalamus",
    28: "Right_Ventral_DC",
    29: "Left_Ventral_DC",
    30: "Cerebellar_Vermal_I_V",
    31: "Cerebellar_Vermal_VI_VII",
    32: "Cerebellar_Vermal_VIII_X",
    33: "Left_Basal_Forebrain",
    34: "Right_Basal_Forebrain",
    35: "Right_Anterior_Cingulate",
    36: "Left_Anterior_Cingulate",
    37: "Right_Anterior_Insula",
    38: "Left_Anterior_Insula",
    39: "Right_Anterior_Orbital",
    40: "Left_Anterior_Orbital",
    41: "Right_Angular_Gyrus",
    42: "Left_Angular_Gyrus",
    43: "Right_Calcarine",
    44: "Left_Calcarine",
    45: "Right_Central_Operculum",
    46: "Left_Central_Operculum",
    47: "Right_Cuneus",
    48: "Left_Cuneus",
    49: "Right_Entorhinal",
    50: "Left_Entorhinal",
    51: "Right_Frontal_Operculum",
    52: "Left_Frontal_Operculum",
    53: "Right_Frontal_Pole",
    54: "Left_Frontal_Pole",
    55: "Right_Fusiform",
    56: "Left_Fusiform",
    57: "Right_Gyrus_Rectus",
    58: "Left_Gyrus_Rectus",
    59: "Right_Inferior_Occipital",
    60: "Left_Inferior_Occipital",
    61: "Right_Inferior_Temporal",
    62: "Left_Inferior_Temporal",
    63: "Right_Lingual",
    64: "Left_Lingual",
    65: "Right_Lateral_Orbital",
    66: "Left_Lateral_Orbital",
    67: "Right_Middle_Cingulate",
    68: "Left_Middle_Cingulate",
    69: "Right_Medial_Frontal",
    70: "Left_Medial_Frontal",
    71: "Right_Middle_Frontal",
    72: "Left_Middle_Frontal",
    73: "Right_Middle_Occipital",
    74: "Left_Middle_Occipital",
    75: "Right_Medial_Orbital",
    76: "Left_Medial_Orbital",
    77: "Right_Postcentral",
    78: "Left_Postcentral",
    79: "Right_Precentral",
    80: "Left_Precentral",
    81: "Right_Superior_Frontal",
    82: "Left_Superior_Frontal",
    83: "Right_Middle_Temporal",
    84: "Left_Middle_Temporal",
    85: "Right_Occipital_Pole",
    86: "Left_Occipital_Pole",
    87: "Right_Occipital_Fusiform",
    88: "Left_Occipital_Fusiform",
    89: "Right_OpIFG",
    90: "Left_OpIFG",
    91: "Right_Orbital_IFG",
    92: "Left_Orbital_IFG",
    93: "Right_Posterior_Cingulate",
    94: "Left_Posterior_Cingulate",
    95: "Right_Precuneus",
    96: "Left_Precuneus",
    97: "Right_Parahippocampal",
    98: "Left_Parahippocampal",
    99: "Right_Posterior_Insula",
    100: "Left_Posterior_Insula",
    101: "Right_Parietal_Operculum",
    102: "Left_Parietal_Operculum",
    103: "Right_Postcentral_2",
    104: "Left_Postcentral_2",
    105: "Right_Posterior_Orbital",
    106: "Left_Posterior_Orbital",
    107: "Right_Planum_Polare",
    108: "Left_Planum_Polare",
    109: "Right_Precentral_2",
    110: "Left_Precentral_2",
    111: "Right_Planum_Temporale",
    112: "Left_Planum_Temporale",
    113: "Right_Subcallosal",
    114: "Left_Subcallosal",
    115: "Right_Superior_Frontal_2",
    116: "Left_Superior_Frontal_2",
    117: "Right_Supplementary_Motor",
    118: "Left_Supplementary_Motor",
    119: "Right_Supramarginal",
    120: "Left_Supramarginal",
    121: "Right_Superior_Occipital",
    122: "Left_Superior_Occipital",
    123: "Right_Superior_Parietal",
    124: "Left_Superior_Parietal",
    125: "Right_Superior_Temporal",
    126: "Left_Superior_Temporal",
    127: "Right_Temporal_Pole",
    128: "Left_Temporal_Pole",
    129: "Right_Triangular_IFG",
    130: "Left_Triangular_IFG",
    131: "Right_Transverse_Temporal",
    132: "Left_Transverse_Temporal",
}


# ============================================================
# FEATURE EXTRACTION
# ============================================================

def extract_features(segmentation_file):

    print(f"\nProcessing: {segmentation_file.name}")

    img = nib.load(str(segmentation_file))
    data = np.asarray(img.dataobj)

    voxel_sizes = img.header.get_zooms()[:3]
    voxel_volume = float(np.prod(voxel_sizes))

    print(f"Shape: {data.shape}")
    print(f"Voxel size: {voxel_sizes}")
    print(f"Voxel volume: {voxel_volume:.3f} mm³")

    features = {}

    # --------------------------------------------------------
    # Volume of every brain structure
    # --------------------------------------------------------

    for label_id, label_name in LABELS.items():

        voxel_count = np.sum(data == label_id)

        volume = voxel_count * voxel_volume

        features[f"{label_name}_volume_mm3"] = float(volume)

    # --------------------------------------------------------
    # Important combined structures
    # --------------------------------------------------------

    def total(left, right):
        return features[left] + features[right]

    def asymmetry(left, right):
        return features[right] - features[left]

    # Hippocampus
    features["Hippocampus_total_volume_mm3"] = total(
        "Left_Hippocampus_volume_mm3",
        "Right_Hippocampus_volume_mm3"
    )

    features["Hippocampus_asymmetry_mm3"] = asymmetry(
        "Left_Hippocampus_volume_mm3",
        "Right_Hippocampus_volume_mm3"
    )

    # Amygdala
    features["Amygdala_total_volume_mm3"] = total(
        "Left_Amygdala_volume_mm3",
        "Right_Amygdala_volume_mm3"
    )

    # Thalamus
    features["Thalamus_total_volume_mm3"] = total(
        "Left_Thalamus_volume_mm3",
        "Right_Thalamus_volume_mm3"
    )

    # Caudate
    features["Caudate_total_volume_mm3"] = total(
        "Left_Caudate_volume_mm3",
        "Right_Caudate_volume_mm3"
    )

    # Putamen
    features["Putamen_total_volume_mm3"] = total(
        "Left_Putamen_volume_mm3",
        "Right_Putamen_volume_mm3"
    )

    # Pallidum
    features["Pallidum_total_volume_mm3"] = total(
        "Left_Pallidum_volume_mm3",
        "Right_Pallidum_volume_mm3"
    )

    # Lateral ventricles
    features["Lateral_Ventricle_total_volume_mm3"] = total(
        "Left_Lateral_Ventricle_volume_mm3",
        "Right_Lateral_Ventricle_volume_mm3"
    )

    # Inferior lateral ventricles
    features["Inf_Lat_Vent_total_volume_mm3"] = total(
        "Left_Inf_Lat_Vent_volume_mm3",
        "Right_Inf_Lat_Vent_volume_mm3"
    )

    # --------------------------------------------------------
    # Subject ID
    # --------------------------------------------------------

    filename = segmentation_file.name

    subject_id = filename.replace("_trans.nii.gz", "")

    features["Subject_ID"] = subject_id

    return features


# ============================================================
# MAIN
# ============================================================

def main():

    print("===================================")
    print("NeuroTrace Brain Feature Extraction")
    print("===================================")

    print(f"\nSearching for segmentation outputs:")
    print(SEGMENTATION_DIR)

    segmentation_files = sorted(
        SEGMENTATION_DIR.glob("*/*_trans.nii.gz")
    )

    print(f"\nFound {len(segmentation_files)} segmentation file(s).")

    if not segmentation_files:
        print("\nERROR: No segmentation files found.")
        print("Expected files like:")
        print("eval/crl_104/crl_104_trans.nii.gz")
        return

    all_features = []

    for segmentation_file in segmentation_files:

        try:
            features = extract_features(segmentation_file)
            all_features.append(features)

        except Exception as e:

            print(f"\nERROR processing {segmentation_file.name}")
            print(e)

    if not all_features:
        print("\nNo features were extracted.")
        return

    df = pd.DataFrame(all_features)

    # Put Subject_ID first
    columns = ["Subject_ID"] + [
        c for c in df.columns if c != "Subject_ID"
    ]

    df = df[columns]

    df.to_csv(OUTPUT_FILE, index=False)

    print("\n===================================")
    print("FEATURE EXTRACTION COMPLETE")
    print("===================================")

    print(f"\nSubjects processed: {len(df)}")
    print(f"Features generated: {len(df.columns) - 1}")

    print(f"\nSaved to:")
    print(OUTPUT_FILE)

    print("\nFirst few rows:")
    print(df.iloc[:, :8].to_string(index=False))


if __name__ == "__main__":
    main()