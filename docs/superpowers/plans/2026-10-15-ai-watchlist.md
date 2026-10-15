# Intellia AI Watchlist Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A static daily AI learning-hub page, curated by Claude from RSS feeds, published on GitHub Pages, refreshed by a noon Task Scheduler job on the user's laptop.

**Architecture:** `build.py` fetches feeds into `pool.json`; `claude -p` reads the pool and the editorial brief and writes `today.json`; `render.py` fills `template.html` into `index.html`; `daily.ps1` runs those steps and pushes. No framework, no JavaScript on the page.

**Tech Stack:** Python 3.14 standard library, PowerShell 5.1, Claude Code CLI, git, GitHub Pages, Google Fonts.

**Spec:** `docs/superpowers/specs/2026-10-15-ai-watchlist-design.md`

## Global Constraints

- Python standard library only; no pip installs.
- No JavaScript in the page; one HTML file served from the `main` branch root.
- Sentence case in all user-facing text; no em-dashes; no hype words.
- Design tokens exactly as spec section 7; the page must show none of the tells in `~/.claude/skills/avoiding-ai-slop-design/research/baseline-tells.md`.
- Tests run with `python test_watchlist.py` and print `ok` on success.
- Commit after each task with a conventional prefix (`feat:`, `test:`, `chore:`).

---

### Task 1: Repository scaffold and sources

**Files:**
- Create: `.gitignore`, `sources.txt`, `test_watchlist.py` (runner only)

**Interfaces:**
- Produces: `sources.txt` lines of the form `<section> <url>` with `#` comments; sections `watch`, `models`, `tools`, `reading`.

- [ ] **Step 1: Initialise git and ignore generated files**

Run in the project folder:

```bash
git init -b main
```

`.gitignore`:

```
pool.json
logs/
__pycache__/
```

- [ ] **Step 2: Write `sources.txt`**

```
# section url   (sections: watch, models, tools, reading; text after the URL is ignored)

# Watch: weekly recaps and explainers
watch https://www.youtube.com/feeds/videos.xml?channel_id=UCsBjURrPoezykLs9EqgamOA   Fireship
watch https://www.youtube.com/feeds/videos.xml?channel_id=UChpleBmo18P08aKCIgti38g   Matt Wolfe
watch https://www.youtube.com/feeds/videos.xml?channel_id=UCNJ1Ymd5yFuUPtn21xtRbbw   AI Explained
watch https://www.youtube.com/feeds/videos.xml?channel_id=UCHhYXsLBEVVnbvsq57n1MTQ   The AI Advantage
watch https://www.youtube.com/feeds/videos.xml?channel_id=UCawZsQWqfGSbCI5yjkdVkTA   Matthew Berman
watch https://www.youtube.com/feeds/videos.xml?channel_id=UCrDwWp7EBBv4NwvScIpBDOA   Anthropic
watch https://www.youtube.com/feeds/videos.xml?channel_id=UCXZCJLdBC09xxGZ6gcdrc6A   OpenAI

# New models and tools: lab and vendor news
models https://openai.com/news/rss.xml
models https://blog.google/technology/ai/rss/
models https://deepmind.google/blog/rss.xml
models https://ai.meta.com/blog/rss/
models https://blogs.microsoft.com/ai/feed/
models https://github.com/anthropics/claude-code/releases.atom   Claude Code releases

# Tools and skills you can use
tools https://github.com/trending?since=daily
tools https://github.com/trending/python?since=daily
tools https://github.com/trending/typescript?since=daily
tools https://github.com/anthropics/skills/commits/main.atom   Anthropic skills repo
tools https://github.com/punkpeye/awesome-mcp-servers/commits/main.atom

# Worth reading
reading https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=60
reading https://www.reddit.com/r/ClaudeAI/top/.rss?t=week
reading https://www.reddit.com/r/ClaudeCode/top/.rss?t=week
reading https://www.reddit.com/r/ChatGPTPro/top/.rss?t=week
```

Anthropic's news feed URL is unknown (`/rss.xml` is 404); add it in Task 2 if the live run finds one.

- [ ] **Step 3: Write the test runner skeleton**

`test_watchlist.py`:

```python
"""Run with: python test_watchlist.py"""
import sys


def run():
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    for t in tests:
        t()
        print(".", end="")
    print(f"\nok ({len(tests)} tests)")


if __name__ == "__main__":
    run()
```

- [ ] **Step 4: Run it**

Run: `python test_watchlist.py`
Expected: `ok (0 tests)`

- [ ] **Step 5: Commit**

```bash
git add .gitignore sources.txt test_watchlist.py HANDOFF.md docs
git commit -m "chore: scaffold watchlist repo with sources and test runner"
```

---

### Task 2: build.py, feeds to pool.json

