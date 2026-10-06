"""The pack's stage and its controls, fixes of 2026-09-25: "Rip again" sits over the cards and never
moves the Sheet / Cards switch, a drag on the pack turns it and it springs back, and a tap while the
cards are dealt hurries them. Since 2026-10-05 the pack waits in the starters' place on a followed team
(packgate.js) and the deal holds each hit with its label. The motion tests run on the page's virtual
clock (pages/roster_pack.VCLOCK), so no test waits for a real animation, and "how long it took" is the
page's own time."""
import re

import pytest

from pages.roster_motion import cards_page, motion_page, stage_opens
from pages.roster_pack import rip, vc_install, vc_now, vc_run, vc_until
from test_render import open_page

STARTERS = "TEAMS.espn.roster.filter(p => p.start).length"
DOWN = "document.querySelectorAll('.cards-col:not(.bench) .tc.down').length"


def chips(page):
    return page.evaluate("[...document.querySelectorAll('.rmode .chip')].map(b => Math.round(b.getBoundingClientRect().x))")


@pytest.mark.render
def test_rip_again_is_over_the_cards_and_the_switch_holds_still(browser, page_file):
    ctx, page, errors = cards_page(browser, page_file, keep_stage=True)
    in_cards = chips(page)
    rip(page)
    page.wait_for_selector(".pk-stage", state="detached")
    # The page stays on the cards that just landed (2026-09-27: closing the stage threw it to the top):
    # the starters' grid is on screen once the stage has gone. (It asserted a scroll until 2026-10-05,
    # when the shorter header let the whole grid fit without one.)
    grid = page.evaluate("(r => [r.top, r.bottom])(document.querySelector('#view .cards .cardgrid').getBoundingClientRect())")
    assert 0 <= grid[0] < grid[1] <= page.viewport_size["height"], grid
    assert page.locator(".cards .rule [data-rerip]").count() == 1
    assert page.locator(".rmode [data-rerip]").count() == 0
    page.evaluate("scrollTo(0, 0)")
    assert chips(page) == in_cards, "the rip moves neither Sheet nor Cards"
    page.click("[data-rmode='sheet']")
    assert chips(page) == in_cards, "Sheet and Cards stay where they were"
    assert page.locator("[data-rerip]").count() == 0
    assert errors == []
    ctx.close()


