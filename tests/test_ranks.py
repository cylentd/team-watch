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


def test_one_week_only_and_the_teams_left_off_are_named():
    """ATL played Thursday, so the file's number for Bijan Robinson is already week 4's
    (2026-09-26). He must not lead week 3's list, and the list must say why ATL is missing."""
    raw = {"scoring": "half-PPR", "players": [
        {"name": "Bijan Robinson", "pos": "RB", "team": "ATL", "opp": "NO", "game": "ATL @ NO",
         "kickoff": "2026-10-06 00:15:00", "pts": 19.7, "injury": None, "mu": {"RUSH": 97.5, "TD": .8}},
        {"name": "Jahmyr Gibbs", "pos": "RB", "team": "DET", "opp": "NYJ", "game": "NYJ @ DET",
         "kickoff": "2026-09-27 17:00:00", "pts": 18.8, "injury": "Questionable", "mu": {"RUSH": 76, "REC": 41, "RECS": 4.5, "TD": .8}},
        {"name": "Derrick Henry", "pos": "RB", "team": "BAL", "opp": "DAL", "game": "BAL @ DAL",
         "kickoff": "2026-09-27 20:25:00", "pts": 17.9, "injury": None, "mu": None},
    ]}
    schedule = {"games": [
        {"week": 4, "away": "ATL", "home": "NO", "kickoff": "2026-10-06T00:15:00Z"},
        {"week": 3, "away": "NYJ", "home": "DET", "kickoff": "2026-09-27T17:00:00Z"},
        {"week": 3, "away": "BAL", "home": "DAL", "kickoff": "2026-09-27T20:25:00Z"},
    ]}
    r = live_ranks(raw, slug, None, schedule)
    assert r["week"] == 3 and r["off"] == ["ATL"]
    assert [(x["slug"], x["rank"]) for x in r["rows"]] == [("jahmyr-gibbs", 1), ("derrick-henry", 2)]
    gibbs = r["rows"][0]
    assert gibbs["kick"] == "2026-09-27T17:00:00Z" and gibbs["inj"] == "Q"
    assert gibbs["mu"] == {"RUSH": 76, "REC": 41, "RECS": 4.5, "TD": .8}


def test_the_cards_take_the_same_week_cut():
    """The roster cards read LIVE_PROJECTIONS, and a Thursday team's row is next week's there too:
    no points, no rank, and `done` says whether his team played or has a bye."""
    from projections import live_projections
    raw = {"scoring": "half-PPR", "players": [
        {"name": "Bijan Robinson", "pos": "RB", "team": "ATL", "kickoff": "2026-10-06 00:15:00", "pts": 19.7, "src": "model"},
        {"name": "Bye Back", "pos": "RB", "team": "SEA", "kickoff": "2026-10-04 17:00:00", "pts": 18.0, "src": "model"},
        {"name": "Jahmyr Gibbs", "pos": "RB", "team": "DET", "kickoff": "2026-09-27 17:00:00", "pts": 18.8, "src": "model"},
    ]}
    schedule = {"games": [
        {"week": 3, "away": "ATL", "home": "GB", "kickoff": "2026-09-25T00:15:00Z"},
        {"week": 3, "away": "NYJ", "home": "DET", "kickoff": "2026-09-27T17:00:00Z"},
        {"week": 4, "away": "ATL", "home": "NO", "kickoff": "2026-10-06T00:15:00Z"},
        {"week": 4, "away": "SEA", "home": "LAR", "kickoff": "2026-10-04T17:00:00Z"},
    ]}
    wanted = {"bijan-robinson", "bye-back", "jahmyr-gibbs"}
    # Gibbs alone is in week 3 here, so weigh the vote with two more DET rows the cut ignores.
    raw["players"] += [{"name": f"Det {i}", "pos": "WR", "team": "DET", "kickoff": "2026-09-27 17:00:00", "pts": 5.0} for i in range(2)]
    p = live_projections(raw, slug, wanted, None, schedule)["players"]
    assert (p["bijan-robinson"]["done"], p["bijan-robinson"]["pts"], p["bijan-robinson"]["rank"]) == ("played", None, None)
    assert p["bye-back"]["done"] == "bye"
    assert (p["jahmyr-gibbs"]["done"], p["jahmyr-gibbs"]["rank"]) == (None, 1)


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
        tiers = page.evaluate("[...document.querySelectorAll('.rk-tier b')].map(e => e.textContent.trim())")
        assert tiers and tiers[0].upper() == "TIER 1"
        # Only the reader's own players are his: a leaguemate's roster is not (2026-09-26, when
        # the leaguemate rosters landed every rostered player read MINE).
        mine = page.evaluate("[...document.querySelectorAll('.rk-row.mine')].map(e => e.dataset.rkopen)")
        own = page.evaluate("[...new Set(Object.values(TEAMS).filter(t => !t.mate).flatMap(t => t.roster.map(p => p.slug)))]")
        assert set(mine) <= set(own), set(mine) - set(own)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.locator("[data-rkpos='FLEX']").click()
        assert page.locator(".rk-pos").count() > 0, "FLEX rows say the position and its rank"
        page.locator(".rk-row").first.click()
        page.wait_for_selector("#modal.on")
        assert errors == []
    finally:
        ctx.close()
