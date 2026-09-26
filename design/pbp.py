"""nflverse play-by-play -> the drive strip's payload. The second producer of one shape.

`api/game.py` shapes an ESPN summary into drives the strip draws. This shapes nflverse's
play-by-play into the same thing, and the two are interchangeable by design:

    past games   nflverse, written to games/<game_id>.json at build time, served as a static file
    live games   ESPN, through /api/game, the only source that has a drive while it is happening

Why a second producer rather than one. ESPN's public site API sits behind an Akamai bot wall that
answers this client with 403 in a tenth of a second (measured 2026-09-22 and again 2026-09-23;
`api/live.py` reaches a *different* ESPN host, cookie-authed, and is unaffected). Whether Vercel's
egress is treated the same way is not knowable from here. Every game in a player's game log is a
finished game, so the path that carries almost all of the value does not have to depend on it.

And nflverse is the better source for a finished game anyway. ESPN states air yards, yards after
the catch, the tackler and the fumble recovery inside a sentence, which `api/game.py` has to mine
with regular expressions; nflverse states them as columns. Where the two disagree about a name,
this file is the one that did not have to guess.

The shape is the contract. tests/test_pbp.py checks it against api/game.py's output for the one
game both sources describe -- same drives, same plays, same yard lines -- so a change to either
producer that breaks the other fails the build.
"""
import json
import math
import pathlib
import re

ORD = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}

# What the strip can act out. A sack is drawn as a run backwards, because that is what it looks
# like on the field; a kneel is a rush for the same reason (and it is what ESPN calls one, which
# is the whole of the 132-vs-129 difference between the two producers on the checked game).
RUSHING = {"run", "qb_kneel"}
# Drive bookkeeping: real rows, nothing a figure can act out. `no_play` is a penalty that wiped
# the snap out. Listed rather than fallen through to, so an unfamiliar play_type is reported.
BOOKKEEPING = {"kickoff", "punt", "extra_point", "no_play", "qb_spike", "penalty", "timeout"}

# "17-J.Allen" -> "J.Allen": the jersey number is in every nflverse description and in none of the
# page's prose. Then "J.Allen" -> "J. Allen", the spelling the strip's name join uses throughout.
JERSEY = re.compile(r"\b\d{1,2}-(?=[A-Z])")
CLOCK_PREFIX = re.compile(r"^\(\d?\d:\d\d\)\s*")
SHOTGUN = re.compile(r"^\((?:Shotgun|No Huddle|No Huddle, Shotgun|Punt formation|Field Goal formation)\)\s*")


def tidy(name):
    """'J.Allen' -> 'J. Allen'. None stays None: some plays name nobody, which is an answer."""
    if not name or (isinstance(name, float) and math.isnan(name)):
        return None
    return re.sub(r"\.\s*", ". ", str(name)).strip()


def text(desc):
    """nflverse's description as the caption should read it: no jersey numbers, no game clock
    repeated from the row it is already on, no formation note."""
    out = JERSEY.sub("", str(desc or ""))
    return SHOTGUN.sub("", CLOCK_PREFIX.sub("", out)).strip()


def num(v):
    """A pandas cell as a plain number, or None. NaN is 'not stated', never 0."""
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f


def spot(yardline_100, home_ball):
    """One end-to-end scale, the same one api/game.py puts every play on: 0 is the home goal line
    and 100 the away one. nflverse's `yardline_100` counts down to the end zone the possessing
    team is attacking, so which team has the ball is what flips it."""
    y = num(yardline_100)
    if y is None:
        return None
    return 100 - y if home_ball else y


def kind(r):
    """Which of the strip's five play kinds this row is, or None when it is bookkeeping."""
    pt = r.get("play_type")
    if pt in RUSHING:
        return "rush"
    if pt == "field_goal":
        return "fg"
    if pt != "pass":
        return None
    if num(r.get("interception")):
        return "int"
    if num(r.get("sack")):
        return "rush"                     # yards lost on the ground, drawn as a run backwards
    return "pass" if num(r.get("complete_pass")) else "inc"


def down_distance(r):
    """'1st & 10 · BUF 25'. nflverse carries the two halves separately; the strip wants the line
    ESPN's `shortDownDistanceText` would have given it."""
    down, togo, at = num(r.get("down")), num(r.get("ydstogo")), r.get("yrdln")
    if down is None:
        return str(at or "")
    label = ORD.get(int(down), f"{int(down)}th")
    goal = togo is not None and num(r.get("yardline_100")) == togo
    return f"{label} & {'Goal' if goal else int(togo or 0)}" + (f" · {at}" if at else "")


