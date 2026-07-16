# Agent Notes for adamllll Profile Repo

## Purpose

This repository powers the GitHub profile README for `adamllll`.

## Editing Rules

- Primary surface: `README.md`.
- Generated visual: `assets/adam-os-hero.svg`.
- Generator: `scripts/render_profile_hero.py`; edit the generator rather than hand-editing the generated SVG.
- Keep the profile concise and visual; it should work as a public landing card.
- Prefer GitHub-compatible Markdown and simple inline HTML.
- Avoid custom CSS blocks because GitHub strips most style tags.
- Do not commit secrets, private URLs, API keys, or machine-local paths.
- External image badges are acceptable when they are stable public badge/render services.

## Visual Direction

- Current style: dark ADAM_OS public-desktop card / cyan-violet-magenta / Win95 chrome accents.
- Tone: concise, technical, slightly atmospheric; signal over scoreboard.
- The hero's status, accent, counters, and 28-day pulse are generated from real GitHub contribution data.
- Do not add a separate README contribution section or third-party contribution graph. GitHub already renders its native contribution module below the README.

## Automation

- `.github/workflows/refresh-profile-hero.yml` refreshes the hero daily and commits only when its visual data changes.
- `PROFILE_STATS_TOKEN` is optional. When configured as a repository secret, it can expose contribution data visible to that token; otherwise the workflow uses the GitHub-provided token/public calendar fallback.
- Automated commits use `github-actions[bot]`, not the profile owner, so refreshes do not manufacture owner contributions.

## Verification

Before commit:

```bash
GH_TOKEN="$(gh auth token)" python3 scripts/render_profile_hero.py
python3 -c "import xml.etree.ElementTree as ET; ET.parse('assets/adam-os-hero.svg')"
git diff --check
git diff -- README.md AGENTS.md scripts/render_profile_hero.py .github/workflows/refresh-profile-hero.yml assets/adam-os-hero.svg
git status --short
```

For major visual changes, inspect the generated SVG locally and the rendered README on GitHub after push.
