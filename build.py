"""Fetch every feed in sources.txt and write pool.json (items from the last 7 days).

Run: python build.py
"""

import gzip
import hashlib
import html
import json
import re
import sys
import time
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


def decode(body):
    if body[:2] == bytes(
        [0x1F, 0x8B]
    ):  # gzip magic; some servers compress even when not asked
        body = gzip.decompress(body)
    return body.decode("utf-8", "replace")


def fetch(url):
    if "reddit.com" in url:
        time.sleep(3)  # reddit returns 429 to back-to-back requests
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return decode(r.read())


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


def item(
    section, title, url, source, published, summary="", thumbnail=None, extra=None
):
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
    return clean(feed_title, 60) or re.sub(
        r"^www\.", "", urllib.parse.urlparse(url).netloc
    )


def parse_feed(text, section, url):
    root = ET.fromstring(text)
    items = []
    if root.tag.endswith("feed"):  # Atom: YouTube, Reddit, GitHub
        source = source_name(url, root.findtext("a:title", "", NS))
        for e in root.findall("a:entry", NS):
            link = next(
                (
                    l
                    for l in e.findall("a:link", NS)
                    if l.get("rel", "alternate") == "alternate"
                ),
                None,
            )
            href = (link.get("href") if link is not None else "").strip()
            vid = e.findtext("yt:videoId", "", NS)
            thumb = f"https://i.ytimg.com/vi/{vid}/mqdefault.jpg" if vid else None
            summary = (
                e.findtext("m:group/m:description", "", NS)
                or e.findtext("a:summary", "", NS)
                or e.findtext("a:content", "", NS)
            )
            when = e.findtext("a:published", "", NS) or e.findtext("a:updated", "", NS)
            items.append(
                item(
                    section,
                    e.findtext("a:title", "", NS),
                    href,
                    source,
                    parse_date(when),
                    summary,
                    thumb,
                )
            )
    else:  # RSS 2.0
        ch = root.find("channel")
        source = source_name(url, ch.findtext("title", ""))
        for e in ch.findall("item"):
            items.append(
                item(
                    section,
                    e.findtext("title", ""),
                    (e.findtext("link") or "").strip(),
                    source,
                    parse_date(e.findtext("pubDate", "")),
                    e.findtext("description", ""),
                )
            )
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
        out.append(
            item(
                section,
                repo,
                f"https://github.com/{repo}",
                "GitHub trending",
                now,
                desc.group(1) if desc else "",
                extra={
                    "stars_today": int(stars.group(1).replace(",", ""))
                    if stars
                    else None
                },
            )
        )
    return out


def parse_hn(text, section):
    out = []
    for h in json.loads(text)["hits"]:
        discussion = f"https://news.ycombinator.com/item?id={h['objectID']}"
        out.append(
            item(
                section,
                h.get("title") or "",
                h.get("url") or discussion,
                "Hacker News",
                parse_date(h.get("created_at")),
                "",
                extra={
                    "points": h.get("points"),
                    "comments": h.get("num_comments"),
                    "discussion": discussion,
                },
            )
        )
    return out


def load_sources(path="sources.txt"):
    """Lines of 'section url [display name]'; returns (section, url, name or None)."""
    rows = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 2)
        if len(parts) < 2:
            print(f"warning: sources.txt: no url in {line!r}", file=sys.stderr)
            continue
        section, url, *name = parts
        rows.append((section, url, name[0].strip() if name else None))
    return rows


def collect(pairs, now):
    items = []
    for section, url, name in pairs:
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
        if name:
            for it in new:
                it["source"] = name
        items += new
    return items


def prune(items, now):
    seen, out = set(), []
    for it in sorted(items, key=lambda i: i["published"] or "", reverse=True):
        if (
            not it["published"]
            or now - datetime.fromisoformat(it["published"]) > WINDOW
        ):
            continue
        if not it["url"] or it["url"] in seen:
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
        json.dump(
            {"built": now.isoformat(), "items": pool}, f, indent=1, ensure_ascii=False
        )
    sources = sorted(set(i["source"] for i in pool))
    print(f"{len(pool)} items from {len(sources)} sources -> pool.json")
