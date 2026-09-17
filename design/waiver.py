"""The Waivers sub-tab's data: ff-jarvis's `model.season.waiver_packet`, feed block `waiver` first,
then data/waiver_packet.json, whichever was built later. Rows are cut to the fields the page draws;
every number is the packet's own, nothing is recomputed here.

Self-contained like news.py and signals.py: paths and slugify come in as arguments."""
import json

LANES = ("usage", "open", "role")


def load_packet(feed_path, dwr_path):
    found = []
    try:
        block = (json.loads(feed_path.read_text(encoding="utf-8")).get("waiver") or {}).get("data")
        if block and block.get("leagues"):
            found.append(block)
    except (OSError, json.JSONDecodeError):
        pass
    path = dwr_path / "waiver_packet.json"
    try:
        if path.exists():
            d = json.loads(path.read_text(encoding="utf-8"))
            if d.get("leagues"):
                found.append(d)
    except (OSError, json.JSONDecodeError):
        pass
    return max(found, key=lambda b: b.get("date") or "") if found else None


def _pick(d, *keys):
    return {k: d.get(k) for k in keys} if isinstance(d, dict) else None


def _row(p, slugify):
    game = p.get("game") or {}
    return {
        "n": p.get("name"), "slug": slugify(p.get("name") or ""), "pos": p.get("pos"), "team": p.get("team"),
        "pts": p.get("pts"), "availability": p.get("availability"),
        "opp": game.get("opponent"), "home": game.get("home"),
        # the wire screen
        "lane": p.get("lane"), "work": p.get("work"), "role_pts": p.get("role_pts"), "edge": p.get("edge"),
        "snap": p.get("snap_pct"), "tgt": p.get("target_share"), "car": p.get("carry_share"),
        "starts": _pick(p.get("starts_now"), "replaces", "slot", "their_pts", "margin"),
        "vacated": _pick(p.get("vacated"), "name", "injury"),
        "gain": p.get("gain"), "share_pct": p.get("share_pct"),
        "promoted": _pick(p.get("promoted"), "from", "to"),
        # adds and stash
        "upgrade": _pick(p.get("upgrade"), "replaces", "slot", "their_pts", "margin"),
        "stash_reason": p.get("stash_reason"),
    }


def live_waiver(feed_path, dwr_path, slugify):
    """LIVE_WAIVER: {date, week, clears, leagues: {espn|yahoo: {team, type, budget_left, wire, adds,
    stash, drops}}}, or None when ff-jarvis has not built a packet."""
    packet = load_packet(feed_path, dwr_path)
    if not packet:
        return None
    leagues = {}
    for label, lg in packet["leagues"].items():
        w = lg.get("waiver") or {}
        leagues[label] = {
            "team": lg.get("team"), "type": w.get("type"), "budget_left": w.get("budget_left"),
            "lineup_unknown": bool(lg.get("lineup_unknown")),
            **{k: [_row(p, slugify) for p in lg.get(k) or []] for k in ("wire", "adds", "stash", "drops")},
        }
    return {"date": packet.get("date"), "week": packet.get("week"), "clears": packet.get("clears"),
            "leagues": leagues}


def slugs(waiver):
    """Every player the tab draws, for build.py's headshot list."""
    return [r["slug"] for lg in ((waiver or {}).get("leagues") or {}).values()
            for k in ("wire", "adds", "stash", "drops") for r in lg[k] if r["slug"]]
