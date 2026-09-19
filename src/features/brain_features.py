import os
import json
import numpy as np
import pandas as pd
import nibabel as nib
from typing import Dict, List, Optional
from src.segmentation.unest import load_segmentation, get_region_volumes


LABEL_MAPPING = {
    0: "background",
    1: "3rd-Ventricle",
    2: "4th-Ventricle",
    3: "Right-Accumbens-Area",
    4: "Left-Accumbens-Area",
    5: "Right-Amygdala",
    6: "Left-Amygdala",
    7: "Brain-Stem",
    8: "Right-Caudate",
    9: "Left-Caudate",
    10: "Right-Cerebellum-Exterior",
    11: "Left-Cerebellum-Exterior",
    12: "Right-Cerebellum-White-Matter",
    13: "Left-Cerebellum-White-Matter",
    14: "Right-Cerebral-White-Matter",
    15: "Left-Cerebral-White-Matter",
    16: "Right-Hippocampus",
    17: "Left-Hippocampus",
    18: "Right-Inf-Lat-Vent",
    19: "Left-Inf-Lat-Vent",
    20: "Right-Lateral-Ventricle",
    21: "Left-Lateral-Ventricle",
    22: "Right-Pallidum",
    23: "Left-Pallidum",
    24: "Right-Putamen",
    25: "Left-Putamen",
    26: "Right-Thalamus-Proper",
    27: "Left-Thalamus-Proper",
    28: "Right-Ventral-DC",
    29: "Left-Ventral-DC",
    30: "Cerebellar-Vermal-Lobules-I-V",
    31: "Cerebellar-Vermal-Lobules-VI-VII",
    32: "Cerebellar-Vermal-Lobules-VIII-X",
    33: "Left-Basal-Forebrain",
    34: "Right-Basal-Forebrain",
    35: "Right-ACgG--anterior-cingulate-gyrus",
    36: "Left-ACgG--anterior-cingulate-gyrus",
    37: "Right-AIns--anterior-insula",
    38: "Left-AIns--anterior-insula",
    39: "Right-AOrG--anterior-orbital-gyrus",
    40: "Left-AOrG--anterior-orbital-gyrus",
    41: "Right-AnG---angular-gyrus",
    42: "Left-AnG---angular-gyrus",
    43: "Right-Calc--calcarine-cortex",
    44: "Left-Calc--calcarine-cortex",
    45: "Right-CO----central-operculum",
    46: "Left-CO----central-operculum",
    47: "Right-Cun---cuneus",
    48: "Left-Cun---cuneus",
    49: "Right-Ent---entorhinal-area",
    50: "Left-Ent---entorhinal-area",
    51: "Right-FO----frontal-operculum",
    52: "Left-FO----frontal-operculum",
    53: "Right-FRP---frontal-pole",
    54: "Left-FRP---frontal-pole",
    55: "Right-FuG---fusiform-gyrus",
    56: "Left-FuG---fusiform-gyrus",
    57: "Right-GRe---gyrus-rectus",
    58: "Left-GRe---gyrus-rectus",
    59: "Right-IOG---inferior-occipital-gyrus",
    60: "Left-IOG---inferior-occipital-gyrus",
    61: "Right-ITG---inferior-temporal-gyrus",
    62: "Left-ITG---inferior-temporal-gyrus",
    63: "Right-LiG---lingual-gyrus",
    64: "Left-LiG---lingual-gyrus",
    65: "Right-LOrG--lateral-orbital-gyrus",
    66: "Left-LOrG--lateral-orbital-gyrus",
    67: "Right-MCgG--middle-cingulate-gyrus",
    68: "Left-MCgG--middle-cingulate-gyrus",
    69: "Right-MFC---medial-frontal-cortex",
    70: "Left-MFC---medial-frontal-cortex",
    71: "Right-MFG---middle-frontal-gyrus",
    72: "Left-MFG---middle-frontal-gyrus",
    73: "Right-MOG---middle-occipital-gyrus",
    74: "Left-MOG---middle-occipital-gyrus",
    75: "Right-MOrG--medial-orbital-gyrus",
    76: "Left-MOrG--medial-orbital-gyrus",
    77: "Right-MPoG--postcentral-gyrus",
    78: "Left-MPoG--postcentral-gyrus",
    79: "Right-MPrG--precentral-gyrus",
    80: "Left-MPrG--precentral-gyrus",
    81: "Right-MSFG--superior-frontal-gyrus",
    82: "Left-MSFG--superior-frontal-gyrus",
    83: "Right-MTG---middle-temporal-gyrus",
    84: "Left-MTG---middle-temporal-gyrus",
    85: "Right-OCP---occipital-pole",
    86: "Left-OCP---occipital-pole",
    87: "Right-OFuG--occipital-fusiform-gyrus",
    88: "Left-OFuG--occipital-fusiform-gyrus",
    89: "Right-OpIFG-opercular-part-of-the-IFG",
    90: "Left-OpIFG-opercular-part-of-the-IFG",
    91: "Right-OrIFG-orbital-part-of-the-IFG",
    92: "Left-OrIFG-orbital-part-of-the-IFG",
    93: "Right-PCgG--posterior-cingulate-gyrus",
    94: "Left-PCgG--posterior-cingulate-gyrus",
    95: "Right-PCu---precuneus",
    96: "Left-PCu---precuneus",
    97: "Right-PHG---parahippocampal-gyrus",
    98: "Left-PHG---parahippocampal-gyrus",
    99: "Right-PIns--posterior-insula",
    100: "Left-PIns--posterior-insula",
    101: "Right-PO----parietal-operculum",
    102: "Left-PO----parietal-operculum",
    103: "Right-PoG---postcentral-gyrus",
    104: "Left-PoG---postcentral-gyrus",
    105: "Right-POrG--posterior-orbital-gyrus",
    106: "Left-POrG--posterior-orbital-gyrus",
    107: "Right-PP----planum-polare",
    108: "Left-PP----planum-polare",
    109: "Right-PrG---precentral-gyrus",
    110: "Left-PrG---precentral-gyrus",
    111: "Right-PT----planum-temporale",
    112: "Left-PT----planum-temporale",
    113: "Right-SCA---subcallosal-area",
    114: "Left-SCA---subcallosal-area",
    115: "Right-SFG---superior-frontal-gyrus",
    116: "Left-SFG---superior-frontal-gyrus",
    117: "Right-SMC---supplementary-motor-cortex",
    118: "Left-SMC---supplementary-motor-cortex",
    119: "Right-SMG---supramarginal-gyrus",
    120: "Left-SMG---supramarginal-gyrus",
    121: "Right-SOG---superior-occipital-gyrus",
    122: "Left-SOG---superior-occipital-gyrus",
    123: "Right-SPL---superior-parietal-lobule",
    124: "Left-SPL---superior-parietal-lobule",
    125: "Right-STG---superior-temporal-gyrus",
    126: "Left-STG---superior-temporal-gyrus",
    127: "Right-TMP---temporal-pole",
    128: "Left-TMP---temporal-pole",
    129: "Right-TrIFG-triangular-part-of-the-IFG",
    130: "Left-TrIFG-triangular-part-of-the-IFG",
    131: "Right-TTG---transverse-temporal-gyrus",
    132: "Left-TTG---transverse-temporal-gyrus",
}


