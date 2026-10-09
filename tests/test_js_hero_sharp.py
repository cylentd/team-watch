"""Home's hero, in Node (David 2026-10-08: "the headshot is not clear. looks pixelated. I also want the scoreboard
animation back"): data/hero.js dgHeroCuts names every headshot cut so the browser takes one sharp at the size the
pane draws it, and dgFlapWords turns the headline into split-flap words. Where they land on the band, and the flip
under reduced motion, is tests/test_hero_motion.py."""
import re

import pytest

SM = {"ceedee-lamb": "heads/ceedee-lamb.webp", "bucky-irving": "heads/bucky-irving.webp"}
LG = {"ceedee-lamb": "heads/lg/ceedee-lamb.webp"}
XL = {"ceedee-lamb": "heads/xl/ceedee-lamb.webp"}
CUTS = [[SM, 96], [LG, 256], [XL, 512]]       # player.js headSrcset's widths: what ff-jarvis cuts
POSES = {"sweat": "Sweat"}


@pytest.fixture(scope="module")
def js(node_js):
    return node_js("data/hero.js")


# ---------------------------------------------------------------- the face's cuts

@pytest.mark.req("Home", ac="the hero's face offers every cut, so a 2x screen loads the 512px one and never blurs")
def test_the_face_offers_every_cut_and_falls_back_to_the_largest(js):
    got = js("dgHeroCuts", "ceedee-lamb", CUTS)
    assert got == {"src": XL["ceedee-lamb"],
                   "srcset": f"{SM['ceedee-lamb']} 96w, {LG['ceedee-lamb']} 256w, {XL['ceedee-lamb']} 512w"}


def test_a_player_with_only_the_small_head_has_that_one_cut(js):
    assert js("dgHeroCuts", "bucky-irving", CUTS) == {"src": SM["bucky-irving"], "srcset": f"{SM['bucky-irving']} 96w"}


@pytest.mark.parametrize("cuts", [[[SM, 96], [None, 256]], []], ids=["a-missing-map", "no-maps"])
def test_no_cut_for_him_is_no_image(js, cuts):
    assert js("dgHeroCuts", "nobody", cuts) is None


@pytest.fixture(scope="module")
def pane(node_js):
    js = node_js("data/hero.js", "surface/digest/face.js",
                 globals={"HEADS": SM, "HEADS_LG": LG, "HEADS_XL": XL, "LG_BLIP_LABEL": POSES})
    js("(globalThis.dgTeamCode = c => c || '', globalThis.blipReactSVG = () => '<svg></svg>', 0)")
    return js


def test_the_pane_names_every_cut_ff_jarvis_makes(pane):
    html = pane("dgHeroFaceParts", {"slug": "ceedee-lamb", "team": "DAL"}, {"banner": "tnf"})["html"]
    want = pane("dgHeroCuts", "ceedee-lamb", CUTS)
    assert f'src="{want["src"]}" srcset="{want["srcset"]}" sizes="' in html


# The face's measured side (dgHeroSharp): a stand-in band holding a face drawn in a box of the given size.
SHARP = """(([w, h]) => { const img = {getBoundingClientRect: () => ({width: w, height: h}), sizes: ''};
  dgHeroSharp({querySelector: () => img}); return img.sizes; })"""


@pytest.mark.req("Home", ac="the hero's face asks for the larger side of its pane, where object-fit cover draws it")
@pytest.mark.parametrize("box, want", [([121.2, 230], "230px"), ([473.2, 279.9], "474px")], ids=["phone", "desktop"])
def test_the_face_asks_for_the_larger_side_of_its_box(pane, box, want):
    assert pane(f"{SHARP}({box})") == want


def test_no_band_or_no_face_is_left_alone(pane):
    assert pane("(dgHeroSharp(null), dgHeroSharp({querySelector: () => null}), 'ok')") == "ok"


# ---------------------------------------------------------------- the headline's split-flap words

def words_of(html):
    return re.findall(r'<i class="dg-hw" style="--i:(\d+)">(.*?)</i>', html)


@pytest.mark.req("Home", ac="the hero's headline turns over word by word like a scoreboard, left to right")
def test_each_word_is_one_flap_counting_left_to_right(js):
    got = words_of(js("dgFlapWords", "Irving piles up"))
    assert got == [("0", "Irving"), ("1", "piles"), ("2", "up")]


def test_a_word_inside_emphasis_keeps_its_emphasis_and_the_count_runs_on(js):
    html = js("dgFlapWords", 'Lamb <em class="dg-em go">2 TDs</em>')
    assert html == ('<i class="dg-hw" style="--i:0">Lamb</i> <em class="dg-em go">'
                    '<i class="dg-hw" style="--i:1">2</i> <i class="dg-hw" style="--i:2">TDs</i></em>')


@pytest.mark.parametrize("head", ["A&amp;M wins", "  Two  spaces ", 'x <em class="dg-em">y</em>.', ""])
def test_the_words_read_exactly_as_before(js, head):
    strip = lambda s: re.sub(r"<[^>]+>", "", s)
    assert strip(js("dgFlapWords", head)) == strip(head)


def test_an_entity_stays_inside_its_word(js):
    assert words_of(js("dgFlapWords", "A&amp;M")) == [("0", "A&amp;M")]
