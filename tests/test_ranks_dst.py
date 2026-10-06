"""Ranks > D/ST and K, in the browser (2026-10-05, plan U6c): layout and taps only. The rows, the order,
the league's cell and every flag are Node's (tests/test_js_dst.py). The tab's own tests mount Ranks
alone (tests/component.py); the two ways in from another view load the full page."""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.ranks import RanksPage
from test_render import open_at

PHONE = (390, 844)
NO_TEAM = 'try { localStorage.removeItem("tw-team"); } catch (e) {}\n'


@pytest.mark.render
@pytest.mark.req("Ranks", ac="no team reads ESPN, which has no K tab")
def test_no_team_reads_espn_with_no_k_tab(mount):
    page, errors = mount("ranks", size=PHONE, init=(NO_TEAM,))
    ranks = RanksPage(page)
    assert ranks.chips() == ["QB", "RB", "WR", "TE", "FLEX", "D/ST"], "ESPN has no K slot"
    ranks.pick("DST")
    assert len(ranks.dst_rows()) == 32
    assert "points and yards allowed" in ranks.sub(), "ESPN's D/ST scoring"
    assert any(r["streamer"] for r in ranks.dst_rows()), "a streamer wears its tag"
    assert ranks.fits() and ranks.chips_fit()
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Ranks", ac="a Yahoo team adds the K tab, on that league's scoring")
def test_a_yahoo_team_adds_the_k_tab_on_that_leagues_scoring(mount):
    page, errors = mount("ranks", size=PHONE)      # the suite's seed picks the Yahoo team
    ranks = RanksPage(page)
    assert ranks.chips() == ["QB", "RB", "WR", "TE", "FLEX", "D/ST", "K"]
    assert ranks.fits() and ranks.chips_fit(), "seven chips fit one row at 390px"
    ranks.pick("K")
    assert len(ranks.dst_rows()) == 32
    assert "distance ÷ 10" in ranks.sub(), "The Madden Curse kicks by distance"
    ranks.pick("DST")
    assert "points allowed" in ranks.sub()
    assert ranks.fits() and ranks.chips_fit()
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Ranks", ac="switching to ESPN drops an open K tab for RB")
def test_a_team_switch_to_espn_drops_a_k_tab_that_is_open(mount):
    page, errors = mount("ranks", size=PHONE)
    ranks = RanksPage(page)
    ranks.pick("K")
    ranks.pick_team("espn")
    assert ranks.chips() == ["QB", "RB", "WR", "TE", "FLEX", "D/ST"]
    assert ranks.pressed() == "RB", "K is gone, so RB"
    assert errors == []


@pytest.mark.render
def test_a_dst_file_for_another_week_than_the_page_draws_no_dst_or_k_tab(mount):
    """After the turn the D/ST file still holds last week (2026-10-05): no tab, rather than week 2's board
    under week 3's chips. The fixture's file is week 2, the page's week is moved to 3."""
    page, errors = mount("ranks", size=PHONE)
    ranks = RanksPage(page)
    assert "D/ST" in ranks.chips()
    page.evaluate("LIVE_SCHEDULE.week = 3; render()")
    assert ranks.chips() == ["QB", "RB", "WR", "TE", "FLEX"]
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Ranks", ac="every tab links to the Schedule leaf")
def test_ranks_links_to_the_schedule_leaf(mount):
    """The link, not the leaf: strength of schedule is another view's."""
    page, errors = mount("ranks", size=PHONE)
    ranks = RanksPage(page)
    link = ranks.schedule_link()
    assert link["text"].lower() == "schedule" and link["goes"] == "schedule"
    ranks.pick("DST")
    assert ranks.schedule_link()["goes"] == "schedule", "on every tab"
    assert errors == []


@pytest.mark.journey
@pytest.mark.render
@pytest.mark.req("Ranks", ac="Waivers' Stream a D/ST link lands on Ranks > D/ST in one tap")
def test_the_waivers_view_links_to_the_dst_board_in_one_tap(browser, page_file):
    """"Stream a D/ST" on Waivers is rkOpenDst's caller: one tap from Waivers lands on Ranks > D/ST."""
    ctx, page, errors = open_at(browser, page_file, PHONE, "#waivers")
    try:
        ranks = RanksPage(page)
        assert ranks.surface() == "waivers"
        link = ranks.waivers_dst_link()
        assert link and link["text"].lower() == "stream a d/st"   # .btn is set in capitals
        assert link["height"] >= 44
        ranks.follow_waivers_dst_link()
        assert ranks.surface() == "ranks"
        assert ranks.pressed() == "D/ST"
        assert errors == []
    finally:
        ctx.close()


@pytest.mark.journey
@pytest.mark.render
@pytest.mark.req("Ranks", ac="another view opens Ranks on the D/ST tab with one call")
def test_another_view_opens_ranks_on_the_dst_tab(browser, page_file):
    """rkOpenDst() is the one call a link elsewhere makes (Digest, Waivers): Ranks on D/ST, no second tap.
    Without it the way in is Stats, Ranks, D/ST: three taps."""
    ctx, page, errors = open_at(browser, page_file, PHONE)
    try:
        ranks = RanksPage(page)
        assert ranks.surface() == "digest"
        ranks.open_dst_from_elsewhere()
        assert ranks.surface() == "ranks"
        assert len(ranks.dst_rows()) == 32
        assert ranks.pressed() == "D/ST"
        assert errors == []
    finally:
        ctx.close()
