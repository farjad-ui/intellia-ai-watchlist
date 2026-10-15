# Handoff
_Last updated: 2026-10-15 16:30 · desktop · no git repo yet_

## Goal
A lightweight, fully automated daily AI briefing page ("Intellia AI Watchlist") the user shares with their consulting team. Digest paragraph on top, then four link sections (Videos, Lab news, Discussions, Repos). Static site, no framework, must not look AI-generated.

## Done
- Brainstorm answers collected: public URL on GitHub Pages; sources = YouTube channels, lab blogs, HN/Reddit, GitHub trending; fully automated, no curated list; daily digest written by Claude on top of headlines; refresh once a day ~7am PKT.
- Design research across Vercel guidelines, Impeccable, Emil Kowalski, Rauno, Anthropic frontend-design, slop essays, 8 component libraries, 19 reference sites, and the locally installed taste-skill / ui-ux-pro-max skills. Raw reports in `~/.claude/skills/avoiding-ai-slop-design/research/`.
- New personal skill written and tested: `~/.claude/skills/avoiding-ai-slop-design/` (SKILL.md + references/tells.md, craft-floor.md, reading-pages.md, sources.md). RED baseline without the skill showed 11 tells; GREEN run with the skill showed none. Screenshots and the GREEN sample page are in `docs/design-research/`.
- `.claude/launch.json` serves the scratchpad on port 8765 for previews (python http.server).

- Round 2 (user said v1 was text-only and boring): editorial readability research (Butterick, Bringhurst, Guardian Source, FT Origami, BBC GEL, NN/g, Semafor/Axios/Verge list patterns) added as `references/editorial.md` in the skill. Second mock `docs/design-research/direction-sample-v2.html` (screenshots 04-07): standfirst, digest prose, one summary sentence per item, real 16:9 YouTube thumbnails on videos only, Literata + Public Sans, ledger-green paper `#edf1e8`, blue-black link accent `#2a4590`.
- Feed probe (`python -I`, stdlib): YouTube RSS has thumbnails + descriptions; Reddit RSS and OpenAI RSS have summaries; GitHub trending is HTML with descriptions; Anthropic RSS URL unknown (404 at /rss.xml); hnrss.org timed out once, retry or use Algolia API.

- User approved the v2 visuals and the curated content model (learning hub, not news): sections Watch / New models and tools / Tools and skills you can use / Worth reading, rolling 7 days, routine curates against `editorial.md`.
- Spec written: `docs/superpowers/specs/2026-10-15-ai-watchlist-design.md`.

## In progress
- Brainstorming (superpowers:brainstorming, architectural path) at the "user reviews written spec" gate. No site code exists; the two sample HTML files are throwaway tests.

## Next steps
1. User reviews the spec; apply any changes.
2. Invoke superpowers:writing-plans on the spec to produce the implementation plan.
3. Implement in the order in spec section 11, starting with the cloud-sandbox fetch check and `git init`.

## Decisions (and why)
- 2026-10-15: Static site on GitHub Pages under the user's personal GitHub. Simplest to host and share; no login needed.
- 2026-10-15: Daily job runs as a Claude Code cloud routine (uses the subscription, no API key) with Windows Task Scheduler + `claude -p` as fallback. User asked to avoid an Anthropic API key. Cloud sandbox outbound fetch still to be verified; if blocked, move feed fetching to a GitHub Action and keep only digest writing in the routine.
- 2026-10-15: Design: Read-mode single column (~40rem), date as the title, serif digest prose, one sans for lists, hairlines not cards, one accent used only for ages newer than the previous issue, light and dark from the same tokens. Rejected: card grid, dark-by-default, eyebrows, pills, any motion beyond link hover.
- 2026-10-15: No Lenis, no component libraries, no build tools. Research showed all of them are landing-page kits; a reading page needs under 10 lines of motion CSS.

## Open questions / blockers
- User quoted the laptop/Task Scheduler option without comment; assumed it is the fallback, cloud routine primary. Confirm.
- Exact feed list (which YouTube channels, subreddits) not yet chosen.
- v2 voice (Literata + Public Sans, ledger green, blue-black links) not yet confirmed by the user.
- Per-item summaries need a writer: Claude in the daily routine (one sentence per item) or feed descriptions truncated. Routine is the better reading; decide in the spec.
- Lab-news thumbnails: possible via og:image fetch in build.py, but the v2 mock keeps images on videos only so an image means video. Confirm.

## How to verify
- Preview any HTML: `.claude/launch.json` config `scratch` (port 8765), or `python -m http.server 8765 --directory <folder>`.
- Skill self-check: give an agent the brief in `docs/design-research/` with the skill loaded; screenshot must show none of the tells listed in `~/.claude/skills/avoiding-ai-slop-design/research/baseline-tells.md`.
