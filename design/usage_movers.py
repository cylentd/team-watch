"""LIVE_USAGE_MOVERS: the players whose work grew most week over week (2026-10-06), from ff-jarvis's usage_movers.json
(model.season.usage_movers; the producer's docstring is the field contract, METHODOLOGY 12.105).

Descriptive and untested, and the file's own `label` says so. The Digest draws one card per row. The page computes
nothing and picks nothing: the file's order (biggest `change` first) is kept, and a row's words are Claude's `line`
or, when it failed ff-jarvis's number check, the template `fact` (the file already puts the fact in `line` then; this
cut does the same for a file that left `line` empty).

    {season, week, asof, from_week, to_week, label, llm,
     rows: [{slug, name, pos, team, metric "tgt_pct"|"snap", was, now, change, spark [3 weeks, oldest first, null where
             he has no row], targets, carries (null when the grid has none), teammate {name, was, now}|null, fact, line,
             source "claude"|"template"}]}

The cut keeps the keys the file has and fills none: a field ff-jarvis dropped is a missing key that fails the build by
name (design/contract.py), not a null the page draws as a blank card. `nums`, the producer's check of its own line,
stays behind. None when ff-jarvis has written no file: the Digest then draws no such rows.
"""
import sources

TOP = ("season", "week", "asof", "from_week", "to_week", "label", "llm")
ROW = ("slug", "name", "pos", "team", "metric", "was", "now", "change", "spark", "targets", "carries", "teammate", "fact", "source")
MATE = ("name", "was", "now")


def load_usage_movers():
    """The ff-jarvis file (usage_movers.json): feed block `usage_movers` first, the file second; None when neither
    exists. A file with no rows still counts (it says "nothing moved"), so the feed test is on `asof`. Lives here, not
    in sources.py, which is at its 500-line budget (tests/test_budgets.py)."""
    return sources.feed_block(("usage_movers",), "asof") or sources.read_first(sources.DWR / "usage_movers.json")


def _row(r):
    row = {k: r[k] for k in ROW if k in r}
    line = r.get("line") or r.get("fact")
    if line:
        row["line"] = line
    elif "line" in r:
        row["line"] = line   # present and empty: `problems` names it
    return row


def live_usage_movers(raw):
    """None when ff-jarvis has written no file."""
    if not raw or not isinstance(raw.get("rows"), list):
        return None
    return {**{k: raw[k] for k in TOP if k in raw}, "rows": [_row(r) for r in raw["rows"]]}


def problems(block):
    """What design/contract.py's row spec cannot say: a spark is 3 weeks, a teammate is {name, was, now} when there is
    one, and a line that is there has words. A key that is absent is the row spec's to name, not repeated here."""
    out = []
    for i, r in enumerate((block or {}).get("rows") or []):
        at = f"LIVE_USAGE_MOVERS.rows[{i}]"
        if "spark" in r and not (isinstance(r["spark"], list) and len(r["spark"]) == 3):
            out.append(f"{at}.spark")
        if isinstance(r.get("teammate"), dict):
            out += [f"{at}.teammate.{k}" for k in MATE if k not in r["teammate"]]
        if "line" in r and not r["line"]:
            out.append(f"{at}.line")
    return out


def report(block):
    if not block:
        return "Usage movers: none, so the Digest has no such rows"
    return f"Usage movers: week {block['week']}, {len(block['rows'])} rows"
