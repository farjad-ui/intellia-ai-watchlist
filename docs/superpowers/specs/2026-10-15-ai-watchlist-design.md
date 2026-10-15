# Intellia AI Watchlist: design spec

Date: 2026-10-15. Status: approved in conversation, pending written review.

## 1. Purpose

A static web page the Intellia consulting team opens for five minutes a day to learn what is new in AI and what they can use. It is a learning hub, not a news site: releases, explainers, tools a non-engineer can try, and the occasional story that is genuinely big. Fully automated, no login, shared by URL.

## 2. Constraints and decisions

- Static site on GitHub Pages, repo on the user's personal GitHub, served from the `main` branch root.
- No framework, no build tool, no npm, no JavaScript on the page. Python 3 standard library only.
- The daily job runs on the user's laptop: Windows Task Scheduler runs `daily.ps1` at 12:00 Pakistan time, which runs the Python steps and calls `claude -p` headless for the curation step (billed to the subscription, no API key). A Claude Code cloud routine is the fallback if the laptop is often off at noon.
- Visual direction: the editorial mock `docs/design-research/direction-sample-v2.html`, built with the `avoiding-ai-slop-design` skill. Tokens and layout in section 7.
- Content direction: curated, not summarised. The routine reads a written editorial brief and selects a few items from a larger pool.
- Rolling seven-day window, refreshed daily, newest items marked.

## 3. Repository layout

```
sources.txt        feeds, one per line: "<section> <url>"
editorial.md       the brief the routine reads every morning (audience, picks, skips, voice)
build.py           fetch feeds -> pool.json (stdlib only)
render.py          today.json + template.html -> index.html
template.html      the page, with named placeholders
daily.ps1          the scheduled job: pull, build, claude -p, render, commit, push
prompt.md          the curation prompt passed to claude -p
today.json         what the routine wrote this morning (committed)
index.html         rendered output (committed; this is what Pages serves)
test_watchlist.py  one small test file
HANDOFF.md, CLAUDE.md, docs/
```

`pool.json` is written by `build.py` and gitignored. Everything else is committed by the routine.

## 4. Sources (`sources.txt`)

Format: `section url`, split on the first whitespace. Lines starting with `#` are comments. Sections: `watch`, `models`, `tools`, `reading`. Special URLs handled by `build.py`:

- `https://www.youtube.com/feeds/videos.xml?channel_id=...`: Atom, has `media:thumbnail` and `media:description`.
- Blog and lab RSS or Atom feeds: title, link, published, summary.
- `https://github.com/trending?since=daily` and language variants: HTML, parsed with regex for repo name, description, stars today.
- `https://hn.algolia.com/api/v1/search?tags=front_page`: JSON, title, url, points, comments.
- `https://www.reddit.com/r/<sub>/top/.rss?t=week`: Atom with summaries.

Initial list (user to adjust): Watch: Fireship, Matt Wolfe, AI Explained, The AI Advantage, Matthew Berman, Anthropic, OpenAI, Google. Models: Anthropic news, OpenAI news, Google DeepMind blog, Google AI blog, Meta AI, Mistral news, Microsoft Copilot blog. Tools: GitHub trending (all, Python, TypeScript), the awesome-claude-skills and awesome-mcp-servers lists' commit feeds, Anthropic skills repo. Reading: HN front page, r/ClaudeAI, r/ClaudeCode, r/ChatGPTPro. The Anthropic RSS URL must be located during implementation; `/rss.xml` returns 404.

## 5. Data flow

```
sources.txt -> build.py -> pool.json (all items from the last 7 days)
pool.json + editorial.md + previous today.json -> Claude (routine) -> today.json
today.json + template.html -> render.py -> index.html -> git push -> GitHub Pages
```

### build.py

- Reads `sources.txt`, fetches each URL with `urllib.request` and a 20-second timeout, a plain User-Agent, and `ssl` defaults.
- Normalises each entry to: `id` (sha1 of url), `section`, `title`, `url`, `source` (channel or outlet name, or hostname), `published` (ISO 8601 UTC), `summary` (feed text, HTML stripped, 400 chars max), `thumbnail` (YouTube only), `extra` (stars today, points, comments when present).
- Keeps items published within the last 7 days, dedupes by url, sorts newest first, writes `pool.json` as `{"built": "<ISO>", "items": [...]}`.
- A feed that fails or parses to zero items prints one warning line and is skipped. If every feed fails, exit code 1 so the routine stops and the page stays as it was.

### The daily job (`daily.ps1`, Task Scheduler, 12:00 Pakistan daily)

1. `git pull --ff-only`.
2. `python build.py`. Stop if it exits non-zero.
3. `claude -p` with `prompt.md` piped on stdin, `--allowedTools "Read,Write"`, `--permission-mode acceptEdits`. The prompt tells Claude to read `editorial.md`, `pool.json` and the existing `today.json`, and write a new `today.json` following the schema in section 6: 5-8 items per section against the brief, preferring items not in yesterday's issue, with the digest and one summary per item in the brief's voice. Stop if `today.json` did not change.
4. `python render.py`. Stop if it exits non-zero.
5. `git add today.json index.html`, commit `daily: YYYY-MM-DD`, `git push`.
6. Append one line per run to `logs/daily.log` (gitignored) so a silent failure can be found.

