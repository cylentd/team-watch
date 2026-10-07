"""design/digest.py: the Digest block, from ff-jarvis's weekly_digest.json; and the Digest's rows (surface/digest/).

Python for the block, component (`mount`, `DigestPage`) for what a phone and the wall draw from it. The
view after the week's first kickoff is tests/test_digest_after_kickoff.py, the Recap row is
tests/test_digest_recap_row.py, and the page's pure functions are tests/test_js_digest.py (Node).
"""
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "design"))
sys.path.insert(0, str(REPO / "api"))

import pytest  # noqa: E402

from _espn import slugify  # noqa: E402
import contract  # noqa: E402
from component import mount  # noqa: E402,F401  (the fixture)
from digest import kicks, live_digest, report  # noqa: E402
from pages.digest import DigestPage  # noqa: E402
from sources import load_digest  # noqa: E402

PHONE, WALL = (390, 844), (1400, 900)


def _block(schedule=None):
    return live_digest(load_digest(), slugify, schedule)


SCHEDULE = {"alias": {"LA": "LAR", "WAS": "WSH"}, "games": [
    {"home": "DEN", "away": "LAR", "kickoff": "2026-09-28T00:20:00Z", "week": 3},
    {"home": "WSH", "away": "SEA", "kickoff": "2026-09-27T17:00:00Z", "week": 3},
    {"home": "HOU", "away": "LAR", "kickoff": "2026-10-04T17:00:00Z", "week": 4}]}


@pytest.mark.req("Digest", ac="kickoffs answer in both team-code dialects")
def test_kicks_answers_in_both_dialects_for_the_packets_week():
    ko = kicks(SCHEDULE, 3)
    assert ko["LA"] == ko["LAR"] == "2026-09-28T00:20:00Z"
    assert ko["WAS"] == ko["WSH"] == "2026-09-27T17:00:00Z"
    assert "HOU" not in ko and kicks(None, 3) == {}


@pytest.mark.req("Digest", ac="a game's row carries its kickoff for the browser")
def test_game_rows_carry_their_kickoff_for_the_browser():
    b = _block(SCHEDULE)
    assert b["hurt"][0]["game"]["ko"] == "2026-09-28T00:20:00Z"
    assert b["wx"][0]["ko"] == "2026-09-27T17:00:00Z"
    assert all(r["ko"] is None or r["ko"].endswith("Z") for r in b["best"] + b["top5"])


@pytest.mark.req("Digest", ac="the packet carries no results; Recap still cuts its left-hurt rows")
def test_the_packet_carries_no_results_but_recap_still_cuts_left_hurt_rows():
    """2026-10-05: the week's results moved to This week > Recap (LIVE_RECAP), so the Digest's packet no
    longer carries finals, stars, smashed, busts or left. design/recap.py still cuts its left-hurt rows with
    digest._left: a tagged headline gives the injury, an untagged one loses his name, suffix and all, and his
    newest headline since, when there is one, is `later`, without his name or tag."""
    from digest import _left
    b = _block()
    assert not {"finals", "pending", "stars", "smashed", "busts", "left"} & set(b)
    left = [_left(x, slugify) for x in load_digest()["results"]["left_hurt"]]
    assert [(r["n"], r["injury"], r["rest"], r["later"]) for r in left] == [
        ("Tua Tagovailoa", "concussion", "ruled out for the remainder", None),
        ("De'Von Achane", "knee", "questionable to return", "suffers season-ending torn ACL"),
        ("Travis Etienne", None, "exits early Sunday", None)]
    assert b["asof_words"] == "Fri 10:40 PM"


