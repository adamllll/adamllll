#!/usr/bin/env python3
"""Render the animated profile identity from real GitHub contributions.

The output is a self-contained, GitHub-safe SVG. Contribution data controls
the 52 bands inside the ADAM word mark and the compact timeline below it.
"""

from __future__ import annotations

import html
import json
import math
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


USERNAME = os.environ.get("PROFILE_LOGIN", "adamllll")
OUTPUT = Path(os.environ.get("PROFILE_ACTIVITY_OUTPUT", "assets/profile-activity.svg"))
GRAPHQL_URL = "https://api.github.com/graphql"
PUBLIC_CALENDAR_URL = f"https://github.com/users/{USERNAME}/contributions"

QUERY = """
query ProfileActivity($login: String!) {
  viewer {
    login
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
  user(login: $login) {
    login
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


@dataclass(frozen=True)
class ActivityData:
    total: int
    weekly: list[int]
    active_days: int
    last_7: int
    last_30: int
    daily_peak: int
    source: str


def request(url: str, *, token: str | None = None, payload: dict | None = None) -> str:
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{USERNAME}-profile-activity",
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8")


def graphql_calendar(token: str) -> tuple[int, list[dict[str, int | str]], str]:
    raw = request(
        GRAPHQL_URL,
        token=token,
        payload={"query": QUERY, "variables": {"login": USERNAME}},
    )
    body = json.loads(raw)
    if body.get("errors"):
        raise RuntimeError(body["errors"][0].get("message", "GraphQL query failed"))

    viewer = body.get("data", {}).get("viewer") or {}
    profile = body.get("data", {}).get("user")
    if not profile:
        raise RuntimeError(f"GitHub user {USERNAME!r} was not found")
    if str(viewer.get("login", "")).lower() == USERNAME.lower():
        profile = viewer
        source = "github-graphql-viewer"
    else:
        source = "github-graphql-public"

    calendar = profile["contributionsCollection"]["contributionCalendar"]
    days = [
        {"date": day["date"], "count": int(day["contributionCount"])}
        for week in calendar["weeks"]
        for day in week["contributionDays"]
    ]
    return int(calendar["totalContributions"]), days, source


def public_calendar() -> tuple[int, list[dict[str, int | str]]]:
    """Parse the public contribution calendar rendered by GitHub."""
    raw = request(PUBLIC_CALENDAR_URL)
    total_match = re.search(r"([\d,]+)\s+contributions?\s+in\s+the\s+last\s+year", raw, re.I)
    if not total_match:
        raise RuntimeError("Could not find the yearly contribution total in GitHub HTML")
    total = int(total_match.group(1).replace(",", ""))

    days_by_date: dict[str, int] = {}
    cell_pattern = re.compile(
        r"<td\b(?P<attrs>[^>]*)>\s*</td>\s*<tool-tip\b[^>]*>(?P<tip>.*?)</tool-tip>",
        re.I | re.S,
    )
    for match in cell_pattern.finditer(raw):
        attrs = match.group("attrs")
        if "ContributionCalendar-day" not in attrs:
            continue
        date_match = re.search(r'data-date="([^"]+)"', attrs)
        if not date_match:
            continue
        tip = html.unescape(re.sub(r"<[^>]+>", "", match.group("tip")))
        count_match = re.search(r"([\d,]+)\s+contributions?", tip, re.I)
        days_by_date[date_match.group(1)] = int(count_match.group(1).replace(",", "")) if count_match else 0

    if len(days_by_date) < 300:
        raise RuntimeError(f"Only parsed {len(days_by_date)} contribution days from GitHub HTML")
    days = [{"date": day, "count": count} for day, count in sorted(days_by_date.items())]
    return total, days


def load_calendar() -> tuple[int, list[dict[str, int | str]], str]:
    token = (
        os.environ.get("PROFILE_STATS_TOKEN")
        or os.environ.get("GH_TOKEN")
        or os.environ.get("GITHUB_TOKEN")
    )
    if token:
        try:
            return graphql_calendar(token)
        except (RuntimeError, urllib.error.URLError, json.JSONDecodeError) as exc:
            print(f"warning: GraphQL unavailable ({exc}); falling back to public calendar", file=sys.stderr)
    total, days = public_calendar()
    return total, days, "github-public-calendar"


def weekly_activity(days: list[dict[str, int | str]]) -> tuple[list[int], list[int]]:
    calendar = {date.fromisoformat(str(item["date"])): int(item["count"]) for item in days}
    latest = max(calendar)
    rolling_start = latest - timedelta(days=363)
    daily = [calendar.get(rolling_start + timedelta(days=index), 0) for index in range(364)]

    days_since_sunday = (latest.weekday() + 1) % 7
    current_week_start = latest - timedelta(days=days_since_sunday)
    first_week_start = current_week_start - timedelta(weeks=51)
    weekly = [
        sum(calendar.get(first_week_start + timedelta(days=week * 7 + day), 0) for day in range(7))
        for week in range(52)
    ]
    return daily, weekly


def activity_strength(value: int, peak: int) -> float:
    if value <= 0:
        return 0.0
    return min(1.0, math.sqrt(value / max(1, peak)))


def activity_from_days(
    total: int,
    days: list[dict[str, int | str]],
    source: str,
) -> ActivityData:
    daily, weekly = weekly_activity(days)
    return ActivityData(
        total=total,
        weekly=weekly,
        active_days=sum(count > 0 for count in daily),
        last_7=sum(daily[-7:]),
        last_30=sum(daily[-30:]),
        daily_peak=max(daily, default=0),
        source=source,
    )


def activity_from_snapshot(path: Path) -> ActivityData:
    payload = json.loads(path.read_text(encoding="utf-8"))
    weekly = [int(value) for value in payload["weekly"]]
    if len(weekly) != 52:
        raise ValueError(f"Expected 52 weekly values in {path}, found {len(weekly)}")
    total = int(payload["total"])
    if sum(weekly) != total:
        raise ValueError(f"Weekly values in {path} sum to {sum(weekly)}, expected {total}")
    return ActivityData(
        total=total,
        weekly=weekly,
        active_days=int(payload["active_days"]),
        last_7=int(payload["last_7"]),
        last_30=int(payload["last_30"]),
        daily_peak=int(payload["peak"]),
        source="github-activity-snapshot",
    )


def load_activity() -> ActivityData:
    snapshot = os.environ.get("PROFILE_ACTIVITY_SNAPSHOT")
    if snapshot:
        return activity_from_snapshot(Path(snapshot))
    total, days, source = load_calendar()
    if not days:
        raise RuntimeError("GitHub returned an empty contribution calendar")
    return activity_from_days(total, days, source)


def render(activity: ActivityData) -> str:
    total = activity.total
    weekly = activity.weekly
    weekly_peak = max(weekly, default=1)
    active_days = activity.active_days
    last_7 = activity.last_7
    scan_duration = max(4.8, 8.2 - min(last_7, 18) * 0.16)

    letter_bars: list[str] = []
    timeline_bars: list[str] = []
    recent_overlays: list[str] = []
    bar_width = 1480 / len(weekly)

    for index, value in enumerate(weekly):
        strength = activity_strength(value, weekly_peak)
        opacity = 0.18 if value == 0 else 0.38 + strength * 0.62
        x = 60 + index * bar_width
        delay = index * 0.032
        letter_bars.append(
            f'<rect class="activity-band" x="{x:.1f}" y="76" width="{bar_width + 1:.1f}" '
            f'height="306" fill="#F7F8FC" opacity="{opacity:.2f}" style="animation-delay:{delay:.2f}s"/>'
        )

        tick_height = 4 if value == 0 else 5 + round(18 * value / max(1, weekly_peak))
        tick_y = 430 - tick_height
        timeline_bars.append(
            f'<rect class="timeline-band" x="{x:.1f}" y="{tick_y}" width="{max(3, bar_width - 3):.1f}" '
            f'height="{tick_height}" fill="#F7F8FC" opacity="{max(.28, opacity):.2f}" '
            f'style="animation-delay:{delay:.2f}s"/>'
        )

        if index >= len(weekly) - 4 and value > 0:
            recent_overlays.append(
                f'<rect class="recent-band" x="{x:.1f}" y="76" width="{bar_width + 1:.1f}" '
                f'height="306" fill="#F7F8FC" opacity="0"/>'
            )

    letter_svg = "\n    ".join(letter_bars)
    timeline_svg = "\n  ".join(timeline_bars)
    recent_svg = "\n    ".join(recent_overlays)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="520" viewBox="0 0 1600 520" role="img" aria-labelledby="title desc">
  <title id="title">ADAM contribution identity</title>
  <desc id="desc">A living GitHub profile generated from real activity. The rolling year contains {total} contributions across {active_days} active days, with {last_7} contributions in the last seven days.</desc>
  <metadata>source=github-contribution-calendar; user={USERNAME}; window=52-sunday-weeks</metadata>
  <defs>
    <style>
      .activity-band, .timeline-band {{
        transform-box: fill-box;
        transform-origin: center bottom;
        animation: band-rise .85s cubic-bezier(.16,1,.3,1) both;
      }}
      .activity-scan {{ animation: scan {scan_duration:.2f}s cubic-bezier(.16,1,.3,1) infinite; }}
      .recent-band {{ animation: recent-pulse 2.8s ease-in-out infinite; }}
      @keyframes band-rise {{
        from {{ transform: scaleY(.03); opacity: 0; }}
        to {{ transform: scaleY(1); }}
      }}
      @keyframes scan {{
        0% {{ transform: translateX(-180px); opacity: 0; }}
        12% {{ opacity: .72; }}
        72% {{ opacity: .72; }}
        88%, 100% {{ transform: translateX(1660px); opacity: 0; }}
      }}
      @keyframes recent-pulse {{
        0%, 100% {{ opacity: 0; }}
        50% {{ opacity: .18; }}
      }}
      @media (prefers-reduced-motion: reduce) {{
        .activity-band, .timeline-band, .activity-scan, .recent-band {{ animation: none; }}
      }}
    </style>
    <clipPath id="adam-word">
      <text x="52" y="366" font-family="Arial Black, Arial, Helvetica, sans-serif" font-size="380" font-weight="900" letter-spacing="-22">ADAM</text>
    </clipPath>
  </defs>

  <rect width="1600" height="520" fill="#3156E6"/>

  <g font-family="Arial, Helvetica, sans-serif">
    <text x="68" y="54" fill="#F7F8FC" font-size="16" font-weight="800" letter-spacing="2">52 WEEKS SHAPE THE NAME</text>
    <text x="1530" y="54" fill="#F7F8FC" font-size="16" font-weight="800" text-anchor="end">{total} CONTRIBUTIONS</text>
  </g>

  <g clip-path="url(#adam-word)">
    {letter_svg}
    {recent_svg}
    <rect class="activity-scan" x="-180" y="74" width="90" height="312" fill="#101218" opacity=".72"/>
  </g>
  <text x="52" y="366" fill="none" stroke="#101218" stroke-width="3" stroke-opacity=".34" font-family="Arial Black, Arial, Helvetica, sans-serif" font-size="380" font-weight="900" letter-spacing="-22">ADAM</text>

  <g>
    {timeline_svg}
  </g>
  <line x1="60" y1="434" x2="1540" y2="434" stroke="#F7F8FC" stroke-opacity=".32"/>

  <g font-family="Arial, Helvetica, sans-serif">
    <text x="68" y="475" fill="#F7F8FC" font-size="18" font-weight="700">Each vertical band is one week. Brighter bands mean more contributions.</text>
    <rect x="1160" y="447" width="372" height="54" fill="#F7F8FC"/>
    <text x="1192" y="481" fill="#101218" font-size="17" font-weight="800" letter-spacing=".8">OPEN PERSONAL SITE  ↗</text>
  </g>
</svg>
'''


def main() -> None:
    activity = load_activity()
    svg = render(activity)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")

    print(
        json.dumps(
            {
                "user": USERNAME,
                "source": activity.source,
                "total": activity.total,
                "active_days": activity.active_days,
                "last_30": activity.last_30,
                "last_7": activity.last_7,
                "peak": activity.daily_peak,
                "weeks": len(activity.weekly),
                "output": str(OUTPUT),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
