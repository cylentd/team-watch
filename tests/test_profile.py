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
from test_render import browser, drive, go  # noqa: F401  (browser is a fixture)
from test_render import open_page as open_any_page

PROFILES = json.loads((FIXTURES / "data" / "player_profiles.json").read_text(encoding="utf-8"))
MARKET_STOCK = json.loads((FIXTURES / "data" / "market_stock.json").read_text(encoding="utf-8"))


def open_page(browser, page_file, viewport):
    """Every rendered test here clicks a player on the roster, and the page opens on the Board
    since 2026-09-24, so go to the roster first."""
    ctx, page, errors = open_any_page(browser, page_file, viewport)
    drive(page, go("roster"))
    return ctx, page, errors


def tab(page, name):
    """Open one of the modal's panes. Only the open pane is in the DOM (tabs.js), so a test that
    wants the matchup blocks has to ask for them; a pane with nothing in it draws no button, so
    `.count()` first when the player may not have that pane at all."""
    page.locator(f"#modal [data-pftab='{name}']").click()


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
    """The row's matchup, a clause on its meta line since the Matchup column went (2026-09-25)."""
    return row(page, name).locator(".mu-meta")


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
    assert cell(page, "Jahmyr Gibbs").count() == 0                         # bye: no clause
    assert cell(page, "Joe Burrow").count() == 0                           # no profile: no clause
    page.evaluate("VIEW='espn'; render()")
    assert "mu-hard" in cell(page, "George Kittle").locator(".mu-n").get_attribute("class")
    assert "mu-easy" in cell(page, "Tee Higgins").locator(".mu-n").get_attribute("class")
    assert re.sub(r"\s+", " ", cell(page, "Tee Higgins").inner_text()).strip() == "vs PIT 8th"
    # The ordinal says what it ranks in its title, since the column header that carried it went.
    tip = cell(page, "Tee Higgins").locator(".mu-n").get_attribute("title")
    assert "easiest of 32" in tip
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
    # The ordinal is the profile's since 2026-09-24: a phone row reads "TE · SF vs LAR".
    assert meta.is_visible() and re.sub(r"\s+", " ", meta.inner_text()).strip() == "vs LAR"
    assert not meta.locator(".mu-n").is_visible()
    assert kittle.locator(".rproj").is_visible()
    assert row(page, "Brock Purdy").locator(".mu-meta").count() == 0       # no profile: no clause
    page.evaluate("VIEW='yahoo'; render()")
    assert row(page, "Jahmyr Gibbs").locator(".mu-meta").count() == 0      # bye: no clause
    assert page.evaluate("document.documentElement.scrollWidth") <= 390
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_head_carries_the_verdict_and_both_teams(browser, page_file):
    """The verdict word and the two-league tag left the roster row on 2026-09-25 for the profile
    head. Looked up by slug, so a sheet opened from anywhere (search passes a bare {n, pos, team})
    says the same thing a roster row's sheet does."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    modal = page.locator("#modal")
    page.evaluate("VIEW='espn'; render()")
    row(page, "Chase Brown").click()                     # RISING in watch, on both fixture rosters
    tags = modal.locator(".pf-tags")
    assert tags.locator(".tag.verdict").inner_text().strip() == "RISING"
    assert tags.locator(".pf-why").inner_text().startswith("snaps +13.0")
    assert tags.locator(".pf-mine").inner_text().strip() == "On 2 of your teams"
    from_search = page.evaluate("""() => { openProfile({n: "Chase Brown", pos: "RB", team: "CIN"});
      return document.querySelector("#modal .pf-tags").innerText; }""")
    assert "RISING" in from_search and "On 2 of your teams" in from_search
    page.evaluate("""() => openProfile(findPlayer('espn', TEAMS.espn.roster.filter(p => p.start)
      .findIndex(p => p.n === 'Brock Purdy')))""")      # watch says hold, one roster: no line
    assert modal.locator(".pf-tags").count() == 0
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_panes_split_the_blocks_and_only_one_is_in_the_dom(browser, page_file):
    """Three panes since 2026-09-22, replacing eleven stacked blocks and the Details disclosure
    nested inside them. Each block still renders exactly as before; what changed is which pane
    it belongs to, and that only the open pane exists in the DOM at all."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    modal = page.locator("#modal")
    row(page, "Amon-Ra St. Brown").click()
    assert [b.inner_text() for b in modal.locator("[data-pftab]").all()] == ["USAGE", "MATCHUP", "LOG"]
    # Usage opens first: target depth, red zone, middle vs outside. Nothing from another pane.
    assert modal.locator(".pf-sec", has_text="Target depth").locator(".pf-zone").count() == 4
    assert "31% · 4 of 13" in modal.locator(".pf-sec", has_text="Red zone").inner_text()
    assert modal.locator(".pf-rank").count() == 0
    tab(page, "matchup")
    assert modal.locator(".pf-rank").inner_text().strip() == "9th easiest of 32 for WRs"
    assert modal.locator(".pf-zones").count() == 0                         # usage is gone, not hidden
    assert modal.locator(".pf-tag", has_text="UNTESTED").first.inner_text().strip() == "UNTESTED"
    assert modal.inner_text().count("METHODOLOGY") == 1
    tab(page, "log")
    assert modal.locator(".pf-table-wk").count() == 1
    assert "PROJECTION" in modal.inner_text()
    page.keyboard.press("Escape")
    assert "on" not in modal.get_attribute("class")
    assert page.evaluate("document.activeElement.classList.contains('row')")
    row(page, "Chase Brown").click()
    # Four tabs for him, three for St. Brown above: Bio reads LIVE_PEDIGREE alone, and the
    # fixture has a pedigree record for this back and none for that receiver. A pane with
    # nothing in it draws no button rather than opening on an empty panel.
    assert [b.inner_text() for b in modal.locator("[data-pftab]").all()] == ["USAGE", "MATCHUP", "LOG", "BIO"]
    tab(page, "usage")
    text = modal.inner_text()
    assert "Target depth" not in text and modal.locator(".pf-zones").count() == 0   # a back: no block
    assert text.index("6 of 11") < text.index("1 of 13")                   # carries before targets
    page.keyboard.press("Escape")
    row(page, "Jahmyr Gibbs").click()
    tab(page, "usage")
    assert "5 of 9" in modal.inner_text()                                  # carries, under 10
    tab(page, "matchup")
    assert "Bye, or no schedule yet." in modal.inner_text()
    page.keyboard.press("Escape")
    page.evaluate("VIEW='espn'; render()")
    row(page, "George Kittle").click()
    tab(page, "usage")
    rz = modal.locator(".pf-sec", has_text="Red zone").inner_text()
    assert "3 of 8" in rz and "%" not in rz.split("\n")[1]                  # counts under 10
    tab(page, "matchup")
    assert "mu-hard" in modal.locator(".pf-rank").get_attribute("class")
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_lede_leads_with_three_numbers(browser, page_file):
    """The modal's answer to "what do I do with him", above the charts and above the tabs: what
    he scores, who he plays, and whether the role backs it up. Numbers only -- DESIGN.md's market
    rule bans a verdict word, and METHODOLOGY 12.46 is why. A cell whose source has nothing for
    this player is left out rather than dashed, so the row never shows a number that failed."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    row(page, "Amon-Ra St. Brown").click()
    cells = page.locator("#modal .pf-lede-c")
    assert cells.count() == 3
    assert [c.locator("b").inner_text() for c in cells.all()] == ["17.3", "9th", "#5"]
    assert [c.locator(".pf-lede-l").inner_text() for c in cells.all()] == ["PROJECTED", "EASIEST", "TARGET SHARE"]
    assert cells.nth(1).locator(".pf-lede-s").inner_text() == "of 32 WRs"
    # 9th of 32 is neither of the eight easiest nor the eight hardest: plain, the same call the
    # roster row's MATCHUP cell makes. Kittle at 25th is one of the eight hardest.
    assert cells.nth(1).get_attribute("class") == "pf-lede-c"
    # The rank now has exactly one home at each altitude: the lede, and the radar's own label.
    # It used to be in the card under the radar as well -- three copies of one number.
    assert page.locator("#modal .pf-stat-r").count() == 0
    page.keyboard.press("Escape")
    page.evaluate("VIEW='espn'; render()")
    row(page, "George Kittle").click()
    assert "mu-hard" in page.locator("#modal .pf-lede-c").nth(1).get_attribute("class")
    assert page.locator("#modal .pf-lede-c").nth(1).locator("b").inner_text() == "8th"
    page.keyboard.press("Escape")
    page.evaluate("VIEW='yahoo'; render()")                 # Gibbs is on the Yahoo roster
    row(page, "Jahmyr Gibbs").click()                       # a bye: the one place a dash earns it
    bye = page.locator("#modal .pf-lede-c", has_text="bye week")
    assert bye.count() == 1 and bye.locator("b").inner_text() == "—"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_facts_show_pedigree_and_fantasy_draft(browser, page_file):
    """tests/fixtures/data/pedigree.json: Jahmyr Gibbs was 1.12 (pick 12 overall) in the real
    2023 NFL draft, drafted 1.01 by my ESPN team and 1.02 in Yahoo; Chase Brown has an ESPN pick
    only, the per-league optional-ness that fantasy_draft's shape allows.

    The bio splits in two (2026-09-22). Age, size, experience and the bye qualify every number in
    the modal, so they are a line under his name; where he was drafted is history that decides
    nothing this week, so it keeps a headed block at the foot of the left column."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    row(page, "Jahmyr Gibbs").click()
    # The bye is the one fact here that decides something, so it is on the identity line under
    # his name; the rest is reference and lives in its own Bio pane. The fixture's pedigree
    # carries no measurables, so the pane's live shape is proved against a stub -- what matters
    # is that a missing field drops out rather than dashing.
    assert page.locator("#modal .pf-who .lbl").inner_text().upper().endswith("· BYE 6")
    tab(page, "bio")
    facts = page.locator("#modal .pf-tabpane .pf-facts").inner_text()
    assert "Week 6" not in facts                      # the bye is the head's now, not the grid's
    assert "Rd 1.12 · 2023" in facts and "overall" not in facts
    assert page.evaluate("""() => {
      LIVE_PEDIGREE.players['stub'] = {age: 27, height: '73', weight: 210, years_exp: 5, bye: 9};
      const d = document.createElement('div');
      d.innerHTML = bioBlockHTML({slug: 'stub'});
      return [...d.querySelectorAll('dt')].map((k, i) =>
        k.textContent + ' ' + d.querySelectorAll('dd')[i].textContent); }""") \
        == ["Age 27", "Size 6′1″ · 210 lb", "Exp 5 yr pro"]
    # One row per league I have a team in, labelled by my team's name there (uppercase in the
    # render); "by X" only when someone else took him.
    labels = [d.inner_text() for d in page.locator("#modal .pf-facts dt").all()]
    assert page.evaluate("TEAMS.yahoo.name").upper() in labels
    assert page.evaluate("TEAMS.espn.name").upper() in labels
    assert "Rd 1.01 · by Big Salty" in facts
    assert "Rd 1.02 · by Team Minh" in facts
    page.keyboard.press("Escape")
    row(page, "Chase Brown").click()
    tab(page, "bio")
    facts = page.locator("#modal .pf-tabpane .pf-facts").inner_text()
    assert "Rd 3.07 · by Big Salty" in facts
    assert page.evaluate("TEAMS.yahoo.name").upper() not in [d.inner_text() for d in page.locator("#modal .pf-facts dt").all()]
    page.keyboard.press("Escape")
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_head_line_gives_the_fantasy_tier(browser, page_file):
    """"RB4": his rank by points per game, season to date, among every RB in LIVE_POOL
    (watch.json) -- said the way a fantasy reader says it, never as a WR1/2/3 tier that reads
    like a depth chart. No lineup slot, no depth-chart label."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    row(page, "Chase Brown").click()
    head = page.locator("#modal .pf-who .lbl").inner_text().upper()
    rank, of, _tied = page.evaluate("ppgRank({slug: 'chase-brown', pos: 'RB'})")
    # One separator for the whole line, and the same one the rest of the page uses. The bye
    # joins it (2026-09-22) rather than taking a third line in a head fixed above the scroll.
    assert head == f"RB · CIN · RB{rank} · BYE 10"
    assert "|" not in head
    assert of == page.evaluate("LIVE_POOL.players.filter(r => r.pos === 'RB' && r.ppg !== null).length")
    page.keyboard.press("Escape")
    row(page, "Amon-Ra St. Brown").click()          # not in the fixture pool: no clause at all
    assert page.locator("#modal .pf-who .lbl").inner_text().upper() == "WR · DET"
    page.keyboard.press("Escape")
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_weather_shows_stadium_forecast_with_icons(browser, page_file):
    """tests/fixtures/data/weather.json: Amon-Ra St. Brown is away at KC (outdoor, sunny), Chase
    Brown is home at CIN (outdoor, cooler), Jahmyr Gibbs has no next game (a bye in the fixture)
    so no forecast to show at all. The forecast sits inside the matchup block, in the Matchup
    pane."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    row(page, "Amon-Ra St. Brown").click()
    tab(page, "matchup")
    wx = page.locator("#modal .pf-sec", has_text="Week 3 @ KC").locator(".pf-weather")
    assert wx.count() == 1
    text = wx.inner_text()
    assert "71°F" in text and "Sunny" in text and "10 mph" in text and "from S" in text
    assert "%" not in text                              # the sky phrase carries the rain chance
    assert wx.locator("svg.pf-wx-i").count() == 2
    page.keyboard.press("Escape")
    row(page, "Chase Brown").click()
    tab(page, "matchup")
    text = page.locator("#modal .pf-weather").inner_text()
    assert "58°F" in text and "Partly Cloudy" in text and "6 mph" in text
    page.keyboard.press("Escape")
    row(page, "Jahmyr Gibbs").click()
    tab(page, "matchup")
    assert page.locator("#modal .pf-weather").count() == 0
    page.keyboard.press("Escape")
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_red_zone_split_names_the_teammates(browser, page_file):
    """red_zone.others (player_profiles.json): Amon-Ra St. Brown has 4 of DET's 13 red-zone
    targets; Sam LaPorta 4 and Jahmyr Gibbs 2 are named, the other 3 are "3 more". His segment
    comes first and is the bright one."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    row(page, "Amon-Ra St. Brown").click()
    split = page.locator("#modal .pf-split")
    assert split.count() == 1
    # Small type drops the first name to an initial; the header carries the full one.
    key = split.locator(".pf-split-key").inner_text()
    assert key.index("A. St. Brown 4") < key.index("S. LaPorta 4") < key.index("J. Gibbs 2") < key.index("3 more")
    assert "Amon-Ra" not in key
    segs = split.locator(".pf-split-bar i")
    assert segs.count() == 3 and "me" in segs.first.get_attribute("class")
    page.keyboard.press("Escape")
    row(page, "Chase Brown").click()          # a back: a carries split above a targets split
    splits = page.locator("#modal .pf-split")
    assert splits.count() == 2
    assert "Z. Moss 3" in splits.nth(0).inner_text() and "J. Chase 5" in splits.nth(1).inner_text()
    page.keyboard.press("Escape")
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_rate_under_its_floor_shows_its_sample_and_no_rank(browser, page_file):
    """2026-09-26: M. Stafford's 33% goal-line share was 1 of 3 and ranked 85th percentile. In the
    fixture L. Jackson is 1 of 4 against a floor of 5, J. Allen 3 of 5. Below the floor the number
    stays, says what it is out of, and nothing ranks it: not the radar, not Leaders."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    got = page.evaluate("""(() => {
      const s = sheetFor({slug: 'lamar-jackson'}), a = s.axes.find(x => x.id === 'gl_pct');
      const d = document.createElement('div'); d.innerHTML = statDetailHTML(s, 'gl_pct');
      const allen = sheetFor({slug: 'josh-allen'});
      const d2 = document.createElement('div'); d2.innerHTML = statDetailHTML(allen, 'gl_pct');
      return {rank: sheetRank('QB', 'gl_pct', 'lamar-jackson'), allen: sheetRank('QB', 'gl_pct', 'josh-allen'),
              smp: d.querySelector('.pf-stat-smp').textContent, thin: d.querySelector('.pf-stat-thin').textContent,
              dim: d.querySelector('b').className, meta: d.querySelector('.pf-stat-wk').textContent,
              allenSmp: d2.querySelector('.pf-stat-smp').textContent, allenThin: d2.querySelectorAll('.pf-stat-thin').length,
              held: bdThinOut('QB', 'gl_pct', -1).map(r => sampleShort(r, a)), floor: a.floor};
    })()""")
    assert got["rank"] is None and got["allen"] is not None
    assert got["smp"] == "1 of 4 team carries inside the 5"
    assert got["thin"] == "Too few to rank (needs 5)" and got["dim"] == "thin"
    assert "of " not in got["meta"]                       # no "of 0" for a rank that is not one
    assert got["allenSmp"] == "3 of 5 team carries inside the 5" and got["allenThin"] == 0
    assert got["held"] == ["3/4", "2/3", "1/4"]           # C. Ward 75%, T. Shough 66.7%, L. Jackson 25%
    assert not errors
    ctx.close()


def test_stat_sheet_draws_the_positions_own_axes(browser, page_file):
    """ff-jarvis's `sheet.axes` drives the shape: six for a receiver, none of them a raw count
    the Grid already shows. Every number is his season rank among the position ("#3", "#3*" on a
    tie), first place at the rim. Each label is a button; the card under the sheet shows that
    stat's number, its elite bar and the weeks as a line, and the caption under the chart carries
    that axis's own "of N" -- the rank itself is the lede's and the radar label's, not the
    card's, so one number has one home."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    row(page, "Amon-Ra St. Brown").click()
    radar = page.locator("#modal .pf-radar")
    assert radar.count() == 1
    assert radar.locator("polygon.pf-radar-shape").count() == 1
    assert radar.locator(".pf-radar-ring").count() == 4
    axes = page.evaluate("USAGE.sheet.axes.WR.map(a => a.id)")
    assert axes == ["wopr", "route_pct", "tprr", "yprr", "fdrr", "rz_tgt"]
    assert page.locator("#modal .pf-radar-l").count() == len(axes)
    assert page.locator("#modal .pf-radar-l", has_text="aDOT").count() == 0   # not "more is better"
    rank, of, _tied = page.evaluate("sheetRank('WR', 'wopr', 'amonra-st-brown')")
    mark = page.evaluate("rankMark(sheetRank('WR', 'wopr', 'amonra-st-brown'))")
    assert rank >= 1 and of >= rank
    # No tie marker anywhere, from 2026-09-22: rankAmong already shares the rank, and the
    # asterisk on top only said "someone else has this number", which decides nothing.
    assert mark == f"#{rank}"
    assert "*" not in radar.text_content()
    # Rank first, then the stat's plain name (HTML labels over the chart since 2026-09-25).
    assert f"{mark}Target share" in page.locator("#modal .pf-radar-box").text_content()
    # The denominator lives on the card's header line, not in a caption under the chart: it
    # repeated the lede's own "of 120" and cost the left column height it did not have.
    assert f"of {of}" in page.locator("#modal .pf-stat-wk").inner_text()
    assert page.locator("#modal .pf-sheet .pf-cap").count() == 0
    # The card opens on the first axis and follows a tap on another.
    card = page.locator("#modal .pf-stat")
    assert card.count() == 1
    assert card.locator(".pf-stat-l").inner_text() == "TARGET SHARE"
    assert card.locator(".pf-stat-r").count() == 0             # the rank belongs to the lede
    # The gap, not the threshold: "elite >= 0.00" printed in red said the elite bar was the bad
    # thing, when what is red is him being under it. The colour now agrees with the sign.
    assert card.locator(".pf-stat-d").inner_text() == "0.11 over the elite bar (0.70)"
    assert card.locator(".pf-stat-d").get_attribute("class").endswith("up")
    # And the initials are defined, with a second clause on what to do with the number.
    assert "air yards" in card.locator(".pf-stat-def").inner_text()
    assert "predictor" in card.locator(".pf-stat-why").inner_text()
    assert "on" in page.locator("#modal .pf-radar-l", has_text="Target share").get_attribute("class")
    # A pick moves three things at once, so the chart and the card are visibly the same stat.
    assert radar.locator("circle.pf-radar-dot.on").get_attribute("data-col") == "wopr"
    page.locator("#modal .pf-radar-l", has_text="Yds/route").click()
    assert card.locator(".pf-stat-l").inner_text() == "YDS/ROUTE"
    assert "on" in page.locator("#modal .pf-radar-l", has_text="Yds/route").get_attribute("class")
    assert "on" not in page.locator("#modal .pf-radar-l", has_text="Target share").get_attribute("class")
    assert radar.locator("circle.pf-radar-dot.on").get_attribute("data-col") == "yprr"
    # Each axis has its own denominator (everyone with a target, but only those with routes),
    # so the header follows the pick rather than freezing on the opening axis's.
    yprr_of = page.evaluate("sheetRank('WR', 'yprr', 'amonra-st-brown')")[1]
    assert f"of {yprr_of}" in page.locator("#modal .pf-stat-wk").inner_text()
    assert "pctl" not in page.locator("#modal").inner_text()
    page.keyboard.press("Escape")
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_every_block_says_how_many_weeks_it_covers(browser, page_file):
    """The blocks do not share a window. Red zone and target depth are season to date; anything
    divided by routes waits on heatradar, which publishes one week at a time, so Route%, TPRR,
    YPRR and 1D/RR can be a one-week number sitting on the same chart as two-week ones. A number
    whose window is not stated cannot be checked -- which is exactly how a correct red-zone
    figure came to look wrong."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    row(page, "Amon-Ra St. Brown").click()
    tab(page, "usage")
    wins = {w.locator("xpath=ancestor::section").locator(".lbl").inner_text(): w.inner_text()
            for w in page.locator("#modal .pf-win").all()}
    assert wins == {"TARGET DEPTH": "2 wk", "RED ZONE": "2 wk"}   # .lbl uppercases in the render
    # And per stat, on the card. Three states, because the fixture has no weekly rows for the
    # sheet stats and that is itself one of them.
    radar = page.locator("#modal .pf-radar")
    meta = page.locator("#modal .pf-stat-wk")
    of = page.evaluate("sheetRank('WR', 'yprr', 'amonra-st-brown')")[1]
    page.locator("#modal .pf-radar-l", has_text="Yds/route").click()
    assert meta.inner_text() == f"2 gm · of {of}"          # no weekly rows: games, no window
    plant = """(weeks) => {
      const row = USAGE.rows.find(r => r.slug === 'amonra-st-brown');
      USAGE.rows = USAGE.rows.filter(r => r.slug !== 'amonra-st-brown');
      weeks.forEach(wk => USAGE.rows.push({...row, wk, v: {...row.v, yprr: 1.5 + wk}}));
    }"""
    page.evaluate(plant, [1, 2])
    page.locator("#modal .pf-radar-l", has_text="Yds/route").click()
    assert meta.inner_text() == f"of {of} · wk 1–2"         # two weeks: the range, no games
    # Now as heatradar actually publishes it: week 1 only, while his other stats have two.
    page.evaluate(plant, [1])
    page.locator("#modal .pf-radar-l", has_text="Yds/route").click()
    assert meta.inner_text() == f"of {of} · wk 1"
    assert "gm" not in meta.inner_text()                    # never both counts of one sample
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_too_few_measured_axes_draw_no_shape(browser, page_file):
    """Under three measured axes there is no shape, and <polygon> with two points renders as a
    bare line between them -- which reads as a broken chart rather than as a player heatradar
    has not covered yet. The vertices still plot, because they are real, and the count says why
    the rest is missing. (Rashee Rice in week 2: WOPR and RZ Tgts measured, the four
    route-derived stats not.)"""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    row(page, "Amon-Ra St. Brown").click()
    radar = page.locator("#modal .pf-radar")
    assert radar.locator("polygon.pf-radar-shape").count() == 1     # six axes: a real shape
    assert radar.locator(".pf-radar-note").count() == 0
    page.keyboard.press("Escape")
    # Strip four of his six axes and reopen: two points left, so no polygon and a count instead.
    page.evaluate("""() => {
      const r = USAGE.sheet.rows.find(x => x.slug === 'amonra-st-brown');
      ['route_pct', 'tprr', 'yprr', 'fdrr'].forEach(k => { r.v[k] = null; });
      for (const k in SHEET_BY) delete SHEET_BY[k];   // memoised per position+axis
    }""")
    row(page, "Amon-Ra St. Brown").click()
    assert radar.locator("polygon.pf-radar-shape").count() == 0
    assert radar.locator("circle.pf-radar-dot").count() == 2
    assert radar.locator(".pf-radar-note").text_content().strip() == "2 of 6 stats measured"
    assert page.locator("#modal .pf-radar-box").text_content().count("—") == 4   # the unmeasured axes say so
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_each_position_gets_its_own_shape(browser, page_file):
    """A back's sheet is opportunity and rushing talent, a passer's is volume and his legs.
    Four to six axes each, and the sheet is tinted by position so a run of profiles reads
    QB/RB/WR/TE without anyone reading the label."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    axes = page.evaluate(
        "Object.fromEntries(Object.entries(USAGE.sheet.axes).map(([k, v]) => [k, v.map(a => a.id)]))")
    assert axes["RB"] == ["wopp", "opp_pct", "route_pct", "rz", "ryoe", "brk_rate"]
    assert axes["QB"] == ["dropbacks", "designed_pct", "scr_rate", "gl_pct", "rz_att", "fp_db"]
    assert axes["TE"] == axes["WR"]
    for pos, ids in axes.items():
        assert 4 <= len(ids) <= 6, pos
        assert len(set(ids)) == len(ids), pos
    row(page, "Chase Brown").click()
    assert page.locator("#modal .pf-sheet.pos-rb").count() == 1
    assert page.locator("#modal .pf-radar-l").count() == 6
    page.keyboard.press("Escape")
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_ties_share_a_rank(browser, page_file):
    """Competition ranking: two tied for first are both 1st and say so, the next is 3rd -- never
    RB1 and RB2 by whichever the sort happened to put first."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    page.evaluate("""USAGE.sheet.rows.push(
      {n: 'A', slug: 'a', pos: 'XX', team: 'T', g: 1, v: {car: 10}},
      {n: 'B', slug: 'b', pos: 'XX', team: 'T', g: 1, v: {car: 10}},
      {n: 'C', slug: 'c', pos: 'XX', team: 'T', g: 1, v: {car: 5}})""")
    assert page.evaluate("sheetRank('XX', 'car', 'a')") == [1, 3, True]
    assert page.evaluate("sheetRank('XX', 'car', 'b')") == [1, 3, True]
    assert page.evaluate("sheetRank('XX', 'car', 'c')") == [3, 3, False]
    assert page.evaluate("sheetRank('XX', 'car', 'nobody')") is None
    # The tie is in the rank itself -- both are 1st and the next is 3rd -- not in a marker on it.
    assert page.evaluate("rankText('XX', [1, 3, true])") == "XX1"
    assert page.evaluate("rankText('XX', [3, 3, false])") == "XX3"
    assert page.evaluate("rankMark([1, 3, true])") == "#1"
    assert page.evaluate("rankAmong({a: 2.5, b: 2.5, c: 2.5}, 'b')") == [1, 3, True]
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_height_reads_in_feet_not_inches(browser, page_file):
    """Sleeper stores height as bare inches in a string; nobody reads a receiver as 73."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    assert page.evaluate("inchesText('73')") == "6′1″"
    assert page.evaluate("inchesText('72')") == "6′0″"
    assert page.evaluate("inchesText(null)") is None
    assert page.evaluate("shortName('Xavier Worthy')") == "X. Worthy"
    assert page.evaluate("shortName('Kenneth Walker III')") == "K. Walker III"
    assert page.evaluate("shortName('Ja\\'Marr Chase')") == "J. Chase"
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
    modal = page.locator("#modal")
    tab(page, "matchup")
    text = modal.inner_text()
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
    modal = page.locator("#modal")
    tab(page, "matchup")
    text = modal.inner_text()
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
    modal = page.locator("#modal")
    tab(page, "matchup")
    rank_line = modal.locator(".pf-cap", has_text="RB rank #8")
    assert rank_line.count() == 1
    assert rank_line.locator(".delta").count() == 0
    text = modal.inner_text()
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
    modal = page.locator("#modal")
    tab(page, "matchup")
    text = modal.inner_text()
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
            # Every pane, not just the one that opens: a verdict word hiding in the matchup
            # pane is still on the page.
            for b in page.locator("#modal [data-pftab]").all():
                b.click()
                assert not words.search(page.locator("#modal").inner_text()), (view, i)
            assert not words.search(page.locator("#modal").inner_text()), (view, i)
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
    assert page.locator("#modal .pf-empty").count() == 1
    # The usage and matchup panes need LIVE_PROFILES, so neither draws a tab and the notice says
    # why once. The stat sheet, weekly history and projection each read their own source
    # (LIVE_USAGE/LIVE_GAMELOG/LIVE_PROJECTIONS) and still render -- a player with no matchup
    # profile is not blank, and the lede still leads with what it can price.
    assert page.locator("#modal [data-pftab]").count() == 0
    assert page.locator("#modal .pf-sec").count() == 2         # weekly history, projection
    assert page.locator("#modal .pf-radar").count() == 1
    assert page.locator("#modal .pf-lede-c").count() == 2      # projected + WOPR, no matchup
    assert errors == []
    ctx.close()
