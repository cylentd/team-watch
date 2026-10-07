"""The profile's panes: Season, Usage, Props, Matchup and Bio, the archetype tiles, the Season table's live
row, and the page with no profiles file. The contract, the roster rows, the head and the strip are
test_profile.py. Each test mounts the roster and works through pages/profile.py (see test_profile.py)."""
import re

import pytest

import build
from component import Mounter, mount  # noqa: F401  (the fixture)
from pages.profile import ProfilePage
from pages.roster import on_roster

REQ = "The profile modal"
ST_BROWN = "Amon-Ra St. Brown"


# ------------------------------------------------------------------ the panes

@pytest.mark.render
@pytest.mark.req(REQ, ac="three-plus panes split the blocks and only the open pane is in the DOM")
def test_panes_split_the_blocks_and_only_one_is_in_the_dom(mount):
    """Three panes since 2026-09-22, replacing eleven stacked blocks and the Details disclosure
    nested inside them. Each block still renders exactly as before; what changed is which pane
    it belongs to, and that only the open pane exists in the DOM at all."""
    profile, errors = on_roster(mount)
    profile.open_from_roster(ST_BROWN)
    assert profile.tab_labels() == ["SEASON", "USAGE", "PROPS", "MATCHUP"]
    # Season opens first (2026-09-28): his points and his schedule, nothing from another pane.
    assert profile.season_blocks() == 1
    assert "PROJECTION" in profile.text()
    assert profile.zone_blocks() == 0
    profile.tab("usage")
    # Usage: target depth, red zone, middle vs outside.
    assert profile.season_blocks() == 0
    assert profile.zones_in("Target depth") == 4
    assert "31% · 4 of 13" in profile.section_text("Red zone")
    assert profile.rank() is None
    profile.tab("matchup")
    assert profile.rank() == "9th easiest of 32 for WRs"
    assert profile.zone_blocks() == 0                        # usage is gone, not hidden
    # The pane presents the numbers (2026-09-29, David: "untested is not needed"): no amber tag,
    # no methodology citation, one card per subject.
    assert "UNTESTED" not in profile.text() and "METHODOLOGY" not in profile.text()
    assert len(profile.columns()) == 3
    profile.close()
    assert not profile.is_open()
    assert profile.focus_on_roster_row()
    profile.open_from_roster("Chase Brown")
    # Five tabs for him, four for St. Brown above: Bio reads LIVE_PEDIGREE alone, and the
    # fixture has a pedigree record for this back and none for that receiver. A pane with
    # nothing in it draws no button rather than opening on an empty panel. The last pane read
    # (Matchup, above) is not carried over: every player opens on Season.
    assert profile.tab_labels() == ["SEASON", "USAGE", "PROPS", "MATCHUP", "BIO"]
    assert profile.selected_tab() == "season"
    profile.tab("usage")
    text = profile.text()
    assert "Target depth" not in text and profile.zone_blocks() == 0   # a back: no block
    assert text.index("6 of 11") < text.index("1 of 13")                 # carries before targets
    profile.close()
    profile.open_from_roster("Jahmyr Gibbs")
    profile.tab("usage")
    assert "5 of 9" in profile.text()                                    # carries, under 10
    profile.tab("matchup")
    assert "Bye, or no schedule yet." in profile.text()
    profile.close()
    profile.roster.show_team("espn")
    profile.open_from_roster("George Kittle")
    profile.tab("usage")
    rz = profile.section_text("Red zone")
    assert "3 of 8" in rz and "%" not in rz.split("\n")[1]                # counts under 10
    profile.tab("matchup")
    assert "mu-hard" in profile.rank_class()
    assert errors == []


