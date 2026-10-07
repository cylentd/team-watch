"""A waiver card draws only the proof stats that have a value (2026-10-07: an availability-unknown Watch
card drew three blank "—" stats). `wvProofShown` (data/proofshow.js) keeps the cells with a value, so a
card with none draws no stats row at all."""
import pytest


@pytest.fixture(scope="module")
def ps(node_js):
    return node_js("data/firstsentence.js", "data/proofshow.js")


def test_a_stat_with_no_value_is_dropped(ps):
    cells = [{"id": "snap", "now": 71}, {"id": "tgt_pct", "now": None}, {"id": "adot", "now": 8.4}]
    assert [c["id"] for c in ps("wvProofShown", cells)] == ["snap", "adot"]


def test_a_zero_is_a_value(ps):
    assert ps("wvProofShown", [{"id": "rz", "now": 0}]) == [{"id": "rz", "now": 0}]


TEXT = "Wilson took 21 carries in week 2. He starts over Chase Brown in both leagues."


def test_a_card_with_stats_ledes_with_the_first_sentence_and_the_back_has_the_rest(ps):
    assert ps("wvLedeText", TEXT, True) == "Wilson took 21 carries in week 2."
    assert ps("wvBackRest", TEXT, True) == "He starts over Chase Brown in both leagues."


def test_a_card_without_stats_ledes_with_the_whole_summary_and_the_back_repeats_none(ps):
    assert ps("wvLedeText", TEXT, False) == TEXT
    assert ps("wvBackRest", TEXT, False) == ""


def test_a_back_with_no_part_is_thin(ps):
    assert ps("wvBackThin", {"trends": "", "summary": "", "news": "", "others": ""}) is True


def test_a_back_with_any_part_is_not_thin(ps):
    assert ps("wvBackThin", {"trends": "", "summary": "", "news": "", "others": "<p>Yahoo: FA</p>"}) is False


def test_a_back_that_would_only_list_the_other_leagues_moves_them_to_the_front(ps):
    assert ps("wvOthersToFront", {"trends": "", "summary": "", "news": "", "others": "<p>x</p>"}) is True


def test_other_leagues_stay_on_a_back_that_has_more(ps):
    assert ps("wvOthersToFront", {"trends": "<div>t</div>", "summary": "", "news": "", "others": "<p>x</p>"}) is False


def test_no_other_leagues_means_nothing_to_move(ps):
    assert ps("wvOthersToFront", {"trends": "", "summary": "", "news": "", "others": ""}) is False


def test_a_league_with_the_headers_status_and_no_verdict_draws_no_line(ps):
    assert ps("wvOtherRepeats", "unknown", {"status": "unknown"}) is True


def test_a_league_with_another_status_draws_a_line(ps):
    assert ps("wvOtherRepeats", "unknown", {"status": "waiver"}) is False


def test_an_unknown_league_with_a_verdict_still_repeats_the_header(ps):
    assert ps("wvOtherRepeats", "unknown", {"status": "unknown", "verdict": {"kind": "bench"}}) is True


def test_an_open_league_with_the_same_status_but_a_verdict_or_need_draws_a_line(ps):
    got = [ps("wvOtherRepeats", "fa", {"status": "fa", "verdict": {"kind": "bench"}}),
           ps("wvOtherRepeats", "fa", {"status": "fa", "need": True})]
    assert got == [False, False]


def test_all_blank_stats_leave_nothing_to_draw(ps):
    cells = [{"id": "a", "now": None}, {"id": "b", "now": None}, {"id": "c", "now": None}]
    assert ps("wvProofShown", cells) == []
