"""This week > Preview > Past games (2026-10-05, storyboard https://claude.ai/artifact/NTeV8W2N9mFnYgftfbuqPV,
option 1A): every earlier week's previews as they were written, so a reader can always go back to one.

ff-jarvis archives each take into history kind `previews` the first time its game is past kickoff
(model.season.preview_record.archive), once per game: the first row per key is the frozen take, the
one graded. `game_previews.json` holds one week, so the history is the only place an earlier week lives.

The current week stays in LIVE_PREVIEW (the page draws its finals from there); this file holds every
other week of the season, ~5 KB a game, so it is never injected: the build writes it beside index.html
and the page fetches it the first time a reader opens an earlier week (js/surface/preview/archive.js).

    {"season", "weeks": {"4": [game]}}
    game = {"key", "week", "home", "away", "kickoff", "line", "market_win", "take"}

`line` and `take` are cut by preview.py's own `_line` and `_take`, so an archived game draws with the same
dossier as a live one. A row stores its players by ff-jarvis key only, so their name, position and club come
from the projections (`names`); a player the projections no longer list keeps his key, title-cased. The
projection behind each call was not archived, so `proj` is null and the row draws without it.
"""
import json

from preview import _line, _take

NAME = "preview_archive.json"


def _names(rows, proj, slugify):
    """{key: {n, slug, pos, team, proj: None}} for every player an archived take calls."""
    known = {p["key"]: p for p in proj or []}
    out = {}
    for r in rows:
        for c in (r.get("take") or {}).get("players") or []:
            k = c["key"]
            p = known.get(k) or {"name": k.title(), "pos": "", "team": ""}
            out[k] = {"n": p["name"], "slug": slugify(p["name"]), "pos": p["pos"], "team": p["team"], "proj": None}
    return out


def archive(rows, current_week, proj, slugify):
    """The file's document from history `previews` rows (sources.load_preview_archive), every week but
    `current_week`, each week's games in kickoff order. None with no earlier week."""
    rows = [r for r in rows if r.get("take") and r.get("week") is not None and r["week"] != current_week]
    if not rows:
        return None
    names = _names(rows, proj, slugify)
    weeks = {}
    for r in sorted(rows, key=lambda r: (r["kickoff"], r["key"])):
        line = r.get("line") or {}
        weeks.setdefault(str(r["week"]), []).append({
            "key": r["key"], "week": r["week"], "home": r["home"], "away": r["away"], "kickoff": r["kickoff"],
            "line": _line(line, r["home"], r["away"]), "market_win": line.get("market_win") or None,
            "take": _take(r["take"], names, r["home"], r["away"])})
    return {"season": rows[0].get("season"), "weeks": weeks}


def build(repo, rows, current_week, proj, slugify):
    """build.py's one call: write `<repo>/preview_archive.json` and return the summary line."""
    doc = archive(rows, current_week, proj, slugify)
    path = repo / NAME
    if not doc:
        if path.exists():
            path.unlink()
        return "Preview archive: no earlier week yet"
    text = json.dumps(doc, ensure_ascii=False, separators=(",", ":"))
    path.write_text(text, encoding="utf-8")
    n = sum(len(g) for g in doc["weeks"].values())
    return f"Preview archive: weeks {', '.join(sorted(doc['weeks'], key=int))}, {n} games, " \
           f"{len(text.encode('utf-8')) / 1024:.0f} KB to {NAME}"


def write(repo, slugify):
    """build.py's one line: read this season's archived takes, the page's week and the projections (for the
    players' names), then `build`. Imported here so build.py stays inside its line budget (test_budgets.py)."""
    from sources import load_game_preview, load_player_proj, load_preview_archive
    gp = load_game_preview() or {}
    return build(repo, load_preview_archive(gp.get("season")), gp.get("week"),
                 (load_player_proj() or {}).get("players"), slugify)
