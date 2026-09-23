"""The Waivers sub-tab's data: ff-jarvis's `model.season.waiver_packet`, feed block `waiver` first,
then data/waiver_packet.json, whichever was built later. Rows are cut to the fields the cards draw;
every number is the packet's own, nothing is recomputed here.

One card per candidate, not per league: the packet lists a league's wire under that league, and
each record carries its own cross-league `leagues` map, so a player on both wires is one card with
two league rows. The first league to list him wins, in the packet's own order. A packet-level
`wire`/`stash` list, if the producer ever emits one, is read first.

Self-contained like news.py and signals.py: paths and slugify come in as arguments."""
import json

TIERS = ("must", "worth", "watch", "spec", "stash")
MAX_LEAGUES = 3


def load_packet(feed_path, dwr_path):
    # The file goes first: `date` is a day, not a time, so a same-day tie is common, and max() keeps
    # the first. The producer writes the file itself; the feed only holds the last refresh's copy.
    found = []
    path = dwr_path / "waiver_packet.json"
    try:
        if path.exists():
            d = json.loads(path.read_text(encoding="utf-8"))
            if d.get("leagues"):
                found.append(d)
    except (OSError, json.JSONDecodeError):
        pass
    try:
        block = (json.loads(feed_path.read_text(encoding="utf-8")).get("waiver") or {}).get("data")
        if block and block.get("leagues"):
            found.append(block)
    except (OSError, json.JSONDecodeError):
        pass
    return max(found, key=lambda b: b.get("date") or "") if found else None


def _pick(d, *keys):
    return {k: d.get(k) for k in keys} if isinstance(d, dict) else None


def _league(lg):
    """One league's view of a candidate: can I get him there, and what he does for that roster."""
    lg = lg or {}
    return {"status": lg.get("status"), "clears": lg.get("clears"), "need": bool(lg.get("need")),
            "verdict": _pick(lg.get("verdict"), "kind", "over", "slot", "margin"),
            "drop": _pick(lg.get("drop"), "name", "pos", "pts")}


def _row(p, slugify, tier=None):
    game = p.get("game") or {}
    return {
        "n": p.get("name"), "slug": slugify(p.get("name") or ""), "pos": p.get("pos"), "team": p.get("team"),
        "opp": game.get("opponent"), "home": game.get("home"),
        # A packet from before tiers existed reads as all Watch, so the tab still draws it.
        "tier": p.get("tier") or tier or "watch", "weeks": p.get("weeks"),
        "injury": p.get("injury"), "injury_note": p.get("injury_note"), "practice": p.get("practice"),
        "news_latest": _pick(p.get("news_latest"), "headline", "date"), "news_count": p.get("news_count") or 0,
        "leagues": {k: _league(v) for k, v in (p.get("leagues") or {}).items()},
        "summary": _pick(p.get("summary"), "text", "src"),
    }


def _candidates(packet):
    """(record, default tier) in the packet's order, packet-level lists first, then per league."""
    for p in packet.get("wire") or []:
        yield p, None
    for p in packet.get("stash") or []:
        yield p, "stash"
    for lg in (packet.get("leagues") or {}).values():
        for p in lg.get("wire") or []:
            yield p, None
        for p in lg.get("stash") or []:
            yield p, "stash"


def _meta(packet):
    """leagues_meta in the packet's order, at most three. Falls back to each league's own block
    when the producer has not written leagues_meta, so an old packet still draws a hero."""
    meta = packet.get("leagues_meta")
    if not meta:
        meta = {k: {"label": k.upper(), "faab_left": (lg.get("waiver") or {}).get("budget_left"),
                    "faab_budget": None, "clears": packet.get("clears"), "needs": []}
                for k, lg in (packet.get("leagues") or {}).items()}
    return {k: {"label": m.get("label") or k, "faab_left": m.get("faab_left"),
                "faab_budget": m.get("faab_budget"), "clears": m.get("clears"),
                "needs": list(m.get("needs") or [])}
            for k, m in list(meta.items())[:MAX_LEAGUES]}


def live_waiver(feed_path, dwr_path, slugify):
    """LIVE_WAIVER: {date, week, clears, leagues_meta, players}, or None when ff-jarvis has not
    built a packet. `players` is one row per candidate, grouped by tier in TIERS order."""
    packet = load_packet(feed_path, dwr_path)
    if not packet:
        return None
    seen, rows = set(), []
    for p, tier in _candidates(packet):
        key = p.get("key") or (p.get("name") or "").lower()
        if key in seen:
            continue
        seen.add(key)
        rows.append(_row(p, slugify, tier))
    order = {t: i for i, t in enumerate(TIERS)}
    rows.sort(key=lambda r: order.get(r["tier"], len(TIERS)))   # stable: packet order within a tier
    return {"date": packet.get("date"), "week": packet.get("week"), "clears": packet.get("clears"),
            "leagues_meta": _meta(packet), "players": rows}


def report(wv):
    """build.py's one-line summary of LIVE_WAIVER."""
    if not wv:
        return "Waiver: no waiver_packet.json/feed block, the tab says so"
    per = ", ".join(f"{sum(r['tier'] == t for r in wv['players'])} {t}" for t in TIERS)
    return f"Waiver: {per}, leagues {'/'.join(wv['leagues_meta'])}, clears {wv['clears']}"


def slugs(waiver):
    """Every player the tab draws, for build.py's headshot list."""
    return [r["slug"] for r in (waiver or {}).get("players") or [] if r["slug"]]
