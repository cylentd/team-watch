"""Breaking news load, split out of build.py to keep that file within its file-line budget
(tests/test_budgets.py's PY_FILE_BACKLOG ratchet) once market_stock's re-keying needed the room.
Self-contained: takes the feed and ff-jarvis data-root paths as arguments instead of importing
build.py's FEED/DWR constants, so there is no import cycle back into build.py."""
import datetime as dt
import json
import pathlib
import re
import sys

from slate import LOCAL_TZ, UTC

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "api"))
from _espn import slugify  # noqa: E402

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
# A later story that undoes an earlier `out` one: he is back, cleared, active or on the report no more.
# `active` alone would match "inactive" and "active roster", so it is `active for` / `activated`.
RETURN_RE = re.compile(
    r"\bcleared\b|\bwill play\b|(?<!not )\bexpected to play\b|(?<!in)\bactive for\b|\bactivated\b|"
    r"\bremoved from (?:the )?injury report\b|\boff (?:the )?injury report\b|"
    r"\breturns\b|\breturned\b|\bgood to go\b|\bfull practice\b|\bfull participant\b", re.I)
NOT_BACK_RE = re.compile(r"\bruled out\b|\bwon't play\b|\bwill not play\b|\bnot expected to play\b|"
                         r"\bdoubtful\b|\bunlikely to play\b|\bnot cleared\b|\bsuspended\b|\bplaced on\b", re.I)


# The game-day word a headline states (ledger #95, 2026-10-09: News as an injury report), most final first;
# the first match wins. "Not ruled out" is not Out. A practice line gives that day's participation: dnp,
# limited or full. Read off the headline only: the desc and the read restate it or speculate.
GAME_WORDS = [
    ("out", r"(?<!not )\bruled out\b|\bwill not play\b|\bwon't play\b|\bout (?:sunday|monday|thursday|against|for)\b|"
            r"\bnot expected to play\b|\bplaced on\b|\bexpected to return in week\b"),
    ("doubtful", r"\bdoubtful\b"),
    ("questionable", r"\bquestionable\b|\bgame-time decision\b"),
    ("cleared", r"\boff (?:the )?injury report\b|\bwill play\b|\bready to go\b|\bwill start\b|\bexpected to play\b|"
                r"\bfull go\b|\bremoved from\b"),
    ("dnp", r"\bdoes(?:n't| not) practice\b|\bnot practicing\b|\bnon-participant\b|\bdnp\b|\bmiss(?:es|ed)? practice\b|"
            r"\bnot (?:seen|spotted) (?:at )?practic|\babsent from practice\b|\bnot at practice\b|\bmisses another\b"),
    ("limited", r"\blimited\b|\bworking to side\b|\bin pads\b"),
    ("full", r"\bfull\b|\bpractices\b|\bpracticing\b|\bat practice\b|\breturns to practice\b|\bparticipating\b|"
             r"\bback at practice\b"),
]
GAME_RE = [(k, re.compile(p, re.I)) for k, p in GAME_WORDS]
PRACTICE_WORDS = ("dnp", "limited", "full")
PRACTICE_DAY_RE = re.compile(r"\b(Wed|Thu|Fri)(?:nesday|rsday|day)\b")
# Sleeper's injury designation as a game-day word: what the page shows when no story states one.
SLEEPER_WORD = {"Out": "out", "IR": "out", "PUP": "out", "DNR": "out", "Doubtful": "doubtful",
                "Questionable": "questionable"}
REPORT_POS = ("QB", "RB", "WR", "TE")   # the positions the leagues start and the report follows
NEXT_UP_MAX = 2                         # teammates a ruled-out story names as next up; the scanner's read names two at most in practice


def game_status(title):
    """out | doubtful | questionable | cleared | dnp | limited | full | None, from the headline's words."""
    for word, rx in GAME_RE:
        if rx.search(title or ""):
            return word
    return None


