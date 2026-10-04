"""The checker behind design/contract.py: walks a block against its spec and names every missing field.

contract.py holds the specs (data) and the public API (`problems`, `validate`); this file holds the
rules for reading a spec, plus the Breaking rail's per-kind shapes (WIRE_*), which `_wire_events`
reads and design/wire_watch.py cuts to. contract.py re-exports the WIRE_* names, so callers keep
`from contract import WIRE_EVENT`.
"""

# ff-jarvis's wire_watch (design/wire_watch.py), the Breaking rail. Per league a list of events;
# every event carries WIRE_EVENT and its kind's own keys. wire_watch.py cuts to exactly these and
# never fills a required one, so a field the producer dropped fails here by name. `headline`,
# `clears`, `practice`, `note` and the `over` of a need-drop may be null.
WIRE_EVENT = ["kind", "at", "key", "name", "pos", "team", "headline"]
WIRE_KIND = {
    "path": ["status", "clears", "because", "verdict"],
    "drop": ["by", "status", "clears", "verdict"],
    "status": ["from", "to", "practice", "note", "mine"],
    "adds": ["count"],
}
WIRE_BECAUSE = ["key", "name", "status", "practice", "note"]
# A drop's verdict: kind bench|need; `start` true with a `slot` when he would start there (the
# kind stays "bench"). An event's `status` may be "unknown", which the rail says as such.
WIRE_VERDICT = ["kind", "start", "slot", "over", "over_key", "margin"]
# Of the lists above, the keys a producer may leave out (wire_watch.py writes them as null).
WIRE_OPTIONAL = {"headline", "clears", "practice", "note", "over", "over_key", "start", "slot"}
# Keys only one kind may leave out. A path's `verdict` (2026-09-23) is a drop's verdict shape,
# what claiming the opened player does for my roster; a producer from before it sends none.
# A drop's verdict stays required.
WIRE_KIND_OPTIONAL = {"path": {"verdict"}}
# Each kind's sub-objects and their keys; one listed in WIRE_KIND_OPTIONAL may be null.
WIRE_SUBS = {"path": {"because": WIRE_BECAUSE, "verdict": WIRE_VERDICT}, "drop": {"verdict": WIRE_VERDICT}}


def _row_specs(spec):
    """`rows` is one (field, keys) pair, or a list of them for a block with two row lists."""
    if not spec:
        return []
    return list(spec) if isinstance(spec[0], (list, tuple)) else [spec]


def problems(name, obj, spec, limit=8):
    """Missing fields of `obj` against its `spec`, as `LIVE_X.key` / `LIVE_X.rows[i].key`, at most `limit`."""
    if obj is None:
        return []
    out = [f"{name}.{k}" for k in spec["keys"] if k not in obj]
    for field, keys in _row_specs(spec.get("rows")):
        if field and isinstance(obj.get(field), list):
            for i, row in enumerate(obj[field]):
                out += [f"{name}.{field}[{i}].{k}" for k in keys if k not in row]
                if len(out) >= limit:
                    break
    for field, keys in spec.get("objs", []):
        if isinstance(obj.get(field), dict):
            out += [f"{name}.{field}.{k}" for k in keys if k not in obj[field]]
    for field, sub, keys in spec.get("sub_rows", []):
        inner = (obj.get(field) or {}).get(sub)
        if isinstance(inner, list):
            for i, row in enumerate(inner):
                out += [f"{name}.{field}.{sub}[{i}].{k}" for k in keys if k not in row]
                if len(out) >= limit:
                    break
    field, keys = spec.get("map", (None, []))
    if field and isinstance(obj if field == "." else obj.get(field), dict):   # "." is the block itself
        for key, row in (obj if field == "." else obj[field]).items():
            out += [f"{name}{'' if field == '.' else '.' + field}[{key!r}].{k}" for k in keys if not isinstance(row, dict) or k not in row]
            if len(out) >= limit:
                break
    for field, sub, keys in spec.get("nested", []):
        if not isinstance(obj.get(field), dict):
            continue
        for key, row in obj[field].items():
            inner = row.get(sub) if isinstance(row, dict) else None
            if isinstance(inner, dict):
                out += [f"{name}.{field}[{key!r}].{sub}.{k}" for k in keys if k not in inner]
    out += _row_children(name, obj, spec)
    for check in spec.get("checks", []):   # a block whose nested shape is beyond the row specs
        out += check(obj)
    if spec.get("wire_events"):
        out += _wire_events(name, obj)
    return out[:limit]


def _wire_events(name, obj):
    """Each league's `events`, each event by its kind, and the kind's one sub-object."""
    out = []
    for lg, block in (obj.get("leagues") or {}).items():
        at = f"{name}.leagues[{lg!r}]"
        if not isinstance(block, dict) or not isinstance(block.get("events"), list):
            out.append(f"{at}.events")
            continue
        for i, e in enumerate(block["events"]):
            here = f"{at}.events[{i}]"
            kind = e.get("kind")
            if kind not in WIRE_KIND:
                out.append(f"{here}.kind")
                continue
            out += [f"{here}.{k}" for k in WIRE_EVENT + WIRE_KIND[kind] if k not in e]
            for sub, keys in WIRE_SUBS.get(kind, {}).items():
                if isinstance(e.get(sub), dict):
                    out += [f"{here}.{sub}.{k}" for k in keys if k not in e[sub]]
                elif sub in e and not (e[sub] is None and sub in WIRE_KIND_OPTIONAL.get(kind, ())):
                    out.append(f"{here}.{sub}")
    return out


def _row_children(name, obj, spec):
    """Objects hanging off each row: `row_objs` is a nullable sub-object whose keys must all be
    there when it is present; `row_maps` is a {key: object} map per row, each object checked,
    and its own nullable sub-objects with it."""
    out = []
    for field, sub, keys in spec.get("row_objs", []):
        for i, row in enumerate(obj.get(field) or []):
            inner = row.get(sub)
            if isinstance(inner, dict):
                out += [f"{name}.{field}[{i}].{sub}.{k}" for k in keys if k not in inner]
    for field, sub, keys, children in spec.get("row_maps", []):
        for i, row in enumerate(obj.get(field) or []):
            for key, inner in (row.get(sub) or {}).items():
                at = f"{name}.{field}[{i}].{sub}[{key!r}]"
                out += [f"{at}.{k}" for k in keys if not isinstance(inner, dict) or k not in inner]
                for child, ckeys in children.items():
                    c = inner.get(child) if isinstance(inner, dict) else None
                    if isinstance(c, dict):
                        out += [f"{at}.{child}.{k}" for k in ckeys if k not in c]
    return out
