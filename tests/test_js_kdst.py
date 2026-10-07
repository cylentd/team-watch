"""A kicker's and a defense's points bars (2026-10-07): `data/kdst.js` says which score a league reads for a
club's K or D/ST, the weeks to draw (a bye is absent from the file, so it is an empty slot) and the weeks a
different kicker kicked (drawn faded). ff-jarvis's gamelog_kdst.json holds every number; the page picks."""
import pytest

DST = {"leagues": {"espn": {"dst": "dst_espn", "k": None}, "yahoo": {"dst": "dst_yahoo", "k": "k_yahoo"},
                   "ayo": {"dst": "dst_yahoo", "k": "k_ayo"}}}
ROW = lambda wk, k=("A.Kicker",), **x: {"week": wk, "opp": "XXX", "home": True, "dst_espn": 7.5, "dst_yahoo": 6.0,
                                        "k_yahoo": 9.5, "k_ayo": 9.0, "kickers": list(k), **x}
KD = {"teams": {"BAL": [ROW(1), ROW(2, ("A.Kicker", "B.Backup"), k_yahoo=0.0), ROW(4, ("B.Backup",), dst_espn=-1.0)]}}


@pytest.fixture(scope="module")
def kd(node_js):
    return node_js("data/dst.js", "data/kdst.js")


@pytest.mark.parametrize("lg,pos,want", [("espn", "DST", "dst_espn"), ("yahoo", "DST", "dst_yahoo"),
                                         ("ayo", "DST", "dst_yahoo"), ("yahoo", "K", "k_yahoo"),
                                         ("ayo", "K", "k_ayo"), ("espn", "K", None), ("nope", "DST", None)])
def test_a_league_reads_its_own_score_and_espn_has_no_kicker(kd, lg, pos, want):
    assert kd("kdstKey", DST, lg, pos) == want


def test_a_defense_gets_one_row_per_game_in_the_leagues_scoring(kd):
    assert kd("kdstRows", KD, "BAL", "dst_espn") == [{"wk": 1, "pts": 7.5}, {"wk": 2, "pts": 7.5}, {"wk": 4, "pts": -1.0}]


def test_the_page_spelling_of_a_club_finds_the_files_row(kd):
    kd2 = {"teams": {"LA": [ROW(1)], "JAX": [ROW(1)], "WAS": [ROW(1)]}}
    assert [len(kd("kdstRows", kd2, c, "dst_yahoo")) for c in ("LAR", "JAC", "WSH")] == [1, 1, 1]


@pytest.mark.parametrize("block,club,key", [(None, "BAL", "dst_espn"), (KD, "ZZZ", "dst_espn"), (KD, "BAL", None)])
def test_no_file_no_club_or_no_score_means_no_bars(kd, block, club, key):
    assert kd("kdstRows", block, club, key) is None


def test_a_kicker_is_faded_in_the_weeks_nobody_with_his_name_kicked(kd):
    assert kd("kdstFaded", KD, "BAL", "Alex Kicker") == [4]


def test_a_week_with_two_kickers_counts_for_the_rostered_one(kd):
    assert 2 not in kd("kdstFaded", KD, "BAL", "Alex Kicker")


def test_a_name_that_matches_nobody_fades_nothing(kd):
    assert kd("kdstFaded", KD, "BAL", "Zed Unknown") == []
