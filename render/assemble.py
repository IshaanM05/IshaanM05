#!/usr/bin/env python3
"""Assemble the PNG frames captured by capture.js into the final looping
animated WebP used in the README.

Usage: python3 render/assemble.py
"""
import glob
import os

from PIL import Image

HERE = os.path.dirname(__file__)
FRAMES_GLOB = os.path.join(HERE, "frames", "frame_*.png")
OUT_PATH = os.path.join(HERE, "..", "physical-ai.webp")
TOTAL_DURATION_MS = 5000


def main():
    frames = sorted(glob.glob(FRAMES_GLOB))
    if not frames:
        raise SystemExit("no frames found — run `node capture.js` first")

    imgs = [Image.open(f).convert("RGB") for f in frames]
    per_frame = TOTAL_DURATION_MS / len(imgs)

    imgs[0].save(
        OUT_PATH,
        save_all=True,
        append_images=imgs[1:],
        duration=per_frame,
        loop=0,
        quality=85,
        method=6,
    )
    print(f"wrote {OUT_PATH} ({len(imgs)} frames, {TOTAL_DURATION_MS}ms loop)")


if __name__ == "__main__":
    main()
