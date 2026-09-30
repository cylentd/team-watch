"""The third league, AYO (2026-09-29, David: "Everything"): a second Yahoo league through every view.

design/leagues.py is the page's league list, held here to ff-jarvis's model/common/registry.py. The
fixture's AYO files (tests/fixtures/data/ayo_*) mirror the first Yahoo league's shape with their own
teams: Taylor Made for Sundays holds Chase Brown (on all three of David's teams), Jahmyr Gibbs (Yahoo
too), Tee Higgins and Brock Purdy (ESPN too) and Justin Jefferson (AYO only). It has no past seasons,
owners, managers or trade verdicts, as AYO had none when it landed.
"""
import importlib.util
import json
import shutil

import pytest

import build
import contract
import leagues
import sources
from conftest import FIXTURES, REPO
from league_recap import live_league_yahoo
from test_render import browser, drive, go, open_page  # noqa: F401  (browser is a fixture)

def read(name):
    return json.loads((FIXTURES / "data" / name).read_text(encoding="utf-8"))


def injected(fragment, name):
    import re
    m = re.search(rf"^const {name} = (.*);$", fragment, re.M)
    assert m, f"{name} not injected"
    return json.loads(m.group(1).replace("<\\/", "</"))


# ---------------------------------------------------------------- the list, held to ff-jarvis's

def test_the_league_list_is_ff_jarvis_own():
    """One list in two repos: ff-jarvis's registry is the source, this test holds the page's copy to it."""
    reg = next((p / "ff-jarvis" / "model" / "common" / "registry.py" for p in REPO.parents
                if (p / "ff-jarvis" / "model" / "common" / "registry.py").exists()), None)
    if reg is None:
        pytest.skip("ff-jarvis (with its league registry) is not checked out beside team-watch")
    spec = importlib.util.spec_from_file_location("ffj_registry", reg)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert [(lg.key, lg.platform, lg.label) for lg in mod.LEAGUES] == [tuple(lg) for lg in leagues.LEAGUES]
    assert mod.LEGACY == leagues.LEGACY
    kinds = {k for v in mod.LEGACY.values() for k in v} | {"waivers", "league_box", "case_rosters"}
    assert all(mod.file(k, kind) == leagues.file(k, kind) for k in leagues.KEYS for kind in kinds)


def test_each_yahoo_league_names_its_blocks_and_files():
    assert leagues.YAHOO == ("yahoo", "ayo")
    assert leagues.blocks("yahoo") == ("LIVE_YAHOO", "LIVE_LEAGUE_YAHOO", "LIVE_TRADES")
    assert leagues.blocks("ayo") == ("LIVE_AYO", "LIVE_LEAGUE_AYO", "LIVE_TRADES_AYO")
    assert leagues.file("ayo", "rosters") == "ayo_rosters.json" and leagues.file("yahoo", "rosters") == "league_rosters.json"
    assert leagues.private_file("yahoo").name == "league_private.json"
    assert not leagues.private_file("ayo").exists(), "AYO has no private pairs yet"


# ---------------------------------------------------------------- (f) the contract covers the new blocks

def test_the_contract_checks_the_new_blocks():
    for a, b in zip(leagues.blocks("yahoo"), leagues.blocks("ayo")):
        assert contract.CONTRACT[b] is contract.CONTRACT[a]
    row = {"n": "A", "pos": "RB", "team": "PIT", "slot": "RB", "slug": None}
    assert contract.problems("LIVE_AYO", {"name": "T", "league": "L", "updated": "d", "roster": [row]}) == []
    assert contract.problems("LIVE_AYO", {"name": "T", "league": "L", "updated": "d",
                                          "roster": [{k: v for k, v in row.items() if k != "slot"}]}) == ["LIVE_AYO.roster[0].slot"]
    with pytest.raises(contract.ContractError, match="LIVE_AYO is missing LIVE_AYO.updated"):
        contract.validate("LIVE_AYO", {"name": "T", "league": "L", "roster": []})
    lg = live_league_yahoo(read("ayo_league.json"), None, None, read("ayo_rosters.json"), lambda s: s, key="ayo")
    contract.validate("LIVE_LEAGUE_AYO", lg)
    del lg["history"]
    assert contract.problems("LIVE_LEAGUE_AYO", lg) == ["LIVE_LEAGUE_AYO.history"]


# ---------------------------------------------------------------- the build