@pytest.mark.render
@pytest.mark.parametrize("motion", [False, True])
def test_a_pack_with_no_metal_deals_its_starters_and_says_so(browser, page_file, motion):
    """2026-09-27: a week where nobody on the roster is a hit still gets its pack (2026-10-05: the
    starters, every one stock)."""
    ctx, page, errors = motion_page(browser, page_file) if motion else cards_page(browser, page_file)
    vc_install(page)                                            # a no-op on the motion page, which has it
    page.evaluate("""Object.values(LIVE_PROJECTIONS.players).forEach(r => { if (r.rank) r.rank = 40; });
      if (typeof LIVE_SIGNED !== 'undefined' && LIVE_SIGNED) LIVE_SIGNED.players = {};
      render()""")
    assert page.evaluate("packCards(TEAMS.espn).some(packHit)") is False
    page.click("[data-pkrip]" if motion else "[data-pkopen]")
    rip(page)
    vc_until(page, "document.querySelector('.pk-msg')?.textContent.startsWith('No metal')", 20000)
    vc_until(page, "!document.querySelector('.pk-stage')", 8000)
    assert page.evaluate(DOWN) == 0 and page.locator(".cards .tc.pk-slot").count() == 0
    assert page.locator(".cards .rule [data-rerip]").count() == 1, "it can be ripped again too"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_packs_side_seams_are_never_clipped(browser, page_file):
    """2026-09-27: a clip-path on the pack's turned edge slices dropped the spin to 16 fps on a
    throttled CPU (53 without). The side seams are shaped by border-radius instead."""
    ctx, page, errors = cards_page(browser, page_file, keep_stage=True)
    clips = page.evaluate("[...document.querySelectorAll('.pk-stage .pack-wall')].map(w => getComputedStyle(w).clipPath)")
    assert len(clips) == 2 and set(clips) == {"none"}, clips
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_drag_on_the_pack_turns_it_and_it_springs_back(browser, page_file):
    ctx, page, errors = cards_page(browser, page_file, keep_stage=True)
    box = page.locator(".pk-stage .pack-seal").bounding_box()
    y = box["y"] + box["height"] * .6
    page.mouse.move(box["x"] + box["width"] / 2, y)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] * .9, y, steps=5)
    turned = page.evaluate("parseFloat(document.querySelector('.pk-center').style.getPropertyValue('--pry'))")
    page.mouse.up()
    assert turned > 10, "the pack turns with the drag"
    assert page.evaluate("document.querySelector('.pk-center').style.getPropertyValue('--pry')") == "", "and springs back"
    assert page.locator(".pk-stage .pack-seal").count() == 1, "a drag on the body does not rip"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_drag_on_the_waiting_pack_turns_it_and_a_tap_opens_it(browser, page_file):
    """2026-10-05: the pack in the starters' place turns with a sideways drag and springs back to the
    front; a press that never moved opens the stage."""
    ctx, page, errors = cards_page(browser, page_file, gate=True)
    turn = "parseFloat((getComputedStyle(document.querySelector('.pk-gate .pack-glow')).rotate.match(/(-?[\\d.]+)deg/) || [0, 0])[1])"
    box = page.locator(".pk-gpack").bounding_box()
    y = box["y"] + box["height"] * .6
    page.mouse.move(box["x"] + box["width"] * .3, y)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] * .9, y, steps=5)
    turned = page.evaluate(turn)
    page.mouse.up()
    assert turned > 40, turned
    assert page.evaluate(turn) == 0, "it springs back to the front (reduced motion: at once)"
    assert page.locator(".pk-stage").count() == 0, "a drag does not open it"
    page.mouse.click(box["x"] + box["width"] / 2, y)
    page.wait_for_selector(".pk-stage")
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_tap_does_not_hurry_the_best_cards_reveal(browser, page_file):
    """2026-09-27: the last card is the payoff; a tap during it changes nothing."""
    ctx, page, errors = motion_page(browser, page_file)
    stage_opens(page)
    rip(page)
    # The page's clock stops the moment the reveal begins (its first animation is still to run).
    vc_until(page, "!!document.querySelector('.pk-stage.pk-dim')", 120000)
    page.mouse.click(20, 400)
    # The clock parks every animation (a pending pause); a rate read before it settles reads 1 even when
    # the tap's updatePlaybackRate(6) landed, so wait for each to be ready first.
    rates = page.evaluate("""async () => {
      const anims = document.querySelector('.pk-stage').getAnimations({subtree: true})
        .filter(a => a.effect.getTiming().iterations !== Infinity);
      await Promise.all(anims.map(a => a.ready));
      return anims.map(a => a.playbackRate);
    }""")
    assert rates and all(r == 1 for r in rates), rates
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_taps_hurry_the_deal(browser, page_file):
    ctx, page, errors = motion_page(browser, page_file)
    stage_opens(page)
    rip(page)
    vc_until(page, "!!document.querySelector('.pk-card')")
    t0 = vc_now(page)
    while page.locator(".pk-stage").count() and vc_now(page) - t0 < 15000:
        page.mouse.click(20, 400)
        vc_run(page, 150)
    took = (vc_now(page) - t0) / 1000                           # the page's seconds, not the host's
    n = page.evaluate("packCards(TEAMS.espn).length")
    # Untouched, a stock card takes ~0.6s, a hit ~2.3s and the best one ~5.5s more.
    assert took < 1.2 * n + 3, f"{n} cards took {took:.1f}s of page time with taps"
    assert page.locator(".cards .tc.pk-slot").count() == 0
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_deal_ends_with_every_starter_face_up_and_holds_each_hit_centred(browser, page_file):
    """2026-10-05: each card rises straight to the stage's centre; a metal holds there with its label
    (centred within 2px, it was 10px off in the storyboard), and the deal ends with every starter face up
    in its slot."""
    ctx, page, errors = motion_page(browser, page_file)
    stage_opens(page)
    rip(page)
    vc_until(page, "!!document.querySelector('.pk-msg .pk-tag')", 30000)
    held = page.evaluate("""(() => { const cs = document.querySelectorAll('.pk-card'), r = cs[cs.length - 1].getBoundingClientRect();
      return [r.left + r.width / 2, document.documentElement.clientWidth / 2, document.querySelector('.pk-msg').textContent]; })()""")
    assert abs(held[0] - held[1]) <= 2, held
    assert re.search(r"(Holo|Gold|Silver)#\d+ \w+ THIS WEEK", held[2]), held[2]
    vc_until(page, "!document.querySelector('.pk-stage')", 60000)
    assert page.evaluate(DOWN) == 0 and page.locator(".cards .tc.pk-slot").count() == 0
    assert page.locator(".cards-col:not(.bench) .tc").count() == page.evaluate(STARTERS)
    assert errors == []
    ctx.close()


