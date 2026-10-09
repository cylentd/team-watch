"""Players > Ranks (design/ranks.py, 2026-09-26): the tiers are natural breaks, the rank is the
roster card's, and the view draws each tier with its rows. The view's tests mount Ranks alone
(tests/component.py) and read it through tests/pages/ranks.py."""
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "design"))
from ranks import live_ranks, natural_breaks  # noqa: E402
from component import mount  # noqa: E402,F401  (the fixture)
from pages.ranks import RanksPage  # noqa: E402
from pages.teamswitch import TeamSwitchPage  # noqa: E402

# A first visit: nothing picked, nothing followed (the suite's seed picks and follows David's teams).
FRESH_READER = 'try { localStorage.removeItem("tw-team"); localStorage.removeItem("tw-follow"); } catch (e) {}\n'


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


@pytest.mark.req("Ranks", ac="tiers break where the points gap")
def test_breaks_fall_at_the_widest_drops():
    # Three clear groups: the tier lines must land between them, not at a round count.
    pts = [20.0, 19.8, 15.1, 15.0, 14.9, 9.0, 8.8, 8.7]
    assert natural_breaks(pts, 3) == [1, 1, 2, 2, 2, 3, 3, 3]


@pytest.mark.req("Ranks", ac="never more tiers than players")
def test_breaks_never_ask_for_more_tiers_than_players():
    assert natural_breaks([10.0, 9.0], 8) == [1, 2]
    assert natural_breaks([], 4) == []


@pytest.mark.req("Ranks", ac="a long dense tail spreads over several tiers")
def test_week3_shaped_wr_list_is_not_one_giant_tier():
    """The plain gap rule this replaced gave WR tiers of 1, 2, 1, 1, 2 and 41 on week 3: sparse at
    the top, dense below. Natural breaks must spread a long dense tail over several tiers."""
    pts = [17.6, 16.6, 16.5, 15.9, 15.0] + [14.0 - i * 0.1 for i in range(43)]
    tiers = natural_breaks(pts, 9)
    sizes = [tiers.count(t) for t in range(1, 10)]
    assert max(sizes) < 20, sizes


@pytest.mark.req("Ranks", ac="rows carry the card's rank; a player out is left off")
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