@pytest.mark.render
@pytest.mark.req("Digest", ac="no Results row, board, tabs or wait card; the banner falls to the top headline")
def test_the_digest_has_no_results_row_banner_board_or_wait_card(mount):
    """2026-10-05 (David: "we probably need a recap section for the week instead of dumping it into the
    Digest. The Digest should be a curated list of content for readers to enjoy and not just a results
    section that stays there for the whole week and quickly become stale"). On a phone and on the wall,
    before the week, on a Monday after games and once the week is over: no Results row, no board, no
    Smashed / Busts / Left hurt tabs, no "Waiting on week N" card. Monday opens no row of its own. The
    banner the packet's "results" rule used to draw falls to the top headline."""
    states = ("2026-09-18T12:00:00Z", "2026-09-22T12:00:00Z", "2026-09-28T13:00:00Z", "2026-10-02T12:00:00Z")
    for size in (PHONE, WALL):
        page, errors = mount("digest", size=size)
        dg = DigestPage(page)
        for at in states:
            dg.plant_results_lead(at)       # the old packet still says its lead is the results rule
            rows, lead, head, news = dg.row_ids(), dg.packet_lead(), dg.headline_text(), dg.packet_first_headline()
            assert "res" not in rows and dg.retired_parts() == 0, (size, at, rows)
            assert lead is None or lead["rule"] != "results", (size, at, lead)
            if news and lead and lead["rule"] == "news":
                assert head == news, (size, at, head, news)
            if size[0] < 1100 and dg.weekday() == 1:
                assert dg.open_row_count() == 0, (size, at)
        assert errors == []


@pytest.mark.render
@pytest.mark.req("Digest", ac="the parts the Recap view draws with still draw")
def test_the_parts_the_recap_view_draws_with_still_draw(mount):
    """2026-10-05: the Results row is gone from the Digest, but the functions that drew a call, a box line, a
    board, a reason and a left-hurt row stay under their names (surface/digest/parts.js, lead.js) for the Recap
    view, which draws them from LIVE_RECAP. A LIVE_RECAP row has no `why`, so dgWhy takes a planted one."""
    page, errors = mount("digest", size=PHONE)
    got = DigestPage(page).recap_parts()
    assert errors == []
    assert got["board"] == got["stars"] > 0
    assert got["boardText"] and got["first"].split(" ")[0] in got["boardText"]
    assert re.match(r"^Gibbs (rumbles for|runs wild for|bulldozes for|churns out) 164 yards and 3 TDs$", got["call"]), got["call"]
    assert got["box"] and not any(b.endswith("pts") for b in got["box"])    # yards, never points (2026-10-05)
    assert got["topLine"] == "164 yards, 3 TDs"
    assert got["why"] == "31% tgt +10TD luck +5"
    assert got["out"] == ["Out 3 wks", "Season"]
    assert got["leftRow"].startswith("L. Jackson") and "Ankle" in got["leftRow"]      # his injury as an amber word, then how long
    assert got["games"] == ["1 game", "15 games"]


@pytest.mark.render
@pytest.mark.req("Digest", ac="before kickoff nothing stands beside Need to know")
def test_before_kickoff_the_digest_has_no_highlights_section(mount):
    """David, 2026-10-04: bored of the Digest's Highlights. Before kickoff nothing stands beside Need to
    know, which takes the wall's band; the Players tab keeps the Highlights (test_js_digest.py)."""
    page, errors = mount("digest", size=PHONE)
    dg = DigestPage(page)
    dg.plant_not_live()
    assert dg.retired_highlights() == 0
    assert "no-facts" in dg.ticker_classes()
    assert "Highlights" not in dg.section_titles()
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Digest", ac="the call picks its verb from his day")
def test_the_call_picks_its_verb_from_his_day(mount):
    """Week 3's real lines (Sleeper and nflverse agree, 2026-09-29): the verb follows what his day was
    made of, the TDs ride at the end, a receiver's one throw does not make him a passer, and with no
    box line yet it says the score."""
    page, errors = mount("digest", size=PHONE)
    got = DigestPage(page).calls()
    assert errors == []
    rush, rec, pas, short = (r"(rumbles for|runs wild for|bulldozes for|churns out)", r"(hauls in \d+ for|reels in \d+ for|torches them for|racks up)",
                             r"(slings|airs it out for|carves them up for|lights it up for)", r"(punches in|plunges in for|cashes in|owns the goal line:)")
    c = got["calls"]
    assert re.match(rf"^Gibbs {rush} 164 yards and 3 TDs$", c[0]), c[0]
    assert re.match(rf"^Smith-Njigba {rec} 128 yards and 2 TDs$", c[1]), c[1]      # one throw is not a passer
    assert re.match(rf"^Purdy {pas} 297 yards and 4 TDs$", c[2]), c[2]
    assert re.match(rf"^Mumpfield {rec} 93 yards and a TD$", c[3]), c[3]
    assert re.match(rf"^Williams {short} 3 TDs$", c[4]), c[4]
    assert c[5] == "Etienne scores 21.4"
    assert got["again"] == c[0] and got["weeks"] > 1        # fixed for his week, fresh across weeks


