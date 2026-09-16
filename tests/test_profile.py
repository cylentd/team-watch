"""The player profile: its contract, its injection, the roster's MATCHUP column and the slide-over.

The fixture (tests/fixtures/data/player_profiles.json) spreads the matchup rank (factor rank 1 =
toughest, so "Nth easiest" = 33 - rank): Higgins 8th easiest (green), St. Brown 9th (plain),
Chase Brown 17th (plain), Kittle 25th (red), Gibbs on a bye. Burrow and Purdy have no profile.
Red zone: Kittle 3 of 8 team targets (counts, under 10), St. Brown 31% · 4 of 13 (share).
"""
import copy
import json
import re

import pytest

import build
import contract
from conftest import FIXTURES
from test_build import injected
from test_render import browser, open_page  # noqa: F401  (browser is a fixture)

PROFILES = json.loads((FIXTURES / "data" / "player_profiles.json").read_text(encoding="utf-8"))
MARKET_STOCK = json.loads((FIXTURES / "data" / "market_stock.json").read_text(encoding="utf-8"))


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


def test_contract_rejects_a_red_zone_without_team_counts():
    d = copy.deepcopy(PROFILES)
    d["players"]["george-kittle"]["red_zone"].pop("team_targets")
    d["players"]["chase-brown"]["red_zone"].pop("team_carries")
    assert contract.problems("LIVE_PROFILES", d) == [
        "LIVE_PROFILES.players['george-kittle'].red_zone.team_targets",
        "LIVE_PROFILES.players['chase-brown'].red_zone.team_carries",
    ]


def test_build_injects_the_profiles(built):
    got = injected(built.fragment)["LIVE_PROFILES"]
    assert set(got["players"]) == set(PROFILES["players"])
    assert any(line.startswith("Profiles: 5 players") for line in built.report)


def test_no_profiles_file_injects_null(monkeypatch):
    monkeypatch.setattr(build, "load_profiles", lambda: None)
    b = build.render()
    assert injected(b.fragment)["LIVE_PROFILES"] is None


# ------------------------------------------------------------------ market.stock (step 5)

def test_contract_accepts_the_market_stock_fixture():
    assert contract.problems("LIVE_MARKET_STOCK", MARKET_STOCK) == []


def test_contract_rejects_a_market_row_missing_a_field():
    d = copy.deepcopy(MARKET_STOCK)
    d["players"]["george kittle"].pop("d_rank")
    assert contract.problems("LIVE_MARKET_STOCK", d) == ["LIVE_MARKET_STOCK.players['george kittle'].d_rank"]


def test_build_injects_the_market_stock_from_the_feed(built):
    """build.py re-keys the producer's norm_name-keyed players by slug (profileFor()'s key), so
    the injected keys are slugs of the fixture's names, not the fixture's own keys."""
    got = injected(built.fragment)["LIVE_MARKET_STOCK"]
    assert got["backtested"] is False
    want = {build.slugify(rec["name"]) for rec in MARKET_STOCK["players"].values()}
    assert set(got["players"]) == want
    assert any(line.startswith("Market stock: 4 players") for line in built.report)


def test_no_market_stock_injects_null(monkeypatch):
    monkeypatch.setattr(build, "load_market_stock", lambda: None)
    b = build.render()
    assert injected(b.fragment)["LIVE_MARKET_STOCK"] is None


# ------------------------------------------------------------------ rendered, in Chromium

def row(page, name):
    return page.locator(".row", has_text=name).first


def cell(page, name):
    return row(page, name).locator(".match")


