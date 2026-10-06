"""Preview > Past games' file (design/preview_archive.py, 2026-10-05): earlier weeks' frozen takes from ff-jarvis
history `previews`, cut by preview.py's own `_line` / `_take` so an archived game draws with the live dossier."""
import json
import re

import contract  # noqa: F401  (imported so a broken build module fails here too)
from preview_archive import archive, build


def slug(n):
    return re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")


TAKE = {"headline": "Browns edge the Steelers", "lean": "Watson throws.\n\nRodgers struggles.", "vs_market": "", "risk": "Sacks.",
        "pick": {"winner": "CLE", "score": {"CLE": 20, "PIT": 18}}, "win": {"CLE": 54},
        "ats": {"side": "CLE", "conf": "solid", "edge": "x"}, "total": {"call": "under", "conf": "lean"},
        "players": [{"key": "deshaun watson", "call": "up", "why": "Runs."}, {"key": "nobody known", "call": "down", "why": "?"}]}


def row(week, key, kickoff):
    return {"key": key, "season": 2026, "week": week, "kickoff": kickoff, "home": "CLE", "away": "PIT",
            "line": {"spread_home": 2.5, "total": 38.5, "market_win": {"CLE": 42.8, "PIT": 57.2}}, "take": TAKE}


PROJ = [{"key": "deshaun watson", "name": "Deshaun Watson", "pos": "QB", "team": "CLE"}]


def test_every_week_but_the_current_one_in_kickoff_order():
    rows = [row(4, "b", "2026-10-02T00:15:00Z"), row(4, "a", "2026-10-01T00:15:00Z"), row(5, "c", "2026-10-09T00:15:00Z")]
    doc = archive(rows, 5, PROJ, slug)
    assert list(doc["weeks"]) == ["4"] and [g["key"] for g in doc["weeks"]["4"]] == ["a", "b"]
    g = doc["weeks"]["4"][0]
    assert g["line"]["fav"] == "PIT" and g["line"]["by"] == 2.5 and g["market_win"] == {"CLE": 42.8, "PIT": 57.2}
    assert g["take"]["head"] == "Browns edge the Steelers" and g["take"]["ats"]["side"] == "CLE"


def test_players_take_their_name_from_the_projections_else_their_key():
    ps = archive([row(4, "a", "2026-10-01T00:15:00Z")], 5, PROJ, slug)["weeks"]["4"][0]["take"]["players"]
    assert [(p["n"], p["slug"], p["pos"], p["proj"]) for p in ps] == [
        ("Deshaun Watson", "deshaun-watson", "QB", None), ("Nobody Known", "nobody-known", "", None)]


def test_no_earlier_week_means_no_file(tmp_path):
    assert archive([row(5, "c", "2026-10-09T00:15:00Z")], 5, PROJ, slug) is None
    (tmp_path / "preview_archive.json").write_text("{}", encoding="utf-8")
    assert build(tmp_path, [], 5, PROJ, slug) == "Preview archive: no earlier week yet"
    assert not (tmp_path / "preview_archive.json").exists()            # a stale file never outlives its data


def test_build_writes_compact_json(tmp_path):
    line = build(tmp_path, [row(4, "a", "2026-10-01T00:15:00Z")], 5, PROJ, slug)
    assert line.startswith("Preview archive: weeks 4, 1 games")
    doc = json.loads((tmp_path / "preview_archive.json").read_text(encoding="utf-8"))
    assert doc["season"] == 2026 and len(doc["weeks"]["4"]) == 1
