"""The roster's Cards view with motion on, mounted, for the pack's motion tests (test_pack_stage.py): a
context of its own (`mount` loads with reduced motion on), the page's virtual clock (`VCLOCK`,
pages/roster_pack.py) installed, the cards shown. A test that only reads the cards or the pack under
reduced motion mounts `RosterPage` through `on_cards` (test_roster_cards.py). Kept apart from
roster_pack.py because `RosterPage` (pages/roster.py) imports that module.
"""
from pages.roster import MOTION, RosterPage


def on_motion(mount):
    """The ESPN roster in Cards view as a reader without reduced motion sees it, on the virtual clock:
    (RosterPage, errors). `mount` may be a `Mounter` over another build (a signed week)."""
    page, errors = mount("roster", size=(390, 844), init=(MOTION,))
    roster = RosterPage(page)
    roster.allow_motion()
    roster.install_clock()
    roster.show_cards("espn")
    return roster, errors
