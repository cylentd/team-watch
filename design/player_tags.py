"""LIVE_PLAYER_TAGS: player tags (2026-10-08, ledger #41), from ff-jarvis's player_tags block (`model.season.player_tags`,
METHODOLOGY 12.114 and 12.118). Drawn as pills on Roster rows and Ranks rows, and explained one plain line each in the
profile. The file holds numbers only; every word is the page's (content.json `tags.*`, keyed by tag and kind).

David's decisions (2026-10-08): show RISING, TRENDING and POTENTIAL, the last under the name Sleeper. LUCKY is hidden
until ff-jarvis re-tests a sharper rule (it flags elite players whose skill beats their workload). ff-jarvis's own
SLEEPER tag is never shown ("a starter on the waiver almost never happens; if he is, the other tags already cover him");
ff-jarvis stopped writing it (0bb6610; `league` is always null and never read here). Both are dropped by the one `SHOWN`
filter below. POTENTIAL comes one entry per usage signal; the effect
(`rules.POTENTIAL.thresholds.effect_xfp_pg`) is said only for the signals the file names in `effect_signals`, never for
VACATED. `potential_forward` (the descriptive weekly record) is not read: its record counts frozen weeks only, and the
page does not show it yet.

    {season, week, through, last_n, hours, effect, effect_signals, alias,
     players: {key: [{tag, kind: tested|fact, nums: {name: number, signal?: str}}]}}

    key            ff-jarvis's: `highlights_candidates.slugify` of the name, or `<slug>-<team slug>` when two tagged players
                   share a name. Passed through; the page tries the plain slug, then slug-team in its own spelling and in
                   nflverse's (`alias`, nflverse -> page, signals.TEAM_ALIAS).
    last_n         RISING's games counted (the words say "last 3 games")
    hours          TRENDING's window (the words say "last 24 hours")
    effect         POTENTIAL's effect in expected points a game, or None; `effect_signals` the signals it belongs to

None when ff-jarvis has written no file, or no shown tag survives: the rows and the profile draw no tags.
"""
from signals import TEAM_ALIAS
from sources import DWR, feed_block, read_first

# The tags the page shows; any other is dropped here. LUCKY is hidden until ff-jarvis re-tests a sharper rule (David,
# 2026-10-08, ledger #41 2a: it flags elite players whose skill beats their workload).
SHOWN = ("RISING", "TRENDING", "POTENTIAL")
KINDS = ("tested", "fact")
SIGNALS = ("VACATED", "ROOKIE_RAMP", "ROUTES_FIRST", "EFFICIENT_PARTTIMER")   # potential_forward_schema.FLAGS
NEEDS = {"RISING": ("last", "earlier"), "TRENDING": ("rank", "adds"), "POTENTIAL": ("signal",)}


def load_player_tags():
    """ff-jarvis's player_tags block: feed block `player_tags` first, then `player_tags.json`; None when neither exists.
    Kept here, not in sources.py, which is at its line budget (tests/test_budgets.py)."""
    return feed_block(("player_tags",), "players") or read_first(DWR / "player_tags.json")


def _thresholds(raw, tag):
    return (((raw.get("rules") or {}).get(tag) or {}).get("thresholds")) or {}


def _entries(es):
    return [{"tag": e.get("tag"), "kind": e.get("kind"), "nums": e.get("nums")}
            for e in es or [] if isinstance(e, dict) and e.get("tag") in SHOWN]


def live_player_tags(raw):
    """The block, or None without a file or a shown tag."""
    if not raw or not raw.get("players"):
        return None
    players = {k: es for k, es in ((k, _entries(v)) for k, v in raw["players"].items()) if es}
    if not players:
        return None
    pot = _thresholds(raw, "POTENTIAL")
    effect = pot.get("effect_xfp_pg")
    return {"season": raw.get("season"), "week": raw.get("week"), "through": raw.get("through"),
            "last_n": _thresholds(raw, "RISING").get("last_n"), "hours": _thresholds(raw, "TRENDING").get("hours"),
            "effect": effect, "effect_signals": list(pot.get("effect_signals") or []) if effect is not None else [],
            "alias": dict(TEAM_ALIAS), "players": players}


def problems(block):
    """The nested shape `contract.py` cannot say with a row spec: each entry's tag, kind and the numbers its words need."""
    out = []
    for key, es in sorted(((block or {}).get("players") or {}).items()):
        for i, e in enumerate(es):
            at = f"LIVE_PLAYER_TAGS.players[{key!r}][{i}]"
            if e.get("tag") not in SHOWN:
                out.append(f"{at}.tag {e.get('tag')!r}")
                continue
            if e.get("kind") not in KINDS:
                out.append(f"{at}.kind {e.get('kind')!r}")
            nums = e.get("nums") if isinstance(e.get("nums"), dict) else {}
            out += [f"{at}.nums.{k}" for k in NEEDS[e["tag"]] if nums.get(k) is None]
            if e["tag"] == "POTENTIAL" and nums.get("signal") is not None and nums["signal"] not in SIGNALS:
                out.append(f"{at}.nums.signal {nums['signal']!r}")
    return out


def report(block):
    if not block:
        return "Player tags: no player_tags block, so no tags on rows or the profile"
    n = {}
    for es in block["players"].values():
        for e in es:
            n[e["tag"]] = n.get(e["tag"], 0) + 1
    counts = ", ".join(f"{k} {v}" for k, v in sorted(n.items()))
    return f"Player tags: week {block['week']}, {len(block['players'])} players ({counts})"
