"""Inline the ff-jarvis headshots into a self-contained index.html.

design/src/ holds the design (assembled by assemble.py); this replaces the /*__HEADS__*/ token with a
slug -> data-URI map so the page works offline and as a published Artifact.
Run: python design/build.py
"""
import base64
import datetime as dt
import json
import os
import pathlib
import re
import zoneinfo

from assemble import assemble   # design/assemble.py: design/src/** -> the page template

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent

# The three input roots. Each can be pointed elsewhere by env var so a build can run against a
# pinned snapshot (the regression suite) instead of whatever ff-jarvis holds right now.
HEADS_SRC = pathlib.Path(os.environ.get("TEAM_WATCH_HEADS", "C:/Users/David/Github/ff-jarvis/app/public/heads"))
DWR = pathlib.Path(os.environ.get("TEAM_WATCH_DATA", "C:/Users/David/Github/ff-jarvis/data"))
FEED = pathlib.Path(os.environ.get("TEAM_WATCH_FEED", REPO / "data" / "feed.json"))
ESPN_ROSTERS = DWR / "espn_rosters.json"
YAHOO_ROSTERS = DWR / "league_rosters.json"
BP_PROPS = DWR / "bettingpros_props.json"
SLEEPER_STATUS = DWR / "sleeper_status.json"
DFS_POOL = DWR / "dfs_pool.json"
PLAYER_PROJ = DWR / "player_projections.json"

# A depth-chart slot at or past this number, for the player's position, reads as "the backup."
# Mirrors ff-jarvis's model.clients.sleeper.BACKUP_DEPTH.
BACKUP_DEPTH = {"QB": 2, "RB": 2, "TE": 2, "WR": 3}
SUFFIX_RE = re.compile(r"\b(jr|sr|ii|iii|iv|v)\b\.?$")


def norm_name(name):
    """Matches ff-jarvis's model.common.data.norm_name() exactly -- the join key Sleeper's status
    file (and everything else in ff-jarvis) uses. Deliberately separate from slugify() below, which
    serves headshot filenames and isn't guaranteed to normalize identically."""
    n = re.sub(r"[.'\-]", "", name.lower()).strip()
    n = SUFFIX_RE.sub("", n).strip()
    return re.sub(r"\s+", " ", n)


def sleeper_flag(rec):
    """Mirrors ff-jarvis's model.clients.sleeper.derive_status() -- the one place "is this guy
    playing" gets decided. Team-watch's badges only render OUT/Q today; 'backup' is computed for
    parity with the source of truth but has no UI here yet."""
    if not rec:
        return None
    if not rec.get("playing", True):
        return "out"
    if rec.get("injury") == "Questionable":
        return "q"
    if rec.get("depth") and rec["depth"] >= BACKUP_DEPTH.get(rec.get("pos"), 9):
        return "backup"
    return None


def load_status():
    """norm_name -> Sleeper record (ff-jarvis's model.clients.sleeper), the canonical injury/depth
    read every feature should prefer over deriving its own. Feed-first (what the scheduled refresh
    saw), the ff-jarvis file directly as a fallback -- the same two-tier pattern load_props_raw()
    and load_model_raw() already use below."""
    feed = FEED
    try:
        d = json.loads(feed.read_text(encoding="utf-8"))
        block = (d.get("status") or {}).get("data")
        if block and block.get("players"):
            return block["players"]
    except (OSError, json.JSONDecodeError):
        pass
    if SLEEPER_STATUS.exists():
        try:
            return json.loads(SLEEPER_STATUS.read_text(encoding="utf-8")).get("players", {})
        except (OSError, json.JSONDecodeError):
            pass
    return {}

SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}

# Sportsbooks the builder shows, in display order. BettingPros returns its own consensus line
# alongside them even when the request filters by book; it is kept per prop as a reference and
# never listed as a book you can bet at.
BOOK_ORDER = ["DraftKings", "Underdog"]
REFERENCE_BOOK = "Consensus"
POS_ORDER = {"QB": 0, "RB": 1, "WR": 2, "TE": 3}
MKT_ORDER = {"PASS": 0, "RUSH": 1, "REC": 2, "RECS": 3, "TD": 4}
# BettingPros team codes that differ from the ESPN/nflverse codes the rest of the page uses.
TEAM_FIX = {"JAC": "JAX", "LA": "LAR"}   # the book's and the model's spellings, one canon
# Where the model's rate sits relative to the book's line across the whole slate (week 1 2026:
# medians 1.12 rush, 1.13 rec, 1.01 receptions, 0.94 pass), and how far from that a line can be
# before it is read as a role change rather than a disagreement.
STALE_CENTRE = {"RUSH": 1.12, "REC": 1.10, "RECS": 1.0, "PASS": 0.93}
STALE_BAND = 1.35


