from pathlib import Path

import nibabel as nib
import numpy as np
import trimesh

from scipy import ndimage
from skimage.measure import marching_cubes


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

EVAL_DIR = (
    ROOT
    / "models"
    / "wholeBrainSeg_Large_UNEST_segmentation"
    / "eval"
)

OUTPUT_DIR = ROOT / "frontend" / "public" / "models"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# IMPORTANT ANATOMICAL REGIONS
# ============================================================

IMPORTANT_REGIONS = {
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
}


# ============================================================
# PERFORMANCE SETTINGS
# ============================================================

BRAIN_MAX_FACES = 35000
REGION_MAX_FACES = 3500
MIN_COMPONENT_SIZE = 100


# ============================================================
# MATERIALS
# ============================================================

brain_material = trimesh.visual.material.PBRMaterial(
    name="BrainSurface",
    baseColorFactor=[
        145,
        165,
        195,
        150,
    ],
    metallicFactor=0.0,
    roughnessFactor=0.85,
    alphaMode="BLEND",
    doubleSided=True,
)


region_material = trimesh.visual.material.PBRMaterial(
    name="ImportantRegion",
    baseColorFactor=[
        70,
        165,
        245,
        255,
    ],
    metallicFactor=0.05,
    roughnessFactor=0.5,
    alphaMode="BLEND",
    doubleSided=True,
)


# ============================================================
# CONNECTED COMPONENT FUNCTIONS
# ============================================================

def largest_component(mask):
    """
    Keep only the largest connected component.
    Used for the outer brain mask.
    """

    if not np.any(mask):
        return mask

    labeled, count = ndimage.label(
        mask,
        structure=np.ones((3, 3, 3)),
    )

    if count == 0:
        return mask

    sizes = np.bincount(labeled.ravel())
    sizes[0] = 0

    largest_id = np.argmax(sizes)

    print(f"    Components found: {count}")
    print(
        f"    Largest component: "
        f"{sizes[largest_id]:,} voxels"
    )

    return labeled == largest_id


def clean_region(mask):
    """
    Remove tiny disconnected components and keep
    the largest meaningful component.
    """

    if not np.any(mask):
        return mask

    labeled, count = ndimage.label(
        mask,
        structure=np.ones((3, 3, 3)),
    )

    if count == 0:
        return mask

    sizes = np.bincount(labeled.ravel())
    sizes[0] = 0

    valid_ids = np.where(
        sizes >= MIN_COMPONENT_SIZE
    )[0]

    valid_ids = valid_ids[valid_ids != 0]

    if len(valid_ids) == 0:
        return np.zeros_like(mask, dtype=bool)

    largest_id = valid_ids[
        np.argmax(sizes[valid_ids])
    ]

    print(f"    Components found: {count}")
    print(
        f"    Keeping component: "
        f"{sizes[largest_id]:,} voxels"
    )

    return labeled == largest_id


# ============================================================
# MESH CREATION
# ============================================================

def create_mesh(
    mask,
    affine,
    material,
    max_faces,
):
    """
    Convert a voxel mask into a world-space triangular mesh.

    Important:
    marching_cubes works in voxel coordinates here.
    The NIfTI affine is applied exactly once afterward.
    """

    if not np.any(mask):
        return None

    # Generate surface in voxel coordinates.
    vertices, faces, normals, values = marching_cubes(
        mask.astype(np.float32),
        level=0.5,
        spacing=(1.0, 1.0, 1.0),
    )

    # Convert voxel coordinates to world coordinates.
    vertices_h = np.column_stack(
        [
            vertices,
            np.ones(len(vertices)),
        ]
    )

    vertices_world = (
        vertices_h @ affine.T
    )[:, :3]

    mesh = trimesh.Trimesh(
        vertices=vertices_world,
        faces=faces,
        process=True,
    )

    mesh.visual.material = material

    original_faces = len(mesh.faces)

    if original_faces > max_faces:
        try:
            mesh = mesh.simplify_quadric_decimation(
                face_count=max_faces
            )

            print(
                f"    Faces: "
                f"{original_faces:,} -> "
                f"{len(mesh.faces):,}"
            )

        except Exception as error:
            print(
                "    Mesh simplification failed: "
                f"{error}"
            )

    return mesh


# ============================================================
# GENERATE ONE SUBJECT
# ============================================================

