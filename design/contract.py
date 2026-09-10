"""The shape each injected data block must have, checked where the data enters the page.

build.py injects six `const LIVE_*` blocks. The JS reads fixed field names off them (see
src/js/data/*.js); a field renamed or dropped on the Python side used to show up as a blank
panel or a console error on the deployed page. Now it fails the build.

The lists below are the fields the JS dereferences (top-level keys, then the keys read off each
row). A block may be None -- that is "source not available", and the page falls back to its
sample -- but a block that is present must be whole. Null values are fine; absent keys are not.
"""

CONTRACT = {
    "LIVE_ESPN": {
        "keys": ["name", "league", "updated", "roster"],
        "rows": ("roster", ["n", "pos", "team", "slot", "slug", "status"]),
    },
    "LIVE_YAHOO": {
        "keys": ["name", "league", "updated", "roster"],
        "rows": ("roster", ["n", "pos", "team", "slug"]),
    },
    "LIVE_FEED": {
        "keys": ["generated", "steps", "usage_ready", "pool_size", "fetched"],
    },
    "LIVE_NEWS": {
        "keys": ["items"],
        "rows": ("items", ["id", "title", "desc", "impact", "team", "categories", "link", "when"]),
    },
    "LIVE_PROPS": {
        "keys": ["fetched", "events", "books", "players", "windows", "model", "props", "wrcb", "logs"],
        "rows": ("props", ["n", "slug", "pos", "team", "mkt", "game", "commence", "kick", "line",
                           "book", "books", "mine", "win"]),
        # logs[slug] = {g: [[year, week, opp], ...], v: {MKT: [value per game]}} -- gamelog.js
        # indexes both, so a log missing either is a crash on expand, not a blank chart.
        "map": ("logs", ["g", "v"]),
    },
    "LIVE_DFS_YAHOO": {
        "keys": ["fetched", "modeled", "lined", "players"],
        "rows": ("players", ["n", "pos", "team", "sal", "proj", "src", "status", "slug", "game"]),
    },
}


class ContractError(SystemExit):
    """Raised as SystemExit so `python design/build.py` exits non-zero with the message."""


def problems(name, obj, limit=8):
    """Missing fields as `LIVE_X.key` / `LIVE_X.rows[i].key`, at most `limit` of them."""
    if obj is None:
        return []
    spec = CONTRACT[name]
    out = [f"{name}.{k}" for k in spec["keys"] if k not in obj]
    field, keys = spec.get("rows", (None, []))
    if field and isinstance(obj.get(field), list):
        for i, row in enumerate(obj[field]):
            out += [f"{name}.{field}[{i}].{k}" for k in keys if k not in row]
            if len(out) >= limit:
                break
    field, keys = spec.get("map", (None, []))
    if field and isinstance(obj.get(field), dict):
        for key, row in obj[field].items():
            out += [f"{name}.{field}[{key!r}].{k}" for k in keys if not isinstance(row, dict) or k not in row]
            if len(out) >= limit:
                break
    return out[:limit]


def validate(name, obj):
    bad = problems(name, obj)
    if bad:
        raise ContractError(f"contract: {name} is missing " + ", ".join(bad))
