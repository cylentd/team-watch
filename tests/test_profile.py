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


def sheet(page):
    """Open the stat sheet. Since 2026-09-28 the radar lives in the sphere in the profile head
    (orb.js) and opens as a layer over the profile (orbsheet.js); under the suite's reduced motion
    it lands at once, with no morph to wait for."""
    page.locator("#modal .pf-orb").click()


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
def test_head_carries_the_verdict(browser, page_file):
    """The verdict word left the roster row on 2026-09-25 for the profile head. Looked up by slug,
    so a sheet opened from anywhere (search passes a bare {n, pos, team}) says the same thing a
    roster row's sheet does. "On 2 of your teams" went on 2026-09-28 to the owner pills."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    modal = page.locator("#modal")
    page.evaluate("VIEW='espn'; render()")
    row(page, "Chase Brown").click()                     # RISING in watch, on both fixture rosters
    tags = modal.locator(".pf-tags")
    assert tags.locator(".tag.verdict").inner_text().strip() == "RISING"
    assert tags.locator(".pf-why").inner_text().startswith("snaps +13.0")
    assert modal.locator(".pf-mine").count() == 0
    from_search = page.evaluate("""() => { openProfile({n: "Chase Brown", pos: "RB", team: "CIN"});
      return document.querySelector("#modal .pf-tags").innerText; }""")
    assert "RISING" in from_search
    page.evaluate("""() => openProfile(findPlayer('espn', TEAMS.espn.roster.filter(p => p.start)
      .findIndex(p => p.n === 'Brock Purdy')))""")      # watch says hold, one roster: no line
    assert modal.locator(".pf-tags").count() == 0
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_head_carries_his_injury_status(browser, page_file):
    """2026-09-30 (David: "should injured players have their status on the player profile?"): the head
    says the level and Sleeper's reason, from the same injFor() the roster cards read; a healthy player
    shows nothing. It is a line of the name block, under the identity line, at every width (moved there
    the same day: alone in the head's middle it looked stray)."""
    for size in ((1400, 900), (360, 800)):
        ctx, page, errors = open_page(browser, page_file, size)
        got = page.evaluate("""() => {
          const hurt = Object.entries(LIVE_INJURY.players).map(([slug, r]) => ({slug, r}))
            .map(x => ({...x, e: searchIndex().find(e => e.slug === x.slug)})).find(x => x.e);
          openProfile(searchPlayer(hurt.e));
          const box = document.querySelector('#modal .pf-inj');
          const want = injFor({slug: hurt.slug});
          const lbl = document.querySelector('#modal .pf-who .lbl');
          const out = {has: !!box, cls: box && box.className, word: box && box.querySelector('.pf-inj-s').textContent.trim(),
                       note: (box && box.querySelector('.pf-inj-n') || {}).textContent || null, want,
                       inWho: !!box.closest('.pf-who'), afterId: lbl.nextElementSibling === box,
                       belowId: box.getBoundingClientRect().top >= lbl.getBoundingClientRect().bottom};
          const well = searchIndex().find(e => !injFor({slug: e.slug}) && !e.status);
          openProfile(searchPlayer(well));
          out.healthy = document.querySelectorAll('#modal .pf-inj').length;
          return out; }""")
        assert got["has"], got
        assert got["cls"].endswith({"OUT": "out", "D": "d", "Q": "q"}[got["want"]["s"]])
        assert got["note"] == got["want"]["note"]
        assert got["healthy"] == 0
        assert got["inWho"] and got["afterId"] and got["belowId"], "a line of the name block, under the identity"
        assert page.evaluate("document.documentElement.scrollWidth") <= size[0]
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
    assert [b.inner_text() for b in modal.locator("[data-pftab]").all()] == ["SEASON", "USAGE", "PROPS", "MATCHUP"]
    # Season opens first (2026-09-28): his points and his schedule, nothing from another pane.
    assert modal.locator(".pf-season").count() == 1
    assert "PROJECTION" in modal.inner_text()
    assert modal.locator(".pf-zones").count() == 0
    tab(page, "usage")
    # Usage: target depth, red zone, middle vs outside.
    assert modal.locator(".pf-season").count() == 0
    assert modal.locator(".pf-sec", has_text="Target depth").locator(".pf-zone").count() == 4
    assert "31% · 4 of 13" in modal.locator(".pf-sec", has_text="Red zone").inner_text()
    assert modal.locator(".pf-rank").count() == 0
    tab(page, "matchup")
    assert modal.locator(".pf-rank").inner_text().strip() == "9th easiest of 32 for WRs"
    assert modal.locator(".pf-zones").count() == 0                         # usage is gone, not hidden
    # The pane presents the numbers (2026-09-29, David: "untested is not needed"): no amber tag,
    # no methodology citation, one card per subject.
    assert "UNTESTED" not in modal.inner_text() and "METHODOLOGY" not in modal.inner_text()
    assert modal.locator(".pf-cols > .pf-col").count() == 3
    page.keyboard.press("Escape")
    assert "on" not in modal.get_attribute("class")
    assert page.evaluate("document.activeElement.classList.contains('row')")
    row(page, "Chase Brown").click()
    # Five tabs for him, four for St. Brown above: Bio reads LIVE_PEDIGREE alone, and the
    # fixture has a pedigree record for this back and none for that receiver. A pane with
    # nothing in it draws no button rather than opening on an empty panel. The last pane read
    # (Matchup, above) is not carried over: every player opens on Season.
    assert [b.inner_text() for b in modal.locator("[data-pftab]").all()] == ["SEASON", "USAGE", "PROPS", "MATCHUP", "BIO"]
    assert modal.locator("[data-pftab='season']").get_attribute("aria-selected") == "true"
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
def test_the_strip_says_how_good_and_how_used(browser, page_file):
    """The strip under the head (2026-09-28): rank by points per game, ppg, role share, snaps, all
    LIVE_POOL. The share is the one pool.py plots for his position -- carries for a back, targets
    for a receiver -- and a cell with no source is left out, so a player the pool does not carry
    shows no strip rather than four dashes. The rank left the identity line for it."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    page.evaluate("VIEW='espn'; render()")
    row(page, "Chase Brown").click()
    cells = page.locator("#modal .pf-lede-c")
    assert [c.locator("b").inner_text() for c in cells.all()] == ["RB1", "17.4", "62%", "71%"]
    assert [c.locator(".pf-lede-l").inner_text() for c in cells.all()] == ["RANK", "PPG", "CARRIES", "SNAPS"]
    assert "RB1" not in page.locator("#modal .pf-who .lbl").inner_text()   # one home for the rank
    page.keyboard.press("Escape")
    row(page, "George Kittle").click()
    assert page.locator("#modal .pf-lede-l").nth(2).inner_text() == "TARGETS"
    page.keyboard.press("Escape")
    page.evaluate("VIEW='yahoo'; render()")
    row(page, "Amon-Ra St. Brown").click()                  # not in the fixture pool
    assert page.locator("#modal .pf-lede").count() == 0
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_season_lists_every_week_played_and_to_come(browser, page_file):
    """The Season pane (2026-09-28): one row per week of his club's schedule. A played week shows
    his points and his line; the first week still to come is the lime row with the kickoff and the
    projection; a week with games for everyone but his club and no pedigree bye is left out, not
    called a bye. The opponent carries its rank against his position, 1st allowing the most."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    page.evaluate("VIEW='espn'; render()")
    row(page, "George Kittle").click()
    season = page.locator("#modal .pf-season")
    rows = season.locator(".ss-row")
    kinds = [r.get_attribute("class").replace("ss-row ", "") for r in rows.all()]
    assert kinds == ["ss-head", "ss-played", "ss-played", "ss-next", "ss-total"]
    assert rows.nth(1).locator(".ss-pts").inner_text() == "12.1"
    nxt = season.locator(".ss-next")
    assert nxt.locator(".ss-opp").inner_text() == "KC"
    assert nxt.locator(".ss-date").inner_text() == "Mon 1:25 PM"
    assert nxt.locator(".ss-pts").inner_text() == "13.6"
    assert nxt.locator(".ss-note").inner_text() == "projected · TE1 this week"
    # The When column is one column for every row: the dates played line up with the kickoffs.
    lefts = page.evaluate("""() => [...document.querySelectorAll('#modal .pf-season .ss-date')]
      .map(e => Math.round(e.getBoundingClientRect().left))""")
    assert len(set(lefts)) == 1, lefts
    assert season.locator(".ss-total .ss-pts").inner_text() == "21.5"
    page.keyboard.press("Escape")
    page.evaluate("VIEW='yahoo'; render()")
    row(page, "Jahmyr Gibbs").click()
    at_sea = page.locator("#modal .ss-row.gl-open .ss-rk")
    assert at_sea.inner_text() == "22nd"                    # SEA allows RBs the 11th-fewest of 32
    assert page.locator("#modal .ss-row.ss-bye").count() == 0   # his bye is week 6, not week 3
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_season_is_one_line_a_week_on_a_phone(browser, page_file):
    """No sideways scroll and no blocks of chips: a phone reads each week as box-score shorthand in
    one cell, and the stat columns are not drawn beside it."""
    ctx, page, errors = open_page(browser, page_file, (360, 800))
    page.evaluate("VIEW='yahoo'; render()")
    row(page, "Jahmyr Gibbs").click()
    first = page.locator("#modal .ss-row.ss-played").first
    assert first.locator(".ss-line").inner_text() == "29-156-2 · 5-30"
    assert first.locator(".ss-stat").first.is_visible() is False
    heads = page.evaluate("""() => [...document.querySelectorAll('#modal .ss-row')].slice(0, 3)
      .map(r => Math.round(r.querySelector('.ss-pts').getBoundingClientRect().right))""")
    assert len(set(heads)) == 1, heads                      # the points line up under their head
    assert page.evaluate("document.querySelector('#modal').scrollWidth <= document.querySelector('#modal').clientWidth")
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_owners_name_each_leagues_team(browser, page_file):
    """One pill per league (2026-09-28): the team that rosters him by name, or free agent when every
    team in that league is loaded and none has him. "Yours" is the reader's own team only."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))      # David's browser, Yahoo team
    row(page, "Amon-Ra St. Brown").click()
    pills = page.locator("#modal .pf-own")
    text = lambda: [re.sub(r"\s+", " ", p.inner_text()).strip() for p in pills.all()]  # noqa: E731
    assert text() == ["Yahoo Yours", "ESPN Free agent", "AYO Free agent"]   # the third league, 2026-09-29
    assert "mine" in pills.first.get_attribute("class")
    assert "free" in pills.nth(1).get_attribute("class")
    page.keyboard.press("Escape")
    # A leaguemate's browser: no owner link, no team picked. The same pill names the team.
    page.evaluate("localStorage.setItem('tw-owner', ''); localStorage.removeItem('tw-team')")
    row(page, "Amon-Ra St. Brown").click()
    assert text() == ["Yahoo Chat Take the Wheel", "ESPN Free agent", "AYO Free agent"]
    assert "mine" not in pills.first.get_attribute("class")
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_desktop_panes_sit_side_by_side_and_a_phone_stacks_them(browser, page_file):
    """2026-09-29, David: Usage and Matchup "should fit without scrolling", Props two to a row. On
    a desktop the blocks share a top edge; on a phone the same blocks stack in the same order. The
    league tags are grey, not the leagues' brand colours, and a played week carries no play mark."""
    tops = lambda sel: page.evaluate(  # noqa: E731
        f"[...document.querySelectorAll({sel!r})].map(e => [e.getBoundingClientRect().top, e.getBoundingClientRect().bottom])")
    for w, h, side in [(1400, 900, True), (360, 800, False)]:
        ctx, page, errors = open_page(browser, page_file, (w, h))
        row(page, "Amon-Ra St. Brown").click()
        tab(page, "usage")
        a, b = tops("#modal .pf-tabpane > *")[:2]
        assert (a[0] == b[0]) if side else (b[0] >= a[1])
        # His bar wears his position's colour; his teammates' stay grey (2026-09-29).
        bar = "e => getComputedStyle(e).backgroundColor"
        assert page.locator("#modal .pf-tm.me .pf-tm-bar i").evaluate(bar) \
            != page.locator("#modal button.pf-tm .pf-tm-bar i").first.evaluate(bar)
        tab(page, "matchup")
        cols = tops("#modal .pf-cols > .pf-col")
        assert len(cols) >= 2
        assert (cols[0][0] == cols[1][0]) if side else (cols[1][0] >= cols[0][1])
        bgs = page.locator("#modal .pf-own-l").evaluate_all("els => els.map(e => getComputedStyle(e).backgroundColor)")
        assert len(bgs) == 3 and len(set(bgs)) == 1                # one grey for every league (AYO the third), no brand colour
        tab(page, "season")
        assert page.locator("#modal .ss-row svg").count() == 0
        # A draft pick sits by the league it belongs to, not at the far edge of the pane (David,
        # 2026-09-29: "on desktop we stretch out info").
        page.keyboard.press("Escape")
        row(page, "Chase Brown").click()
        tab(page, "bio")
        gap = page.evaluate("""(() => { const r = document.querySelector('#modal .pf-facts > div');
          return r.querySelector('dd').getBoundingClientRect().right - r.querySelector('dt').getBoundingClientRect().left; })()""")
        assert gap <= 560
        assert errors == []
        ctx.close()


@pytest.mark.render
def test_an_owner_pill_opens_that_teams_roster(browser, page_file):
    """A team's pill is a way to that team's roster (2026-09-28, for looking up a trade). It is a
    look, not a pick: the reader's own team is still theirs afterwards, and Back returns to the
    view they came from. A free agent's pill goes nowhere."""
    ctx, page, errors = open_any_page(browser, page_file, (1400, 900))
    drive(page, go("usage"))                                  # somewhere that is not a roster
    page.evaluate("openProfile({n: 'Chase Brown', pos: 'RB', team: 'CIN', slug: 'chase-brown'})")
    pill = page.locator("#modal button.pf-own", has_text="ESPN")   # the ESPN team, not the one in view
    assert pill.count() == 1
    key = pill.get_attribute("data-ownteam")
    assert key.startswith("espn") and page.evaluate("VIEW") == "yahoo"
    pill.click()
    page.wait_for_function("location.hash === '#roster'")
    assert "on" not in page.locator("#modal").get_attribute("class")
    assert page.evaluate("VIEW") == key
    assert page.evaluate("myTeamLoad()") == "yahoo"           # the reader's pick is untouched
    page.go_back()
    page.wait_for_function("location.hash === '#usage'")
    page.evaluate("openProfile({n: 'Amon-Ra St. Brown', pos: 'WR', team: 'DET', slug: 'amonra-st-brown'})")
    assert page.locator("#modal span.pf-own.free").count() == 2   # free agent in ESPN and AYO: not a button
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_archetype_sits_in_the_head_and_explains_itself_in_usage(browser, page_file):
    """2026-09-29, David: the archetype "should be on the player profile" (it showed only under a
    Leaders comparison pick). His two words are tags with an icon in the head; a tap opens Usage
    on the block that says what each means and the numbers that produced it. A word the model
    withholds is no tag, and its reason stands in its place in Usage."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    who = page.evaluate("""(() => {
      const arch = (LIVE_ARCHETYPE && LIVE_ARCHETYPE.players) || {};
      const row = slug => LIVE_GAMELOG.rows.find(r => r.slug === slug);
      const pick = f => { const s = Object.keys(arch).find(k => f(arch[k]) && row(k)); if (!s) return null;
        const r = row(s); return {n: r.n, pos: r.pos, team: r.team, slug: s, role: arch[s].role, style: arch[s].style,
                                  role_null: arch[s].role_null}; };
      return {both: pick(a => a.role && a.style), one: pick(a => !a.role && a.style)};
    })()""")
    assert who["both"], "the fixture needs a player with both words"
    page.evaluate("p => openProfile(p)", who["both"])
    # The chips sit under his name, in one row on a desktop.
    tags = page.locator("#modal .pf-who .pf-arch .pf-arch-slot")
    assert tags.count() == 2 and tags.first.is_visible()
    assert tags.nth(0).bounding_box()["y"] == tags.nth(1).bounding_box()["y"]
    assert tags.nth(0).locator(".pf-sk-role svg").count() == 1            # a tile on every chip, stone by field
    assert tags.nth(1).locator(".pf-sk-style svg").count() == 1
    role_word = page.evaluate("v => bdRoleWord(v)", who["both"]["role"])
    assert tags.nth(0).inner_text().strip().upper() == role_word.upper()
    tags.nth(1).click()
    assert page.locator("#modal [data-pftab='usage']").get_attribute("aria-selected") == "true"
    block = page.locator("#modal .pf-sec-arch")
    assert block.count() == 1
    assert block.locator(".bd-mean").count() == 2                         # each word says what it means
    assert block.locator(".bd-ev").count() >= 1                           # and what produced it
    # Starting a row, it takes the whole row with Role and Style side by side; beside a block, stacked.
    starts_row = block.evaluate("e => [...e.parentNode.children].indexOf(e) % 2 === 0")
    fields = block.locator(".pf-arch-two > .bd-fld")
    assert (fields.nth(0).bounding_box()["y"] == fields.nth(1).bounding_box()["y"]) == starts_row
    if who["one"]:
        page.evaluate("p => openProfile(p)", who["one"])
        assert page.locator("#modal .pf-head .pf-arch .pf-arch-slot").count() == 1
        tab(page, "usage")
        assert who["one"]["role_null"] in page.locator("#modal .pf-sec-arch .bd-why").first.inner_text()
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_props_draws_his_last_games_against_the_line(browser, page_file):
    """2026-09-29, David: "see his receptions, yds, tds as bar chart in the past X games". A player
    with a market log gets a Props tab: one chart per market he records, the leg sheet's bars, lime
    where he went over this week's line -- the over, whatever side the model picks. No log, no tab."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    who = page.evaluate("""(() => {
      const logs = (LIVE_MARKET && LIVE_MARKET.logs) || {};
      const p = PROPS.find(r => ['WR', 'TE', 'RB'].includes(r.pos) && r.mkt !== 'TD' && logs[r.slug || slugOf(r.n)]);
      const none = LIVE_GAMELOG.rows.find(r => !logs[r.slug] && r.pos !== 'QB');
      return {p: {n: p.n, pos: p.pos, team: p.team, slug: p.slug || slugOf(p.n)}, mkt: p.mkt,
              line: legSide(p).line, vals: logs[p.slug || slugOf(p.n)].v[p.mkt],
              none: none && {n: none.n, pos: none.pos, team: none.team, slug: none.slug}};
    })()""")
    page.evaluate("p => openProfile(p)", who["p"])
    tab(page, "props")
    heads = [s.inner_text() for s in page.locator("#modal .pf-sec-prop .lbl").all()]
    mkt_name = page.evaluate("m => MKT[m]", who["mkt"]).upper()
    assert mkt_name in heads
    sec = page.locator("#modal .pf-sec-prop", has=page.locator(".lbl", has_text=re.compile(f"^{re.escape(mkt_name)}$", re.I)))
    assert sec.locator(".ls-bar").count() == len(who["vals"])
    over = sum(1 for v in who["vals"] if v > who["line"])
    assert sec.locator(".ls-bar.hit").count() == over
    assert sec.locator(".ls-cap b").inner_text().startswith(f"Over {who['line']} in {over}/{len(who['vals'])}")
    if who["none"]:
        page.evaluate("p => openProfile(p)", who["none"])
        assert page.locator("#modal [data-pftab='props']").count() == 0
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_usage_opens_on_his_share_of_his_own_team(browser, page_file):
    """2026-09-29, David: usage "should have his teammates there for comparison". Usage leads with
    his share of his team's targets (a back: carries, then targets) from the game log, the top five
    by volume with him among them, the rest as one row. A teammate's row opens that profile; a
    passer gets no block."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    page.evaluate("openProfile({n: 'Amon-Ra St. Brown', pos: 'WR', team: 'DET', slug: 'amonra-st-brown'})")
    tab(page, "usage")
    sec = page.locator("#modal .pf-sec-team")
    assert sec.count() == 1
    assert page.locator("#modal .pf-tabpane > section").first.get_attribute("class").endswith("pf-sec-team")
    want = page.evaluate("""(() => { const d = teamShareRows('DET', 'tgt');
      const me = d.rows.findIndex(r => r.slug === 'amonra-st-brown');
      return {me, v: d.rows[me].v, total: d.total, n: d.rows.length}; })()""")
    lead = sec.locator(".pf-lead").first.inner_text()
    assert f"{want['v']} of {want['total']}" in lead and "targets" in lead
    assert sec.locator(".lbl").inner_text() == "DET TARGETS"                # the head names the stat
    pcts = [int(b.inner_text().rstrip("%")) for b in sec.locator(".pf-tm > b").all()]
    assert abs(sum(pcts) - 100) <= len(pcts)                  # the rows are the whole team, give or take rounding
    named = sec.locator(".pf-tm:not(.rest) > b").all()
    vals = [int(b.inner_text().rstrip("%")) for b in named]
    assert vals == sorted(vals, reverse=True)
    assert sec.locator(".pf-tm.me").count() == 1
    assert sec.locator(".pf-tm.me").evaluate("e => e.tagName") == "DIV"   # his own row goes nowhere
    mate = sec.locator("button.pf-tm").first
    slug = mate.get_attribute("data-tmslug")
    mate.click()
    name = page.evaluate("s => LIVE_GAMELOG.rows.find(r => r.slug === s).n", slug)
    assert page.locator("#pf-title").inner_text().upper() == name.upper()
    page.evaluate("openProfile({n: 'Josh Allen', pos: 'QB', team: 'BUF', slug: 'josh-allen'})")
    if page.locator("#modal [data-pftab='usage']").count():
        tab(page, "usage")
    assert page.locator("#modal .pf-sec-team").count() == 0
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_sphere_turns_rests_and_stops(browser, page_file):
    """STYLE.md rule 1 as rewritten on 2026-09-28: a tap cue may move, slowly, only while it can be
    seen, resting where its data reads, and never under reduced motion. The sphere starts turning as
    the profile opens (2026-09-30; it used to hold still 2 s first) and rests after the turn; a shut
    profile stops it."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    page.emulate_media(reduced_motion="no-preference")
    row(page, "Amon-Ra St. Brown").click()
    yaw = "ORB_STATE.get(document.querySelector('#modal .pf-orb')).yaw"
    page.wait_for_timeout(600)
    a = page.evaluate(yaw)
    page.wait_for_timeout(400)
    assert 0 < a < page.evaluate(yaw)
    page.keyboard.press("Escape")
    page.wait_for_timeout(100)
    shut = page.evaluate(yaw)
    page.wait_for_timeout(500)
    assert page.evaluate(yaw) == shut
    page.emulate_media(reduced_motion="reduce")
    row(page, "Amon-Ra St. Brown").click()
    page.wait_for_timeout(2600)
    assert page.evaluate(yaw) == 0
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_sphere_opens_the_sheet_over_the_profile(browser, page_file):
    """The radar is a sphere in the head (orb.js) and a tap opens the flat sheet over the profile.
    Escape and Back close the sheet alone and put the reader back in the profile, on the pane they
    left; the sphere's caption is the rank the sheet opens on."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    row(page, "Amon-Ra St. Brown").click()
    orb = page.locator("#modal .pf-orb")
    rank = page.evaluate("rankMark(sheetRank('WR', 'wopr', 'amonra-st-brown'))")
    assert re.sub(r"\s+", " ", orb.inner_text()).strip() == f"{rank} TARGET SHARE"
    assert page.locator("#modal .pf-radar").count() == 0      # not drawn until asked for
    tab(page, "usage")
    sheet(page)
    assert page.locator("#modal .pf-orblayer .pf-radar").count() == 1
    assert page.locator("#modal .pf-orbsheet .pf-lr.on .pf-lr-n").inner_text() == "Target share"
    page.keyboard.press("Escape")
    assert page.locator("#modal .pf-orblayer").count() == 0
    assert "on" in page.locator("#modal").get_attribute("class")
    assert page.locator("#modal [data-pftab='usage']").get_attribute("aria-selected") == "true"
    assert page.evaluate("document.activeElement.classList.contains('pf-orb')")
    sheet(page)
    page.go_back()
    assert page.locator("#modal .pf-orblayer").count() == 0
    assert "on" in page.locator("#modal").get_attribute("class")
    page.evaluate("VIEW='espn'; render()")
    page.go_back()                                            # the profile's own entry
    row(page, "George Kittle").click()                        # no sheet row: no sphere
    assert page.locator("#modal .pf-orb").count() == 0
    assert errors == []
    ctx.close()


