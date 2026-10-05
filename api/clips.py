"""Official team clips for Live > TDs. GET /api/clips?ch=SEA  (a nflverse team code, or NFL)

The page asks this function, never YouTube. Vercel's edge keeps a good reply for CACHE_S, so every
reader in a region shares one YouTube call per channel per five minutes: 2 quota units each
(playlistItems.list and videos.list cost 1 apiece), against a 10,000-unit daily default.

A reply: {"ch", "clips": [{id, title, posted (ISO UTC), secs, shape "tall"|"wide", embed}]}, newest
first: uploads of the last WINDOW_H hours that run MAX_SECS or less. `embed` is false for the
channels that refuse a player on our site (api/_yt_channels.json, written by design/yt_channels.py
from ff-jarvis), so the page links out instead.

The key is YOUTUBE_DATA_API_KEY, sent as the X-Goog-Api-Key header, never in a URL (URLs land in
logs). A 502 (YouTube or the network failed, quota spent included) is kept at the edge for FAIL_S, so
a failure is not retried by every reader every round and outlives its cause by one minute at most; 400
unknown channel and 503 no key are never cached. Neither the key nor YouTube's error body is ever echoed.
"""
import datetime
import json
import os
import re
import urllib.parse
import urllib.request

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

API = "https://www.googleapis.com/youtube/v3"
CACHE_S = 300
SWR_S = 60
FAIL_S = 60
CACHE_CONTROL = {"ok": f"public, max-age=0, s-maxage={CACHE_S}, stale-while-revalidate={SWR_S}",
                 "fail": f"public, max-age=0, s-maxage={FAIL_S}"}
TIMEOUT_S = 8
WINDOW_H = 30
MAX_SECS = 180
TALL_RATIO = 1.2
KEY_ENV = "YOUTUBE_DATA_API_KEY"
CHANNELS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_yt_channels.json")
DURATION = re.compile(r"^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$")


class KeyMissing(Exception):
    """No YOUTUBE_DATA_API_KEY in the environment."""


def load_channels():
    with open(CHANNELS_FILE, encoding="utf-8") as f:
        return json.load(f)


CHANNELS = load_channels()


def _get(path, params):
    """One YouTube call -> parsed JSON. Raises on any network error or non-2xx; the key rides in a header."""
    key = os.environ.get(KEY_ENV)
    if not key:
        raise KeyMissing()
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"X-Goog-Api-Key": key, "Accept": "application/json",
                                               "User-Agent": "team-watch/1"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
        status = getattr(r, "status", 200)
        if not 200 <= status < 300:
            raise OSError(f"YouTube answered {status}")
        return json.loads(r.read())


def parse_time(text):
    """YouTube's RFC 3339 stamp -> aware UTC datetime, or None."""
    try:
        return datetime.datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(datetime.timezone.utc)
    except (AttributeError, ValueError):
        return None


def parse_duration(text):
    """ISO 8601 "PT1M5S" -> seconds, or None when it is not one."""
    m = DURATION.match(text or "")
    if not m or not any(m.groups()):
        return None
    h, mi, s = (int(g or 0) for g in m.groups())
    return h * 3600 + mi * 60 + s


def shape_of(player):
    """"tall" when the embed is taller than TALL_RATIO x its width (a Short), else "wide"."""
    try:
        w, h = float(player["embedWidth"]), float(player["embedHeight"])
    except (KeyError, TypeError, ValueError):
        return "wide"
    return "tall" if h > TALL_RATIO * w else "wide"


def recent_uploads(items, now):
    """playlistItems -> [(id, title, posted datetime)] posted within WINDOW_H of `now`."""
    cutoff = now - datetime.timedelta(hours=WINDOW_H)
    out = []
    for it in items or []:
        cd = it.get("contentDetails") or {}
        posted = parse_time(cd.get("videoPublishedAt"))
        if cd.get("videoId") and posted and cutoff <= posted <= now + datetime.timedelta(minutes=5):
            out.append((cd["videoId"], (it.get("snippet") or {}).get("title") or "", posted))
    return out


def clips(code, now=None):
    """The channel's short recent uploads, newest first. Raises on a YouTube failure."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    chan = CHANNELS[code]
    listing = _get("playlistItems", {"part": "contentDetails,snippet", "maxResults": 50,
                                     "playlistId": chan["uploads"]})
    fresh = recent_uploads(listing.get("items"), now)
    out = []
    if fresh:
        detail = _get("videos", {"part": "contentDetails,player", "maxHeight": 720,
                                 "id": ",".join(vid for vid, _, _ in fresh)})
        by_id = {v.get("id"): v for v in detail.get("items") or []}
        for vid, title, posted in fresh:
            v = by_id.get(vid)
            secs = parse_duration(((v or {}).get("contentDetails") or {}).get("duration"))
            if v is None or secs is None or secs > MAX_SECS:
                continue
            out.append({"id": vid, "title": title, "posted": posted.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "secs": secs, "shape": shape_of(v.get("player")), "embed": bool(chan.get("embed"))})
    out.sort(key=lambda c: c["posted"], reverse=True)
    return {"ch": code, "clips": out}


class handler(BaseHTTPRequestHandler):

    def _send(self, code, payload, cache=None):
        """cache: "ok" (a good reply), "fail" (YouTube trouble, kept briefly) or None (no-store)."""
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", CACHE_CONTROL.get(cache, "no-store"))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        code = (parse_qs(urlparse(self.path).query).get("ch") or [""])[0]
        if code not in CHANNELS:
            return self._send(400, {"error": "ch must be a team code or NFL."})
        try:
            self._send(200, clips(code), cache="ok")
        except KeyMissing:
            print("clips: YOUTUBE_DATA_API_KEY is not set")
            self._send(503, {"error": "Clips are not set up."})
        except Exception as exc:                                       # noqa: BLE001
            # The type and status only: an HTTPError's body is YouTube's, and is never ours to repeat.
            print(f"clips: {type(exc).__name__} {getattr(exc, 'code', '')}")
            self._send(502, {"error": "Could not reach YouTube. Trying again."}, cache="fail")

    def log_message(self, fmt, *args):
        """Vercel already logs the request line; this would double every entry."""