Task Scheduler settings: run whether the user is logged on or not is unnecessary (it needs the user's Claude login), so run only when logged on; tick "Run task as soon as possible after a scheduled start is missed"; start in the repo folder.

### render.py

- Loads `today.json`, validates required keys (fails with a clear message naming the missing key), computes relative ages ("3h", "2d") from `published` against `generated`, marks items newer than `previous_generated` as new, escapes all text, fills `template.html` placeholders with `string.Template`, writes `index.html`.
- No Markdown; the digest is a list of plain-text paragraphs.

## 6. `today.json` schema

```json
{
  "generated": "2026-10-16T02:05:00Z",
  "previous_generated": "2026-10-15T02:04:00Z",
  "date_label": "Friday 16 October 2026",
  "standfirst": "One sentence on what this issue is about.",
  "digest": ["Paragraph 1", "Paragraph 2", "..."],
  "sections": [
    {
      "key": "watch",
      "title": "Watch",
      "items": [
        {
          "title": "Sonnet 5 in 100 seconds",
          "url": "https://...",
          "source": "Fireship",
          "published": "2026-10-15T14:00:00Z",
          "summary": "What it is, why you would care, how hard it is to try. 15-25 words.",
          "thumbnail": "https://i.ytimg.com/vi/<id>/mqdefault.jpg"
        }
      ]
    }
  ],
  "feed_count": 24
}
```

Section keys and titles, in page order: `watch` "Watch", `models` "New models and tools", `tools` "Tools and skills you can use", `reading` "Worth reading". `thumbnail` is present only on `watch` items.

## 7. The page

Single HTML file, no JavaScript, Google Fonts for Literata (400, 500, optical size axis) and Public Sans (400, 500).

Tokens (from the approved mock):

| Role | Light | Dark |
|---|---|---|
| canvas | `#edf1e8` | `#151c17` |
| ink | `#1a221d` | `#e2e8df` |
| accent (links, new-item ages) | `#2a4590` | `#aabff2` |
| muted | `color-mix(in oklab, ink 62%, canvas)` | same |
| rule | `color-mix(in oklab, ink 10%, canvas)` | same |

Layout, top to bottom, one column of 40rem with 1rem gutters:

1. Masthead: "Intellia AI Watchlist" small in Public Sans; the date as the h1 in Literata; the standfirst in muted Literata.
2. "This week in AI": 3-5 paragraphs of digest prose, 18px, line-height 1.6, max 62ch.
3. Four sections. Each has a running head (Public Sans, 0.85rem, muted, hairline beneath) and 5-8 items separated by whitespace. Item: headline as the link (Literata 500, hairline underline in accent), one summary sentence (Literata 400), "Source · 3h" in Public Sans muted. Ages newer than `previous_generated` are set in accent at weight 500; a one-line legend under the standfirst explains it.
4. Watch items carry a 144px 16:9 thumbnail trailing the text on desktop and under the headline on phones; `aspect-ratio`, `object-fit: cover`, width and height attributes, 3px radius, `saturate(.7)` at rest. No other section has images.
5. Footer: one sentence, "Updated Friday 16 October 2026 at 07:05 PKT from 24 feeds."

Both colour schemes via `prefers-color-scheme`, `color-scheme: light dark`, matching `theme-color` metas, SVG favicon. Motion: two transitions (link underline colour, thumbnail saturation) under `prefers-reduced-motion: no-preference`. `::selection`, focus ring, tap highlight and scrollbar from the palette. Skip link, sequential headings, `scroll-margin-top` on section anchors.

## 8. Editorial brief (`editorial.md`)

Written in plain English so the user can edit it. Contents:

- Readers: consultants moving into AI deployment; comfortable with tools, not with code.
- Pick: model and product releases, pricing and feature changes, weekly recaps and explainers, tools and skills usable in an afternoon without an engineer, discussions with a practical takeaway, and a story only when it is big enough that a client will ask about it.
- Skip: research papers, policy and safety commentary, funding news, ML libraries and infrastructure repos, drama, anything already in yesterday's issue unless it changed.
- Counts: 5-8 per section, fewer if nothing qualifies.
- Voice: plain, specific, sentence case, no hype words, no em-dashes. Digest opens with what changed this week. Each summary is one sentence of 15-25 words covering what it is, why you would care, and how hard it is to try.

## 9. Error handling

- Feed failures are per-feed and non-fatal; total failure stops the run.
- Routine failure at any step leaves the previous `index.html` in place; the footer date shows the staleness.
- `render.py` refuses malformed `today.json` rather than rendering a broken page.
- Thumbnails are hotlinked from YouTube; a missing image shows the reserved box with the canvas colour.

## 10. Testing

`test_watchlist.py`, runnable with `python test_watchlist.py`:

- Parses a fixture YouTube Atom string and a fixture RSS string into normalised items with the right fields.
- Drops items older than 7 days and dedupes by url.
- Renders a minimal `today.json` and asserts the date, a headline and a thumbnail URL appear in the output, and that `<` in a title is escaped.
- Fails on a `today.json` missing `sections`.

Manual checks before calling it done: live `python build.py` returns items from every section; the rendered page opens at phone and desktop width in both schemes with none of the tells in the skill's baseline list; the routine completes one real run and the Pages URL updates.

## 11. Implementation order

1. `git init`, `sources.txt`, `build.py` with tests, live run.
2. `template.html` and `render.py` with tests, using a hand-written `today.json`.
3. `editorial.md` and `prompt.md`; one manual `claude -p` run to produce a real `today.json`; render and inspect the page in the browser.
4. `daily.ps1`; run it by hand once end to end.
5. GitHub repo, Pages enabled, first push; confirm the URL.
6. Register the Task Scheduler job at 12:00; confirm the next run.

## 12. Out of scope

Login, search, archive pages, email delivery, comments, analytics, per-user preferences, Instagram sources (no public feed).