def test_the_build_carries_ayo_from_its_own_files(built):
    ayo = injected(built.fragment, "LIVE_AYO")
    assert (ayo["name"], ayo["league"]) == ("Taylor Made for Sundays", "AYO Fantasy Football")
    assert [p["n"] for p in ayo["roster"]] == ["Brock Purdy", "Jahmyr Gibbs", "Chase Brown", "Tee Higgins", "Justin Jefferson"]
    lg = injected(built.fragment, "LIVE_LEAGUE_AYO")
    keys = {t["name"]: t["key"] for t in lg["teams"]}
    assert keys["Taylor Made for Sundays"] == "ayo" and keys["Don Wick"] == "ayo-don-wick"
    assert lg["history"] is False and lg["weeks"][-1]["head"] == "TAYLOR MADE STAYS PERFECT"
    assert injected(built.fragment, "LIVE_TRADES_AYO") is None, "no verdicts file, no block: never invented"
    assert injected(built.fragment, "LIVE_LEAGUE_YAHOO")["history"] is True
    mates = [t["key"] for t in injected(built.fragment, "LIVE_MATES")["teams"]]
    assert "ayo-don-wick" in mates
    assert injected(built.fragment, "LIVE_FEED")["fetched"]["ayo"] == "2026-09-10"


def test_ayo_is_scored_by_its_own_kicking_rules(built):
    """AYO's kicking differs from the first league's (ff-jarvis, 2026-09-29): 3/3/3/4/5 by distance, no
    miss penalty, no field-goal yards. Read off ayo_settings.json's rows, never typed here."""
    gd = {lg["key"]: lg for lg in injected(built.fragment, "LIVE_GAMEDAY")["leagues"]}
    assert set(gd) == {"espn", "yahoo", "ayo"}
    rules = gd["ayo"]["rules"]
    kick = {t["s"][0]: t["p"] for t in rules["off"] if t["s"][0].startswith("fg") or t["s"][0].startswith("xp")}
    assert kick == {"fgm_0_19": 3.0, "fgm_20_29": 3.0, "fgm_30_39": 3.0, "fgm_40_49": 4.0, "fgm_50p": 5.0, "xpm": 1.0}
    assert rules["unknown"] == []
    assert gd["ayo"]["me"] == "12" and gd["ayo"]["games"] == [["4", "12"], ["6", "2"]]


def test_podiums_alone_make_a_record_book(built):
    """AYO's history arrived as podiums only (2016-2025, no games, no owners): champions under the name
    each won with, head to head this season, and `history` true, so Records draws, not the empty state."""
    hist = {"seasons": {"2025": {"podium": [{"id": 12, "name": "RUN CMC"}, {"id": 3, "name": "B"}, {"id": 11, "name": "C"}]},
                        "2024": {"podium": [{"id": 3, "name": "Team Smith"}, {"id": 8, "name": "B"}, {"id": 10, "name": "C"}]}}}
    b = live_league_yahoo(read("ayo_league.json"), hist, None, read("ayo_rosters.json"), lambda s: s, key="ayo")
    contract.validate("LIVE_LEAGUE_AYO", b)
    assert b["history"] is True and b["since"] == 2024
    assert [(c["y"], c["id"], c["name"]) for c in b["champs"]] == [(2025, None, "RUN CMC"), (2024, None, None)]
    assert b["spoons"] == []


def build_without_ayo(tmp_path, monkeypatch):
    """The fixture page built from a data dir with no ayo_* file, written beside its heads; its path."""
    data = tmp_path / "data"
    shutil.copytree(FIXTURES / "data", data, ignore=shutil.ignore_patterns("ayo_*"))
    monkeypatch.setattr(sources, "DWR", data)
    b = build.render()
    page = tmp_path / "index.html"
    page.write_text(b.page, encoding="utf-8")
    build.write_heads(tmp_path)
    return b, page


def test_the_build_without_ayo_files_leaves_ayo_out(tmp_path, monkeypatch):
    """Tonight's real data dir had no ayo_* files when this landed: the build must not fail on it."""
    b, _ = build_without_ayo(tmp_path, monkeypatch)
    for name in leagues.blocks("ayo"):
        assert injected(b.fragment, name) is None
    assert not any(t["league"] == "ayo" for t in injected(b.fragment, "LIVE_MATES")["teams"])
    assert [lg["key"] for lg in injected(b.fragment, "LIVE_GAMEDAY")["leagues"]] == ["espn", "yahoo"]


# ---------------------------------------------------------------- the page

