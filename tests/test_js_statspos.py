"""Stats' one position (data/statspos.js, 2026-10-06, David's "A Slide"), in Node.

Every Stats view used to keep its own position: WR on Ranks, then Leaders opened on RB. Now the reader
picks once and every Stats view that has that position shows it. A view without it shows its nearest
one and leaves the choice alone: FLEX and Work vs points' All are both RB, WR and TE together, so each
stands for the other; All also stands in for a position Work vs points lacks (QB, D/ST, K); a view of
QB to TE only keeps the last of QB to TE the reader picked, else RB. The strip under the thumb picks the
segment under the finger as it slides (statsSegAt)."""
import pytest

CORE = ["QB", "RB", "WR", "TE"]


@pytest.fixture(scope="module")
def sp(node_js):
    return node_js("data/statspos.js")


def state(shared, core="RB"):
    return {"shared": shared, "core": core}


# ---- each view's positions, in strip order ----

def test_ranks_this_week_lists_flex_then_the_leagues_d_st_and_k(sp):
    assert sp("statsPosList", "ranks", {}) == CORE + ["FLEX"]
    assert sp("statsPosList", "ranks", {"extra": ["DST"]}) == CORE + ["FLEX", "DST"]
    assert sp("statsPosList", "ranks", {"extra": ["DST", "K"]}) == CORE + ["FLEX", "DST", "K"]


def test_ranks_rest_of_season_lists_qb_to_te_only(sp):
    assert sp("statsPosList", "ranks", {"ros": True, "extra": ["DST", "K"]}) == CORE


def test_work_vs_points_lists_all_then_rb_wr_te(sp):
    assert sp("statsPosList", "movers", {}) == ["ALL", "RB", "WR", "TE"]


@pytest.mark.parametrize("leaf", ["board", "usage", "schedule"])
def test_leaders_usage_and_schedule_list_qb_to_te(sp, leaf):
    assert sp("statsPosList", leaf, {}) == CORE


def test_a_view_lists_only_the_positions_it_has_data_for(sp):
    assert sp("statsPosList", "board", {"have": ["RB", "WR"]}) == ["RB", "WR"], "Leaders without QB or TE lanes"
    assert sp("statsPosList", "usage", {"have": []}) == []


@pytest.mark.parametrize("leaf", ["digest", "roster"])
def test_a_view_with_no_position_lists_none(sp, leaf):
    assert sp("statsPosList", leaf, {}) == []


# ---- the shared choice -> what a view shows ----

def test_a_view_that_has_the_shared_position_shows_it(sp):
    assert sp("statsPosShown", CORE + ["FLEX"], state("WR")) == "WR"
    assert sp("statsPosShown", ["ALL", "RB", "WR", "TE"], state("TE")) == "TE"
    assert sp("statsPosShown", CORE + ["FLEX", "DST", "K"], state("K")) == "K"


def test_flex_and_all_stand_for_each_other(sp):
    assert sp("statsPosShown", ["ALL", "RB", "WR", "TE"], state("FLEX")) == "ALL"
    assert sp("statsPosShown", CORE + ["FLEX"], state("ALL")) == "FLEX"


@pytest.mark.parametrize("shared", ["QB", "DST", "K"])
def test_work_vs_points_shows_all_for_a_position_it_lacks(sp, shared):
    assert sp("statsPosShown", ["ALL", "RB", "WR", "TE"], state(shared, core="QB")) == "ALL"


@pytest.mark.parametrize("shared", ["FLEX", "DST", "K", "ALL"])
def test_a_qb_to_te_view_keeps_the_last_of_qb_to_te_the_reader_picked(sp, shared):
    assert sp("statsPosShown", CORE, state(shared, core="TE")) == "TE"


def test_with_no_qb_to_te_pick_yet_a_qb_to_te_view_shows_rb(sp):
    assert sp("statsPosShown", CORE, state("FLEX", core=None)) == "RB"


def test_a_league_without_d_st_or_k_shows_the_last_qb_to_te_pick(sp):
    assert sp("statsPosShown", CORE + ["FLEX", "DST"], state("K", core="WR")) == "WR"


def test_a_remembered_position_the_view_lacks_falls_to_rb_then_the_first(sp):
    assert sp("statsPosShown", ["RB", "WR"], state("FLEX", core="QB")) == "RB"
    assert sp("statsPosShown", ["WR", "TE"], state("FLEX", core="QB")) == "WR"


def test_a_view_with_no_positions_shows_none(sp):
    assert sp("statsPosShown", [], state("WR")) is None


# ---- picking ----

def test_a_pick_becomes_the_shared_position(sp):
    assert sp("statsPosPick", state("RB"), "WR") == {"shared": "WR", "core": "WR"}


@pytest.mark.parametrize("pos", ["FLEX", "ALL", "DST", "K"])
def test_a_pick_outside_qb_to_te_keeps_the_last_qb_to_te(sp, pos):
    assert sp("statsPosPick", state("WR", core="WR"), pos) == {"shared": pos, "core": "WR"}


def test_before_any_pick_work_vs_points_opens_on_all(sp):
    """Each view's own opening position stands until the reader picks one: All on Work vs points."""
    assert sp("statsPosShown(statsPosList('movers'), STATS_POS)") == "ALL"


@pytest.mark.parametrize("leaf", ["ranks", "board", "usage", "schedule"])
def test_before_any_pick_the_rest_open_on_rb(sp, leaf):
    """Each view's own opening position stands until the reader picks one: RB elsewhere."""
    assert sp(f"statsPosShown(statsPosList('{leaf}'), STATS_POS)") == "RB"


# ---- the segment under the finger ----

def test_the_segment_under_the_finger_is_the_one_whose_slice_holds_x(sp):
    # a 320px strip from x=20, seven segments of ~45.7px
    assert sp("statsSegAt", 20, 20, 320, 7) == 0
    assert sp("statsSegAt", 65, 20, 320, 7) == 0
    assert sp("statsSegAt", 66, 20, 320, 7) == 1
    assert sp("statsSegAt", 339, 20, 320, 7) == 6


def test_a_finger_past_either_end_holds_the_end_segment(sp):
    assert sp("statsSegAt", 0, 20, 320, 4) == 0
    assert sp("statsSegAt", 400, 20, 320, 4) == 3
