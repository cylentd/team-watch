"""Home's hero on a desktop and under a pointer (David 2026-10-08, ledger #73: "the desktop design is not good. Also on
hover the headline doesnt flip like a scoreboard like the previous animation"), in the browser. On a desktop the pane
hugs a whole, uncropped head; a pointer over the band turns the headline over letter by letter, as the ghost's letters
did from b0284898; reduced motion leaves it still. The character rule is a Node test, tests/test_js_hero_chars.py."""
import pytest

from component import mount  # noqa: E402,F401  (the fixture)
from pages.digest_day import DigestDayPage
from test_digest_day import NOON, PHONE

pytestmark = pytest.mark.render

# The narrowest desktop, David's own screen, the widest: three pages, within the module's page budget (component.py).
DESKS = [(1024, 900), (1635, 900), (1920, 1080)]
SLANT = 0.22        # face.css --dg-pane-slant: the share of the pane's width its slanted edge takes at the top
MOTION = "window.__heroHover = 1"     # a page of its own, so turning motion on never reaches another test's page
STILL = "window.__heroStill = 1"      # a page of its own, so the pointer left over the band never reaches another test

BOXES = """bn => { const box = el => { const r = el.getBoundingClientRect(); return {l: r.left, r: r.right, t: r.top, b: r.bottom, w: r.width, h: r.height}; };
  const q = s => bn.querySelector(s);
  return {pane: box(q('[data-testid="digest-lead-pane"]')), face: box(q('[data-testid="digest-lead-face"]')),
          head: box(q('[data-testid="digest-lead-head"]')), fit: getComputedStyle(q('img.dg-hface')).objectFit}; }"""
# Every letter of the headline: its text and whether it is turned (a transform other than none).
LETTERS = """bn => { const h = bn.querySelector('[data-testid="digest-lead-head"]');
  const cs = [...h.querySelectorAll('.dg-hc')];
  return {text: cs.map(c => c.textContent).join(''), solid: h.textContent.replace(/\\s+/g, ''),
          turned: cs.map(c => getComputedStyle(c).transform !== 'none'),
          delays: cs.map(c => parseFloat(getComputedStyle(c).transitionDelay))}; }"""


def player_day(mount, size, init=()):
    page, errors = mount("digest", size=size, heads=True, init=init)
    DigestDayPage(page).plant_tnf_about_player(NOON["thu"])
    return page, page.get_by_test_id("digest-lead"), errors


@pytest.mark.req("Home", ac="on a desktop the hero's face is the whole head and shoulders, never cropped")
@pytest.mark.parametrize("size", DESKS, ids=[str(s[0]) for s in DESKS])
def test_a_desktop_draws_the_whole_head(mount, size):
    _, bn, errors = player_day(mount, size)
    got = bn.evaluate(BOXES)
    assert got["fit"] == "contain", "the square head is drawn whole inside its box, never cropped to cover it"
    assert errors == []


@pytest.mark.req("Home", ac="on a desktop the pane hugs the face: no more room beside him than its slanted edge takes")
@pytest.mark.parametrize("size", DESKS, ids=[str(s[0]) for s in DESKS])
def test_a_desktop_pane_hugs_the_face(mount, size):
    _, bn, errors = player_day(mount, size)
    got = bn.evaluate(BOXES)
    pane, face = got["pane"], got["face"]
    assert pane["w"] - face["w"] <= SLANT * pane["w"] + 1 and abs(face["r"] - pane["r"]) <= 1
    assert got["head"]["r"] <= pane["l"] + SLANT * pane["w"], "the headline ends before the pane"
    assert errors == []


@pytest.mark.req("Home", ac="on Blip's day no ghost letters peek out beside the narrower desktop pane")
def test_blips_day_shows_no_ghost_beside_the_pane(mount):
    page, errors = mount("digest", size=DESKS[1], heads=True)     # the desktop tests' own page: every test plants its day
    dg = DigestDayPage(page)
    dg.plant_tnf(NOON["thu"])
    got = dg.hero_pane()
    assert got["blip"] and got["ghost"] is False
    assert errors == []


@pytest.mark.req("Home", ac="a pointer over the hero turns its headline over letter by letter, left to right")
def test_a_pointer_turns_the_headline_over_letter_by_letter(mount):
    page, bn, errors = player_day(mount, DESKS[1], init=(MOTION,))
    page.emulate_media(reduced_motion="no-preference")
    before = bn.evaluate(LETTERS)
    bn.hover()
    page.wait_for_function("() => [...document.querySelectorAll('.dg-bn.hero .dg-hc')].every(c => getComputedStyle(c).transform !== 'none')")
    after = bn.evaluate(LETTERS)
    assert before["text"] == before["solid"] and not any(before["turned"]), "every letter is one tile, at rest before"
    assert all(after["turned"]) and after["delays"] == sorted(after["delays"]) and after["delays"][0] < after["delays"][-1]
    assert errors == []


@pytest.mark.req("Home", ac="reduced motion keeps the headline still under a pointer")
def test_reduced_motion_keeps_the_headline_still_under_a_pointer(mount):
    _, bn, errors = player_day(mount, DESKS[0], init=(STILL,))
    bn.hover()
    got = bn.evaluate(LETTERS)
    assert got["text"] == got["solid"] and not any(got["turned"])
    assert errors == []


@pytest.mark.req("Home", ac="a phone's hero keeps its pane: the face covers it, top to bottom")
def test_a_phone_keeps_the_covering_face(mount):
    _, bn, errors = player_day(mount, PHONE)
    assert bn.evaluate(BOXES)["fit"] == "cover"
    assert errors == []
