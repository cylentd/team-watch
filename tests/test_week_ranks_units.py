"""The data side of Stats > Ranks, one function at a time (design/ranks.py and design/week_ranks.py): the report
line, the list file's shape check and its limits, and the two ways a Ranks block is cut. Plain dicts in, plain
dicts out; the whole-page checks are in test_week_ranks.py."""
import pytest

import week_ranks
from ranks import FALLBACK_WORDS, live_ranks, report as ranks_report

TIERS = " · QB 2 in 3 tiers · RB 0 in 0 tiers · WR 0 in 0 tiers · TE 0 in 0 tiers · FLEX 1 in 1 tiers"
BLOCK = {"rows": [{"pos": "QB", "tier": 2}, {"pos": "QB", "tier": 3}], "flex": [{"tier": 1}]}


def slug(name):
    return name.lower().replace(" ", "-")


def row(name, pos, rank, tier, pts, val=None, team="AAA", opp="BBB"):
    return {"key": name.lower(), "name": name, "pos": pos, "team": team, "opp": opp, "kickoff": "2026-09-13T17:00:00Z",
            "rank": rank, "tier": tier, "val": float(-rank) if val is None else val, "pts": pts, "src": "ours"}


def doc(lists=None, off=(), scoring="half"):
    empty = {name: [] for name in week_ranks.LISTS}
    return {"v": 1, "generated": "2026-09-10T07:35:00Z", "ros": None,
            "weekly": {"season": 2026, "week": 4, "scoring": scoring, "off": list(off), "lists": {**empty, **(lists or {})}}}


def test_the_report_names_the_source_then_each_lists_size_and_tiers():
    assert ranks_report({**BLOCK, "from": "week_ranks"}) == "Ranks: week_ranks" + TIERS
    assert ranks_report({**BLOCK, "from": "projections"}) == FALLBACK_WORDS + TIERS
    assert ranks_report(None) == "Ranks: none, so no Ranks view"


def test_no_projections_and_no_lists_is_no_block_but_lists_alone_make_one():
    assert live_ranks({}, slug) is None
    assert live_ranks(None, slug, None, None, None) is None
    alone = live_ranks(None, slug, None, None, doc({"QB": [row("Ann Arm", "QB", 1, 1, 1.236)]}, off=["SF", "CIN"], scoring="ppr"))
    assert (alone["from"], alone["week"], alone["off"], alone["scoring"]) == ("week_ranks", 4, ["CIN", "SF"], "ppr")
    assert [(r["slug"], r["pts"], r["home"], r["inj"], r["mu"]) for r in alone["rows"]] == [("ann-arm", 1.24, None, None, None)]


def test_a_list_row_is_enriched_from_the_projections_row_by_slug():
    raw = {"players": [{"name": "Ann Arm", "pos": "QB", "team": "BBB", "game": "AAA @ BBB", "pts": 9.0, "injury": "Doubtful"}]}
    got = live_ranks(raw, slug, None, None, doc({"QB": [row("Ann Arm", "QB", 1, 1, 8.0)]}))["rows"][0]
    assert (got["home"], got["inj"], got["pts"], got["rank"], got["tier"]) == (True, "D", 9.0, 1, 1)   # his projection (9.0), not the list's frozen 8.0


def test_of_two_projection_rows_for_one_player_the_higher_points_stay_and_a_tie_keeps_the_first():
    first = {"name": "Ann Arm", "pos": "QB", "team": "BBB", "game": "AAA @ BBB", "pts": 9.0, "injury": "Questionable"}
    lists = doc({"QB": [row("Ann Arm", "QB", 1, 1, 8.0)]})
    tie = live_ranks({"players": [first, {**first, "injury": None}]}, slug, None, None, lists)["rows"][0]
    assert tie["inj"] == "Q", "equal points: the first row stays"
    higher = live_ranks({"players": [first, {**first, "injury": None, "pts": 9.5}]}, slug, None, None, lists)["rows"][0]
    assert higher["inj"] is None, "more points: the later row wins"


NAMELESS = {"pos": "QB", "team": "BBB", "game": "AAA @ BBB", "pts": 9.0, "injury": "Questionable"}
POINTLESS = {"name": "Ann Arm", "pos": "QB", "team": "BBB", "game": "AAA @ BBB", "injury": "Questionable"}


@pytest.mark.parametrize("extra", [[NAMELESS], [POINTLESS], [{"name": "Ann Arm", "pts": 9.0}, POINTLESS]],
                         ids=["no name", "no points", "a pointless row after a bare one"])
def test_a_projection_row_with_no_points_or_no_name_enriches_no_one(extra):
    lists = doc({"QB": [row("Ann Arm", "QB", 1, 1, 8.0)]})
    assert live_ranks({"players": extra}, slug, None, None, lists)["rows"][0]["inj"] is None


