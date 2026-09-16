"""The player profile: its contract, its injection, and the rendered chip and slide-over panel.

The fixture (tests/fixtures/data/player_profiles.json) holds St. Brown (WR, PLUS untested, two
zones), Kittle (TE, MINUS untested, one zone, no coverage), Chase Brown (RB, EVEN tested),
Gibbs (RB, bye) and Higgins (WR, EVEN untested, coordinator changed). Burrow and Purdy have none.
"""
import copy
import json

import pytest

import build
import contract
from conftest import FIXTURES
from test_build import injected
from test_render import browser, open_page  # noqa: F401  (browser is a fixture)

PROFILES = json.loads((FIXTURES / "data" / "player_profiles.json").read_text(encoding="utf-8"))


def test_contract_accepts_the_fixture():
    assert contract.problems("LIVE_PROFILES", PROFILES) == []


def test_contract_rejects_a_player_missing_next():
    d = copy.deepcopy(PROFILES)
    d["players"]["amonra-st-brown"].pop("next")
    assert contract.problems("LIVE_PROFILES", d) == ["LIVE_PROFILES.players['amonra-st-brown'].next"]


def test_contract_rejects_a_partial_next_but_allows_a_bye():
    d = copy.deepcopy(PROFILES)
    d["players"]["chase-brown"]["next"].pop("tested")
    assert d["players"]["jahmyr-gibbs"]["next"] is None
    assert contract.problems("LIVE_PROFILES", d) == ["LIVE_PROFILES.players['chase-brown'].next.tested"]


def test_build_injects_the_profiles(built):
    got = injected(built.fragment)["LIVE_PROFILES"]
    assert set(got["players"]) == set(PROFILES["players"])
    assert any(line.startswith("Profiles: 5 players") for line in built.report)


def test_no_profiles_file_injects_null(monkeypatch):
    monkeypatch.setattr(build, "load_profiles", lambda: None)
    b = build.render()
    assert injected(b.fragment)["LIVE_PROFILES"] is None


# ------------------------------------------------------------------ rendered, in Chromium

def row(page, name):
    return page.locator(".row", has_text=name).first


def chip(page, name):
    c = row(page, name).locator(".mchip")
    return None if c.count() == 0 else c.first


@pytest.mark.render
def test_chip_text_per_verdict_and_untested_mark(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    want = {"Amon-Ra St. Brown": ("PLUS", True), "Chase Brown": ("EVEN", False)}
    for name, (word, untested) in want.items():
        c = chip(page, name)
        assert c is not None, name
        assert c.inner_text().strip() == word
        assert ("untested" in c.get_attribute("class")) is untested
        assert (c.locator(".flask").count() == 1) is untested
    assert chip(page, "Jahmyr Gibbs") is None          # bye: next is null
    assert chip(page, "Joe Burrow") is None            # no profile at all
    page.evaluate("VIEW='espn'; render()")
    assert chip(page, "George Kittle").inner_text().strip() == "MINUS"
    assert chip(page, "Tee Higgins").inner_text().strip() == "EVEN"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_panel_untested_tag_iff_not_tested(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    drawer = page.locator("#drawer")
    row(page, "Amon-Ra St. Brown").click()
    assert drawer.locator(".pf-untested").count() == 1
    assert "on paper" in drawer.locator(".pf-verdict").inner_text()
    assert drawer.locator(".pf-untested").get_attribute("title") == PROFILES["players"]["amonra-st-brown"]["next"]["method"]
    assert drawer.locator(".pf-sec").count() == 4
    page.keyboard.press("Escape")
    assert "on" not in drawer.get_attribute("class")
    assert page.evaluate("document.activeElement.classList.contains('row')")
    row(page, "Chase Brown").click()
    assert drawer.locator(".pf-untested").count() == 0
    assert "on paper" not in drawer.inner_text()
    assert PROFILES["players"]["chase-brown"]["next"]["method"] in drawer.inner_text()
    page.keyboard.press("Escape")
    row(page, "Jahmyr Gibbs").click()
    assert drawer.locator(".pf-v").count() == 0
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_no_profiles_renders_no_chips_and_a_quiet_panel(browser, monkeypatch, tmp_path):
    monkeypatch.setattr(build, "load_profiles", lambda: None)
    p = tmp_path / "index.html"
    p.write_text(build.render().page, encoding="utf-8")
    ctx, page, errors = open_page(browser, p, (390, 844))
    assert page.locator(".mchip").count() == 0
    row(page, "Amon-Ra St. Brown").click()
    assert page.locator("#drawer .pf-empty").count() == 1
    assert page.locator("#drawer .pf-sec").count() == 0
    assert errors == []
    ctx.close()
