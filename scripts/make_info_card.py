#!/usr/bin/env python3
"""Hand-author a neofetch-style info card SVG: a title bar, then colored
key/value rows that fade + slide in on a short stagger.

Set STATIC=1 to emit a frozen (fully-visible) frame for local Quick Look
previews instead of the animated version.

Usage: python scripts/make_info_card.py
"""
import os

WIDTH = 490
LINE_H = 30
PAD_TOP = 70
PAD_X = 24
TITLE = "ishaan@github"
STATIC = os.environ.get("STATIC") == "1"

ACCENT = "#39d353"
KEY_COLOR = "#39d353"
VAL_COLOR = "#c9d1d9"
DIM_COLOR = "#8b949e"
BG = "#0d1117"
BORDER = "#30363d"

ROWS = [
    ("Now", "Perception Lead, IITB Racing"),
    ("Prev", "Lead Intern, MapIoT AI"),
    ("Stack", "C++ · Python · ROS 2 · PyTorch"),
    ("Highlights", "FSP Champion '26 · FSAI 4th '25"),
]

STAGGER = 0.12
FADE_DUR = 0.5
START_DELAY = 0.4  # let the title bar draw first


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg() -> str:
    height = PAD_TOP + LINE_H * len(ROWS) + 24

    row_svgs = []
    for i, (key, val) in enumerate(ROWS):
        y = PAD_TOP + i * LINE_H
        start = START_DELAY + i * STAGGER
        if STATIC:
            transform_attr = ""
            opacity_attr = 'opacity="1"'
            anim = ""
        else:
            transform_attr = 'transform="translate(-16,0)"'
            opacity_attr = 'opacity="0"'
            anim = f"""
        <animate attributeName="opacity" from="0" to="1"
          begin="{start:.2f}s" dur="{FADE_DUR:.2f}s" fill="freeze" />
        <animateTransform attributeName="transform" type="translate"
          from="-16,0" to="0,0"
          begin="{start:.2f}s" dur="{FADE_DUR:.2f}s" fill="freeze"
          calcMode="spline" keySplines="0.25 0.1 0.25 1" />"""
        row_svgs.append(f"""
    <g {opacity_attr} {transform_attr}>{anim}
      <text x="{PAD_X}" y="{y}" class="key">{esc(key)}</text>
      <text x="{PAD_X + 108}" y="{y}" class="val">{esc(val)}</text>
    </g>""")

    title_anim = "" if STATIC else f"""
      <animate attributeName="opacity" from="0" to="1" begin="0.05s" dur="0.3s" fill="freeze" />"""
    title_opacity = "1" if STATIC else "0"

    dots = "".join(
        f'<circle cx="{18 + i * 16}" cy="20" r="5" fill="{c}"/>'
        for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"])
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}"
     width="{WIDTH}" height="{height}">
  <style>
    text {{
      font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
      font-size: 14px;
    }}
    .key {{ fill: {KEY_COLOR}; font-weight: bold; }}
    .val {{ fill: {VAL_COLOR}; }}
    .title {{ fill: {DIM_COLOR}; font-size: 13px; }}
  </style>
  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="8"
    fill="{BG}" stroke="{BORDER}" />
  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="36" rx="8" fill="#161b22" />
  <rect x="0.5" y="28.5" width="{WIDTH - 1}" height="8" fill="#161b22" />
  {dots}
  <g opacity="{title_opacity}">{title_anim}
    <text x="{WIDTH / 2}" y="24" text-anchor="middle" class="title">{esc(TITLE)}</text>
  </g>
{"".join(row_svgs)}
</svg>
"""
    return svg


def main():
    svg = build_svg()
    out = "info-card.svg"
    with open(out, "w") as f:
        f.write(svg)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
