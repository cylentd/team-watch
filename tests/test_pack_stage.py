"""The pack's stage and its controls, fixes of 2026-09-25: "Rip again" sits over the cards and never
moves the Sheet / Cards switch, a drag on the pack turns it and it springs back, and a tap while the
cards are dealt hurries them. The motion tests run on the page's virtual clock (test_roster_cards.VCLOCK),
so no test waits for a real animation, and "how long it took" is the page's own time."""
import pytest

from test_roster_cards import (cards_page, motion_page, rip, stage_opens, vc_install, vc_now, vc_run,
                               vc_until)


def chips(page):
    return page.evaluate("[...document.querySelectorAll('.rmode .chip')].map(b => Math.round(b.getBoundingClientRect().x))")


@pytest.mark.render
def test_rip_again_is_over_the_cards_and_the_switch_holds_still(browser, page_file):
    ctx, page, errors = cards_page(browser, page_file)
    assert page.locator(".pack").count() > 0, "the fixture's schedule has a week ahead, so a pack to open"
    page.click(".pack .pack-seal")
    rip(page)
    page.wait_for_selector(".pk-stage", state="detached")
    page.wait_for_timeout(100)
    # The page stays on the cards that just landed (2026-09-27: closing the stage threw it to the top).
    # The cards end the page, and since the footer went (2026-10-04) nothing is under them to scroll past,
    # so they may sit below the middle: on screen and scrolled down is the point.
    top = page.evaluate("document.querySelector('#view .cards').getBoundingClientRect().top")
    assert page.evaluate("scrollY") > 0 and 0 <= top < page.viewport_size["height"] * .6, top
    assert page.locator(".cards .rule [data-rerip]").count() == 1
    assert page.locator(".rmode [data-rerip]").count() == 0
    in_cards = chips(page)
    page.click("[data-rmode='sheet']")
    assert chips(page) == in_cards, "Sheet and Cards stay where they were"
    assert page.locator("[data-rerip]").count() == 0
    assert errors == []
    ctx.close()


@pytest.mark.render
@pytest.mark.parametrize("motion", [False, True])
def test_an_empty_pack_still_opens_and_says_so(browser, page_file, motion):
    """2026-09-27: a week where nobody on the roster is top 12 gets a pack with nothing in it."""
    ctx, page, errors = motion_page(browser, page_file) if motion else cards_page(browser, page_file)
    vc_install(page)                                            # a no-op on the motion page, which has it
    vc_run(page, 500)
    if page.locator(".pk-stage").count():
        page.keyboard.press("Escape")
    page.evaluate("""Object.values(LIVE_PROJECTIONS.players).forEach(r => { if (r.rank) r.rank = 40; });
      if (typeof LIVE_SIGNED !== 'undefined' && LIVE_SIGNED) LIVE_SIGNED.players = {};
      render()""")
    assert page.locator(".pack .pack-seal").count() > 0, "the fixture's schedule has a week ahead, so a pack to open"
    assert page.evaluate("packCards(TEAMS.espn).length") == 0
    page.click(".pack .pack-seal")
    rip(page)
    vc_until(page, "document.querySelector('.pk-msg')?.textContent.startsWith('Empty')", 6000)
    assert page.text_content(".pk-count").startswith("0 ")
    vc_until(page, "!document.querySelector('.pk-stage')", 6000)
    assert page.locator(".cards .rule [data-rerip]").count() == 1, "an empty pack can be ripped again too"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_packs_side_seams_are_never_clipped(browser, page_file):
    """2026-09-27: a clip-path on the pack's turned edge slices dropped the spin to 16 fps on a
    throttled CPU (53 without). The side seams are shaped by border-radius instead."""
    ctx, page, errors = cards_page(browser, page_file, keep_stage=True)
    assert page.locator(".pk-stage").count() > 0, "the fixture's schedule has a week ahead, so a pack on the stage"
    clips = page.evaluate("[...document.querySelectorAll('.pk-stage .pack-wall')].map(w => getComputedStyle(w).clipPath)")
    assert len(clips) == 2 and set(clips) == {"none"}, clips
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_drag_on_the_pack_turns_it_and_it_springs_back(browser, page_file):
    ctx, page, errors = cards_page(browser, page_file, keep_stage=True)
    assert page.locator(".pk-stage").count() > 0, "the fixture's schedule has a week ahead, so a pack on the stage"
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
    # Untouched, a card takes ~2.4s and the best one ~5.5s more.
    assert took < 1.2 * n + 3, f"{n} cards took {took:.1f}s of page time with taps"
    assert page.locator(".cards .tc.pk-slot").count() == 0
    assert errors == []
    ctx.close()
