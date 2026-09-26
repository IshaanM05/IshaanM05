#!/usr/bin/env python3
"""Convert a prepped grayscale photo into a self-typing monochrome ASCII SVG.

Downsamples the image to a character grid, maps brightness to a glyph
density ramp, then wraps each row in a clip-path wipe animation staggered
top to bottom (SMIL), so the portrait "types" itself in once and freezes.

Usage: python scripts/make_ascii_svg.py [source-prepped.png] [out.svg]
"""
import sys

from PIL import Image, ImageOps

RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense); fine gradation to avoid a blotchy, binary look
CHAR_W = 6.2
CHAR_H = 11
FONT_SIZE = 12
FILL = "#c9d1d9"
BG = "transparent"
STAGGER = 0.03  # seconds between row starts
ROW_DURATION = 0.35

# The README embeds this SVG at DISPLAY_WIDTH. Sizing the character grid so
# each glyph lands near CHAR_W (its native size) means the portrait reads as
# an actual face at display size instead of blurring into a gray block —
# but that only works if DISPLAY_WIDTH is generous enough to fit real detail
# (a face needs on the order of 80+ columns to resolve eyes/nose/mouth; 100
# cols needs ~620px here, not the 370px a cramped two-column layout implies).
DISPLAY_WIDTH = 490
COLS = round(DISPLAY_WIDTH / CHAR_W)


def image_to_ascii_grid(img: Image.Image, cols: int, rows: int) -> list[str]:
    # LANCZOS averages each output pixel over a wide source neighborhood,
    # so fine sensor/CLAHE grain gets smoothed out instead of aliasing into
    # visual noise the way a nearest/bilinear downsample would.
    img = img.convert("L").resize((cols, rows), Image.LANCZOS)
    # A gentle stretch only clips the extreme 0.3% tails (near-pure white
    # background, deepest shadow) — enough to use the full ramp without
    # crushing every midtone to solid black like an aggressive cutoff does.
    img = ImageOps.autocontrast(img, cutoff=0.3)
    pixels = img.load()
    ramp_len = len(RAMP)
    grid = []
    for y in range(rows):
        line = []
        for x in range(cols):
            brightness = pixels[x, y]  # 0 dark - 255 bright
            idx = int((255 - brightness) / 256 * ramp_len)
            idx = max(0, min(ramp_len - 1, idx))
            line.append(RAMP[idx])
        grid.append("".join(line))
    return grid


def escape(ch: str) -> str:
    return {"&": "&amp;", "<": "&lt;", ">": "&gt;"}.get(ch, ch)


def build_svg(grid: list[str]) -> str:
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    width = cols * CHAR_W
    height = rows * CHAR_H
    rows_svg = []

    for i, row in enumerate(grid):
        y = (i + 1) * CHAR_H - 2
        start = i * STAGGER
        end = start + ROW_DURATION
        row_text = "".join(escape(c) for c in row)
        clip_id = f"clip{i}"

        rows_svg.append(f"""
    <clipPath id="{clip_id}">
      <rect x="0" y="{y - FONT_SIZE}" width="0" height="{FONT_SIZE + 4}">
        <animate attributeName="width" from="0" to="{width}"
          begin="{start:.3f}s" dur="{ROW_DURATION:.3f}s" fill="freeze"
          calcMode="spline" keySplines="0.25 0.1 0.25 1" />
      </rect>
    </clipPath>""")

    text_lines = []
    for i, row in enumerate(grid):
        y = (i + 1) * CHAR_H - 2
        clip_id = f"clip{i}"
        row_text = "".join(escape(c) for c in row)
        text_lines.append(
            f'    <text x="0" y="{y}" clip-path="url(#{clip_id})">{row_text}</text>'
        )

    # cursor block that rides the wipe edge of each row, staggered same as rows
    cursors = []
    for i in range(rows):
        y = (i + 1) * CHAR_H - 2
        start = i * STAGGER
        end = start + ROW_DURATION
        cursors.append(f"""
    <rect class="cursor" x="0" y="{y - FONT_SIZE + 1}" width="{CHAR_W:.1f}" height="{FONT_SIZE}"
      opacity="0">
      <animate attributeName="x" from="0" to="{width - CHAR_W:.1f}"
        begin="{start:.3f}s" dur="{ROW_DURATION:.3f}s" fill="freeze"
        calcMode="spline" keySplines="0.25 0.1 0.25 1" />
      <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.01;0.9;1"
        begin="{start:.3f}s" dur="{ROW_DURATION:.3f}s" fill="freeze" />
    </rect>""")

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.1f} {height:.1f}"
     width="{width:.0f}" height="{height:.0f}">
  <defs>{"".join(rows_svg)}
  </defs>
  <style>
    text {{
      font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
      font-size: {FONT_SIZE}px;
      fill: {FILL};
      white-space: pre;
    }}
    .cursor {{ fill: {FILL}; }}
    svg {{ background: {BG}; }}
  </style>
{chr(10).join(text_lines)}
{"".join(cursors)}
</svg>
"""
    return svg


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    out = sys.argv[2] if len(sys.argv) > 2 else "ishaan-ascii.svg"

    img = Image.open(src)
    aspect = img.height / img.width
    rows = round(COLS * aspect * (CHAR_W / CHAR_H))
    grid = image_to_ascii_grid(img, COLS, rows)
    svg = build_svg(grid)

    with open(out, "w") as f:
        f.write(svg)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
