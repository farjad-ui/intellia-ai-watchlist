"""Run with: python test_watchlist.py"""

import sys

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

    (it,) = parse_feed(
        YT, "watch", "https://www.youtube.com/feeds/videos.xml?channel_id=x"
    )
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
    assert it["extra"] == {
        "points": 612,
        "comments": 300,
        "discussion": "https://news.ycombinator.com/item?id=1",
    }


def test_prune_window_and_dedupe():
    from build import parse_feed, prune

    old = RSS.replace("15 Oct 2026", "1 Oct 2026")
    items = (
        parse_feed(RSS, "m", "u")
        + parse_feed(RSS, "m", "u")
        + parse_feed(old, "m", "u")
    )
    out = prune(items, NOW)
    assert len(out) == 1


def test_decode_handles_gzip():
    import gzip
    from build import decode

    assert decode(gzip.compress("héllo".encode())) == "héllo"
    assert decode("plain".encode()) == "plain"


def test_load_sources_reads_optional_name():
    import os, tempfile
    from build import load_sources

    path = os.path.join(tempfile.mkdtemp(), "s.txt")
    lines = ["# c", "watch https://a  Fire ship", "models https://b"]
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    assert load_sources(path) == [
        ("watch", "https://a", "Fire ship"),
        ("models", "https://b", None),
    ]


TODAY = {
    "generated": "2026-10-16T07:00:00+00:00",
    "previous_generated": "2026-10-15T07:00:00+00:00",
    "date_label": "Friday 16 October 2026",
    "standfirst": "What is new this week.",
    "digest": ["First paragraph.", "Second <b>paragraph</b>."],
    "sections": [
        {
            "key": "watch",
            "title": "Watch",
            "items": [
                {
                    "title": "A <video>",
                    "url": "https://youtube.com/watch?v=1",
                    "source": "Fireship",
                    "published": "2026-10-16T01:00:00+00:00",
                    "summary": "Why it matters.",
                    "thumbnail": "https://i.ytimg.com/vi/1/mqdefault.jpg",
                },
                {
                    "title": "Old one",
                    "url": "https://youtube.com/watch?v=2",
                    "source": "Fireship",
                    "published": "2026-10-14T01:00:00+00:00",
                    "summary": "Older.",
                    "thumbnail": None,
                },
            ],
        }
    ],
}


def test_render_fills_template_and_escapes():
    from render import render

    out = render(
        TODAY,
        "$date_label|$digest|$sections|$legend|$updated|$feed_count",
        feed_count=24,
    )
    assert "Friday 16 October 2026" in out
    assert "Second &lt;b&gt;paragraph&lt;/b&gt;" in out
    assert "A &lt;video&gt;" in out
    assert 'src="https://i.ytimg.com/vi/1/mqdefault.jpg"' in out
    assert '<span class="new">6h</span>' in out  # newer than previous issue
    assert "Fireship · 2d" in out  # older item, plain age
    assert 'class="item video"' in out and 'class="item"' in out
    assert "16 October 2026 at 12:00" in out  # generated shown in Pakistan time
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


def test_render_drops_non_http_urls():
    import copy
    from render import render

    t = copy.deepcopy(TODAY)
    t["sections"][0]["items"][0]["url"] = "javascript:alert(1)"
    t["sections"][0]["items"][1]["thumbnail"] = "javascript:alert(2)"
    out = render(t, "$sections")
    assert "javascript:" not in out
    assert "A &lt;video&gt;" not in out  # item with a bad link is skipped
    assert "Old one" in out


def test_render_tolerates_sloppy_today_json():
    import copy
    from render import render

    t = copy.deepcopy(TODAY)
    t["previous_generated"] = "2026-10-15T07:00:00"  # no timezone
    t["sections"][0]["items"][0]["published"] = None  # missing date
    t["sections"][0]["items"][1]["published"] = "2026-10-14T01:00:00"
    out = render(t, "$sections")
    assert (
        "Fireship ·" not in out.split("Old one")[0].split("A &lt;video&gt;")[1]
    )  # no age shown
    assert "Fireship · 2d" in out


def test_render_rejects_digest_string():
    import copy
    from render import render

    t = copy.deepcopy(TODAY)
    t["digest"] = "one long string"
    try:
        render(t, "")
    except ValueError as e:
        assert "digest" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_render_computes_date_label():
    import copy
    from render import render

    t = copy.deepcopy(TODAY)
    del t["date_label"]
    assert render(t, "$date_label") == "Friday 16 October 2026"


def test_atom_prefers_alternate_link_and_prune_drops_empty_urls():
    from build import parse_feed, prune

    feed = YT.replace(
        '<link rel="alternate"',
        '<link rel="replies" href="https://x/replies"/>\n  <link rel="alternate"',
    )
    (it,) = parse_feed(feed, "watch", "u")
    assert it["url"] == "https://www.youtube.com/watch?v=QZVzuq28eFw"
    nolink = parse_feed(
        YT.replace(
            '<link rel="alternate" href="https://www.youtube.com/watch?v=QZVzuq28eFw"/>',
            "",
        ),
        "watch",
        "u",
    )
    assert prune(nolink, NOW) == []


def test_load_sources_skips_short_and_indented_lines():
    import os, tempfile
    from build import load_sources

    path = os.path.join(tempfile.mkdtemp(), "s.txt")
    open(path, "w", encoding="utf-8").write(
        "watch\n   # indented comment\nmodels https://b\n"
    )
    assert load_sources(path) == [("models", "https://b", None)]


def test_slack_message():
    from notify import slack_message

    import copy, json

    msg = slack_message(TODAY, "https://example.github.io/w/")
    assert (
        msg["text"]
        == "Intellia AI Watchlist · Friday 16 October: What is new this week."
    )
    assert msg["blocks"][0] == {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": "Intellia AI Watchlist · Friday 16 October",
        },
    }
    flat = json.dumps(msg["blocks"], ensure_ascii=False)
    assert "First paragraph." in flat  # opening digest paragraph
    assert "*Watch*" in flat
    assert "<https://youtube.com/watch?v=1|A &lt;video&gt;>" in flat
    assert "Why it matters. _Fireship_" in flat
    assert "<https://example.github.io/w/|Read the full issue>" in flat
    assert (
        msg["unfurl_links"] is False and msg["unfurl_media"] is False
    )  # no preview cards
    assert all(b["type"] != "context" for b in msg["blocks"])  # no small footnote text

    t = copy.deepcopy(TODAY)
    items = t["sections"][0]["items"]
    items[1]["url"] = "javascript:alert(1)"
    items += [dict(items[0], url=f"https://e.com/{n}") for n in range(4)]
    flat = json.dumps(slack_message(t, "u")["blocks"])
    assert "javascript:" not in flat
    assert flat.count("\\u2022") == 3  # three items per section at most


def run():
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    for t in tests:
        t()
        print(".", end="")
    print(f"\nok ({len(tests)} tests)")


if __name__ == "__main__":
    run()
