"""Inject the live data into index.html and copy the ff-jarvis headshots beside it.

design/src/ holds the design (assembled by assemble.py); this replaces the /*__HEADS__*/ token with
the slug -> heads/<slug>.webp map and every LIVE_* block. The heads are files, not data URIs, so a
published Artifact (design/index.html) shows initials unless heads/ is published with it.
Run: python design/build.py
"""
import hashlib
import json
import os
import pathlib
import re
import sys

import contract                 # design/contract.py: the shape each LIVE_* block must have
import pbp                      # design/pbp.py: nflverse play-by-play -> games/<id>.json
import lint_css                 # design/lint_css.py: theme rules; an error fails the build
from assemble import assemble   # design/assemble.py: design/src/** -> the page template
from news import load_news      # design/news.py: breaking news, split out to stay in budget
from signals import live_signals, load_usage, report as signals_report  # My Teams trend and news
from waiver import live_waiver, slugs as waiver_slugs, report as waiver_report  # the Waivers sub-tab
from wire_watch import live_wire, report as wire_report                          # its Breaking rail
from pool import live_pool, report as pool_report  # design/pool.py: the Pool page
from usage import live_usage, load_grid, report as usage_report  # design/usage.py: the Usage grid
from slate import assign_windows, day_windows, kickoff   # design/slate.py: kickoff windows
from schedule import load_schedule, report as schedule_report  # when Live may poll, and when not
from pedigree import live_pedigree, report as pedigree_report   # design/pedigree.py: the profile modal's bio strip
from gamelog import live_gamelog, report as gamelog_report      # design/gamelog.py: the profile modal's weekly history
from projections import live_projections, report as projections_report  # design/projections.py: projected vs actual
from injury import live_injury, report as injury_report  # design/injury.py: who is out, doubtful, questionable
from lines import live_lines, report as lines_report  # design/lines.py: implied points per team
from routes import live_routes, report as routes_report          # design/routes.py: the profile sheet's YPRR axis
from archetype import (                                           # design/archetype.py: role/style labels + OL context
    load_archetype, load_trenches, live_archetype, live_trenches,
    report_archetype, report_trenches,
)
from sources import (                                    # design/sources.py: the ff-jarvis adapter
    ROOT, REPO, DWR, FEED, ESPN_ROSTERS, YAHOO_ROSTERS, DFS_POOL,
    feed_block, read_first, load_status, load_props_raw, load_model_raw,
    load_player_proj, load_wrcb, load_profiles, load_dfs_pool, load_gamelog_weekly,
    load_draft_pedigree, load_weather, load_routes,
)

# One slug for one name across the page and the functions: api/league.py slugs a connected
# league's players at request time with this same function (api/_espn.py).
sys.path.insert(0, str(REPO / "api"))
from _espn import slugify  # noqa: E402

# Pointed elsewhere by env var so a build can run against a pinned snapshot (the regression
# suite) instead of whatever ff-jarvis holds right now. The other input roots (DWR, FEED) live
# in sources.py, which owns every ff-jarvis read; this one only ever feeds write_heads() here.
HEADS_SRC = pathlib.Path(os.environ.get("TEAM_WATCH_HEADS", "C:/Users/David/Github/ff-jarvis/app/public/heads"))
# Served next to the page, and the prefix of every HEADS url, so the two cannot disagree.
HEADS_DIR = "heads"
# The 256px heads (2026-09-25), which ff-jarvis cuts for its draft board's players only. The
# 96px ones are sharp in a 40px row but blur when a trading card stretches them 2-3x, so the
# cards (HEADS_LG) take the large file where there is one. About 230 players, 1.9 MB.
HEADS_LG = "lg"


def _mirror(src_dir, out):
    """Make <out> hold exactly src_dir's .webp files: copy what changed, drop what is gone."""
    out.mkdir(parents=True, exist_ok=True)
    src = {p.name: p for p in src_dir.glob("*.webp")}
    for stale in out.glob("*.webp"):
        if stale.name not in src:
            stale.unlink()
    for name, p in src.items():
        target = out / name
        data = p.read_bytes()
        if not target.exists() or target.read_bytes() != data:
            target.write_bytes(data)
    return len(src)