**Files:**
- Create: `build.py`
- Modify: `test_watchlist.py`

**Interfaces:**
- Produces: `pool.json` as `{"built": "<ISO UTC>", "items": [item...]}`. Item keys: `id`, `section`, `title`, `url`, `source`, `published` (ISO UTC), `summary`, `thumbnail` (or null), `extra` (dict).
- Functions used by tests: `parse_feed(text, section, url)`, `parse_trending(text, section, now)`, `parse_hn(text, section)`, `prune(items, now)`.

- [ ] **Step 1: Write the failing tests**

Add above `run()` in `test_watchlist.py`:

```python
from datetime import datetime, timedelta, timezone

NOW = datetime(2026, 10, 16, 7, 0, tzinfo=timezone.utc)

YT = """<?xml version="1.0"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns:media="http://search.yahoo.com/mrss/" xmlns="http://www.w3.org/2005/Atom">
 <title>Fireship</title>
 <entry>
  <yt:videoId>QZVzuq28eFw</yt:videoId>
  <title>Sonnet 5 in 100 seconds</title>
  <link rel="alternate" href="https://www.youtube.com/watch?v=QZVzuq28eFw"/>
  <published>2026-10-15T14:00:00+00:00</published>
  <media:group><media:description>Quick look &amp; demo.</media:description>
   <media:thumbnail url="https://i.ytimg.com/vi/QZVzuq28eFw/hqdefault.jpg"/></media:group>
 </entry>
</feed>"""

RSS = """<?xml version="1.0"?><rss version="2.0"><channel><title>OpenAI News</title>
<item><title>GPT-5.5 system card</title><link>https://openai.com/x</link>
<pubDate>Wed, 15 Oct 2026 10:00:00 GMT</pubDate>
<description>&lt;p&gt;A &lt;b&gt;400k&lt;/b&gt; context window.&lt;/p&gt;</description></item>
</channel></rss>"""

TRENDING = """<article class="Box-row"><h2 class="h3 lh-condensed">
<a href="/owner/repo" data-view-component="true">owner / repo</a></h2>
<p class="col-9 color-fg-muted my-1 pr-4">A tool that  does things.</p>
<span class="d-inline-block float-sm-right">1,234 stars today</span></article>"""

HN = '{"hits":[{"objectID":"1","title":"Why MCP needs a registry","url":"https://example.com/mcp","created_at":"2026-10-15T20:00:00Z","points":612,"num_comments":300}]}'


def test_parse_youtube_atom():
    from build import parse_feed
    (it,) = parse_feed(YT, "watch", "https://www.youtube.com/feeds/videos.xml?channel_id=x")
    assert it["title"] == "Sonnet 5 in 100 seconds"
    assert it["url"] == "https://www.youtube.com/watch?v=QZVzuq28eFw"
    assert it["source"] == "Fireship"
    assert it["published"] == "2026-10-15T14:00:00+00:00"
    assert it["summary"] == "Quick look & demo."
    assert it["thumbnail"] == "https://i.ytimg.com/vi/QZVzuq28eFw/mqdefault.jpg"
    assert it["section"] == "watch"


def test_parse_rss_strips_html_and_parses_date():
    from build import parse_feed
    (it,) = parse_feed(RSS, "models", "https://openai.com/news/rss.xml")
    assert it["source"] == "OpenAI News"
    assert it["summary"] == "A 400k context window."
    assert it["published"] == "2026-10-15T10:00:00+00:00"
    assert it["thumbnail"] is None


def test_parse_trending():
    from build import parse_trending
    (it,) = parse_trending(TRENDING, "tools", NOW)
    assert it["title"] == "owner/repo"
    assert it["url"] == "https://github.com/owner/repo"
    assert it["summary"] == "A tool that does things."
    assert it["extra"]["stars_today"] == 1234
    assert it["published"] == NOW.isoformat()


def test_parse_hn():
    from build import parse_hn
    (it,) = parse_hn(HN, "reading")
    assert it["url"] == "https://example.com/mcp"
    assert it["extra"] == {"points": 612, "comments": 300, "discussion": "https://news.ycombinator.com/item?id=1"}


def test_prune_window_and_dedupe():
    from build import parse_feed, prune
    old = RSS.replace("15 Oct 2026", "1 Oct 2026")
    items = parse_feed(RSS, "m", "u") + parse_feed(RSS, "m", "u") + parse_feed(old, "m", "u")
    out = prune(items, NOW)
    assert len(out) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python test_watchlist.py`
Expected: `ModuleNotFoundError: No module named 'build'`

- [ ] **Step 3: Write `build.py`**

