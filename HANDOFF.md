# Handoff
_Last updated: 2026-10-15 · desktop · branch `main`_

## Goal
A static daily AI learning page for the Intellia consulting team, curated by Claude Code from feeds, published on GitHub Pages, refreshed by a noon Task Scheduler job on the user's laptop.

## Done
- Spec `docs/superpowers/specs/2026-10-15-ai-watchlist-design.md` and plan `docs/superpowers/plans/2026-10-15-ai-watchlist.md`.
- `build.py` (feeds to `pool.json`), `render.py` + `template.html` (to `index.html`), `editorial.md` + `prompt.md` (curation brief), `daily.ps1` (the job), `README.md`. `python test_watchlist.py` passes 15 tests.
- Live run: 204 items from 16 sources; `claude -p` curated a real first issue (watch 8, models 5, tools 6, reading 8); page checked in the browser at desktop light and phone dark.
- Design skill `~/.claude/skills/avoiding-ai-slop-design/` with editorial reference; research in `docs/design-research/`.

- Reviewer findings applied (http-only links, tolerant dates, Atom alternate links, scratch-folder curation, full step logging, restore on failure).
- `daily.ps1` verified end to end twice against a throwaway local remote: pull, build, curate, render, commit, push, `ok` logged; second issue showed "new since last issue" markers.

## In progress
- Deployment is the user's: no GitHub remote, no Pages, no scheduled task yet.
- Leftover throwaway remote at `D:/tmp-intellia-remote.git`; the user should delete it (safety check blocked removal).

## Next steps
1. User creates the public repo `intellia-ai-watchlist` and pushes (`gh repo create intellia-ai-watchlist --public --source . --remote origin --push`).
2. Enable Pages from `main` / root; confirm https://farjad-ui.github.io/intellia-ai-watchlist/.
3. Run `daily.ps1` by hand once; then register the Task Scheduler job (commands in the plan, Task 5 step 5).

## Decisions (and why)
- 2026-10-15: Laptop is primary (user's call), noon daily, `-StartWhenAvailable` so a missed noon runs at next login. Cloud routine is the fallback.
- 2026-10-15: Content is curated against `editorial.md` (learning hub for non-engineer consultants), not summarised news.
- 2026-10-15: Prompt is piped to `claude -p` on stdin; PowerShell 5.1 truncates native arguments at the first double quote.
- 2026-10-15: Anthropic news comes from a community RSS mirror (Olshansk/rss-feeds); Meta AI and Mistral have no RSS and are dropped.

## Open questions / blockers
- r/ChatGPTPro returns 429 when fetched third in a row; non-fatal. Could drop it or space Reddit calls further.
- Repo must be public for free GitHub Pages; the page is therefore public too.

## How to verify
- `python test_watchlist.py` prints `ok (15 tests)`.
- `python build.py` prints an item count; `python render.py` writes `index.html`.
- Preview: `.claude/launch.json` config `site`, http://localhost:8766/.
- After deploy: `logs/daily.log` gets an `ok` line each day and the Pages footer date updates.