def test_flex_rows_carry_their_position_rank_and_the_position_lists_hold_no_flex():
    lists = doc({"RB": [row("Ann Arm", "RB", 1, 1, 9.0), row("Bo Back", "RB", 2, 2, 8.0)],
                 "WR": [row("Cy Catch", "WR", 1, 1, 9.5)],
                 "FLEX": [row("Cy Catch", "WR", 1, 1, 9.5), row("Bo Back", "RB", 2, 1, 8.0), row("Ann Arm", "RB", 3, 2, 9.0)]})
    got = live_ranks({"players": [{"name": "x", "pts": 1.0}]}, slug, None, None, lists)
    assert [(r["slug"], r["rank"]) for r in got["rows"]] == [("ann-arm", 1), ("bo-back", 2), ("cy-catch", 1)]
    assert [(r["slug"], r["rank"], r["tier"]) for r in got["flex"]] == [("cy-catch", 1, 1), ("bo-back", 2, 1), ("ann-arm", 1, 2)]   # the list's own order and tiers, as shipped (ledger #98)


def test_the_old_cut_rounds_points_to_hundredths():
    back = {"name": "Bo Back", "pos": "RB", "team": "BBB", "game": "AAA @ BBB", "pts": 1.236, "rank_pts": 2.5,
            "unlined_backup": True, "pts_before_unlined": 4.5}
    got = live_ranks({"players": [back]}, slug)["rows"][0]
    assert got["pts"] == 1.24


def test_the_old_cut_lists_positions_in_rows_and_leaves_flex_to_its_own_key():
    players = [{"name": n, "pos": p, "team": "BBB", "game": "AAA @ BBB", "pts": v} for n, p, v in
               (("Ann Arm", "QB", 9.0), ("Bo Back", "RB", 8.0), ("Cy Catch", "WR", 7.0), ("Di Tight", "TE", 6.0))]
    got = live_ranks({"players": players}, slug)
    assert (got["from"], [r["pos"] for r in got["rows"]], len(got["flex"])) == ("projections", ["QB", "RB", "WR", "TE"], 3)


def test_a_list_is_capped_at_eight_problems():
    rows = [row(f"Player {i}", "RB", i + 1, 1, None) for i in range(12)]
    assert len(week_ranks.problems(doc({"RB": rows}))) == 8


def test_the_first_tier_is_one_and_equal_order_keys_are_allowed():
    assert week_ranks.problems(doc({"RB": [row("A A", "RB", 1, 2, 1.0)]}))[0].startswith("weekly.lists.RB[0].tier")
    tied = doc({"RB": [row("A A", "RB", 1, 1, 1.0, val=5.0), row("B B", "RB", 2, 1, 1.0, val=5.0)]})
    assert week_ranks.problems(tied) == []


def test_a_weekly_block_missing_a_field_says_which_are_needed():
    bad = doc()
    del bad["weekly"]["off"]
    assert week_ranks.problems(bad) == ["weekly: needs season, week, scoring, off, lists"]


@pytest.mark.parametrize("pos", week_ranks.POSITIONS)
def test_the_cards_rank_is_the_place_in_the_list_and_the_lists_length(pos):
    lists = doc({pos: [row("Ann Arm", pos, 1, 1, 2.0), row("Bo Back", pos, 2, 1, 1.0)]})
    assert week_ranks.position_ranks(lists, slug) == {"ann-arm": (1, 2), "bo-back": (2, 2)}


# ---- the old cut and the file loader, one function at a time ----

def player(name, pos, pts, **more):
    return {"name": name, "pos": pos, "team": "BBB", "game": "AAA @ BBB", "pts": pts, **more}


def old_rows(players):
    return {r["slug"]: r for r in live_ranks({"players": players}, slug)["rows"]}


def test_natural_breaks_split_at_the_widest_drops_and_never_ask_for_more_tiers_than_players():
    from ranks import natural_breaks
    assert natural_breaks([20.0, 19.8, 15.1, 15.0, 14.9, 9.0, 8.8, 8.7], 3) == [1, 1, 2, 2, 2, 3, 3, 3]
    assert natural_breaks([10.0, 9.0], 8) == [1, 2]
    assert natural_breaks([], 4) == []


@pytest.mark.parametrize("pos, depth", [("QB", 32), ("RB", 60), ("WR", 72), ("TE", 32)])
def test_the_old_cut_lists_each_position_to_its_depth(pos, depth):
    players = [player(f"Player {i:03d}", pos, 100.0 - i) for i in range(depth + 1)]
    assert len(live_ranks({"players": players}, slug)["rows"]) == depth


def test_home_is_read_from_the_game_string():
    got = old_rows([player("Home Guy", "QB", 9.0), player("Away Guy", "QB", 8.0, team="AAA"),
                    player("Lost Guy", "QB", 7.0, team="CCC"), player("Bye Guy", "QB", 6.0, game=""),
                    player("No Team", "QB", 5.0, team=None)])
    assert {s: r["home"] for s, r in got.items()} == {"home-guy": True, "away-guy": False, "lost-guy": None, "bye-guy": None, "no-team": None}


