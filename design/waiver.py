"""The Waivers sub-tab's data: ff-jarvis's `model.season.waiver_packet`, feed block `waiver` first,
then data/waiver_packet.json, whichever was built later. Rows are cut to the fields the cards draw;
every number is the packet's own, nothing is recomputed here.

One card per candidate, not per league: the packet lists a league's wire under that league, and
each record carries its own cross-league `leagues` map, so a player on both wires is one card with
two league rows. The first league to list him wins, in the packet's own order. A packet-level
`wire`/`stash` list, if the producer ever emits one, is read first.

Self-contained like news.py and signals.py: paths and slugify come in as arguments."""
import json

from injury import level

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
    # `tier` is this league's own (ff-jarvis, from 2026-09-23); null on an older packet, and the
    # card then falls back to the row's top-level tier (data/waiver.js waiverTier).
    tier = lg.get("tier") if lg.get("tier") in TIERS else None
    return {"status": lg.get("status"), "clears": lg.get("clears"), "need": bool(lg.get("need")), "tier": tier, "lane": None,
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
    """(record, default tier, league whose list carried it) in the packet's order, packet-level
    lists first (league None), then per league."""
    for p in packet.get("wire") or []:
        yield p, None, None
    for p in packet.get("stash") or []:
        yield p, "stash", None
    for key, lg in (packet.get("leagues") or {}).items():
        for p in lg.get("wire") or []:
            yield p, None, key
        for p in lg.get("stash") or []:
            yield p, "stash", key


def _set_lane(row, p, league):
    """`lane` is why that league's screen listed him (judged against that roster), so it belongs
    to the league view, not the card: Jerome Ford is a STARTER in ESPN and nothing in Yahoo. A
    packet-level record's lane applies to every league it has a view for."""
    if not p.get("lane"):
        return
    for k, view in row["leagues"].items():
        if league in (None, k) and view["lane"] is None:
            view["lane"] = p["lane"]


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


NOW_LABEL = {"Out": "O", "IR": "IR", "Doubtful": "D"}   # status_now -> the packet's own `injury` code
ACT_TIERS = ("must", "worth")                             # tiers that say "go get him"


def _fresh_label(code):
    """Sleeper's injury code as Out / IR / Doubtful, or None (healthy, Questionable, unknown)."""
    lv = level(code)
    return "IR" if code == "IR" else "Out" if lv == "OUT" else "Doubtful" if lv == "D" else None


def _overlay(rows, status, slugify):
    """Fresh status on each card. The packet is built once in the morning, Sleeper runs again through the
    day, so a card tiered must/worth can be out by the time it is read (2026-10-04 audit). `status_now` is
    Sleeper's Out / IR / Doubtful for him, else None. A must/worth card whose packet `injury` does not
    already say it gets `status_flag` too (that code, O / IR / D; the card words it with copy key
    waiver.card.nowFlag), and sorts after its tier peers. The tier is ff-jarvis's and is
    never recomputed here; with no status every card carries `status_now` None and the order is untouched."""
    live = {slugify(v.get("name") or ""): v.get("injury") for v in (status or {}).values()}
    for r in rows:
        now = _fresh_label(live.get(r["slug"]))
        r["status_now"] = now
        stale = bool(now) and r["tier"] in ACT_TIERS and r.get("injury") != NOW_LABEL[now]
        r["status_flag"] = NOW_LABEL[now] if stale else None
    return rows


def live_waiver(feed_path, dwr_path, slugify, status=None):
    """LIVE_WAIVER: {date, week, clears, leagues_meta, players}, or None when ff-jarvis has not
    built a packet. `players` is one row per candidate, grouped by tier in TIERS order. `status` is
    sources.load_status() (Sleeper's latest) and overlays `status_now` / `status_flag` (see `_overlay`)."""
    packet = load_packet(feed_path, dwr_path)
    if not packet:
        return None
    seen, rows = {}, []
    for p, tier, league in _candidates(packet):
        key = p.get("key") or (p.get("name") or "").lower()
        if key not in seen:
            seen[key] = _row(p, slugify, tier)
            rows.append(seen[key])
        _set_lane(seen[key], p, league)
    order = {t: i for i, t in enumerate(TIERS)}
    _overlay(rows, status, slugify)
    # stable: packet order within a tier, a card flagged by fresh status after its peers
    rows.sort(key=lambda r: (order.get(r["tier"], len(TIERS)), bool(r["status_flag"])))
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
