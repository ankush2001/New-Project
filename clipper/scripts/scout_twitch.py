#!/usr/bin/env python3
"""scout_twitch.py - top clips in a game category from the last N hours (Twitch Helix API).

Needs env vars TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET (free Twitch developer app) and network
access to api.twitch.tv / id.twitch.tv (add them to the allowed domains). Never prints the secret.

  python3 scout_twitch.py ["Grand Theft Auto VI"] [--hours 24] [--first 50] [--lang en] [--out scout.json]

Writes a JSON list sorted by views: url (FULL clip url, use it with yt-dlp), title, broadcaster,
creator, views, created_at, duration, language. Titles are NOT proof: contact-sheet every pick.
"""
import json, os, sys, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone


def call(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def opt(a, k, d):
    return a[a.index(k) + 1] if k in a else d


def main():
    a = sys.argv[1:]
    game = a[0] if a and not a[0].startswith("--") else "Grand Theft Auto VI"
    hours, first = float(opt(a, "--hours", 24)), int(opt(a, "--first", 50))
    lang, out = opt(a, "--lang", "en"), opt(a, "--out", "scout.json")
    cid, sec = os.environ.get("TWITCH_CLIENT_ID"), os.environ.get("TWITCH_CLIENT_SECRET")
    if not cid or not sec:
        sys.exit("set TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET first")
    tok = call("https://id.twitch.tv/oauth2/token", urllib.parse.urlencode(
        {"client_id": cid, "client_secret": sec, "grant_type": "client_credentials"}).encode())["access_token"]
    H = {"Client-Id": cid, "Authorization": f"Bearer {tok}"}
    g = call("https://api.twitch.tv/helix/games?" + urllib.parse.urlencode({"name": game}), headers=H)["data"]
    if not g:
        sys.exit(f"no Twitch category named {game!r}")
    start = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    clips, cursor = [], None
    while len(clips) < first * 3:
        q = {"game_id": g[0]["id"], "started_at": start, "first": 100}
        if cursor:
            q["after"] = cursor
        r = call("https://api.twitch.tv/helix/clips?" + urllib.parse.urlencode(q), headers=H)
        clips += r["data"]
        cursor = r.get("pagination", {}).get("cursor")
        if not cursor:
            break
    keep = [c for c in clips if not lang or c.get("language", "").startswith(lang)]
    keep.sort(key=lambda c: -c["view_count"])
    res = [{"url": c["url"], "title": c["title"], "broadcaster": c["broadcaster_name"],
            "creator": c["creator_name"], "views": c["view_count"], "created_at": c["created_at"],
            "duration": c["duration"], "language": c.get("language")} for c in keep[:first]]
    json.dump(res, open(out, "w"), indent=1)
    for c in res[:20]:
        print(f"{c['views']:>7}  {c['created_at']}  {c['broadcaster']:<18} {c['title'][:60]}")
    print(f"\n{len(res)} clips -> {out}")


if __name__ == "__main__":
    main()