@pytest.mark.render
@pytest.mark.req("Digest", ac="a finished week drops the preview rows and draws no wait card")
def test_a_finished_week_drops_the_preview_rows_and_draws_no_wait_card(mount):
    """Once every game of the packet's week has kicked off (the fixture's week 3 ends with KC @ SF,
    2026-09-21), Hurt and Matchups have nothing left to preview and next week's are not written: they
    leave the ticker (2026-09-29). The card that stood in for them, Blip's "Waiting on week N" (storyboard
    UDoWgLMrzUHup5tX53zaue option B), left on 2026-10-05 with the Results row: the Recap row takes that
    slot of the page. Weather and Top 5 read next week's data and stay. Hurt is Need to know since
    2026-09-29, above the rows: with nobody hurt it says so, and once the week is over it waits on next
    week's report."""
    page, errors = mount("digest", size=PHONE)
    dg = DigestPage(page)
    # The fixture's page week is 2, the packet's is 3: the page week is set to the packet's, as it is live.
    dg.set_clock("2026-09-20T12:00:00Z", nobody_out=True, packet_week=True)
    before = dg.row_ids()
    assert "mu" in before and "hurt" not in before
    assert dg.need_none() == "Nobody new is out since Tuesday."
    dg.set_clock("2026-09-22T12:00:00Z", nobody_out=True, packet_week=True)
    after = dg.row_ids()
    assert not {"hurt", "mu", "wait"} & set(after) and ("wx" in after or "t5" in after)
    # The page week is the packet's (3) and every game of it has kicked off: the row waits for the next
    # week's report, never "Week 3's" for a week that is over (2026-10-05).
    assert dg.need_none() == "Week 4's injury report is still in the trainer's room."
    assert dg.retired_wait_card() == 0
    # Blip's voice for a Matchups row with nothing to call stays (digest.js dgMuNone): one of three lines,
    # never the record (2026-09-29, David: "say something funny ... instead of boring stats").
    blip = dg.blip_jokes()
    assert blip["drawn"] in blip["jokes"]
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Digest", ac="every row of the wall has its grid area in every state the fixture week reaches")
def test_every_wall_row_has_its_area(mount):
    """On a desktop the ticker is a grid of named bands, and a band set per state (wall.css). A row whose
    area the state's template lacks makes the grid invent columns for it, and every band shrinks to a
    sliver: the Starters row and the finished-week wait card landed on two branches, each passing, and
    together broke the wall (2026-09-29). So every state the fixture week reaches, from before its first
    game to after its last, and with each band that comes and goes: each row's area is in the template."""
    page, errors = mount("digest", size=WALL)
    dg = DigestPage(page)
    seen = {}
    clocks = ("2026-09-10T12:00:00Z", "2026-09-14T18:00:00Z", "2026-09-17T12:00:00Z", "2026-09-18T12:00:00Z",
              "2026-09-21T20:00:00Z", "2026-09-22T00:30:00Z", "2026-09-22T12:00:00Z", "2026-09-24T12:00:00Z")
    # Each clock with the Recap link, then two without it (a recap under half final draws no link).
    for at, hide in [(c, False) for c in clocks] + [("2026-09-18T12:00:00Z", True), ("2026-09-22T12:00:00Z", True)]:
        got = dg.plant_wall_clock(at, hide)
        seen[got["cls"]] = at
        assert got["missing"] == [], f"{at} ({got['cls']}): rows with no area in the template: {got['missing']}"
        assert got["cols"] == 12, f"{at} ({got['cls']}): {got['cols']} columns, the wall has 12"
    # The fixture week must reach the finished-week layout, with and without the Recap link, or the
    # check above never saw it (the recap fixture's week ends Monday 2026-10-05, so the link shows all of September).
    assert any("wk-done" in c for c in seen), seen
    assert any("wk-done" in c and "has-recap" in c for c in seen) and any("wk-done" in c and "has-recap" not in c for c in seen), seen
    assert any("has-recap" in c and "wk-done" not in c for c in seen) and any("has-recap" not in c for c in seen), seen
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Digest", ac="a lead about one player and a name in Top 5 open his profile")
def test_every_player_opens_his_profile(mount):
    """A lead about one player and a name in Top 5 open his profile, like every other Digest row
    (2026-09-29, David: "should we be able to click on players to open their profile?"). Top 5 took
    this from Risers & fallers, which left the Digest the same day."""
    page, errors = mount("digest", size=WALL)
    dg = DigestPage(page)
    dg.set_clock("2026-09-18T12:00:00Z")                  # inside the fixture week
    assert dg.lead_buttons()["all"] == 1
    slug = dg.lead_slug()
    dg.tap_lead()
    assert dg.profile_open()
    assert dg.profile_has_title()
    dg.close_profile()
    dg.early()                                            # Ranks' fixture week is ahead of it
    name = dg.tap_top5_first_row()
    assert name.split(". ")[-1].upper() in dg.profile_title().upper()
    assert slug
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Digest", ac="Top 5 links to Ranks; one call reads as 1 call")
def test_top_5_links_to_ranks_and_one_call_is_singular(mount):
    """Top 5 is next week's projections, so it goes to Ranks, the same projections for every player
    (2026-09-29; it went to Leaders, the season's stat leaders). A lone call reads "1 call"."""
    page, errors = mount("digest", size=WALL)
    dg = DigestPage(page)
    assert dg.row_go("t5") == "ranks"
    dg.plant_one_call()
    # the link names the view, not a count of takes against FantasyPros (2026-10-04)
    assert [dg.row_go_text("mu"), dg.row_line_text("mu")] == ["Start/Sit", "1 call this week"]
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Digest", ac="every news line opens its story in a new tab; the face and name open the profile")
def test_every_news_line_opens_its_story(mount):
    """2026-09-30 (David: "For the news on the digest, it should link to the news source"): each line is
    a link to its story in a new tab, the story's own page when ff-jarvis kept one, else a search for the
    headline; the face and name still open the profile, and no link sits inside a button."""
    page, errors = mount("digest", size=WALL)
    dg = DigestPage(page)
    lines = dg.news_lines()
    assert lines and all(a and a["target"] == "_blank" and "noopener" in a["rel"] for a in lines), lines
    assert dg.news_nested_controls() == 0 and dg.news_names_open_profiles()
    assert sorted(a["href"] for a in lines) == sorted(dg.news_expected_hrefs())
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Digest", ac="Need to know leads with new starters, then who sits; a started game takes its starters out")
def test_need_to_know_leads_with_new_starters_then_who_sits(mount):
    """Need to know (2026-09-29, storyboard 96B1dMss6vfyhhsQLUSK4x B) lies open under the banner: Sleeper's
    new #1s and team moves first, tagged "New QB1" or "New team" with over whom (with his status), then
    the packet's out, IR and doubtful, then one line of the questionable. Five lines, then "N more".
    News no longer carries the starters, and they go with the team's kickoff."""
    page, errors = mount("digest", size=PHONE)
    dg = DigestPage(page)
    dg.plant_need_clock("2026-09-17T12:00:00Z")
    tags, lines = dg.need_tags(), dg.need_lines()
    assert tags[:4] == ["New QB1", "New QB1", "New team", "New RB1"]
    # The tag says "New QB1", so the line starts at "over" (2026-09-29); every line leads with a face.
    assert lines[:4] == ["over S. Sanders", "over J. Daniels (Out)", "MIN → NYG · QB3", "over J. Mason"]
    assert dg.need_faces_lead()
    # The fixture makes 8 lines: five shown, then "3 more"; and some players are questionable.
    assert tags == ["New QB1", "New QB1", "New team", "New RB1", "OUT"]
    assert dg.need_more() == "3 more"
    assert dg.need_has_questionable_line()
    assert dg.need_questionable_taps_open_profiles() and dg.news_new_starter_blocks() == 0
    dg.start_games_of_new_starters()
    assert dg.need_tag_count() == 0, "a started game takes its starters out of Need to know"
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Digest", ac="Sleeper adds read as counts")
def test_sleeper_adds_read_as_counts_on_the_digest(mount):
    page, errors = mount("digest", size=PHONE)
    dg = DigestPage(page)
    dg.plant_sleeper_adds("2026-09-22T12:00:00Z")           # a Tuesday: adds lies open
    assert dg.row_count_text("adds") == "4.0M"
    assert dg.row_line("adds") == "Ollie Gordon II 4.0M adds"
    assert "Sleeper trending" in dg.row_foot("adds")
    assert dg.row_plus("adds") == ["4.0M", "833K"]
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Digest", ac="a started game drops its rows live and the lead gives way")
def test_a_started_game_drops_its_rows_live_and_the_lead_gives_way(mount):
    """The Friday packet read on Monday morning: nothing about a Sunday game survives in the
    browser, the lead falls to the top headline (it fell to the week's results until 2026-10-05, when
    those moved to Recap), and the stamp says how old the packet is."""
    page, errors = mount("digest", size=PHONE)
    dg = DigestPage(page)
    dg.set_clock("2026-09-28T13:00:00Z")      # the page's clock is its own after load
    # the hurt starter's game has started, so the banner is the top headline, never a results call
    assert dg.packet_lead() == {"rule": "news", "index": 0}
    assert dg.headline() == dg.packet_first_headline()
    assert dg.lead_pills() == 0
    assert dg.lead_when() == "Week 3 · updated Fri 10:40 PM"
    assert dg.row_count("res") == 0 and dg.open_row_count() == 0
    assert "LA@DEN" not in dg.packet_hurt_games()
    # The fixture schedule holds one week-3 game, so give one top-5 row a Sunday kickoff by hand.
    n = dg.packet_top5_count()
    dg.plant_sunday_top5_kickoff()
    assert dg.packet_top5_count() == n - 1
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Digest", ac="the wall opens every panel and a head is not a toggle")
def test_the_wall_opens_every_panel_and_a_head_is_not_a_toggle(mount):
    """From 1100px the Digest is a wall (2026-09-26): every topic open, the day's row marked, the
    lead's ghost naming why he leads. A tap on a panel's head must not close it."""
    page, errors = mount("digest", size=WALL)
    dg = DigestPage(page)
    assert dg.panel_row_count() == dg.open_row_count() > 0      # the Recap link is a band to tap, not a panel that opens
    assert dg.link_row_count() == 1 and dg.open_link_row_count() == 0
    dg.tap_head("adds")
    assert dg.row_is_open("adds")
    assert dg.ghost() == "WR2"
    assert dg.fits()
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Digest", ac="Top 5 is Ranks' own rows under position tabs, tiers in Ranks' colours")
def test_top_5_is_ranks_own_rows_under_position_tabs(mount):
    """2026-09-29, storyboard Ms6FbdvynVPoRTKEidPGAz 5A (David: "it's supposed to be forward looking ...
    like a mini feed of our rankings"): Top 5 reads LIVE_RANKS, the rows Ranks draws, never the packet,
    so the two cannot disagree. A tab per position and FLEX, five rows each, a tap swaps them."""
    page, errors = mount("digest", size=PHONE)
    dg = DigestPage(page)
    dg.early()
    dg.tap_head("t5")
    want = dg.t5_expected()
    assert dg.t5_tabs() == list(want)
    for pos in want:
        dg.pick_t5(pos)
        assert dg.t5_slugs(pos) == want[pos], pos
    first = dg.ranks_first_pts("QB")
    dg.pick_t5("QB")
    assert dg.t5_first_pts("QB") == first
    assert dg.row_go("t5") == "ranks"
    # Tiers in Ranks' colours (2026-09-29, David: "colors for T1, T2, T3 so it's easily scannable"):
    # Tier 1 filled lime, a lower tier an outline, a different colour per tier.
    tiers, lime = dg.t5_tiers(), dg.lime()
    assert all(bg == f"rgb({lime})" for name, bg, _ in tiers if name == "T1")
    colours = {name: c for name, _, c in tiers if name != "T1"}
    assert len(set(colours.values())) == len(colours)
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Digest", ac="Start of the week heads the Matchups card; the foot is Start/Sit's record")
def test_start_of_the_week_heads_the_matchups_card(mount):
    """2026-10-03, David: yes to a Start of the week: our boldest START (Start/Sit v3: the widest gap
    between our rank and his season average), first in the Matchups card, our rank over his average
    on the right. None: no row. The foot is Start/Sit's record, SMASH, START and SIT as hit-miss."""
    page, errors = mount("digest", size=PHONE)
    dg = DigestPage(page)
    want = dg.start_take()
    dg.open_row("mu")
    first = dg.first_ln("mu")
    assert first["sotw"] == "Start of the week"
    assert first["slug"] == want["slug"]
    assert first["right"] == f"{want['pos']}{want['rank']} avg {want['pos']}{want['avg_rank']}"
    foot = dg.row_foot_text("mu")
    assert foot.startswith("Record since week 5: SMASH 7-3, START 2-2, SIT 4-1.")
    # 2026-10-06: the foot says what each call has been through (12.61, 12.73, 12.75), and the label loses its lime.
    assert "Failed test (12.61, 12.73)" in foot and "Failed test (12.75)" in foot and "Untested" in foot
    assert dg.sotw_color() != dg.lime(), "plain until the week-9 review of START"
    assert "Failed test (12.75)" in dg.sotw_title()
    dg.plant_no_start_take()
    assert dg.sotw_count() == 0
    assert dg.row_foot_text("mu").startswith("Record starts with week 5.")
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Digest", ac="Weather counts the Weather view's games; a calm week draws no row on a phone and a sentence on the wall")
def test_weather_is_the_weather_tabs_own_games(mount):
    """2026-09-29, 6A (David: "the next tab over is the weather and it's actually already live"): the
    row counts the games the Weather view says move scoring (wtRows().moves, still to kick off) and
    links there. A calm week draws no row on a phone and one quiet sentence on the wall."""
    page, errors = mount("digest", size=PHONE)
    dg = DigestPage(page)
    dg.early()
    dg.plant_weather_moves(True)
    assert dg.row_count_text("wx") == "1"
    assert dg.row_line("wx") == "Rain in 1 game"
    dg.tap_head("wx")
    assert dg.weather_games() == 1 and dg.weather_readings() == ["60%"]
    assert dg.row_go("wx") == "weather"
    dg.plant_weather_moves(False)
    assert dg.row_display("wx") == "none"
    assert errors == []
    page, errors = mount("digest", size=WALL)               # the same calm week on the wall
    dg = DigestPage(page)
    dg.early()
    dg.plant_weather_moves(False)
    assert dg.row_display("wx") != "none"
    assert dg.row_line("wx") == "No game's weather moves scoring"
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Digest", ac="every topic label carries its icon, stroked in the label's colour")
def test_every_topic_label_carries_its_icon(mount):
    """2026-09-29, 3A: a drawn icon beside every topic's label, stroked in the label's own colour."""
    page, errors = mount("digest", size=PHONE)
    got = DigestPage(page).icons_match_labels()
    assert got and all(ok for _, ok in got), got
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Digest", ac="a headline naming no player is a plain block and keeps the Digest up")
def test_a_headline_naming_no_player_keeps_the_digest_up(mount):
    """2026-09-29, David: "the digest is broken". A defender's IR move came through with a slug and no
    name; News keyed a block to the slug, avatarHTML read the missing name, and the throw blanked the
    whole Digest. A headline naming no player is a plain block of its own, whatever it carries."""
    page, errors = mount("digest", size=WALL)
    dg = DigestPage(page)
    dg.plant_news_without_a_player()
    block = dg.news_block_with("Jalen Davis")
    assert errors == []
    assert dg.row_ids()
    assert block and block["tag"] == "DIV" and "Jalen Davis placed on IR" in block["text"]   # a plain block, not a profile button


