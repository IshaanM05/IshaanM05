#!/usr/bin/env python3
"""Prep a photo for ASCII conversion: remove background, boost local
contrast (CLAHE), and composite onto white so the background maps to
the blank end of the ASCII ramp.

Background removal prefers rembg (neural matting) when it's installed;
otherwise it falls back to OpenCV GrabCut, a classic CV segmentation
algorithm that needs no pretrained weights.

Usage: python scripts/prep_photo.py source-photo.jpg
"""
import sys
from io import BytesIO

import cv2
import numpy as np
from PIL import Image

try:
    from rembg import remove as _rembg_remove
except ImportError:
    _rembg_remove = None


def _grabcut_cutout(bgr: np.ndarray) -> np.ndarray:
    """Segment the foreground with GrabCut, seeded by a centered rect
    (the subject is assumed roughly centered, portrait-style). Returns
    an RGBA array with the background made transparent."""
    h, w = bgr.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    margin_x, margin_y = int(w * 0.08), int(h * 0.04)
    rect = (margin_x, margin_y, w - 2 * margin_x, h - 2 * margin_y)

    cv2.grabCut(bgr, mask, rect, bgd_model, fgd_model, 8, cv2.GC_INIT_WITH_RECT)
    fg_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype("uint8")
    # Clean up small speckle holes/islands, then feather the edge so the
    # cutout boundary doesn't alias into noisy ASCII glyphs later.
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    fg_mask = cv2.GaussianBlur(fg_mask, (9, 9), 0)

    rgba = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGBA)
    rgba[:, :, 3] = fg_mask
    return rgba


def prep(src_path: str, out_path: str = "source-prepped.png") -> None:
    if _rembg_remove is not None:
        with open(src_path, "rb") as f:
            input_bytes = f.read()
        cutout_bytes = _rembg_remove(input_bytes)
        cutout = Image.open(BytesIO(cutout_bytes)).convert("RGBA")
    else:
        print("rembg not available, falling back to OpenCV GrabCut")
        bgr = cv2.imread(src_path)
        rgba = _grabcut_cutout(bgr)
        cutout = Image.fromarray(cv2.cvtColor(rgba, cv2.COLOR_BGRA2RGBA))

    # 2. Composite onto pure white.
    white_bg = Image.new("RGBA", cutout.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, cutout).convert("RGB")

    # 3. Denoise, then boost local contrast with CLAHE. A mild bilateral
    # filter first removes the sensor-noise grain that CLAHE would otherwise
    # amplify into speckle, while keeping edges (jawline, glasses) sharp.
    gray = cv2.cvtColor(np.array(composited), cv2.COLOR_RGB2GRAY)
    denoised = cv2.bilateralFilter(gray, d=7, sigmaColor=50, sigmaSpace=50)
    clahe = cv2.createCLAHE(clipLimit=1.8, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)

    Image.fromarray(enhanced).save(out_path)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python scripts/prep_photo.py <source-photo>")
        sys.exit(1)
    prep(sys.argv[1])
