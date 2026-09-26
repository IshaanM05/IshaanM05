#!/usr/bin/env python3
"""Generate a looping "physical AI" header animation: a top-down
autonomous vehicle with a rotating LiDAR sweep detecting objects around
it. An original self-contained SVG (matching the rest of this profile's
no-third-party-GIF approach) rather than a stock robotics GIF, and one
that's literally what a perception pipeline does.

Usage: python scripts/make_physical_ai_svg.py
"""
import math

WIDTH = 700
HEIGHT = 220
CX, CY = 350, 120  # sensor origin, centered on the car

ACCENT = "#39d353"
DIM = "#2ea043"
GRID = "#21262d"
BODY_FILL = "#161b22"
BODY_STROKE = "#39d353"

SWEEP_DURATION = 4.0  # seconds per full 360° rotation, loops forever
SWEEP_RANGE = 95      # sweep beam length (px)

# Objects detected around the car: (angle_deg, distance, size)
OBJECTS = [
    (20, 80, 5), (65, 60, 4), (110, 85, 6), (150, 70, 4),
    (200, 75, 5), (245, 65, 4), (290, 90, 6), (335, 70, 4),
]


def polar(cx, cy, angle_deg, r):
    rad = math.radians(angle_deg - 90)  # 0deg = up
    return cx + r * math.cos(rad), cy + r * math.sin(rad)


def build_grid():
    lines = []
    for x in range(0, WIDTH + 1, 35):
        lines.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{HEIGHT}" stroke="{GRID}" stroke-width="1"/>')
    for y in range(0, HEIGHT + 1, 35):
        lines.append(f'<line x1="0" y1="{y}" x2="{WIDTH}" y2="{y}" stroke="{GRID}" stroke-width="1"/>')
    return "".join(lines)


def build_range_rings():
    rings = []
    for r in (40, 65, 90):
        rings.append(
            f'<circle cx="{CX}" cy="{CY}" r="{r}" fill="none" stroke="{DIM}" '
            f'stroke-width="1" stroke-dasharray="3 4" opacity="0.35"/>'
        )
    return "".join(rings)


def build_car():
    # Simple top-down car: rounded body + four wheels + sensor mast dot.
    return f"""
  <g>
    <rect x="{CX - 26}" y="{CY - 16}" width="52" height="32" rx="8"
      fill="{BODY_FILL}" stroke="{BODY_STROKE}" stroke-width="2"/>
    <rect x="{CX - 20}" y="{CY - 20}" width="14" height="8" rx="2" fill="{BODY_STROKE}" opacity="0.85"/>
    <circle cx="{CX}" cy="{CY}" r="3.5" fill="{ACCENT}"/>
    <circle cx="{CX - 20}" cy="{CY - 18}" r="4" fill="{BODY_FILL}" stroke="{ACCENT}" stroke-width="1.5"/>
    <circle cx="{CX - 20}" cy="{CY + 18}" r="4" fill="{BODY_FILL}" stroke="{ACCENT}" stroke-width="1.5"/>
    <circle cx="{CX + 20}" cy="{CY - 18}" r="4" fill="{BODY_FILL}" stroke="{ACCENT}" stroke-width="1.5"/>
    <circle cx="{CX + 20}" cy="{CY + 18}" r="4" fill="{BODY_FILL}" stroke="{ACCENT}" stroke-width="1.5"/>
  </g>"""


def build_sweep():
    # A thin wedge rotating a full 360 degrees, looping forever, with a
    # fading trail behind it (three staggered copies at decreasing opacity).
    trails = []
    for i, opacity in enumerate([0.35, 0.2, 0.1]):
        offset_deg = (i + 1) * 10
        trails.append(f"""
    <path d="M {CX} {CY} L {CX} {CY - SWEEP_RANGE} A {SWEEP_RANGE} {SWEEP_RANGE} 0 0 0 {CX + SWEEP_RANGE * math.sin(math.radians(offset_deg)):.1f} {CY - SWEEP_RANGE * math.cos(math.radians(offset_deg)):.1f} Z"
      fill="{ACCENT}" opacity="{opacity}">
      <animateTransform attributeName="transform" type="rotate"
        from="0 {CX} {CY}" to="360 {CX} {CY}"
        dur="{SWEEP_DURATION}s" repeatCount="indefinite" />
    </path>""")

    main = f"""
    <path d="M {CX} {CY} L {CX} {CY - SWEEP_RANGE} A {SWEEP_RANGE} {SWEEP_RANGE} 0 0 0 {CX + SWEEP_RANGE * math.sin(math.radians(8)):.1f} {CY - SWEEP_RANGE * math.cos(math.radians(8)):.1f} Z"
      fill="{ACCENT}" opacity="0.55">
      <animateTransform attributeName="transform" type="rotate"
        from="0 {CX} {CY}" to="360 {CX} {CY}"
        dur="{SWEEP_DURATION}s" repeatCount="indefinite" />
    </path>"""

    return "".join(trails) + main


def build_objects():
    dots = []
    for angle, dist, size in OBJECTS:
        x, y = polar(CX, CY, angle, dist)
        blip_start = (angle / 360.0) * SWEEP_DURATION
        # keyTimes fractions for a quick opacity blip timed to when the
        # sweep passes this angle, looping every SWEEP_DURATION seconds.
        t0 = blip_start / SWEEP_DURATION
        t1 = min(t0 + 0.03, 0.999)
        t2 = min(t0 + 0.18, 1.0)
        key_times = f"0;{t0:.3f};{t1:.3f};{t2:.3f};1"
        values = "0.15;0.15;1;0.15;0.15"
        dots.append(f"""
    <circle cx="{x:.1f}" cy="{y:.1f}" r="{size}" fill="{ACCENT}" opacity="0.15">
      <animate attributeName="opacity" values="{values}" keyTimes="{key_times}"
        dur="{SWEEP_DURATION}s" repeatCount="indefinite" />
    </circle>""")
    return "".join(dots)


def build_svg() -> str:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}"
     width="{WIDTH}" height="{HEIGHT}">
  <defs>
    <clipPath id="frame-clip">
      <rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" rx="10"/>
    </clipPath>
  </defs>
  <style>
    text {{
      font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
      fill: {DIM};
      font-size: 12px;
    }}
  </style>
  <g clip-path="url(#frame-clip)">
    <rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="#0d1117"/>
    {build_grid()}
    {build_range_rings()}
    {build_sweep()}
    {build_objects()}
    {build_car()}
  </g>
  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="10" fill="none" stroke="#30363d"/>
  <text x="14" y="{HEIGHT - 14}">LIDAR_PERCEPTION.exe · physical AI</text>
</svg>
"""
    return svg


def main():
    svg = build_svg()
    out = "physical-ai.svg"
    with open(out, "w") as f:
        f.write(svg)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