```python
"""Fetch every feed in sources.txt and write pool.json (items from the last 7 days).

Run: python build.py
"""
import hashlib
import html
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

UA = "Mozilla/5.0 (compatible; intellia-watchlist/1.0)"
WINDOW = timedelta(days=7)
NS = {
    "a": "http://www.w3.org/2005/Atom",
    "m": "http://search.yahoo.com/mrss/",
    "yt": "http://www.youtube.com/xml/schemas/2015",
}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "replace")


def clean(text, limit=400):
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    return " ".join(text.split())[:limit]


def parse_date(s):
    if not s:
        return None
    s = s.strip()
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        try:
            d = parsedate_to_datetime(s)
        except (TypeError, ValueError):
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)


def item(section, title, url, source, published, summary="", thumbnail=None, extra=None):
    return {
        "id": hashlib.sha1(url.encode()).hexdigest()[:12],
        "section": section,
        "title": clean(title, 200),
        "url": url,
        "source": source,
        "published": published.isoformat() if published else None,
        "summary": clean(summary),
        "thumbnail": thumbnail,
        "extra": extra or {},
    }


def source_name(url, feed_title):
    m = re.search(r"reddit\.com/r/([^/]+)", url)
    if m:
        return "r/" + m.group(1)
    return clean(feed_title, 60) or re.sub(r"^www\.", "", urllib.parse.urlparse(url).netloc)


def parse_feed(text, section, url):
    root = ET.fromstring(text)
    items = []
    if root.tag.endswith("feed"):  # Atom: YouTube, Reddit, GitHub
        source = source_name(url, root.findtext("a:title", "", NS))
        for e in root.findall("a:entry", NS):
            link = e.find("a:link", NS)
            href = (link.get("href") if link is not None else "").strip()
            vid = e.findtext("yt:videoId", "", NS)
            thumb = f"https://i.ytimg.com/vi/{vid}/mqdefault.jpg" if vid else None
            summary = (e.findtext("m:group/m:description", "", NS)
                       or e.findtext("a:summary", "", NS)
                       or e.findtext("a:content", "", NS))
            when = e.findtext("a:published", "", NS) or e.findtext("a:updated", "", NS)
            items.append(item(section, e.findtext("a:title", "", NS), href, source,
                              parse_date(when), summary, thumb))
    else:  # RSS 2.0
        ch = root.find("channel")
        source = source_name(url, ch.findtext("title", ""))
        for e in ch.findall("item"):
            items.append(item(section, e.findtext("title", ""), (e.findtext("link") or "").strip(),
                              source, parse_date(e.findtext("pubDate", "")), e.findtext("description", "")))
    return items


def parse_trending(text, section, now):
    out = []
    for block in text.split('<article class="Box-row">')[1:]:
        m = re.search(r'<h2[^>]*>\s*<a[^>]*href="/([^"/]+/[^"/]+)"', block, re.S)
        if not m:
            continue
        repo = m.group(1)
        desc = re.search(r'<p class="col-9[^"]*">(.*?)</p>', block, re.S)
        stars = re.search(r"([\d,]+)\s+stars today", block)
        out.append(item(section, repo, f"https://github.com/{repo}", "GitHub trending", now,
                        desc.group(1) if desc else "",
                        extra={"stars_today": int(stars.group(1).replace(",", "")) if stars else None}))
    return out


def parse_hn(text, section):
    out = []
    for h in json.loads(text)["hits"]:
        discussion = f"https://news.ycombinator.com/item?id={h['objectID']}"
        out.append(item(section, h.get("title") or "", h.get("url") or discussion, "Hacker News",
                        parse_date(h.get("created_at")), "",
                        extra={"points": h.get("points"), "comments": h.get("num_comments"),
                               "discussion": discussion}))
    return out


def load_sources(path="sources.txt"):
    pairs = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        section, url = line.split()[:2]
        pairs.append((section, url))
    return pairs


def collect(pairs, now):
    items = []
    for section, url in pairs:
        try:
            text = fetch(url)
            if "hn.algolia.com" in url:
                new = parse_hn(text, section)
            elif "github.com/trending" in url:
                new = parse_trending(text, section, now)
            else:
                new = parse_feed(text, section, url)
        except Exception as e:  # one bad feed must not stop the run
            print(f"warning: {url}: {e}", file=sys.stderr)
            continue
        if not new:
            print(f"warning: {url}: no items", file=sys.stderr)
        items += new
    return items


def prune(items, now):
    seen, out = set(), []
    for it in sorted(items, key=lambda i: i["published"] or "", reverse=True):
        if not it["published"] or now - datetime.fromisoformat(it["published"]) > WINDOW:
            continue
        if it["url"] in seen:
            continue
        seen.add(it["url"])
        out.append(it)
    return out


if __name__ == "__main__":
    now = datetime.now(timezone.utc)
    pool = prune(collect(load_sources(), now), now)
    if not pool:
        sys.exit("error: no items from any feed")
    with open("pool.json", "w", encoding="utf-8") as f:
        json.dump({"built": now.isoformat(), "items": pool}, f, indent=1, ensure_ascii=False)
    sources = sorted(set(i["source"] for i in pool))
    print(f"{len(pool)} items from {len(sources)} sources -> pool.json")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python test_watchlist.py`