def is_stale(mkt, mu, line):
    r0 = STALE_CENTRE.get(mkt, 1.0)
    ratio = mu / line
    return ratio > r0 * STALE_BAND or ratio < r0 / STALE_BAND
# The anytime-TD market prices whole teams too; those rows are not players.
NFL_TEAMS = {
    "Arizona Cardinals", "Atlanta Falcons", "Baltimore Ravens", "Buffalo Bills",
    "Carolina Panthers", "Chicago Bears", "Cincinnati Bengals", "Cleveland Browns",
    "Dallas Cowboys", "Denver Broncos", "Detroit Lions", "Green Bay Packers",
    "Houston Texans", "Indianapolis Colts", "Jacksonville Jaguars", "Kansas City Chiefs",
    "Las Vegas Raiders", "Los Angeles Chargers", "Los Angeles Rams", "Miami Dolphins",
    "Minnesota Vikings", "New England Patriots", "New Orleans Saints", "New York Giants",
    "New York Jets", "Philadelphia Eagles", "Pittsburgh Steelers", "San Francisco 49ers",
    "Seattle Seahawks", "Tampa Bay Buccaneers", "Tennessee Titans", "Washington Commanders",
}

SLUGS = [
    # league-wide pool + builder samples
    "chase-brown", "isaiah-likely", "jalen-coker", "bhayshul-tuten", "blake-corum",
    "braelon-allen", "dylan-sampson", "chig-okonkwo", "brenton-strange",
    "dontayvion-wicks", "jalen-nailor", "adonai-mitchell", "alec-pierce",
    "carnell-tate", "denzel-boston", "devaughn-vele",
    # Yahoo - Chat Take the Wheel
    "derrick-henry", "devon-achane", "rashee-rice", "tetairoa-mcmillan",
    "davante-adams", "jameson-williams", "josh-jacobs", "tony-pollard",
    "courtland-sutton", "matthew-stafford", "xavier-worthy", "deebo-samuel",
    "dallas-goedert",
    # ESPN - Purdy Big in Japan
    "amonra-st-brown", "cam-skattebo", "tee-higgins", "george-kittle",
    "dk-metcalf", "brock-purdy", "jordan-mason", "jared-goff", "jerry-jeudy",
    "hunter-henry", "najee-harris", "tyrone-tracy",
]


def slugify(name):
    """ESPN display name -> headshot slug, matching ff-jarvis's file naming."""
    cleaned = "".join(c if (c.isalnum() or c == " ") else "" for c in name.lower())
    parts = [p for p in cleaned.split() if p not in SUFFIXES]
    return "-".join(parts)


def live_espn(available):
    """The real ESPN roster, so the mock's structure is never invented."""
    if not ESPN_ROSTERS.exists():
        return None
    d = json.loads(ESPN_ROSTERS.read_text(encoding="utf-8"))
    status = load_status()
    me = d["me"]
    out = []
    flex = 0
    for p in d["detail"][me]:
        slot = p["slot"]
        if slot == "FLEX":
            flex += 1
            slot = f"FLX{flex}"
        elif slot == "BE":
            slot = "BN"
        name = p["name"].replace(" D/ST", "")
        slug = slugify(name)
        # Sleeper wins whenever it has a record for this player -- even a "healthy" read overrides
        # a stale ESPN status. ESPN's own field only fills the gap when Sleeper has no entry at all.
        rec = status.get(norm_name(name))
        if rec is not None:
            badge = {"out": "OUT", "q": "Q"}.get(sleeper_flag(rec))
        else:
            badge = {"QUESTIONABLE": "Q", "OUT": "OUT"}.get(p.get("status") or "", None)
        out.append({
            "n": name,
            "pos": "DST" if p["pos"] == "DEF" else p["pos"],
            "team": p["team"],
            "slot": slot,
            "slug": slug if slug in available else None,
            "status": badge,
        })
    return {"name": me, "league": d["league"], "league_id": d["league_id"],
            "updated": d["updated"], "roster": out}


