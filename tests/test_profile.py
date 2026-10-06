"""The player profile: its contract, its injection, the roster's matchup clause, the head and the strip. The
panes are test_profile_panes.py, the stat sheet test_profile_sheet.py, Compare test_profile_compare.py; the
tests that need navigation or Back are test_profile_journeys.py.

The profile is an overlay with no leaf, so each test mounts the roster (the surface that opens it) and
works through pages/profile.py. The fixture (tests/fixtures/data/player_profiles.json) spreads the matchup
rank (factor rank 1 = toughest, so "Nth easiest" = 33 - rank): Higgins 8th easiest (green), St. Brown 9th
(plain), Chase Brown 17th (plain), Kittle 25th (red), Gibbs on a bye. Burrow and Purdy have no profile.
Red zone: Kittle 3 of 8 team targets (counts, under 10), St. Brown 31% · 4 of 13 (share).
"""
import copy
import json

import pytest

import build
import contract
from component import mount  # noqa: F401  (the fixture)
from conftest import FIXTURES
from pages.roster import on_roster
from test_build import injected

PROFILES = json.loads((FIXTURES / "data" / "player_profiles.json").read_text(encoding="utf-8"))
MARKET_STOCK = json.loads((FIXTURES / "data" / "market_stock.json").read_text(encoding="utf-8"))
REQ = "The profile modal"
ST_BROWN = "Amon-Ra St. Brown"


@pytest.mark.req(REQ, ac="the fixture's profiles meet the contract")
def test_contract_accepts_the_fixture():
    assert contract.problems("LIVE_PROFILES", PROFILES) == []


@pytest.mark.req(REQ, ac="a profile missing its next game fails the build")
def test_contract_rejects_a_player_missing_next():
    d = copy.deepcopy(PROFILES)
    d["players"]["amonra-st-brown"].pop("next")
    assert contract.problems("LIVE_PROFILES", d) == ["LIVE_PROFILES.players['amonra-st-brown'].next"]


@pytest.mark.req(REQ, ac="a partial next game fails the build, a bye (null) does not")
def test_contract_rejects_a_partial_next_but_allows_a_bye():
    d = copy.deepcopy(PROFILES)
    d["players"]["chase-brown"]["next"].pop("tested")
    assert d["players"]["jahmyr-gibbs"]["next"] is None
    assert contract.problems("LIVE_PROFILES", d) == ["LIVE_PROFILES.players['chase-brown'].next.tested"]


@pytest.mark.req(REQ, ac="a red zone without team counts fails the build")
def test_contract_rejects_a_red_zone_without_team_counts():
    d = copy.deepcopy(PROFILES)
    d["players"]["george-kittle"]["red_zone"].pop("team_targets")
    d["players"]["chase-brown"]["red_zone"].pop("team_carries")
    assert contract.problems("LIVE_PROFILES", d) == [
        "LIVE_PROFILES.players['george-kittle'].red_zone.team_targets",
        "LIVE_PROFILES.players['chase-brown'].red_zone.team_carries",
    ]


@pytest.mark.req(REQ, ac="the build injects the profiles it was given")
def test_build_injects_the_profiles(built):
    got = injected(built.fragment)["LIVE_PROFILES"]
    assert set(got["players"]) == set(PROFILES["players"])
    assert any(line.startswith("Profiles: 5 players") for line in built.report)


@pytest.mark.req(REQ, ac="no profiles file injects null")
def test_no_profiles_file_injects_null(monkeypatch):
    monkeypatch.setattr(build, "load_profiles", lambda: None)
    b = build.render()
    assert injected(b.fragment)["LIVE_PROFILES"] is None


# ------------------------------------------------------------------ market.stock (step 5)

@pytest.mark.req(REQ, ac="the market stock fixture meets the contract")
def test_contract_accepts_the_market_stock_fixture():
    assert contract.problems("LIVE_MARKET_STOCK", MARKET_STOCK) == []


@pytest.mark.req(REQ, ac="a market row missing a field fails the build")
def test_contract_rejects_a_market_row_missing_a_field():
    d = copy.deepcopy(MARKET_STOCK)
    d["players"]["george kittle"].pop("d_rank")
    assert contract.problems("LIVE_MARKET_STOCK", d) == ["LIVE_MARKET_STOCK.players['george kittle'].d_rank"]


