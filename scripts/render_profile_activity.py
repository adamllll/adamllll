#!/usr/bin/env python3
"""Render a vaporwave pixel city from real GitHub contributions.

The output is a self-contained, GitHub-safe SVG. Each of the 52 towers maps
to one week; tower height and lit windows increase with contribution activity.
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


BASE_Y = 418


def activity_palette(value: int) -> tuple[str, str]:
    if value == 0:
        return "#342b43", "#0d1117"
    if value <= 5:
        return "#06ffa5", "#0b151b"
    if value <= 14:
        return "#00d8ff", "#0c1420"
    if value <= 24:
        return "#c774e8", "#151225"
    return "#ff6ad5", "#191221"


def tower_geometry(index: int, value: int, peak: int) -> tuple[int, int, int, str, str]:
    x = 70 + index * 28
    amount = activity_strength(value, peak)
    height = 14 if value == 0 else 42 + round(218 * amount)
    edge, body = activity_palette(value)
    return x, BASE_Y - height, height, edge, body


def render_reflection(index: int, value: int, peak: int) -> str:
    x, y, height, edge, body = tower_geometry(index, value, peak)
    cap = 7 if height >= 50 else 0
    return (
        f'<g transform="translate(0 {BASE_Y * 2}) scale(1 -1)">'
        f'<rect x="{x}" y="{y + cap}" width="21" height="{height - cap}" '
        f'fill="{body}" stroke="{edge}" stroke-width="2"/>'
        + (
            f'<rect x="{x + 4}" y="{y}" width="13" height="{cap + 2}" '
            f'fill="{body}" stroke="{edge}" stroke-width="2"/>'
            if cap
            else ""
        )
        + "</g>"
    )


def render_tower(index: int, value: int, peak: int, *, latest: bool) -> str:
    x, y, height, edge, body = tower_geometry(index, value, peak)
    amount = activity_strength(value, peak)
    cap = 7 if height >= 50 else 0
    delay = index * 0.019
    contribution_label = "contribution" if value == 1 else "contributions"
    parts = [
        f'<g class="tower" style="animation-delay:{delay:.3f}s">',
        f'  <title>Week {index + 1}: {value} {contribution_label}</title>',
        f'  <rect x="{x}" y="{y + cap}" width="21" height="{height - cap}" '
        f'fill="{body}" stroke="{edge}" stroke-width="2" '
        f'opacity="{0.42 if value == 0 else 0.98}"/>',
    ]
    if cap:
        parts.append(
            f'  <rect x="{x + 4}" y="{y}" width="13" height="{cap + 2}" '
            f'fill="{body}" stroke="{edge}" stroke-width="2"/>'
        )

    if value > 0:
        rows = max(1, (height - 21) // 12)
        slots = rows * 2
        lit_count = max(1, round(amount * slots))
        order = sorted(range(slots), key=lambda slot: (slot * 19 + index * 11) % max(1, slots))
        lit_slots = set(order[:lit_count])
        colors = ("#00d8ff", "#ff6ad5", "#fffd82", "#06ffa5")
        for slot in range(slots):
            row, column = divmod(slot, 2)
            window_y = BASE_Y - 13 - row * 12
            if window_y <= y + 9:
                continue
            window_x = x + 4 + column * 9
            if slot in lit_slots:
                color = colors[(slot + index) % len(colors)]
                class_attr = ' class="current-window"' if latest else ""
                parts.append(
                    f'  <rect{class_attr} x="{window_x}" y="{window_y}" '
                    f'width="4" height="6" fill="{color}"/>'
                )
            else:
                parts.append(
                    f'  <rect x="{window_x}" y="{window_y}" width="4" height="6" '
                    'fill="#332344" opacity=".55"/>'
                )

    if value >= 15:
        parts.extend(
            [
                f'  <rect x="{x + 10}" y="{y - 11}" width="2" height="11" fill="{edge}"/>',
                f'  <rect class="beacon" x="{x + 7}" y="{y - 16}" '
                'width="8" height="7" fill="#fffd82"/>',
            ]
        )

    if latest and value > 0:
        parts.append(
            f'  <path class="now-pulse" d="M{x - 5} {y - 7}h31v{height + 14}h-31z" '
            'fill="none" stroke="#06ffa5" stroke-width="2"/>'
        )
    parts.append("</g>")
    return "\n".join(parts)


def timeline_ticks(reference: date | None = None) -> list[tuple[int, str, str]]:
    latest = reference or date.today()
    days_since_sunday = (latest.weekday() + 1) % 7
    current_week_start = latest - timedelta(days=days_since_sunday)
    first_week_start = current_week_start - timedelta(weeks=51)

    ticks: list[tuple[int, str, str]] = []
    previous_year: int | None = None
    for index in (0, 13, 26, 39):
        week_start = first_week_start + timedelta(weeks=index)
        label = week_start.strftime("%b").upper()
        if previous_year is None or week_start.year != previous_year:
            label += f" '{week_start.strftime('%y')}"
        anchor = "start" if index == 0 else "middle"
        ticks.append((70 + index * 28, label, anchor))
        previous_year = week_start.year

    ticks.append((70 + 51 * 28 + 21, "NOW", "end"))
    return ticks


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
    weekly = activity.weekly
    weekly_peak = max(weekly, default=1)
    rolling_total = sum(weekly)
    safe_username = html.escape(USERNAME)
    towers = "\n      ".join(
        render_tower(index, value, weekly_peak, latest=index == len(weekly) - 1)
        for index, value in enumerate(weekly)
    )
    reflections = "\n      ".join(
        render_reflection(index, value, weekly_peak)
        for index, value in enumerate(weekly)
    )
    ticks = "\n      ".join(
        f'<g><rect x="{x}" y="426" width="2" height="8" '
        f'fill="{("#06ffa5" if label == "NOW" else "#7d668f")}"/>'
        f'<text x="{x}" y="456" '
        f'fill="{("#06ffa5" if label == "NOW" else "#a997b7")}" '
        f'font-size="17" font-weight="700" text-anchor="{anchor}">{label}</text></g>'
        for x, label, anchor in timeline_ticks()
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="560" viewBox="0 0 1600 560" role="img" aria-labelledby="title desc" shape-rendering="crispEdges">
  <title id="title">{safe_username}'s contribution city</title>
  <desc id="desc">A vaporwave pixel skyline generated from {rolling_total} contributions across {activity.active_days} active days. Each of the 52 towers represents one week; height and lit windows increase with activity. The last seven days contain {activity.last_7} contributions.</desc>
  <metadata>source={activity.source}; user={safe_username}; window=52-sunday-weeks; calendar-total={activity.total}; rolling-total={rolling_total}</metadata>
  <defs>
    <linearGradient id="night" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#0d1117"/>
      <stop offset=".6" stop-color="#0e1019"/>
      <stop offset="1" stop-color="#151020"/>
    </linearGradient>
    <linearGradient id="sun" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#fffd82"/>
      <stop offset=".45" stop-color="#ff9871"/>
      <stop offset="1" stop-color="#ff4db8"/>
    </linearGradient>
    <linearGradient id="reflection-alpha" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ffffff" stop-opacity=".5"/>
      <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>
    <pattern id="stars" width="104" height="76" patternUnits="userSpaceOnUse">
      <rect x="15" y="13" width="2" height="2" fill="#ffffff" opacity=".42"/>
      <rect x="67" y="21" width="3" height="3" fill="#00d8ff" opacity=".25"/>
      <rect x="39" y="57" width="2" height="2" fill="#ff6ad5" opacity=".34"/>
      <rect x="91" y="65" width="2" height="2" fill="#ffffff" opacity=".2"/>
    </pattern>
    <pattern id="scanlines" width="8" height="8" patternUnits="userSpaceOnUse">
      <rect width="8" height="4" fill="#000000" opacity="0"/>
      <rect y="4" width="8" height="4" fill="#000000" opacity=".1"/>
    </pattern>
    <clipPath id="pixel-sun">
      <path d="M1184 116h88v8h32v8h24v16h16v16h8v24h8v32h8v72h-8v32h-8v24h-16v16h-24v8h-32v8h-88v-8h-32v-8h-24v-16h-16v-24h-8v-32h-8v-72h8v-32h8v-24h16v-16h24v-8h32v-8z"/>
    </clipPath>
    <mask id="reflection-mask">
      <rect x="0" y="418" width="1600" height="142" fill="url(#reflection-alpha)"/>
    </mask>
    <filter id="sun-glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="5" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <style>
      text {{ font-family: "Courier New", Consolas, monospace; }}
      .tower {{ transform-box: fill-box; transform-origin: center bottom; animation: city-boot .68s steps(6, end) both; }}
      .beacon {{ animation: beacon 3.2s steps(2, end) infinite; }}
      .now-pulse {{ animation: now-pulse 3.2s steps(4, end) infinite; }}
      .current-window {{ animation: current-window 3.2s steps(2, end) infinite; }}
      @keyframes city-boot {{ from {{ transform: scaleY(.04); opacity: .15; }} to {{ transform: scaleY(1); opacity: 1; }} }}
      @keyframes beacon {{ 0%, 42%, 60%, 100% {{ opacity: 1; }} 51% {{ opacity: .18; }} }}
      @keyframes now-pulse {{ 0%, 100% {{ opacity: .16; }} 50% {{ opacity: .78; }} }}
      @keyframes current-window {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: .38; }} }}
      @media (prefers-reduced-motion: reduce) {{
        .tower, .beacon, .now-pulse, .current-window {{ animation: none; }}
      }}
    </style>
  </defs>

  <rect width="1600" height="560" fill="url(#night)"/>
  <rect width="1600" height="560" fill="url(#stars)"/>

  <g clip-path="url(#pixel-sun)" opacity=".94" filter="url(#sun-glow)">
    <rect x="1080" y="106" width="320" height="300" fill="url(#sun)"/>
    <rect x="1070" y="224" width="340" height="8" fill="#11101a"/>
    <rect x="1070" y="244" width="340" height="10" fill="#11101a"/>
    <rect x="1070" y="268" width="340" height="13" fill="#11101a"/>
    <rect x="1070" y="298" width="340" height="17" fill="#11101a"/>
    <rect x="1070" y="336" width="340" height="22" fill="#11101a"/>
  </g>

  <text x="67" y="62" fill="#00d8ff" font-size="21" font-weight="700">{safe_username}</text>
  <text x="67" y="110" fill="#00d8ff" font-family="Arial Black, Arial, sans-serif" font-size="43" font-weight="900" opacity=".52">COMMIT CITY</text>
  <text x="73" y="110" fill="#ff6ad5" font-family="Arial Black, Arial, sans-serif" font-size="43" font-weight="900" opacity=".52">COMMIT CITY</text>
  <text x="70" y="110" fill="#f7f3ff" font-family="Arial Black, Arial, sans-serif" font-size="43" font-weight="900">COMMIT CITY</text>
  <text x="70" y="141" fill="#a997b7" font-size="18">52 TOWERS. ONE ROLLING YEAR.</text>

  <text x="1530" y="62" fill="#fffd82" font-size="28" font-weight="700" text-anchor="end">{rolling_total} CONTRIBUTIONS</text>
  <text x="1530" y="92" fill="#a997b7" font-size="17" text-anchor="end">HEIGHT + WINDOWS FOLLOW REAL ACTIVITY</text>

  <path d="M0 416V384h42v-20h34v12h38v-42h32v26h36v-18h34v36h30v-60h36v30h34v-22h36v46h32v-28h36v72z" fill="#0b0e14" opacity=".55"/>
  <path d="M872 416v-36h32v-32h34v18h38v-52h34v38h34v-24h38v42h32v-66h38v28h34v-40h38v58h34v-32h38v98z" fill="#10101a" opacity=".48"/>

  <path d="M0 418h1600v142H0z" fill="#24152f" opacity=".18"/>
  <g fill="none" stroke="#9d5fc4" stroke-width="2" opacity=".34">
    <path d="M800 418L52 560M800 418L312 560M800 418L530 560M800 418L1070 560M800 418L1288 560M800 418L1548 560"/>
    <path d="M0 430h1600M0 450h1600M0 480h1600M0 516h1600M0 558h1600"/>
  </g>
  <line x1="0" y1="418" x2="1600" y2="418" stroke="#ff6ad5" stroke-width="3" opacity=".56"/>

  <g mask="url(#reflection-mask)" opacity=".3">
      {reflections}
  </g>

  <g>
      {towers}
  </g>

  <g>
      {ticks}
  </g>

  <text x="70" y="536" fill="#b7a9c2" font-size="17" font-weight="700">TOWER HEIGHT + LIT WINDOWS = WEEKLY COMMITS</text>
  <g transform="translate(1116 519)">
    <rect width="15" height="15" fill="#342b43"/><text x="26" y="14" fill="#a997b7" font-size="16">0</text>
    <rect x="82" width="15" height="15" fill="#06ffa5"/><text x="108" y="14" fill="#a997b7" font-size="16">LOW</text>
    <rect x="190" width="15" height="15" fill="#00d8ff"/><text x="216" y="14" fill="#a997b7" font-size="16">BUSY</text>
    <rect x="312" width="15" height="15" fill="#ff6ad5"/><text x="338" y="14" fill="#a997b7" font-size="16">PEAK</text>
  </g>

  <rect width="1600" height="560" fill="url(#scanlines)" pointer-events="none"/>
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
                "rolling_total": sum(activity.weekly),
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
