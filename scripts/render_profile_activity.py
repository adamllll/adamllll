#!/usr/bin/env python3
"""Render a data-driven ADAM identity from real GitHub contributions.

The output is a self-contained, GitHub-safe SVG. Each of the 52 vertical bands
maps to one week; fill height and brightness increase with contribution activity.
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


CANVAS_WIDTH = 1600
CANVAS_HEIGHT = 720
WORD_X = 60
WORD_TOP = 126
WORD_BOTTOM = 550
WORD_HEIGHT = WORD_BOTTOM - WORD_TOP
WORD_FONT_SIZE = 520
BAND_AREA_WIDTH = 1480
BAND_GAP = 4
TIMELINE_BASE_Y = 602
FOOTER_Y = 660
WEBSITE_LABEL = "HOME.ADAMLLLL.COM"


def activity_color(value: int) -> str:
    if value <= 5:
        return "#315ee8"
    if value <= 14:
        return "#00d8ff"
    if value <= 24:
        return "#c774e8"
    return "#ff6ad5"


def band_geometry(index: int, count: int = 52) -> tuple[float, float]:
    step = BAND_AREA_WIDTH / count
    return WORD_X + index * step, step - BAND_GAP


def render_activity_band(index: int, value: int, peak: int, *, recent: bool) -> str:
    x, width = band_geometry(index)
    strength = activity_strength(value, peak)
    fill_height = 14 if value == 0 else 72 + round((WORD_HEIGHT - 72) * strength)
    fill_y = WORD_BOTTOM - fill_height
    color = activity_color(value)
    delay = 0.35 + index * 0.026
    contribution_label = "contribution" if value == 1 else "contributions"
    parts = [
        f'<g class="activity-band" style="animation-delay:{delay:.3f}s">',
        f'  <title>Week {index + 1}: {value} {contribution_label}</title>',
        f'  <rect x="{x:.2f}" y="{WORD_TOP}" width="{width:.2f}" height="{WORD_HEIGHT}" '
        f'fill="#315ee8" opacity="{0.16 if value == 0 else 0.23:.2f}"/>',
    ]
    if value > 0:
        parts.append(
            f'  <rect x="{x:.2f}" y="{fill_y}" width="{width:.2f}" height="{fill_height}" '
            f'fill="{color}" opacity="{0.48 + strength * 0.5:.2f}"/>'
        )
        parts.append(
            f'  <rect x="{x + 3:.2f}" y="{fill_y - 4}" width="{max(2, width - 6):.2f}" '
            'height="4" fill="#f7f3ff" opacity=".58"/>'
        )
    if recent and value > 0:
        parts.append(
            f'  <rect class="recent-band" x="{x:.2f}" y="{WORD_TOP}" '
            f'width="{width:.2f}" height="{WORD_HEIGHT}" fill="#fffd82" opacity="0"/>'
        )
    parts.append("</g>")
    return "\n".join(parts)


def render_timeline_band(index: int, value: int, peak: int) -> str:
    x, width = band_geometry(index)
    strength = activity_strength(value, peak)
    height = 4 if value == 0 else 7 + round(27 * strength)
    opacity = 0.24 if value == 0 else 0.52 + strength * 0.46
    delay = 0.45 + index * 0.022
    return (
        f'<rect class="timeline-band" x="{x:.2f}" y="{TIMELINE_BASE_Y - height}" '
        f'width="{width:.2f}" height="{height}" fill="{activity_color(value)}" '
        f'opacity="{opacity:.2f}" style="animation-delay:{delay:.3f}s"/>'
    )


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
        x, width = band_geometry(index)
        ticks.append((round(x if index == 0 else x + width / 2), label, anchor))
        previous_year = week_start.year

    ticks.append((WORD_X + BAND_AREA_WIDTH, "NOW", "end"))
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
    scan_duration = max(7.4, 10.8 - min(activity.last_7, 20) * 0.12)
    activity_bands = "\n      ".join(
        render_activity_band(
            index,
            value,
            weekly_peak,
            recent=index >= len(weekly) - 4,
        )
        for index, value in enumerate(weekly)
    )
    timeline_bands = "\n      ".join(
        render_timeline_band(index, value, weekly_peak)
        for index, value in enumerate(weekly)
    )
    floor_lines = "\n      ".join(
        f'<line x1="{WORD_X}" y1="{y}" x2="{WORD_X + BAND_AREA_WIDTH}" y2="{y}"/>'
        for y in range(WORD_TOP + 22, WORD_BOTTOM, 26)
    )
    ticks = "\n      ".join(
        f'<g><rect x="{x}" y="612" width="2" height="8" '
        f'fill="{("#06ffa5" if label == "NOW" else "#7d668f")}"/>'
        f'<text x="{x}" y="646" '
        f'fill="{("#06ffa5" if label == "NOW" else "#a997b7")}" '
        f'font-size="15" font-weight="700" text-anchor="{anchor}">{label}</text></g>'
        for x, label, anchor in timeline_ticks()
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" viewBox="0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}" role="img" aria-labelledby="title desc" shape-rendering="crispEdges">
  <title id="title">ADAM contribution signal</title>
  <desc id="desc">A data-driven ADAM word mark formed by 52 weekly bands. Bright fill height follows {rolling_total} GitHub contributions across {activity.active_days} active days, with {activity.last_7} contributions in the last seven days.</desc>
  <metadata>source={activity.source}; user={safe_username}; window=52-sunday-weeks; calendar-total={activity.total}; rolling-total={rolling_total}</metadata>
  <defs>
    <linearGradient id="night" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#090d16"/>
      <stop offset=".64" stop-color="#0c101a"/>
      <stop offset="1" stop-color="#161022"/>
    </linearGradient>
    <linearGradient id="activity-scan-fill" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#f7f3ff" stop-opacity="0"/>
      <stop offset=".5" stop-color="#f7f3ff" stop-opacity=".36"/>
      <stop offset="1" stop-color="#f7f3ff" stop-opacity="0"/>
    </linearGradient>
    <pattern id="stars" width="104" height="76" patternUnits="userSpaceOnUse">
      <rect x="15" y="13" width="2" height="2" fill="#f7f3ff" opacity=".25"/>
      <rect x="67" y="21" width="3" height="3" fill="#00d8ff" opacity=".18"/>
      <rect x="39" y="57" width="2" height="2" fill="#ff6ad5" opacity=".2"/>
      <rect x="91" y="65" width="2" height="2" fill="#f7f3ff" opacity=".12"/>
    </pattern>
    <pattern id="scanlines" width="8" height="8" patternUnits="userSpaceOnUse">
      <rect width="8" height="4" fill="#05070d" opacity="0"/>
      <rect y="4" width="8" height="4" fill="#05070d" opacity=".07"/>
    </pattern>
    <clipPath id="adam-word">
      <text x="{WORD_X}" y="{WORD_BOTTOM}" textLength="{BAND_AREA_WIDTH}" lengthAdjust="spacingAndGlyphs" font-family="Arial Black, Arial, sans-serif" font-size="{WORD_FONT_SIZE}" font-weight="900">ADAM</text>
    </clipPath>
    <style>
      text {{ font-family: "Courier New", Consolas, monospace; }}
      .poster {{ animation: poster-in .45s cubic-bezier(.16, 1, .3, 1) both; }}
      .word-outline {{ animation: outline-lock .8s steps(6, end) .12s both; }}
      .star-field {{ animation: star-drift 20s steps(20, end) 2.8s infinite alternate; }}
      .activity-band {{ transform-box: fill-box; transform-origin: center bottom; animation: band-rise .85s steps(7, end) both; }}
      .timeline-band {{ transform-box: fill-box; transform-origin: center bottom; animation: timeline-rise .55s steps(5, end) both; }}
      .activity-scan {{ animation: activity-scan {scan_duration:.2f}s cubic-bezier(.16, 1, .3, 1) 2.2s infinite; }}
      .recent-band {{ animation: recent-pulse 3.4s steps(4, end) 2.8s infinite; }}
      .signal-rail {{ animation: signal-run 7.2s linear 2.5s infinite; }}
      .website-pulse {{ animation: website-pulse 4.6s steps(2, end) 3.2s infinite; }}
      @keyframes poster-in {{ from {{ opacity: .72; }} to {{ opacity: 1; }} }}
      @keyframes outline-lock {{ 0% {{ transform: translateX(-8px); opacity: .18; }} 58% {{ transform: translateX(3px); opacity: .56; }} 100% {{ transform: translateX(0); opacity: .48; }} }}
      @keyframes star-drift {{ from {{ transform: translateX(-18px); opacity: .58; }} to {{ transform: translateX(24px); opacity: .82; }} }}
      @keyframes band-rise {{ from {{ transform: scaleY(.05); opacity: .32; }} to {{ transform: scaleY(1); opacity: 1; }} }}
      @keyframes timeline-rise {{ from {{ transform: scaleY(.08); opacity: .24; }} to {{ transform: scaleY(1); }} }}
      @keyframes activity-scan {{ 0% {{ transform: translateX(0); opacity: 0; }} 7% {{ opacity: .52; }} 34% {{ transform: translateX(1810px); opacity: .26; }} 42%, 100% {{ transform: translateX(1810px); opacity: 0; }} }}
      @keyframes recent-pulse {{ 0%, 100% {{ opacity: 0; }} 48% {{ opacity: .16; }} 58% {{ opacity: .04; }} }}
      @keyframes signal-run {{ from {{ stroke-dashoffset: 0; }} to {{ stroke-dashoffset: -200; }} }}
      @keyframes website-pulse {{ 0%, 100% {{ opacity: .46; }} 50% {{ opacity: 1; }} }}
      @media (prefers-reduced-motion: reduce) {{
        .poster, .word-outline, .star-field, .activity-band, .timeline-band,
        .recent-band, .signal-rail, .website-pulse {{ animation: none; }}
        .activity-scan {{ display: none; }}
      }}
    </style>
  </defs>

  <g class="poster">
    <rect width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" fill="url(#night)"/>
    <g class="star-field">
      <rect x="-80" width="1760" height="{FOOTER_Y}" fill="url(#stars)"/>
    </g>

    <text x="{WORD_X}" y="44" fill="#00d8ff" font-size="18" font-weight="700">{safe_username}</text>
    <text x="{WORD_X}" y="78" fill="#f7f3ff" font-family="Arial Black, Arial, sans-serif" font-size="22" font-weight="900">52 WEEKS SHAPE THE NAME</text>
    <text x="1540" y="51" fill="#fffd82" font-size="30" font-weight="700" text-anchor="end">{rolling_total} CONTRIBUTIONS</text>
    <text x="1540" y="79" fill="#a997b7" font-size="14" text-anchor="end">ROLLING YEAR / LIVE GITHUB ACTIVITY</text>
    <line x1="{WORD_X}" y1="96" x2="1540" y2="96" stroke="#315ee8" stroke-width="2" opacity=".42"/>

    <text x="{WORD_X}" y="{WORD_BOTTOM}" textLength="{BAND_AREA_WIDTH}" lengthAdjust="spacingAndGlyphs" fill="#13275a" font-family="Arial Black, Arial, sans-serif" font-size="{WORD_FONT_SIZE}" font-weight="900">ADAM</text>

    <g clip-path="url(#adam-word)">
      {activity_bands}
      <g fill="none" stroke="#090d16" stroke-width="4" opacity=".64">
        {floor_lines}
      </g>
      <rect class="activity-scan" x="-150" y="{WORD_TOP}" width="92" height="{WORD_HEIGHT}" fill="url(#activity-scan-fill)"/>
    </g>

    <text class="word-outline" x="{WORD_X}" y="{WORD_BOTTOM}" textLength="{BAND_AREA_WIDTH}" lengthAdjust="spacingAndGlyphs" fill="none" stroke="#315ee8" stroke-width="4" opacity=".48" font-family="Arial Black, Arial, sans-serif" font-size="{WORD_FONT_SIZE}" font-weight="900">ADAM</text>

    <line class="signal-rail" x1="{WORD_X}" y1="558" x2="1540" y2="558" stroke="#00d8ff" stroke-width="2" stroke-dasharray="8 42" opacity=".52"/>
    <g>
      {timeline_bands}
    </g>
    <line x1="{WORD_X}" y1="{TIMELINE_BASE_Y + 2}" x2="1540" y2="{TIMELINE_BASE_Y + 2}" stroke="#315ee8" stroke-width="2" opacity=".48"/>
    <g>
      {ticks}
    </g>

    <rect y="{FOOTER_Y}" width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT - FOOTER_Y}" fill="#090c13" opacity=".95"/>
    <line x1="0" y1="{FOOTER_Y}" x2="{CANVAS_WIDTH}" y2="{FOOTER_Y}" stroke="#315ee8" stroke-width="2" opacity=".62"/>
    <text x="{WORD_X}" y="698" fill="#b7a9c2" font-size="14" font-weight="700">EACH BAND IS ONE WEEK / HEIGHT + BRIGHTNESS FOLLOW REAL ACTIVITY</text>

    <g opacity=".86">
      <rect class="website-pulse" x="1320" y="681" width="6" height="6" fill="#315ee8"/>
      <text x="1540" y="688" fill="#aebbe2" font-size="14" font-weight="700" text-anchor="end">OPEN DESKTOP ARCHIVE</text>
      <text x="1540" y="710" fill="#8091be" font-size="12" text-anchor="end">{WEBSITE_LABEL}</text>
      <line x1="1320" y1="716" x2="1540" y2="716" stroke="#315ee8" stroke-width="1" opacity=".42"/>
    </g>

    <rect width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" fill="url(#scanlines)" pointer-events="none"/>
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