SIGN = """(() => { const p = TEAMS.espn.roster.find(p => p.start && p.pos === 'TE') || TEAMS.espn.roster.find(p => p.start && p.pos === 'WR');
  LIVE_SIGNED.players[p.slug] = {rank: 2, pts: 22.6}; render(); return p.pos; })()"""


@pytest.mark.render
def test_a_signed_card_holds_again_while_it_is_signed(browser, signed_file):
    """2026-10-05: the autograph is its own beat. The label names the finish and the week, the pen
    writes it with sparks, and nothing of it is left running when the stage has gone."""
    ctx, page, errors = motion_page(browser, signed_file)
    pos = page.evaluate(SIGN)
    stage_opens(page)
    rip(page)
    vc_until(page, "!!document.querySelector('.pk-msg .pk-tag.t-signed')", 30000)
    assert page.text_content(".pk-msg") == f"Signed#2 {pos} IN WEEK 3 · 22.6 PTS"
    inking = page.evaluate("""(() => { const cs = document.querySelectorAll('.pk-card'), c = cs[cs.length - 1];
      return [c.classList.contains('pk-unsigned'), c.querySelector('.sg.cool').getAnimations().length, c.querySelector('.tip').getAnimations().length]; })()""")
    assert inking[0] is False and inking[1] == 1 and inking[2] == 1, inking
    vc_until(page, "!document.querySelector('.pk-stage')", 60000)
    assert page.locator(".spk").count() == 0, "every spark has gone"
    assert errors == []
    ctx.close()


@pytest.fixture(scope="module")
def signed_file(built, page_file):
    """The page with an empty LIVE_SIGNED for week 3 (as test_roster_cards.signed_file)."""
    text, n = re.subn(r"^const LIVE_SIGNED = .*;$", 'const LIVE_SIGNED = {"wk": 3, "players": {}};', built.page, count=1, flags=re.M)
    assert n == 1
    p = page_file.parent / "signed-stage.html"
    p.write_text(text, encoding="utf-8")
    return p


