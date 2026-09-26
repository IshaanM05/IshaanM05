#!/usr/bin/env python3
"""Fetch a GitHub user's contribution calendar by scraping the same HTML
fragment the profile page itself uses: https://github.com/users/<username>/contributions

By default this is a public, unauthenticated request, so it only sees
public-repo activity — GitHub's own graph shows a higher total to the
profile owner when logged in, because it privately counts contributions
to private repos too. Set GH_SESSION_COOKIE (a live GitHub web session
cookie, e.g. from the `user_session` cookie after logging in as the
profile owner) to authenticate as the owner and match that fuller count.
This is a session cookie, not an API token — treat it as sensitive, expect
it to expire periodically, and know that the resulting total includes
private-repo contribution counts that a public visitor cannot see.

Writes data/contributions.json with raw days plus derived stats
(current streak, longest streak, best day, monthly totals).

Usage: python scripts/fetch_contributions.py [username]
"""
import json
import os
import sys
from collections import defaultdict
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup

USERNAME = sys.argv[1] if len(sys.argv) > 1 else "IshaanM05"
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")


def _authenticated_headers():
    cookie = os.environ.get("GH_SESSION_COOKIE")
    if not cookie:
        return {"User-Agent": "Mozilla/5.0"}, False
    return {"User-Agent": "Mozilla/5.0", "Cookie": f"user_session={cookie}; logged_in=yes"}, True


def fetch_days():
    headers, tried_auth = _authenticated_headers()
    resp = requests.get(URL, headers=headers, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # GitHub sets its own logged_in=yes/no response cookie reflecting whether
    # the session actually authenticated — the fragment's HTML looks the same
    # either way (it's a public-viewable page), so that cookie is the only
    # reliable signal an expired/invalid session cookie was silently ignored.
    used_session_cookie = False
    if tried_auth:
        if resp.cookies.get("logged_in") == "yes":
            used_session_cookie = True
        else:
            print("GH_SESSION_COOKIE set but didn't authenticate (expired?) — falling back to public data", file=sys.stderr)
            resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

    def count_from_tooltip(cell_id):
        if not cell_id:
            return 0
        tip = soup.find("tool-tip", attrs={"for": cell_id})
        if not tip:
            return 0
        text = tip.get_text(strip=True)
        if text.lower().startswith("no contributions"):
            return 0
        digits = "".join(c for c in text.split(" ")[0] if c.isdigit())
        return int(digits) if digits else 0

    days = []
    cells = soup.select("td.ContributionCalendar-day")
    if cells:
        for cell in cells:
            d = cell.get("data-date")
            level = cell.get("data-level")
            count_attr = cell.get("data-count")
            if d is None:
                continue
            if count_attr is not None:
                count = int(count_attr)
            else:
                count = count_from_tooltip(cell.get("id"))
            days.append({
                "date": d,
                "count": count,
                "level": int(level) if level is not None else 0,
            })
    else:
        # fallback for the newer rect-based markup
        for rect in soup.select("rect.ContributionCalendar-day, rect[data-date]"):
            d = rect.get("data-date")
            level = rect.get("data-level")
            if d is None:
                continue
            tooltip_id = rect.get("id")
            count = 0
            if tooltip_id:
                tip = soup.find("tool-tip", attrs={"for": tooltip_id})
                if tip:
                    text = tip.get_text(strip=True)
                    digits = "".join(c for c in text.split(" ")[0] if c.isdigit())
                    count = int(digits) if digits else 0
            days.append({
                "date": d,
                "count": count,
                "level": int(level) if level is not None else 0,
            })

    days.sort(key=lambda x: x["date"])
    return days, used_session_cookie


def derive_stats(days):
    total = sum(d["count"] for d in days)

    current_streak = 0
    longest_streak = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    best_day = max(days, key=lambda x: x["count"], default=None)

    monthly = defaultdict(int)
    for d in days:
        month_key = d["date"][:7]  # YYYY-MM
        monthly[month_key] += d["count"]

    return {
        "total": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "monthly": dict(sorted(monthly.items())),
    }


def main():
    days, used_session_cookie = fetch_days()
    stats = derive_stats(days)
    stats["includes_private_contributions"] = used_session_cookie

    payload = {
        "username": USERNAME,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "days": days,
        "stats": stats,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(payload, f, indent=2)
    scope = "private+public" if used_session_cookie else "public only"
    print(f"wrote {OUT_PATH} ({len(days)} days, {stats['total']} contributions, {scope})")


if __name__ == "__main__":
    main()