def clock(r):
    """'Q1 9:09'. nflverse zero-pads the minute and ESPN does not, and a scoreboard that reads
    09:09 from one source and 9:09 from the other is one source showing through. Broadcast
    convention, and what the strip was designed against, is no leading zero."""
    q, t = num(r.get("qtr")), r.get("time")
    t = re.sub(r"^0(?=\d:)", "", str(t)) if t else ""
    return f"Q{int(q)} {t}" if q and t else t


def tacklers(r):
    """Everyone nflverse credits with the tackle, first-named first. An assisted tackle names two
    (38% of 2026's runs through week 2), and the strip draws the second man arriving: it is the
    one per-play fact that says a back took more than one man to bring down. Broken tackles are
    not a per-play column anywhere nflverse publishes; the game total comes from PFR (brk)."""
    out = []
    for key in ("solo_tackle_1_player_name", "assist_tackle_1_player_name", "assist_tackle_2_player_name",
                "tackle_with_assist_1_player_name", "tackle_with_assist_2_player_name"):
        who = tidy(r.get(key))
        if who and who not in out:
            out.append(who)
    return out


def fumble(r, end, dirn):
    """The loose ball: where it settled, who got it, and whether possession changed. nflverse
    states the recovery as yards gained from the end of the play, so the spot is derived."""
    if not num(r.get("fumble")):
        return None
    by = tidy(r.get("fumble_recovery_1_player_name")) or tidy(r.get("forced_fumble_player_1_player_name"))
    gained = num(r.get("fumble_recovery_1_yards")) or 0
    return {"spot": max(0, min(100, end + dirn * gained)), "by": by or "",
            "lost": bool(num(r.get("fumble_lost")))}


def carriers(r, k):
    """(who the play belongs to, the passer when there is one). A sack belongs to the passer --
    he is the one the yards came off, and the one the figure on the field is."""
    if k == "rush":
        if num(r.get("sack")):
            return tidy(r.get("passer_player_name")), None
        return tidy(r.get("rusher_player_name")), None
    if k == "fg":
        return tidy(r.get("kicker_player_name")), None
    return tidy(r.get("receiver_player_name")), tidy(r.get("passer_player_name"))


def play_row(r, home_ball):
    """One play as the strip draws it, or None when it is drive bookkeeping."""
    k = kind(r)
    if k is None:
        return None
    start = spot(r.get("yardline_100"), home_ball)
    if start is None:
        return None
    dirn = 1 if home_ball else -1
    gained = num(r.get("yards_gained")) or 0
    who, qb = carriers(r, k)
    row = {"k": k, "from": start, "to": max(0, min(100, start + dirn * gained)),
           "tx": text(r.get("desc")), "dd": down_distance(r), "clock": clock(r), "who": who}
    if qb or k in ("pass", "inc", "int"):
        row["qb"] = qb
    if num(r.get("down")) and num(r.get("ydstogo")) is not None:
        row["line"] = start + dirn * num(r.get("ydstogo"))
    if k == "pass":
        yac = num(r.get("yards_after_catch"))
        if yac is not None:
            row["yac"] = yac
    if k == "inc":
        air = num(r.get("air_yards"))
        if air is not None:
            row["depth"] = abs(air)        # how far it was thrown: what the arc is drawn to
    if k == "int":
        air = num(r.get("air_yards")) or 0
        row["to"] = max(0, min(100, start + dirn * air))
        row["ret"] = num(r.get("return_yards")) or 0
    if k == "fg":
        row["to"] = 100 if home_ball else 0
        row["made"] = r.get("field_goal_result") == "made"
    if num(r.get("touchdown")) and r.get("td_team") == r.get("posteam"):
        row["td"] = True
    fum = fumble(r, row["to"], dirn)
    if fum:
        row["fum"] = fum
    tks = tacklers(r)
    if tks:
        row["tk"] = tks[0]
    if len(tks) > 1:
        row["tk2"] = tks[1]
    if k == "rush" and num(r.get("sack")):
        row["sack"] = True                 # drawn as a run backwards; the flag is what says why
    return row