KEY_REGIONS = {
    "hippocampus": [16, 17],
    "amygdala": [5, 6],
    "ventricles": [1, 2, 18, 19, 20, 21],
    "thalamus": [26, 27],
    "caudate": [8, 9],
    "putamen": [24, 25],
    "pallidum": [22, 23],
    "accumbens": [3, 4],
    "brainstem": [7],
    "cerebellum": [10, 11, 12, 13, 30, 31, 32],
    "cerebral_white_matter": [14, 15],
    "entorhinal": [49, 50],
    "parahippocampal": [97, 98],
    "cingulate": [35, 36, 67, 68, 93, 94],
    "precuneus": [95, 96],
    "frontal_pole": [53, 54],
    "temporal_pole": [127, 128],
}


def extract_volumetric_features(
    seg_path: str,
    voxel_volume_mm3: float,
    include_all_regions: bool = False,
) -> Dict[str, float]:
    """Extract volumetric features from segmentation mask.

    Args:
        seg_path: Path to segmentation NIfTI file
        voxel_volume_mm3: Volume of a single voxel in mm^3
        include_all_regions: If True, include all 133 regions; else only key regions

    Returns:
        Dictionary mapping feature names to volumes (mm^3)
    """
    seg_array = load_segmentation(seg_path)
    volumes = get_region_volumes(seg_array, voxel_volume_mm3)

    features = {}

    if include_all_regions:
        for label_id, vol in volumes.items():
            name = LABEL_MAPPING.get(label_id, f"Region_{label_id}")
            features[f"vol_{name}"] = vol
    else:
        for region_name, label_ids in KEY_REGIONS.items():
            total_vol = sum(volumes.get(lid, 0.0) for lid in label_ids)
            features[f"vol_{region_name}"] = total_vol

        total_brain_vol = sum(volumes.values())
        features["vol_total_brain"] = total_brain_vol

        for region_name, label_ids in KEY_REGIONS.items():
            region_vol = features[f"vol_{region_name}"]
            if total_brain_vol > 0:
                features[f"vol_{region_name}_ratio"] = region_vol / total_brain_vol
            else:
                features[f"vol_{region_name}_ratio"] = 0.0

    return features


