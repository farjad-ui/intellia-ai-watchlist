"""Post today's issue to Slack through an incoming webhook.

The webhook URL lives in slack-webhook.txt (gitignored): anyone with it can post
to the channel. With no such file, this does nothing.

Run: python notify.py
"""

import json
import os
import sys
import urllib.request

from render import PKT, parse

SITE = "https://farjad-ui.github.io/intellia-ai-watchlist/"
WEBHOOK_FILE = "slack-webhook.txt"


def mrkdwn(s):
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def slack_message(today, site=SITE):
    gen = parse(today["generated"]).astimezone(PKT)
    return {
        "text": (
            f"*Intellia AI Watchlist · {gen:%A} {gen.day} {gen:%B}*\n"
            f"{mrkdwn(today['standfirst'])}\n"
            f"<{site}|Read today's issue>"
        )
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
