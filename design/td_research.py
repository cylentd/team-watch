"""LIVE_TD_RESEARCH: the Slips view's Anytime TDs card (2026-10-09), from ff-jarvis's `td_research` block
(`model.season.td_research`, METHODOLOGY 12.133/12.134). The book's anytime-TD price per player, his tier
(LOCK, VALUE, MORE, LONG) and the six checks behind it. **It moves no number**: the page prints the book's
chance, the checks' facts and, last in the sheet, our model's chance as a second opinion.

The cut keeps only listed players (a tier), adds the page's slug, names the book whose price is shown, and keeps
the four rule values the group headers print. It also carries Claude's pending games (`claude_props` `games`
with `pending: "early"` and an `expected_at`), so the card can say when our picks arrive; the claude_props block
itself is left as it is.

    {season, week, asof, rules: {lock_min_p, value_min_p, value_min_checks, list_min_p}, record,
     players: [{slug, name, team, pos, opp, game, kickoff, status, tier, book: {p, price, book}, ours: {p} | null,
                evidence, checks: [{key, passed, value}]}],
     pending: [{kickoff, home, away, expected_at}]}
"""
from slips import slugify
from sources import DWR, feed_block, load_claude_props, read_first

TIERS = ("LOCK", "VALUE", "MORE", "LONG")
CHECKS = ("rz_work", "implied_total", "opp_allowed", "opp_missing", "near_td", "role_up")
RULES = ("lock_min_p", "value_min_p", "value_min_checks", "list_min_p")
ROW_KEYS = ("name", "team", "pos", "opp", "game", "kickoff", "status", "tier", "evidence", "checks")


def load_td_research():
    """Feed block `td_research` first, then `td_research.json`; None when neither exists. Kept here, not in
    sources.py, which is at its line budget."""
    return feed_block(("td_research",), "players") or read_first(DWR / "td_research.json")


def _rule(rules, k):
    v = (rules or {}).get(k)
    return v.get("value") if isinstance(v, dict) else v


def _book(b, order):
    """{p, price, book}: the book whose price is the one shown, in the producer's book order."""
    if not isinstance(b, dict) or not isinstance(b.get("p"), (int, float)):
        return None
    books = b.get("books") or {}
    name = next((k for k in [*order, *books] if books.get(k) == b.get("price")), None)
    return {"p": b["p"], "price": b.get("price"), "book": name}


def _row(r, order):
    out = {k: r.get(k) for k in ROW_KEYS}
    out["slug"] = slugify(r.get("name") or r.get("key") or "")
    out["book"] = _book(r.get("book"), order)
    ours = r.get("ours")
    out["ours"] = {"p": ours["p"]} if isinstance(ours, dict) and isinstance(ours.get("p"), (int, float)) else None
    out["checks"] = [{k: c.get(k) for k in ("key", "passed", "value")} for c in r.get("checks") or []]
    return out


def pending_games(claude_raw):
    """Claude's games still waiting on their early call, each with when the picks are expected."""
    games = (claude_raw or {}).get("games") or {}
    rows = games.values() if isinstance(games, dict) else games
    return [{k: g.get(k) for k in ("kickoff", "home", "away", "expected_at")} for g in rows
            if isinstance(g, dict) and g.get("pending") == "early" and g.get("expected_at") and g.get("kickoff")]


def live_td_research(raw, claude_raw=None):
    """The block, or None when ff-jarvis has written no file or listed nobody."""
    if not raw or not raw.get("players"):
        return None
    order = _rule(raw.get("rules"), "book_order") or ["DraftKings", "Consensus"]
    players = [_row(r, order) for r in raw["players"] if r.get("tier")]
    if not players:
        return None
    return {"season": raw.get("season"), "week": raw.get("week"), "asof": raw.get("asof"),
            "rules": {k: _rule(raw.get("rules"), k) for k in RULES},
            "record": {k: (raw.get("record") or {}).get(k) for k in TIERS},
            "players": players, "pending": pending_games(claude_raw)}


def load_live():
    return live_td_research(load_td_research(), load_claude_props())


def problems(block):
    """A tier or check word the page does not know fails the build, as a prop tier word does."""
    out = []
    for i, p in enumerate((block or {}).get("players") or []):
        if p.get("tier") not in TIERS:
            out.append(f"LIVE_TD_RESEARCH.players[{i}].tier {p.get('tier')!r}")
        if p.get("book") is not None and not isinstance(p["book"].get("p"), (int, float)):
            out.append(f"LIVE_TD_RESEARCH.players[{i}].book.p")
        out += [f"LIVE_TD_RESEARCH.players[{i}].checks[{j}].key {c.get('key')!r}"
                for j, c in enumerate(p.get("checks") or []) if c.get("key") not in CHECKS]
    return out


def report(block):
    if not block:
        return "Anytime TDs: no td_research block, so no card on Slips"
    n = {k: sum(1 for p in block["players"] if p["tier"] == k) for k in TIERS}
    return f"Anytime TDs: week {block['week']}, " + ", ".join(f"{k} {v}" for k, v in n.items()) + f", {len(block['pending'])} pending"
