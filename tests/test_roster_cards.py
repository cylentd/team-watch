"""The roster's Cards view (2026-09-25): the tier is this week's rank at the position, K and DST are
support cards with no tier, the Sheet / Cards choice survives a reload, and the week's pack opens
once. The ranks and the implied points are computed at build time; the rest renders."""
import pytest

from lines import live_lines
from projections import position_ranks
from test_render import browser, drive, go, open_page  # noqa: F401  (browser is a fixture)


def slug(n):
    return n.lower().replace(" ", "-")


def test_rank_is_within_the_position_over_everyone_projected():
    players = [{"name": "A One", "pos": "RB", "pts": 20}, {"name": "B Two", "pos": "RB", "pts": 12},
               {"name": "C Three", "pos": "WR", "pts": 15}, {"name": "D Four", "pos": "RB", "pts": None},
               {"name": "B Two", "pos": "RB", "pts": 9}]          # a duplicate keeps his best number
    r = position_ranks(players, slug)
    assert r["a-one"] == (1, 2) and r["b-two"] == (2, 2) and r["c-three"] == (1, 1)
    assert "d-four" not in r


def test_implied_points_split_the_total_by_the_spread():
    pool = {"games": {"BAL@DAL": {"odds": {"overUnder": 52.5, "homeSpread": 3.5, "awaySpread": -3.5}},
                      "LA@SF": {"odds": {"overUnder": 44.0, "homeSpread": -2.0, "awaySpread": 2.0}},
                      "X@Y": {"odds": {"overUnder": None}}}}
    t = live_lines(pool, {"LA": "LAR"})["teams"]
    assert t["BAL"] == {"implied": 28.0, "opp": "DAL", "spread": -3.5, "total": 52.5}
    assert t["DAL"]["implied"] == 24.5
    assert t["LAR"]["opp"] == "SF" and t["SF"]["implied"] == 23.0
    assert "X" not in t
    assert live_lines({"games": {}}, {}) is None


def cards_page(browser, page_file, viewport=(360, 660)):
    ctx, page, errors = open_page(browser, page_file, viewport)
    drive(page, go("roster"))
    page.evaluate("VIEW='espn'; render()")
    page.click("[data-rmode='cards']")
    return ctx, page, errors


@pytest.mark.render
def test_cards_draw_every_player_and_the_choice_survives_a_reload(browser, page_file):
    ctx, page, errors = cards_page(browser, page_file)
    n = page.evaluate("TEAMS.espn.roster.length")
    assert page.locator(".cards .tc").count() == n
    support = page.evaluate("TEAMS.espn.roster.filter(p => p.pos === 'K' || p.pos === 'DST').length")
    assert page.locator(".cards .tc.tier-k, .cards .tc.tier-dst").count() == support
    page.reload()
    page.wait_for_function("document.getElementById('view').children.length > 0")
    drive(page, go("roster"))
    assert page.evaluate("ROSTER_MODE") == "cards"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_tier_is_the_rank_and_support_cards_have_none(browser, page_file):
    ctx, page, errors = cards_page(browser, page_file)
    tiers = page.evaluate("[1,2,3,4,12,13,24,25,null].map(cardTier)")
    assert tiers == ["sig", "sr", "sr", "ur", "ur", "r", "r", "c", "c"]
    # A support card, drawn directly: no rank line, no foil, whatever the fixture's roster holds.
    page.evaluate("""document.querySelector('.cards .cardgrid').insertAdjacentHTML('beforeend',
      cardHTML({n:'Bengals', pos:'DST', team:'CIN', slot:'DST', start:true, slug:null}, 0, 'espn'))""")
    dst = page.locator(".cards .tc.tier-dst").last
    assert dst.locator(".tc-foot").count() == 0 and dst.locator(".tc-spark, .tc-etch").count() == 0
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_tap_flips_the_card_and_its_back_opens_the_profile(browser, page_file):
    ctx, page, errors = cards_page(browser, page_file)
    card = page.locator(".cards .tc").first
    card.click()
    assert "back" in card.get_attribute("class")
    card.locator(".bk-open").click()
    assert page.locator("#modal").is_visible()
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_pack_opens_once_a_week(browser, page_file):
    ctx, page, errors = cards_page(browser, page_file)
    if page.locator(".pack").count() == 0:
        pytest.skip("the fixture's schedule has no week ahead, so no pack to open")
    page.click(".pack-seal")                                   # reduced motion: the end at once
    page.wait_for_selector(".pack-done")
    assert page.locator(".pack-grid .tc.pk-down").count() == 0
    page.click(".pack-done")
    assert page.locator(".pack").count() == 0
    assert errors == []
    ctx.close()
