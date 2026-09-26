"""Players > Ranks (design/ranks.py, 2026-09-26): the tiers are natural breaks, the rank is the
roster card's, and the view draws each tier with its rows."""
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "design"))
from ranks import live_ranks, natural_breaks  # noqa: E402
from test_render import browser, SEED  # noqa: E402,F401  (the suite's one Chromium and its pinned clock)


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def test_breaks_fall_at_the_widest_drops():
    # Three clear groups: the tier lines must land between them, not at a round count.
    pts = [20.0, 19.8, 15.1, 15.0, 14.9, 9.0, 8.8, 8.7]
    assert natural_breaks(pts, 3) == [1, 1, 2, 2, 2, 3, 3, 3]


def test_breaks_never_ask_for_more_tiers_than_players():
    assert natural_breaks([10.0, 9.0], 8) == [1, 2]
    assert natural_breaks([], 4) == []


def test_week3_shaped_wr_list_is_not_one_giant_tier():
    """The plain gap rule this replaced gave WR tiers of 1, 2, 1, 1, 2 and 41 on week 3: sparse at
    the top, dense below. Natural breaks must spread a long dense tail over several tiers."""
    pts = [17.6, 16.6, 16.5, 15.9, 15.0] + [14.0 - i * 0.1 for i in range(43)]
    tiers = natural_breaks(pts, 9)
    sizes = [tiers.count(t) for t in range(1, 10)]
    assert max(sizes) < 20, sizes


def test_rows_carry_the_card_rank_and_skip_the_out():
    raw = {"scoring": "half-PPR", "through": "2026 wk3", "players": [
        {"name": "A Back", "pos": "RB", "team": "ATL", "opp": "NO", "game": "ATL @ NO", "pts": 19.7},
        {"name": "B Back", "pos": "RB", "team": "DET", "opp": "NYJ", "game": "NYJ @ DET", "pts": 18.8},
        {"name": "Out Back", "pos": "RB", "team": "GB", "opp": "TB", "game": "GB @ TB", "pts": 18.0},
        {"name": "A Wideout", "pos": "WR", "team": "SEA", "opp": "LAR", "game": "SEA @ LAR", "pts": 17.6},
    ]}
    status = {"x": {"name": "Out Back", "injury": "Out"}}
    r = live_ranks(raw, slug, status)
    rbs = [x for x in r["rows"] if x["pos"] == "RB"]
    assert [x["slug"] for x in rbs] == ["a-back", "b-back"], "a player out this week is left off"
    assert [x["rank"] for x in rbs] == [1, 2]
    assert rbs[0]["home"] is False and rbs[1]["home"] is True, "home is read from the game string"
    assert [x["slug"] for x in r["flex"]] == ["a-back", "b-back", "a-wideout"]
    assert r["flex"][2]["rank"] == 1, "a FLEX row keeps its position rank"


def test_no_projections_is_no_block():
    assert live_ranks({}, slug) is None


@pytest.mark.render
def test_ranks_draws_tiers_and_opens_a_profile(browser, page_file):
    ctx = browser.new_context(viewport={"width": 360, "height": 740}, reduced_motion="reduce")
    page = ctx.new_page()
    page.set_default_timeout(5000)
    page.route(re.compile(r"^https?://"), lambda route: route.abort())
    page.add_init_script(SEED)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    try:
        page.goto(page_file.as_uri() + "#ranks")
        page.wait_for_function("document.querySelectorAll('.rk-row').length > 0")
        tiers = page.evaluate("[...document.querySelectorAll('.rk-tier')].map(e => e.textContent.trim())")
        assert tiers and tiers[0].upper() == "TIER 1"
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.locator("[data-rkpos='FLEX']").click()
        assert page.locator(".rk-pos").count() > 0, "FLEX rows say the position and its rank"
        page.locator(".rk-row").first.click()
        page.wait_for_selector("#modal.on")
        assert errors == []
    finally:
        ctx.close()
