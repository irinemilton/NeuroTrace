from pathlib import Path
from typing import Dict, Optional

import nibabel as nib
import numpy as np
from scipy import ndimage


# ============================================================
# REGION LABELS
# ============================================================

REGIONS = {
    "hippocampus": [16, 17],
    "amygdala": [18, 19],
    "thalamus": [26, 27],
    "caudate": [8, 9],
    "putamen": [24, 25],
    "pallidum": [22, 23],
    "lateral_ventricle": [20, 21],
}


# ============================================================
# LOAD NIFTI
# ============================================================

def load_segmentation(segmentation_path: Path):
    """Load a segmentation NIfTI and return image + data."""

    image = nib.load(str(segmentation_path))

    data = np.asarray(image.dataobj)

    # Segmentation labels are discrete integers.
    data = np.rint(data).astype(np.int32)

    return image, data


# ============================================================
# REGION MEASUREMENTS
# ============================================================

def measure_region(
    data: np.ndarray,
    affine: np.ndarray,
    spacing: np.ndarray,
    labels: list[int],
) -> Dict:
    """Calculate quantitative measurements for a region."""

    mask = np.isin(data, labels)

    voxel_count = int(np.count_nonzero(mask))

    voxel_volume = float(np.prod(spacing))

    volume_mm3 = float(voxel_count * voxel_volume)

    if voxel_count == 0:
        return {
            "voxel_count": 0,
            "voxel_spacing_mm": spacing.tolist(),
            "voxel_volume_mm3": voxel_volume,
            "volume_mm3": 0.0,
            "dimensions_mm": [0.0, 0.0, 0.0],
            "centroid_voxel": None,
            "centroid_mm": None,
            "bounding_box_voxels": None,
            "connected_components": 0,
        }

    # --------------------------------------------------------
    # Bounding box
    # --------------------------------------------------------

    coordinates = np.argwhere(mask)

    minimum = coordinates.min(axis=0)
    maximum = coordinates.max(axis=0)

    bbox_voxels = maximum - minimum + 1

    dimensions_mm = bbox_voxels * spacing

    # --------------------------------------------------------
    # Centroid in voxel coordinates
    # --------------------------------------------------------

    centroid_voxel = coordinates.mean(axis=0)

    # --------------------------------------------------------
    # Convert centroid to physical/world coordinates
    # --------------------------------------------------------

    centroid_h = np.append(centroid_voxel, 1.0)

    centroid_world = affine @ centroid_h

    # --------------------------------------------------------
    # Connected components
    # --------------------------------------------------------

    structure = ndimage.generate_binary_structure(
        rank=3,
        connectivity=1,
    )

    _, component_count = ndimage.label(
        mask,
        structure=structure,
    )

    return {
        "voxel_count": voxel_count,
        "voxel_spacing_mm": [
            float(x) for x in spacing
        ],
        "voxel_volume_mm3": voxel_volume,
        "volume_mm3": volume_mm3,
        "dimensions_mm": [
            float(x) for x in dimensions_mm
        ],
        "centroid_voxel": [
            float(x) for x in centroid_voxel
        ],
        "centroid_mm": [
            float(x) for x in centroid_world[:3]
        ],
        "bounding_box_voxels": [
            int(x) for x in bbox_voxels
        ],
        "connected_components": int(component_count),
    }


# ============================================================
# BILATERAL MEASUREMENTS
# ============================================================

def measure_bilateral_region(
    data: np.ndarray,
    affine: np.ndarray,
    spacing: np.ndarray,
    left_label: int,
    right_label: int,
) -> Dict:
    """Measure left and right sides separately."""

    left = measure_region(
        data,
        affine,
        spacing,
        [left_label],
    )

    right = measure_region(
        data,
        affine,
        spacing,
        [right_label],
    )

    left_volume = left["volume_mm3"]
    right_volume = right["volume_mm3"]

    total_volume = left_volume + right_volume

    if total_volume > 0:
        asymmetry_percent = (
            abs(left_volume - right_volume)
            / ((left_volume + right_volume) / 2)
        ) * 100.0
    else:
        asymmetry_percent = 0.0

    return {
        "left": left,
        "right": right,
        "total_volume_mm3": float(total_volume),
        "asymmetry_percent": float(asymmetry_percent),
    }


# ============================================================
# SUBJECT MEASUREMENTS
# ============================================================

