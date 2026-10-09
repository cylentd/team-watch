"""Home's hero v3, "the spread" (David 2026-10-08, ledger #70), in Node: surface/digest/face.js puts the subject in
a pane, his club's code on its edge. Where the pane sits on the band is tests/test_digest_day.py."""
import json

import pytest

LG = {"ceedee-lamb": "heads/lg/ceedee-lamb.webp"}
SM = {"bucky-irving": "heads/bucky-irving.webp"}
POSES = {"laugh": "Ha", "sweat": "Sweat", "flatline": "Meh"}   # LG_BLIP_LABEL's shape: pose -> label


def sandbox(node_js, heads_lg):
    js = node_js("data/hero.js", "surface/digest/face.js",
                 globals={"HEADS": SM, "HEADS_LG": heads_lg, "LG_BLIP_LABEL": POSES})
    # The view's helpers from other files, as small stand-ins: the club as the data spells it, Blip as his pose.
    js("(globalThis.dgTeamCode = c => c || '', globalThis.blipReactSVG = (l, p) => `<svg data-blip='${p}'></svg>`, 0)")
    return lambda lead: js("dgHeroFaceParts", lead, {"banner": "tnf"})


@pytest.fixture(scope="module")
def parts(node_js):
    return sandbox(node_js, LG)


@pytest.mark.req("Home", ac="a player's face sits in the hero's pane with his club's code on its edge")
def test_a_players_face_sits_in_the_pane_with_his_club(parts):
    got = parts({"slug": "ceedee-lamb", "team": "DAL"})
    assert (got["kind"], got["team"]) == ("has-face", "DAL")
    assert got["html"].startswith('<div class="dg-hpane" data-testid="digest-lead-pane"')
    assert 'src="heads/lg/ceedee-lamb.webp"' in got["html"]
    assert '<span class="dg-hclub" data-testid="digest-lead-club">DAL</span>' in got["html"]


def test_a_face_whose_club_is_unknown_has_no_code(parts):
    got = parts({"slug": "ceedee-lamb"})
    assert got["kind"] == "has-face" and "digest-lead-club" not in got["html"]


def test_without_big_heads_the_small_one_fills_the_pane(node_js):
    got = sandbox(node_js, None)({"slug": "bucky-irving", "team": "TB"})
    assert got["kind"] == "has-face" and 'src="heads/bucky-irving.webp"' in got["html"]


@pytest.mark.req("Home", ac="on a day about no one player Blip stands in the pane, with no club")
def test_blip_stands_in_the_pane_with_no_club(parts):
    got = parts({"tone": "", "take": None})
    assert (got["kind"], got["team"]) == ("has-blip", "")
    assert got["html"].startswith('<div class="dg-hpane" data-testid="digest-lead-pane"')
    assert "data-blip='sweat'" in got["html"] and "digest-lead-club" not in got["html"]


# ---------------------------------------------------------------- the band's budget (dgHeroFit)
# A band taller than a third of the screen takes its headline a size down (`long`), once. A stand-in band of a given
# height; the classes the headline ends with, in the order they were added.
FIT = """(([h, tall, had]) => { const added = [...had];
  const head = {classList: {contains: c => added.includes(c), add: c => added.push(c)}};
  const band = {getBoundingClientRect: () => ({height: tall}), querySelector: () => head};
  globalThis.window = {innerHeight: h}; dgHeroFit({querySelector: () => band}); return added; })"""


@pytest.fixture(scope="module")
def fit(node_js):
    js = node_js("data/hero.js", "surface/digest/face.js", globals={"HEADS": SM, "HEADS_LG": LG, "LG_BLIP_LABEL": POSES})
    run = lambda screen, band, had=(): js(f"{FIT}({json.dumps([screen, band, list(had)])})")
    run.budget = js("DG_HERO_BUDGET")
    return run


SCREEN = 900


@pytest.mark.req("Home", ac="a hero taller than its share of the screen takes its headline a size down, never cut")
@pytest.mark.parametrize("over, want", [(0, []), (1, ["long"])], ids=["at-the-budget", "over"])
def test_a_band_over_its_share_of_the_screen_steps_its_headline_down(fit, over, want):
    assert fit(SCREEN, SCREEN / fit.budget + over) == want


def test_a_headline_already_down_is_not_stepped_again(fit):
    assert fit(900, 400, ["long"]) == ["long"]


def test_no_band_or_no_root_is_left_alone(node_js):
    js = node_js("data/hero.js", "surface/digest/face.js", globals={"HEADS": SM, "HEADS_LG": LG, "LG_BLIP_LABEL": POSES})
    assert js("(dgHeroFit(null), dgHeroFit({querySelector: () => null}), 'ok')") == "ok"


def test_a_pose_blip_cannot_draw_leaves_the_band_bare(node_js):
    js = node_js("data/hero.js", "surface/digest/face.js", globals={"HEADS": SM, "HEADS_LG": LG, "LG_BLIP_LABEL": {}})
    assert js("dgHeroFaceParts", {"tone": ""}, {"banner": "tnf"}) == {"kind": "", "team": "", "html": ""}