@pytest.mark.render
@pytest.mark.parametrize("size,side", [((1400, 900), True), ((360, 800), False)])
@pytest.mark.req(REQ, ac="a desktop lays the blocks side by side, a phone stacks them in the same order")
def test_desktop_panes_sit_side_by_side_and_a_phone_stacks_them(mount, size, side):
    """2026-09-29, David: Usage and Matchup "should fit without scrolling", Props two to a row. On
    a desktop the blocks share a top edge; on a phone the same blocks stack in the same order. The
    league tags are grey, not the leagues' brand colours, and a played week carries no play mark."""
    profile, errors = on_roster(mount, size)
    profile.open_from_roster(ST_BROWN)
    profile.tab("usage")
    a, b = profile.pane_blocks()[:2]
    assert (a[0] == b[0]) if side else (b[0] >= a[1])
    # His bar wears his position's colour; his teammates' stay grey (2026-09-29).
    bars = profile.tm_bar_colours()
    assert bars["me"] != bars["mate"]
    profile.tab("matchup")
    cols = profile.columns()
    assert len(cols) >= 2
    assert (cols[0][0] == cols[1][0]) if side else (cols[1][0] >= cols[0][1])
    leagues = profile.owner_league_colours()
    assert len(leagues) == 3 and len(set(leagues)) == 1        # one grey for every league (AYO the third), no brand colour
    profile.tab("season")
    assert profile.season_icons() == 0
    # A draft pick sits by the league it belongs to, not at the far edge of the pane (David,
    # 2026-09-29: "on desktop we stretch out info").
    profile.close()
    profile.open_from_roster("Chase Brown")
    profile.tab("bio")
    assert profile.draft_row_span() <= 560
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="Usage leads with his share of his own team; a teammate's row opens his profile; a passer gets no block")
def test_usage_opens_on_his_share_of_his_own_team(mount):
    """2026-09-29, David: usage "should have his teammates there for comparison". Usage leads with
    his share of his team's targets (a back: carries, then targets) from the game log, the top five
    by volume with him among them, the rest as one row. A teammate's row opens that profile; a
    passer gets no block."""
    profile, errors = on_roster(mount)
    profile.open_player({"n": ST_BROWN, "pos": "WR", "team": "DET", "slug": "amonra-st-brown"})
    profile.tab("usage")
    assert profile.sections("team") == 1
    assert profile.pane_sections()[0] == "team"
    want = profile.team_share("DET", "tgt")
    block = profile.team_block()
    assert f"{want['v']} of {want['total']}" in block["lead"] and "targets" in block["lead"]
    assert block["label"] == "DET TARGETS"                      # the head names the stat
    rows = profile.team_rows()
    pcts = [r["pct"] for r in rows]
    assert abs(sum(pcts) - 100) <= len(pcts)                    # the rows are the whole team, give or take rounding
    named = [r["pct"] for r in rows if not r["rest"]]
    assert named == sorted(named, reverse=True)
    mine = [r for r in rows if r["me"]]
    assert len(mine) == 1 and mine[0]["tag"] == "DIV"            # his own row goes nowhere
    mate = next(r for r in rows if r["tag"] == "BUTTON")
    profile.open_teammate(mate["slug"])
    assert profile.title().upper() == profile.gamelog_name(mate["slug"]).upper()
    profile.open_player({"n": "Josh Allen", "pos": "QB", "team": "BUF", "slug": "josh-allen"})
    if profile.has_tab("usage"):
        profile.tab("usage")
    assert profile.sections("team") == 0
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="the red-zone split names the teammates, his segment first and bright")
def test_red_zone_split_names_the_teammates(mount):
    """red_zone.others (player_profiles.json): Amon-Ra St. Brown has 4 of DET's 13 red-zone
    targets; Sam LaPorta 4 and Jahmyr Gibbs 2 are named, the other 3 are "3 more". His segment
    comes first and is the bright one."""
    profile, errors = on_roster(mount)
    profile.open_from_roster(ST_BROWN)
    profile.tab("usage")
    splits = profile.splits()
    assert len(splits) == 1
    # Small type drops the first name to an initial; the header carries the full one.
    key = splits[0]["key"]
    assert key.index("A. St. Brown 4") < key.index("S. LaPorta 4") < key.index("J. Gibbs 2") < key.index("3 more")
    assert "Amon-Ra" not in key
    segments = splits[0]["segments"]
    assert len(segments) == 3 and "me" in segments[0]
    profile.close()
    profile.open_from_roster("Chase Brown")      # a back: a carries split above a targets split
    profile.tab("usage")
    splits = profile.splits()
    assert len(splits) == 2
    assert "Z. Moss 3" in splits[0]["key"] and "J. Chase 5" in splits[1]["key"]
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="Props draws his last games against the line; no market log, no tab")
def test_props_draws_his_last_games_against_the_line(mount):
    """2026-09-29, David: "see his receptions, yds, tds as bar chart in the past X games". A player
    with a market log gets a Props tab: one chart per market he records, the leg sheet's bars, lime
    where he went over this week's line -- the over, whatever side the model picks. No log, no tab."""
    profile, errors = on_roster(mount)
    who = profile.prop_player()
    profile.open_player(who["p"])
    profile.tab("props")
    name = profile.market_name(who["mkt"]).upper()
    assert name in profile.prop_heads()
    chart = profile.prop_chart(name)
    assert chart["bars"] == len(who["vals"])
    over = sum(1 for v in who["vals"] if v > who["line"])
    assert chart["hits"] == over
    assert chart["caption"].startswith(f"Over {who['line']} in {over}/{len(who['vals'])}")
    assert who["none"], "the fixture needs a non-passer with no market log"
    profile.open_player(who["none"])
    assert not profile.has_tab("props")
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="the archetype is two tiles in the head; a tap opens Usage on the block that explains them")
def test_the_archetype_sits_in_the_head_and_explains_itself_in_usage(mount):
    """2026-09-29, David: the archetype "should be on the player profile" (it showed only under a
    Leaders comparison pick). His two words are tags with an icon in the head; a tap opens Usage
    on the block that says what each means and the numbers that produced it. A word the model
    withholds is no tag, and its reason stands in its place in Usage."""
    profile, errors = on_roster(mount)
    who = profile.archetype_players()
    assert who["both"], "the fixture needs a player with both words"
    profile.open_player(who["both"])
    # The tiles are the first medallions of the head rail (rail.js), in one row.
    slots = profile.arch_slots()
    assert [s["field"] for s in slots] == ["role", "style"] and slots[0]["visible"]
    assert slots[0]["y"] == slots[1]["y"]
    assert [s["svgs"] for s in slots] == [1, 1]                           # a tile on every chip, stone by field
    assert slots[0]["text"].strip().upper() == profile.role_word(who["both"]["role"]).upper()
    profile.open_arch_slot(1)
    assert profile.selected_tab() == "usage"
    assert profile.sections("arch") == 1
    block = profile.arch_block()
    assert block["means"] == 2                                            # each word says what it means
    assert block["evidence"] >= 1                                         # and what produced it
    # Starting a row, it takes the whole row with Role and Style side by side; beside a block, stacked.
    assert block["side_by_side"] == block["starts_row"]
    assert who["one"], "the fixture needs a player with a style and no role"
    profile.open_player(who["one"])
    assert len(profile.arch_slots()) == 1
    profile.tab("usage")
    assert who["one"]["role_null"] in profile.arch_block()["why"]
    assert errors == []