Expected: `ok (5 tests)`

- [ ] **Step 5: Live run and fix dead feeds**

Run: `python build.py`
Expected: a count line and at most a few warnings. For each warning, open the feed URL in the browser and correct `sources.txt` (wrong channel id, moved feed) or remove the line. Search for Anthropic's news RSS and add it under `models` if one exists.

- [ ] **Step 6: Commit**

```bash
git add build.py test_watchlist.py sources.txt
git commit -m "feat: fetch feeds into pool.json"
```

---

### Task 3: template.html and render.py

**Files:**
- Create: `template.html`, `render.py`, `today.json` (hand-written sample)
- Modify: `test_watchlist.py`

**Interfaces:**
- Consumes: `today.json` schema from spec section 6 (without `feed_count`; render counts `sources.txt`).
- Produces: `render(today: dict, template: str, now=None, feed_count=0) -> str`; `index.html`.

- [ ] **Step 1: Write the failing tests**

Add to `test_watchlist.py`:

```python
TODAY = {
    "generated": "2026-10-16T07:00:00+00:00",
    "previous_generated": "2026-10-15T07:00:00+00:00",
    "date_label": "Friday 16 October 2026",
    "standfirst": "What is new this week.",
    "digest": ["First paragraph.", "Second <b>paragraph</b>."],
    "sections": [{"key": "watch", "title": "Watch", "items": [
        {"title": "A <video>", "url": "https://youtube.com/watch?v=1", "source": "Fireship",
         "published": "2026-10-16T01:00:00+00:00", "summary": "Why it matters.",
         "thumbnail": "https://i.ytimg.com/vi/1/mqdefault.jpg"},
        {"title": "Old one", "url": "https://youtube.com/watch?v=2", "source": "Fireship",
         "published": "2026-10-14T01:00:00+00:00", "summary": "Older.", "thumbnail": None},
    ]}],
}


def test_render_fills_template_and_escapes():
    from render import render
    out = render(TODAY, "$date_label|$digest|$sections|$legend|$updated|$feed_count", feed_count=24)
    assert "Friday 16 October 2026" in out
    assert "Second &lt;b&gt;paragraph&lt;/b&gt;" in out
    assert "A &lt;video&gt;" in out
    assert 'src="https://i.ytimg.com/vi/1/mqdefault.jpg"' in out
    assert '<span class="new">6h</span>' in out       # newer than previous issue
    assert "Fireship · 2d" in out                     # older item, plain age
    assert "class=\"item video\"" in out and "class=\"item\"" in out
    assert "16 October 2026 at 12:00" in out          # generated shown in Pakistan time
    assert "|24" in out
    assert "new since" in out


def test_render_rejects_missing_sections():
    from render import render
    try:
        render({"generated": "2026-10-16T07:00:00+00:00"}, "")
    except ValueError as e:
        assert "sections" in str(e)
    else:
        raise AssertionError("expected ValueError")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python test_watchlist.py`
Expected: `ModuleNotFoundError: No module named 'render'`

- [ ] **Step 3: Write `render.py`**

