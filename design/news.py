"""Breaking news load, split out of build.py to keep that file within its file-line budget
(tests/test_budgets.py's PY_FILE_BACKLOG ratchet) once market_stock's re-keying needed the room.
Self-contained: takes the feed and ff-jarvis data-root paths as arguments instead of importing
build.py's FEED/DWR constants, so there is no import cycle back into build.py."""
import datetime as dt
import json

from slate import LOCAL_TZ, UTC


def load_news(feed_path, dwr_path):
    """Breaking news from ff-jarvis's own scanner (it watches FantasyPros' wire and writes
    data/breaking_news.json) -- feed first, then the file directly, same two-tier pattern as
    every other live read in build.py. `when` is reformatted the same way build.py's kickoff()
    does it, so a news row and a kickoff badge read as the same kind of timestamp."""
    raw = None
    try:
        d = json.loads(feed_path.read_text(encoding="utf-8"))
        block = ((d.get("market") or {}).get("news") or {}).get("data")
        if block and block.get("items"):
            raw = block
    except (OSError, json.JSONDecodeError):
        pass
    if raw is None:
        path = dwr_path / "breaking_news.json"
        if path.exists():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                raw = None
    if not raw or not raw.get("items"):
        return None
    # Sorted here, not trusted from the source or left to the client: the scanner's own file has
    # shuffled order before now, and a client-side sort would need the raw timestamp shipped
    # alongside the display string anyway. dt.min as the fallback key puts an unparseable date
    # last, never first.
    def parsed_time(it):
        try:
            return dt.datetime.strptime(it["created"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
        except (KeyError, TypeError, ValueError):
            return dt.datetime.min.replace(tzinfo=UTC)
    items = []
    for it in sorted(raw["items"], key=parsed_time, reverse=True):
        t = parsed_time(it)
        when = None if t == dt.datetime.min.replace(tzinfo=UTC) else (
            t.astimezone(LOCAL_TZ).strftime("%a %I:%M%p").replace(" 0", " ").replace("AM", "a").replace("PM", "p"))
        items.append({
            "id": it.get("id"), "title": it.get("title"), "desc": it.get("desc"),
            "impact": it.get("impact"), "team": it.get("team_id"),
            "categories": it.get("categories") or [], "link": it.get("link"), "when": when,
        })
    return {"items": items}