def live_feed():
    """What `python -m model.refresh` last wrote. Drives the status strip, so the page reports
    the real state of each source instead of a hardcoded banner. Only the provenance is taken —
    the payloads stay out of the page until there is something in them."""
    path = FEED
    if not path.exists():
        return None
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    usage = (d.get("usage") or {}).get("data") or {}
    market = d.get("market") or {}
    return {
        "generated": d.get("generated"),
        "steps": d.get("steps", []),
        "usage_ready": bool(usage.get("ready")),
        "usage_note": usage.get("note"),
        "pool_size": len(usage.get("pool") or []),
        "fetched": {
            "espn": ((d.get("rosters") or {}).get("espn") or {}).get("fetched"),
            "yahoo": ((d.get("rosters") or {}).get("yahoo") or {}).get("fetched"),
            "props": ((market.get("props") or {}).get("fetched")),
            "props_bp": ((market.get("props_bp") or {}).get("fetched")),
            "props_model": ((market.get("props_model") or {}).get("fetched")),
            "dfs": ((market.get("dfs") or {}).get("fetched")),
        },
    }


def nfl_roster():
    """slug -> (pos, team) from the nflverse roster ff-jarvis caches. Optional: without pandas
    or the file, a touchdown-only name that no yards market identifies is left out."""
    path = DWR / "cache" / "roster_2026.parquet"
    try:
        import pandas as pd
        d = pd.read_parquet(path, columns=["full_name", "position", "team"])
    except Exception:
        return {}
    out = {}
    for name, pos, team in d.itertuples(index=False):
        if pos in POS_ORDER and name:
            out.setdefault(slugify(name), (pos, team))
    return out


def load_props_raw():
    """The BettingPros pull, preferring the feed (`market.props_bp`) so the page shows what the
    scheduled refresh saw. A feed older than the props step lacks the block; then the file the
    props client wrote is read directly, the same way the rosters are."""
    feed = FEED
    try:
        d = json.loads(feed.read_text(encoding="utf-8"))
        block = ((d.get("market") or {}).get("props_bp") or {}).get("data")
        if block and block.get("props"):
            return block, "feed.json"
    except (OSError, json.JSONDecodeError):
        pass
    if BP_PROPS.exists():
        try:
            return json.loads(BP_PROPS.read_text(encoding="utf-8")), "ff-jarvis/data"
        except (OSError, json.JSONDecodeError):
            return None, None
    return None, None


def load_model_raw():
    """P(over) per priced line from ff-jarvis's `model.market.props_model`, feed first, file second,
    the same way the lines themselves are read."""
    feed = FEED
    try:
        d = json.loads(feed.read_text(encoding="utf-8"))
        block = ((d.get("market") or {}).get("props_model") or {}).get("data")
        if block and block.get("lines"):
            return block
    except (OSError, json.JSONDecodeError):
        pass
    # Third choice: the copy kept beside the feed. The ff-jarvis checkout can sit on another branch
    # (two sessions share it), and the refresh then rewrites the feed without the model block.
    for path in (DWR / "props_model.json", REPO / "data" / "props_model.json"):
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
    return None


def load_player_proj():
    """Half-PPR points for every player from ff-jarvis's `model.market.projections`, feed block
    first (`projections`), then the file, same two-tier pattern as the other live reads. A feed
    written before that step existed has no block, and an ff-jarvis checkout on another branch
    may have no file: then nothing is modelled and every DFS row falls back to Yahoo's FPPG,
    which the header says out loud."""
    feed = FEED
    try:
        d = json.loads(feed.read_text(encoding="utf-8"))
        block = (d.get("projections") or {}).get("data")
        if block and block.get("players"):
            return block
    except (OSError, json.JSONDecodeError):
        pass
    for path in (PLAYER_PROJ, REPO / "data" / "player_projections.json"):
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
    return None


LOCAL_TZ = zoneinfo.ZoneInfo("America/Los_Angeles")
UTC = dt.timezone.utc


def kickoff(commence):
    """BettingPros gives kickoff in UTC. Bucket it on David's clock: the 1pm-ET wave is morning,
    the 4pm wave afternoon, everything from the night windows (Thu, Sun, Mon) evening. This is
    only the raw time-of-day bucket (`base`) -- it says nothing about which calendar date the
    game falls on, which is why `assign_windows` below exists as a second pass. `t` is the
    localized datetime, returned so that pass can group by `t.date()` (never the raw UTC
    string: a 5:20pm Pacific kickoff is after midnight UTC the next day, so slicing `commence`
    directly would put it on the wrong date)."""
    try:
        t = dt.datetime.strptime(commence, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC).astimezone(LOCAL_TZ)
    except (TypeError, ValueError):
        return None, None, None
    base = "morning" if t.hour < 12 else "afternoon" if t.hour < 16 else "evening"
    label = t.strftime("%a %I:%M%p").replace(" 0", " ").replace("AM", "a").replace("PM", "p")
    return base, label, t


