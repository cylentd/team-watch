"""The team switch on a phone (2026-09-25): the menu used to open clipped under the title, so a tap
meant for ESPN landed on the Sheet / Cards chips below it. A click in Playwright retries until the
target is hit, so the test asks what is actually on top at the point a finger would tap."""
import pytest

from test_render import browser, drive, go, open_page  # noqa: F401  (browser is a fixture)

pytestmark = pytest.mark.render


@pytest.mark.parametrize("mode", ["sheet", "cards"])
def test_every_league_in_the_menu_is_on_top_where_a_finger_taps(browser, page_file, mode):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    drive(page, go("roster"))
    page.click(f"[data-rmode='{mode}']")
    page.click("[data-tsbtn]")
    covered = page.evaluate("""[...document.querySelectorAll('.ts-menu .ts-item')].map(b => {
      const r = b.getBoundingClientRect(), hit = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
      return hit && b.contains(hit) ? null : (b.dataset.k || 'add') + ' under ' + (hit ? hit.className : 'nothing');
    }).filter(Boolean)""")
    assert covered == []
    other = page.evaluate("VIEW === 'yahoo' ? 'espn' : 'yahoo'")
    page.click(f".ts-item[data-k='{other}']")
    assert page.evaluate("VIEW") == other
    assert errors == []
    ctx.close()


SHOWN = "[...document.querySelectorAll('.ts-menu .ts-item[data-k]')].map(b => b.dataset.k)"


def test_the_menu_lists_followed_teams_and_a_league_on_request(browser, page_file):
    """2026-09-26: the menu is the reader's own teams. Since 2026-09-29 every other team waits
    behind its league's row (storyboard option A), and a star follows one, the menu staying open."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    drive(page, go("roster"))
    page.click("[data-tsbtn]")
    assert sorted(page.evaluate(SHOWN)) == ["espn", "yahoo"], "unset, the list is David's two teams"
    lg = page.evaluate("MATES[0]?.league || null")
    if not lg:
        pytest.skip("the fixture has no leaguemates")
    mates = page.evaluate(f"mateKeys('{lg}').sort(tsByName)")
    page.click(f"[data-tsleague='{lg}']")
    assert page.evaluate(SHOWN) == [lg, *mates], "David's team first, then by name"
    page.click(f"[data-follow='{mates[0]}']")
    assert page.locator("[data-tsmenu]").is_visible(), "a star keeps the menu open"
    page.click("[data-tsback]")
    assert page.evaluate(SHOWN) == ["yahoo", "espn", mates[0]], "Back shows the first screen, the new follow in it"
    assert page.evaluate("document.activeElement.dataset.tsleague") == lg, "focus returns to the league's row"
    page.click("[data-follow='yahoo']")
    assert "yahoo" not in page.evaluate(SHOWN), "unfollowed, it leaves Following"
    assert page.evaluate("JSON.parse(localStorage.getItem('tw-follow'))") == ["espn", mates[0]]
    assert errors == []
    ctx.close()


def test_a_whole_league_fits_the_menu_on_a_phone(browser, page_file):
    """Option A's point: a league's twelve on screen without scrolling the menu, at 360 x 740."""
    ctx, page, errors = open_page(browser, page_file, (360, 740))
    drive(page, go("roster"))
    page.click("[data-tsbtn]")
    if not page.locator("[data-tsleague]").count():
        pytest.skip("the fixture has no leaguemates")
    page.click("[data-tsleague]")
    over = page.evaluate("(m => m.scrollHeight - m.clientHeight)(document.querySelector('[data-tsmenu]'))")
    assert over <= 1, f"the league's list scrolls {over}px inside the menu"
    assert page.evaluate("document.activeElement.matches('[data-tsback]')"), "focus moves to Back"
    assert errors == []
    ctx.close()


def test_the_menu_opens_on_the_league_of_an_unfollowed_team(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    drive(page, go("roster"))
    mate = page.evaluate("MATES.map(m => m.key)[0] || null")
    if not mate:
        pytest.skip("the fixture has no leaguemates")
    # Viewed, not picked: a pick follows the team by default (data/mates.js followLoad).
    page.evaluate(f"VIEW = '{mate}'; render()")
    page.click("[data-tsbtn]")
    assert page.locator("[data-tsback]").is_visible()
    assert page.get_attribute(f".ts-item[data-k='{mate}']", "aria-selected") == "true"
    assert errors == []
    ctx.close()