@pytest.mark.req("Ranks", ac="one week only; the teams left off are named")
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
    schedule = {"week": 3, "games": [
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


@pytest.mark.req("Ranks", ac="the roster cards take the same week cut")
def test_the_cards_take_the_same_week_cut():
    """The roster cards read LIVE_PROJECTIONS, and a Thursday team's row is next week's there too:
    no points, no rank, and `done` says whether his team played or has a bye."""
    from projections import live_projections
    raw = {"scoring": "half-PPR", "players": [
        {"name": "Bijan Robinson", "pos": "RB", "team": "ATL", "kickoff": "2026-10-06 00:15:00", "pts": 19.7, "src": "model"},
        {"name": "Bye Back", "pos": "RB", "team": "SEA", "kickoff": "2026-10-04 17:00:00", "pts": 18.0, "src": "model"},
        {"name": "Jahmyr Gibbs", "pos": "RB", "team": "DET", "kickoff": "2026-09-27 17:00:00", "pts": 18.8, "src": "model"},
    ]}
    schedule = {"week": 3, "games": [
        {"week": 3, "away": "ATL", "home": "GB", "kickoff": "2026-09-25T00:15:00Z"},
        {"week": 3, "away": "NYJ", "home": "DET", "kickoff": "2026-09-27T17:00:00Z"},
        {"week": 4, "away": "ATL", "home": "NO", "kickoff": "2026-10-06T00:15:00Z"},
        {"week": 4, "away": "SEA", "home": "LAR", "kickoff": "2026-10-04T17:00:00Z"},
    ]}
    wanted = {"bijan-robinson", "bye-back", "jahmyr-gibbs"}
    p = live_projections(raw, slug, wanted, None, schedule)["players"]
    assert (p["bijan-robinson"]["done"], p["bijan-robinson"]["pts"], p["bijan-robinson"]["rank"]) == ("played", None, None)
    assert p["bye-back"]["done"] == "bye"
    assert (p["jahmyr-gibbs"]["done"], p["jahmyr-gibbs"]["rank"]) == (None, 1)


@pytest.mark.req("Ranks", ac="no projections, no block")
def test_no_projections_is_no_block():
    assert live_ranks({}, slug) is None


@pytest.mark.req("Ranks", ac="the matchup rides on QB, RB, TE, never WR")
def test_matchup_rides_on_qb_rb_te_never_wr():
    """`mx` is ff-jarvis's `matchup.pts` (2026-09-29), the points a defense adds or takes. The WR
    effect tests null, so a WR carries none even if a file ever gave him one."""
    raw = {"players": [
        {"name": "A Back", "pos": "RB", "team": "ATL", "game": "ATL @ NO", "pts": 19.7, "matchup": {"pts": 1.74, "opp": "NO", "priced": 0.66}},
        {"name": "A Wideout", "pos": "WR", "team": "SEA", "game": "SEA @ LAR", "pts": 17.6, "matchup": {"pts": 1.0, "opp": "LAR"}},
        {"name": "A Passer", "pos": "QB", "team": "BUF", "game": "NE @ BUF", "pts": 21.8},
    ]}
    got = {x["slug"]: (x["mx"], x["mxp"]) for x in live_ranks(raw, slug)["rows"]}
    assert got == {"a-back": (1.7, 0.7), "a-wideout": (None, None), "a-passer": (None, None)}


@pytest.mark.req("Ranks", ac="floor and ceiling ride through untouched")
def test_the_band_rides_on_every_row_and_card_as_the_file_wrote_it():
    """`floor` and `ceil` (plan U5, 2026-10-05) are ff-jarvis's 10th and 90th percentile outcome, cut
    through untouched: the page never computes a band. A ruled-out or already-played player keeps
    his row on the cards with no points and no band; a file with no band (older, or a position the
    table does not cover) gives null, never a missing key."""
    from projections import live_projections
    raw = {"players": [
        {"name": "A Back", "pos": "RB", "team": "ATL", "game": "ATL @ NO", "pts": 19.7, "floor": 7.4, "ceil": 31.2, "src": "model"},
        {"name": "No Band", "pos": "WR", "team": "SEA", "game": "SEA @ LAR", "pts": 12.0, "src": "model"},
        {"name": "Out Back", "pos": "RB", "team": "GB", "game": "GB @ TB", "pts": 0.0, "floor": 0.0, "ceil": 0.0, "src": "model"},
    ]}
    status = {"x": {"name": "Out Back", "injury": "Out"}}
    rows = {x["slug"]: x for x in live_ranks(raw, slug, status)["rows"]}
    assert (rows["a-back"]["floor"], rows["a-back"]["ceil"]) == (7.4, 31.2)
    assert (rows["no-band"]["floor"], rows["no-band"]["ceil"]) == (None, None)
    cards = live_projections(raw, slug, {"a-back", "no-band", "out-back"}, status)["players"]
    assert (cards["a-back"]["floor"], cards["a-back"]["ceil"]) == (7.4, 31.2)
    assert (cards["no-band"]["floor"], cards["no-band"]["ceil"]) == (None, None)
    assert cards["out-back"]["pts"] is None and (cards["out-back"]["floor"], cards["out-back"]["ceil"]) == (None, None)


@pytest.mark.render
@pytest.mark.req("Ranks", ac="a matchup tag shows from half a point, never on a WR")
def test_ranks_tags_a_matchup_from_half_a_point(mount):
    """The fixture gives Chase Brown +1.4, Joe Burrow -0.9, George Kittle -0.3 (under the half
    point) and a WR +1.0 (never shown)."""
    page, errors = mount("ranks")
    ranks = RanksPage(page)
    ranks.pick("FLEX")
    tags = {r["slug"]: r["mx"] for r in ranks.rows()}
    assert tags.get(slug("Chase Brown")) == "+1.4"
    assert tags.get(slug("George Kittle")) is None and tags.get(slug("Amon-Ra St. Brown")) is None
    ranks.pick("QB")
    burrow = next(r for r in ranks.rows() if r["slug"] == slug("Joe Burrow"))
    assert (burrow["mx"], burrow["mx_up"]) == ("−0.9", False)
    assert ranks.fits()
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Ranks", ac="the back list follows the points it shows and says nothing about whose number it is")
def test_the_back_list_follows_the_points_it_shows_and_says_nothing_about_whose_number_it_is(mount):
    """The fixture's week_ranks list ships Brown, Hall and Miller (16.2, 15.0, 3.1) in our points' order, tiered 1, 1, 2
    (ff-jarvis #88; drawn as shipped, ledger #98). Readers see one rank: no note on the books' order, no "No line" tag
    (David: users do not need to know whose number it is; the tag is gone, ledger #96)."""
    page, errors = mount("ranks")
    ranks = RanksPage(page)
    rows = ranks.rows()
    assert [[r["slug"], r["pts"]] for r in rows] == [["chase-brown", "16.2"], ["breece-hall", "15.0"], ["kendre-miller", "3.1"]]
    assert [t.upper() for t in ranks.tiers()] == ["TIER 1", "TIER 2"], "the list's own tiers, as shipped (ledger #98)"
    ranks.pick("FLEX")
    assert [r["slug"] for r in ranks.rows()] == ["amonra-st-brown", "chase-brown", "breece-hall", "george-kittle", "kendre-miller"]
    assert ranks.fits()
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Ranks", ac="tiers drawn, only the reader's own players marked, a row opens the profile")
def test_ranks_draws_tiers_and_opens_a_profile(mount):
    page, errors = mount("ranks")
    ranks = RanksPage(page)
    tiers = ranks.tiers()
    assert tiers and tiers[0].upper() == "TIER 1"
    # Only the reader's own players are his: a leaguemate's roster is not (2026-09-26, when
    # the leaguemate rosters landed every rostered player read MINE).
    mine = {r["slug"] for r in ranks.rows() if r["mine"]}
    own = ranks.own_slugs()
    assert mine <= own, mine - own
    assert ranks.fits()
    ranks.pick("FLEX")
    assert any(r["pos"] for r in ranks.rows()), "FLEX rows say the position and its rank"
    ranks.open_first_row()
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Ranks", ac="unfollowing a team takes its players off the MINE list at once")
def test_unfollowing_a_team_takes_its_players_off_mine_without_a_reload(mount):
    """David, 2026-10-06: "Unselecting your team doesn't remove them from the MINE designation in Stats > Ranks."
    The reader follows what the switch lists (the seed: Yahoo, ESPN, AYO). Each star tapped in the header's menu
    leaves exactly the players of the teams still followed marked, with the menu still open."""
    page, errors = mount("ranks", size=(390, 844))
    ranks, switch = RanksPage(page), TeamSwitchPage(page)
    ranks.pick("FLEX")
    shown, followed = ranks.shown_slugs(), ["yahoo", "espn", "ayo"]
    assert ranks.mine_slugs() == ranks.held_by(followed) & shown != set(), "the fixture holds players the list shows"
    switch.open_menu()
    wrong_mine, menu_closed = [], []
    for gone in list(followed):
        switch.follow(gone)
        followed.remove(gone)
        if ranks.mine_slugs() != ranks.held_by(followed) & shown:
            wrong_mine.append(gone)
        if not switch.menu_is_visible():
            menu_closed.append(gone)
    assert wrong_mine == [], "MINE did not match the teams still followed after unfollowing these"
    assert menu_closed == [], "a star keeps the menu open"
    assert ranks.mine_slugs() == set()
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Ranks", ac="a reader's pick marks that team's players, not David's")
def test_a_leaguemate_who_picks_their_team_sees_their_players_as_mine(mount):
    """A pick follows the team by default (data/mates.js followLoad); the page is public, and David's three teams
    are three of ~36, so his rosters are nobody else's MINE."""
    page, errors = mount("ranks", size=(390, 844), init=(FRESH_READER,))
    ranks = RanksPage(page)
    ranks.pick("FLEX")
    mate, theirs = ranks.first_mate(), "george-kittle"
    assert mate and theirs in ranks.shown_slugs(), "the fixture has a leaguemate and a TE on the list"
    ranks.put_on_roster(mate, theirs)
    ranks.pick_team(mate)
    assert ranks.mine_slugs() == {theirs}, "David's players, on the list too, are not his"
    assert ranks.shown_slugs() & ranks.held_by(["yahoo", "espn", "ayo"]), "David's teams do hold players on the list"
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Ranks", ac="a reader with no team has no MINE tags")
def test_a_first_visit_marks_no_one_as_mine(mount):
    page, errors = mount("ranks", size=(390, 844), init=(FRESH_READER,))
    ranks = RanksPage(page)
    ranks.pick("FLEX")
    assert ranks.shown_slugs() & ranks.held_by(["yahoo", "espn", "ayo"]), "David's teams do hold players on the list"
    assert ranks.mine_slugs() == set()
    assert errors == []