# ------------------------------------------------------------------ the Season table

@pytest.mark.render
@pytest.mark.req(REQ, ac="Season lists every week played and to come: played, the lime next row, a total")
def test_season_lists_every_week_played_and_to_come(mount):
    """The Season pane (2026-09-28): one row per week of his club's schedule. A played week shows
    his points and his line; the first week still to come is the lime row with the kickoff and the
    projection; a week with games for everyone but his club and no pedigree bye is left out, not
    called a bye. The opponent carries its rank against his position, 1st allowing the most."""
    profile, errors = on_roster(mount, team="espn")
    profile.open_from_roster("George Kittle")
    rows = profile.season_rows()
    assert [" ".join(r["classes"]) for r in rows] == ["ss-head", "ss-played", "ss-played", "ss-next", "ss-total"]
    assert rows[1]["pts"] == "12.1"
    nxt = profile.season_row("ss-next")
    assert nxt["opp"] == "KC"
    assert nxt["date"] == "Mon 1:25 PM"
    assert nxt["pts"] == "13.6"
    assert nxt["note"] == "projected · TE1 this week"
    # The When column is one column for every row: the dates played line up with the kickoffs.
    lefts = profile.season_date_lefts()
    assert len(set(lefts)) == 1, lefts
    assert profile.season_row("ss-total")["pts"] == "21.5"
    profile.close()
    profile.roster.show_team("yahoo")
    profile.open_from_roster("Jahmyr Gibbs")
    rows = profile.season_rows()
    assert [r["rk"] for r in rows if "gl-open" in r["classes"]] == ["22nd"]   # SEA allows RBs the 11th-fewest of 32
    assert not [r for r in rows if "ss-bye" in r["classes"]]                  # his bye is week 6, not week 3
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="a phone reads each Season week as one line of box-score shorthand")
def test_season_is_one_line_a_week_on_a_phone(mount):
    """No sideways scroll and no blocks of chips: a phone reads each week as box-score shorthand in
    one cell, and the stat columns are not drawn beside it."""
    profile, errors = on_roster(mount, (360, 800))
    profile.open_from_roster("Jahmyr Gibbs")
    first = profile.season_row("ss-played")
    assert first["line"] == "29-156-2 · 5-30"
    assert first["stat_visible"] is False
    assert len(set(profile.season_pts_rights(3))) == 1          # the points line up under their head
    assert not profile.modal_overflows()
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="this week's Season row is drawn from Live's poll: live, final, no stats, and a closed profile ignores the poll")
def test_season_draws_this_weeks_row_from_live_stats(mount):
    """2026-10-04: a profile said "No stats" for a player Live had already scored, because LIVE_GAMELOG is
    baked at build time. Week 3 has no log row; the poll's league-wide leaders have Kittle. While SF is
    on the clock the row is lime and says "Q3 4:12 · live"; when the poll says final it is a plain
    played row that says "Final"; with no stats at all the row stays "No stats". A poll redraws the
    open table in place, and one after the profile closes does nothing."""
    profile, errors = on_roster(mount, team="espn")
    profile.season_live_game()
    profile.open_from_roster("George Kittle")
    week = profile.season_week(3)
    assert "ss-live" in week["classes"]
    assert week["pts_main"] == "16.2"
    assert week["line"] == "6-82-1 · 8 tgt"
    assert week["date"] == "Q3 4:12 · live"
    assert profile.season_row("ss-total")["pts"] == "21.5"          # played weeks only
    # The next poll: the game is over, the row stays and is a played row.
    profile.poll_final()
    week = profile.season_week(3)
    assert "ss-live" not in week["classes"] and "ss-played" in week["classes"]
    assert week["date"] == "Final"
    assert week["line"] == "6-82-1 · 8 tgt"
    # No stats for him: the row is what it was.
    profile.poll_without_stats()
    assert profile.season_week(3)["line"] == "No stats"
    # Closed: a poll leaves the dialog alone.
    profile.close()
    profile.poll()
    assert not profile.is_open()
    assert errors == []