def test_what_the_points_are_made_of_is_the_producers_own_means_rounded_to_a_tenth():
    got = old_rows([player("Ann Arm", "QB", 9.0, mu={"PASS": 245.26, "RUSH": 15, "TD": 0.3}),
                    player("Bo Back", "RB", 8.0, mu={"RUSH": 70.04, "REC": 28, "RECS": 3.4, "TD": 0.4}),
                    player("Cy Catch", "WR", 7.0, mu={}), player("Di Tight", "TE", 6.0), player("Ed Arm", "QB", 5.0, mu={"TD": 0.3})])
    assert got["ann-arm"]["mu"] == {"PASS": 245.3, "RUSH": 15}
    assert got["bo-back"]["mu"] == {"RUSH": 70.0, "REC": 28, "RECS": 3.4, "TD": 0.4}
    assert [got[s]["mu"] for s in ("cy-catch", "di-tight", "ed-arm")] == [None, None, None]


def test_the_matchup_is_kept_to_a_tenth_and_a_receiver_has_none():
    got = old_rows([player("Bo Back", "RB", 8.0, matchup={"pts": 1.74, "priced": 0.66}),
                    player("Cy Catch", "WR", 7.0, matchup={"pts": 1.0, "priced": 0.4}), player("Di Tight", "TE", 6.0)])
    assert [(got[s]["mx"], got[s]["mxp"]) for s in ("bo-back", "cy-catch", "di-tight")] == [(1.7, 0.7), (None, None), (None, None)]


def test_the_old_cuts_rank_counts_from_one_down_the_points():
    got = old_rows([player("Ann Arm", "QB", 9.0), player("Bo Arm", "QB", 8.0), player("Cy Arm", "QB", 7.0)])
    assert [got[s]["rank"] for s in ("ann-arm", "bo-arm", "cy-arm")] == [1, 2, 3]


def test_the_loader_reads_the_file_returns_it_whole_and_names_every_problem(tmp_path, monkeypatch):
    import json
    import sources
    monkeypatch.setattr(sources, "FEED", tmp_path / "no-feed.json")
    monkeypatch.setattr(sources, "DWR", tmp_path)
    assert week_ranks.load_week_ranks() is None, "no file, no feed: none"
    good = doc({"QB": [row("Ann Arm", "QB", 1, 1, 2.0)]})
    (tmp_path / "week_ranks.json").write_text(json.dumps(good), encoding="utf-8")
    assert week_ranks.load_week_ranks() == good
    bad = doc({"RB": [row("A A", "RB", 2, 1, 1.0), row("B B", "RB", 1, 1, 1.0)]})
    (tmp_path / "week_ranks.json").write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(SystemExit) as stop:
        week_ranks.load_week_ranks()
    assert str(stop.value) == ("week_ranks.json: weekly.lists.RB[0].rank: 2, expected 1; weekly.lists.RB[1].rank: 1, expected 2; "
                               "weekly.lists.RB[1].val: -1.0 is not a number at or below the row above")


def test_the_check_says_what_is_wrong_in_its_own_words():
    assert week_ranks.problems({}) == ["week_ranks: needs v, generated, weekly"]
    assert week_ranks.problems({**doc(), "v": 3}) == ["v: 3, expected 1 or 2"]
    assert week_ranks.problems(doc(scoring="ppr")) == ["weekly.scoring: 'ppr', expected 'half'"]
    assert week_ranks.problems(doc({"QB": [{"x": 1}, row("A A", "QB", 2, 1, 1.0)]}))[0].startswith("weekly.lists.QB[0]: keys ['x'], expected")
    notnum = doc({"QB": [row("A A", "QB", 1, 1, 1.0, val="x")]})
    assert week_ranks.problems(notnum) == ["weekly.lists.QB[0].val: 'x' is not a number at or below the row above"]


# ---- the cards' rank from the Ranks block (ledger #81) ----

@pytest.mark.parametrize("block", [None, {}, {"from": "projections", "rows": [{"slug": "a", "pos": "QB", "rank": 1}]}],
                         ids=["none", "empty", "the old cut"])
def test_ranks_places_is_none_without_a_week_ranks_cut(block):
    from ranks import ranks_places
    assert ranks_places(block) is None


def test_ranks_places_maps_each_slug_to_its_rank_and_its_positions_length():
    from ranks import ranks_places
    rows = [{"slug": "q1", "pos": "QB", "rank": 1}, {"slug": "r1", "pos": "RB", "rank": 1}, {"slug": "r2", "pos": "RB", "rank": 2}]
    assert ranks_places({"from": "week_ranks", "rows": rows}) == {"q1": (1, 1), "r1": (1, 2), "r2": (2, 2)}
