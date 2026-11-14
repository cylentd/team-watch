"""Boom and bust on Stats > Ranks (2026-11-13, density redo), as drawn: Projection's row unchanged, Upside and Safe rows
that lead with their percent and the points small under it, the one-line explainer and its ⓘ, the list with no odds,
and the fit at 360px. The sort rules are Node tests (test_js_outcome.py).

Fixture odds (tests/fixtures, boom / bust): Chase Brown 16.2 pts .27/.17, Breece Hall 15.0 .29/.19, Kendre Miller 3.1
.01/.86, Amon-Ra St. Brown 17.3 .33/.11, George Kittle 13.6 .37/.12, Joe Burrow 19.4 .22/.14."""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.ranks import RanksPage
from pages.ranks_odds import RanksOddsPage
from wording import words

RB_BY = {"pts": ["chase-brown", "breece-hall", "kendre-miller"],
         "boom": ["breece-hall", "chase-brown", "kendre-miller"],
         "bust": ["chase-brown", "breece-hall", "kendre-miller"]}
FLEX_BY = {"boom": ["george-kittle", "amonra-st-brown", "breece-hall", "chase-brown", "kendre-miller"],
           "bust": ["amonra-st-brown", "george-kittle", "chase-brown", "breece-hall", "kendre-miller"]}
PTS = words("ranks.odds.pts")
RB_ANSWERS = {"boom": [["breece-hall", "29%", PTS.format(n="15.0")], ["chase-brown", "27%", PTS.format(n="16.2")],
                       ["kendre-miller", "1%", PTS.format(n="3.1")]],
              "bust": [["chase-brown", "17%", PTS.format(n="16.2")], ["breece-hall", "19%", PTS.format(n="15.0")],
                       ["kendre-miller", "86%", PTS.format(n="3.1")]]}


def open_ranks(mount, pos="RB"):
    page, errors = mount("ranks")
    ranks = RanksPage(page)
    if pos != "RB":
        ranks.pick(pos)
    return ranks, RanksOddsPage(page), errors


@pytest.mark.req("Ranks", ac="Projection keeps the row as it was")
def test_projection_rows_keep_two_lines_their_range_and_no_odds(mount):
    _, odds, errors = open_ranks(mount)
    assert odds.sorts() == [words("ranks.sort.pts"), words("ranks.sort.boom"), words("ranks.sort.bust")]
    assert odds.pressed() == words("ranks.sort.pts"), "a visit opens on Projection"
    assert odds.answers() == [[s, None, None] for s in RB_BY["pts"]]
    assert {lines for lines, _, _ in odds.row_shape()} == {2}
    assert errors == []


@pytest.mark.req("Ranks", ac="a sort shows the number it sorts by")
@pytest.mark.parametrize("sort", ["boom", "bust"])
def test_a_sorted_row_leads_with_its_percent_and_the_points_under_it(mount, sort):
    _, odds, errors = open_ranks(mount)
    odds.sort_by(sort)
    assert odds.answers() == RB_ANSWERS[sort]
    assert odds.row_shape() == [[2, False, False]] * 3, "two lines, no range, no matchup delta"
    assert errors == []


@pytest.mark.req("Ranks", ac="Projection, Upside and Safe sorts")
@pytest.mark.parametrize("sort", ["boom", "bust", "pts"])
def test_each_sort_orders_the_backs_and_only_projection_keeps_tiers(mount, sort):
    ranks, odds, errors = open_ranks(mount)
    odds.sort_by("boom" if sort == "pts" else sort)
    odds.sort_by(sort)
    assert [r["slug"] for r in ranks.rows()] == RB_BY[sort]
    assert len(ranks.tiers()) == (2 if sort == "pts" else 0), "tiers are cut on points, so a sorted list has none"
    assert errors == []