@pytest.mark.render
def test_the_waiting_pack_keeps_the_starters_place_and_the_bench_shows(browser, page_file):
    """2026-10-05: on a followed team the pack stands over the starters' grid, which keeps its size with
    every card face down; Rip and Skip sit under the pack; the bench draws as always."""
    ctx, page, errors = cards_page(browser, page_file, gate=True)
    assert page.evaluate(DOWN) == page.evaluate(STARTERS) > 0
    assert page.locator(".cards-col.bench .tc").count() > 0 and page.locator(".cards-col.bench .tc.down").count() == 0
    box = lambda s: page.locator(s).bounding_box()
    # The fixture's ESPN lineup is one row; a real one is three, taller than the pack. The place is the
    # grid, grown to hold the pack and its buttons when the grid is shorter (packgate.css .pk-zone).
    zone, grid, pk, rip_, skip = (box(s) for s in (".pk-zone", ".pk-zone > .cardgrid", ".pk-gpack .pack-seal", "[data-pkrip]", "[data-pkskip]"))
    assert grid["y"] <= pk["y"] < grid["y"] + 60 and pk["y"] + pk["height"] < rip_["y"] < rip_["y"] + rip_["height"] <= zone["y"] + zone["height"]
    assert abs(pk["x"] + pk["width"] / 2 - (grid["x"] + grid["width"] / 2)) < 6, "centred over the grid"
    assert 120 <= pk["width"] <= 150 and abs(rip_["y"] - skip["y"]) < 1
    assert page.locator(".rule [data-pkopen].wait").count() == 1, "the chip waits, hidden, for a Skip"
    assert page.locator(".pk-stage").count() == 0
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_skip_turns_the_starters_face_up_and_leaves_the_chip_across_a_reload(browser, page_file):
    ctx, page, errors = cards_page(browser, page_file, gate=True)
    at = "(r => [r.left, r.top + scrollY, r.width, r.height])(document.querySelector('.cards-col:not(.bench) .cardgrid').getBoundingClientRect())"
    grid = page.evaluate(at)
    page.click("[data-pkskip]")                                # reduced motion: at once
    assert page.locator(".pk-gate").count() == 0 and page.evaluate(DOWN) == 0
    assert page.locator(".cards-col:not(.bench) .tc").count() == page.evaluate(STARTERS)
    assert page.evaluate(at) == grid, "the cards turn where they lay"
    wk = page.evaluate("schedWeek()")
    chip = page.locator(".cards .rule [data-pkopen]")
    assert chip.count() == 1 and chip.inner_text() == f"Open week {wk}" and "wait" not in chip.get_attribute("class")
    page.reload()
    page.wait_for_function("document.getElementById('view').children.length > 0")
    page.evaluate("VIEW='espn'; render()")
    assert page.locator(".pk-gate").count() == 0 and page.locator(".cards .rule [data-pkopen]").count() == 1
    page.click("[data-pkopen]")                                # the chip opens the stage directly
    page.wait_for_selector(".pk-stage .pack-seal")
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_skip_with_motion_shrinks_the_pack_into_the_chip_and_turns_the_cards_in_a_wave(browser, page_file):
    ctx, page, errors = motion_page(browser, page_file)
    page.click("[data-pkskip]")
    shrink = page.evaluate("""(() => { const a = document.querySelector('.pk-gpack').getAnimations()[0];
      return a ? +a.effect.getKeyframes()[1].scale : null; })()""")
    assert shrink is not None and shrink < .2, shrink
    vc_until(page, "!document.querySelector('.pk-gate')", 2000)
    assert page.evaluate(DOWN) == page.evaluate(STARTERS), "the cards turn after the pack has gone"
    vc_run(page, 230)
    first = page.evaluate(DOWN)
    assert 0 < page.evaluate(STARTERS) - first < page.evaluate(STARTERS), "one after another, not at once"
    vc_until(page, f"{DOWN} === 0 && !document.querySelector('.cards .tc.up')", 3000)
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_browsed_team_shows_its_roster_with_the_chip_and_sheet_never_waits(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (360, 800))
    page.evaluate("localStorage.setItem('tw-follow', JSON.stringify(['yahoo'])); navGo('roster'); VIEW='espn'; ROSTER_MODE='cards'; render()")
    assert page.locator(".pk-gate").count() == 0 and page.locator(".cards .tc.down").count() == 0
    assert page.locator(".cards .rule [data-pkopen]").count() == 1, "a team only browsed: its roster, and the chip"
    page.evaluate("VIEW='yahoo'; render()")
    assert page.locator(".pk-gate").count() == 1, "a followed team waits"
    page.click("[data-rmode='sheet']")
    assert page.locator(".pk-gate").count() == 0 and page.locator(".pk-stage").count() == 0, "Sheet never waits"
    assert page.locator(".row.start").count() > 0
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_waiting_pack_turns_by_itself_only_with_motion(browser, page_file):
    """STYLE.md motion rule 1: a slow turn as a tap cue, never under reduced motion."""
    ctx, page, errors = cards_page(browser, page_file, gate=True)
    assert page.evaluate("PK_IDLES.size") == 0, "reduced motion: it stands still"
    ctx.close()
    ctx, page, errors = motion_page(browser, page_file)
    assert page.evaluate("PK_IDLES.size") == 1
    # The turn is the page's own frame loop on the wall clock: it rests 2 s first, then turns.
    page.wait_for_function("""parseFloat((getComputedStyle(document.querySelector('.pk-gate .pack-glow')).rotate.match(/(-?[\\d.]+)deg/) || [0, 0])[1]) > 1""",
                           timeout=6000)
    assert errors == []
    ctx.close()