```python
"""Render today.json through template.html into index.html.

Run: python render.py
"""
import html
import json
from datetime import datetime, timedelta, timezone
from string import Template

PKT = timezone(timedelta(hours=5))  # ponytail: fixed offset, Pakistan has no DST
REQUIRED = ("generated", "date_label", "standfirst", "digest", "sections")


def esc(s):
    return html.escape(str(s or ""), quote=True)


def age(published, now):
    minutes = int((now - datetime.fromisoformat(published)).total_seconds() // 60)
    if minutes < 60:
        return f"{max(minutes, 1)}m"
    if minutes < 1440:
        return f"{minutes // 60}h"
    return f"{minutes // 1440}d"


def render_item(it, now, prev):
    new = bool(prev) and datetime.fromisoformat(it["published"]) > datetime.fromisoformat(prev)
    cls, thumb = "item", ""
    if it.get("thumbnail"):
        cls = "item video"
        thumb = (f'<a class="thumb" href="{esc(it["url"])}" tabindex="-1" aria-hidden="true">'
                 f'<img src="{esc(it["thumbnail"])}" width="320" height="180" alt="" loading="lazy"></a>')
    a = age(it["published"], now)
    age_html = f'<span class="new">{a}</span>' if new else a
    return (f'<li class="{cls}"><h3><a href="{esc(it["url"])}">{esc(it["title"])}</a></h3>'
            f'<p>{esc(it["summary"])}</p><p class="meta">{esc(it["source"])} · {age_html}</p>{thumb}</li>\n'), new


def render(today, template, now=None, feed_count=0):
    missing = [k for k in REQUIRED if k not in today]
    if missing:
        raise ValueError(f"today.json missing: {', '.join(missing)}")
    now = now or datetime.fromisoformat(today["generated"])
    prev = today.get("previous_generated", "")
    digest = "".join(f"<p>{esc(p)}</p>\n" for p in today["digest"])
    sections, any_new = "", False
    for s in today["sections"]:
        rows = [render_item(i, now, prev) for i in s["items"]]
        any_new = any_new or any(n for _, n in rows)
        key = esc(s["key"])
        sections += (f'<section id="{key}" aria-labelledby="{key}-h"><h2 id="{key}-h">{esc(s["title"])}</h2>'
                     f'<ul class="items">\n{"".join(r for r, _ in rows)}</ul></section>\n')
    legend = '<p class="legend">Ages in blue are new since the last issue.</p>' if any_new else ""
    gen = datetime.fromisoformat(today["generated"]).astimezone(PKT)
    updated = f"{gen:%A} {gen.day} {gen:%B %Y} at {gen:%H:%M}"
    return Template(template).safe_substitute(
        date_label=esc(today["date_label"]), standfirst=esc(today["standfirst"]),
        digest=digest, sections=sections, legend=legend, updated=updated, feed_count=feed_count)


if __name__ == "__main__":
    with open("today.json", encoding="utf-8") as f:
        today = json.load(f)
    with open("template.html", encoding="utf-8") as f:
        template = f.read()
    with open("sources.txt", encoding="utf-8") as f:
        feeds = sum(1 for l in f if l.strip() and not l.startswith("#"))
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(render(today, template, feed_count=feeds))
    print("index.html written")
```

- [ ] **Step 4: Write `template.html`**

The CSS is the approved mock's, with `.new` and `.legend` added and the digest heading renamed.

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>$date_label · Intellia AI Watchlist</title>
<meta name="description" content="Daily AI learning hub for the Intellia consulting team: what is new, what to watch, tools you can use.">
<meta name="theme-color" media="(prefers-color-scheme: light)" content="#edf1e8">
<meta name="theme-color" media="(prefers-color-scheme: dark)" content="#151c17">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Cstyle%3Erect{fill:%23edf1e8}path{fill:%232a4590}@media(prefers-color-scheme:dark){rect{fill:%23151c17}path{fill:%23aabff2}}%3C/style%3E%3Crect width='16' height='16' rx='3'/%3E%3Cpath d='M7 3h2v10H7z'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Literata:opsz,wght@7..72,400;7..72,500&family=Public+Sans:wght@400;500&display=swap">
<style>
:root {
  color-scheme: light dark;
  --bg: #edf1e8;      /* ledger-green paper */
  --fg: #1a221d;      /* green-black ink */
  --accent: #2a4590;  /* blue-black pen ink: links and new-item ages */
  --muted: color-mix(in oklab, var(--fg) 62%, var(--bg));
  --rule: color-mix(in oklab, var(--fg) 10%, var(--bg));
  --serif: Literata, Georgia, "Times New Roman", serif;
  --sans: "Public Sans", system-ui, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root { --bg: #151c17; --fg: #e2e8df; --accent: #aabff2; }
}
html { -webkit-text-size-adjust: 100%; scrollbar-color: color-mix(in oklab, var(--fg) 25%, var(--bg)) var(--bg); }
body {
  margin: 0; background: var(--bg); color: var(--fg);
  font: 1rem/1.5 var(--serif);
  -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility;
  -webkit-tap-highlight-color: color-mix(in oklab, var(--accent) 20%, transparent);
  min-height: 100dvh;
}
.page { max-width: 40rem; margin-inline: auto; padding: 2.5rem max(1rem, env(safe-area-inset-right)) 3rem max(1rem, env(safe-area-inset-left)); }
::selection { background: color-mix(in oklab, var(--accent) 22%, var(--bg)); }
a { color: inherit; text-decoration: underline; text-decoration-thickness: 1px; text-underline-offset: .18em;
    text-decoration-color: color-mix(in oklab, var(--accent) 40%, var(--bg)); }
@media (hover: hover) {
  a:hover { text-decoration-color: var(--accent); text-decoration-thickness: 2px; }
  .item:hover .thumb img { filter: none; }
}
h3 a:visited { color: var(--muted); }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; border-radius: 2px; }
.skip { position: absolute; left: -999px; }
.skip:focus { left: 1rem; top: 1rem; background: var(--bg); padding: .5rem; }
.site { font: 500 .85rem/1.2 var(--sans); margin: 0 0 1.25rem; }
h1 { font: 500 1.75rem/1.15 var(--serif); letter-spacing: -.01em; margin: 0; text-wrap: balance; }
.standfirst { font: 1.125rem/1.5 var(--serif); color: var(--muted); margin: .6rem 0 0; max-width: 34em; text-wrap: pretty; }
.legend { font: .84rem/1.4 var(--sans); color: var(--muted); margin: .6rem 0 0; }
section { margin-top: 3rem; scroll-margin-top: 1.5rem; }
h2 { font: 500 .85rem/1.2 var(--sans); color: var(--muted); margin: 0 0 1rem; padding-bottom: .45rem; border-bottom: 1px solid var(--rule); }
.digest { font: 1.125rem/1.6 var(--serif); max-width: 62ch; text-wrap: pretty; }
.digest p { margin: 0; }
.digest p + p { margin-top: .8em; }
.items { list-style: none; margin: 0; padding: 0; }
.item { padding: .75rem 0; }
.item h3 { font: 500 1.0625rem/1.3 var(--serif); margin: 0 0 .3rem; text-wrap: balance; }
.item p { margin: 0; text-wrap: pretty; }
.meta { font: .84rem/1.4 var(--sans); color: var(--muted); font-variant-numeric: tabular-nums; margin-top: .35rem; }
.new { color: var(--accent); font-weight: 500; }
.video { display: grid; grid-template-columns: minmax(0, 1fr) 144px; grid-template-areas: "h t" "p t" "m t"; column-gap: 1.25rem; align-items: start; }
.video h3 { grid-area: h; }
.video p { grid-area: p; }
.video .meta { grid-area: m; }
.thumb { grid-area: t; display: block; text-decoration: none; }
.thumb img { display: block; width: 144px; height: auto; aspect-ratio: 16 / 9; object-fit: cover; border-radius: 3px; background: var(--rule); filter: saturate(.7); }
@media (max-width: 40rem) {
  .video { grid-template-columns: 1fr; grid-template-areas: "h" "t" "p" "m"; }
  .thumb { margin: .15rem 0 .5rem; }
  .thumb img { width: 160px; }
}
footer { margin-top: 4rem; padding-top: 1rem; border-top: 1px solid var(--rule); font: .84rem/1.5 var(--sans); color: var(--muted); }
footer p { margin: 0; }
@media (prefers-reduced-motion: no-preference) {
  a { transition: text-decoration-color 130ms ease-out; }
  .thumb img { transition: filter 150ms ease; }
}
</style>
</head>
<body>
<a class="skip" href="#digest">Skip to content</a>
<div class="page">
<header>
  <p class="site" translate="no">Intellia AI Watchlist</p>
  <h1>$date_label</h1>
  <p class="standfirst">$standfirst</p>
  $legend
