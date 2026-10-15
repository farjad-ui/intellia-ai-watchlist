# Intellia AI Watchlist

A daily AI learning page for the Intellia team. Published at https://farjad-ui.github.io/intellia-ai-watchlist/ once GitHub Pages is enabled.

## How it works

1. `build.py` fetches every feed in `sources.txt` and keeps the last seven days in `pool.json`.
2. Claude Code reads `editorial.md` and `pool.json` and writes the issue to `today.json`.
3. `render.py` turns `today.json` into `index.html`.
4. `daily.ps1` runs all three, commits and pushes. Task Scheduler runs it at 12:00 every day.

## Files you edit

- `sources.txt`: the feeds. One per line, `section url display-name`. Sections are `watch`, `models`, `tools`, `reading`.
- `editorial.md`: what gets picked and how it is written. Edit it in plain English when the page drifts.

## Commands

Run the whole job by hand:

```
powershell -ExecutionPolicy Bypass -File daily.ps1
```

Run the tests:

```
python test_watchlist.py
```

Failures are logged to `logs/daily.log`. If a day is missed, the page keeps the last issue and the footer shows its date.