def assign_windows(rows):
    """Split each time-of-day bucket (`base`) by calendar date, so a slip built from one window
    never mixes two different days -- the bug this exists to fix: "evening" alone can hold
    Thursday Night, Sunday Night and Monday Night, three different dates in the same week.

    A base with only one date that week keeps its plain label ("Evening"). A base with more
    than one date splits per date, labeled by weekday ("Thursday Night", "Monday Night") --
    applied to all three bases, not just evening, since a late-season Saturday slate can put
    real games in the morning/afternoon hour bands on two different dates too.

    Writes the resulting window key onto each row as `win` (kept separate from `slot`, the raw
    3-value time-of-day bucket -- `win` is the date-safe grouping key and its set of values is
    not stable week to week). Returns the ordered list of windows, chronological by kickoff.
    """
    by_base = {}
    for p in rows:
        t = p.pop("_t", None)
        if t is None:
            continue
        by_base.setdefault(p["slot"], {}).setdefault(t.date(), []).append((p, t))

    windows = []
    for base in ("morning", "afternoon", "evening"):
        dates = by_base.get(base)
        if not dates:
            continue
        multi = len(dates) > 1
        for d, entries in dates.items():
            if multi:
                key = f"{base}-{d:%a}".lower()
                label = f"{d:%A} Night" if base == "evening" else f"{d:%A} {base.capitalize()}"
            else:
                key = base
                label = base.capitalize()
            # Collision guard: two dates sharing a weekday name only happens if a pull ever
            # spans two weeks; disambiguate rather than silently merging them.
            if any(w["k"] == key for w in windows):
                key, label = f"{key}-{d.day}", f"{label} ({d.day})"
            for p, t in entries:
                p["win"] = key
            windows.append({
                "k": key, "label": label, "short": label.upper(), "date": d.isoformat(),
                "kick": min(entries, key=lambda e: e[1])[0]["kick"],
                "n": len(entries), "games": len({p["game"] for p, _ in entries}),
                "_when": min(t for _, t in entries),
            })
    windows.sort(key=lambda w: w["_when"])
    for w in windows:
        del w["_when"]
    return windows


def load_wrcb():
    """RotoBaller's WR/CB column for the week, feed first then the ff-jarvis file."""
    feed = FEED
    try:
        d = json.loads(feed.read_text(encoding="utf-8"))
        block = ((d.get("market") or {}).get("wrcb") or {}).get("data")
        if block and block.get("records"):
            return block
    except (OSError, json.JSONDecodeError):
        pass
    path = DWR / "wrcb.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
    return None


def load_news():
    """Breaking news from ff-jarvis's own scanner (it watches FantasyPros' wire and writes
    data/breaking_news.json) -- feed first, then the file directly, same two-tier pattern as
    every other live read here. `when` is reformatted the same way kickoff() below does it, so a
    news row and a kickoff badge read as the same kind of timestamp."""
    feed = FEED
    raw = None
    try:
        d = json.loads(feed.read_text(encoding="utf-8"))
        block = ((d.get("market") or {}).get("news") or {}).get("data")
        if block and block.get("items"):
            raw = block
    except (OSError, json.JSONDecodeError):
        pass
    if raw is None:
        path = DWR / "breaking_news.json"
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


def implied(american):
    """Break-even probability of an American price, vig included."""
    a = float(american)
    return 100.0 / (a + 100.0) if a > 0 else -a / (-a + 100.0)