@pytest.mark.req("Ranks", ac="Projection, Upside and Safe sorts")
@pytest.mark.parametrize("sort", ["boom", "bust"])
def test_flex_sorts_across_positions(mount, sort):
    ranks, odds, errors = open_ranks(mount, "FLEX")
    odds.sort_by(sort)
    assert [r["slug"] for r in ranks.rows()] == FLEX_BY[sort]
    assert errors == []


@pytest.mark.req("Ranks", ac="the explainer is one line naming the bar")
@pytest.mark.parametrize("pos,sort,line", [
    ("RB", "pts", words("ranks.head.subShort").format(scoring="half-PPR")),
    ("RB", "boom", words("ranks.head.subBoom").format(n=20)),
    ("QB", "bust", words("ranks.head.subBust").format(n=12)),
    ("FLEX", "boom", words("ranks.head.withOthers").format(line=words("ranks.head.subBoom").format(n=20),
                                                           rest=words("ranks.head.otherBoom").format(pos="TE", n=15))),
    ("FLEX", "bust", words("ranks.head.withOthers").format(line=words("ranks.head.subBust").format(n=8),
                                                           rest=words("ranks.head.otherBust").format(pos="TE", n=5))),
])
def test_the_explainer_is_one_line_at_360_naming_the_bar(mount, pos, sort, line):
    _, odds, errors = open_ranks(mount, pos)
    odds.sort_by("boom" if sort == "pts" else sort)
    odds.sort_by(sort)
    assert odds.line() == line
    assert odds.line_count() == 1
    assert errors == []


@pytest.mark.req("Ranks", ac="the full definition is behind the ⓘ")
@pytest.mark.parametrize("sort,full", [
    ("pts", words("ranks.head.sub").format(scoring="half-PPR")),
    ("boom", words("ranks.odds.note").format(boom=20, bust=8)),
])
def test_the_info_tap_opens_and_closes_the_full_definition(mount, sort, full):
    _, odds, errors = open_ranks(mount)
    odds.sort_by("boom" if sort == "pts" else sort)
    odds.sort_by(sort)
    assert odds.more() is None
    odds.tap_info()
    assert odds.more().count(full) == 1
    odds.tap_info()
    assert odds.more() is None
    assert errors == []


@pytest.mark.req("Ranks", ac="no odds in the file, nothing drawn")
def test_a_list_without_odds_draws_no_chips_no_answer_and_keeps_its_tiers(mount):
    ranks, odds, errors = open_ranks(mount)
    odds.sort_by("boom")
    odds.plant_no_odds()
    assert odds.sorts() == []
    assert odds.answers() == [[s, None, None] for s in RB_BY["pts"]]
    assert [r["slug"] for r in ranks.rows()] == RB_BY["pts"] and len(ranks.tiers()) == 2, "back to the build's order"
    assert odds.line() == words("ranks.head.subShort").format(scoring="half-PPR")
    assert errors == []


def test_defenses_have_no_sort(mount):
    ranks, odds, errors = open_ranks(mount, "DST")
    assert ranks.dst_rows() and odds.sorts() == []
    assert errors == []


def test_leaving_ranks_forgets_the_sort_and_closes_the_info(mount):
    ranks, odds, errors = open_ranks(mount)
    odds.sort_by("bust")
    odds.tap_info()
    odds.leave_and_come_back()
    assert odds.pressed() == words("ranks.sort.pts") and odds.more() is None
    assert [r["slug"] for r in ranks.rows()] == RB_BY["pts"]
    assert errors == []


@pytest.mark.req("Ranks", ac="the row fits 360px")
@pytest.mark.parametrize("pos,sort", [("RB", "pts"), ("FLEX", "boom"), ("QB", "bust")])
def test_at_360_no_name_is_cut(mount, pos, sort):
    ranks, odds, errors = open_ranks(mount, pos)
    odds.sort_by("boom" if sort == "pts" else sort)
    odds.sort_by(sort)
    assert odds.row_fit() and odds.sort_row_fits() and ranks.fits()
    assert errors == []