@pytest.mark.req(REQ, ac="the build re-keys the market stock by slug")
def test_build_injects_the_market_stock_from_the_feed(built):
    """build.py re-keys the producer's norm_name-keyed players by slug (profileFor()'s key), so
    the injected keys are slugs of the fixture's names, not the fixture's own keys."""
    got = injected(built.fragment)["LIVE_MARKET_STOCK"]
    assert got["backtested"] is False
    want = {build.slugify(rec["name"]) for rec in MARKET_STOCK["players"].values()}
    assert set(got["players"]) == want
    assert any(line.startswith("Market stock: 4 players") for line in built.report)


@pytest.mark.req(REQ, ac="no market stock file injects null")
def test_no_market_stock_injects_null(monkeypatch):
    monkeypatch.setattr(build, "load_market_stock", lambda: None)
    b = build.render()
    assert injected(b.fragment)["LIVE_MARKET_STOCK"] is None


@pytest.mark.req(REQ, ac="the sheet keeps ff-jarvis's shrunk value and elite list, null when absent")
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


# ------------------------------------------------------------------ the roster rows, rendered

@pytest.mark.render
@pytest.mark.req(REQ, ac="a roster row's matchup clause names the opponent's rank, tinted, titled")
def test_matchup_column_rows(mount):
    profile, errors = on_roster(mount)
    rows = profile.roster
    st_brown = rows.matchup(ST_BROWN)
    assert st_brown["text"] == "@ KC 9th"
    assert st_brown["n_class"].strip() == "mu-n"
    assert rows.matchup("Jahmyr Gibbs") is None                         # bye: no clause
    assert rows.matchup("Joe Burrow") is None                           # no profile: no clause
    rows.show_team("espn")
    assert "mu-hard" in rows.matchup("George Kittle")["n_class"]
    higgins = rows.matchup("Tee Higgins")
    assert "mu-easy" in higgins["n_class"]
    assert higgins["text"] == "vs PIT 8th"
    # The ordinal says what it ranks in its title, since the column header that carried it went.
    assert "easiest of 32" in higgins["n_title"]
    assert rows.chip_count() == 0
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="a phone row carries the matchup clause on its meta line, not in a column")
def test_phone_moves_matchup_to_the_meta_line(mount):
    profile, errors = on_roster(mount, (390, 844), team="espn")
    rows = profile.roster
    kittle = rows.phone_matchup("George Kittle")
    assert not kittle["column_visible"]
    # The ordinal is the profile's since 2026-09-24: a phone row reads "TE · SF vs LAR".
    assert kittle["clause"]["visible"] and kittle["clause"]["text"] == "vs LAR"
    assert not kittle["clause"]["n_visible"]
    assert kittle["projection_visible"]
    assert rows.matchup("Brock Purdy") is None                          # no profile: no clause
    rows.show_team("yahoo")
    assert rows.matchup("Jahmyr Gibbs") is None                         # bye: no clause
    assert rows.page_width() <= 390
    assert errors == []


# ------------------------------------------------------------------ the head and the strip

@pytest.mark.render
@pytest.mark.req(REQ, ac="the head carries watch's verdict word and a plain-words reason, from any way in")
def test_head_carries_the_verdict(mount):
    """The verdict word left the roster row on 2026-09-25 for the profile head. Looked up by slug,
    so a sheet opened from anywhere (search passes a bare {n, pos, team}) says the same thing a
    roster row's sheet does. "On 2 of your teams" went on 2026-09-28 to the owner pills."""
    profile, errors = on_roster(mount, team="espn")
    profile.open_from_roster("Chase Brown")                  # RISING in watch, on both fixture rosters
    tags = profile.tags()
    assert tags["verdict"] == "RISING"
    # Plain words since 2026-10-05 (plan U3): watch's "snaps +13.0, share +N; buy or start" is a sentence.
    why = tags["why"]
    assert why.startswith("Snaps up 13.0 points and his share of the work up ") and why.endswith("Worth a start, or an add if he is free.")
    assert "+" not in why and "snaps +" not in why
    assert profile.owner_marks() == 0
    profile.open_player({"n": "Chase Brown", "pos": "RB", "team": "CIN"})
    assert "RISING" in profile.tags()["text"]
    profile.open_starter("espn", "Brock Purdy")              # watch says hold, one roster: no line
    assert profile.tags() is None
    assert errors == []


