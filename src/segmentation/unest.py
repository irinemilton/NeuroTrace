import os
import torch
import nibabel as nib
import numpy as np
from monai.inferers import SlidingWindowInferer
from monai.transforms import (
    Compose,
    LoadImaged,
    EnsureChannelFirstd,
    NormalizeIntensityd,
    EnsureTyped,
    Activationsd,
    Invertd,
    AsDiscreted,
    SaveImaged,
)
from monai.data import Dataset, DataLoader
from typing import Optional
import sys

MODEL_DIR = os.path.join("models", "wholeBrainSeg_Large_UNEST_segmentation")
sys.path.append(os.path.join(MODEL_DIR, "scripts"))

from networks.unest_base_patch_4 import UNesT


def load_unest_model(device: torch.device) -> UNesT:
    """Load the pretrained UNesT model for 133-class brain segmentation."""
    model = UNesT(
        in_channels=1,
        out_channels=133,
        img_size=(96, 96, 96),
        feature_size=16,
        patch_size=4,
        depths=(2, 2, 8, 2),
        num_heads=(4, 8, 16, 32),
        embed_dim=(128, 256, 512),
        norm_name="instance",
        conv_block=False,
        res_block=True,
        dropout_rate=0.0,
    )
    model.to(device)

    checkpoint_path = os.path.join(MODEL_DIR, "models", "model.pt")
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Model checkpoint not found at {checkpoint_path}")

    state_dict = torch.load(checkpoint_path, map_location=device)
    if "state_dict" in state_dict:
        state_dict = state_dict["state_dict"]

    new_state_dict = {}
    for k, v in state_dict.items():
        new_key = k.replace("module.", "").replace("network.", "")
        new_state_dict[new_key] = v

    missing, unexpected = model.load_state_dict(new_state_dict, strict=False)
    if missing:
        print(f"Missing keys: {missing}")
    if unexpected:
        print(f"Unexpected keys: {unexpected}")

    model.eval()
    print("UNesT model loaded successfully")
    return model


def get_preprocessing_transforms():
    """Return MONAI preprocessing transforms matching the inference config."""
    return Compose([
        LoadImaged(keys="image"),
        EnsureChannelFirstd(keys="image"),
        NormalizeIntensityd(keys="image", nonzero=True, channel_wise=True),
        EnsureTyped(keys="image"),
    ])


def get_postprocessing_transforms(preprocessing_transforms, output_dir: str):
    """Return MONAI postprocessing transforms."""
    return Compose([
        Activationsd(keys="pred", softmax=True),
        Invertd(
            keys="pred",
            transform=preprocessing_transforms,
            orig_keys="image",
            meta_key_postfix="meta_dict",
            nearest_interp=False,
            to_tensor=True,
        ),
        AsDiscreted(keys="pred", argmax=True),
        SaveImaged(keys="pred", meta_keys="pred_meta_dict", output_dir=output_dir, output_postfix="seg", resample=False),
    ])


def segment_mri(
    input_path: str,
    output_dir: str,
    device: Optional[torch.device] = None,
    roi_size: tuple = (96, 96, 96),
    sw_batch_size: int = 4,
    overlap: float = 0.7,
    use_cache: bool = True,
) -> str:
    """
    Run UNesT segmentation on a preprocessed MRI scan.

    Args:
        input_path: Path to preprocessed NIfTI file (.nii.gz)
        output_dir: Directory to save segmentation output
        device: Torch device (auto-detected if None)
        roi_size: Sliding window ROI size
        sw_batch_size: Sliding window batch size
        overlap: Overlap between windows
        use_cache: If True, skip processing if output already exists

    Returns:
        Path to the segmentation output file
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    if base_name.endswith(".nii"):
        base_name = os.path.splitext(base_name)[0]
    output_file = os.path.join(output_dir, f"{base_name}_seg.nii.gz")

    if use_cache and os.path.exists(output_file):
        print(f"Using cached segmentation: {output_file}")
        return output_file

    print(f"Loading UNesT model on {device}...")
    model = load_unest_model(device)

    inferer = SlidingWindowInferer(
        roi_size=roi_size,
        sw_batch_size=sw_batch_size,
        overlap=overlap,
        mode="gaussian",
        device=device,
    )

    preprocessing = get_preprocessing_transforms()
    postprocessing = get_postprocessing_transforms(preprocessing, output_dir)

    data = [{"image": input_path}]
    dataset = Dataset(data=data, transform=preprocessing)
    dataloader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=0)

    print(f"Running segmentation on {input_path}...")
    with torch.no_grad():
        for batch in dataloader:
            inputs = batch["image"].to(device)
            preds = inferer(inputs, model)
            batch["pred"] = preds
            postprocessing(batch)

    print(f"Segmentation saved to {output_file}")
    return output_file


def load_segmentation(seg_path: str) -> np.ndarray:
    """Load segmentation mask as numpy array."""
    img = nib.load(seg_path)
    return img.get_fdata(dtype=np.int32)


def get_region_volumes(seg_array: np.ndarray, voxel_volume_mm3: float) -> dict:
    """Calculate volume (in mm^3) for each segmented region."""
    unique, counts = np.unique(seg_array, return_counts=True)
    volumes = {}
    for label_id, count in zip(unique, counts):
        if label_id == 0:
            continue
        volumes[int(label_id)] = count * voxel_volume_mm3
    return volumes


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run UNesT brain segmentation")
    parser.add_argument("input", help="Path to preprocessed .nii.gz MRI file")
    parser.add_argument("output_dir", help="Directory to save segmentation")
    parser.add_argument("--no-cache", action="store_true", help="Disable caching")
    args = parser.parse_args()

    segment_mri(args.input, args.output_dir, use_cache=not args.no_cache)