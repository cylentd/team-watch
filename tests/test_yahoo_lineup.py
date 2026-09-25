"""The Yahoo lineup comes from the scrape's own slots, never from a guess.

Until 2026-09-25 build.py dropped the slot the scrape carries and hydrate.js inferred a lineup of
QB, 2 RB, 3 WR, TE and a flex: 8 starters, the K and DST on the bench, and the flex handed to
whoever came first in roster order. The league starts 9: QB, 2 RB, 2 WR, TE, W/R/T, K, DEF.
"""
import json

import pytest

import build
from test_render import browser, open_page  # noqa: F401  (browser is a fixture)

# The shape of ff-jarvis's league_rosters.json, one row per Yahoo slot the league uses.
ROWS = [
    ("QB One", "QB", "QB"), ("RB One", "RB", "RB"), ("RB Two", "RB", "RB"),
    ("WR One", "WR", "WR"), ("WR Two", "WR", "WR"), ("TE One", "TE", "TE"),
    ("Flex Guy", "WR", "W/R/T"), ("Kicker Guy", "K", "K"), ("Bengals", "DEF", "DEF"),
    ("Bench Tight End", "TE", "BN"),
]


@pytest.fixture
def slotted(tmp_path, monkeypatch):
    detail = [{"id": str(i), "name": n, "team": "CIN", "pos": pos, "slot": slot}
              for i, (n, pos, slot) in enumerate(ROWS)]
    f = tmp_path / "league_rosters.json"
    f.write_text(json.dumps({"me": "Mine", "league": "L", "league_id": "1", "updated": "2026-09-25",
                             "detail": {"Mine": detail}}), encoding="utf-8")
    monkeypatch.setattr(build, "YAHOO_ROSTERS", f)


def test_the_scrape_slot_is_passed_through_in_the_page_names(slotted):
    slots = [r["slot"] for r in build.live_yahoo(set())["roster"]]
    assert slots == ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DST", "BN"]


@pytest.mark.render
def test_the_roster_starts_the_nine_yahoo_started(browser, slotted, tmp_path):
    p = tmp_path / "index.html"
    p.write_text(build.render().page, encoding="utf-8")
    ctx, page, errors = open_page(browser, p, (390, 844))
    rows = page.evaluate("TEAMS.yahoo.roster.map(r => [r.n, r.slot, r.start])")
    starters = [n for n, _, start in rows if start]
    assert len(starters) == 9
    assert {"Kicker Guy", "Bengals", "Flex Guy"} <= set(starters)
    assert ["Bench Tight End", "BN", False] in rows
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_scrape_without_slots_still_infers_a_lineup(browser, page_file):
    """The fixture's rows carry no slot: the fallback fills QB, 2 RB, 2 WR, TE, flex, K, DST."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    rows = page.evaluate("TEAMS.yahoo.roster.map(r => [r.pos, r.slot, r.start])")
    assert rows and all(start for _, _, start in rows)
    assert errors == []
    ctx.close()
