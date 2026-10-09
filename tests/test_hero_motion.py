"""Home's hero (David 2026-10-08: "the headshot is not clear. looks pixelated. I also want the scoreboard animation
back"), in the browser: the face asks for a cut as large as the side it is drawn at, and the headline turns over word
by word as the band lands, at rest under reduced motion. The rules themselves are Node tests, tests/test_js_hero_sharp.py.
"""
import pytest

from component import mount  # noqa: E402,F401  (the fixture)
from pages.digest_day import DigestDayPage
from test_digest_day import NOON, PHONE, WIDE

pytestmark = pytest.mark.render

MOTION = "window.__heroMotion = 1"     # a page of its own, so turning motion on never reaches another test's page

# The face: object-fit cover draws the square head at the larger of the pane's two sides.
FACE = """bn => { const img = bn.querySelector('img.dg-hface'), r = img.getBoundingClientRect();
  return {sizes: img.sizes, side: Math.ceil(Math.max(r.width, r.height)), srcset: img.srcset}; }"""
# Every split-flap word of the headline: its text, animation and delay, and the headline's words as read.
WORDS = """bn => { const h = bn.querySelector('[data-testid="digest-lead-head"]');
  const tiles = [...h.querySelectorAll('.dg-hw')].map(w => { const s = getComputedStyle(w);
    return {t: w.textContent, anim: s.animationName, delay: parseFloat(s.animationDelay), transform: s.transform}; });
  return {tiles, words: h.textContent.trim().split(/\\s+/)}; }"""


def hero(page):
    return page.get_by_test_id("digest-lead")


@pytest.mark.req("Home", ac="the hero's face asks for a cut as large as the side it is drawn at, so it never blurs")
@pytest.mark.parametrize("size", [PHONE, WIDE], ids=["phone", "wide"])
def test_the_face_asks_for_the_side_it_is_drawn_at(mount, size):
    page, errors = mount("digest", size=size, heads=True)
    DigestDayPage(page).plant_tnf_about_player(NOON["thu"])
    got = hero(page).evaluate(FACE)
    assert got["sizes"] == f"{got['side']}px" and got["srcset"]
    assert errors == []


@pytest.mark.req("Home", ac="the hero's headline turns over word by word, left to right, as the band lands")
def test_the_headline_turns_over_word_by_word(mount):
    page, errors = mount("digest", size=PHONE, init=(MOTION,))
    page.emulate_media(reduced_motion="no-preference")
    DigestDayPage(page).at(NOON["fri"])
    got = hero(page).evaluate(WORDS)
    assert [w["t"] for w in got["tiles"]] == got["words"], "every word of the headline is one tile"
    assert {w["anim"] for w in got["tiles"]} == {"dg-flip-word"}
    delays = [w["delay"] for w in got["tiles"]]
    assert delays == sorted(delays) and delays[0] < delays[-1], "the words turn over left to right"
    assert errors == []


@pytest.mark.req("Home", ac="reduced motion gets the hero's headline at rest, with no flip")
def test_reduced_motion_gets_the_headline_at_rest(mount):
    page, errors = mount("digest", size=PHONE)
    DigestDayPage(page).at(NOON["fri"])
    got = hero(page).evaluate(WORDS)
    assert got["tiles"] and {(w["anim"], w["transform"]) for w in got["tiles"]} == {("none", "none")}
    assert errors == []
