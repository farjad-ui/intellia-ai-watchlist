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
