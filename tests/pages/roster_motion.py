"""The roster's Cards view on the full page, for the tests that cannot mount it (test_pack_stage.py,
test_clip_sheet.py): a page with motion on, on the virtual clock (`VCLOCK`, pages/roster_pack.py), or a
journey over the whole app. A test that only reads the cards or the pack mounts `RosterPage` instead
(`on_cards` in test_roster_cards.py). Kept apart from roster_pack.py because these open a page, and
`RosterPage` (pages/roster.py) imports that module.
"""
import re

from pages.roster import RosterPage
from test_render import LOAD_MS, SEED, drive, go, open_page, watch_errors


def cards_page(browser, page_file, viewport=(360, 660), keep_stage=False, gate=False):
    """The ESPN roster in Cards view on the full page, reduced motion. ESPN is a followed team, so this
    week's pack waits in the starters' place: `keep_stage` opens it onto its stage, `gate` leaves it
    waiting, neither skips it so the starters are face up."""
    ctx, page, errors = open_page(browser, page_file, viewport)
    drive(page, go("roster"))
    roster = RosterPage(page)
    roster.show_cards("espn")
    assert roster.gates() == 1, "the fixture's schedule has a week ahead, so a pack waits"
    if keep_stage:
        roster.open_stage()
    elif not gate:
        roster.skip_pack()
    return ctx, page, errors


def motion_page(browser, page_file):
    """The same, with motion on, as a reader without reduced motion sees it, on the virtual clock."""
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="no-preference")
    page = ctx.new_page()
    page.set_default_timeout(5000)
    errors = watch_errors(page)
    page.route(re.compile(r"^https?://"), lambda route: route.abort())
    page.add_init_script(SEED)
    page.goto(page_file.as_uri() + "#roster", timeout=LOAD_MS)
    page.wait_for_function("document.getElementById('view').children.length > 0")
    roster = RosterPage(page)
    roster.install_clock()
    roster.show_cards("espn")
    return ctx, page, errors


def stage_opens(page):
    """Rip on the motion page's waiting pack opens the stage, on the page's clock."""
    RosterPage(page).open_stage_on_the_clock()
