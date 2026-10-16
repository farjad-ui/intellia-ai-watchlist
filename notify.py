"""Post today's issue to Slack through an incoming webhook.

The webhook URL lives in slack-webhook.txt (gitignored): anyone with it can post
to the channel. With no such file, this does nothing.

Run: python notify.py
"""

import json
import os
import sys
import urllib.request

from render import PKT, parse, safe_url

SITE = "https://farjad-ui.github.io/intellia-ai-watchlist/"
WEBHOOK_FILE = "slack-webhook.txt"
PER_SECTION = 3


def mrkdwn(s):
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def section_text(section, prev):
    """Top items, those new since the last issue first, as a Slack mrkdwn list."""
    items = [i for i in section.get("items", []) if safe_url(i.get("url"))]
    is_new = lambda i: bool(
        prev and parse(i.get("published") or "") and parse(i["published"]) > prev
    )
    items = sorted(items, key=lambda i: not is_new(i))[
        :PER_SECTION
    ]  # stable: keeps curated order
    if not items:
        return None
    lines = [f"*{mrkdwn(section.get('title'))}*"]
    for i in items:
        lines.append(
            f"• <{safe_url(i['url'])}|{mrkdwn(i.get('title'))}>\n"
            f"   {mrkdwn(i.get('summary'))} _{mrkdwn(i.get('source'))}_"
        )
    return "\n".join(lines)


def slack_message(today, site=SITE):
    gen = parse(today["generated"]).astimezone(PKT)
    title = f"Intellia AI Watchlist · {gen:%A} {gen.day} {gen:%B}"
    prev = (
        parse(today["previous_generated"]) if today.get("previous_generated") else None
    )
    md = lambda t: {"type": "section", "text": {"type": "mrkdwn", "text": t}}
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": title}},
        md(f"*{mrkdwn(today['standfirst'])}*"),
    ]
    if today.get("digest"):
        blocks.append(md(mrkdwn(today["digest"][0])))
    for s in today["sections"]:
        text = section_text(s, prev)
        if text:
            blocks += [{"type": "divider"}, md(text)]
    blocks += [
        {"type": "divider"},
        md(
            f"*<{site}|Read the full issue>* for the whole week's digest and every pick."
        ),
    ]
    # no preview cards: one per YouTube link would bury the text
    return {
        "text": f"{title}: {today['standfirst']}",
        "blocks": blocks,
        "unfurl_links": False,
        "unfurl_media": False,
    }


if __name__ == "__main__":
    if not os.path.exists(WEBHOOK_FILE):
        print("no slack-webhook.txt, skipping Slack")
        sys.exit(0)
    url = open(WEBHOOK_FILE, encoding="utf-8").read().strip()
    with open("today.json", encoding="utf-8") as f:
        body = json.dumps(slack_message(json.load(f))).encode()
    req = urllib.request.Request(url, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        print("slack:", r.read().decode())
