from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

EVAL_DIR = (
    PROJECT_ROOT
    / "models"
    / "wholeBrainSeg_Large_UNEST_segmentation"
    / "eval"
)

OUTPUT_CSV = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "brain_features.csv"
)


# ============================================================
# UNesT LABEL MAPPING
# ============================================================

LABEL_MAPPING = {
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
# VOXEL VOLUME
# ============================================================

def get_voxel_volume(seg_path: Path) -> float:
    """
    Return the physical volume of one voxel in mm³.
    """

    image = nib.load(str(seg_path))

    zooms = image.header.get_zooms()[:3]

    voxel_volume = float(
        np.prod(zooms)
    )

    return voxel_volume


# ============================================================
# LOAD SEGMENTATION
# ============================================================

def load_segmentation_array(seg_path: Path) -> np.ndarray:
    """
    Load the UNesT segmentation as a NumPy array.

    The segmentation is a discrete label map:
        0   = background
        1   = anatomical region 1
        2   = anatomical region 2
        ...
        132 = anatomical region 132
    """

    image = nib.load(str(seg_path))

    data = np.asarray(
        image.dataobj
    )

    # Convert safely to integer labels.
    data = np.rint(data).astype(
        np.int16
    )

    return data


# ============================================================
# CALCULATE REGIONAL VOLUMES
# ============================================================

def get_region_volumes(
    segmentation: np.ndarray,
    voxel_volume_mm3: float,
) -> dict:
    """
    Calculate volume for labels 1-132.

    Volume =
        number of voxels belonging to region
        × physical voxel volume
    """

    volumes = {}

    for label_id in range(1, 133):

        voxel_count = int(
            np.count_nonzero(
                segmentation == label_id
            )
        )

        volume_mm3 = (
            voxel_count
            * voxel_volume_mm3
        )

        volumes[label_id] = float(
            volume_mm3
        )

    return volumes


# ============================================================
# EXTRACT ONE SUBJECT
# ============================================================

def extract_subject(
    subject_id: str,
    seg_path: Path,
) -> dict:

    print(
        f"Extracting features: {subject_id}"
    )

    # --------------------------------------------------------
    # Load segmentation
    # --------------------------------------------------------

    segmentation = load_segmentation_array(
        seg_path
    )

    # --------------------------------------------------------
    # Calculate voxel volume
    # --------------------------------------------------------

    voxel_volume = get_voxel_volume(
        seg_path
    )

    # --------------------------------------------------------
    # Calculate all regional volumes
    # --------------------------------------------------------

    volumes = get_region_volumes(
        segmentation,
        voxel_volume,
    )

    # --------------------------------------------------------
    # Start feature dictionary
    # --------------------------------------------------------

    features = {
        "Subject_ID": subject_id
    }

    # ========================================================
    # 132 ANATOMICAL REGION FEATURES
    # ========================================================

    for label_id in range(1, 133):

        region_name = LABEL_MAPPING.get(
            label_id,
            f"Region_{label_id}",
        )

        features[
            f"{region_name}_volume_mm3"
        ] = volumes[label_id]

    # ========================================================
    # IMPORTANT STRUCTURES
    # ========================================================

    right_hippocampus = volumes[16]
    left_hippocampus = volumes[17]

    right_amygdala = volumes[5]
    left_amygdala = volumes[6]

    right_thalamus = volumes[26]
    left_thalamus = volumes[27]

    right_caudate = volumes[8]
    left_caudate = volumes[9]

    right_putamen = volumes[24]
    left_putamen = volumes[25]

    right_pallidum = volumes[22]
    left_pallidum = volumes[23]

    right_lateral_ventricle = volumes[20]
    left_lateral_ventricle = volumes[21]

    right_inf_lat_vent = volumes[18]
    left_inf_lat_vent = volumes[19]

    # ========================================================
    # DERIVED FEATURES
    # ========================================================

    features[
        "Hippocampus_total_volume_mm3"
    ] = (
        right_hippocampus
        + left_hippocampus
    )

    features[
        "Hippocampus_asymmetry_mm3"
    ] = abs(
        right_hippocampus
        - left_hippocampus
    )

    features[
        "Amygdala_total_volume_mm3"
    ] = (
        right_amygdala
        + left_amygdala
    )

    features[
        "Thalamus_total_volume_mm3"
    ] = (
        right_thalamus
        + left_thalamus
    )

    features[
        "Caudate_total_volume_mm3"
    ] = (
        right_caudate
        + left_caudate
    )

    features[
        "Putamen_total_volume_mm3"
    ] = (
        right_putamen
        + left_putamen
    )

    features[
        "Pallidum_total_volume_mm3"
    ] = (
        right_pallidum
        + left_pallidum
    )

    features[
        "Lateral_Ventricle_total_volume_mm3"
    ] = (
        right_lateral_ventricle
        + left_lateral_ventricle
    )

    features[
        "Inf_Lat_Vent_total_volume_mm3"
    ] = (
        right_inf_lat_vent
        + left_inf_lat_vent
    )

    return features


# ============================================================
# FIND COMPLETED SEGMENTATIONS
# ============================================================

def find_segmentations():

    if not EVAL_DIR.exists():

        print(
            f"Segmentation directory not found:"
        )

        print(EVAL_DIR)

        return []

    results = []

    for subject_dir in sorted(
        EVAL_DIR.iterdir()
    ):

        if not subject_dir.is_dir():
            continue

        subject_id = subject_dir.name

        seg_path = (
            subject_dir
            / f"{subject_id}_trans.nii.gz"
        )

        if seg_path.exists():

            results.append(
                (
                    subject_id,
                    seg_path,
                )
            )

    return results


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("NeuroTrace - Brain Feature Extraction")
    print("=" * 60)

    segmentations = find_segmentations()

    print(
        f"Completed segmentations found: "
        f"{len(segmentations)}"
    )

    if not segmentations:

        print(
            "No completed segmentations found."
        )

        return

    all_features = []

    # --------------------------------------------------------
    # Process each completed segmentation
    # --------------------------------------------------------

    for subject_id, seg_path in segmentations:

        try:

            features = extract_subject(
                subject_id,
                seg_path,
            )

            all_features.append(
                features
            )

        except Exception as exc:

            print(
                f"ERROR processing "
                f"{subject_id}: {exc}"
            )

    # --------------------------------------------------------
    # Stop if all subjects failed
    # --------------------------------------------------------

    if not all_features:

        print(
            "No features extracted."
        )

        return

    # --------------------------------------------------------
    # Create dataframe
    # --------------------------------------------------------

    df = pd.DataFrame(
        all_features
    )

    # --------------------------------------------------------
    # Keep Subject_ID first
    # --------------------------------------------------------

    columns = [
        "Subject_ID"
    ] + [
        column
        for column in df.columns
        if column != "Subject_ID"
    ]

    df = df[columns]

    # --------------------------------------------------------
    # Save CSV
    # --------------------------------------------------------

    OUTPUT_CSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        OUTPUT_CSV,
        index=False,
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print()

    print("=" * 60)
    print("FEATURE EXTRACTION COMPLETE")
    print("=" * 60)

    print(
        f"Subjects : {len(df)}"
    )

    print(
        f"Features : {len(df.columns)}"
    )

    print(
        f"Output   : {OUTPUT_CSV}"
    )

    print("=" * 60)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()