def get_voxel_volume(img_path: str) -> float:
    """Calculate voxel volume in mm^3 from NIfTI header."""
    img = nib.load(img_path)
    zooms = img.header.get_zooms()[:3]
    return float(np.prod(zooms))


def extract_features_for_subject(
    subject_id: str,
    seg_dir: str,
    clinical_df: pd.DataFrame,
    include_all_regions: bool = False,
) -> Optional[Dict]:
    """Extract combined imaging + clinical features for a single subject.

    Args:
        subject_id: Subject identifier (e.g., "101")
        seg_dir: Directory containing segmentation outputs
        clinical_df: DataFrame with clinical data (must have Codigo column)
        include_all_regions: Whether to include all 133 regions

    Returns:
        Dictionary of features, or None if subject not found
    """
    seg_file = os.path.join(seg_dir, f"{subject_id}_seg.nii.gz")
    if not os.path.exists(seg_file):
        print(f"Segmentation not found for subject {subject_id}: {seg_file}")
        return None

    voxel_vol = get_voxel_volume(seg_file)
    img_features = extract_volumetric_features(seg_file, voxel_vol, include_all_regions)

    clinical_row = clinical_df[clinical_df["Codigo"] == int(subject_id)]
    if clinical_row.empty:
        print(f"Clinical data not found for subject {subject_id}")
        return None

    clinical_features = clinical_row.iloc[0].to_dict()
    clinical_features.pop("Dxo", None)
    clinical_features.pop("Dxo_label", None)

    combined = {"subject_id": subject_id}
    combined.update(clinical_features)
    combined.update(img_features)

    return combined


def build_feature_matrix(
    clinical_csv: str,
    seg_dir: str,
    output_csv: str,
    include_all_regions: bool = False,
) -> pd.DataFrame:
    """Build full feature matrix for all subjects with both clinical and imaging data.

    Args:
        clinical_csv: Path to cleaned clinical CSV
        seg_dir: Directory with segmentation outputs
        output_csv: Path to save feature matrix
        include_all_regions: Whether to include all 133 regions

    Returns:
        Feature matrix DataFrame
    """
    clinical_df = pd.read_csv(clinical_csv)

    subject_ids = clinical_df["Codigo"].astype(str).tolist()
    all_features = []

    for sid in subject_ids:
        feats = extract_features_for_subject(sid, seg_dir, clinical_df, include_all_regions)
        if feats:
            all_features.append(feats)

    if not all_features:
        raise ValueError("No subjects found with both clinical and imaging data")

    feature_df = pd.DataFrame(all_features)
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    feature_df.to_csv(output_csv, index=False)
    print(f"Feature matrix saved to {output_csv} with shape {feature_df.shape}")
    print(f"Columns: {list(feature_df.columns)}")

    return feature_df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract brain volumetric features")
    parser.add_argument("--clinical", default="data/processed/clinical_cleaned.csv")
    parser.add_argument("--seg-dir", default="data/processed/segmentations")
    parser.add_argument("--output", default="data/processed/features.csv")
    parser.add_argument("--all-regions", action="store_true")
    args = parser.parse_args()

    build_feature_matrix(args.clinical, args.seg_dir, args.output, args.all_regions)