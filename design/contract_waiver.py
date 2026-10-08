"""The shape of the Waivers blocks (contract.py's LIVE_WAIVER and LIVE_WAIVER_TEAMS), split out to keep contract.py in budget.

design/waiver.py, from ff-jarvis's model.season.waiver_packet: one card row per candidate (`players`), and
`leagues_meta` per league, in the order the cards draw their league rows. `summary` and `news_latest` may be
null. A league's `status` is fa | waiver | rostered | mine | unknown -- no value is enforced here: "unknown"
(the scrape could not tell) is a real answer, and the card says so rather than guessing FA (data/waiver.js
waiverListed). A league's `lane` is why its screen listed him (usage, role, open, insure, starter, injured), else null.
"""
import contract_checks   # design/contract_checks.py: the rules that read a spec

WAIVER_ROW = ["n", "slug", "pos", "team", "opp", "home", "tier", "weeks", "injury", "injury_note",
              "practice", "news_latest", "news_count", "leagues", "summary"]
# One league's view of a candidate (waiver.py `_league`). `verdict` and `drop` may be null; when
# either is an object the card reads every key below. `tier` is that league's own tier (added
# 2026-09-23); a packet from before it reads null there and the card falls back to the row's
# top-level `tier`, which ff-jarvis keeps as the best of the per-league ones.
WAIVER_LEAGUE = ["status", "clears", "need", "tier", "lane", "verdict", "drop"]
WAIVER_VERDICT = ["kind", "over", "slot", "margin"]
WAIVER_DROP = ["name", "pos", "pts"]
WAIVER_META = ["label", "faab_left", "faab_budget", "clears", "needs"]

LIVE_WAIVER = {
    "keys": ["date", "week", "clears", "leagues_meta", "players"],
    "rows": ("players", WAIVER_ROW),
    "map": ("leagues_meta", WAIVER_META),
    "row_objs": [("players", "summary", ["text", "src"])],
    "row_maps": [("players", "leagues", WAIVER_LEAGUE,
                  {"verdict": WAIVER_VERDICT, "drop": WAIVER_DROP})],
}


def teams_problems(obj):
    """Each team's block is a LIVE_WAIVER, so it is held to LIVE_WAIVER's fields (the page draws it with the
    same code), named by the team's key: `LIVE_WAIVER_TEAMS.teams['ayo-don-wick'].players[0].tier`."""
    out = []
    for key, team in (obj.get("teams") or {}).items():
        out += [p.replace("LIVE_WAIVER", f"LIVE_WAIVER_TEAMS.teams[{key!r}]", 1)
                for p in contract_checks.problems("LIVE_WAIVER", team, LIVE_WAIVER)]
    return out


# design/waiver.py live_waiver_teams (ledger #22): every other team's Waivers, {date, teams: {team key: a
# LIVE_WAIVER block}} keyed like design/mates.py. None without ff-jarvis's waiver_teams.json.
LIVE_WAIVER_TEAMS = {"keys": ["date", "teams"], "checks": [teams_problems]}
