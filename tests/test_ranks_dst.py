"""Ranks > D/ST and K, in the browser (2026-10-05, plan U6c): layout and taps only. The rows, the order,
the league's cell and every flag are Node's (tests/test_js_dst.py)."""
import pytest

from test_render import open_at

PHONE = (390, 844)
NO_TEAM = 'try { localStorage.removeItem("tw-team"); } catch (e) {}\n'
ESPN_TEAM = 'try { localStorage.setItem("tw-team", "espn"); } catch (e) {}\n'
CHIPS = "[...document.querySelectorAll('[data-rkpos]')].map(b => b.textContent.trim())"
FITS = "document.documentElement.scrollWidth <= innerWidth && document.querySelector('.setrow').scrollWidth <= document.querySelector('.setrow').clientWidth"


@pytest.mark.render
def test_no_team_reads_espn_with_no_k_tab(browser, page_file):
    ctx, page, errors = open_at(browser, page_file, PHONE, "#ranks", (NO_TEAM,))
    try:
        assert page.evaluate(CHIPS) == ["QB", "RB", "WR", "TE", "FLEX", "D/ST"], "ESPN has no K slot"
        page.locator("[data-rkpos='DST']").click()
        assert page.locator(".rk-d").count() == 32
        assert "points and yards allowed" in page.locator(".rk-headline p").first.inner_text(), "ESPN's D/ST scoring"
        assert page.locator(".rk-dtag").count() > 0, "a streamer wears its tag"
        assert page.evaluate(FITS)
        assert errors == []
    finally:
        ctx.close()


@pytest.mark.render
def test_a_yahoo_team_adds_the_k_tab_on_that_leagues_scoring(browser, page_file):
    ctx, page, errors = open_at(browser, page_file, PHONE, "#ranks")      # the suite's seed picks the Yahoo team
    try:
        assert page.evaluate(CHIPS) == ["QB", "RB", "WR", "TE", "FLEX", "D/ST", "K"]
        assert page.evaluate(FITS), "seven chips fit one row at 390px"
        page.locator("[data-rkpos='K']").click()
        assert page.locator(".rk-d").count() == 32
        assert "distance ÷ 10" in page.locator(".rk-headline p").first.inner_text(), "The Madden Curse kicks by distance"
        page.locator("[data-rkpos='DST']").click()
        assert "points allowed" in page.locator(".rk-headline p").first.inner_text()
        assert page.evaluate(FITS)
        assert errors == []
    finally:
        ctx.close()


@pytest.mark.render
def test_a_team_switch_to_espn_drops_a_k_tab_that_is_open(browser, page_file):
    ctx, page, errors = open_at(browser, page_file, PHONE, "#ranks")
    try:
        page.locator("[data-rkpos='K']").click()
        page.evaluate("pickTeam('espn')")
        assert page.evaluate(CHIPS) == ["QB", "RB", "WR", "TE", "FLEX", "D/ST"]
        assert page.locator("[data-rkpos][aria-pressed='true']").inner_text().strip() == "RB", "K is gone, so RB"
        assert errors == []
    finally:
        ctx.close()


@pytest.mark.render
def test_ranks_links_to_the_schedule_leaf(browser, page_file):
    """The link, not the leaf: strength of schedule is another view's."""
    ctx, page, errors = open_at(browser, page_file, PHONE, "#ranks")
    try:
        link = page.locator(".rk-sched")
        assert link.inner_text().strip().lower() == "schedule" and link.get_attribute("data-rkgo") == "schedule"
        page.locator("[data-rkpos='DST']").click()
        assert page.locator(".rk-sched").get_attribute("data-rkgo") == "schedule", "on every tab"
        assert errors == []
    finally:
        ctx.close()


@pytest.mark.render
def test_the_waivers_view_links_to_the_dst_board_in_one_tap(browser, page_file):
    """"Stream a D/ST" on Waivers is rkOpenDst's caller: one tap from Waivers lands on Ranks > D/ST."""
    ctx, page, errors = open_at(browser, page_file, PHONE, "#waivers")
    try:
        assert page.evaluate("SURFACE") == "waivers"
        link = page.locator("[data-wvdst]")
        assert link.count() == 1 and link.inner_text().strip().lower() == "stream a d/st"   # .btn is set in capitals
        assert link.bounding_box()["height"] >= 44
        link.click()
        assert page.evaluate("SURFACE") == "ranks"
        assert page.locator("[data-rkpos][aria-pressed='true']").inner_text().strip() == "D/ST"
        assert errors == []
    finally:
        ctx.close()


@pytest.mark.render
def test_another_view_opens_ranks_on_the_dst_tab(browser, page_file):
    """rkOpenDst() is the one call a link elsewhere makes (Digest, Waivers): Ranks on D/ST, no second tap.
    Without it the way in is Stats, Ranks, D/ST: three taps."""
    ctx, page, errors = open_at(browser, page_file, PHONE)
    try:
        assert page.evaluate("SURFACE") == "digest"
        page.evaluate("rkOpenDst()")
        assert page.evaluate("SURFACE") == "ranks"
        assert page.locator(".rk-d").count() == 32
        assert page.locator("[data-rkpos][aria-pressed='true']").inner_text().strip() == "D/ST"
        assert errors == []
    finally:
        ctx.close()
