#!/usr/bin/env python3
"""Render the profile hero from GitHub's real contribution calendar.

The generated SVG is static and GitHub-safe. A scheduled workflow refreshes it;
no JavaScript, CSS injection, or third-party graph renderer is involved.
"""

from __future__ import annotations

import html
import json
import os
import re
import sys
from datetime import date, timedelta
import urllib.error
import urllib.request
from pathlib import Path

USERNAME = os.environ.get("PROFILE_LOGIN", "adamllll")
OUTPUT = Path(os.environ.get("PROFILE_HERO_OUTPUT", "assets/adam-os-hero.svg"))
GRAPHQL_URL = "https://api.github.com/graphql"
PUBLIC_CALENDAR_URL = f"https://github.com/users/{USERNAME}/contributions"

QUERY = """
query ProfilePulse($login: String!) {
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


def request(url: str, *, token: str | None = None, payload: dict | None = None) -> str:
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{USERNAME}-profile-hero",
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
    """Parse the same public calendar HTML rendered on the GitHub profile."""
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
    days = [{"date": date, "count": count} for date, count in sorted(days_by_date.items())]
    return total, days


def load_calendar() -> tuple[int, list[dict[str, int | str]], str]:
    token = (
        os.environ.get("PROFILE_STATS_TOKEN")
        or os.environ.get("GH_TOKEN")
        or os.environ.get("GITHUB_TOKEN")
    )
    if token:
        try:
            total, days, source = graphql_calendar(token)
            return total, days, source
        except (RuntimeError, urllib.error.URLError, json.JSONDecodeError) as exc:
            print(f"warning: GraphQL unavailable ({exc}); falling back to public calendar", file=sys.stderr)
    total, days = public_calendar()
    return total, days, "github-public-calendar"


def activity_mode(last_7: int) -> tuple[str, str]:
    if last_7 == 0:
        return "QUIET", "#7c3aed"
    if last_7 <= 3:
        return "WARM", "#00d8ff"
    if last_7 <= 12:
        return "ACTIVE", "#72f1b8"
    return "SURGE", "#ff6ad5"


def render(total: int, days: list[dict[str, int | str]], source: str) -> str:
    days = sorted(days, key=lambda item: str(item["date"]))
    counts = [int(day["count"]) for day in days]
    active_days = sum(count > 0 for count in counts)
    last_7 = sum(counts[-7:])
    last_30 = sum(counts[-30:])
    peak = max(counts, default=0)
    mode, accent = activity_mode(last_7)

    calendar_by_date = {str(day["date"]): int(day["count"]) for day in days}
    latest_date = date.fromisoformat(str(days[-1]["date"]))
    current_week_start = latest_date - timedelta(days=latest_date.weekday())
    window_start = current_week_start - timedelta(days=21)
    recent = [
        calendar_by_date.get((window_start + timedelta(days=index)).isoformat(), 0)
        for index in range(28)
    ]
    recent_peak = max(recent, default=0)
    bars: list[str] = []
    points: list[str] = []
    for index, count in enumerate(recent):
        x = 18 + index * 10
        height = 4 if count == 0 else 8 + round(36 * count / max(1, recent_peak))
        y = 228 - height
        if count == 0:
            color = "#2a2346"
        elif count < max(2, recent_peak * 0.34):
            color = "#00d8ff"
        elif count < max(3, recent_peak * 0.67):
            color = "#72f1b8"
        else:
            color = "#ff6ad5"
        bars.append(f'<rect x="{x}" y="{y}" width="6" height="{height}" rx="2" fill="{color}"/>')
        points.append(f"{x + 3},{y - 4}")

    sparkline = " ".join(points)
    bars_svg = "\n      ".join(bars)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="420" viewBox="0 0 1600 420" role="img" aria-labelledby="title desc">
  <title id="title">ADAM OS profile — {mode.lower()} commit pulse</title>
  <desc id="desc">A GitHub-safe profile banner generated from real contribution activity: {total} contributions in the last year, {last_7} in the last seven days.</desc>
  <metadata>source=github-contribution-calendar; user={USERNAME}; window=rolling-year</metadata>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#070b12"/>
      <stop offset="0.42" stop-color="#14102a"/>
      <stop offset="0.78" stop-color="#1a0a2e"/>
      <stop offset="1" stop-color="#0b1020"/>
    </linearGradient>
    <linearGradient id="horizon" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{accent}" stop-opacity="0"/>
      <stop offset="0.55" stop-color="#7c3aed" stop-opacity="0.35"/>
      <stop offset="1" stop-color="#ff6ad5" stop-opacity="0.55"/>
    </linearGradient>
    <linearGradient id="titleFill" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#f8f7ff"/>
      <stop offset="0.55" stop-color="{accent}"/>
      <stop offset="1" stop-color="#ff6ad5"/>
    </linearGradient>
    <linearGradient id="titlebar" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#000080"/>
      <stop offset="0.55" stop-color="#7b2cbf"/>
      <stop offset="1" stop-color="{accent}"/>
    </linearGradient>
    <linearGradient id="scan" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ffffff" stop-opacity="0.08"/>
      <stop offset="0.5" stop-color="#ffffff" stop-opacity="0"/>
      <stop offset="1" stop-color="#ffffff" stop-opacity="0.05"/>
    </linearGradient>
    <pattern id="grid" width="56" height="56" patternUnits="userSpaceOnUse">
      <path d="M56 0H0V56" fill="none" stroke="#7c3aed" stroke-opacity="0.18" stroke-width="1"/>
    </pattern>
    <pattern id="dots" width="18" height="18" patternUnits="userSpaceOnUse">
      <circle cx="1.5" cy="1.5" r="1.2" fill="{accent}" fill-opacity="0.18"/>
    </pattern>
    <filter id="softGlow" x="-20%" y="-40%" width="140%" height="180%">
      <feGaussianBlur stdDeviation="6" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>

  <rect width="1600" height="420" fill="url(#bg)"/>
  <rect width="1600" height="420" fill="url(#dots)"/>
  <rect width="1600" height="420" fill="url(#grid)" opacity="0.9"/>
  <rect y="220" width="1600" height="200" fill="url(#horizon)"/>
  <rect width="1600" height="420" fill="url(#scan)"/>

  <g opacity="0.55" stroke="{accent}" stroke-width="1.2">
    <path d="M0 320 L800 250 L1600 320" fill="none"/>
    <path d="M80 420 L800 250 L1520 420" fill="none" stroke-opacity="0.35"/>
    <path d="M240 420 L800 250 L1360 420" fill="none" stroke-opacity="0.25"/>
    <path d="M420 420 L800 250 L1180 420" fill="none" stroke-opacity="0.2"/>
  </g>
  <path d="M0 280 L180 210 L320 250 L470 180 L620 240 L760 160 L930 230 L1100 150 L1280 220 L1450 170 L1600 230 L1600 420 L0 420 Z" fill="#0b1020" opacity="0.72"/>
  <path d="M0 310 L220 250 L380 290 L560 220 L740 280 L920 210 L1120 270 L1320 200 L1600 260 L1600 420 L0 420 Z" fill="#14102a" opacity="0.85"/>

  <g transform="translate(72 68)">
    <rect width="420" height="236" fill="#c0c0c0"/>
    <path d="M0 0H420V236H0Z" fill="none" stroke="#ffffff" stroke-width="3"/>
    <path d="M3 233H420V0" fill="none" stroke="#222222" stroke-width="3"/>
    <rect x="10" y="10" width="400" height="28" fill="url(#titlebar)"/>
    <text x="24" y="30" fill="#ffffff" font-family="Consolas, 'Courier New', monospace" font-size="15" font-weight="700">PROFILE.EXE</text>
    <g transform="translate(352 14)">
      <rect width="18" height="18" fill="#c0c0c0" stroke="#ffffff"/>
      <path d="M1 17H18V1" fill="none" stroke="#222" stroke-width="1.5"/>
      <path d="M4 9H14" stroke="#111" stroke-width="2"/>
      <rect x="24" width="18" height="18" fill="#c0c0c0" stroke="#ffffff"/>
      <path d="M25 17H42V1" fill="none" stroke="#222" stroke-width="1.5"/>
      <rect x="29" y="5" width="8" height="7" fill="none" stroke="#111" stroke-width="1.5"/>
    </g>
    <rect x="18" y="52" width="384" height="164" fill="#050816" stroke="#222" stroke-width="2"/>
    <text x="36" y="88" fill="#72f1b8" font-family="Consolas, 'Courier New', monospace" font-size="16" font-weight="700">C:\\ADAM_OS&gt; boot profile.exe</text>
    <text x="36" y="122" fill="#f8f7ff" font-family="Consolas, 'Courier New', monospace" font-size="14">surface   public desktop card</text>
    <text x="36" y="150" fill="#f8f7ff" font-family="Consolas, 'Courier New', monospace" font-size="14">lanes     systems · interfaces</text>
    <text x="36" y="178" fill="#f8f7ff" font-family="Consolas, 'Courier New', monospace" font-size="14">          tools · AI build loops</text>
    <text x="36" y="206" fill="{accent}" font-family="Consolas, 'Courier New', monospace" font-size="14">policy    real rhythm drives chrome</text>
  </g>

  <g transform="translate(540 78)">
    <text x="0" y="0" fill="{accent}" font-family="Consolas, 'Courier New', monospace" font-size="17" letter-spacing="3">PUBLIC DESKTOP // {mode}</text>
    <text x="0" y="74" fill="url(#titleFill)" font-family="Consolas, 'Courier New', monospace" font-size="84" font-weight="700" filter="url(#softGlow)">ADAM_OS</text>
    <text x="2" y="118" fill="#cfc9ff" font-family="Consolas, 'Courier New', monospace" font-size="18">systems · interfaces · tools · AI loops</text>
    <g transform="translate(2 148)" font-family="Consolas, 'Courier New', monospace" font-size="14">
      <rect width="120" height="32" rx="4" fill="#111827" stroke="#00d8ff"/>
      <text x="14" y="21" fill="#00d8ff">HOME BASE</text>
      <rect x="132" width="136" height="32" rx="4" fill="#111827" stroke="{accent}"/>
      <text x="148" y="21" fill="{accent}">LIVE PULSE</text>
      <rect x="280" width="136" height="32" rx="4" fill="#111827" stroke="#ff6ad5"/>
      <text x="298" y="21" fill="#ff6ad5">NO TROPHIES</text>
    </g>
  </g>

  <g transform="translate(1210 66)">
    <rect width="318" height="272" fill="#0b1020" stroke="{accent}" stroke-width="2" opacity="0.97"/>
    <rect width="318" height="36" fill="#14102a"/>
    <circle cx="292" cy="18" r="5" fill="{accent}"/>
    <text x="16" y="24" fill="{accent}" font-family="Consolas, 'Courier New', monospace" font-size="15" font-weight="700">COMMIT PULSE // {mode}</text>
    <g font-family="Consolas, 'Courier New', monospace">
      <text x="18" y="72" fill="#7780a1" font-size="12">ROLLING YEAR</text>
      <text x="18" y="105" fill="#f8f7ff" font-size="30" font-weight="700">{total}</text>
      <text x="124" y="72" fill="#7780a1" font-size="12">LAST 30D</text>
      <text x="124" y="105" fill="#00d8ff" font-size="30" font-weight="700">{last_30}</text>
      <text x="224" y="72" fill="#7780a1" font-size="12">LAST 7D</text>
      <text x="224" y="105" fill="{accent}" font-size="30" font-weight="700">{last_7}</text>
      <text x="18" y="136" fill="#cfc9ff" font-size="12">ACTIVE {active_days}D</text>
      <text x="124" y="136" fill="#cfc9ff" font-size="12">PEAK {peak}/DAY</text>
      <text x="224" y="136" fill="#cfc9ff" font-size="12">28D TRACE</text>
      <polyline points="{sparkline}" fill="none" stroke="{accent}" stroke-width="1.5" stroke-opacity="0.42"/>
      {bars_svg}
      <text x="18" y="254" fill="#7780a1" font-size="11">generated from GitHub activity</text>
    </g>
  </g>

  <rect y="392" width="1600" height="28" fill="#050816"/>
  <rect y="392" width="180" height="28" fill="{accent}"/>
  <rect x="180" y="392" width="180" height="28" fill="#ff6ad5"/>
  <rect x="360" y="392" width="180" height="28" fill="#7c3aed"/>
  <text x="560" y="411" fill="#cfc9ff" font-family="Consolas, 'Courier New', monospace" font-size="14">adamllll · real activity in the chrome · public desktop online</text>
</svg>
'''


def main() -> None:
    total, days, source = load_calendar()
    if not days:
        raise RuntimeError("GitHub returned an empty contribution calendar")
    svg = render(total, days, source)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")
    counts = [int(day["count"]) for day in days]
    print(
        json.dumps(
            {
                "user": USERNAME,
                "source": source,
                "total": total,
                "active_days": sum(count > 0 for count in counts),
                "last_30": sum(counts[-30:]),
                "last_7": sum(counts[-7:]),
                "output": str(OUTPUT),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