@pytest.mark.render
@pytest.mark.parametrize("size", [(1400, 900), (360, 800)])
@pytest.mark.req(REQ, ac="the head says a hurt player's level and reason under his identity; a healthy one shows nothing")
def test_head_carries_his_injury_status(mount, size):
    """2026-09-30 (David: "should injured players have their status on the player profile?"): the head
    says the level and Sleeper's reason, from the same injFor() the roster cards read; a healthy player
    shows nothing. It is a line of the name block, under the identity line, at every width (moved there
    the same day: alone in the head's middle it looked stray)."""
    profile, errors = on_roster(mount, size)
    hurt = profile.open_injured_player()
    inj = profile.injury()
    assert inj is not None, hurt
    assert inj["cls"].endswith({"OUT": "out", "D": "d", "Q": "q"}[hurt["want"]["s"]])
    assert inj["note"] == hurt["want"]["note"]
    assert inj["in_who"] and inj["after_id"] and inj["below_id"], "a line of the name block, under the identity"
    assert profile.roster.page_width() <= size[0]
    profile.open_healthy_player()
    assert profile.injury() is None
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="the strip leads with the projection, then ppg, rank, role share and snaps")
def test_the_strip_says_how_good_and_how_used(mount):
    """The strip under the head (2026-09-28): ppg, rank by points per game, role share, snaps, all
    LIVE_POOL. The share is the one pool.py plots for his position -- carries for a back, targets
    for a receiver -- and a cell with no source is left out, so a player the pool does not carry
    shows no pool cells rather than dashes. The rank left the identity line for it. Since 2026-10-05
    (plan U3) this week's projection leads it and season ppg is second: "WR3 / 26.2 PPG" read as the
    projection."""
    profile, errors = on_roster(mount, team="espn")
    profile.open_from_roster("Chase Brown")
    cells = profile.strip()
    assert [c["value"] for c in cells] == [profile.projection("chase-brown"), "17.4", "RB1", "62%", "71%"]
    assert [c["label"] for c in cells] == ["PROJ.", "PPG", "RANK", "CARRIES", "SNAPS"]
    assert [c["proj"] for c in cells] == [True, False, False, False, False]
    assert "RB1" not in profile.identity()                   # one home for the rank
    profile.close()
    profile.open_from_roster("George Kittle")
    assert profile.strip()[3]["label"] == "TARGETS"
    profile.close()
    profile.roster.show_team("yahoo")
    profile.open_from_roster(ST_BROWN)                       # not in the fixture pool: his projection alone
    assert [c["label"] for c in profile.strip()] == ["PROJ."]
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="the fantasy tier (RBn by ppg) leads the strip; the identity line keeps position, club, bye")
def test_the_fantasy_tier_leads_the_strip(mount):
    """"RB4": his rank by points per game, season to date, among every RB in LIVE_POOL
    (watch.json) -- said the way a fantasy reader says it, never as a WR1/2/3 tier that reads
    like a depth chart. It sat on the identity line until 2026-09-28 and leads the strip since;
    the line keeps position, club and bye."""
    profile, errors = on_roster(mount)
    profile.open_from_roster("Chase Brown")
    head = profile.identity().upper()
    rank, of, _tied = profile.ppg_rank("chase-brown", "RB")
    # One separator for the whole line, and the same one the rest of the page uses.
    assert head == "RB · CIN · BYE 10"
    assert "|" not in head
    assert profile.strip()[2]["value"] == f"RB{rank}"        # projection, ppg, then the rank
    assert of == profile.pool_size("RB")
    profile.close()
    profile.open_from_roster(ST_BROWN)                       # not in the fixture pool: no rank anywhere
    assert profile.identity().upper() == "WR · DET"
    assert len(profile.strip()) == 1                         # his projection; no pool rank or share
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="one owner pill per league: yours, a leaguemate's team, or free agent")
def test_owners_name_each_leagues_team(mount):
    """One pill per league (2026-09-28): the team that rosters him by name, or free agent when every
    team in that league is loaded and none has him. "Yours" is the reader's own team only."""
    profile, errors = on_roster(mount)           # David's browser, Yahoo team
    profile.open_from_roster(ST_BROWN)
    owners = profile.owners()
    assert [o["text"] for o in owners] == ["Yahoo Yours", "ESPN Free agent", "AYO Free agent"]   # the third league, 2026-09-29
    assert owners[0]["mine"]
    assert owners[1]["free"]
    profile.close()
    # A leaguemate's browser: no owner link, no team picked. The same pill names the team.
    profile.become_a_leaguemate()
    profile.open_from_roster(ST_BROWN)
    owners = profile.owners()
    assert [o["text"] for o in owners] == ["Yahoo Chat Take the Wheel", "ESPN Free agent", "AYO Free agent"]
    assert not owners[0]["mine"]
    assert errors == []