@pytest.mark.render
def test_ordinal_and_colour_class(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    got = page.evaluate("""() => ({
      nth: ordinal(easiestRank({rank: 24, of: 32})),
      suffixes: [1, 2, 3, 4, 11, 12, 13, 21, 22, 23].map(ordinal),
      cls: [8, 9, 24, 25].map(n => matchupClass(n, 32)),
    })""")
    assert got["nth"] == "9th"
    assert got["suffixes"] == ["1st", "2nd", "3rd", "4th", "11th", "12th", "13th", "21st", "22nd", "23rd"]
    assert got["cls"] == ["mu-easy", "", "", "mu-hard"]
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_matchup_column_rows(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    assert re.sub(r"\s+", " ", cell(page, "Amon-Ra St. Brown").inner_text()).strip() == "@ KC 9th"
    assert cell(page, "Amon-Ra St. Brown").locator(".mu-n").get_attribute("class").strip() == "mu-n"
    assert cell(page, "Jahmyr Gibbs").inner_text().strip() == "—"          # bye
    assert cell(page, "Jahmyr Gibbs").locator(".mu-none").count() == 1
    assert cell(page, "Joe Burrow").locator(".mu-none").count() == 1      # no profile
    page.evaluate("VIEW='espn'; render()")
    assert "mu-hard" in cell(page, "George Kittle").locator(".mu-n").get_attribute("class")
    assert "mu-easy" in cell(page, "Tee Higgins").locator(".mu-n").get_attribute("class")
    assert re.sub(r"\s+", " ", cell(page, "Tee Higgins").inner_text()).strip() == "vs PIT 8th"
    tip = page.locator(".colhead .ch-match > summary").get_attribute("title")
    assert tip.startswith("Rank among 32 defenses against his position")
    assert page.locator(".mchip").count() == 0
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_phone_moves_matchup_to_the_meta_line(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.evaluate("VIEW='espn'; render()")
    kittle = row(page, "George Kittle")
    assert not kittle.locator(".match").is_visible()
    meta = kittle.locator(".nm-2 .mu-meta")
    assert meta.is_visible() and re.sub(r"\s+", " ", meta.inner_text()).strip() == "· vs LAR 25th"
    assert "mu-hard" in meta.locator(".mu-n").get_attribute("class")
    assert row(page, "Brock Purdy").locator(".mu-meta").count() == 0       # no profile: no clause
    page.evaluate("VIEW='yahoo'; render()")
    assert row(page, "Jahmyr Gibbs").locator(".mu-meta").count() == 0      # bye: no clause
    assert page.evaluate("document.documentElement.scrollWidth") <= 390
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_panel_blocks_and_details_collapsed(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    drawer = page.locator("#drawer")
    row(page, "Amon-Ra St. Brown").click()
    assert drawer.locator(".pf-sec").count() == 3
    assert drawer.locator(".pf-rank").inner_text().strip() == "9th easiest of 32 for WRs"
    assert "31% · 4 of 13" in drawer.locator(".pf-sec").nth(2).inner_text()
    details = drawer.locator("details.pf-details")
    assert details.count() == 1 and details.get_attribute("open") is None
    assert not drawer.locator(".pf-dsec").first.is_visible()
    drawer.locator(".pf-details > summary").click()
    assert details.get_attribute("open") is not None
    assert drawer.locator(".pf-tag", has_text="UNTESTED").first.inner_text().strip() == "UNTESTED"
    assert drawer.inner_text().count("METHODOLOGY") == 1
    page.keyboard.press("Escape")
    assert "on" not in drawer.get_attribute("class")
    assert page.evaluate("document.activeElement.classList.contains('row')")
    row(page, "Chase Brown").click()
    text = drawer.inner_text()
    assert "A back has no depth zones." in text and drawer.locator(".pf-stack").count() == 0
    assert text.index("6 of 11") < text.index("1 of 13")                   # carries before targets
    page.keyboard.press("Escape")
    row(page, "Jahmyr Gibbs").click()
    assert "Bye, or no schedule yet." in drawer.inner_text()
    assert "5 of 9" in drawer.inner_text()                                  # carries, under 10
    page.keyboard.press("Escape")
    page.evaluate("VIEW='espn'; render()")
    row(page, "George Kittle").click()
    assert "mu-hard" in drawer.locator(".pf-rank").get_attribute("class")
    rz = drawer.locator(".pf-sec").nth(2).inner_text()
    assert "3 of 8" in rz and "%" not in rz                                 # counts under 10
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_red_zone_line_switches_at_ten(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    got = page.evaluate("""() => [
      rzLineHTML(1, 5, 0.2, ["team target", "team targets"], false),
      rzLineHTML(3, 10, 0.3, ["team target", "team targets"], false),
    ].map(h => { const d = document.createElement("div"); d.innerHTML = h; return d.textContent; })""")
    assert got[0].startswith("1 of 5") and "%" not in got[0]
    assert got[1].startswith("30% · 3 of 10")
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_market_row_shows_priced_numbers(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    row(page, "Amon-Ra St. Brown").click()
    drawer = page.locator("#drawer")
    drawer.locator(".pf-details > summary").click()
    text = drawer.inner_text()
    assert "UNTESTED" in text
    assert "17.8 pts" in text and "role 18.2 pts" in text
    assert "WR rank #5" in text and "z 0.82" in text
    assert "Priced: REC" in text
    assert not re.search(r"\b(BUY|SELL|RISING|FALLING|HOT|COLD)\b", text, re.I)
    page.keyboard.press("Escape")
    ctx.close()


@pytest.mark.render
def test_market_row_falls_back_to_model_pts(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    page.evaluate("VIEW='espn'; render()")
    row(page, "George Kittle").click()
    drawer = page.locator("#drawer")
    drawer.locator(".pf-details > summary").click()
    text = drawer.inner_text()
    assert "UNTESTED" in text
    assert "13.1 pts, the model's number" in text
    assert "No market priced yet." in text
    page.keyboard.press("Escape")
    ctx.close()


@pytest.mark.render
def test_market_row_zero_d_rank_shows_no_change_marker(browser, page_file):
    """d_rank 0 (Chase Brown, tests/fixtures/data/market_stock.json) must not render a delta
    marker next to the rank -- "#8 -- 0" reads as a range, not as "no change." z moves to the
    role line instead of sharing the rank line."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    row(page, "Chase Brown").click()
    drawer = page.locator("#drawer")
    drawer.locator(".pf-details > summary").click()
    rank_line = drawer.locator(".pf-cap", has_text="RB rank #8")
    assert rank_line.count() == 1
    assert rank_line.locator(".delta").count() == 0
    text = drawer.inner_text()
    assert "z -0.05" in text
    page.keyboard.press("Escape")
    ctx.close()


@pytest.mark.render
def test_market_row_partial_markets_shows_priced_not_no_market(browser, page_file):
    """A src:"model" row can still carry a partial `markets` list (Tee Higgins: ["REC"]); the
    "No market priced yet." sentence is only for a row with no markets priced at all."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    page.evaluate("VIEW='espn'; render()")
    row(page, "Tee Higgins").click()
    drawer = page.locator("#drawer")
    drawer.locator(".pf-details > summary").click()
    text = drawer.inner_text()
    assert "UNTESTED" in text
    assert "11.2 pts, the model's number" in text
    assert "Priced: REC" in text
    assert "No market priced yet." not in text
    page.keyboard.press("Escape")
    ctx.close()


@pytest.mark.render
def test_no_verdict_words_on_the_page(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    words = re.compile(r"\b(PLUS|MINUS|EVEN)\b", re.I)
    for view in ("yahoo", "espn"):
        page.evaluate(f"VIEW='{view}'; render()")
        assert not words.search(page.locator("body").inner_text()), view
        for i in range(page.locator(".row").count()):
            page.locator(".row").nth(i).click()
            summary = page.locator("#drawer .pf-details > summary")
            if summary.count():
                summary.click()
            assert not words.search(page.locator("#drawer").inner_text()), (view, i)
            page.keyboard.press("Escape")
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_no_profiles_renders_dashes_and_a_quiet_panel(browser, monkeypatch, tmp_path):
    monkeypatch.setattr(build, "load_profiles", lambda: None)
    p = tmp_path / "index.html"
    p.write_text(build.render().page, encoding="utf-8")
    ctx, page, errors = open_page(browser, p, (390, 844))
    assert page.locator(".match .mu-n").count() == 0
    row(page, "Amon-Ra St. Brown").click()
    assert page.locator("#drawer .pf-empty").count() == 1
    assert page.locator("#drawer .pf-sec").count() == 0
    assert errors == []
    ctx.close()
