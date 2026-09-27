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


def test_the_menu_lists_followed_teams_and_leaguemates_on_request(browser, page_file):
    """2026-09-26: the menu is the reader's own teams; every other team waits behind Leaguemates,
    and a star moves one across, the menu staying open."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    drive(page, go("roster"))
    page.click("[data-tsbtn]")
    shown = lambda: page.evaluate("[...document.querySelectorAll('.ts-menu .ts-item[data-k]')].map(b => b.dataset.k)")
    assert sorted(shown()) == ["espn", "yahoo"], "unset, the list is David's two teams"
    mates = page.evaluate("MATES.map(m => m.key)")
    if not mates:
        pytest.skip("the fixture has no leaguemates")
    page.click("[data-tsmore]")
    assert set(shown()) == {"espn", "yahoo", *mates}
    page.click(f"[data-follow='{mates[0]}']")
    assert page.locator("[data-tsmenu]").is_visible(), "a star keeps the menu open"
    followed = page.evaluate("[...document.querySelectorAll('.ts-star[aria-pressed=true]')].map(b => b.dataset.follow)")
    assert followed == ["yahoo", "espn", mates[0]]
    page.click("[data-follow='yahoo']")
    assert page.get_attribute("[data-follow='yahoo']", "aria-pressed") == "false", "unfollowed, it moves down to Leaguemates"
    assert page.evaluate("JSON.parse(localStorage.getItem('tw-follow'))") == ["espn", mates[0]]
    assert errors == []
    ctx.close()