</header>
<main>
<section id="digest" aria-labelledby="digest-h">
  <h2 id="digest-h">This week in AI</h2>
  <div class="digest">
$digest  </div>
</section>
$sections</main>
<footer>
  <p>Updated $updated Pakistan time from $feed_count feeds. Curated for the Intellia team.</p>
</footer>
</div>
</body>
</html>
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python test_watchlist.py`
Expected: `ok (7 tests)`

- [ ] **Step 6: Write a sample `today.json` and render it**

Write `today.json` by hand with the `TODAY` structure from the test but with two real items per section (copy four items from `pool.json`, add a summary sentence each). Then:

Run: `python render.py`
Expected: `index.html written`

- [ ] **Step 7: Inspect in the browser**

Point `.claude/launch.json` config `scratch` at the project folder (replace the scratchpad path with the project path), start it, open `http://localhost:8765/`, screenshot at desktop and phone width, light and dark. Check: thumbnails only on Watch items, ages in blue on items newer than `previous_generated`, legend present, footer reads "Updated Friday 16 October 2026 at 12:00 Pakistan time from N feeds."

- [ ] **Step 8: Commit**

```bash
git add render.py template.html today.json index.html test_watchlist.py .claude/launch.json
git commit -m "feat: render today.json into the page"
```

---

### Task 4: Editorial brief and curation prompt, first real issue

**Files:**
- Create: `editorial.md`, `prompt.md`
- Modify: `today.json`, `index.html` (regenerated)

**Interfaces:**
- Consumes: `pool.json` from Task 2, `today.json` schema from Task 3.
- Produces: `prompt.md` read by `daily.ps1` in Task 5.

- [ ] **Step 1: Write `editorial.md`**