@pytest.mark.req("Digest", ac="a starter row leaves at the team's next kickoff")
def test_a_starter_row_leaves_at_the_teams_next_kickoff_after_its_game():
    """ff-jarvis measures a row from the team's latest game (`since`); the page drops it at the next
    one, in the schedule's dialect whatever the packet's (LA is LAR there)."""
    from digest import next_kick
    assert next_kick(SCHEDULE, "LA", "2026-09-20 17:00:00") == "2026-09-28T00:20:00Z"
    assert next_kick(SCHEDULE, "LA", "2026-09-28 00:20:00") == "2026-10-04T17:00:00Z", "Monday night's trade waits for week 4"
    assert next_kick(SCHEDULE, "WAS", "2026-09-27 17:00:00") is None
    assert next_kick(None, "LA", "2026-09-20 17:00:00") is None


@pytest.mark.req("Digest", ac="the fixture block is whole")
def test_fixture_block_is_whole():
    b = _block()
    contract.validate("LIVE_DIGEST", b)
    assert b["week"] == 3 and b["lead"] == {"rule": "hurt", "index": 0}
    assert [len(b[k]) for k in ("hurt", "best", "wx", "adds", "top5", "up", "down", "gems", "news")] == \
        [12, 4, 1, 6, 20, 5, 5, 5, 10]


