"""api/clips.py, driven through its handler with a fake request and a mocked urlopen (2026-10-05).

Nothing here touches the network: urllib.request.urlopen is replaced, and a test that reached
YouTube would fail on the fake's own assertion."""
import datetime
import importlib.util
import io
import json
import pathlib
import types
import urllib.error

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent
KEY = "test-key-NOT-A-REAL-ONE"
NOW = datetime.datetime(2026, 10, 5, 20, 0, tzinfo=datetime.timezone.utc)
FAIL_CACHE = "public, max-age=0, s-maxage=60"       # a 502: kept a minute, so a failure is not retried every round


def stamp(hours_ago):
    return (NOW - datetime.timedelta(hours=hours_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


@pytest.fixture
def clips(monkeypatch):
    spec = importlib.util.spec_from_file_location("clips_fn", REPO / "api" / "clips.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setenv("YOUTUBE_DATA_API_KEY", KEY)

    class Frozen(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return NOW

    # The module's own `datetime` name only; the real module is left alone.
    monkeypatch.setattr(mod, "datetime", types.SimpleNamespace(
        datetime=Frozen, timedelta=datetime.timedelta, timezone=datetime.timezone))
    return mod


class Reply:
    def __init__(self, body, status=200):
        self.body, self.status = json.dumps(body).encode(), status

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class Upstream:
    """A urlopen stand-in: answers by endpoint and keeps every request it was asked."""

    def __init__(self, listing=None, detail=None, fail=None):
        self.listing, self.detail, self.fail, self.seen = listing, detail, fail, []

    def __call__(self, req, timeout=None):
        self.seen.append((req, timeout))
        assert req.full_url.startswith("https://www.googleapis.com/youtube/v3/"), req.full_url
        if self.fail:
            raise self.fail
        return Reply(self.listing if "/playlistItems?" in req.full_url else self.detail)


def item(vid, hours_ago, title=None):
    return {"contentDetails": {"videoId": vid, "videoPublishedAt": stamp(hours_ago)},
            "snippet": {"title": title or f"title {vid}"}}


def video(vid, duration, w=480, h=270):
    return {"id": vid, "contentDetails": {"duration": duration},
            "player": {"embedWidth": str(w), "embedHeight": str(h)}}


def get(mod, path, monkeypatch, upstream):
    """Run the handler for `path`; returns (status, headers, body dict)."""
    monkeypatch.setattr(mod.urllib.request, "urlopen", upstream)
    h = mod.handler.__new__(mod.handler)
    h.path, h.request_version, h.requestline = path, "HTTP/1.1", f"GET {path} HTTP/1.1"
    h.client_address, h.wfile = ("test", 0), io.BytesIO()
    h.do_GET()
    head, _, body = h.wfile.getvalue().partition(b"\r\n\r\n")
    lines = head.decode().split("\r\n")
    headers = dict(line.split(": ", 1) for line in lines[1:])
    return int(lines[0].split()[1]), headers, json.loads(body)


def test_good_path_filters_sorts_and_flags(clips, monkeypatch):
    up = Upstream(
        listing={"items": [item("old", 31), item("short", 2), item("long", 1), item("tall", 5),
                           item("newest", 0.5), item("gone", 3)]},
        detail={"items": [video("short", "PT1M5S"), video("long", "PT3M1S"),
                          video("tall", "PT45S", 405, 720), video("newest", "PT3M")]})
    status, headers, body = get(clips, "/api/clips?ch=SEA", monkeypatch, up)
    assert status == 200
    assert headers["Cache-Control"] == "public, max-age=0, s-maxage=300, stale-while-revalidate=60"
    assert headers["Content-Type"] == "application/json"
    assert body["ch"] == "SEA"
    got = [(c["id"], c["secs"], c["shape"]) for c in body["clips"]]
    assert got == [("newest", 180, "wide"), ("short", 65, "wide"), ("tall", 45, "tall")]
    assert [c["posted"] for c in body["clips"]] == [stamp(0.5), stamp(2), stamp(5)]
    assert body["clips"][1]["title"] == "title short"
    assert all(c["embed"] is False for c in body["clips"])          # SEA is blocked in ff-jarvis's file
    url = up.seen[1][0].full_url                                    # one videos call, the last 30 h only
    assert "id=short%2Clong%2Ctall%2Cnewest%2Cgone" in url
    assert "maxHeight=720" in url and "part=contentDetails%2Cplayer" in url
    assert len(up.seen) == 2


def test_embed_flag_comes_from_the_channel_file(clips, monkeypatch):
    up = Upstream(listing={"items": [item("a", 1)]}, detail={"items": [video("a", "PT10S")]})
    assert get(clips, "/api/clips?ch=PHI", monkeypatch, up)[2]["clips"][0]["embed"] is True


def test_playlist_is_the_uploads_playlist_with_50_items(clips, monkeypatch):
    up = Upstream(listing={"items": []})
    status, _, body = get(clips, "/api/clips?ch=NFL", monkeypatch, up)
    assert (status, body) == (200, {"ch": "NFL", "clips": []})
    assert len(up.seen) == 1                                          # nothing fresh: no videos call
    url = up.seen[0][0].full_url
    assert f"playlistId={clips.CHANNELS['NFL']['uploads']}" in url
    assert "maxResults=50" in url and "playlistItems" in url


def test_the_key_goes_in_a_header_only_and_calls_time_out(clips, monkeypatch):
    up = Upstream(listing={"items": [item("a", 1)]}, detail={"items": [video("a", "PT10S")]})
    get(clips, "/api/clips?ch=PHI", monkeypatch, up)
    for req, timeout in up.seen:
        assert req.get_header("X-goog-api-key") == KEY
        assert KEY not in req.full_url and "key=" not in req.full_url
        assert timeout is not None and timeout <= 8


@pytest.mark.parametrize("path", ["/api/clips", "/api/clips?ch=", "/api/clips?ch=XXX", "/api/clips?ch=sea"])
def test_unknown_or_missing_channel_is_400_no_store(clips, monkeypatch, path):
    up = Upstream()
    status, headers, _ = get(clips, path, monkeypatch, up)
    assert status == 400 and headers["Cache-Control"] == "no-store"
    assert up.seen == []


def test_missing_key_is_503_no_store(clips, monkeypatch):
    monkeypatch.delenv("YOUTUBE_DATA_API_KEY")
    up = Upstream()
    status, headers, _ = get(clips, "/api/clips?ch=SEA", monkeypatch, up)
    assert status == 503 and headers["Cache-Control"] == "no-store"
    assert up.seen == []


@pytest.mark.parametrize("fail", [
    urllib.error.HTTPError("https://x", 403, f"quota {KEY}", {}, io.BytesIO(b"secret youtube body")),
    urllib.error.URLError("down"),
    TimeoutError("slow"),
])
def test_youtube_trouble_is_502_kept_a_minute_and_leaks_nothing(clips, monkeypatch, capsys, fail):
    status, headers, body = get(clips, "/api/clips?ch=SEA", monkeypatch, Upstream(fail=fail))
    assert status == 502 and headers["Cache-Control"] == FAIL_CACHE
    text = json.dumps(body)
    assert KEY not in text and "secret youtube body" not in text and "quota" not in text
    assert KEY not in capsys.readouterr().out


def test_a_non_2xx_reply_is_502(clips, monkeypatch):
    class Bad(Upstream):
        def __call__(self, req, timeout=None):
            return Reply({"error": "nope"}, status=500)
    status, headers, _ = get(clips, "/api/clips?ch=SEA", monkeypatch, Bad())
    assert status == 502 and headers["Cache-Control"] == FAIL_CACHE


def test_second_call_failing_is_502(clips, monkeypatch):
    class Half(Upstream):
        def __call__(self, req, timeout=None):
            if "/videos?" in req.full_url:
                raise urllib.error.URLError("down")
            return super().__call__(req, timeout)
    status, headers, _ = get(clips, "/api/clips?ch=SEA", monkeypatch,
                             Half(listing={"items": [item("a", 1)]}))
    assert status == 502 and headers["Cache-Control"] == FAIL_CACHE


def test_a_failure_is_kept_60_seconds_at_the_edge_never_the_good_reply_s_five_minutes(clips, monkeypatch):
    """A quota-spent 403 must not be retried by every reader every round; 400 and 503 stay no-store."""
    bad = Upstream(fail=urllib.error.HTTPError("https://x", 403, "quota", {}, io.BytesIO(b"")))
    _, headers, _ = get(clips, "/api/clips?ch=SEA", monkeypatch, bad)
    assert headers["Cache-Control"] == "public, max-age=0, s-maxage=60"
    assert "s-maxage=300" not in headers["Cache-Control"] and "stale-while-revalidate" not in headers["Cache-Control"]
    assert get(clips, "/api/clips?ch=XXX", monkeypatch, Upstream())[1]["Cache-Control"] == "no-store"
    monkeypatch.delenv("YOUTUBE_DATA_API_KEY")
    assert get(clips, "/api/clips?ch=SEA", monkeypatch, Upstream())[1]["Cache-Control"] == "no-store"


def test_duration_and_shape_parsing(clips):
    assert clips.parse_duration("PT1M5S") == 65
    assert clips.parse_duration("PT45S") == 45
    assert clips.parse_duration("PT1H") == 3600
    assert clips.parse_duration("P0D") is None and clips.parse_duration(None) is None
    assert clips.shape_of({"embedWidth": "100", "embedHeight": "120"}) == "wide"   # not over 1.2x
    assert clips.shape_of({"embedWidth": "100", "embedHeight": "121"}) == "tall"
    assert clips.shape_of(None) == "wide"


def test_requirements_stay_stdlib_only():
    reqs = (REPO / "requirements.txt").read_text(encoding="utf-8")
    lines = [ln for ln in reqs.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    assert [ln.split(">")[0].split("=")[0] for ln in lines] == ["anthropic"]
