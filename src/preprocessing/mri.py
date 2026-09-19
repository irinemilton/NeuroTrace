import os
import nibabel as nib
import numpy as np
from typing import Tuple

def load_nifti(image_path: str) -> nib.Nifti1Image:
    """Load a NIfTI image using NiBabel.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the loaded object is not a NIfTI image.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"MRI file not found: {image_path}")
    img = nib.load(image_path)
    if not isinstance(img, nib.Nifti1Image):
        raise ValueError(f"File is not a valid NIfTI image: {image_path}")
    return img

def validate_image(img: nib.Nifti1Image) -> Tuple[Tuple[int, ...], Tuple[float, ...]]:
    """Validate dimensions and voxel spacing.

    Returns:
        tuple of shape and voxel spacing (affine diagonal).
    """
    shape = img.shape
    if len(shape) != 3:
        raise ValueError(f"Expected a 3‑D volume, got shape {shape}")
    # Voxel spacing is derived from the affine matrix
    spacing = tuple(abs(img.header.get_zooms()))[:3]
    return shape, spacing

def intensity_normalization(data: np.ndarray) -> np.ndarray:
    """Zero‑mean, unit‑variance normalization of the image intensities.

    Clip extreme outliers to the 0.5th and 99.5th percentiles to improve stability.
    """
    # Clip extreme values
    lower, upper = np.percentile(data, [0.5, 99.5])
    data = np.clip(data, lower, upper)
    mean = data.mean()
    std = data.std()
    if std == 0:
        std = 1.0
    return (data - mean) / std

def preprocess_mri(input_path: str, output_path: str) -> None:
    """Full preprocessing pipeline for a T1‑weighted MRI.

    Steps:
        1. Load NIfTI.
        2. Validate dimensions / voxel spacing.
        3. Intensity normalization.
        4. Save a new NIfTI file (same header/affine) ready for segmentation.
    """
    img = load_nifti(input_path)
    shape, spacing = validate_image(img)
    print(f"Loaded MRI: shape={shape}, spacing={spacing}")

    data = img.get_fdata(dtype=np.float32)
    norm_data = intensity_normalization(data)

    # Preserve original header and affine
    preproc_img = nib.Nifti1Image(norm_data, affine=img.affine, header=img.header)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    nib.save(preproc_img, output_path)
    print(f"Preprocessed MRI saved to {output_path}")

if __name__ == "__main__":
    # Example usage from command line
    import argparse
    parser = argparse.ArgumentParser(description="Preprocess a T1 MRI for NeuroTrace")
    parser.add_argument("input", help="Path to input .nii/.nii.gz file")
    parser.add_argument("output", help="Path where the preprocessed file will be written")
    args = parser.parse_args()
    preprocess_mri(args.input, args.output)