@pytest.mark.req("Digest", ac="kickoffs are Pacific words")
def test_kickoffs_are_pacific_words():
    b = _block()
    assert b["hurt"][0]["game"] == {"away": "LA", "home": "DEN", "kick": "Sun 5:20 PM",   # 00:20 UTC Monday
                                    "ko": "2026-09-28T00:20:00Z"}
    assert b["wx"][0]["kick"] == "Sun 10:00 AM"
    assert b["hurt"][4]["game"] is None                                                    # Dart, on IR


@pytest.mark.req("Digest", ac="best spots keep position order and slugs")
def test_best_spots_keep_position_order_and_slugs():
    b = _block()
    assert [(r["pos"], r["n"]) for r in b["best"]] == [
        ("QB", "C.J. Stroud"), ("RB", "Quinshon Judkins"), ("WR", "CeeDee Lamb"), ("TE", "Pat Freiermuth")]
    assert b["best"][2]["slug"] == slugify("CeeDee Lamb") and b["best"][2]["home"] is True


@pytest.mark.req("Digest", ac="a headline splits at its tag and takes a news kind")
def test_headline_splits_at_its_tag_and_takes_a_news_kind():
    news = _block()["news"]
    assert news[0]["n"] == "Jaylen Wright" and news[0]["rest"] == "doubtful to play Sunday"
    assert news[0]["when"] == "8:31 AM" and news[0]["kind"] == "injury"
    assert news[7]["kind"] == "out"                         # "Josh Simmons (back) ruled out for Sunday"
    assert news[0]["slugs"][0] == "jaylen-wright"


