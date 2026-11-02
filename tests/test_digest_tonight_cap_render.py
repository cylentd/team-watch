"""Tonight's blocks count in the five, in the page: digest.js hands dgDayBlocks the real count of Tonight blocks.

David, 2026-11-01. The rule itself is pinned in Node (test_js_digest_tonight_cap.py); this proves the page passes it.
The fixture's Monday draws only two of its cards, so the five-block total is out of reach cheaply: the test
records what the page passes to dgDayBlocks and compares it with the blocks Tonight drew.
"""
import pytest

from component import mount  # noqa: E402,F401  (the fixture)
from pages.digest_live import DigestLivePage

PHONE = (390, 844)
MON_NIGHT = "2026-10-06T00:30:00Z"   # Monday 5:30 PM Pacific, the Monday pair 15 minutes in
CLOCK = {"CHI": {"state": "in", "q": 1, "clock": "9:00", "half": False, "detail": "", "clubs": ["CHI", "PHI"]}}
SPY = """() => { const real = dgDayBlocks; window.PASSED = [];
  dgDayBlocks = (...a) => { window.PASSED.push(a[3]); return real(...a); }; render();
  return [window.PASSED.at(-1), document.querySelector('.dg-tns').children.length]; }"""


@pytest.mark.render
@pytest.mark.req("Digest", ac="Tonight's blocks count in the five")
def test_the_digest_passes_the_number_of_tonight_blocks_it_drew(mount):
    page, errors = mount("digest", size=PHONE)
    dg = DigestLivePage(page)
    dg.plant_live(at=MON_NIGHT, mon=["CHI", "PHI"], monKick="2026-10-06T00:15:00Z", sunState="final",
                  monState="in_game", clock=CLOCK)
    assert page.evaluate(SPY) == [1, 1]   # one block drew (the game's), and one was passed
    assert errors == []
