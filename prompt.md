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