# Every column that names somebody, paired with the id column beside it. The ids are GSIS ids,
# which nflverse's own roster file also carries -- so the name a face hangs on is a join, not a
# string match. api/game.py has to reduce "James Cook III" to "J.Cook" and hope; this does not.
NAMED = [("passer_player_name", "passer_player_id"), ("receiver_player_name", "receiver_player_id"),
         ("rusher_player_name", "rusher_player_id"), ("kicker_player_name", "kicker_player_id"),
         ("solo_tackle_1_player_name", "solo_tackle_1_player_id"),
         ("assist_tackle_1_player_name", "assist_tackle_1_player_id"),
         ("assist_tackle_2_player_name", "assist_tackle_2_player_id"),
         ("interception_player_name", "interception_player_id"),
         ("fumble_recovery_1_player_name", "fumble_recovery_1_player_id")]


def athletes(rows, roster):
    """(faces, names), keyed the way the play text writes a name -- the same two tables
    api/game.py ships, built by id instead of by spelling.

    `roster` is nflverse's own roster frame for the season, indexed by gsis_id."""
    faces, names = {}, {}
    for r in rows:
        for name_col, id_col in NAMED:
            who, gsis = tidy(r.get(name_col)), r.get(id_col)
            if not who or not gsis or gsis not in roster.index:
                continue
            row = roster.loc[gsis]
            full, head = row.get("full_name"), row.get("headshot_url")
            if isinstance(full, str):
                names.setdefault(full, who)
            if isinstance(head, str) and head:
                faces.setdefault(who, head)
    return faces, names


def drive_rows(rows, home_abbr):
    """One entry per drive that has a play the strip can draw, in order."""
    out, seen = [], {}
    for r in rows:
        key = num(r.get("fixed_drive"))
        if key is None:
            continue
        seen.setdefault(key, []).append(r)
    for key in sorted(seen):
        raw = seen[key]
        team = next((r.get("posteam") for r in raw if r.get("posteam")), None)
        if not team:
            continue
        home_ball = team == home_abbr
        plays = [p for p in (play_row(r, home_ball) for r in raw) if p]
        if not plays:
            continue
        before, after = drive_score(raw, home_ball)
        result = str(raw[0].get("fixed_drive_result") or "")
        out.append({
            "team": team, "dir": 1 if home_ball else -1, "result": result,
            "label": f"{team} drive, {len(plays)} plays, {result.lower()}",
            "clock": plays[0]["clock"], "score": before,
            "end": {"dd": result, "tx": _drive_line(raw, plays), "score": after},
            "plays": plays,
        })
    return out


def drive_score(raw, home_ball):
    """([home, away] before the drive, [home, away] after it).

    Two different columns, because nflverse states them from two different points of view.
    `posteam_score` is the score BEFORE the play, from the possessing team's side, so the first
    row of a drive gives the state it opened in without a drive that opens with a score
    inheriting it. `total_home_score` is the score AFTER the play, already the right way round.
    """
    first = raw[0]
    ps, ds = num(first.get("posteam_score")), num(first.get("defteam_score"))
    if ps is None or ds is None:
        before = [0, 0]
    else:
        before = [int(ps), int(ds)] if home_ball else [int(ds), int(ps)]
    scored = [r for r in raw if num(r.get("total_home_score")) is not None]
    if not scored:
        return before, before
    return before, [int(num(scored[-1].get("total_home_score")) or 0),
                    int(num(scored[-1].get("total_away_score")) or 0)]


def _drive_line(raw, plays):
    yards = sum(abs(p["to"] - p["from"]) for p in plays)
    return f"{len(plays)} plays, {round(yards)} yards"


def unknown_types(rows):
    """Play types the shaping neither drew nor recognised as bookkeeping. Named, not swallowed."""
    out = {}
    for r in rows:
        pt = r.get("play_type")
        if pt and pt not in BOOKKEEPING and pt not in RUSHING and pt not in ("pass", "field_goal"):
            out[pt] = out.get(pt, 0) + 1
    return out or None