```markdown
# Editorial brief

This file is read by Claude every morning before it writes today.json. Edit it in plain English when the page drifts.

## Readers

Consultants at Intellia moving into AI deployment. Comfortable with tools, products and clients; not engineers. They open the page once a day for five minutes to learn what is new and what they could try or tell a client about.

## Pick

- Model and product releases, pricing changes, new features in Claude, Claude Code, ChatGPT, Gemini, Copilot, Notion AI and similar.
- Weekly recaps and explainers: "X in 100 seconds", "what happened in AI this week", walkthroughs of new features, honest hands-on tests.
- Tools, skills, MCP servers and templates a consultant could try in an afternoon without an engineer: document, slide and spreadsheet generators, research and writing helpers, workflow and scheduling tools, Claude Code skills.
- Discussions with a practical takeaway, especially how people use Claude and Claude Code at work.
- A big story only when it is big enough that a client will ask about it.

## Skip

- Research papers, benchmarks without a product behind them, policy and safety commentary, funding rounds, personnel news.
- ML libraries, training frameworks, GPU and infrastructure repos, anything whose README starts with a CUDA version.
- Drama, speculation, hype pieces, reaction videos.
- Anything that appeared in yesterday's issue unless something changed.

## Counts

Five to eight items per section. Fewer is fine when nothing qualifies. Never pad.

## Voice

Plain and specific. Sentence case. No hype words (game-changing, revolutionary, must-see). No em-dashes. Write for a colleague, not a reader of a newspaper.

- Standfirst: one sentence on what this issue is about.
- Digest ("This week in AI"): three to five short paragraphs. Open with what changed this week. Say what it means for a consultant. Mention the week's big story only if there is one.
- Item summary: one sentence of 15 to 25 words covering what it is, why you would care, and how hard it is to try. Vary the length. Never restate the headline.
```

- [ ] **Step 2: Write `prompt.md`**

```markdown
You are curating today's issue of the Intellia AI Watchlist, a daily learning page for a consulting team. Work only with the Read and Write tools in the current folder.

1. Read `editorial.md` (the brief), `pool.json` (candidate items from the last 7 days) and `today.json` (yesterday's issue; it may be missing).
2. Choose items for four sections against the brief: `watch` (title "Watch"), `models` (title "New models and tools"), `tools` (title "Tools and skills you can use"), `reading` (title "Worth reading"). Candidates carry a `section` field; you may move an item to a better section. Prefer items not in yesterday's issue. Five to eight per section, fewer if nothing qualifies.
3. Write the new `today.json` with exactly this shape and nothing else:

{
  "generated": "<copy the built value from pool.json>",
  "previous_generated": "<the generated value from yesterday's today.json, or omit the key if there was none>",
  "date_label": "<generated converted to Pakistan time (UTC+5), formatted like Friday 16 October 2026>",
  "standfirst": "<one sentence>",
  "digest": ["<paragraph>", "<paragraph>", "<paragraph>"],
  "sections": [
    {"key": "watch", "title": "Watch", "items": [
      {"title": "<headline, 6-12 words, sentence case, subject first>",
       "url": "<url from the pool>",
       "source": "<source from the pool>",
       "published": "<published from the pool>",
       "summary": "<one sentence, 15-25 words>",
       "thumbnail": "<thumbnail from the pool, or null>"}
    ]},
    {"key": "models", "title": "New models and tools", "items": []},
    {"key": "tools", "title": "Tools and skills you can use", "items": []},
    {"key": "reading", "title": "Worth reading", "items": []}
  ]
}

Rules: copy url, source, published and thumbnail exactly from the pool; rewrite titles only to fix capitalisation or trim clickbait, keeping the meaning; thumbnails appear only on watch items; follow the voice section of the brief for every sentence; valid JSON, UTF-8, no trailing commas, no Markdown fences.
4. Do not edit any other file. Reply with one line: the number of items in each section.
```

- [ ] **Step 3: Produce the first real issue**

Run from the project folder:

```bash
python build.py
```

then

```bash
cat prompt.md | claude -p --allowedTools "Read,Write" --permission-mode acceptEdits
```

(PowerShell: `Get-Content prompt.md -Raw | claude -p --allowedTools "Read,Write" --permission-mode acceptEdits`. Pass the prompt on stdin: PowerShell 5.1 cuts native arguments at the first double quote.)
Expected: one line of counts, and `today.json` rewritten.

- [ ] **Step 4: Validate and render**

Run: `python -c "import json; d=json.load(open('today.json', encoding='utf-8')); print([ (s['key'], len(s['items'])) for s in d['sections'] ])"`
Then: `python render.py`
Expected: counts between 0 and 8 per section; `index.html written`.

- [ ] **Step 5: Inspect the page**

Open `http://localhost:8765/` again. Read every summary against the brief's voice rules. If the selection is off (hype videos, infra repos), tighten `editorial.md` and rerun Step 3. If the JSON was malformed, tighten `prompt.md`. Check the page against the avoiding-ai-slop-design baseline tells one more time.

- [ ] **Step 6: Commit**

```bash
git add editorial.md prompt.md today.json index.html
git commit -m "feat: editorial brief, curation prompt and first issue"
```