@pytest.mark.render
@pytest.mark.parametrize("viewport", [(360, 740), (1400, 900)])
def test_the_sheet_holds_still_under_a_tap_and_a_scroll(browser, page_file, viewport):
    """2026-09-29, David: tapping a stat "will expand the shape of the container which causes the
    content to jump", and "scrolling or swiping on this modal will move the content behind it".
    The sheet opens centred and keeps that top (orbsheet.js orbPin), so a fold grows it downward;
    a wheel on the scrim or on a sheet with nothing to scroll moves neither the profile nor the page."""
    ctx, page, errors = open_page(browser, page_file, viewport)
    row(page, "Amon-Ra St. Brown").click()
    sheet(page)
    radar = page.locator("#modal .pf-orbsheet .pf-radar")
    top = radar.bounding_box()["y"]
    page.locator("#modal .pf-orbsheet .pf-lr summary").last.click()
    assert page.locator("#modal .pf-orbsheet .pf-lr[open]").count() == 1
    assert radar.bounding_box()["y"] == pytest.approx(top, abs=1)
    under = "[document.querySelector('#modal .dr-body').scrollTop, scrollY]"
    before = page.evaluate(under)
    box = page.locator("#modal .pf-orbscrim").bounding_box()
    page.mouse.move(box["x"] + 4, box["y"] + 4)
    page.mouse.wheel(0, 600)
    page.wait_for_timeout(100)
    assert page.evaluate(under) == before
    # A sideways swipe on the scrim leaves the profile's tab where it was (modal.js up()).
    selected = "document.querySelector('#modal [data-pftab][aria-selected=true]').dataset.pftab"
    was = page.evaluate(selected)
    page.evaluate("""(() => { const el = document.querySelector('#modal .pf-orbscrim');
      const at = x => [new Touch({identifier: 1, target: el, clientX: x, clientY: 20})];
      el.dispatchEvent(new TouchEvent('touchstart', {bubbles: true, touches: at(300), changedTouches: at(300)}));
      el.dispatchEvent(new TouchEvent('touchend', {bubbles: true, touches: [], changedTouches: at(120)})); })()""")
    assert page.evaluate(selected) == was
    assert page.locator("#modal .pf-orblayer").count() == 1
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_an_elite_stat_glows(browser, page_file):
    """Ranked and over the position's elite bar (sheet.js sheetElite): the ladder row and the radar
    label and vertex carry `elite`, and nothing else does."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    row(page, "Amon-Ra St. Brown").click()
    sheet(page)
    want = page.evaluate("""(() => { const s = sheetFor({slug: 'amonra-st-brown'});
      return s.axes.filter(a => sheetElite(s, a, sheetRank(s.pos, a.id, s.row.slug))).map(a => a.id).sort(); })()""")
    assert want, "the fixture needs an elite stat for this receiver"
    for sel in (".pf-lr.elite", ".pf-radar-l.elite", ".pf-radar-dot.elite"):
        got = sorted(page.eval_on_selector_all(f"#modal .pf-orbsheet {sel}", "els => els.map(e => e.dataset.col)"))
        assert got == want, sel
    glow = page.eval_on_selector("#modal .pf-orbsheet .pf-lr.elite .pf-lr-bar i", "e => getComputedStyle(e).boxShadow")
    assert glow != "none"
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
    labels = [d.inner_text().upper() for d in page.locator("#modal .pf-facts dt").all()]
    assert page.evaluate("TEAMS.yahoo.name").upper() in labels
    assert page.evaluate("TEAMS.espn.name").upper() in labels
    # Each league's row leads with its tag, the owner pills' own word (2026-09-29).
    assert page.locator("#modal .pf-facts dt[data-league='Yahoo']").count() == 1
    assert page.locator("#modal .pf-facts dt[data-league='ESPN']").count() == 1
    assert "Rd 1.01 · by Big Salty" in facts
    assert "Rd 1.02 · by Team Minh" in facts
    page.keyboard.press("Escape")
    row(page, "Chase Brown").click()
    tab(page, "bio")
    facts = page.locator("#modal .pf-tabpane .pf-facts").inner_text()
    assert "Rd 3.07 · by Big Salty" in facts
    assert page.evaluate("TEAMS.yahoo.name").upper() not in [d.inner_text().upper() for d in page.locator("#modal .pf-facts dt").all()]
    page.keyboard.press("Escape")
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_fantasy_tier_leads_the_strip(browser, page_file):
    """"RB4": his rank by points per game, season to date, among every RB in LIVE_POOL
    (watch.json) -- said the way a fantasy reader says it, never as a WR1/2/3 tier that reads
    like a depth chart. It sat on the identity line until 2026-09-28 and leads the strip since;
    the line keeps position, club and bye."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    row(page, "Chase Brown").click()
    head = page.locator("#modal .pf-who .lbl").inner_text().upper()
    rank, of, _tied = page.evaluate("ppgRank({slug: 'chase-brown', pos: 'RB'})")
    # One separator for the whole line, and the same one the rest of the page uses.
    assert head == "RB · CIN · BYE 10"
    assert "|" not in head
    assert page.locator("#modal .pf-lede-c b").first.inner_text() == f"RB{rank}"
    assert of == page.evaluate("LIVE_POOL.players.filter(r => r.pos === 'RB' && r.ppg !== null).length")
    page.keyboard.press("Escape")
    row(page, "Amon-Ra St. Brown").click()          # not in the fixture pool: no rank anywhere
    assert page.locator("#modal .pf-who .lbl").inner_text().upper() == "WR · DET"
    assert page.locator("#modal .pf-lede").count() == 0
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
    tab(page, "usage")
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
    tab(page, "usage")
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
      const lad = (who) => { const d = document.createElement('div'); d.innerHTML = ladderHTML(who, 'gl_pct'); return d; };
      const d = lad(s), row = d.querySelector('[data-col="gl_pct"]');
      const d2 = lad(sheetFor({slug: 'josh-allen'})), row2 = d2.querySelector('[data-col="gl_pct"]');
      const ranked = [...d.querySelectorAll('.pf-lr')].map(r => !!sheetRank('QB', r.dataset.col, 'lamar-jackson'));
      return {rank: sheetRank('QB', 'gl_pct', 'lamar-jackson'), allen: sheetRank('QB', 'gl_pct', 'josh-allen'),
              facts: row.querySelector('.pf-lr-facts').textContent, floor: row.querySelector('.pf-lr-floor').textContent,
              dim: row.querySelector('.pf-lr-v').className, have: row.querySelector('.pf-lr-rk').textContent,
              last: ranked.slice(ranked.indexOf(false)).every(x => !x),
              allenFacts: row2.querySelector('.pf-lr-facts').textContent, allenFloor: row2.querySelectorAll('.pf-lr-floor').length,
              allenRk: row2.querySelector('.pf-lr-rk b').textContent,
              held: bdThinOut('QB', 'gl_pct', -1).map(r => sampleShort(r, a))};
    })()""")
    assert got["rank"] is None and got["allen"] is not None
    assert "1 of 4 team carries inside the 5" in got["facts"]
    # Why there is no rank, in words: the floor, and what a rate on fewer would be.
    assert got["floor"] == "Ranked from 5 team carries inside the 5: a rate on fewer is one game's noise, not a season."
    assert got["dim"] == "pf-lr-v dim"
    assert got["have"] == "4 of 5team carries inside the 5"   # his sample against the floor, not a rank
    assert got["last"]                                       # unranked rows sit under every ranked one
    assert "3 of 5 team carries inside the 5" in got["allenFacts"] and got["allenFloor"] == 0
    assert got["allenRk"].startswith("#")
    assert got["held"] == ["3/4", "2/3", "1/4"]           # C. Ward 75%, T. Shough 66.7%, L. Jackson 25%
    assert not errors
    ctx.close()


def test_stat_sheet_draws_the_positions_own_axes(browser, page_file):
    """ff-jarvis's `sheet.axes` drives the shape: six for a receiver, none of them a raw count
    the Grid already shows. Every number is his season rank among the position ("#3", "#3*" on a
    tie), first place at the rim. Each label is a button, and the ladder under the chart lists
    every stat best first; a label and its row light together, and the row folds out the
    definition and the elite gap."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    row(page, "Amon-Ra St. Brown").click()
    sheet(page)
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
    assert page.locator("#modal .pf-sheet .pf-cap").count() == 0
    # The ladder under the chart (2026-09-29): every stat at once, best first, each row with its
    # own denominator (everyone with a target, but only those with routes).
    rows = page.locator("#modal .pf-lr")
    assert rows.count() == len(axes)
    order = [r.get_attribute("data-col") for r in rows.all()]
    pct = page.evaluate("""cols => cols.map(c => { const rk = sheetRank('WR', c, 'amonra-st-brown');
      return rk ? ladderPct(rk) : -1; })""", order)
    assert pct == sorted(pct, reverse=True)
    wopr = page.locator("#modal .pf-lr[data-col='wopr']")
    assert "on" in wopr.get_attribute("class")
    assert wopr.locator(".pf-lr-rk").inner_text().split() == [mark, "of", str(of)]
    # Folded: the definition is a tap away, not a paragraph in the way of the numbers.
    assert not wopr.locator(".pf-lr-def").is_visible()
    wopr.locator("summary").click()
    # The gap, not the threshold: "elite >= 0.00" printed in red said the elite bar was the bad
    # thing, when what is red is him being under it. The colour agrees with the sign.
    assert wopr.locator(".pf-lr-d").inner_text() == "0.11 over the elite bar (0.70)"
    assert wopr.locator(".pf-lr-d").get_attribute("class").endswith("up")
    # And the initials are defined, with a second clause on what to do with the number.
    assert "air yards" in wopr.locator(".pf-lr-def").inner_text()
    assert "predictor" in wopr.locator(".pf-lr-why").inner_text()
    assert "on" in page.locator("#modal .pf-radar-l", has_text="Target share").get_attribute("class")
    assert radar.locator("circle.pf-radar-dot.on").get_attribute("data-col") == "wopr"
    # A label tap lights the chart and the row together and opens that row alone.
    page.locator("#modal .pf-radar-l", has_text="Yds/route").click()
    yprr = page.locator("#modal .pf-lr[data-col='yprr']")
    assert "on" in yprr.get_attribute("class") and yprr.get_attribute("open") is not None
    assert wopr.get_attribute("open") is None
    assert "on" not in page.locator("#modal .pf-radar-l", has_text="Target share").get_attribute("class")
    assert radar.locator("circle.pf-radar-dot.on").get_attribute("data-col") == "yprr"
    yprr_of = page.evaluate("sheetRank('WR', 'yprr', 'amonra-st-brown')")[1]
    assert yprr.locator(".pf-lr-rk small").inner_text() == f"of {yprr_of}"
    # And a row tap moves the chart.
    page.locator("#modal .pf-lr[data-col='rz_tgt'] summary").click()
    page.wait_for_selector("#modal circle.pf-radar-dot.on[data-col='rz_tgt']", timeout=2000)   # toggle fires a task later
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
    assert wins == {"DET TARGETS": "2 wk", "TARGET DEPTH": "2 wk", "RED ZONE": "2 wk"}   # .lbl uppercases in the render
    # And per stat, in its ladder row's fold. Three states, because the fixture has no weekly rows
    # for the sheet stats and that is itself one of them.
    sheet(page)
    page.locator("#modal .pf-radar-l", has_text="Yds/route").click()
    facts = page.locator("#modal .pf-lr[data-col='yprr'] .pf-lr-facts span").last
    assert facts.inner_text() == "2 gm"                     # no weekly rows: games, no window
    plant = """(weeks) => {
      const row = USAGE.rows.find(r => r.slug === 'amonra-st-brown');
      USAGE.rows = USAGE.rows.filter(r => r.slug !== 'amonra-st-brown');
      weeks.forEach(wk => USAGE.rows.push({...row, wk, v: {...row.v, yprr: 1.5 + wk}}));
      const s = sheetFor({slug: 'amonra-st-brown'});
      return ladderWindow(s, statWeeks('amonra-st-brown', 'yprr'));
    }"""
    assert page.evaluate(plant, [1, 2]) == "wk 1–2"         # two weeks: the range, no games
    # Now as heatradar actually publishes it: week 1 only, while his other stats have two.
    assert page.evaluate(plant, [1]) == "wk 1"
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
    sheet(page)
    radar = page.locator("#modal .pf-radar")
    assert radar.locator("polygon.pf-radar-shape").count() == 1     # six axes: a real shape
    assert radar.locator(".pf-radar-note").count() == 0
    page.keyboard.press("Escape")                                   # the sheet
    page.keyboard.press("Escape")                                   # the profile
    # Strip four of his six axes and reopen: two points left, so no polygon and a count instead.
    page.evaluate("""() => {
      const r = USAGE.sheet.rows.find(x => x.slug === 'amonra-st-brown');
      ['route_pct', 'tprr', 'yprr', 'fdrr'].forEach(k => { r.v[k] = null; });
      for (const k in SHEET_BY) delete SHEET_BY[k];   // memoised per position+axis
    }""")
    row(page, "Amon-Ra St. Brown").click()
    sheet(page)
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
    assert page.locator("#modal .pf-orb.pos-rb").count() == 1   # the sphere wears the tint too
    sheet(page)
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
    assert "UNTESTED" not in text                             # tags cut 2026-09-29 (David)
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
    assert "UNTESTED" not in text                             # tags cut 2026-09-29 (David)
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
    assert "UNTESTED" not in text                             # tags cut 2026-09-29 (David)
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
    # The matchup pane needs LIVE_PROFILES, so it draws no tab and the notice says why once. The
    # Season table, the projection, the team share and the stat sheet each read their own source
    # (LIVE_GAMELOG/LIVE_PROJECTIONS/LIVE_USAGE) and still render -- a player with no matchup
    # profile is not blank.
    tabs = [b.get_attribute("data-pftab") for b in page.locator("#modal [data-pftab]").all()]
    assert tabs == ["season", "usage", "props"]
    assert page.locator("#modal .pf-season").count() == 1
    assert page.locator("#modal .pf-sec").count() == 1         # the projection
    tab(page, "usage")
    assert [s.get_attribute("class").split()[-1] for s in page.locator("#modal .pf-tabpane > section").all()] == ["pf-sec-team", "pf-sec-arch"]
    sheet(page)
    assert page.locator("#modal .pf-radar").count() == 1
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_compare_picks_from_the_profile_and_draws_one_radar(browser, page_file):
    """Compare (2026-09-30): the head's button opens the picker over the profile with the reader's
    own team first; two ticks and Compare draw three chips, one shape each on one radar, and the
    rows; Back closes the whole layer and leaves the profile open."""
    ctx, page, errors = open_page(browser, page_file, (360, 800))
    row(page, "Amon-Ra St. Brown").click()
    page.locator("#modal [data-compare]").click()
    assert page.locator("#modal .cmp-layer").count() == 1
    rows = page.locator("#modal .cmp-row")
    assert rows.count() >= 2
    assert page.locator("#modal .cmp-go").is_disabled()
    rows.nth(0).click()
    rows = page.locator("#modal .cmp-row")
    rows.nth(1).click()
    assert page.locator("#modal .cmp-row.on").count() == 2
    page.locator("#modal [data-cmp=go]").click()
    assert page.locator("#modal .cmp-chip:not(.add)").count() == 3
    assert page.locator("#modal .cmp-stat").count() == 5
    shapes = page.locator("#modal .cmp-shape").count()
    assert shapes == 3 or page.locator("#modal .cmp-note").count() == 1
    assert page.evaluate("!!document.activeElement.closest('.cmp-sheet')")
    page.go_back()
    page.wait_for_timeout(200)
    assert page.locator("#modal .cmp-layer").count() == 0
    assert page.locator("#modal.on").count() == 1
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_compare_search_reaches_any_player(browser, page_file):
    """A search pick joins the set and the lists come back; the box never keeps a stale query."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    row(page, "Amon-Ra St. Brown").click()
    page.locator("#modal [data-compare]").click()
    page.locator("#cmp-q").fill("kittle")
    hit = page.locator("#modal .cmp-row", has_text="Kittle")
    assert hit.count() == 1
    hit.click()
    assert page.locator("#cmp-q").input_value() == ""
    assert page.locator("#modal .cmp-row.on", has_text="Kittle").count() == 1
    page.keyboard.press("Escape")
    assert page.locator("#modal .cmp-layer").count() == 0
    assert page.locator("#modal.on").count() == 1
    assert errors == []
    ctx.close()


def test_the_sheet_keeps_the_fluke_filter():
    """ff-jarvis's shrunk value and elite list (METHODOLOGY 12.68) reach the page; a row without
    them keeps el null, which is how the page knows to fall back to the raw test."""
    import usage
    block = {"axes": {"WR": [{"id": "tprr", "elite": 25}]},
             "rows": [{"name": "A B", "pos": "WR", "v": {"tprr": 30}, "ev": {"tprr": 24}, "el": []},
                      {"name": "C D", "pos": "WR", "v": {"tprr": 30}}]}
    rows = usage._sheet(block, lambda n: n.lower().replace(" ", "-"))["rows"]
    assert (rows[0]["ev"], rows[0]["el"]) == ({"tprr": 24}, [])
    assert (rows[1]["ev"], rows[1]["el"]) == ({}, None)


@pytest.mark.render
def test_elite_reads_the_fluke_filter(browser, page_file):
    """St. Brown's fixture row clears the WOPR and TPRR bars raw, but the filter keeps WOPR only:
    WOPR glows, TPRR does not and says the sample is too small, and a bar with no history behind
    it is dotted and named."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    row(page, "Amon-Ra St. Brown").click()
    sheet(page)
    assert "elite" in page.locator("#modal .pf-lr[data-col='wopr']").get_attribute("class")
    tprr = page.locator("#modal .pf-lr[data-col='tprr']")
    assert "elite" not in tprr.get_attribute("class")
    tprr.locator("summary").click()
    assert "too few games" in tprr.inner_text()
    assert "published analyst standard" in tprr.inner_text()
    assert "prov" in page.locator("#modal .pf-radar-bar[data-col='tprr']").get_attribute("class")
    assert "prov" not in page.locator("#modal .pf-radar-bar[data-col='wopr']").get_attribute("class")
    assert errors == []
    ctx.close()