def write_games(cache, schedule, out_dir):
    """One games/<game_id>.json per game nflverse has played, for the page to fetch on demand.

    Static files rather than injected data, and rather than a server. Injecting them is out --
    39 KB a game and 272 games in a season is five times the whole page. A server is out too: a
    Vercel Python function may not import pandas (requirements.txt lists `anthropic` and nothing
    else, or Vercel stops treating these as file-based functions at all). A static file is served
    from the CDN, costs 8 KB gzipped, and is immutable the moment the game ends.

    Returns (written, skipped). Needs pandas, so it is imported here rather than at module load:
    everything above this line is pure and the tests drive it with plain dicts.
    """
    import pandas as pd                                          # noqa: PLC0415

    season = _season(schedule)
    pbp_path = pathlib.Path(cache) / f"pbp_{season}.parquet"
    roster_path = pathlib.Path(cache) / f"roster_{season}.parquet"
    if not pbp_path.exists() or not roster_path.exists():
        return 0, "no nflverse cache"

    frame = pd.read_parquet(pbp_path)
    roster = pd.read_parquet(roster_path).set_index("gsis_id")
    by_id = {(g["home"], g["away"], g["week"]): g for g in schedule["games"]}
    kits = json.loads((pathlib.Path(__file__).parent / "kits.json").read_text(encoding="utf-8"))["kits"]
    brk = broken_tackles(pathlib.Path(cache) / f"adv_wk_rush_{season}.parquet")
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written, skipped = 0, 0
    for game_id, rows in frame.groupby("game_id", sort=True):
        records = rows.where(rows.notna(), None).to_dict("records")
        home, away = rows.home_team.iloc[0], rows.away_team.iloc[0]
        meta = by_id.get((_espn_code(home), _espn_code(away), int(rows.week.iloc[0])), {})
        try:
            payload = shape(records, roster, dict(meta, game_id=str(game_id), home=home, away=away,
                                                  kits=kits, brk=brk.get(str(game_id))))
        except LookupError:
            skipped += 1                                         # scheduled, not played
            continue
        (out_dir / f"{game_id}.json").write_text(
            json.dumps(payload, separators=(",", ":")), encoding="utf-8")
        written += 1
    return written, skipped


def broken_tackles(path):
    """{game_id: {full name: broken tackles}} from PFR's weekly advanced rushing file, running and
    receiving together (a back breaks tackles after the catch too). PFR states this per game and
    never per play, which is why the strip says it on the play card and never acts out a miss.
    Missing file -> {}: the count is a line on the card, not something a game needs to draw."""
    import pandas as pd                                          # noqa: PLC0415

    if not pathlib.Path(path).exists():
        return {}
    out = {}
    for r in pd.read_parquet(path).itertuples():
        n = (num(r.rushing_broken_tackles) or 0) + (num(r.receiving_broken_tackles) or 0)
        if n and isinstance(r.pfr_player_name, str):
            out.setdefault(str(r.game_id), {})[r.pfr_player_name] = n
    return out


def _season(schedule):
    """The NFL season, which is NOT the year of the last kickoff: a season that opens in
    September ends in January, so the largest year in the schedule is the wrong one and nflverse
    files it under the earlier. The game_id carries it outright ('2026_02_DET_BUF')."""
    years = [int(str(g["id"])[:4]) for g in schedule["games"] if str(g.get("id", ""))[:4].isdigit()]
    return max(years) if years else min(int(str(g.get("kickoff", "0"))[:4]) for g in schedule["games"])


def _espn_code(code):
    """The schedule speaks ESPN's dialect (LAR, WSH); nflverse's play rows do not. Imported from
    the module that owns that table rather than written out again -- it is already one table in
    two places too many (it also ships to the page inside LIVE_SCHEDULE.alias)."""
    from schedule import TO_ESPN                                 # noqa: PLC0415
    return TO_ESPN.get(code, code)


def shape(rows, roster, meta):
    """The whole game as the strip draws it. `meta` carries what the play rows do not: the two
    clubs' codes and the ESPN event id, both of which the schedule already knows.

    Raises LookupError when no drive carried a play the strip can draw, which is what an
    unplayed game looks like -- worth saying, rather than drawing an empty field.
    """
    home, away = meta["home"], meta["away"]
    drives = drive_rows(rows, home)
    if not drives:
        raise LookupError(f"{meta.get('game_id')} carried no play the strip can draw")
    faces, names = athletes(rows, roster)
    last = drives[-1]["end"]["score"]
    kits = meta.get("kits") or {}
    side = lambda abbr, score: dict({"abbr": abbr, "name": abbr, "score": score},
                                    **({"kit": kits[abbr]} if abbr in kits else {}))
    # PFR's per-game broken tackles, keyed the way the play text spells a name. Only players this
    # game's rows name, and only a count above zero: "broke 0 tackles" is not worth a line.
    brk = {names[full]: int(n) for full, n in (meta.get("brk") or {}).items() if full in names and n}
    return {
        "event": str(meta.get("espn") or ""), "game": meta.get("game_id"),
        "state": "post", "detail": meta.get("detail") or "Final",
        "source": "nflverse",
        "home": side(home, last[0]),
        "away": side(away, last[1]),
        **({"brk": brk} if brk else {}),
        "current": len(drives) - 1,
        "drives": drives, "faces": faces, "names": names,
        "unknownPlayTypes": unknown_types(rows),
    }
