from pathlib import Path

import nibabel as nib
import numpy as np
import trimesh

from scipy import ndimage
from skimage.measure import marching_cubes


ROOT = Path(__file__).resolve().parents[2]

SEGMENTATION = (
    ROOT
    / "models"
    / "wholeBrainSeg_Large_UNEST_segmentation"
    / "eval"
    / "crl_104"
    / "crl_104_trans.nii.gz"
)

OUTPUT_DIR = ROOT / "frontend" / "public" / "models"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "crl_104_clean_brain.glb"
)


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

# Maximum faces for the outer brain.
BRAIN_MAX_FACES = 35000

# Maximum faces for individual anatomical structures.
REGION_MAX_FACES = 3500

# Remove components smaller than this.
MIN_COMPONENT_SIZE = 100


# ============================================================
# LOAD SEGMENTATION
# ============================================================

print("================================")
print("Loading UNesT segmentation")
print("================================")

print(SEGMENTATION)

if not SEGMENTATION.exists():
    raise FileNotFoundError(
        f"Segmentation not found:\n{SEGMENTATION}"
    )


img = nib.load(SEGMENTATION)

data = np.asarray(
    img.dataobj,
    dtype=np.int16
)

affine = img.affine

voxel_sizes = np.asarray(
    img.header.get_zooms()[:3],
    dtype=float
)

print("Shape:", data.shape)
print("Voxel spacing:", voxel_sizes)


# ============================================================
# CONNECTED COMPONENT FUNCTIONS
# ============================================================

def largest_component(mask):
    """
    Keep ONLY the largest connected component.
    This is the key cleanup step for removing
    floating segmentation fragments.
    """

    if not np.any(mask):
        return mask

    labeled, count = ndimage.label(
        mask,
        structure=np.ones((3, 3, 3))
    )

    if count == 0:
        return mask

    sizes = np.bincount(
        labeled.ravel()
    )

    sizes[0] = 0

    largest_id = np.argmax(sizes)

    print(
        f"    Components found: {count}"
    )

    print(
        f"    Largest component: "
        f"{sizes[largest_id]:,} voxels"
    )

    return labeled == largest_id


def clean_region(mask):
    """
    First remove tiny components,
    then keep the largest remaining component.
    """

    if not np.any(mask):
        return mask

    labeled, count = ndimage.label(
        mask,
        structure=np.ones((3, 3, 3))
    )

    if count == 0:
        return mask

    sizes = np.bincount(
        labeled.ravel()
    )

    sizes[0] = 0

    # Remove tiny components.
    valid_ids = np.where(
        sizes >= MIN_COMPONENT_SIZE
    )[0]

    valid_ids = valid_ids[
        valid_ids != 0
    ]

    if len(valid_ids) == 0:
        return np.zeros_like(
            mask,
            dtype=bool
        )

    # Among valid components,
    # keep only the largest.
    largest_id = valid_ids[
        np.argmax(
            sizes[valid_ids]
        )
    ]

    print(
        f"    Components found: {count}"
    )

    print(
        f"    Keeping component: "
        f"{sizes[largest_id]:,} voxels"
    )

    return labeled == largest_id


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
# MESH CREATION
# ============================================================

def create_mesh(
    mask,
    spacing,
    material,
    max_faces,
):

    if not np.any(mask):
        return None

    vertices, faces, normals, values = (
        marching_cubes(
            mask.astype(np.float32),
            level=0.5,
            spacing=spacing,
        )
    )

    # Convert voxel coordinates
    # into world coordinates.
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

    # Simplify mesh.
    if original_faces > max_faces:

        try:

            mesh = mesh.simplify_quadric_decimation(
                face_count=max_faces
            )

            print(
                f"    Faces: "
                f"{original_faces:,} → "
                f"{len(mesh.faces):,}"
            )

        except Exception as error:

            print(
                "    Mesh simplification "
                f"failed: {error}"
            )

    return mesh


# ============================================================
# CREATE SCENE
# ============================================================

scene = trimesh.Scene()


# ============================================================
# 1. OUTER BRAIN
# ============================================================

print()
print("================================")
print("Creating CLEAN brain surface")
print("================================")


brain_mask = data > 0

print(
    "Initial brain voxels:",
    int(brain_mask.sum())
)


# THE IMPORTANT FIX:
# Keep ONLY the largest connected component.
brain_mask = largest_component(
    brain_mask
)


print(
    "Clean brain voxels:",
    int(brain_mask.sum())
)


brain_mesh = create_mesh(
    brain_mask,
    voxel_sizes,
    brain_material,
    BRAIN_MAX_FACES,
)


if brain_mesh is not None:

    scene.add_geometry(
        brain_mesh,
        node_name="BrainSurface",
        geom_name="BrainSurface",
    )

    print(
        "Brain surface added."
    )


# ============================================================
# 2. IMPORTANT ANATOMICAL REGIONS
# ============================================================

print()
print("================================")
print("Creating anatomical regions")
print("================================")


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


    # Remove disconnected fragments
    # and keep the main component.
    mask = clean_region(
        mask
    )


    cleaned_voxels = int(
        mask.sum()
    )

    if cleaned_voxels == 0:

        continue


    mesh = create_mesh(
        mask,
        voxel_sizes,
        region_material,
        REGION_MAX_FACES,
    )


    if mesh is None:
        continue


    volume_mm3 = (
        cleaned_voxels
        * abs(
            np.linalg.det(
                affine[:3, :3]
            )
        )
    )


    mesh.metadata["label"] = label

    mesh.metadata["region_name"] = name

    mesh.metadata["voxel_count"] = (
        cleaned_voxels
    )

    mesh.metadata["volume_mm3"] = (
        volume_mm3
    )


    scene.add_geometry(
        mesh,
        node_name=name,
        geom_name=name,
    )


    print(
        f"    Volume: "
        f"{volume_mm3:.1f} mm³"
    )


# ============================================================
# 3. EXPORT
# ============================================================

print()
print("================================")
print("EXPORTING CLEAN BRAIN")
print("================================")

print(
    "Meshes:",
    len(scene.geometry)
)


total_faces = sum(
    len(mesh.faces)
    for mesh in scene.geometry.values()
)

print(
    "Total faces:",
    total_faces
)


scene.export(
    OUTPUT_FILE,
    file_type="glb",
)


print()
print("================================")
print("CLEAN BRAIN COMPLETE")
print("================================")

print(
    "Output:"
)

print(
    OUTPUT_FILE
)

print()
print(
    f"File size: "
    f"{OUTPUT_FILE.stat().st_size / 1024 / 1024:.2f} MB"
)