def write_heads(dest_root):
    """Mirror HEADS_SRC into <dest_root>/heads/ (and its lg/ into heads/lg/), dropping a head
    ff-jarvis no longer has, so each folder is exactly the set HEADS / HEADS_LG names. Returns
    how many 96px heads were written."""
    out = pathlib.Path(dest_root) / HEADS_DIR
    n = _mirror(HEADS_SRC, out)
    _mirror(HEADS_SRC / HEADS_LG, out / HEADS_LG)
    return n

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


def _stock_by_slug(players):
    """Re-key market.stock's players from the producer's norm_name key to the same slug
    profileFor() uses (slugify(name)), so stock.js's stockFor() can share profileFor()'s lookup
    instead of hand-mirroring ff-jarvis's norm_name (architecture.md: never hand-mirror logic
    across repos). Two players who land on the same slug keep whichever is `src: "market"` -- a
    priced line beats a model fallback; a tie keeps whichever was seen first."""
    by_slug = {}
    for rec in players.values():
        slug = slugify(rec.get("name") or "")
        prev = by_slug.get(slug)
        if prev is None or (rec.get("src") == "market" and prev.get("src") != "market"):
            by_slug[slug] = rec
    return by_slug


def load_market_stock():
    """ff-jarvis's market.market_stock: feed block `market.stock` first, file fallback, then
    re-keyed by slug (see _stock_by_slug)."""
    block = feed_block(("market", "stock"), "players") or read_first(DWR / "market_stock.json")
    return {**block, "players": _stock_by_slug(block["players"])} if block else block


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
        # no_role (a touchdown line on a player the book prices no yards for). role_note is a
        # separate, hand-written signal (data/role_notes.json) already baked into this row's own
        # p_over/edge -- it rides along only so the card can show why the number moved.
        for k in ("flag", "injury", "injury_note", "depth", "role_note"):
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
        "days": day_windows(windows),
        "model": {"through": model.get("through"), "week": model.get("week"), "generated": model.get("generated"),
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


# Yahoo's lineup slot names -> the ones the page uses. Anything else (QB, RB, WR, TE, K, BN) is
# already the page's name.
YAHOO_SLOT = {"W/R/T": "FLEX", "DEF": "DST", "D/ST": "DST", "IR": "OUT"}


def live_yahoo(available):
    """Yahoo comes from a website scrape with no injury status. Since 2026-09 the scrape carries
    each player's lineup slot, which is passed through; a scrape without one gives slot None, and
    the template falls back to inferring the lineup."""
    if not YAHOO_ROSTERS.exists():
        return None
    d = json.loads(YAHOO_ROSTERS.read_text(encoding="utf-8"))
    me = d["me"]
    out = []
    for p in d["detail"][me]:
        slug = slugify(p["name"])
        slot = p.get("slot")
        out.append({
            "n": p["name"],
            "pos": "DST" if p["pos"] in ("DEF", "D/ST") else p["pos"],
            "team": p["team"],
            "slot": YAHOO_SLOT.get(slot, slot),
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
        elif r["pos"] == "DEF" and r.get("yahoo_proj") is not None:
            # The model has no defense rates, and no DEF ratio ever reaches `scale`, so FPPG went
            # through raw: a defense's season average runs ~2.5x Yahoo's own this-week projection
            # (CIN 14.5 vs 4.3, 2026-09-25), which made the priciest DST look like the best value.
            proj, src = round(r["yahoo_proj"], 1), "yahoo"
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


class Build:
    """What render() returns: the two outputs plus the summary main() prints."""
    def __init__(self, page, fragment, report, heads, missing, stamp=None):
        self.page, self.fragment, self.report, self.heads, self.missing = page, fragment, report, heads, missing
        self.stamp = stamp or {}


def wanted_slugs(live, liveY, props, dfs, waiver, pool):
    """Every slug the page can draw a headshot for, in first-seen order is not needed: render()
    dedupes. Split out of render() for its line budget."""
    wanted = list(SLUGS) + waiver_slugs(waiver) + [p["slug"] for p in (pool or {}).get("players", []) if p["slug"]]
    for src in (live, liveY):
        if src:
            wanted += [p["slug"] for p in src["roster"] if p["slug"]]
    if props:
        wanted += [p["slug"] for p in props["props"] if p["slug"]]
    if dfs:
        wanted += [p["slug"] for p in dfs["players"] if p["slug"]]
    return wanted


def add_market_stock(blocks, report):
    """Loads LIVE_MARKET_STOCK and LIVE_SIGNALS into `blocks` and appends their report lines, plus
    LIVE_WAIVER's and LIVE_POOL's (already loaded, for headshots) -- split out of render() for its
    110-line budget (tests/test_budgets.py's PY_BACKLOG ratchet)."""
    stock = load_market_stock()
    blocks["LIVE_MARKET_STOCK"] = stock
    report.append(f"Market stock: {len(stock['players'])} players" if stock
                  else "Market stock: none, so no market row")
    blocks["LIVE_SIGNALS"] = live_signals(FEED, DWR, (blocks["LIVE_ESPN"], blocks["LIVE_YAHOO"]), slugify)
    report += [signals_report(blocks["LIVE_SIGNALS"]), waiver_report(blocks["LIVE_WAIVER"]),
               wire_report(blocks["LIVE_WIRE"]), pool_report(blocks["LIVE_POOL"]), usage_report(blocks["LIVE_USAGE"])]


def report_sources(report, live, liveY, props, liveDfsYahoo, news, profiles, missing):
    """The per-source lines of render()'s summary -- split out to keep render() under its
    110-line budget (tests/test_budgets.py's PY_BACKLOG ratchet). Mutates `report` in place,
    same convention as add_market_stock()."""
    for label, src in (("ESPN", live), ("Yahoo", liveY)):
        if src:
            report.append(f"{label}: {len(src['roster'])} players, {src['league']}, pulled {src['updated']}")
        else:
            report.append(f"{label}: no live file, template falls back to its own copy")
    if props:
        mine = sum(1 for p in props["props"] if p["mine"])
        report.append(f"Props: {len(props['props'])} lines, {props['players']} players, "
                      f"{props['events']} games, {'/'.join(props['books'])}, pulled {props['fetched']} "
                      f"(from {props['origin']}), {mine} on my rosters")
        report.append("Windows: " + " · ".join(
            f"{w['label']}({w['n']}/{w['games']}g)" for w in props["windows"]))
        if props["model"]:
            report.append(f"Model: {props['model']['modeled']} of {len(props['props'])} lines priced, "
                          f"stats through {props['model']['through']}, run {props['model']['generated']}")
        else:
            report.append("Model: no props_model.json, every card says pending")
    else:
        report.append("Props: no BettingPros file, template falls back to its sample")
    if liveDfsYahoo:
        report.append(f"Yahoo DFS: {len(liveDfsYahoo['players'])} players, pulled {liveDfsYahoo['fetched']}")
    else:
        report.append("Yahoo DFS: no ff-jarvis dfs_pool.json/feed block, template falls back to its sample")
    if news:
        report.append(f"News: {len(news['items'])} items from ff-jarvis's scanner")
    else:
        report.append("News: no breaking_news.json/feed block, template falls back to its sample")
    report.append(f"Profiles: {len(profiles['players'])} players" if profiles else "Profiles: none, so no chips")
    if missing:
        report.append(f"no headshot for {len(missing)} slugs (initials fallback renders)")


def document_head():
    """The <head> of the served page, up to <body>. The page ground is read from tokens.css, so
    what paints before the stylesheet never disagrees with it: the ground under a short page and a
    phone browser's own bar (theme-color) both come from here."""
    void = re.search(r"--void:(#[0-9a-fA-F]{6});",
                     (ROOT / "src" / "css" / "base" / "tokens.css").read_text(encoding="utf-8")).group(1)
    favicon = (
        "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
        f"%3Crect width='32' height='32' fill='%23{void[1:]}'/%3E"
        "%3Crect x='11' y='6' width='10' height='20' fill='%23c8ff2e'/%3E%3C/svg%3E"
    )
    return "\n".join([
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="description" content="Team Watch - roster console for two fantasy football teams.">',
        f'<link rel="icon" href="{favicon}">',
        f'<meta name="theme-color" content="{void}">',
        f"<style>html{{background:{void};color-scheme:dark}}body{{margin:0}}"
        "img{max-width:100%}[hidden]{display:none!important}</style>",
        "</head>",
        "<body>",
    ])


def render():
    """Everything but the writes, so a test can build in-process against fixture inputs.
    Fails (SystemExit) on a lint error, a contract violation, or an assembly problem."""
    bad = lint_css.errors(lint_css.lint())
    if bad:
        raise SystemExit("lint: " + "; ".join(f"{f.file}:{f.line} {f.rule} {f.text}" for f in bad))

    available = {p.stem for p in HEADS_SRC.glob("*.webp")}
    live = live_espn(available)
    liveY = live_yahoo(available)
    liveDfsYahoo = live_dfs_yahoo(available)
    news = load_news(FEED, DWR)

    props = live_props(available, roster_index(("espn", live), ("yahoo", liveY)))

    waiver, pool = live_waiver(FEED, DWR, slugify), live_pool(load_usage(FEED, DWR), slugify)
    # Usage is deliberately not in wanted_slugs: the grid runs 80 rows a position and draws no
    # portrait, so inlining one per name would add megabytes for a column that does not exist.
    usage = live_usage(load_grid(FEED, DWR), slugify)
    wanted = wanted_slugs(live, liveY, props, liveDfsYahoo, waiver, pool)
    wanted_set = set(wanted)

    # Every head ff-jarvis has, not only the wanted ones: a connected league's players are read at
    # runtime, so the build cannot know them. They are files now (write_heads), fetched lazily, so
    # a head nobody scrolls to costs nothing -- inlined, all of them would cost the page 470 KB.
    heads = {slug: f"{HEADS_DIR}/{slug}.webp" for slug in sorted(available)}
    heads_lg = {p.stem: f"{HEADS_DIR}/{HEADS_LG}/{p.name}" for p in sorted((HEADS_SRC / HEADS_LG).glob("*.webp"))}
    missing = [slug for slug in dict.fromkeys(wanted) if slug not in available]

    report = []
    blocks = {
        "LIVE_ESPN": live,
        "LIVE_YAHOO": liveY,
        "LIVE_FEED": live_feed(),
        "LIVE_NEWS": news,
        "LIVE_PROPS": props,
        "LIVE_DFS_YAHOO": liveDfsYahoo,
        "LIVE_PROFILES": load_profiles(),
        "LIVE_WAIVER": waiver,
        "LIVE_WIRE": live_wire(FEED, DWR),
        "LIVE_POOL": pool,
        "LIVE_USAGE": usage,
        "LIVE_SCHEDULE": load_schedule(DWR),
        "LIVE_PEDIGREE": live_pedigree(load_status(), load_draft_pedigree(), slugify, wanted_set),
        "LIVE_GAMELOG": live_gamelog(load_gamelog_weekly(), slugify, wanted_set),
        "LIVE_PROJECTIONS": live_projections(load_player_proj(), slugify, wanted_set, load_status()),
        "LIVE_INJURY": live_injury(load_status(), slugify, wanted_set),
        "LIVE_WEATHER": load_weather(),
        "LIVE_LINES": live_lines(load_dfs_pool(), TEAM_FIX),
        "LIVE_ROUTES": live_routes(load_routes(), slugify, wanted_set),
        "LIVE_ARCHETYPE": live_archetype(load_archetype(FEED, DWR), wanted_set),
        "LIVE_TRENCHES": live_trenches(load_trenches(FEED, DWR)),
    }
    add_market_stock(blocks, report)
    report.append(schedule_report(blocks["LIVE_SCHEDULE"]))
    report += [pedigree_report(blocks["LIVE_PEDIGREE"]), gamelog_report(blocks["LIVE_GAMELOG"]),
              projections_report(blocks["LIVE_PROJECTIONS"]), routes_report(blocks["LIVE_ROUTES"]),
              report_archetype(blocks["LIVE_ARCHETYPE"]), report_trenches(blocks["LIVE_TRENCHES"]),
              lines_report(blocks["LIVE_LINES"]), injury_report(blocks["LIVE_INJURY"]),
              (f"Weather: {len(blocks['LIVE_WEATHER']['teams'])} teams" if blocks["LIVE_WEATHER"]
               else "Weather: none, so no game-day forecast")]
    for name, obj in blocks.items():
        contract.validate(name, obj)   # a missing field fails the build, not the page
    # The build stamp is a hash of the data, never a clock. A timestamp would differ on every run,
    # so `land.ps1` would fold a new build.json into every branch and the page would announce
    # "new data" after a rebuild that changed nothing. The question the page actually asks is
    # "is what I am looking at still the content on main", and that is exactly what this answers.
    block_js = [f"const {name} = " + json.dumps(obj) + ";" for name, obj in blocks.items()]
    stamp = {
        "id": hashlib.sha256("".join(block_js).encode("utf-8")).hexdigest()[:12],
        "week": ((blocks.get("LIVE_PROPS") or {}).get("model") or {}).get("week"),
    }
    # A "</" inside a string (a headline quoting markup, say) would end the <script> early;
    # JSON reads "<\/" as the same two characters, and JS never sees the difference.
    injected = "\n".join(
        ["const HEADS = " + json.dumps(heads) + ";", "const HEADS_LG = " + json.dumps(heads_lg) + ";"]
        + block_js
        + ["const BUILD = " + json.dumps(stamp) + ";"]
    ).replace("</", "<\\/")
    tpl = assemble()
    body = tpl.replace("/*__HEADS__*/", injected)

    # The repo root is what Vercel serves, so that copy is a full HTML document; design/index.html
    # is the same page as a fragment (no doctype/head), which is what the Artifact publisher wants.
    page = f"{document_head()}\n{body}\n</body>\n</html>\n"

    report_sources(report, live, liveY, props, liveDfsYahoo, news, blocks["LIVE_PROFILES"], missing)
    return Build(page, body, report, heads, missing, stamp)


def main():
    b = render()
    (ROOT / "index.html").write_text(b.fragment, encoding="utf-8")
    (REPO / "index.html").write_text(b.page, encoding="utf-8")
    # Served at /build.json next to the page, under Vercel's static default (max-age=0,
    # must-revalidate), so an open tab's check costs a 304 until the data actually moves.
    (REPO / "build.json").write_text(json.dumps(b.stamp), encoding="utf-8")
    kb = len(b.page.encode("utf-8")) / 1024
    print(f"wrote {REPO/'index.html'} and {ROOT/'index.html'} ({kb:.0f} KB), "
          f"{write_heads(REPO)} heads to {HEADS_DIR}/")
    # One JSON per played game, for the drive strip to fetch on demand. Not injected: 39 KB a
    # game against a page that is already 2.2 MB. Not a function either -- a Vercel Python
    # function may not import pandas. Static files off the CDN, immutable once a game has ended.
    sched = load_schedule(DWR)
    if sched:
        written, skipped = pbp.write_games(pathlib.Path(DWR) / "cache", sched, REPO / "games")
        print(f"Games: {written} drive strips written to games/" +
              (f", {skipped} not played yet" if isinstance(skipped, int) else f" ({skipped})"))
    for line in b.report:
        print(line)


if __name__ == "__main__":
    main()