@pytest.mark.req("Digest", ac="Tonight carries the card's facts with slugs and kickoff")
def test_tonight_carries_the_card_facts_with_slugs_and_kickoff():
    b = _block()
    assert b["tonight_last"] is True
    g = b["tonight"][0]
    assert (g["away"], g["home"], g["kick"], g["ko"]) == ("PHI", "CHI", "Mon 5:15 PM", "2026-09-29T00:15:00Z")
    assert g["wx"] == {"roof": "outdoor", "temp_f": 64, "wind_mph": 5, "precip_pct": 1, "short": "Mostly Clear"}
    assert [(r["n"], r["status"], r["injury"]) for r in g["out"]][0] == ("Caleb Williams", "Out", "Hamstring")
    assert g["next_up"][0]["for"] == "Caleb Williams" and g["next_up"][0]["n"] == "Case Keenum"
    assert "groups" not in g and "moved" not in g, "12.46 failed: the books' moves are not carried to the page (2026-10-06)"
    assert [r["call"] for r in g["tcalls"]] == ["BEST", "BEST", "START"]
    assert g["projected"][0]["slug"] == slugify("Jalen Hurts")
    assert live_digest({**load_digest(), "tonight": {"games": [], "last": False}}, slugify)["tonight"] == []


SLEEPER_ADDS = {"source": "sleeper", "hours": 24, "fetched": "2026-09-28 05:52", "weeks": [], "rows": [
    {"key": "ollie gordon", "name": "Ollie Gordon II", "pos": "RB", "team": "MIA", "count": 4039301,
     "was": None, "now": None, "delta": None},
    {"key": "kenyon sadiq", "name": "Kenyon Sadiq", "pos": "TE", "team": "NYJ", "count": 832977,
     "was": None, "now": 35.2, "delta": None}]}


