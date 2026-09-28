"""design/digest.py: the Digest block, from ff-jarvis's weekly_digest.json."""
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "design"))
sys.path.insert(0, str(REPO / "api"))

import pytest  # noqa: E402

from _espn import slugify  # noqa: E402
import contract  # noqa: E402
from digest import kicks, live_digest, report  # noqa: E402
from sources import load_digest  # noqa: E402
from test_render import browser, go, open_page  # noqa: E402,F401  (the suite's one Chromium)


def _block(schedule=None):
    return live_digest(load_digest(), slugify, schedule)


SCHEDULE = {"alias": {"LA": "LAR", "WAS": "WSH"}, "games": [
    {"home": "DEN", "away": "LAR", "kickoff": "2026-09-28T00:20:00Z", "week": 3},
    {"home": "WSH", "away": "SEA", "kickoff": "2026-09-27T17:00:00Z", "week": 3},
    {"home": "HOU", "away": "LAR", "kickoff": "2026-10-04T17:00:00Z", "week": 4}]}


def test_kicks_answers_in_both_dialects_for_the_packets_week():
    ko = kicks(SCHEDULE, 3)
    assert ko["LA"] == ko["LAR"] == "2026-09-28T00:20:00Z"
    assert ko["WAS"] == ko["WSH"] == "2026-09-27T17:00:00Z"
    assert "HOU" not in ko and kicks(None, 3) == {}


def test_game_rows_carry_their_kickoff_for_the_browser():
    b = _block(SCHEDULE)
    assert b["hurt"][0]["game"]["ko"] == "2026-09-28T00:20:00Z"
    assert b["wx"][0]["ko"] == "2026-09-27T17:00:00Z"
    assert all(r["ko"] is None or r["ko"].endswith("Z") for r in b["best"] + b["top5"])


def test_results_cut_to_finals_stars_and_busts():
    b = _block()
    assert b["finals"] == [{"away": "MIA", "home": "BUF", "away_pts": 17.0, "home_pts": 27.0}]
    assert b["pending"] == 2
    assert [(r["pos"], r["n"], r["actual"]) for r in b["stars"]] == [("QB", "Josh Allen", 24.6), ("RB", "James Cook", 19.4)]
    assert b["busts"][0]["slug"] == slugify("De'Von Achane")
    assert b["asof_words"] == "Fri 10:40 PM"


def test_fixture_block_is_whole():
    b = _block()
    contract.validate("LIVE_DIGEST", b)
    assert b["week"] == 3 and b["lead"] == {"rule": "hurt", "index": 0}
    assert [len(b[k]) for k in ("hurt", "best", "wx", "adds", "top5", "up", "down", "gems", "news")] == \
        [12, 4, 1, 6, 20, 5, 5, 5, 10]


def test_kickoffs_are_pacific_words():
    b = _block()
    assert b["hurt"][0]["game"] == {"away": "LA", "home": "DEN", "kick": "Sun 5:20 PM",   # 00:20 UTC Monday
                                    "ko": "2026-09-28T00:20:00Z"}
    assert b["wx"][0]["kick"] == "Sun 10:00 AM"
    assert b["hurt"][4]["game"] is None                                                    # Dart, on IR


def test_best_spots_keep_position_order_and_slugs():
    b = _block()
    assert [(r["pos"], r["n"]) for r in b["best"]] == [
        ("QB", "C.J. Stroud"), ("RB", "Quinshon Judkins"), ("WR", "CeeDee Lamb"), ("TE", "Pat Freiermuth")]
    assert b["best"][2]["slug"] == slugify("CeeDee Lamb") and b["best"][2]["home"] is True


def test_headline_splits_at_its_tag_and_takes_a_news_kind():
    news = _block()["news"]
    assert news[0]["n"] == "Jaylen Wright" and news[0]["rest"] == "doubtful to play Sunday"
    assert news[0]["when"] == "8:31 AM" and news[0]["kind"] == "injury"
    assert news[7]["kind"] == "out"                         # "Josh Simmons (back) ruled out for Sunday"
    assert news[0]["slugs"][0] == "jaylen-wright"


def test_top5_flattens_by_position():
    top5 = _block()["top5"]
    assert [r["pos"] for r in top5[::5]] == ["QB", "RB", "WR", "TE"]
    assert top5[0]["n"] == "Josh Allen"


def test_empty_sections_are_empty_lists_not_errors():
    p = json.loads(json.dumps(load_digest()))
    p.update(lead=None, hurt=[], news=[], gems=[], top5={}, stock={"up": [], "down": []},
             adds={"weeks": [2, 3], "rows": []}, weather={"games": [], "near": None},
             matchups={"calls": 0, "best": {}, "record": None})
    b = live_digest(p, slugify)
    contract.validate("LIVE_DIGEST", b)
    assert b["lead"] is None and b["near"] is None and b["best"] == [] and b["record"] is None


@pytest.mark.render
def test_a_started_game_drops_its_rows_live_and_the_lead_gives_way(browser, page_file):
    """The Friday packet read on Monday morning: nothing about a Sunday game survives in the
    browser, the lead falls to the week's results, and the stamp says how old the packet is."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.goto(page_file.as_uri())
    page.evaluate('Date.now = () => Date.parse("2026-09-28T13:00:00Z")')   # after load: the page pins its own
    for _, sel in go("digest"):
        page.click(sel)
    page.wait_for_selector(".dg-row")
    assert page.locator(".dg-lead-h").inner_text() == "Josh Allen scored 24.6"
    assert page.locator(".dg-lead-when").inner_text() == "Week 3 · updated Fri 10:40 PM"
    assert page.locator(".dg-row[data-dgrow='res'][data-open]").count() == 1
    left = page.evaluate("dgD().hurt.map(r => r.game && r.game.away + '@' + r.game.home)")
    assert "LA@DEN" not in left
    # The fixture schedule holds one week-3 game, so give one top-5 row a Sunday kickoff by hand.
    n = page.evaluate("dgD().top5.length")
    page.evaluate("LIVE_DIGEST.top5.find(r => !r.ko).ko = '2026-09-27T17:00:00Z'; DG_CUT = null")
    assert page.evaluate("dgD().top5.length") == n - 1
    assert page.locator(".dg-row[data-dgrow='res'] .dg-foot").inner_text().startswith("1 game final, 2 to play.")
    assert errors == []
    ctx.close()


def test_no_packet_is_no_block():
    assert live_digest(None, slugify) is None
    contract.validate("LIVE_DIGEST", None)
    assert "no weekly_digest.json" in report(None)


@pytest.mark.render
def test_the_wall_opens_every_panel_and_a_head_is_not_a_toggle(browser, page_file):
    """From 1100px the Digest is a wall (2026-09-26): every topic open, the day's row marked, the
    lead's ghost naming why he leads. A tap on a panel's head must not close it."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    page.goto(page_file.as_uri() + "#digest")
    page.wait_for_selector(".dg-row")
    rows = page.locator(".dg-row:not(.empty)")
    assert rows.count() == page.locator(".dg-row[data-open]").count() > 0
    page.locator(".dg-row[data-dgrow='hurt'] .dg-head").click()
    assert page.locator(".dg-row[data-dgrow='hurt'][data-open]").count() == 1
    assert page.locator(".dg-ghost").inner_text() == "WR2"
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert errors == []
    ctx.close()
