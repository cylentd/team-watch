"""LIVE_SSB (2026-10-03): the Start / Sit picker's FantasyPros ranks, the matchup board and the
teammates-out lists, from design/startsit_board.py. No browser."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "design"))
import contract  # noqa: E402
import sources  # noqa: E402
import startsit_board as ssb  # noqa: E402
from test_build import injected  # noqa: E402


def slugify(name):
    return "".join(c for c in name.lower().replace(" ", "-") if c.isalnum() or c == "-")


def team(pts, rank=1):
    return {"current": {"games": 3, "pos": {p: {"pts_pg": pts + i, "rank": rank + i} for i, p in enumerate(ssb.POS)}}}


DEFENSE = {"form": {"teams": {"A": team(10), "B": team(20), "C": team(15), "D": team(30), "E": team(40), "BYE": team(5)},
                    "league": {"current": {"QB": 17.0, "RB": 19.0, "WR": 25.0, "TE": 10.0}}}}
SCHEDULE = {"week": 4, "alias": {"LA": "LAR"}, "games": [
    {"home": "A", "away": "B", "week": 4}, {"home": "C", "away": "D", "week": 4},
    {"home": "E", "away": "LAR", "week": 4}, {"home": "A", "away": "C", "week": 5}]}


def row(slug, pos, team_, pts=10.0):
    return {"slug": slug, "n": slug, "pos": pos, "team": team_, "pts": pts}


def hurt(slug, n, pos, s, avg):
    return {"n": n, "slug": slug, "pos": pos, "s": s, "avg": avg}


def test_fp_is_the_position_rank_keyed_by_slug():
    raw = {"week": 4, "players": [
        {"player_name": "Josh Allen", "player_position_id": "QB", "pos_rank": "QB1"},
        {"player_name": "Tyler Loop", "player_position_id": "K", "pos_rank": "K12"},
        {"player_name": "Josh Allen", "player_position_id": "QB", "pos_rank": "QB9"},
        {"player_name": "No Rank", "player_position_id": "WR", "pos_rank": None},
        {"player_name": None, "player_position_id": "WR", "pos_rank": "WR1"}]}
    assert ssb._fp(raw, slugify, 4) == {"josh-allen": {"ecr": 1, "pos": "QB"}, "tyler-loop": {"ecr": 12, "pos": "K"}}
    assert ssb._fp(None, slugify, 4) == {}


def test_fp_is_empty_when_the_file_is_another_weeks():
    raw = {"week": 3, "players": [{"player_name": "Josh Allen", "player_position_id": "QB", "pos_rank": "QB1"}]}
    assert ssb._fp(raw, slugify, 4) == {}, "last week's ranks must not read as this week's"
    assert ssb._fp({"players": raw["players"]}, slugify, 4) == {}, "a file with no week is not this week's"
    assert ssb.live_ssb({"week": 4, "rows": []}, None, None, None, raw, slugify)["fp"] == {}
    assert ssb.live_ssb({"week": 3, "rows": []}, None, None, None, raw, slugify)["fp"] == {"josh-allen": {"ecr": 1, "pos": "QB"}}


def test_board_pairs_each_offense_with_the_defense_it_faces():
    week, games = ssb._games(SCHEDULE)
    assert week == 4
    assert games == [("A", "B"), ("C", "D"), ("E", "LA")], "another week's game is out; LAR is back to LA"
    qb = ssb._board(DEFENSE, games)["QB"]
    assert qb["avg"] == 17.0 and qb["n"] == 3
    assert qb["best"][0] == {"team": "LA", "opp": "E", "pts": 40, "rank": 1}
    assert qb["worst"][0] == {"team": "B", "opp": "A", "pts": 10, "rank": 1}
    assert [r["pts"] for r in qb["best"]] == sorted((r["pts"] for r in qb["best"]), reverse=True)
    assert [r["pts"] for r in qb["worst"]] == sorted(r["pts"] for r in qb["worst"])
    assert all(r["opp"] != "BYE" and r["team"] != "BYE" for r in qb["best"] + qb["worst"])


def test_board_keeps_four_a_side_and_skips_what_it_cannot_price():
    games = [(h, a) for h, a in (("A", "B"), ("C", "D"), ("E", "A"), ("B", "C"), ("D", "E"))]
    assert all(len(b["best"]) == len(b["worst"]) == ssb.SHOW for b in ssb._board(DEFENSE, games).values())
    assert ssb._board(DEFENSE, [("A", "NOFORM")])["QB"]["best"] == [{"team": "NOFORM", "opp": "A", "pts": 10, "rank": 1}]
    assert ssb._board({"form": {"teams": DEFENSE["form"]["teams"]}}, [("A", "B")]) == {}, "no league average, no board"
    assert ssb._board(None, [("A", "B")]) == {}


def test_a_week_without_a_schedule_has_no_board():
    assert ssb._games(None) == (None, [])
    assert ssb._games({"week": None, "games": [{"home": "A", "away": "B", "week": None}]}) == (None, [])


def test_out_names_the_teammates_who_will_not_play():
    ranks = {"rows": [row("qb1", "QB", "CAR"), row("wr1", "WR", "CAR"), row("rb1", "RB", "DET"), row("te1", "TE", "SEA")]}
    preview = {"games": [{"inj": {"CAR": [
        hurt("wr1", "Wide Receiver", "WR", "out", 13.0),     # a teammate of the QB, never his own
        hurt("coker", "Jalen Coker", "WR", "out", 14.4),
        hurt("ir1", "Ira Back", "RB", "ir", 9.0),
        hurt("deep", "Deep Backup", "WR", "out", 1.2),       # under MIN_AVG: a deep backup
        hurt("nouse", "No Usage", "TE", "out", None),        # no usage recorded
        hurt("qbx", "Some Quarterback", "QB", "out", 20.0),  # a starting QB out leads: he moves his receivers most
        hurt("quest", "Quest Ionable", "WR", "q", 12.0)],    # still plays
        "DET": [hurt("d1", "Doubt Ful", "TE", "d", None)]}}]}
    got = ssb._out(ranks, preview)
    qb = {"n": "Some Quarterback", "pos": "QB", "s": "Out"}
    coker, back = {"n": "Jalen Coker", "pos": "WR", "s": "Out"}, {"n": "Ira Back", "pos": "RB", "s": "IR"}
    assert got["qb1"] == [qb, coker, {"n": "Wide Receiver", "pos": "WR", "s": "Out"}]
    assert got["wr1"] == [qb, coker, back], "his own row is dropped, never another's"
    assert "te1" not in got and "rb1" not in got, "no teammate out, or no usage to judge him by: no entry"


def test_out_falls_back_to_projected_points_for_a_doubtful_and_caps_the_list():
    ranks = {"rows": [row("qb1", "QB", "T"), row("doubt", "WR", "T", 11.5)]}
    inj = [hurt("doubt", "Doubt Ful", "WR", "d", None)] + [hurt(f"o{i}", f"Out {i}", "RB", "out", 6.0 + i) for i in range(5)]
    got = ssb._out(ranks, {"games": [{"inj": {"T": inj}}]})["qb1"]
    assert got[0] == {"n": "Doubt Ful", "pos": "WR", "s": "Doubtful"}
    assert len(got) == ssb.MAX_OUT
    assert [g["n"] for g in got[1:]] == ["Out 4", "Out 3"]


def test_every_source_missing_still_gives_all_keys():
    got = ssb.live_ssb(None, None, None, None, None, slugify)
    assert got == {"week": None, "fp": {}, "board": {}, "out": {}}
    assert contract.problems("LIVE_SSB", got) == []
    assert "0 FantasyPros ranks" in ssb.report(got)


def test_the_week_falls_back_to_the_ranks():
    assert ssb.live_ssb({"week": 3, "rows": []}, None, None, None, None, slugify)["week"] == 3


def test_a_shape_missing_a_field_fails_the_contract():
    good = {"week": 4, "fp": {"x": {"ecr": 1, "pos": "WR"}},
            "board": {"QB": {"avg": 1, "n": 1, "best": [{"team": "A", "opp": "B", "pts": 1, "rank": 1}], "worst": []}},
            "out": {"x": [{"n": "Jalen Coker", "pos": "WR", "s": "Out"}]}}
    assert contract.problems("LIVE_SSB", good) == []
    bad = json.loads(json.dumps(good))
    del bad["fp"]["x"]["pos"], bad["board"]["QB"]["best"][0]["rank"], bad["out"]["x"][0]["s"], bad["board"]["QB"]["n"]
    assert contract.problems("LIVE_SSB", bad) == [
        "LIVE_SSB.fp['x'].pos", "LIVE_SSB.board['QB'].n", "LIVE_SSB.board['QB'].best[0].rank", "LIVE_SSB.out['x'][0].s"]
    assert contract.problems("LIVE_SSB", {"week": 1, "fp": {}, "board": {}}) == ["LIVE_SSB.out"]


def test_expert_ranks_come_from_the_file(tmp_path, monkeypatch):
    monkeypatch.setattr(sources, "DWR", tmp_path)
    assert sources.load_expert_ranks() is None
    (tmp_path / "expert_ranks.json").write_text('{"players": []}', encoding="utf-8")
    assert sources.load_expert_ranks() == {"players": []}


def test_the_build_injects_the_block(built):
    d = injected(built.fragment)["LIVE_SSB"]
    assert set(d) == {"week", "fp", "board", "out"}
    assert d["week"] == 2
    assert d["fp"]["amonra-st-brown"] == {"ecr": 3, "pos": "WR"} and d["fp"]["jason-myers"]["pos"] == "K"
    assert "no-rank-listed" not in d["fp"]
    qb = d["board"]["QB"]
    assert qb["avg"] == 16.5 and qb["n"] == 1
    assert qb["best"] == [{"team": "WAS", "opp": "LA", "pts": 14.0, "rank": 9}, {"team": "DET", "opp": "SEA", "pts": 12.0, "rank": 6}]
    assert qb["worst"] == list(reversed(qb["best"]))
    assert set(d["board"]) == set(ssb.POS)
    assert d["out"] == {}, "no ranked player has a teammate out in the fixture"
    assert contract.problems("LIVE_SSB", d) == []
    assert any(line.startswith("Start/Sit board: week 2, 6 FantasyPros ranks, 4 positions") for line in built.report)