@pytest.mark.req("Digest", ac="Sleeper adds carry their source and count")
def test_sleeper_adds_carry_their_source_and_count():
    b = live_digest({**load_digest(), "adds": SLEEPER_ADDS}, slugify)
    contract.validate("LIVE_DIGEST", b)
    assert (b["adds_source"], b["adds_hours"], b["adds_weeks"]) == ("sleeper", 24, [])
    assert [(r["n"], r["count"], r["now"]) for r in b["adds"]] == [("Ollie Gordon II", 4039301, None),
                                                                  ("Kenyon Sadiq", 832977, 35.2)]
    # A packet from before 2026-09-28 has no source: it was the ESPN cut.
    old = {**load_digest(), "adds": {"weeks": [2, 3], "rows": []}}
    assert live_digest(old, slugify)["adds_source"] == "espn"


@pytest.mark.req("Digest", ac="an untagged headline does not say his name twice")
def test_an_untagged_headline_does_not_say_his_name_twice():
    """The Monday 2026-09-28 page read "Travis Etienne Travis Etienne Jr. exits early Sunday"."""
    p = json.loads(json.dumps(load_digest()))
    p["news"] = [{"created": "2026-09-27 20:47:00", "headline": "Travis Etienne Jr. exits early Sunday",
                  "key": "travis etienne", "name": "Travis Etienne"}]
    it = live_digest(p, slugify)["news"][0]
    assert (it["n"], it["rest"]) == ("Travis Etienne", "exits early Sunday")


