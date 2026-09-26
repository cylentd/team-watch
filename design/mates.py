"""Every team in David's two leagues, so a leaguemate can pick theirs (leaguemates phase 1,
2026-09-25).

ff-jarvis already pulls all twelve rosters per league into espn_rosters.json and
league_rosters.json (`detail`: team name -> rows); the build used to keep only David's. The row
shapes live here, once, and build.py's LIVE_ESPN / LIVE_YAHOO use them for David's own team, so a
leaguemate's roster is drawn exactly like his.

Team names only, never an owner's name: the page is on a public URL (David, 2026-09-25). The
roster files are keyed by team name, and nothing else about the owner is read.

`slugify` is passed in, like waiver.py's: it lives in api/_espn.py, so a connected league's
players are slugged the same way at request time.
"""
# Yahoo's lineup slot names -> the ones the page uses. Anything else (QB, RB, WR, TE, K, BN) is
# already the page's name.
YAHOO_SLOT = {"W/R/T": "FLEX", "DEF": "DST", "D/ST": "DST", "IR": "OUT"}


def espn_rows(detail, available, badge, slugify):
    """ESPN rows -> the page's roster rows. `badge(name, espn_status)` is the Q/OUT badge (Sleeper
    first, ESPN's own field as the fallback; build.py owns that rule)."""
    out, flex = [], 0
    for p in detail:
        slot = p["slot"]
        if slot == "FLEX":
            flex += 1
            slot = f"FLX{flex}"
        elif slot == "BE":
            slot = "BN"
        elif slot == "IR":
            # Injured reserve is a bench spot, not a lineup one: the page's "OUT" group, the same
            # as Yahoo's (YAHOO_SLOT) and a connected league's (api/league.py). Passed through as
            # "IR" it counted as a starter, and the lineup warning named him (2026-09-25).
            slot = "OUT"
        name = p["name"].replace(" D/ST", "")
        slug = slugify(name)
        out.append({"n": name, "pos": "DST" if p["pos"] == "DEF" else p["pos"], "team": p["team"],
                    "slot": slot, "slug": slug if slug in available else None,
                    "status": badge(name, p.get("status"))})
    return out


def yahoo_rows(detail, available, slugify):
    """Yahoo rows -> the page's roster rows. The scrape carries no injury status."""
    out = []
    for p in detail:
        slug, slot = slugify(p["name"]), p.get("slot")
        out.append({"n": p["name"], "pos": "DST" if p["pos"] in ("DEF", "D/ST") else p["pos"],
                    "team": p["team"], "slot": YAHOO_SLOT.get(slot, slot),
                    "slug": slug if slug in available else None})
    return out


# Lineup order. David's own rows arrive in it from ff-jarvis; another team's ESPN rows arrive in
# whatever order ESPN listed them (2026-09-25: Big Nasty Nate's starters read RB, WR, FLX, RB).
SLOT_ORDER = ["QB", "RB", "WR", "TE", "FLX", "FLEX", "K", "DST", "D/ST", "BN", "OUT"]


def lineup_order(rows):
    """Stable sort by slot: QB, RB, WR, TE, flex, K, DST, bench, out; unknown slots last."""
    def rank(r):
        slot = r["slot"] or ""
        return next((i for i, s in enumerate(SLOT_ORDER) if slot.startswith(s)), len(SLOT_ORDER))
    return sorted(rows, key=rank)


def live_mates(espn, yahoo, available, badge, slugify):
    """LIVE_MATES: {teams: [{key, league, name, roster}]}, every team but David's in each league,
    by name. `espn` / `yahoo` are the parsed roster files, or None. The key is the league plus the
    team name's slug: a renamed team gets a new key, and a reader who picked it falls back to
    David's team (data/mates.js)."""
    teams = []
    for league, d, rows in (("espn", espn, lambda r: espn_rows(r, available, badge, slugify)),
                            ("yahoo", yahoo, lambda r: yahoo_rows(r, available, slugify))):
        if not d:
            continue
        for name in sorted(d["detail"], key=str.lower):
            if name != d["me"]:
                teams.append({"key": f"{league}-{slugify(name)}", "league": league, "name": name,
                              "roster": lineup_order(rows(d["detail"][name]))})
    return {"teams": teams} if teams else None


def slugs(mates):
    """Every leaguemate's player, for the headshots and the per-player blocks."""
    return [p["slug"] for t in (mates or {}).get("teams", []) for p in t["roster"] if p["slug"]]


def report(mates):
    if not mates:
        return "Leaguemates: none"
    by = {}
    for t in mates["teams"]:
        by[t["league"]] = by.get(t["league"], 0) + 1
    return "Leaguemates: " + ", ".join(f"{n} {k}" for k, n in sorted(by.items()))
