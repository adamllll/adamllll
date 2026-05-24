# Agent Notes for adamllll Profile Repo

## Purpose

This repository powers the GitHub profile README for `adamllll`.

## Editing Rules

- Primary file: `README.md`.
- Keep the profile concise and visual; it should work as a public landing card.
- Prefer GitHub-compatible Markdown and simple inline HTML.
- Avoid custom CSS blocks because GitHub strips most style tags.
- Do not commit secrets, private URLs, API keys, or machine-local paths.
- External image badges are acceptable when they are stable public badge/render services.

## Visual Direction

- Current style: dark command-center / cyan-violet / backend-systems profile.
- Tone: concise, technical, slightly atmospheric.
- Useful motifs: terminal snippets, bridge/home-base language, project nodes, signal strips.

## Verification

Before commit:

```bash
git diff -- README.md AGENTS.md
git status --short
```

For major visual changes, inspect the rendered README on GitHub after push.