# ------------------------------------------------------------------ the Bio and Matchup panes

@pytest.mark.render
@pytest.mark.req(REQ, ac="Bio shows pedigree and each league's fantasy draft; the bye is the head's")
def test_facts_show_pedigree_and_fantasy_draft(mount):
    """tests/fixtures/data/pedigree.json: Jahmyr Gibbs was 1.12 (pick 12 overall) in the real
    2023 NFL draft, drafted 1.01 by my ESPN team and 1.02 in Yahoo; Chase Brown has an ESPN pick
    only, the per-league optional-ness that fantasy_draft's shape allows.

    The bio splits in two (2026-09-22). Age, size, experience and the bye qualify every number in
    the modal, so they are a line under his name; where he was drafted is history that decides
    nothing this week, so it keeps a headed block at the foot of the left column."""
    profile, errors = on_roster(mount)
    profile.open_from_roster("Jahmyr Gibbs")
    # The bye is the one fact here that decides something, so it is on the identity line under
    # his name; the rest is reference and lives in its own Bio pane. The fixture's pedigree
    # carries no measurables, so the pane's live shape is proved against a stub -- what matters
    # is that a missing field drops out rather than dashing.
    assert profile.identity().upper().endswith("· BYE 6")
    profile.tab("bio")
    facts = profile.bio_facts()
    assert "Week 6" not in facts                      # the bye is the head's now, not the grid's
    assert "Rd 1.12 · 2023" in facts and "overall" not in facts
    stub = {"age": 27, "height": "73", "weight": 210, "years_exp": 5, "bye": 9}
    assert profile.bio_rows(stub) == ["Age 27", "Size 6′1″ · 210 lb", "Exp 5 yr pro"]
    # One row per league I have a team in, labelled by my team's name there (uppercase in the
    # render); "by X" only when someone else took him.
    labels = profile.draft_labels()
    assert profile.team_name("yahoo").upper() in labels
    assert profile.team_name("espn").upper() in labels
    # Each league's row leads with its tag, the owner pills' own word (2026-09-29).
    assert profile.draft_leagues().count("Yahoo") == 1
    assert profile.draft_leagues().count("ESPN") == 1
    assert "Rd 1.01 · by Big Salty" in facts
    assert "Rd 1.02 · by Team Minh" in facts
    profile.close()
    profile.open_from_roster("Chase Brown")
    profile.tab("bio")
    assert "Rd 3.07 · by Big Salty" in profile.bio_facts()
    assert profile.team_name("yahoo").upper() not in profile.draft_labels()
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="the Matchup pane shows the stadium forecast with icons; a bye has none")
def test_weather_shows_stadium_forecast_with_icons(mount):
    """tests/fixtures/data/weather.json: Amon-Ra St. Brown is away at KC (outdoor, sunny), Chase
    Brown is home at CIN (outdoor, cooler), Jahmyr Gibbs has no next game (a bye in the fixture)
    so no forecast to show at all. The forecast sits inside the matchup block, in the Matchup
    pane."""
    profile, errors = on_roster(mount)
    profile.open_from_roster(ST_BROWN)
    profile.tab("matchup")
    wx = profile.weathers("Week 3 @ KC")
    assert len(wx) == 1
    text = wx[0]["text"]
    assert "71°F" in text and "Sunny" in text and "10 mph" in text and "from S" in text
    assert "%" not in text                              # the sky phrase carries the rain chance
    assert wx[0]["icons"] == 2
    profile.close()
    profile.open_from_roster("Chase Brown")
    profile.tab("matchup")
    wx = profile.weathers()
    assert len(wx) == 1
    assert "58°F" in wx[0]["text"] and "Partly Cloudy" in wx[0]["text"] and "6 mph" in wx[0]["text"]
    profile.close()
    profile.open_from_roster("Jahmyr Gibbs")
    profile.tab("matchup")
    assert profile.weathers() == []
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="the market line shows the books' number, role points, rank and what is priced, no arrows, colour or z")
def test_market_row_shows_priced_numbers(mount):
    profile, errors = on_roster(mount)
    profile.open_from_roster(ST_BROWN)
    profile.tab("matchup")
    text = profile.text()
    assert "UNTESTED" not in text                             # tags cut 2026-09-29 (David)
    assert "17.8 pts" in text and "role 18.2 pts" in text
    assert "WR rank #5" in text and "Priced: REC" in text
    # 12.46: a move against his last game failed its backtest (wrong sign), so the arrows, their colour and z went (2026-10-06).
    assert profile.caps("pts") and all(c["deltas"] == 0 for c in profile.caps("pts"))
    assert not re.search(r"[▲▼]|\bz [\d-]", text)
    assert not re.search(r"\b(BUY|SELL|RISING|FALLING|HOT|COLD)\b", text, re.I)
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="a row with no market falls back to the model's number and says none is priced")
def test_market_row_falls_back_to_model_pts(mount):
    profile, errors = on_roster(mount, team="espn")
    profile.open_from_roster("George Kittle")
    profile.tab("matchup")
    text = profile.text()
    assert "UNTESTED" not in text                             # tags cut 2026-09-29 (David)
    assert "13.1 pts, the model's number" in text
    assert "No market priced yet." in text
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="the matchup rank says in its tooltip that it failed its test")
def test_the_matchup_rank_says_it_failed_its_test(mount):
    """12.61 and 12.73: the defense rank fails as a price (2026-10-06). The sentence and the roster row's ordinal both say so."""
    profile, errors = on_roster(mount)
    profile.open_from_roster(ST_BROWN)
    profile.tab("matchup")
    assert any(m.startswith("Failed test (12.61, 12.73)") for m in profile.marks()), profile.marks()
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="no row of the market line carries a change arrow or a z, whatever the move")
def test_market_row_draws_no_change_marker_on_any_line(mount):
    """12.46 failed its backtest: the move against his previous game, its arrows and colour, and z (the move over
    his sector's sd) are gone from every line of the market block (2026-10-06). Chase Brown has a d_rank of 0
    and a z of -0.05 in tests/fixtures/data/market_stock.json; St. Brown a real move."""
    profile, errors = on_roster(mount)
    profile.open_from_roster("Chase Brown")
    profile.tab("matchup")
    rank_line = profile.caps("RB rank #8")
    assert len(rank_line) == 1 and rank_line[0]["deltas"] == 0
    assert "z -0.05" not in profile.text() and "z " not in profile.caps("role")[0]["text"]
    assert all(c["deltas"] == 0 for c in profile.caps("pts"))
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="a partly priced model row shows what is priced, not 'no market'")
def test_market_row_partial_markets_shows_priced_not_no_market(mount):
    """A src:"model" row can still carry a partial `markets` list (Tee Higgins: ["REC"]); the
    "No market priced yet." sentence is only for a row with no markets priced at all."""
    profile, errors = on_roster(mount, team="espn")
    profile.open_from_roster("Tee Higgins")
    profile.tab("matchup")
    text = profile.text()
    assert "UNTESTED" not in text                             # tags cut 2026-09-29 (David)
    assert "11.2 pts, the model's number" in text
    assert "Priced: REC" in text
    assert "No market priced yet." not in text
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="no verdict words (plus, minus, even) on any roster or pane")
def test_no_verdict_words_on_the_page(mount):
    profile, errors = on_roster(mount)
    words = re.compile(r"\b(PLUS|MINUS|EVEN)\b", re.I)
    for view in ("yahoo", "espn"):
        profile.roster.show_team(view)
        assert not words.search(profile.page_text()), view
        for i in range(profile.roster.count()):
            profile.open_roster_row(i)
            # Every pane, not just the one that opens: a verdict word hiding in the matchup
            # pane is still on the page.
            for _ in profile.tab_all():
                assert not words.search(profile.text()), (view, i)
            assert not words.search(profile.text()), (view, i)
            profile.close()
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="with no profiles file the roster draws no clause and the panel says so once; the other panes still draw")
def test_no_profiles_renders_dashes_and_a_quiet_panel(browser, monkeypatch, tmp_path):
    monkeypatch.setattr(build, "load_profiles", lambda: None)
    m = Mounter(browser, tmp_path, build.render().fragment)      # this build's own page, not the session's
    try:
        page, errors = m("roster", size=(390, 844))
        profile = ProfilePage(page)
        assert profile.roster.column_clauses() == 0
        profile.open_from_roster(ST_BROWN)
        assert profile.empty_notice() == 1
        # The matchup pane needs LIVE_PROFILES, so it draws no tab and the notice says why once. The
        # Season table, the projection, the team share and the stat sheet each read their own source
        # (LIVE_GAMELOG/LIVE_PROJECTIONS/LIVE_USAGE) and still render -- a player with no matchup
        # profile is not blank.
        assert profile.tab_ids() == ["season", "usage", "props"]
        assert profile.season_blocks() == 1
        assert profile.sections() == 2                           # the projection, and Rest of season (LIVE_ROS)
        profile.tab("usage")
        assert profile.pane_sections() == ["team", "arch"]
        profile.open_sheet()
        assert profile.radars() == 1
        assert errors == []
    finally:
        m.pages.close()