def live_props(available, rosters):
    """One row per (player, market) from the BettingPros pull, priced per book.

    The raw file is one row per (player, market, book, side, line). Three things about it are
    handled here rather than in the template: stale lines (an August number sits next to this
    week's for a few players; the newest `updated` per book and side wins), the anytime-TD market
    (BettingPros prices it as one offer per game whose selections are the players, so the row's
    `player` is a meaningless first participant and the real name is in `side`; team rows are
    dropped), and the consensus line that comes back even when the request filters by book.
    `rosters` is slug -> {pos, team, leagues} for my two teams; it sets `mine` and fills position
    and team for a player the TD market names but no yards market does.
    """
    raw, origin = load_props_raw()
    if not raw:
        return None

    # Who a name is: the yards markets carry position and team; the TD market carries neither
    # and spells names its own way ("Deebo Samuel Sr." vs "Deebo Samuel"), so everything keys on
    # the slug, and a TD-only name falls back to my rosters, then to the nflverse roster.
    ident, spelling = {}, {}
    for r in raw["props"]:
        if r.get("market") != "TD" and r.get("player"):
            slug = slugify(r["player"])
            ident.setdefault(slug, (r.get("position"), r.get("team")))
            spelling.setdefault(slug, r["player"])
    nfl = nfl_roster()

    latest = {}
    for r in raw["props"]:
        mkt = r.get("market")
        if mkt == "TD":
            name, side, line = r.get("side") or "", "Over", None
            if name in NFL_TEAMS:
                continue
        else:
            name, side, line = r.get("player") or "", r.get("side"), r.get("line")
        if not name or side not in ("Over", "Under") or r.get("price") is None:
            continue
        slug = slugify(name)
        spelling.setdefault(slug, name)
        key = (slug, mkt, r.get("book"), side)
        prev = latest.get(key)
        if prev is None or (r.get("updated") or "") > (prev["updated"] or ""):
            latest[key] = {"mkt": mkt, "book": r.get("book"), "side": side,
                           "line": line, "price": int(r["price"]), "game": r.get("game"),
                           "commence": r.get("commence"), "updated": r.get("updated") or ""}

    groups = {}
    for (slug, mkt, book, side), r in latest.items():
        g = groups.setdefault((slug, mkt), {"books": {}, "game": r["game"],
                                            "commence": r["commence"], "updated": ""})
        b = g["books"].setdefault(book, {})
        b[side.lower()] = r["price"]
        if side == "Over":
            b["line"] = r["line"]
        g["updated"] = max(g["updated"], r["updated"])

    out = []
    for (slug, mkt), g in groups.items():
        name = spelling[slug]
        ro = rosters.get(slug)
        pos, team = ident.get(slug) or (None, None)
        if not pos and ro:
            pos, team = ro["pos"], ro["team"]
        if not pos and slug in nfl:
            pos, team = nfl[slug]
        if pos not in POS_ORDER:
            continue  # a fullback, linebacker or unknown name priced only for a touchdown
        books = g["books"]
        primary = next((b for b in BOOK_ORDER if "over" in books.get(b, {})), None)
        if primary is None:
            continue  # consensus-only rows are a reference, not a bet
        slot, kick, t = kickoff(g["commence"])
        out.append({
            "slot": slot,
            "kick": kick,
            "_t": t,
            "n": name,
            "slug": slug if slug in available else None,
            "pos": pos,
            "team": TEAM_FIX.get(team, team),
            "mkt": mkt,
            "game": g["game"],
            "commence": g["commence"],
            "updated": g["updated"],
            "line": None if mkt == "TD" else books[primary].get("line"),
            "book": primary,
            "books": {b: books[b] for b in BOOK_ORDER if b in books},
            "ref": books.get(REFERENCE_BOOK),
            "mine": 1 if ro else 0,
            "leagues": ro["leagues"] if ro else [],
        })

    # The model's P(over) for the line the card shows (the primary book's). `model` is that chance
    # in percent; `edge` is it minus the break-even of the over price, in points, so +4 means the
    # model thinks the over clears the vig by four points. Nothing when the model has no rate for
    # the player (rookie, or no game in the last season): the card says "model pending".
    model = load_model_raw()
    priced = {}
    if model:
        for r in model["lines"]:
            priced[(slugify(r["name"]), r["market"], r["line"])] = r
    modeled = 0
    for p in out:
        slug = slugify(p["n"])
        # Every book's own line gets its own P(over): Underdog often posts a different number, and
        # on Underdog the bet is a pick (higher or lower at their line), not a price, so the card
        # carries the pick and its confidence rather than an edge.
        for b, x in p["books"].items():
            rb = priced.get((slug, p["mkt"], x.get("line") if p["mkt"] != "TD" else None))
            if rb is None or rb.get("p_over") is None:
                continue
            x["model"] = round(rb["p_over"] * 100)
            if b == "Underdog" and p["mkt"] != "TD":
                x["pick"] = "higher" if rb["p_over"] >= 0.5 else "lower"
                x["conf"] = round(max(rb["p_over"], 1 - rb["p_over"]) * 100)
            if p["mkt"] != "TD" and x.get("line") and rb.get("mu") and is_stale(p["mkt"], rb["mu"], x["line"]):
                x["stale"] = 1   # this book's own line is the one that moved
        r = priced.get((slug, p["mkt"], p["line"]))
        if r is None:
            continue
        # This week's status rides with the price: OUT (Sleeper says he is not playing, the line
        # is stale), Q (questionable, priced but not slip material), backup (depth chart), or
        # no_role (a touchdown line on a player the book prices no yards for).
        for k in ("flag", "injury", "injury_note", "depth"):
            if r.get(k) is not None:
                p[k] = r[k]
        if r.get("p_over") is None:
            if p.get("flag") != "out":
                p["norole"] = 1   # a touchdown line on a player the book prices no yards for
            continue
        over = p["books"][p["book"]]["over"]
        p["model"] = round(r["p_over"] * 100)
        p["edge"] = round((r["p_over"] - implied(over)) * 100, 1)
        p["mu"] = r["mu"]
        p["games"] = r["games"]   # how much of his own history the rate rests on
        # New team. The model's `team` is the one on his last game log; the book's is this
        # week's. When they differ, every game the rate rests on was in another offense, with
        # another quarterback, and the model has no feature for that (props_model.py names it
        # a v1 blind spot). The card says NEW TEAM and no preset will build a slip on it. `FA`
        # from the book means it does not know either, so no verdict there.
        old = TEAM_FIX.get(r.get("team"), r.get("team"))
        if old and p.get("team") and p["team"] != "FA" and old != p["team"]:
            p["moved"] = old
        if r.get("opp_f"):
            p["opp"], p["opp_f"] = r.get("opp"), r["opp_f"]   # the defense, and what it allows vs league
        modeled += 1
        # Role check. The rate is last season's; the line is this week's. Across the slate the
        # rate sits about 12% above a yards line (a mean over a median) and on top of a receptions
        # line. A line far outside that band means the book knows the role changed -- a demoted
        # starter, a back in a new committee -- and the gap is not an edge. The card says ROLE?
        # and no preset will build a slip on it.
        if p["mkt"] != "TD" and p["line"] and r["mu"] and is_stale(p["mkt"], r["mu"], p["line"]):
            p["stale"] = 1

    # RotoBaller's named WR/CB upgrades and downgrades, a tag on the receiver's cards. Opinion
    # about a matchup the model cannot see; it moves no number and no slip.
    wrcb = load_wrcb()
    if wrcb:
        by_slug = {slugify(r["wr"]): r for r in wrcb.get("records", [])}
        for p in out:
            r = by_slug.get(slugify(p["n"]))
            if r and p["mkt"] in ("REC", "RECS", "TD"):
                p["cb"] = {"v": r["verdict"], "cb": r["cb"], "why": (r.get("rationale") or "")[:400],
                           "url": r.get("source_url")}

    windows = assign_windows(out)

    # Best edge first; unmodelled rows after, mine first, by kickoff; the not-playing last.
    out.sort(key=lambda p: (0, -p["edge"]) if "edge" in p
             else (2 if p.get("flag") == "out" else 1, not p["mine"], p["commence"] or "",
                   POS_ORDER.get(p["pos"], 9), p["n"]))
    return {
        "source": raw.get("source"),
        "origin": origin,
        "fetched": raw.get("fetched"),
        "events": raw.get("events"),
        "failed": raw.get("failed") or [],
        "books": [b for b in BOOK_ORDER if any(b in p["books"] for p in out)],
        "players": len({p["n"] for p in out}),
        "windows": windows,
        "model": {"through": model.get("through"), "generated": model.get("generated"),
                  "modeled": modeled, "status_fetched": model.get("status_fetched"),
                  "not_playing": model.get("not_playing", 0)} if model else None,
        "props": out,
        "wrcb": {"week": wrcb.get("week"), "fetched": wrcb.get("fetched"),
                 "n": len(wrcb.get("records", []))} if wrcb else None,
        # last 12 games per priced player, keyed by slug: the card's game-log strip
        "logs": {slugify(k): v for k, v in (model or {}).get("logs", {}).items() if v},
    }


