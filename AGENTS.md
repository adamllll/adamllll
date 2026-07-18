# Agent Notes for adamllll Profile Repo

## Purpose

This repository powers the GitHub profile README for `adamllll`.

## Editing Rules

- Primary surface: `README.md`.
- Generated visual: `assets/profile-activity.svg`.
- Generator: `scripts/render_profile_activity.py`; edit the generator rather than hand-editing the generated SVG.
- Keep the profile concise and visual; it should work as a public landing card.
- Prefer GitHub-compatible Markdown and simple inline HTML.
- Avoid custom CSS blocks because GitHub strips most style tags from README content.
- Do not commit secrets, private URLs, API keys, or machine-local paths.

## Visual Direction

- Current style: a night-mode Win95 profile window with cobalt activity typography and a large `ADAM` word mark.
- Each of the 52 vertical bands represents one week of real GitHub contribution activity.
- Band brightness, the compact timeline, the yearly total, and recent pulses are data-driven.
- The title bar and taskbar remain as a light system skeleton; during boot, `OPEN ADAM_OS` expands a full pixel frame while 52 vertical data conduits load the word mark, then all temporary boot geometry fades away.
- A compact `SYSTEM DIRECTORY` rail may sit below the poster for real Projects, Blog, and About links; render it as one GitHub-safe preformatted system bar with a right-aligned status label, and hide that decorative status asset on narrow screens.
- Motion must remain self-contained in the SVG, use no JavaScript, and respect `prefers-reduced-motion`.
- Tone: bold, direct, readable, and brand-led rather than dashboard-like.
- Do not add a separate README contribution graph. GitHub already renders its native contribution module below the README.

## Automation

- `.github/workflows/refresh-profile-activity.yml` refreshes the generated identity daily.
- `PROFILE_STATS_TOKEN` is optional. When configured as a repository secret, it can expose contribution data visible to that token; otherwise the workflow uses the GitHub-provided token and public calendar fallback.
- The workflow commits only when `assets/profile-activity.svg` actually changes.
- Automated commits use `github-actions[bot]`, not the profile owner, so refreshes do not manufacture owner contributions.

## Verification

Before commit:

```bash
GH_TOKEN="$(gh auth token)" python3 scripts/render_profile_activity.py
python3 -c "import xml.etree.ElementTree as ET; ET.parse('assets/profile-activity.svg')"
git diff --check
git diff -- README.md AGENTS.md scripts/render_profile_activity.py .github/workflows/refresh-profile-activity.yml assets/profile-activity.svg
git status --short
```

For major visual changes, inspect the generated SVG locally and the rendered README on GitHub after push.
