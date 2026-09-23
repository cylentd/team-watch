"""The Breaking rail's data: ff-jarvis's `wire_watch`, feed block `wire_watch` first, then
data/wire_watch.json, whichever was produced later. A tie reads the file: the producer writes the
file itself, and the feed only holds the last refresh's copy (the same tie rule as waiver.py).

Per league, a list of events, newest first: a path opening behind an injured starter, a useful
drop, a status change on one of my players, and aggregated adds. Every verdict and margin is the
producer's own; this file only trims to the fields the rail draws and reorders nothing.

Strict on purpose: the field lists are contract.py's, and a required field the producer did not
send stays missing here, so the contract fails the build and names it instead of the rail drawing
a blank. Only the keys in contract.WIRE_OPTIONAL are filled with null."""
import json
from datetime import datetime

from contract import WIRE_BECAUSE, WIRE_EVENT, WIRE_KIND, WIRE_OPTIONAL, WIRE_VERDICT

MAX_LEAGUES = 3


def _when(block):
    try:
        return datetime.fromisoformat(block.get("asof") or "")
    except (TypeError, ValueError):
        return None


def load_wire(feed_path, dwr_path):
    """The newer of the file and the feed block, the file on a tie; None when neither exists."""
    found = []
    try:
        path = dwr_path / "wire_watch.json"
        if path.exists():
            d = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(d.get("leagues"), dict):
                found.append(d)
    except (OSError, json.JSONDecodeError):
        pass
    try:
        block = (json.loads(feed_path.read_text(encoding="utf-8")).get("wire_watch") or {}).get("data")
        if block and isinstance(block.get("leagues"), dict):
            found.append(block)
    except (OSError, json.JSONDecodeError):
        pass
    dated = [b for b in found if _when(b)]
    if dated:
        return max(dated, key=_when)     # max() keeps the first of equals, and the file is first
    return found[0] if found else None


def _cut(d, keys):
    """The keys the rail reads: a required one only when present (so the contract sees the gap),
    an optional one always, null when absent."""
    if not isinstance(d, dict):
        return d
    return {k: d.get(k) for k in keys if k in d or k in WIRE_OPTIONAL}


def _event(e):
    kind = e["kind"]
    out = _cut(e, WIRE_EVENT + WIRE_KIND[kind])
    if kind == "path" and "because" in out:
        out["because"] = _cut(out["because"], WIRE_BECAUSE)
    if kind == "drop" and "verdict" in out:
        out["verdict"] = _cut(out["verdict"], WIRE_VERDICT)
    return out


def live_wire(feed_path, dwr_path):
    """LIVE_WIRE: {asof, leagues: {league: {events: [...]}}}, at most three leagues in the
    producer's order, events in the producer's order (newest first). An unknown kind is dropped:
    the rail has nothing to say about it."""
    block = load_wire(feed_path, dwr_path)
    if not block:
        return None
    leagues = {}
    for key, lg in list(block["leagues"].items())[:MAX_LEAGUES]:
        events = (lg or {}).get("events") or []
        leagues[key] = {"events": [_event(e) for e in events if isinstance(e, dict) and e.get("kind") in WIRE_KIND]}
    return {"asof": block.get("asof"), "leagues": leagues}


def report(w):
    """build.py's one-line summary of LIVE_WIRE."""
    if not w:
        return "Wire watch: no wire_watch.json/feed block, the rail says so"
    per = ", ".join(f"{k} {len(v['events'])}" for k, v in w["leagues"].items())
    return f"Wire watch: {per} events, as of {w['asof']}"