def roster_index(*sources):
    """slug -> {pos, team, leagues} across my teams, for the builder's `mine` flag."""
    idx = {}
    for key, src in sources:
        if not src:
            continue
        for p in src["roster"]:
            slug = slugify(p["n"])
            e = idx.setdefault(slug, {"pos": p["pos"], "team": p["team"], "leagues": []})
            e["leagues"].append(key)
    return idx


def live_yahoo(available):
    """Yahoo comes from a website scrape, so it carries no lineup slot or injury status.
    The template infers slots and says so on the page."""
    if not YAHOO_ROSTERS.exists():
        return None
    d = json.loads(YAHOO_ROSTERS.read_text(encoding="utf-8"))
    me = d["me"]
    out = []
    for p in d["detail"][me]:
        slug = slugify(p["name"])
        out.append({
            "n": p["name"],
            "pos": "DST" if p["pos"] in ("DEF", "D/ST") else p["pos"],
            "team": p["team"],
            "slug": slug if slug in available else None,
        })
    return {"name": me, "league": d["league"], "league_id": d["league_id"],
            "updated": d["updated"], "roster": out}


def model_points():
    """slug -> (points, source) for every player ff-jarvis projects this week.

    The arithmetic used to live here, over the priced prop lines only. It moved into ff-jarvis
    (`model.market.projections`), which runs the same half-PPR conversion over every player the
    model has rates for -- 580 rather than the 200 a book happened to post a line for -- and
    prices a player with no game log off the book's own line instead of leaving him blank. One
    number now serves DFS, the roster board and the trend series, and it is computed once.

    `source` is "model" (his own game log) or "line" (the market's read on a player with no log).
    Anyone still missing -- the deep bench, every K and DST -- falls back to Yahoo's FPPG below.
    """
    d = load_player_proj()
    return {slugify(p["name"]): (p["pts"], p["src"]) for p in (d or {}).get("players", [])
            if p.get("pts") is not None}