def measure_subject(
    segmentation_path: Path,
) -> Dict:
    """Calculate all quantitative measurements for one subject."""

    image, data = load_segmentation(segmentation_path)

    spacing = np.asarray(
        image.header.get_zooms()[:3],
        dtype=np.float64,
    )

    affine = np.asarray(
        image.affine,
        dtype=np.float64,
    )

    voxel_volume_mm3 = float(np.prod(spacing))
    brain_mask = data > 0
    brain_voxel_count = int(np.count_nonzero(brain_mask))
    total_brain_volume_mm3 = float(
        brain_voxel_count * voxel_volume_mm3
    )

    midpoint = data.shape[0] / 2.0
    left_mask = brain_mask.copy()
    right_mask = brain_mask.copy()
    left_mask[: int(np.ceil(midpoint)), ...] = False
    right_mask[int(np.floor(midpoint)) :, ...] = False

    left_hemisphere_volume_mm3 = float(
        np.count_nonzero(left_mask) * voxel_volume_mm3
    )
    right_hemisphere_volume_mm3 = float(
        np.count_nonzero(right_mask) * voxel_volume_mm3
    )

    measurements = {
        "segmentation_file": str(segmentation_path),
        "image_shape": [
            int(x) for x in data.shape[:3]
        ],
        "voxel_spacing_mm": [
            float(x) for x in spacing
        ],
        "voxel_volume_mm3": voxel_volume_mm3,
        "total_brain_volume_mm3": total_brain_volume_mm3,
        "hemisphere_volumes_mm3": {
            "left": left_hemisphere_volume_mm3,
            "right": right_hemisphere_volume_mm3,
        },
        "regions": {},
    }

    for region_name, labels in REGIONS.items():

        right_label = labels[0]
        left_label = labels[1]

        region_measurement = measure_bilateral_region(
            data,
            affine,
            spacing,
            left_label,
            right_label,
        )
        region_measurement["brain_volume_percent"] = (
            float(
                region_measurement["total_volume_mm3"]
                / total_brain_volume_mm3
                * 100.0
            )
            if total_brain_volume_mm3 > 0
            else 0.0
        )
        measurements["regions"][region_name] = region_measurement

    return measurements


# ============================================================
# FIND SUBJECT SEGMENTATION
# ============================================================

def find_subject_segmentation(
    project_root: Path,
    subject_id: str,
) -> Optional[Path]:

    path = (
        project_root
        / "models"
        / "wholeBrainSeg_Large_UNEST_segmentation"
        / "eval"
        / subject_id
        / f"{subject_id}_trans.nii.gz"
    )

    if path.exists():
        return path

    return None


# ============================================================
# MAIN TEST
# ============================================================

if __name__ == "__main__":

    project_root = Path(__file__).resolve().parents[2]

    subject_id = "crl_104"

    segmentation = find_subject_segmentation(
        project_root,
        subject_id,
    )

    if segmentation is None:
        raise FileNotFoundError(
            f"Segmentation not found for {subject_id}"
        )

    result = measure_subject(segmentation)

    print("=" * 60)
    print("NEUROTRACE QUANTITATIVE MEASUREMENTS")
    print("=" * 60)

    print(f"Subject: {subject_id}")
    print(f"Segmentation: {segmentation}")

    print(
        "\nVoxel spacing:",
        result["voxel_spacing_mm"],
    )

    for region_name, region in result["regions"].items():

        print(f"\n{region_name.upper()}")
        print("-" * 40)

        print(
            "Left volume:",
            region["left"]["volume_mm3"],
            "mm3",
        )

        print(
            "Right volume:",
            region["right"]["volume_mm3"],
            "mm3",
        )

        print(
            "Total volume:",
            region["total_volume_mm3"],
            "mm3",
        )

        print(
            "Asymmetry:",
            round(
                region["asymmetry_percent"],
                2,
            ),
            "%",
        )

        print(
            "Left voxels:",
            region["left"]["voxel_count"],
        )

        print(
            "Right voxels:",
            region["right"]["voxel_count"],
        )

        print(
            "Connected components:",
            region["left"]["connected_components"],
            "/",
            region["right"]["connected_components"],
        )

    print("\n" + "=" * 60)
    print("MEASUREMENT TEST COMPLETE")
    print("=" * 60)