@pytest.mark.render
def test_the_team_switch_lists_three_teams_and_opens_ayo(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    drive(page, go("roster"))
    page.click("[data-tsbtn]")
    shown = page.evaluate("[...document.querySelectorAll('.ts-menu .ts-item[data-k]')].map(b => b.dataset.k)")
    assert shown == ["yahoo", "espn", "ayo"]
    page.click(".ts-item[data-k='ayo']")
    assert page.evaluate("VIEW") == "ayo"
    assert page.locator(".ts-team").text_content() == "Taylor Made for Sundays"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_ayo_roster_waivers_and_my_recap_draw(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.evaluate("VIEW = 'ayo'; myTeamSave('ayo')")
    drive(page, go("roster"))
    names = page.evaluate("[...document.querySelectorAll('#view .row')].map(r => r.textContent)")
    assert len(names) == 5 and any("Justin Jefferson" in n or "J. Jefferson" in n for n in names)
    assert page.evaluate("[...document.querySelectorAll('#subnav [data-leaf]')].map(b => b.dataset.leaf)") == \
        ["roster", "waivers", "myrecap"], "a Yahoo league's tabs: My recap, not League"
    drive(page, [("click", "[data-leaf='waivers']")])
    assert "Jaylen Warren" in page.locator("#view").text_content(), "AYO's own wire"
    drive(page, [("click", "[data-leaf='myrecap']")])
    assert "Don Wick" in page.locator("#view").text_content(), "week 2's game against Don Wick"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_league_switch_changes_recap_and_a_reload_keeps_it(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    drive(page, go("recap"))
    chips = page.locator(".lg-switch [data-lgpick]")
    assert chips.count() == 2 and chips.nth(0).text_content() == "Madden Curse" and chips.nth(1).text_content() == "AYO"
    assert page.get_attribute("[data-lgpick='yahoo']", "aria-pressed") == "true", "the Madden Curse by default"
    assert "The Madden Curse" in page.locator(".bp-kick").text_content()
    drive(page, [("click", "[data-lgpick='ayo']")])
    assert "AYO Fantasy Football" in page.locator(".bp-kick").text_content()
    assert "Don Wick" in page.locator("#view").text_content()
    assert page.evaluate("getComputedStyle(document.querySelector('.bp-mast')).borderTopColor") == "rgb(31, 200, 224)"
    page.reload()
    page.wait_for_function("document.getElementById('view').children.length > 0")
    drive(page, go("recap"))
    assert page.get_attribute("[data-lgpick='ayo']", "aria-pressed") == "true", "the pick survives a reload"
    drive(page, [("click", "[data-lgpick='yahoo']")])
    assert "The Madden Curse" in page.locator(".bp-kick").text_content()
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_records_and_trades_for_ayo_say_there_is_no_history_yet(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.evaluate("lgLeagueSave('ayo')")
    drive(page, go("records"))
    assert page.locator(".rc-empty").count() == 1 and page.locator(".rc-hh").count() == 0
    assert page.locator(".lg-switch").count() == 1, "the switch stays, so the reader can go back"
    drive(page, go("trades"))
    assert page.locator(".tr-none").text_content().startswith("No trade history for this league yet")
    assert page.locator(".tr-rank").count() == 0
    drive(page, [("click", "[data-lgpick='yahoo']")])
    assert page.locator(".tr-rank").count() == 1, "the Madden Curse's trades, on the same tab"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_one_yahoo_league_draws_no_switch(browser, tmp_path, monkeypatch):
    _, path = build_without_ayo(tmp_path, monkeypatch)
    ctx, page, errors = open_page(browser, path, (390, 844))
    assert page.evaluate("'ayo' in TEAMS") is False
    for leaf in ("recap", "records", "trades"):
        drive(page, go(leaf))
        assert page.locator(".lg-switch").count() == 0, leaf
    page.evaluate("lgLeagueSave('ayo')")   # a pick from a page that had AYO
    drive(page, go("recap"))
    assert "The Madden Curse" in page.locator(".bp-kick").text_content(), "falls back to the league there is"
    drive(page, go("roster"))
    page.click("[data-tsbtn]")
    assert page.evaluate("[...document.querySelectorAll('.ts-menu .ts-item[data-k]')].map(b => b.dataset.k)") == ["yahoo", "espn"]
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_more_than_one_of_my_teams_is_counted_across_three(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    dual = page.evaluate("Object.fromEntries(TEAMS.ayo.roster.map(p => [p.n, p.dual || 0]))")
    assert dual == {"Brock Purdy": 2, "Jahmyr Gibbs": 2, "Chase Brown": 3, "Tee Higgins": 2, "Justin Jefferson": 0}
    assert page.evaluate("TEAMS.yahoo.roster.find(p => p.n === 'Joe Burrow').dual || 0") == 0
    assert page.evaluate("TEAMS.espn.roster.find(p => p.n === 'Chase Brown').dual") == 3
    # Anywhere a player shows which of my leagues rosters him, AYO is one of them.
    assert "AYO" in page.evaluate("ownersHTML({n: 'Justin Jefferson', slug: 'justin-jefferson'})")
    leagues_of = page.evaluate("searchIndex().find(e => e.n === 'Chase Brown').leagues")
    assert sorted(leagues_of) == ["ayo", "espn", "yahoo"]
    props = page.evaluate("PROPS.filter(p => p.n === 'Chase Brown').map(p => p.leagues)")
    assert props and all(sorted(x) == ["ayo", "espn", "yahoo"] for x in props)
    assert errors == []
    ctx.close()
