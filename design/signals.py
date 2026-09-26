"""My Teams row signals: the usage trend from ff-jarvis's `model.season.watch` and a per-player
news count from its scanner, keyed by slug for every player on either of my rosters. The price
half of the row (delta and position rank) is `market.stock`, which the JS reads through
stockFor(); nothing here recomputes a model number.

Self-contained like news.py: paths and slugify come in as arguments, so there is no import
cycle back into build.py."""
import datetime as dt
import json

NEWS_WINDOW_H = 72          # a story older than this, measured from the newest one, is not news
HOT = {"Breaking", "Injury"}
# FantasyPros and the league sites spell three teams differently; compared, never displayed.
TEAM_ALIAS = {"JAC": "JAX", "WSH": "WAS", "LA": "LAR"}


def _team(code):
    return TEAM_ALIAS.get(code, code)


def load_usage(feed_path, dwr_path):
    """watch.json: the feed's `usage` block or the file, whichever carries rosters and was
    generated later. A hand re-run of watch between refreshes leaves the file newer than the
    feed's copy, the same way load_model_raw() treats props_model."""
    found = []
    try:
        block = (json.loads(feed_path.read_text(encoding="utf-8")).get("usage") or {}).get("data")
        found.append(block)
    except (OSError, json.JSONDecodeError):
        pass
    path = dwr_path / "watch.json"
    try:
        if path.exists():
            found.append(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        pass
    found = [b for b in found if b]
    rostered = [b for b in found if b.get("leagues")]
    pick = rostered or found
    return max(pick, key=lambda b: b.get("generated") or "") if pick else None


def usage_by_slug(usage, slugify):
    """slug -> the watch row Team Watch draws. My leagues' rows win over the league-wide pool,
    which only fills a player the roster step did not trend."""
    out = {}
    rows = [r for L in (usage or {}).get("leagues") or [] for r in L.get("players") or []]
    rows += (usage or {}).get("pool") or []
    for r in rows:
        if not isinstance(r, dict):
            continue
        out.setdefault(slugify(r.get("name") or ""), {
            "series": r.get("series") or [], "verdict": r.get("verdict"), "why": r.get("why"),
        })
    return out


def _created(it):
    try:
        return dt.datetime.strptime(it["created"], "%Y-%m-%d %H:%M:%S")
    except (KeyError, TypeError, ValueError):
        return None


def news_by_slug(raw_items, players, slugify):
    """slug -> {n, hot} over the last NEWS_WINDOW_H hours of the scanner's window. A story is
    about a player when its headline starts with his name and, where both say, the team agrees:
    FantasyPros leads with the name ("Chase Brown (hamstring) ..."), and the team check keeps a
    shared name from borrowing another man's story."""
    times = [t for t in map(_created, raw_items) if t]
    if not times:
        return {}
    cutoff = max(times) - dt.timedelta(hours=NEWS_WINDOW_H)
    out = {}
    for it in raw_items:
        t = _created(it)
        if t is None or t < cutoff:
            continue
        head = slugify(it.get("title") or "") + "-"
        for p in players:
            if not p["slug"] or not head.startswith(p["slug"] + "-"):
                continue
            if it.get("team_id") and p.get("team") and _team(it["team_id"]) != _team(p["team"]):
                continue
            row = out.setdefault(p["slug"], {"n": 0, "hot": False})
            row["n"] += 1
            row["hot"] = row["hot"] or bool(HOT & set(it.get("categories") or []))
    return out


def raw_news(feed_path, dwr_path):
    """The scanner's items with their raw `created`, which load_news() formats away."""
    try:
        block = ((json.loads(feed_path.read_text(encoding="utf-8")).get("market") or {})
                 .get("news") or {}).get("data")
        if block and block.get("items"):
            return block["items"]
    except (OSError, json.JSONDecodeError):
        pass
    path = dwr_path / "breaking_news.json"
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("items") or [] if path.exists() else []
    except (OSError, json.JSONDecodeError):
        return []


def report(sig):
    """build.py's one-line summary of LIVE_SIGNALS."""
    if not sig:
        return "Signals: no roster, so no trend or news counts"
    rows = sig["players"].values()
    return f"Signals: {sum(1 for s in rows if s['series'])} trended, {sum(1 for s in rows if s['news'])} with news"


def live_signals(feed_path, dwr_path, rosters, slugify):
    """LIVE_SIGNALS: {through_week, ready, players: {slug: {series, verdict, why, news, hot}}}
    for every player on `rosters` (LIVE_ESPN, LIVE_YAHOO and, since 2026-09-26, each LIVE_MATES
    team; any may be None). A signal is a fact about the player, not about whose team he is on."""
    # One entry per slug: a player on both rosters must not count each story twice. A player with
    # no headshot has no slug, and the page looks signals up by slug, so he has none to find.
    players = list({p["slug"]: p for r in rosters if r for p in r["roster"] if p["slug"]}.values())
    if not players:
        return None
    usage = load_usage(feed_path, dwr_path)
    trend = usage_by_slug(usage, slugify)
    news = news_by_slug(raw_news(feed_path, dwr_path), players, slugify)
    out = {}
    for p in players:
        u = trend.get(p["slug"], {})
        nw = news.get(p["slug"], {})
        out[p["slug"]] = {"series": u.get("series") or [], "verdict": u.get("verdict"),
                          "why": u.get("why"), "news": nw.get("n", 0), "hot": nw.get("hot", False)}
    return {"through_week": (usage or {}).get("through_week"),
            "ready": bool((usage or {}).get("ready")), "players": out}
