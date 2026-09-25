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
