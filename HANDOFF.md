# Handoff
_Last updated: 2026-11-25 16:50 · desktop · branch `main`_

## Goal
A static daily AI learning page for the Intellia consulting team, curated by Claude Code from feeds, published on GitHub Pages (https://farjad-ui.github.io/intellia-ai-watchlist/) and posted to Slack, refreshed by a noon job on the user's laptop.

## Done
- Pipeline: `build.py` (feeds to `pool.json`), Claude curates `today.json` against `editorial.md` + `prompt.md`, `render.py` + `template.html` to `index.html`, `notify.py` posts to Slack (webhook in gitignored `slack-webhook.txt`).
- Ran on the old Windows PC via `daily.ps1` + Task Scheduler (`schedule.ps1`) until 2026-11-20.
- 2026-11-25: moved to this Mac. The job's copy is now `~/intellia-ai-watchlist` (fresh clone from GitHub, outside OneDrive). `daily.sh` (port of `daily.ps1`) runs it; `schedule.sh` writes `~/Library/LaunchAgents/com.intellia.watchlist.plist` (daily 12:00) and loads it. Verified: `launchctl kickstart gui/$(id -u)/com.intellia.watchlist` ran end to end, exit 0, pushed `daily: 2026-11-25`; `python3 test_watchlist.py` passes 16 tests.
- Repo-local git identity set to `farjad-ui` so daily commits match the old ones (the two 2026-11-25 commits went out under the Mac's auto identity).

## In progress
- Nothing. `slack-webhook.txt` was copied from the OneDrive folder on 2026-11-25; daily runs post to Slack at 12:15. The 2026-11-25 issue was posted by hand with `python3 notify.py`.

## Next steps
1. Check the 2026-11-26 noon run: `logs/daily.log` should end with `ok` and `slack ok`.
2. Reddit feeds in `sources.txt` return HTTP 404; fix the URLs or drop them.
3. Optional cleanup: delete `daily.ps1` / `schedule.ps1`; remove `/bin/bash` from Full Disk Access (no longer needed now the job is outside OneDrive).

## Decisions (and why)
- 2026-11-25: Job runs from `~/intellia-ai-watchlist`, not the OneDrive folder. macOS blocks launchd jobs from OneDrive (needed Full Disk Access for `/bin/bash`), and OneDrive left 200 files (git objects, the webhook) online-only that would not download. The OneDrive copy is stale; edit in the new folder or push from anywhere (the job pulls first).
- 2026-11-25: launchd over cron: it runs a missed noon job when the Mac wakes from sleep. If the Mac is shut down at noon, that day is skipped.
- 2026-10-15: Claude curates in a scratch folder holding only its inputs, so feed text cannot steer it into editing the repo.
- 2026-10-15: Anthropic news comes from a community RSS mirror (Olshansk/rss-feeds); Meta AI and Mistral have no RSS and are dropped.

## Open questions / blockers
- Repo must be public for free GitHub Pages; the page is therefore public too.

## How to verify
- `python3 test_watchlist.py` prints `ok (16 tests)`.
- `logs/daily.log` gets an `ok` line each day (launchd output also in `logs/launchd.log`); the Pages footer date updates.
- Preview: `.claude/launch.json` config `site`, http://localhost:8766/.