def generate_subject_glb(segmentation_path):
    """
    Generate one subject-specific GLB.

    Example:
        crl_104_trans.nii.gz
        ->
        crl_104_clean_brain.glb
    """

    subject_id = segmentation_path.name.replace(
        "_trans.nii.gz",
        "",
    )

    output_file = (
        OUTPUT_DIR
        / f"{subject_id}_clean_brain.glb"
    )

    print()
    print("=" * 70)
    print(f"GENERATING GLB: {subject_id}")
    print("=" * 70)

    print(f"Input:")
    print(segmentation_path)

    print(f"Output:")
    print(output_file)

    # --------------------------------------------------------
    # LOAD NIFTI
    # --------------------------------------------------------

    img = nib.load(segmentation_path)

    data = np.asarray(
        img.dataobj,
        dtype=np.int16,
    )

    affine = img.affine

    voxel_sizes = np.asarray(
        img.header.get_zooms()[:3],
        dtype=float,
    )

    print(f"Shape: {data.shape}")
    print(
        "Voxel spacing: "
        f"{voxel_sizes}"
    )

    # --------------------------------------------------------
    # CREATE SCENE
    # --------------------------------------------------------

    scene = trimesh.Scene()

    # --------------------------------------------------------
    # OUTER BRAIN
    # --------------------------------------------------------

    print()
    print("-" * 60)
    print("Creating clean brain surface")
    print("-" * 60)

    brain_mask = data > 0

    print(
        "Initial brain voxels:",
        int(brain_mask.sum()),
    )

    brain_mask = largest_component(
        brain_mask
    )

    print(
        "Clean brain voxels:",
        int(brain_mask.sum()),
    )

    brain_mesh = create_mesh(
        brain_mask,
        affine,
        brain_material,
        BRAIN_MAX_FACES,
    )

    if brain_mesh is not None:

        scene.add_geometry(
            brain_mesh,
            node_name="BrainSurface",
            geom_name="BrainSurface",
        )

        print("Brain surface added.")

    # --------------------------------------------------------
    # IMPORTANT REGIONS
    # --------------------------------------------------------

    print()
    print("-" * 60)
    print("Creating anatomical regions")
    print("-" * 60)

    for label, name in IMPORTANT_REGIONS.items():

        print()
        print(
            f"{name} "
            f"(label {label})"
        )

        mask = data == label

        voxel_count = int(
            mask.sum()
        )

        print(
            f"    Original voxels: "
            f"{voxel_count:,}"
        )

        if voxel_count == 0:
            print(
                "    Region not found."
            )
            continue

        # Clean disconnected pieces.
        mask = clean_region(mask)

        cleaned_voxels = int(
            mask.sum()
        )

        if cleaned_voxels == 0:
            print(
                "    No valid component."
            )
            continue

        mesh = create_mesh(
            mask,
            affine,
            region_material,
            REGION_MAX_FACES,
        )

        if mesh is None:
            continue

        # Physical volume.
        voxel_volume = abs(
            np.linalg.det(
                affine[:3, :3]
            )
        )

        volume_mm3 = (
            cleaned_voxels
            * voxel_volume
        )

        mesh.metadata["label"] = label
        mesh.metadata["region_name"] = name
        mesh.metadata["voxel_count"] = cleaned_voxels
        mesh.metadata["volume_mm3"] = volume_mm3

        scene.add_geometry(
            mesh,
            node_name=name,
            geom_name=name,
        )

        print(
            f"    Volume: "
            f"{volume_mm3:.1f} mm3"
        )

    # --------------------------------------------------------
    # EXPORT
    # --------------------------------------------------------

    print()
    print("-" * 60)
    print("EXPORTING")
    print("-" * 60)

    print(
        "Meshes:",
        len(scene.geometry),
    )

    total_faces = sum(
        len(mesh.faces)
        for mesh in scene.geometry.values()
    )

    print(
        "Total faces:",
        total_faces,
    )

    scene.export(
        output_file,
        file_type="glb",
    )

    file_size_mb = (
        output_file.stat().st_size
        / 1024
        / 1024
    )

    print()
    print(
        f"SUCCESS: {subject_id}"
    )

    print(
        f"GLB: {output_file}"
    )

    print(
        f"Size: {file_size_mb:.2f} MB"
    )

    return output_file


# ============================================================
# FIND COMPLETED SEGMENTATIONS
# ============================================================

def find_segmentations():
    """
    Find every completed UNesT segmentation.
    """

    if not EVAL_DIR.exists():
        raise FileNotFoundError(
            f"UNesT eval directory not found:\n{EVAL_DIR}"
        )

    files = sorted(
        EVAL_DIR.glob(
            "*/*_trans.nii.gz"
        )
    )

    return files


# ============================================================
# MAIN BATCH PROCESS
# ============================================================

def main():

    print()
    print("=" * 70)
    print("NEUROTRACE — BATCH GLB GENERATOR")
    print("=" * 70)

    print()
    print(f"Segmentation directory:")
    print(EVAL_DIR)

    print()
    print(f"GLB output directory:")
    print(OUTPUT_DIR)

    segmentations = find_segmentations()

    print()
    print(
        f"Completed segmentations found: "
        f"{len(segmentations)}"
    )

    if not segmentations:
        print(
            "No completed segmentations found."
        )
        return

    successful = 0
    failed = 0

    for index, segmentation_path in enumerate(
        segmentations,
        start=1,
    ):

        subject_id = segmentation_path.name.replace(
            "_trans.nii.gz",
            "",
        )

        print()
        print(
            f"[{index}/{len(segmentations)}] "
            f"{subject_id}"
        )

        try:

            generate_subject_glb(
                segmentation_path
            )

            successful += 1

        except Exception as error:

            failed += 1

            print()
            print(
                f"ERROR generating {subject_id}:"
            )

            print(error)

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("BATCH GLB GENERATION COMPLETE")
    print("=" * 70)

    print(
        f"Successful: {successful}"
    )

    print(
        f"Failed: {failed}"
    )

    print(
        f"Total: {len(segmentations)}"
    )

    print()
    print(
        f"Output directory:"
    )

    print(
        OUTPUT_DIR
    )


if __name__ == "__main__":
    main()