def load_dfs_pool():
    """Yahoo's own contest salary export, imported into ff-jarvis by `python -m model.clients.dfs
    import <csv>` -- deliberately manual, per that module's own docstring: an automated Yahoo
    scrape is a decision to ask about, not build quietly. Feed-first, the ff-jarvis file directly
    as a fallback, same two-tier pattern as load_status()/load_props_raw()."""
    feed = FEED
    try:
        d = json.loads(feed.read_text(encoding="utf-8"))
        block = ((d.get("market") or {}).get("dfs") or {}).get("data")
        if block and block.get("players"):
            return block
    except (OSError, json.JSONDecodeError):
        pass
    if DFS_POOL.exists():
        try:
            return json.loads(DFS_POOL.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return None


def live_dfs_yahoo(available):
    """The DFS Builder's Yahoo pool. `sal`/`proj` are Yahoo's own $200-cap scale, not DraftKings'.
    Status prefers Sleeper (see load_status()); the pool's own raw Yahoo status column fills the
    gap for a player Sleeper doesn't track. Yahoo's own export can be stale in a way no status
    field catches: a player who has since changed teams (Theo Wease, MIA -> LAC practice squad,
    2026-09-02) still shows up salaried under his old team with a real-looking projection, no
    status at all, because the CSV was captured before the move. Sleeper's own roster team is
    fresher than Yahoo's export in practice, so a disagreement between the two is itself read as
    "this row predates a roster move" and the player is treated as OUT, same as any other
    not-playing badge."""
    pool = load_dfs_pool()
    if not pool or not pool.get("players"):
        return None
    status = load_status()
    # The projection the optimizer builds on is ff-jarvis's, not Yahoo's FPPG (last season's
    # average, which knows nothing about this week or what team he plays for now). Yahoo's
    # number is the fallback for whoever is left after the model and the book's own line have
    # both had a go -- the deep bench, every K and DST -- rescaled per position by the median
    # model points to FPPG among the players it does -- the model shrinks toward the position
    # mean and sits below a raw average for stars, so an unscaled fallback would let a bench
    # QB's stale 15.1 outrank a priced starter on a different scale.
    mp = model_points()
    ratios = {}
    for r in pool["players"]:
        m = mp.get(slugify(r["name"]))
        if m is not None and m[0] and r["fppg"]:
            ratios.setdefault(r["pos"], []).append(m[0] / r["fppg"])
    scale = {pos: sorted(v)[len(v) // 2] for pos, v in ratios.items() if len(v) >= 5}
    players = []
    for r in pool["players"]:
        name = r["name"]
        slug = slugify(name)
        rec = status.get(norm_name(name))
        team = TEAM_FIX.get(r["team"], r["team"])
        if rec is not None:
            rec_team = TEAM_FIX.get(rec.get("team"), rec.get("team"))
            if rec_team and rec_team != team:
                badge = "OUT"
            else:
                badge = {"out": "OUT", "q": "Q"}.get(sleeper_flag(rec))
        else:
            badge = (r.get("status") or "").strip() or None
        pos = "DST" if r["pos"] == "DEF" else r["pos"]
        m = mp.get(slug)
        if m is not None:
            proj, src = round(m[0], 1), m[1]
        else:
            proj, src = round(r["fppg"] * scale.get(r["pos"], 1.0), 1), "yahoo"
        players.append({
            "n": name, "pos": pos, "team": r["team"], "sal": r["salary"], "proj": proj,
            "src": src, "fppg": r["fppg"],
            "status": badge, "slug": slug if slug in available else None, "game": r.get("game"),
        })
    if not players:
        return None
    players.sort(key=lambda p: -p["sal"])
    return {
        "fetched": pool.get("fetched"),
        "modeled": sum(1 for p in players if p["src"] == "model"),
        "lined": sum(1 for p in players if p["src"] == "line"),
        "scale": {k: round(v, 2) for k, v in scale.items()},
        "source": pool.get("source", "ff-jarvis dfs_pool.json"),
        "players": players,
    }


def main():
    available = {p.stem for p in HEADS_SRC.glob("*.webp")}
    live = live_espn(available)
    liveY = live_yahoo(available)
    liveDfsYahoo = live_dfs_yahoo(available)
    news = load_news()

    props = live_props(available, roster_index(("espn", live), ("yahoo", liveY)))

    wanted = list(SLUGS)
    for src in (live, liveY):
        if src:
            wanted += [p["slug"] for p in src["roster"] if p["slug"]]
    if props:
        wanted += [p["slug"] for p in props["props"] if p["slug"]]
    if liveDfsYahoo:
        wanted += [p["slug"] for p in liveDfsYahoo["players"] if p["slug"]]

    heads = {}
    missing = []
    for slug in dict.fromkeys(wanted):
        path = HEADS_SRC / f"{slug}.webp"
        if not path.exists():
            missing.append(slug)
            continue
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        heads[slug] = f"data:image/webp;base64,{b64}"

    injected = (
        "const HEADS = " + json.dumps(heads) + ";\n"
        "const LIVE_ESPN = " + json.dumps(live) + ";\n"
        "const LIVE_YAHOO = " + json.dumps(liveY) + ";\n"
        "const LIVE_FEED = " + json.dumps(live_feed()) + ";\n"
        "const LIVE_NEWS = " + json.dumps(news) + ";\n"
        "const LIVE_PROPS = " + json.dumps(props) + ";\n"
        "const LIVE_DFS_YAHOO = " + json.dumps(liveDfsYahoo) + ";"
    )
    tpl = assemble()
    body = tpl.replace("/*__HEADS__*/", injected)

    # design/index.html is the fragment the Artifact publisher wants (no doctype/head).
    (ROOT / "index.html").write_text(body, encoding="utf-8")

    # The repo root is what Vercel serves, so that copy is a full HTML document.
    favicon = (
        "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
        "%3Crect width='32' height='32' fill='%2308080a'/%3E"
        "%3Crect x='11' y='6' width='10' height='20' fill='%23c8ff2e'/%3E%3C/svg%3E"
    )
    head = "\n".join([
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="description" content="Team Watch - roster console for two fantasy football teams.">',
        f'<link rel="icon" href="{favicon}">',
        "<style>html{background:#08080a;color-scheme:dark}body{margin:0}"
        "img{max-width:100%}[hidden]{display:none!important}</style>",
        "</head>",
        "<body>",
    ])
    page = f"{head}\n{body}\n</body>\n</html>\n"
    (REPO / "index.html").write_text(page, encoding="utf-8")

    kb = len(page.encode("utf-8")) / 1024
    print(f"wrote {REPO/'index.html'} and {ROOT/'index.html'} ({kb:.0f} KB), {len(heads)} heads inlined")
    for label, src in (("ESPN", live), ("Yahoo", liveY)):
        if src:
            print(f"{label}: {len(src['roster'])} players, {src['league']}, pulled {src['updated']}")
        else:
            print(f"{label}: no live file, template falls back to its own copy")
    if props:
        mine = sum(1 for p in props["props"] if p["mine"])
        print(f"Props: {len(props['props'])} lines, {props['players']} players, "
              f"{props['events']} games, {'/'.join(props['books'])}, pulled {props['fetched']} "
              f"(from {props['origin']}), {mine} on my rosters")
        print("Windows: " + " · ".join(
            f"{w['label']}({w['n']}/{w['games']}g)" for w in props["windows"]))
        if props["model"]:
            print(f"Model: {props['model']['modeled']} of {len(props['props'])} lines priced, "
                  f"stats through {props['model']['through']}, run {props['model']['generated']}")
        else:
            print("Model: no props_model.json, every card says pending")
    else:
        print("Props: no BettingPros file, template falls back to its sample")
    if liveDfsYahoo:
        print(f"Yahoo DFS: {len(liveDfsYahoo['players'])} players, pulled {liveDfsYahoo['fetched']}")
    else:
        print("Yahoo DFS: no ff-jarvis dfs_pool.json/feed block, template falls back to its sample")
    if news:
        print(f"News: {len(news['items'])} items from ff-jarvis's scanner")
    else:
        print("News: no breaking_news.json/feed block, template falls back to its sample")
    if missing:
        print(f"no headshot for {len(missing)} slugs (initials fallback renders)")


if __name__ == "__main__":
    main()
