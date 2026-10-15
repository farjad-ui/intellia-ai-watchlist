"""Render today.json through template.html into index.html.

today.json is written by an LLM from untrusted feed data, so everything here
is escaped, links must be http(s), and small format slips must not crash.

Run: python render.py
"""

import html
import json
import urllib.parse
from datetime import datetime, timedelta, timezone
from string import Template

from build import load_sources

PKT = timezone(timedelta(hours=5))  # ponytail: fixed offset, Pakistan has no DST
REQUIRED = ("generated", "standfirst", "digest", "sections")


def esc(s):
    return html.escape(str(s or ""), quote=True)


def safe_url(u):
    u = str(u or "").strip()
    return u if urllib.parse.urlsplit(u).scheme in ("http", "https") else ""


def parse(s):
    """ISO string to aware UTC datetime; None if missing or unreadable."""
    try:
        d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def age(published, now):
    minutes = int((now - published).total_seconds() // 60)
    if minutes < 60:
        return f"{max(minutes, 1)}m"
    if minutes < 1440:
        return f"{minutes // 60}h"
    return f"{minutes // 1440}d"


def render_item(it, now, prev):
    """Returns (html, is_new), or None when the item has no usable link."""
    url = safe_url(it.get("url"))
    if not url:
        return None
    published = parse(it.get("published")) if it.get("published") else None
    new = bool(prev and published and published > prev)
    meta = esc(it.get("source"))
    if published:
        a = age(published, now)
        meta += " · " + (f'<span class="new">{a}</span>' if new else a)
    cls, thumb = "item", ""
    thumbnail = safe_url(it.get("thumbnail"))
    if thumbnail:
        cls = "item video"
        thumb = (
            f'<a class="thumb" href="{esc(url)}" tabindex="-1" aria-hidden="true">'
            f'<img src="{esc(thumbnail)}" width="320" height="180" alt="" loading="lazy"></a>'
        )
    return (
        f'<li class="{cls}"><h3><a href="{esc(url)}">{esc(it.get("title"))}</a></h3>'
        f'<p>{esc(it.get("summary"))}</p><p class="meta">{meta}</p>{thumb}</li>\n'
    ), new


def render(today, template, now=None, feed_count=0):
    missing = [k for k in REQUIRED if k not in today]
    if missing:
        raise ValueError(f"today.json missing: {', '.join(missing)}")
    for k in ("digest", "sections"):
        if not isinstance(today[k], list):
            raise ValueError(f"today.json: {k} must be a list")
    generated = parse(today["generated"])
    if not generated:
        raise ValueError("today.json: generated is not an ISO date")
    now = now or generated
    prev = (
        parse(today["previous_generated"]) if today.get("previous_generated") else None
    )
    digest = "".join(f"<p>{esc(p)}</p>\n" for p in today["digest"])
    sections, any_new = "", False
    for s in today["sections"]:
        rows = [r for r in (render_item(i, now, prev) for i in s.get("items", [])) if r]
        if not rows:
            continue
        any_new = any_new or any(n for _, n in rows)
        key = esc(s.get("key"))
        sections += (
            f'<section id="{key}" aria-labelledby="{key}-h"><h2 id="{key}-h">{esc(s.get("title"))}</h2>'
            f'<ul class="items">\n{"".join(r for r, _ in rows)}</ul></section>\n'
        )
    legend = (
        '<p class="legend">Ages in blue are new since the last issue.</p>'
        if any_new
        else ""
    )
    gen = generated.astimezone(PKT)
    return Template(template).safe_substitute(
        date_label=f"{gen:%A} {gen.day} {gen:%B %Y}",
        standfirst=esc(today["standfirst"]),
        digest=digest,
        sections=sections,
        legend=legend,
        updated=f"{gen:%A} {gen.day} {gen:%B %Y} at {gen:%H:%M}",
        feed_count=feed_count,
    )


if __name__ == "__main__":
    with open("today.json", encoding="utf-8") as f:
        today = json.load(f)
    with open("template.html", encoding="utf-8") as f:
        template = f.read()
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(render(today, template, feed_count=len(load_sources())))
    print("index.html written")
