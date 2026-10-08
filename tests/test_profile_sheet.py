"""The profile's stat sheet: the sphere in the head, the radar and the ladder it opens, the elite glow,
the measured-axes rules. The tests that press Back are test_profile_journeys.py. Each test mounts the
roster and works through pages/profile.py (see test_profile.py)."""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.roster import on_roster
from wording import words

REQ = "The profile modal"
ST_BROWN = "Amon-Ra St. Brown"
ST_BROWN_SLUG = "amonra-st-brown"


@pytest.mark.render
@pytest.mark.req(REQ, ac="the sphere turns from the moment the profile opens, rests, stops when shut, and never turns under reduced motion")
def test_the_sphere_turns_rests_and_stops(mount):
    """STYLE.md rule 1 as rewritten on 2026-09-28: a tap cue may move, slowly, only while it can be
    seen, resting where its data reads, and never under reduced motion. The sphere starts turning as
    the profile opens (2026-09-30; it used to hold still 2 s first) and rests after the turn; a shut
    profile stops it."""
    profile, errors = on_roster(mount)
    try:
        profile.allow_motion(True)
        profile.open_from_roster(ST_BROWN)
        profile.wait_orb_turning(0)                           # it has started turning
        turned = profile.orb_yaw()
        profile.wait_orb_turning(turned)                      # and it keeps turning
        profile.close()
        profile.frames(2)
        shut = profile.orb_yaw()
        profile.hold_frames()                                 # twenty frames of a shut profile, run on the test's clock: still
        profile.run_frames(20)
        assert profile.orb_yaw() == shut
        profile.release_frames()
        profile.allow_motion(False)
        # The old bug held the sphere still for 2 s and then turned it, so a short run would pass a
        # regression to "hold, then turn" under reduced motion. The page's frames are queued and run by the
        # test, 170 of them stamped 16.7 ms apart (2.8 s of the page's own time), instead of waiting that long.
        profile.hold_frames()
        profile.open_from_roster(ST_BROWN)
        profile.wait_orb()
        profile.run_frames(170)
        assert profile.orb_yaw() == 0
        assert errors == []
    finally:
        profile.release_frames()
        profile.allow_motion(False)


