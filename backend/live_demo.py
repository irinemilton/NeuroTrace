from pathlib import Path
from uuid import uuid4

import base64
import json
import re
import shutil

import joblib
import nibabel as nib
import numpy as np
import pandas as pd

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from scipy import ndimage
from skimage.measure import marching_cubes

from src.features.update_brain_features import extract_subject
from src.features.measurements import measure_subject
from src.ml.shap_explainer import explain_features
from src.segmentation.single_segment import segment_single_mri


router = APIRouter()


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

MODEL_DIR = (
    ROOT
    / "models"
    / "alzheimer"
)

MODEL_PATH = (
    MODEL_DIR
    / "neurotrace_alzheimer_model.joblib"
)

META_PATH = (
    MODEL_DIR
    / "neurotrace_feature_metadata.json"
)

LIVE_ROOT = (
    ROOT
    / "data"
    / "live_demo"
)

LIVE_MODELS = (
    ROOT
    / "frontend"
    / "public"
    / "models"
    / "live_demo"
)

LIVE_ROOT.mkdir(
    parents=True,
    exist_ok=True,
)

LIVE_MODELS.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# ANATOMICAL REGIONS
# ============================================================

REGION_LABELS = {

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
# SAME PERFORMANCE SETTINGS AS BRAIN ANALYSIS
# ============================================================

BRAIN_MAX_FACES = 35000

REGION_MAX_FACES = 3500

MIN_COMPONENT_SIZE = 100


# ============================================================
# LOAD ML MODEL
# ============================================================

def load_model():

    if (
        not MODEL_PATH.exists()
        or not META_PATH.exists()
    ):
        raise RuntimeError(
            "Alzheimer model or feature metadata is missing."
        )

    model = joblib.load(
        MODEL_PATH
    )

    features = json.loads(
        META_PATH.read_text(
            encoding="utf-8"
        )
    ).get(
        "features",
        [],
    )

    if len(features) != 141:

        raise RuntimeError(
            f"Expected 141 features, found {len(features)}"
        )

    return model, features


# ============================================================
# ML PREDICTION
# ============================================================

def predict(
    model,
    features,
    values,
):

    frame = pd.DataFrame(
        [
            {
                name: float(
                    values.get(
                        name,
                        0.0,
                    )
                )
                for name in features
            }
        ],
        columns=features,
    )

    prediction = int(
        model.predict(frame)[0]
    )

    probabilities = (
        model.predict_proba(frame)[0]
    )

    classes = list(
        model.classes_
    )

    probability_ad = (
        float(
            probabilities[
                classes.index(1)
            ]
        )
        if 1 in classes
        else 0.0
    )

    probability_non_ad = (
        float(
            probabilities[
                classes.index(0)
            ]
        )
        if 0 in classes
        else 0.0
    )

    explanation = []


    try:

        scaled = (
            model
            .named_steps["scaler"]
            .transform(frame)[0]
        )

        coefficients = (
            model
            .named_steps["classifier"]
            .coef_[0]
        )

        explanation = [

            {
                "feature": name,

                "contribution": float(
                    value
                ),

                "direction": (
                    "AD"
                    if value > 0
                    else "Non-AD"
                ),
            }

            for name, value
            in zip(
                features,
                scaled * coefficients,
            )
        ]


        explanation.sort(
            key=lambda item:
                abs(
                    item[
                        "contribution"
                    ]
                ),
            reverse=True,
        )


        explanation = (
            explanation[:10]
        )

    except Exception:

        pass


    return {

        "prediction":
            prediction,

        "classification":
            "AD"
            if prediction
            else "Non-AD",

        "probability_ad":
            probability_ad,

        "probability_non_ad":
            probability_non_ad,

        "model":
            "Logistic Regression",

        "model_C":
            0.01,

        "features_used":
            141,

        "explanation":
            explanation,
    }


# ============================================================
# CONNECTED COMPONENT CLEANING
# SAME LOGIC AS EXISTING BRAIN ANALYSIS
# ============================================================

def largest_component(mask):

    if not np.any(mask):

        return mask


    labeled, count = ndimage.label(
        mask,
        structure=np.ones(
            (3, 3, 3)
        ),
    )


    if count == 0:

        return mask


    sizes = np.bincount(
        labeled.ravel()
    )

    sizes[0] = 0


    largest_id = np.argmax(
        sizes
    )


    return (
        labeled ==
        largest_id
    )


# ============================================================

def clean_region(mask):

    if not np.any(mask):

        return mask


    labeled, count = ndimage.label(
        mask,
        structure=np.ones(
            (3, 3, 3)
        ),
    )


    if count == 0:

        return mask


    sizes = np.bincount(
        labeled.ravel()
    )

    sizes[0] = 0


    valid_ids = np.where(
        sizes >=
        MIN_COMPONENT_SIZE
    )[0]


    valid_ids = valid_ids[
        valid_ids != 0
    ]


    if len(valid_ids) == 0:

        return np.zeros_like(
            mask,
            dtype=bool,
        )


    largest_id = valid_ids[
        np.argmax(
            sizes[
                valid_ids
            ]
        )
    ]


    return (
        labeled ==
        largest_id
    )


# ============================================================
# MATERIALS
# SAME MATERIALS AS EXISTING BRAIN ANALYSIS
# ============================================================

def create_brain_material():

    import trimesh

    return (
        trimesh.visual.material.PBRMaterial(
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
    )


# ============================================================

def create_region_material():

    import trimesh

    return (
        trimesh.visual.material.PBRMaterial(
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
    )


# ============================================================
# MESH CREATION
# SAME GEOMETRY LOGIC AS segmentation_to_glb.py
# ============================================================

def create_mesh(
    mask,
    spacing,
    affine,
    material,
    max_faces,
):

    import trimesh


    if not np.any(mask):

        return None


    vertices, faces, normals, values = (
        marching_cubes(
            mask.astype(
                np.float32
            ),

            level=0.5,

            spacing=spacing,
        )
    )


    # --------------------------------------------------------
    # Convert voxel coordinates to world coordinates
    # --------------------------------------------------------

    vertices_h = np.column_stack(
        [
            vertices,
            np.ones(
                len(vertices)
            ),
        ]
    )


    vertices_world = (
        vertices_h
        @ affine.T
    )[:, :3]


    # --------------------------------------------------------
    # Create mesh
    # --------------------------------------------------------

    mesh = trimesh.Trimesh(
        vertices=vertices_world,

        faces=faces,

        process=True,
    )


    mesh.visual.material = (
        material
    )


    # --------------------------------------------------------
    # Simplify exactly like existing pipeline
    # --------------------------------------------------------

    original_faces = (
        len(mesh.faces)
    )


    if (
        original_faces >
        max_faces
    ):

        try:

            mesh = (
                mesh
                .simplify_quadric_decimation(
                    face_count=max_faces
                )
            )

        except Exception:

            pass


    return mesh


# ============================================================
# GENERATE LIVE BRAIN GLB
# SAME PIPELINE AS EXISTING BRAIN ANALYSIS
# ============================================================

def make_brain_glb(
    segmentation_path,
    subject_id,
):

    import trimesh


    # --------------------------------------------------------
    # Load NIfTI
    # --------------------------------------------------------

    image = nib.load(
        str(
            segmentation_path
        )
    )


    data = np.asarray(
        image.dataobj,
        dtype=np.int16,
    )


    affine = image.affine


    voxel_sizes = np.asarray(
        image.header.get_zooms()[:3],
        dtype=float,
    )


    # Prevent invalid spacing

    voxel_sizes = np.maximum(
        voxel_sizes,
        0.001,
    )


    scene = trimesh.Scene()


    brain_material = (
        create_brain_material()
    )

    region_material = (
        create_region_material()
    )


    mesh_count = 0


    # ========================================================
    # OUTER BRAIN
    # ========================================================

    brain_mask = (
        data > 0
    )


    # CRITICAL CLEANUP:
    # Keep only the largest connected
    # brain component.

    brain_mask = (
        largest_component(
            brain_mask
        )
    )


    brain_mesh = create_mesh(
        brain_mask,

        voxel_sizes,

        affine,

        brain_material,

        BRAIN_MAX_FACES,
    )


    if brain_mesh is not None:

        scene.add_geometry(
            brain_mesh,

            node_name=
                "BrainSurface",

            geom_name=
                "BrainSurface",
        )

        mesh_count += 1


    # ========================================================
    # IMPORTANT ANATOMICAL REGIONS
    # ========================================================

    for label, name in (
        REGION_LABELS.items()
    ):

        mask = (
            data == label
        )


        if not np.any(mask):

            continue


        # Remove disconnected
        # fragments.

        mask = clean_region(
            mask
        )


        if not np.any(mask):

            continue


        mesh = create_mesh(
            mask,

            voxel_sizes,

            affine,

            region_material,

            REGION_MAX_FACES,
        )


        if mesh is None:

            continue


        # ----------------------------------------------------
        # Store useful metadata
        # ----------------------------------------------------

        voxel_count = int(
            mask.sum()
        )


        volume_mm3 = (
            voxel_count
            *
            abs(
                np.linalg.det(
                    affine[:3, :3]
                )
            )
        )


        mesh.metadata[
            "label"
        ] = label


        mesh.metadata[
            "region_name"
        ] = name


        mesh.metadata[
            "voxel_count"
        ] = voxel_count


        mesh.metadata[
            "volume_mm3"
        ] = volume_mm3


        scene.add_geometry(
            mesh,

            node_name=name,

            geom_name=name,
        )


        mesh_count += 1


    # ========================================================
    # VALIDATE
    # ========================================================

    if mesh_count == 0:

        raise RuntimeError(
            "No renderable geometry was generated "
            "from the uploaded segmentation."
        )


    # ========================================================
    # EXPORT
    # ========================================================

    filename = (
        f"{subject_id}"
        "_clean_brain.glb"
    )


    output_path = (
        LIVE_MODELS /
        filename
    )


    scene.export(
        output_path,
        file_type="glb",
    )


    if (
        not output_path.exists()
        or output_path.stat().st_size == 0
    ):

        raise RuntimeError(
            "GLB generation produced "
            "an empty file."
        )


    return (
        f"/models/live_demo/{filename}",
        mesh_count,
    )


# ============================================================
# FILE HELPERS
# ============================================================

def save(
    upload,
    path,
):

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


    with path.open(
        "wb"
    ) as output:

        shutil.copyfileobj(
            upload.file,
            output,
        )


# ============================================================

def validate(
    upload,
):

    filename = (
        upload.filename
        or ""
    ).lower()


    if not (
        filename.endswith(
            ".nii"
        )
        or
        filename.endswith(
            ".nii.gz"
        )
    ):

        raise HTTPException(
            400,
            "Only .nii and .nii.gz files are supported.",
        )


# ============================================================

def validate_nifti(
    path,
):

    try:

        nib.load(
            str(path)
        )

    except Exception as error:

        raise HTTPException(
            400,
            f"Invalid NIfTI: {error}",
        )


# ============================================================
# PROCESS PIPELINE
# ============================================================

def process(
    subject_id,
    mode,
    filename,
    segmentation_path,
):

    model, features = (
        load_model()
    )


    # --------------------------------------------------------
    # MRI FEATURES
    # --------------------------------------------------------

    values = extract_subject(
        subject_id,
        segmentation_path,
    )


    # --------------------------------------------------------
    # ML
    # --------------------------------------------------------

    prediction = predict(
        model,
        features,
        values,
    )


    # --------------------------------------------------------
    # MEASUREMENTS
    # --------------------------------------------------------

    measurements = (
        measure_subject(
            segmentation_path
        )
    )


    # --------------------------------------------------------
    # SAME 3D GENERATION AS
    # EXISTING BRAIN ANALYSIS
    # --------------------------------------------------------

    (
        model_url,
        mesh_count,
    ) = make_brain_glb(
        segmentation_path,
        subject_id,
    )


    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    result = {

        "status":
            "success",

        "subject_id":
            subject_id,

        "mode":
            mode,

        "input_filename":
            filename,

        "segmentation_process":
            (
                "included"
                if mode == "full"
                else "pre-computed"
            ),

        "mri_available":
            True,

        "segmentation_available":
            True,

        "feature_count":
            141,

        "measurements":
            measurements,

        "prediction":
            prediction,

        "model_url":
            model_url,

        "model_mesh_count":
            mesh_count,

        "message":
            (
                "Full raw T1 MRI → UNesT → "
                "features → ML → 3D analysis completed."
                if mode == "full"
                else
                "Pre-segmented MRI → features → "
                "ML → 3D analysis completed."
            ),
    }


    # --------------------------------------------------------
    # SAVE RESULT
    # --------------------------------------------------------

    directory = (
        LIVE_ROOT /
        subject_id
    )


    directory.mkdir(
        parents=True,
        exist_ok=True,
    )


    (
        directory /
        "result.json"
    ).write_text(
        json.dumps(
            result,
            indent=2,
        ),
        encoding="utf-8",
    )


    return result


# ============================================================
# QUICK ANALYSIS
# ============================================================

@router.post(
    "/live-demo/quick"
)
async def quick(
    file: UploadFile = File(...)
):

    validate(file)


    subject_id = (
        f"live_quick_"
        f"{uuid4().hex[:12]}"
    )


    directory = (
        LIVE_ROOT /
        subject_id
    )


    segmentation = (
        directory /
        "segmentation.nii.gz"
    )


    save(
        file,
        segmentation,
    )


    validate_nifti(
        segmentation
    )


    try:

        return process(
            subject_id,

            "quick",

            file.filename
            or "uploaded_segmentation.nii.gz",

            segmentation,
        )


    except Exception as error:

        shutil.rmtree(
            directory,
            ignore_errors=True,
        )


        raise HTTPException(
            500,
            f"Quick analysis failed: {error}",
        )


# ============================================================
# FULL PIPELINE
# ============================================================

@router.post(
    "/live-demo/full"
)
async def full(
    file: UploadFile = File(...)
):

    validate(file)


    subject_id = (
        f"live_full_"
        f"{uuid4().hex[:12]}"
    )


    directory = (
        LIVE_ROOT /
        subject_id
    )


    raw = (
        directory /
        "raw.nii.gz"
    )


    save(
        file,
        raw,
    )


    validate_nifti(
        raw
    )


    try:

        # ----------------------------------------------------
        # EXISTING SINGLE-SUBJECT UNesT
        # ----------------------------------------------------

        generated = (
            segment_single_mri(
                raw,
                subject_id,
            )
        )


        segmentation = (
            directory /
            "segmentation.nii.gz"
        )


        shutil.copy2(
            generated,
            segmentation,
        )


        # ----------------------------------------------------
        # SAME PROCESSING
        # ----------------------------------------------------

        return process(
            subject_id,

            "full",

            file.filename
            or "uploaded_t1.nii.gz",

            segmentation,
        )


    except Exception as error:

        shutil.rmtree(
            directory,
            ignore_errors=True,
        )


        raise HTTPException(
            500,
            f"Full analysis failed: {error}",
        )


    finally:

        eval_dir = (
            ROOT
            / "models"
            / "wholeBrainSeg_Large_UNEST_segmentation"
            / "eval"
            / subject_id
        )


        if eval_dir.exists():

            shutil.rmtree(
                eval_dir,
                ignore_errors=True,
            )


# ============================================================
# GET LIVE RESULT
# ============================================================

@router.get(
    "/live-demo/result/{subject_id}"
)
def result(
    subject_id: str,
):

    if not re.fullmatch(
        r"live_(quick|full)_[0-9a-f]{12}",
        subject_id,
    ):

        raise HTTPException(
            404,
            "Live analysis not found.",
        )


    path = (
        LIVE_ROOT
        / subject_id
        / "result.json"
    )


    if not path.exists():

        raise HTTPException(
            404,
            "Live analysis not found.",
        )


    return json.loads(
        path.read_text(
            encoding="utf-8"
        )


# ============================================================
# GET LIVE MRI SLICE
# ============================================================

@router.get("/live-demo/slices/{subject_id}")
def slice_view(
        subject_id: str,
        axis: str = Query("axial"),
        index: int | None = Query(None),
):
        """Return safe metadata and an optionally requested grayscale slice.

        The payload uses base64 encoded uint8 pixels rather than requiring a
        server-side image library.  Pixel order is row-major and matches width /
        height in the response.
        """
        if not re.fullmatch(r"live_(quick|full)_[0-9a-f]{12}", subject_id):
            raise HTTPException(404, "Live analysis not found.")

        axis = axis.lower()
        axis_numbers = {"sagittal": 0, "coronal": 1, "axial": 2}
        if axis not in axis_numbers:
            raise HTTPException(400, "Axis must be axial, sagittal, or coronal.")

        segmentation = LIVE_ROOT / subject_id / "segmentation.nii.gz"
        if not segmentation.is_file():
            raise HTTPException(404, "Live segmentation not found.")

        try:
            image = nib.load(str(segmentation))
            shape = tuple(int(value) for value in image.shape[:3])
            if len(shape) != 3 or any(value <= 0 for value in shape):
                raise ValueError("segmentation is not a 3D volume")
            data = np.asarray(image.dataobj, dtype=np.float32)
        except Exception as error:
            raise HTTPException(422, f"Unable to read live segmentation: {error}") from error

        axis_number = axis_numbers[axis]
        axis_length = shape[axis_number]
        if index is None:
            return {
                "subject_id": subject_id,
                "axis": axis,
                "shape": list(shape),
                "voxel_spacing_mm": [float(value) for value in image.header.get_zooms()[:3]],
                "index": None,
                "slice": None,
            }
        if index < 0 or index >= axis_length:
            raise HTTPException(
                400,
                f"Slice index must be between 0 and {axis_length - 1} for {axis}.",
            )

        if axis == "axial":
            pixels = data[:, :, index].T
        elif axis == "sagittal":
            pixels = data[index, :, :].T
        else:
            pixels = data[:, index, :].T

        finite = pixels[np.isfinite(pixels)]
        if finite.size:
            low, high = np.percentile(finite, (1, 99))
            if high <= low:
                high = low + 1.0
            normalized = np.clip((np.nan_to_num(pixels, nan=low) - low) / (high - low), 0, 1)
        else:
            normalized = np.zeros_like(pixels)

        encoded = base64.b64encode(
            (normalized * 255).astype(np.uint8).tobytes(order="C")
        ).decode("ascii")
        return {
            "subject_id": subject_id,
            "axis": axis,
            "shape": list(shape),
            "voxel_spacing_mm": [float(value) for value in image.header.get_zooms()[:3]],
            "index": index,
            "width": int(normalized.shape[1]),
            "height": int(normalized.shape[0]),
            "pixels_base64": encoded,
        }
    )


# ============================================================
# GET LIVE MODEL
# ============================================================

@router.get(
    "/live-demo/model/{filename}"
)
def model(
    filename: str,
):

    if not re.fullmatch(
        r"live_(quick|full)_[0-9a-f]{12}_clean_brain\.glb",
        filename,
    ):

        raise HTTPException(
            404,
            "Model not found.",
        )


    path = (
        LIVE_MODELS /
        filename
    )


    if not path.exists():

        raise HTTPException(
            404,
            "Model not found.",
        )


    return FileResponse(
        path,

        media_type=
            "model/gltf-binary",

        filename=
            path.name,
    )