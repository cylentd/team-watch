"""Breaking news load, split out of build.py to keep that file within its file-line budget
(tests/test_budgets.py's PY_FILE_BACKLOG ratchet) once market_stock's re-keying needed the room.
Self-contained: takes the feed and ff-jarvis data-root paths as arguments instead of importing
build.py's FEED/DWR constants, so there is no import cycle back into build.py."""
import datetime as dt
import json
import re

from slate import LOCAL_TZ, UTC

# What a story means for a lineup, read off its own words, because FantasyPros tags almost nothing
# (13 of 200 items carried a category on 2026-09-16, so category filters showed empty lists).
# First match wins, most severe first. `injury` is the caution tier: a named soft-tissue or head
# injury, a questionable/doubtful tag, a missed practice. A limited or full practice with nothing
# worse in the story is `practice`, routine by design (David, 2026-09-16: "Limited in a practice
# report is common and not that serious", but a hamstring "might be serious").
KINDS = [
    ("out", r"\bruled out\b|\bout for\b|\bwill not play\b|\bwon't play\b|\binjured reserve\b|\bplaced on ir\b|"
            r"\bon ir\b|\bseason-ending\b|\btorn\b|\bsurgery\b|\bsuspended\b|\binactive\b|"
            r"\bout (?:sunday|monday|thursday|saturday|this week|week \d+)\b|\bnot expected to play\b|"
            r"(?<!not expected )\bto miss\b|\bremainder of (?:the )?season\b|\bfractured?\b|"
            r"\bout (?:several|multiple|a few|at least|\d+)\b"),
    # A missed practice is the caution tier -- unless the tag says it was a rest day.
    ("missed", r"\bdoes(?:n't| not) practice\b|\bdid not practice\b|\bmiss(?:es|ed)? practice\b|"
               r"\babsent from practice\b|\bnon-participant\b|\bsidelined at practice\b|\bnot practicing\b|\bdnp\b"),
    # Good news that names an injury is still routine: cleared, practicing, playing.
    ("cleared", r"\boff (?:the )?injury report\b|\bwithout (?:an )?injury designation\b|\bno injury designation\b|"
                r"\bnot expected to miss\b|(?<!not )\bpracticing\b|\blogs full practice\b|\bfull participant\b|"
                r"\bfull practice\b|\bwill play\b|(?<!not )\bexpected to play\b|\bactive for\b"),
    ("injury", r"\bquestionable\b|\bdoubtful\b|\bunlikely to play\b|\bexits?\b|\bmri\b|\bweek-to-week\b|"
               r"\bday-to-day\b|\bprotocol\b|\bconcussion\b|\bhamstring\b|\bachilles\b|\bacl\b|\bmcl\b|"
               r"\bhigh-ankle\b|\bgroin\b|\bcalf\b|\bquad\b|\bestimated to return\b|\btesting\b|"
               r"\bevaluated\b|\bmonitored\b|\bwalking boot\b|\bgame-time decision\b|\bsnap count\b|"
               r"\bsuffer(?:s|ed)?\b"),
    ("move", r"\bsigns?\b|\bsigned\b|\breleased?\b|\bwaived?\b|\btraded?\b|\bclaimed\b|\belevated\b|"
             r"\bpromoted\b|\bnamed (?:the )?starter\b|\bdepth chart\b|\bactivated\b|\bpractice squad\b"),
    ("practice", r"\blimited\b|\bpracticed?\b|\bpractice report\b"),
]
KIND_RE = [(k, re.compile(p, re.I)) for k, p in KINDS]
REST_DAY = re.compile(r"\(rest\b", re.I)


def news_kind(it):
    """out | injury | move | practice | news, from the title first, then the desc and impact."""
    for text in (it.get("title") or "", " ".join(filter(None, (it.get("desc"), it.get("impact"))))):
        for kind, rx in KIND_RE:
            if rx.search(text):
                if kind == "missed":
                    return "practice" if REST_DAY.search(it.get("title") or "") else "injury"
                return "practice" if kind == "cleared" else kind
    return "news"


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
            "kind": news_kind(it),
        })
    return {"items": items}