@pytest.mark.req("Digest", ac="Top 5 flattens by position")
def test_top5_flattens_by_position():
    top5 = _block()["top5"]
    assert [r["pos"] for r in top5[::5]] == ["QB", "RB", "WR", "TE"]
    assert top5[0]["n"] == "Josh Allen"


@pytest.mark.req("Digest", ac="empty sections are empty lists, not errors")
def test_empty_sections_are_empty_lists_not_errors():
    p = json.loads(json.dumps(load_digest()))
    p.update(lead=None, hurt=[], news=[], gems=[], top5={}, stock={"up": [], "down": []},
             adds={"weeks": [2, 3], "rows": []}, weather={"games": [], "near": None},
             matchups={"calls": 0, "best": {}, "record": None})
    b = live_digest(p, slugify)
    contract.validate("LIVE_DIGEST", b)
    assert b["lead"] is None and b["near"] is None and b["best"] == [] and b["record"] is None


@pytest.mark.req("Digest", ac="no packet is no block")
def test_no_packet_is_no_block():
    assert live_digest(None, slugify) is None
    contract.validate("LIVE_DIGEST", None)
    assert "no weekly_digest.json" in report(None)


@pytest.mark.req("Digest", ac="the data layer calls no surface function")
def test_the_digests_data_layer_calls_no_surface_function():
    """model -> contract -> view: data/digest.js (dgWaiting reads the last game's slot) names nothing
    that surface/digest/ declares, so it works with the surface files gone."""
    src = pathlib.Path(__file__).resolve().parents[1] / "design" / "src" / "js"
    data = (src / "data" / "digest.js").read_text(encoding="utf-8")
    declared = set()
    for f in (src / "surface" / "digest").glob("*.js"):
        declared |= set(re.findall(r"^(?:function|const|let)\s+([A-Za-z_]\w*)", f.read_text(encoding="utf-8"), re.M))
    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", data, flags=re.S)
    leaked = sorted(n for n in declared if re.search(rf"(?<![\w.]){n}\b", code)
                    and not re.search(rf"^(?:function|const|let)\s+{n}\b", code, re.M))
    assert leaked == []
    assert "function dgMnfSlot" in data and "function dgWeek" in data