def practice_day(title, status):
    """Wed | Thu | Fri for a practice line (status dnp, limited or full), else None."""
    m = PRACTICE_DAY_RE.search(title or "") if status in PRACTICE_WORDS else None
    return m.group(1) if m else None


def news_people(status, slugify):
    """slug -> {n, pos, team, injury} for every QB, RB, WR and TE Sleeper tracks; injury is SLEEPER_WORD's word."""
    return {slugify(p["name"]): {"n": p["name"], "pos": p.get("pos"), "team": p.get("team"),
                                 "injury": SLEEPER_WORD.get(p.get("injury"))}
            for p in (status or {}).values() if p.get("name") and p.get("pos") in REPORT_POS}


def _about(item, people, names):
    for s in item.get("slugs") or []:
        if s in people:
            return s
    title = (item.get("title") or "").lower()
    return next((s for n, s in names if title.startswith(n + " ") or title.startswith(n + "'")), None)


def _next_up(item, own, people, names):
    """The teammates the scanner's read names, in its order: the next man up when his starter is out."""
    if not own or game_status(item.get("title")) != "out":
        return []
    text, team = (item.get("impact") or "").lower(), people[own]["team"]
    hits = sorted((text.find(n), s) for n, s in names
                  if s != own and people[s]["team"] == team and text.find(n) >= 0)
    seen = []
    for _, s in hits:
        if s not in seen:
            seen.append(s)
    return seen[:NEXT_UP_MAX]


# ff-jarvis's practice report (feed block `practice_report`, its `model.season.practice_report`, 2026-10-09).
PRACTICE_KEYS = ("generated", "season", "week", "dates", "source", "note", "players")
PRACTICE_ROW = ("name", "slug", "team", "pos", "days", "status", "injury")
PRACTICE_MARK = {"DNP": "dnp", "LP": "limited", "FP": "full", None: None}   # its marks in the page's words
PRACTICE_DAYS = {"wed": "Wed", "thu": "Thu", "fri": "Fri"}


def check_practice_report(raw):
    """Raise ValueError naming the first field the report lacks or gets wrong: the build fails, not the page."""
    missing = [k for k in PRACTICE_KEYS if k not in raw]
    if missing:
        raise ValueError(f"practice_report: missing {missing}")
    for i, r in enumerate(raw["players"]):
        lacks = [k for k in PRACTICE_ROW if k not in r]
        if lacks:
            raise ValueError(f"practice_report: players[{i}] missing {lacks}")
        days = r["days"] or {}
        if set(days) != set(PRACTICE_DAYS):
            raise ValueError(f"practice_report: players[{i}] days {sorted(days)}, wants {sorted(PRACTICE_DAYS)}")
        bad = [m for m in days.values() if m not in PRACTICE_MARK]
        if bad:
            raise ValueError(f"practice_report: players[{i}] marks {bad}")
    return raw


def _with_practice(people, practice, slugify):
    """people with each reported QB/RB/WR/TE's days and status: `days` {Wed, Thu, Fri: dnp|limited|full|None},
    `injury` the report's status as a game-day word (else Sleeper's), `report` True."""
    for r in practice["players"]:
        if r.get("pos") not in REPORT_POS:
            continue
        s = slugify(r["name"])
        base = people.get(s) or {"n": r["name"], "pos": r["pos"], "team": r["team"], "injury": None}
        people[s] = {**base, "injury": SLEEPER_WORD.get(r["status"]) or base["injury"],
                     "days": {PRACTICE_DAYS[d]: PRACTICE_MARK[m] for d, m in r["days"].items()}, "report": True}
    return people


