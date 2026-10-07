"""The roster's Cards view for the pack tests (test_pack_stage.py, test_roster_cards.py, test_roster_pack.py):
reduced motion through `show_cards` (and `on_cards` in test_roster_cards.py), motion on, mounted in a context of
its own with the page's virtual clock (`VCLOCK`, pages/roster_pack.py) installed, through `on_motion`. Kept apart
from roster_pack.py because `RosterPage` (pages/roster.py) imports that module.

Setting the page up is one round trip, not a click on the Cards chip and another on Skip or Rip (a click waits
for the control to hold still, ~60-140 ms each): the setup `.click()`s the same two buttons in the page, so the
same handlers run. Each control is still tapped for real in the test about it (`mode` in test_pack_stage's
browsed-team test, `skip_pack` and `rip_gate` in its Skip tests and test_roster_pack's rip tests).
"""
from pages.roster import MOTION, RosterPage

# VIEW = team; the Sheet / Cards chip's handler; then, when a pack waits, Skip or Rip on it. Returns how many
# packs were waiting before either button was pressed.
SHOW_CARDS = """([team, press]) => {
  VIEW = team; render();
  document.querySelector('[data-testid="roster-mode"][data-rmode="cards"]').click();
  const waiting = document.querySelectorAll('[data-testid="roster-pack-gate"]').length;
  const btn = press && document.querySelector('[data-testid="roster-pack-gate"] [data-testid="roster-pack-' + press + '"]');
  if (btn) btn.click();
  return waiting;
}"""


def show_cards(roster, team="espn", press=None):
    """The team's roster in Cards view in one round trip; `press` "skip" or "rip" then presses that button on
    the waiting pack. Returns the packs that were waiting before it."""
    return roster.page.evaluate(SHOW_CARDS, [team, press])


def press_gate(roster, which):
    """Press Rip or Skip ("rip", "skip") on the waiting pack in the page, as setup for a test about what comes
    after (a click on it for real waits for the pack to hold still, ~100 ms)."""
    roster.page.evaluate("w => document.querySelector('[data-testid=\"roster-pack-gate\"] [data-testid=\"roster-pack-' + w + '\"]').click()",
                         which)


def on_motion(mount):
    """The ESPN roster in Cards view as a reader without reduced motion sees it, on the virtual clock:
    (RosterPage, errors). `mount` may be a `Mounter` over another build (a signed week). The page loaded under
    reduced motion (`mount`'s context); the media query is read as the page runs, so switching it and drawing
    the roster again is all it takes."""
    page, errors = mount("roster", size=(390, 844), init=(MOTION,))
    roster = RosterPage(page)
    page.emulate_media(reduced_motion="no-preference")
    roster.install_clock()
    show_cards(roster)
    return roster, errors
