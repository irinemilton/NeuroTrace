"""Reconstruct a 3-D NIfTI volume from a DICOM MRI series."""

import argparse
from pathlib import Path
from typing import Iterable

import nibabel as nib
import numpy as np
import pydicom


def _dicom_files(input_dir: Path) -> Iterable[Path]:
    for path in input_dir.rglob("*"):
        if path.is_file():
            try:
                pydicom.dcmread(str(path), stop_before_pixels=True)
            except (pydicom.errors.InvalidDicomError, OSError):
                continue
            yield path


def _slice_position(dataset) -> float:
    orientation = np.asarray(dataset.ImageOrientationPatient, dtype=float)
    normal = np.cross(orientation[:3], orientation[3:])
    return float(np.dot(np.asarray(dataset.ImagePositionPatient, dtype=float), normal))


def _affine(datasets: list) -> np.ndarray:
    orientation = np.asarray(datasets[0].ImageOrientationPatient, dtype=float)
    row_direction, column_direction = orientation[:3], orientation[3:]
    row_spacing, column_spacing = map(float, datasets[0].PixelSpacing)
    if len(datasets) > 1:
        slice_spacing = abs(_slice_position(datasets[1]) - _slice_position(datasets[0]))
    else:
        slice_spacing = float(getattr(datasets[0], "SliceThickness", 1.0))
    slice_direction = np.cross(row_direction, column_direction)
    origin = np.asarray(datasets[0].ImagePositionPatient, dtype=float)

    affine = np.eye(4, dtype=float)
    # The array is indexed as [row, column, slice].
    affine[:3, 0] = column_direction * row_spacing
    affine[:3, 1] = row_direction * column_spacing
    affine[:3, 2] = slice_direction * slice_spacing
    affine[:3, 3] = origin
    return affine


def reconstruct_series(dicom_paths: list[Path], output_path: Path) -> Path:
    """Write one DICOM series as a geometry-preserving NIfTI volume."""
    datasets = [pydicom.dcmread(str(path)) for path in dicom_paths]
    datasets = [dataset for dataset in datasets if hasattr(dataset, "PixelData")]
    if not datasets:
        raise ValueError("DICOM series contains no pixel data")

    datasets.sort(key=lambda dataset: (
        _slice_position(dataset) if hasattr(dataset, "ImageOrientationPatient") and hasattr(dataset, "ImagePositionPatient")
        else float(getattr(dataset, "InstanceNumber", 0))
    ))
    first = datasets[0]
    shape = (int(first.Rows), int(first.Columns))
    slices = []
    for dataset in datasets:
        pixels = dataset.pixel_array
        if pixels.shape != shape:
            raise ValueError("DICOM series contains inconsistent slice dimensions")
        slices.append(pixels)

    data = np.stack(slices, axis=2)
    image = nib.Nifti1Image(data, _affine(datasets))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(image, str(output_path))
    return output_path


def reconstruct_dicom_directory(input_dir: str, output_dir: str) -> list[Path]:
    """Reconstruct every DICOM series found below ``input_dir``."""
    groups: dict[str, list[Path]] = {}
    for path in _dicom_files(Path(input_dir)):
        dataset = pydicom.dcmread(str(path), stop_before_pixels=True)
        uid = str(getattr(dataset, "SeriesInstanceUID", "unidentified"))
        groups.setdefault(uid, []).append(path)

    outputs = []
    for index, paths in enumerate(groups.values(), start=1):
        dataset = pydicom.dcmread(str(paths[0]), stop_before_pixels=True)
        description = str(getattr(dataset, "SeriesDescription", "series"))
        safe_name = "".join(char if char.isalnum() or char in "-_" else "_" for char in description).strip("_")
        output_name = f"{safe_name or 'series'}_{index:03d}.nii.gz"
        output = reconstruct_series(paths, Path(output_dir) / output_name)
        print(f"Reconstructed {len(paths)} slices -> {output}")
        outputs.append(output)
    return outputs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reconstruct 3-D MRI volumes from DICOM series")
    parser.add_argument("input_dir", help="Directory containing DICOM files")
    parser.add_argument("output_dir", help="Directory for reconstructed NIfTI volumes")
    args = parser.parse_args()
    outputs = reconstruct_dicom_directory(args.input_dir, args.output_dir)
    if not outputs:
        raise SystemExit("No readable DICOM series found")