def news_report(news, status, slugify, practice=None):
    """LIVE_NEWS with the report's fields: each item's `slug` (the fantasy player it is about, or None),
    `status` (game_status), `day` (practice_day) and `next` (teammates named as next up), and `players`,
    the facts the page draws for each slug named and for each player ff-jarvis's practice report lists
    (`practice`, checked by check_practice_report; its `note` passes through). None without news."""
    if not news:
        return None
    people = news_people(status, slugify)
    if practice:
        people = _with_practice(people, check_practice_report(practice), slugify)
    names = sorted(((p["n"].lower(), s) for s, p in people.items()), key=lambda x: -len(x[0]))  # nomutate: longest name first; a slug is the same name less punctuation, so its length orders them alike
    items = []
    for it in news["items"]:
        own = _about(it, people, names)
        word = game_status(it.get("title"))
        items.append({**it, "slug": own, "status": word, "day": practice_day(it.get("title"), word),
                      "next": _next_up(it, own, people, names)})
    named = {s for it in items for s in [it["slug"], *it["next"]] if s} | {s for s, p in people.items() if p.get("report")}
    out = {**news, "items": items, "players": {s: people[s] for s in sorted(named)}}
    if practice:
        out["practice"] = {"note": practice["note"]}
    return out


def news_kind(it):
    """out | injury | move | practice | news, from the title first, then the desc and impact."""
    for text in (it.get("title") or "", " ".join(filter(None, (it.get("desc"), it.get("impact"))))):
        for kind, rx in KIND_RE:
            if rx.search(text):
                if kind == "missed":
                    return "practice" if REST_DAY.search(it.get("title") or "") else "injury"
                return "practice" if kind == "cleared" else kind
    return "news"


def is_return(it):
    """True when the story says the player is back: a return pattern in its title (or, when the title is
    silent, its desc and impact) and nothing in the same text that says he is still out."""
    for text in (it.get("title") or "", " ".join(filter(None, (it.get("desc"), it.get("impact"))))):
        if RETURN_RE.search(text):
            return not NOT_BACK_RE.search(text)
    return False


def mark_superseded(items):
    """Set `superseded` on every `out` story that a later story for the same player undoes. `items` run
    newest first (load_news sorts them), so a story's later ones are those before it in the list. Two
    stories are one player's when their slug candidates share one. The page's lead pin skips a
    superseded story; the row stays in the list."""
    for i, it in enumerate(items):
        it["superseded"] = it["kind"] == "out" and (is_return(it) or any(
            is_return(later) and set(later["slugs"]) & set(it["slugs"]) for later in items[:i]))
    return items


def news_player(title):
    """(name, slugs) for the player a story leads with. The scanner names no player (only
    FantasyPros' own id), but its titles lead with one: "Cooper Kupp (back) practices fully".
    `name` is the text before that injury tag, so it is None for a title without one; the page
    draws initials from it when no head matches. `slugs` run four words down to two, longest
    first, because a name runs two to four ("Amon-Ra St. Brown" is three) and the page, not the
    build, knows which heads exist: it draws the first slug HEADS has. 194 of 200 titles on
    2026-09-24 led with a player; 77 of those had a head in ff-jarvis."""
    title = title or ""
    name = title.split("(")[0].strip() if "(" in title else None
    words = slugify(name or title).split("-")
    return name, ["-".join(words[:n]) for n in (4, 3, 2) if len(words) >= n]


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
        player, slugs = news_player(it.get("title"))
        dated = t != dt.datetime.min.replace(tzinfo=UTC)
        local = t.astimezone(LOCAL_TZ) if dated else None
        # `when` is the page's one time format (js/lib/kick.js) on David's clock, the fallback; `at` is the
        # same moment as ISO UTC, which the page writes in the reader's own clock.
        when = f"{local:%a} {local.hour % 12 or 12}:{local.minute:02d} {'AM' if local.hour < 12 else 'PM'}" if dated else None
        items.append({
            "id": it.get("id"), "title": it.get("title"), "desc": it.get("desc"),
            "impact": it.get("impact"), "team": it.get("team_id"),
            "categories": it.get("categories") or [], "link": it.get("link"), "when": when,
            "at": t.strftime("%Y-%m-%dT%H:%M:%SZ") if dated else None,
            "kind": news_kind(it), "player": player, "slugs": slugs,
        })
    return {"items": mark_superseded(items)}