---

### Task 5: GitHub Pages, daily.ps1 and the scheduled task

**Files:**
- Create: `daily.ps1`
- Create: `README.md` (how to run and edit)

**Interfaces:**
- Consumes: everything above.

- [ ] **Step 1: Create the GitHub repository and push**

The user does this (or approves `gh` doing it). Public repository, because GitHub Pages on a free personal account needs a public repo.

```bash
gh repo create intellia-ai-watchlist --public --source . --remote origin --push
```

Without `gh`: create an empty public repo on github.com named `intellia-ai-watchlist`, then:

```bash
git remote add origin https://github.com/<user>/intellia-ai-watchlist.git
git push -u origin main
```

- [ ] **Step 2: Enable Pages**

On github.com: repository → Settings → Pages → Build and deployment → Source "Deploy from a branch" → Branch `main`, folder `/ (root)` → Save. After a minute the page is at `https://<user>.github.io/intellia-ai-watchlist/`. Open it and confirm it matches the local render. Or with the CLI:

```bash
gh api -X POST repos/<user>/intellia-ai-watchlist/pages -f build_type=legacy -f "source[branch]=main" -f "source[path]=/"
```

- [ ] **Step 3: Write `daily.ps1`**

```powershell
# Daily watchlist job. Scheduled at 12:00 by Task Scheduler.
# Run by hand: powershell -ExecutionPolicy Bypass -File daily.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force logs | Out-Null
function Log($m) { Add-Content logs\daily.log "$(Get-Date -Format s) $m"; Write-Host $m }
try {
  git pull --ff-only
  python build.py
  if ($LASTEXITCODE) { throw "build.py failed" }
  $before = (Get-FileHash today.json).Hash
  Get-Content prompt.md -Raw | claude -p --allowedTools "Read,Write" --permission-mode acceptEdits
  if ($LASTEXITCODE) { throw "claude failed" }
  if ((Get-FileHash today.json).Hash -eq $before) { throw "today.json unchanged" }
  python render.py
  if ($LASTEXITCODE) { throw "render.py failed" }
  git add today.json index.html
  git commit -m "daily: $(Get-Date -Format yyyy-MM-dd)"
  git push
  Log "ok"
} catch {
  Log "FAIL $_"
  exit 1
}
```

- [ ] **Step 4: Run it by hand once**

Run: `powershell -ExecutionPolicy Bypass -File daily.ps1`
Expected: build count, claude's one-line reply, `index.html written`, a push, and `ok` appended to `logs/daily.log`. Reload the Pages URL after a minute and confirm the new date.

- [ ] **Step 5: Register the scheduled task**

Run in PowerShell (as the user, not admin):

```powershell
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$PWD\daily.ps1`"" -WorkingDirectory "$PWD"
$trigger = New-ScheduledTaskTrigger -Daily -At 12:00
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
Register-ScheduledTask -TaskName "Intellia AI Watchlist" -Action $action -Trigger $trigger -Settings $settings
```

`-StartWhenAvailable` runs the job as soon as the laptop is on if noon was missed. Confirm with `Get-ScheduledTask -TaskName "Intellia AI Watchlist"` and, to test immediately, `Start-ScheduledTask -TaskName "Intellia AI Watchlist"` then check `logs/daily.log`.

- [ ] **Step 6: Write `README.md`**

```markdown
# Intellia AI Watchlist

A daily AI learning page for the Intellia team, published at https://<user>.github.io/intellia-ai-watchlist/.

- `sources.txt`: the feeds. One per line, `section url`. Edit freely.
- `editorial.md`: what gets picked and how it is written. Edit when the page drifts.
- `daily.ps1`: the noon job (fetch, curate with Claude Code, render, push). Runs from Task Scheduler as "Intellia AI Watchlist".
- `python test_watchlist.py`: the tests.

Run by hand: `powershell -ExecutionPolicy Bypass -File daily.ps1`. Failures are logged to `logs/daily.log`.
```

- [ ] **Step 7: Commit and push**

```bash
git add daily.ps1 README.md
git commit -m "feat: daily job script and readme"
git push
```

---

## Self-review

- Spec coverage: sources (T1), build and pool (T2), page tokens, layout, new marker, footer, accessibility (T3), brief, prompt, curation (T4), daily job, logging, Task Scheduler, Pages (T5). Error handling: per-feed warnings and total-failure exit (T2), render validation (T3), unchanged-today.json and non-zero exits stop the job (T5). Tests: all four spec test cases in T2 and T3.
- Placeholders: none; `<user>` is the GitHub username the user supplies.
- Consistency: `render(today, template, now=None, feed_count=0)` used identically in tests and `__main__`; `prune(items, now)` and parser names match between tests and `build.py`; section keys match across prompt, template ids and render.
