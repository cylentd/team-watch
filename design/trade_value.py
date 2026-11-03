"""LIVE_TRADE_VALUE: every rostered player's trade value (2026-11-03), from ff-jarvis's trade_value.json
(model.season.trade_value; David: "you have to think of PAR").

Team > Trades > Value draws it: per league, each player's points over replacement (PAR) for the rest of the season,
the replacement level per position it is measured from, and what his manager's screen says he is worth beside our
rate. The page computes nothing: this cut keeps the fields the page reads, in the page's names (`n` for the name, as
the other blocks), and drops the rest (key, ros_pts, par_pg, seen, chips, draft_round, season_out, starters).

    {generated, week, ros_generated, po_weeks,
     leagues: {espn|yahoo|ayo: {replacement: {QB, RB, WR, TE}, me, teams, weeks_left,
                                players: [{slug, n, pos, team, holder, ros_pg, games, par, po_games, po_par, games_healthy,
                                           par_healthy, perc, gap, last2, injury, ir, rank, pos_rank}]}}}
    holder         the fantasy team that rosters him, null for a free agent or a waiver player
    par            (ros_pg - replacement[pos]) x games, rest of season, in that league's scoring; the list's order
    po_par         the same over the fantasy playoff weeks (`po_weeks`, those still to play); null on a file without them
    games_healthy  a what-if: his games at full attendance, only when he is not ruled out and his price counts 0.5+
                   fewer; par_healthy is PAR at those games. Never the price.
    perc, gap      his manager's view, points a game (the trade finder's `perc`), and perc - ros_pg; gap null with
                   no perceived value (a player ruled out this week)

None when ff-jarvis has written no file: Trades then has no Value tab and reads as it did. Judgment, not backtested
(PAR is a convention; perc an untested heuristic): numbers on the page, never a verdict word.
"""

import sources

TOP = ("generated", "week", "ros_generated", "po_weeks")
LEAGUE = ("replacement", "me", "teams", "weeks_left")
PLAYER = ("slug", "pos", "team", "holder", "ros_pg", "games", "par", "po_games", "po_par", "games_healthy", "par_healthy", "perc",
          "gap", "last2", "injury", "ir", "rank", "pos_rank")
POSITIONS = ("QB", "RB", "WR", "TE")


def load_trade_value():
    """ff-jarvis's trade_value.json: feed block `trade_value` first, the file second; None when neither exists."""
    return sources.feed_block(("trade_value",), "leagues") or sources.read_first(sources.DWR / "trade_value.json")


def _league(body):
    players = [{**{k: p.get(k) for k in PLAYER}, "n": p.get("name")} for p in body.get("players") or [] if p.get("slug")]
    return {**{k: body.get(k) for k in LEAGUE}, "players": players}


def live_trade_value(raw):
    if not raw or not raw.get("leagues"):
        return None
    leagues = {k: _league(b) for k, b in raw["leagues"].items()}
    leagues = {k: b for k, b in leagues.items() if b["players"]}
    return {**{k: raw.get(k) for k in TOP}, "leagues": leagues} if leagues else None


def problems(block):
    """What the page could not draw: a position it does not know, a league with no replacement level for one, or a
    list out of PAR order (the page reads the order as the ranking)."""
    out = []
    for key, lg in block["leagues"].items():
        if set(lg["replacement"] or {}) != set(POSITIONS):
            out.append(f"LIVE_TRADE_VALUE {key}: replacement is not QB, RB, WR, TE")
        pars = [p["par"] for p in lg["players"]]
        if any(not isinstance(x, (int, float)) for x in pars) or pars != sorted(pars, reverse=True):
            out.append(f"LIVE_TRADE_VALUE {key}: players not in PAR order")
        out += [f"LIVE_TRADE_VALUE {key}: {p['n']} has position {p['pos']}" for p in lg["players"] if p["pos"] not in POSITIONS]
    return out


def report(block):
    if not block:
        return "Trade value: none, so Trades has no Value tab"
    return "Trade value: " + ", ".join(f"{k} {len(b['players'])}" for k, b in block["leagues"].items()) \
        + f" players, priced {block['ros_generated'] or block['generated']}"
