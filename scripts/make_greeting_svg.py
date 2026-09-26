#!/usr/bin/env python3
"""Generate a self-typing greeting header SVG. Same left-to-right clip-path
wipe technique as the ASCII portrait, just applied to real text — a
terminal-style "Hi, I'm ___" that types itself in once and freezes (no
looping, no third-party typing-SVG service).

Usage: python scripts/make_greeting_svg.py
"""

WIDTH = 980
HEIGHT = 110
LINE1 = "Hi, I'm Ishaan Mondal"
LINE2 = "Perception Lead @ IITB Racing Driverless · ME + AI/DS minor, IIT Bombay"

FONT_SIZE_1 = 40
FONT_SIZE_2 = 18
CHAR_W_1 = 24.5   # approx monospace advance at FONT_SIZE_1
CHAR_W_2 = 11.0   # approx monospace advance at FONT_SIZE_2

FILL_1 = "#39d353"
FILL_2 = "#8b949e"

LINE1_DUR = 1.4
LINE2_DELAY = LINE1_DUR + 0.15
LINE2_DUR = 0.6


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg() -> str:
    line1_width = len(LINE1) * CHAR_W_1
    cursor_w = CHAR_W_1 * 0.55

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}"
     width="{WIDTH}" height="{HEIGHT}">
  <defs>
    <clipPath id="line1-clip">
      <rect x="0" y="0" width="0" height="{HEIGHT}">
        <animate attributeName="width" from="0" to="{line1_width:.1f}"
          begin="0.2s" dur="{LINE1_DUR:.2f}s" fill="freeze"
          calcMode="spline" keySplines="0.4 0 0.2 1" />
      </rect>
    </clipPath>
  </defs>
  <style>
    text {{
      font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
      white-space: pre;
    }}
    .line1 {{ font-size: {FONT_SIZE_1}px; font-weight: bold; fill: {FILL_1}; }}
    .line2 {{ font-size: {FONT_SIZE_2}px; fill: {FILL_2}; }}
  </style>

  <text x="0" y="52" class="line1" clip-path="url(#line1-clip)">{esc(LINE1)}</text>

  <rect class="cursor" x="0" y="18" width="{cursor_w:.1f}" height="{FONT_SIZE_1}" fill="{FILL_1}" opacity="0">
    <animate attributeName="x" from="0" to="{line1_width:.1f}"
      begin="0.2s" dur="{LINE1_DUR:.2f}s" fill="freeze"
      calcMode="spline" keySplines="0.4 0 0.2 1" />
    <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.02;0.92;1"
      begin="0.2s" dur="{LINE1_DUR:.2f}s" fill="freeze" />
  </rect>

  <text x="2" y="82" class="line2" opacity="0">
    {esc(LINE2)}
    <animate attributeName="opacity" from="0" to="1"
      begin="{LINE2_DELAY:.2f}s" dur="{LINE2_DUR:.2f}s" fill="freeze" />
  </text>
</svg>
"""
    return svg


def main():
    svg = build_svg()
    out = "greeting.svg"
    with open(out, "w") as f:
        f.write(svg)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
