#!/usr/bin/env python3
"""Render data/contributions.json as the classic 53-week x 7-day
contribution calendar: rounded, colored boxes on a GitHub-ish green
ramp. Reveals once with a diagonal, line-after-line slide-down (CSS
keyframes that play on load then freeze), plus a legend and stats
footer.

Usage: python scripts/render_heatmap_svg.py
"""
import json
import os
from datetime import date, datetime, timedelta

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
# none -> brightest (level 5 is a neon top end)

CELL = 12
GAP = 3
LEFT_PAD = 30
TOP_PAD = 20
BOTTOM_PAD = 40
RIGHT_PAD = 10

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")
OUT_PATH = "contrib-heatmap.svg"

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load_weeks(days):
    """Bucket days (sorted, ISO date strings) into columns of 7 (Sun..Sat),
    matching GitHub's calendar layout, padding the first week with None."""
    by_date = {d["date"]: d for d in days}
    if not days:
        return []

    last = datetime.strptime(days[-1]["date"], "%Y-%m-%d").date()
    first = datetime.strptime(days[0]["date"], "%Y-%m-%d").date()

    # Align start to the preceding Sunday.
    start = first - timedelta(days=(first.weekday() + 1) % 7)

    weeks = []
    cursor = start
    week = []
    while cursor <= last:
        key = cursor.isoformat()
        week.append(by_date.get(key))
        if cursor.weekday() == 5:  # Saturday -> close week (week starts Sunday)
            weeks.append(week)
            week = []
        cursor += timedelta(days=1)
    if week:
        while len(week) < 7:
            week.append(None)
        weeks.append(week)

    return weeks[-53:]


def month_boundaries(weeks):
    labels = []
    seen_month = None
    for wi, week in enumerate(weeks):
        for day in week:
            if day is None:
                continue
            d = datetime.strptime(day["date"], "%Y-%m-%d").date()
            if d.month != seen_month:
                seen_month = d.month
                labels.append((wi, MONTH_LABELS[d.month - 1]))
            break
    return labels


def build_svg(payload):
    days = payload["days"]
    stats = payload["stats"]
    weeks = load_weeks(days)
    n_weeks = len(weeks)

    width = LEFT_PAD + n_weeks * (CELL + GAP) + RIGHT_PAD
    height = TOP_PAD + 7 * (CELL + GAP) + BOTTOM_PAD

    cells_svg = []
    idx = 0
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            x = LEFT_PAD + wi * (CELL + GAP)
            y = TOP_PAD + di * (CELL + GAP)
            level = day["level"] if day else 0
            color = PALETTE[min(level, len(PALETTE) - 1)]
            title = f'{day["count"]} contributions on {day["date"]}' if day else ""
            delay = (wi + di) * 0.012
            cells_svg.append(f"""
    <rect class="cell" x="{x}" y="{y - 8}" width="{CELL}" height="{CELL}" rx="2.5"
      fill="{color}" opacity="0" style="animation-delay:{delay:.3f}s">
      <title>{title}</title>
    </rect>""")
            idx += 1

    month_labels_svg = []
    for wi, label in month_boundaries(weeks):
        x = LEFT_PAD + wi * (CELL + GAP)
        month_labels_svg.append(
            f'<text x="{x}" y="{TOP_PAD - 8}" class="month">{label}</text>'
        )

    weekday_labels_svg = []
    for di, label in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        y = TOP_PAD + di * (CELL + GAP) + CELL - 2
        weekday_labels_svg.append(
            f'<text x="0" y="{y}" class="weekday">{label}</text>'
        )

    legend_y = height - 22
    legend_x_start = width - RIGHT_PAD - (len(PALETTE) * (CELL + GAP)) - 60
    legend_cells = []
    for i, color in enumerate(PALETTE):
        x = legend_x_start + 34 + i * (CELL + GAP)
        legend_cells.append(
            f'<rect x="{x}" y="{legend_y - 10}" width="{CELL}" height="{CELL}" rx="2.5" fill="{color}"/>'
        )
    legend_svg = (
        f'<text x="{legend_x_start}" y="{legend_y}" class="legend-label">Less</text>'
        + "".join(legend_cells)
        + f'<text x="{legend_x_start + 34 + len(PALETTE) * (CELL + GAP) + 6}" y="{legend_y}" class="legend-label">More</text>'
    )

    footer_text = (
        f'{stats["total"]:,} public contributions in the last year '
        f'&#183; current streak {stats["current_streak"]}d '
        f'&#183; longest streak {stats["longest_streak"]}d'
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"
     width="{width}" height="{height}">
  <style>
    text {{
      font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
      fill: #8b949e;
    }}
    .month {{ font-size: 11px; }}
    .weekday {{ font-size: 10px; }}
    .legend-label {{ font-size: 10px; }}
    .footer {{ font-size: 12px; fill: #c9d1d9; }}
    .cell {{
      animation-name: slide-in;
      animation-duration: 0.5s;
      animation-timing-function: cubic-bezier(0.25, 0.1, 0.25, 1);
      animation-fill-mode: forwards;
    }}
    @keyframes slide-in {{
      0%   {{ opacity: 0; transform: translate(-6px, -6px); }}
      100% {{ opacity: 1; transform: translate(0, 0); }}
    }}
  </style>
{"".join(month_labels_svg)}
{"".join(weekday_labels_svg)}
{"".join(cells_svg)}
{legend_svg}
  <text x="{LEFT_PAD}" y="{height - 4}" class="footer">{footer_text}</text>
</svg>
"""
    return svg


def main():
    with open(DATA_PATH) as f:
        payload = json.load(f)

    svg = build_svg(payload)
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