@pytest.mark.render
@pytest.mark.parametrize("viewport", [(360, 740), (1400, 900)])
@pytest.mark.req(REQ, ac="the sheet holds still under a fold, a wheel on the scrim and a swipe on the scrim")
def test_the_sheet_holds_still_under_a_tap_and_a_scroll(mount, viewport):
    """2026-09-29, David: tapping a stat "will expand the shape of the container which causes the
    content to jump", and "scrolling or swiping on this modal will move the content behind it".
    The sheet opens centred and keeps that top (orbsheet.js orbPin), so a fold grows it downward;
    a wheel on the scrim or on a sheet with nothing to scroll moves neither the profile nor the page."""
    profile, errors = on_roster(mount, viewport)
    profile.open_from_roster(ST_BROWN)
    profile.open_sheet()
    top = profile.radar_top()
    profile.fold_last_stat()
    assert profile.open_folds() == 1
    assert profile.radar_top() == pytest.approx(top, abs=1)
    before = profile.scroll_state()
    profile.wheel_over_scrim()
    assert profile.scroll_state() == before
    # A sideways swipe on the scrim leaves the profile's tab where it was (modal.js up()).
    was = profile.selected_tab()
    profile.swipe_over_scrim()
    assert profile.selected_tab() == was
    assert profile.layers() == 1
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="a stat over the position's elite bar glows on the ladder row, the radar label and the vertex, and nothing else does")
def test_an_elite_stat_glows(mount):
    """Ranked and over the position's elite bar (sheet.js sheetElite): the ladder row and the radar
    label and vertex carry `elite`, and nothing else does."""
    profile, errors = on_roster(mount)
    profile.open_from_roster(ST_BROWN)
    profile.open_sheet()
    want = profile.elite_expected(ST_BROWN_SLUG)
    assert want, "the fixture needs an elite stat for this receiver"
    assert {kind: profile.elite(kind) for kind in ("row", "label", "dot")} == {"row": want, "label": want, "dot": want}
    assert profile.elite_glow() != "none"
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="the sheet draws the position's own axes, ranked, with a ladder best first that folds out its definition")
def test_stat_sheet_draws_the_positions_own_axes(mount):
    """ff-jarvis's `sheet.axes` drives the shape: six for a receiver, none of them a raw count
    the Grid already shows. Every number is his season rank among the position ("#3", "#3*" on a
    tie), first place at the rim. Each label is a button, and the ladder under the chart lists
    every stat best first; a label and its row light together, and the row folds out the
    definition and the elite gap."""
    profile, errors = on_roster(mount)
    profile.open_from_roster(ST_BROWN)
    profile.open_sheet()
    assert profile.radars() == 1
    counts = profile.radar_counts()
    assert counts["shape"] == 1
    assert counts["rings"] == 4
    axes = profile.sheet_axes("WR")
    assert axes == ["wopr", "route_pct", "tprr", "yprr", "fdrr", "rz_tgt"]
    assert counts["labels"] == len(axes)
    assert profile.radar_labels_named("aDOT") == 0           # not "more is better"
    rank, of, _tied = profile.stat_rank("WR", "wopr", ST_BROWN_SLUG)
    mark = profile.rank_mark("WR", "wopr", ST_BROWN_SLUG)
    assert rank >= 1 and of >= rank
    # No tie marker anywhere, from 2026-09-22: rankAmong already shares the rank, and the
    # asterisk on top only said "someone else has this number", which decides nothing.
    assert mark == f"#{rank}"
    assert "*" not in profile.radar_text()
    # Rank first, then the stat's plain name (HTML labels over the chart since 2026-09-25).
    assert f"{mark}{words('profile.axis.wopr')}" in profile.radar_box_text()
    assert profile.sheet_caps() == 0
    # The ladder under the chart (2026-09-29): every stat at once, best first, each row with its
    # own denominator (everyone with a target, but only those with routes).
    cols = profile.ladder_cols()
    assert len(cols) == len(axes)
    pct = profile.ladder_percentiles(cols)
    assert pct == sorted(pct, reverse=True)
    wopr = profile.lr("wopr")
    assert wopr["on"]
    assert wopr["rank"] == [mark, "of", str(of)]
    # Folded: the definition is a tap away, not a paragraph in the way of the numbers.
    assert not wopr["def_visible"]
    profile.toggle_ladder("wopr")
    wopr = profile.lr("wopr")
    # The gap, not the threshold: "elite >= 0.00" printed in red said the elite bar was the bad
    # thing, when what is red is him being under it. The colour agrees with the sign.
    assert wopr["gap"] == "0.11 over the elite bar (0.70)"
    assert wopr["gap_up"]
    # And the initials are defined, with a second clause on what to do with the number.
    assert "air yards" in wopr["def"]
    assert "predictor" in wopr["why"]
    assert profile.label_lit(words("profile.axis.wopr"))
    assert profile.lit_dot() == "wopr"
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="a label or row tap lights the chart and the row together and opens that row alone")
def test_a_label_tap_lights_the_chart_and_opens_that_row_alone(mount):
    """The ladder's rows and the radar's labels move one highlight: a label tap opens its row and shuts
    the one open before it; a row tap moves the chart."""
    profile, errors = on_roster(mount)
    profile.open_from_roster(ST_BROWN)
    profile.open_sheet()
    profile.toggle_ladder("wopr")
    assert profile.lr("wopr")["open"]
    assert profile.label_lit(words("profile.axis.wopr"))
    # A label tap lights the chart and the row together and opens that row alone.
    profile.tap_label("Yds/route")
    yprr = profile.lr("yprr")
    assert yprr["on"] and yprr["open"]
    assert not profile.lr("wopr")["open"]
    assert not profile.label_lit(words("profile.axis.wopr"))
    assert profile.lit_dot() == "yprr"
    assert yprr["rank_small"] == f"of {profile.stat_rank('WR', 'yprr', ST_BROWN_SLUG)[1]}"
    # And a row tap moves the chart.
    profile.toggle_ladder("rz_tgt")
    profile.wait_lit_dot("rz_tgt")                           # the fold's toggle fires a task later
    assert "pctl" not in profile.text()
    profile.press_escape()
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="every block says how many weeks it covers, and a stat with weekly rows names its window")
def test_every_block_says_how_many_weeks_it_covers(mount):
    """The blocks do not share a window. Red zone and target depth are season to date; anything
    divided by routes waits on heatradar, which publishes one week at a time, so Route%, TPRR,
    YPRR and 1D/RR can be a one-week number sitting on the same chart as two-week ones. A number
    whose window is not stated cannot be checked -- which is exactly how a correct red-zone
    figure came to look wrong."""
    profile, errors = on_roster(mount)
    profile.open_from_roster(ST_BROWN)
    profile.tab("usage")
    assert profile.windows() == {"DET TARGETS": "2 wk", "TARGET DEPTH": "2 wk", "RED ZONE": "2 wk"}   # .lbl uppercases in the render
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="a stat with weekly rows names its window in its ladder row's fold")
def test_a_stat_names_its_window_in_its_ladder_row(mount):
    """Per stat, in its ladder row's fold. Three states, because the fixture has no weekly rows
    for the sheet stats and that is itself one of them."""
    profile, errors = on_roster(mount)
    profile.open_from_roster(ST_BROWN)
    profile.open_sheet()
    profile.tap_label("Yds/route")
    assert profile.ladder_facts("yprr")[-1] == "2 gm"          # no weekly rows: games, no window
    assert profile.plant_stat_weeks(ST_BROWN_SLUG, "yprr", [1, 2]) == "wk 1–2"   # two weeks: the range, no games
    # Now as heatradar actually publishes it: week 1 only, while his other stats have two.
    assert profile.plant_stat_weeks(ST_BROWN_SLUG, "yprr", [1]) == "wk 1"
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="under three measured axes the radar draws no shape, only the vertices and a count")
def test_too_few_measured_axes_draw_no_shape(mount):
    """Under three measured axes there is no shape, and <polygon> with two points renders as a
    bare line between them -- which reads as a broken chart rather than as a player heatradar
    has not covered yet. The vertices still plot, because they are real, and the count says why
    the rest is missing. (Rashee Rice in week 2: WOPR and RZ Tgts measured, the four
    route-derived stats not.)"""
    profile, errors = on_roster(mount)
    profile.open_from_roster(ST_BROWN)
    profile.open_sheet()
    counts = profile.radar_counts()
    assert counts["shape"] == 1                              # six axes: a real shape
    assert counts["notes"] == 0
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="with four of six axes stripped the radar draws two vertices, no shape and a count")
def test_two_measured_axes_draw_the_vertices_a_count_and_no_shape(mount):
    """Strip four of his six axes: two points left, so no polygon and a count instead."""
    profile, errors = on_roster(mount)
    profile.strip_axes(ST_BROWN_SLUG, ["route_pct", "tprr", "yprr", "fdrr"])
    profile.open_from_roster(ST_BROWN)
    profile.open_sheet()
    counts = profile.radar_counts()
    assert counts["shape"] == 0
    assert counts["dots"] == 2
    assert profile.radar_note() == "2 of 6 stats measured"
    assert profile.radar_box_text().count("—") == 4          # the unmeasured axes say so
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="each position gets its own axes, and the sphere and sheet wear the position's tint")
def test_each_position_gets_its_own_shape(mount):
    """A back's sheet is opportunity and rushing talent, a passer's is volume and his legs.
    Four to six axes each, and the sheet is tinted by position so a run of profiles reads
    QB/RB/WR/TE without anyone reading the label."""
    profile, errors = on_roster(mount)
    axes = profile.sheet_axes()
    assert axes["RB"] == ["wopp", "opp_pct", "route_pct", "rz", "ryoe", "brk_rate"]
    assert axes["QB"] == ["dropbacks", "designed_pct", "scr_rate", "gl_pct", "rz_att", "fp_db"]
    assert axes["TE"] == axes["WR"]
    assert [pos for pos, ids in axes.items() if not 4 <= len(ids) <= 6] == []
    assert [pos for pos, ids in axes.items() if len(set(ids)) != len(ids)] == []
    profile.open_from_roster("Chase Brown")
    assert profile.orb_tint()["orb"] == "pos-rb"             # the sphere wears the tint too
    profile.open_sheet()
    assert profile.orb_tint()["sheet"] == "pos-rb"
    assert profile.radar_counts()["labels"] == 6
    profile.press_escape()
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="the elite glow reads ff-jarvis's fluke filter: a raw clear on a thin sample does not glow and says why")
def test_elite_reads_the_fluke_filter(mount):
    """St. Brown's fixture row clears the WOPR and TPRR bars raw, but the filter keeps WOPR only:
    WOPR glows, TPRR does not and says the sample is too small, and a bar with no history behind
    it is dotted and named."""
    profile, errors = on_roster(mount)
    profile.open_from_roster(ST_BROWN)
    profile.open_sheet()
    assert profile.lr("wopr")["elite"]
    assert not profile.lr("tprr")["elite"]
    profile.toggle_ladder("tprr")
    text = profile.lr("tprr")["text"]
    assert "too few games" in text
    assert "published analyst standard" in text
    assert profile.bar_provisional("tprr")
    assert not profile.bar_provisional("wopr")
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="a rate under its sample floor shows its sample, says why it has no rank, and sorts under every ranked stat")
def test_a_rate_under_its_floor_shows_its_sample_and_no_rank(mount):
    """2026-09-26: M. Stafford's 33% goal-line share was 1 of 3 and ranked 85th percentile. In the
    fixture L. Jackson is 1 of 4 against a floor of 5, J. Allen 3 of 5. Below the floor the number
    stays, says what it is out of, and nothing ranks it: not the radar, not Leaders."""
    profile, errors = on_roster(mount)
    got = profile.floor_probe()
    assert got["rank"] is None and got["allen"] is not None
    unit = words("profile.sample.teamGlCar")
    assert f"1 of 4 {unit}" in got["facts"]
    # Why there is no rank, in words: the floor, and what a rate on fewer would be.
    assert got["floor"] == "Ranked from 5 team carries inside the 5: a rate on fewer is one game's noise, not a season."
    assert got["dim"] == "pf-lr-v dim"
    assert got["have"] == f"4 of 5{unit}" # his sample against the floor, not a rank
    assert got["last"]                                       # unranked rows sit under every ranked one
    assert f"3 of 5 {unit}" in got["allenFacts"] and got["allenFloor"] == 0
    assert got["allenRk"].startswith("#")
    assert got["held"] == ["3/4", "2/3", "1/4"]           # C. Ward 75%, T. Shough 66.7%, L. Jackson 25%
    assert errors == []
