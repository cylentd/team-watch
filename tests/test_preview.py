"""This week > Preview (2026-09-29, storyboard option A): a slate of every game by kickoff window,
and a tap opens the game's dossier. Rendered from the fixture build. Since 2026-10-05 (storyboard
https://claude.ai/artifact/NTeV8W2N9mFnYgftfbuqPV, picks 1A 2A 3A 4A) a game that is over leaves the slate
for Past games, which heads with Claude's season by bet, and the dossier's answer is one row per bet.

The fixture (tests/fixtures/data/game_previews.json) holds five games, one per window: PIT @ CLE on
Thursday (both on a short week), JAX @ LA on Sunday morning at Wembley (neutral site, wind 17 mph,
LA off a bye, Claude picks the underdog), DET @ CAR at 1:00 (rain 56%, Coker out, St. Brown
questionable, the only game with defense ranks), SF @ NYJ late (SF flew 3 zones east; the line
flipped), and ATL @ NO on Monday in a dome with no take, no rest, travel or site. SEED pins the clock
before all five.
"""
import json
import pathlib
import re

import pytest

import contract
from component import mount  # noqa: F401  (the fixture)
from pages.preview import PreviewPage
from preview import _ats, _base, _blind, _total, live_preview
from test_render import open_at

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "data" / "game_previews.json"


def slug(n):
    return re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")


@pytest.fixture(scope="module")
def block():
    return live_preview(json.loads(FIXTURE.read_text(encoding="utf-8")), slug)


def by_key(block):
    return {g["key"].split("_", 2)[2]: g for g in block["games"]}


def test_the_block_sorts_by_kickoff_into_windows(block):
    assert [(g["key"], g["slot"], g["et"]) for g in block["games"]] == [
        ("2026_02_PIT_CLE", "thu", "8:15 PM"), ("2026_02_JAX_LA", "sunam", "9:30 AM"),
        ("2026_02_DET_CAR", "sun1", "1:00 PM"), ("2026_02_SF_NYJ", "sunlate", "4:25 PM"),
        ("2026_02_ATL_NO", "mon", "8:15 PM")]


def test_the_line_is_a_favourite_and_a_margin_never_a_signed_spread(block):
    g = by_key(block)
    assert g["PIT_CLE"]["line"]["fav"] == "PIT" and g["PIT_CLE"]["line"]["by"] == 2.5   # spread_home +2.5: away favoured
    assert g["SF_NYJ"]["line"]["fav"] == "NYJ" and g["SF_NYJ"]["line"]["open"] == {"fav": "SF", "by": 3.0, "total": 43.5}
    assert g["ATL_NO"]["line"]["open"] is None                                           # no first line seen


def test_flags_are_at_most_two_in_priority_order(block):
    g = by_key(block)
    assert g["PIT_CLE"]["flags"] == [{"k": "short", "teams": ["CLE", "PIT"]}]
    assert g["JAX_LA"]["flags"] == [{"k": "upset"}, {"k": "wx", "wind": 17}]
    assert g["DET_CAR"]["flags"] == [{"k": "wx", "rain": 56}, {"k": "out", "n": "Jalen Coker", "slug": "jalen-coker"}]
    assert g["SF_NYJ"]["flags"] == [{"k": "upset"}, {"k": "moved", "flip": True, "by": 4.5}]
    assert g["ATL_NO"]["flags"] == []


def test_injuries_rest_travel_and_matchup(block):
    g = by_key(block)
    assert g["DET_CAR"]["inj"] == {"CAR": [{"n": "Jalen Coker", "slug": "jalen-coker", "pos": "WR", "s": "out", "avg": 14.4}],
                                   "DET": [{"n": "Amon-Ra St. Brown", "slug": "amon-ra-st-brown", "pos": "WR", "s": "q", "avg": None}]}
    assert g["DET_CAR"]["matchup"]["DET"]["pos"]["RB"] == {"pts": 29.4, "rank": 31}   # keyed by the offense
    assert g["SF_NYJ"]["travel"]["SF"] == {"zones": 3, "body": "13:25", "miles": 2570}
    assert g["JAX_LA"]["rest"]["LA"] == {"days": 13, "short": False, "bye": True}
    assert g["JAX_LA"]["site"] == {"stadium": "Wembley Stadium", "neutral": True}
    atl = g["ATL_NO"]
    assert (atl["rest"], atl["travel"], atl["site"], atl["matchup"], atl["take"]) == (None, None, None, None, None)
    gibbs = g["DET_CAR"]["take"]["players"][0]
    assert gibbs == {"n": "Jahmyr Gibbs", "slug": "jahmyr-gibbs", "pos": "RB", "team": "DET", "proj": 18.8,
                     "call": "up", "why": "The rain and the matchup both point to carries."}


def test_no_file_means_no_block():
    assert live_preview(None, slug) is None
    assert live_preview({"games": {}}, slug) is None


# Confidence and record (2026-09-29, storyboard option A). The fixture: PIT @ CLE no edge, JAX getting 3
# STRONG, DET giving 3.5 SOLID, SF getting 1.5 LEAN with no moneyline; ATL @ NO no take.
def test_the_confidence_fields_pass_through(block):
    g = by_key(block)
    jax = g["JAX_LA"]["take"]
    assert jax["win"] == {"JAX": 54} and jax["total"] == {"call": "under", "conf": "solid"}
    assert jax["ats"] == {"side": "JAX", "conf": "strong",
                          "edge": "Wind and eight time zones cut the Rams' passing; the line still prices a normal Stafford day."}
    assert g["PIT_CLE"]["take"]["ats"] == {"side": None, "conf": None, "edge": None}
    assert g["PIT_CLE"]["take"]["total"] == {"call": None, "conf": None}
    assert g["DET_CAR"]["market_win"] == {"DET": 64.4, "CAR": 35.6}
    assert g["DET_CAR"]["base"] == {"n": 1314, "wins": 67, "covers": 49, "home": None}
    assert g["SF_NYJ"]["market_win"] is None
    assert g["ATL_NO"]["take"] is None and g["ATL_NO"]["market_win"] == {"NO": 57.4, "ATL": 42.6}


def test_a_take_from_before_confidence_reads_null():
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    g = raw["games"]["2026_02_DET_CAR"]
    for k in ("win", "ats", "total", "blind", "vs_blind", "notes"):
        del g["take"][k]
    for k in ("ml", "market_win", "base"):
        del g["facts"]["line"][k]
    det = by_key(live_preview(raw, slug))["DET_CAR"]
    assert (det["take"]["win"], det["take"]["ats"], det["take"]["total"], det["market_win"], det["base"]) == (None,) * 5
    assert (det["take"]["blind"], det["take"]["vs_blind"], det["take"]["notes"]) == (None, None, [])


def test_the_research_pass_blind_number_and_notes(block):
    """ff-jarvis preview-research (2026-09-29): the blind number said like the line, never signed;
    a note's source is a web link or "pbp", anything else is dropped."""
    det = by_key(block)["DET_CAR"]["take"]
    assert det["blind"] == {"fav": "DET", "by": 1.5, "total": 48.5}      # margin_home -1.5: the away side
    assert det["vs_blind"].startswith("The blind number had DET by 1.5")
    assert det["notes"] == [
        {"text": "Carolina has allowed 5.1 yards a carry since week 1.", "source": "https://www.espn.com/nfl/story/_/id/1"},
        {"text": "Gibbs took 11 of Detroit's 14 red-zone carries last week.", "source": "pbp"},
        {"text": "Coker was ruled out Friday.", "source": None}]
    jax = by_key(block)["JAX_LA"]["take"]
    assert (jax["blind"], jax["vs_blind"], jax["notes"]) == (None, None, [])
    assert _blind({"margin_home": 0, "total": 44}, "NO", "ATL") == {"fav": None, "by": 0, "total": 44}
    assert _blind({"margin_home": 3.5}, "NO", "ATL") == {"fav": "NO", "by": 3.5, "total": None}


def test_a_side_without_a_confidence_is_no_edge():
    assert _ats({"side": "IND", "conf": None, "edge": "x"}) == {"side": None, "conf": None, "edge": None}
    assert _ats({"side": None, "conf": "strong", "edge": "x"}) == {"side": None, "conf": None, "edge": None}
    assert _total({"call": "over", "conf": "huge"}) == {"call": None, "conf": None}


def test_the_base_rate_reads_the_producers_percentages():
    # ff-jarvis preview_market's real 3.5-6.5 bucket, 2011-2025.
    pct = {"bucket": "3.5-6.5", "n": 1314, "fav_wins": 66.8, "fav_covers": 48.9, "dog_wins": 33.0, "push": 0.8}
    assert _base(pct) == {"n": 1314, "wins": 67, "covers": 49, "home": None}
    pickem = {"bucket": "0", "n": 212, "home_wins": 52.4, "fav_wins": None, "fav_covers": None, "dog_wins": None, "push": None}
    assert _base(pickem) == {"n": 212, "wins": None, "covers": None, "home": 52}
    assert _base(None) is None and _base({"n": 0}) is None


RECORD = pathlib.Path(__file__).parent / "fixtures" / "data" / "preview_record.json"


def test_the_record_is_cut_newest_week_first(block):
    assert block["record"] is None                          # the module's block is built without the record file
    rec = live_preview(json.loads(FIXTURE.read_text(encoding="utf-8")), slug,
                       json.loads(RECORD.read_text(encoding="utf-8")))["record"]
    assert (rec["through"], rec["n"], rec["ats"], rec["by_conf"]["strong"]) == (2, 8, "4-2-1", "1-0-1")
    assert (rec["closer"], rec["graded"]) == (4, 7)        # TB @ ATL had no moneyline, so no market Brier
    assert (rec["fav"], rec["fav_of"], rec["covered"]) == (6, 8, 1)
    assert rec["blind"] == {"n": 7, "ats": "4-3-0", "mae_blind": 9.1, "mae_market": 8.4}
    assert [w["week"] for w in rec["weeks"]] == [2, 1]
    w2 = rec["weeks"][0]
    assert (w2["ats"], w2["strong"], w2["closer"], w2["graded"], w2["fav"], w2["fav_of"]) == ("1-2-1", "0-0-1", 2, 3, 3, 4)
    # Since 2026-10-05 (Past games, storyboard 2A) every graded game carries all three calls and their hits.
    assert w2["games"][1] == {"key": "2026_02_SEA_LA", "away": "SEA", "home": "LA", "pick": "LA", "side": "LA", "conf": "strong",
                              "spread_home": -3.0, "result": {"home": 27, "away": 24}, "hit": "push", "su": "hit",
                              "total_line": 46.5, "total_call": "over", "total_conf": "solid", "total_hit": "hit"}
    assert (rec["su"], rec["total"], w2["su"], w2["total"]) == ("5-3", "5-1-0", "2-2", "3-0-0")
    assert contract.problems("LIVE_PREVIEW", {**block, "record": rec}) == []


def test_before_a_final_week_the_record_is_empty():
    empty = json.loads(RECORD.read_text(encoding="utf-8"))
    empty.update(through_week=None, weeks=[])
    empty["totals"]["blind"] = {"n": 0, "ats": "0-0-0", "ats_pass": 0, "margin_mae": {"blind": None, "market": None, "final": None}}
    rec = live_preview(json.loads(FIXTURE.read_text(encoding="utf-8")), slug, empty)["record"]
    assert rec["weeks"] == [] and rec["through"] is None and (rec["closer"], rec["graded"]) == (0, 0)
    assert rec["blind"] is None
    assert live_preview(json.loads(FIXTURE.read_text(encoding="utf-8")), slug)["record"] is None



# Component tests (2026-10-06): Preview mounted (`mount`), read through `PreviewPage` (tests/pages/preview.py).
# A phone is 360x800; the one test that needs another view (Slips and Back) is a journey on the full page.
PHONE = (360, 800)


@pytest.fixture
def preview(mount):
    """Preview mounted on the fixture build at a phone's size: (PreviewPage, page errors)."""
    page, errors = mount("preview", size=PHONE, touch=True)
    return PreviewPage(page), errors


@pytest.mark.render
def test_the_slate_lists_every_game_by_window(preview):
    pv, errors = preview
    assert pv.windows() == [["Thursday night", ["PIT @ CLE"]], ["Sunday morning", ["JAX @ LA"]], ["Sunday early", ["DET @ CAR"]],
                            ["Sunday late", ["SF @ NYJ"]], ["Monday night", ["ATL @ NO"]]]
    assert pv.first_window_time() == "5:15 PM"      # the reader's clock (Pacific here), no "ET"
    assert not pv.is_open() and not pv.dossier_visible()
    assert errors == []


@pytest.mark.render
def test_a_row_is_the_call_then_the_headline(preview):
    """Storyboard option C (2026-09-29, David: "super busy"): two lines, like a newspaper's index.
    Win %, the score and the total live in the game's box score, not on the slate. Option B (the
    same day, "too many things screaming for attention"): no flags, and lime only on the game on
    screen and a confident pick."""
    pv, errors = preview
    assert pv.legacy_slate_parts() == 0
    assert pv.lime_words() == ["Very confident", "Confident"]           # the phone has no game on screen
    assert pv.window_head_font().startswith("Newsreader")                # the day reads as a section head
    assert pv.row_head_font().startswith("Newsreader")
    assert "Claude's call arrives" in pv.row_text(4)
    assert errors == []


@pytest.mark.render
def test_the_slate_has_serif_type_in_the_site_ink_and_a_face_per_game(preview):
    """David, 2026-09-29: "very clinical, so much black and white", then the brown ground was "too
    brown", then the cream type left "a weird brown glow". The serif stays; its colour is the site's
    own ink: the day heads and the matchup --ink, the headlines --ink-2. Each row leads with the face
    the headline is about."""
    pv, errors = preview
    colours, ink = pv.serif_colours()
    assert colours == [ink[0], ink[1], ink[0]]                           # never the newsprint cream
    assert pv.ground() == "none"                                         # no painted ground of its own
    assert [pv.row_face_count(i) for i in range(5)] == [1, 1, 1, 1, 0]   # ATL @ NO: no take, no face
    pick = pv.face_players([
        {"head": "Dak outguns a Collins-less Texans team", "players": [{"n": "Nico Collins"}, {"n": "Dak Prescott"}]},
        {"head": "Love's arm carries GB", "players": [{"n": "Josh Jacobs"}, {"n": "Jordan Love"}]},
        {"head": "Defense rules the day", "players": [{"n": "Josh Jacobs"}, {"n": "Jordan Love"}]}])
    assert pick == ["Dak Prescott", "Jordan Love", "Josh Jacobs"]       # first name, last name, else his first call
    assert errors == []


@pytest.mark.render
def test_a_row_shows_only_a_confident_pick(preview):
    """David, 2026-09-29: drop the "JAX getting 2.5" from the slate; only Confident and Very
    confident speak there. A slight pick, no pick and no take draw nothing right of the matchup."""
    pv, errors = preview
    assert [pv.row_ats_count(i) for i in range(5)] == [0, 1, 1, 0, 0]    # no pick, strong, solid, slight, no take
    assert pv.ats_words() == ["Very confident", "Confident"]
    assert pv.side_word_count() == 0
    assert errors == []


@pytest.mark.render
def test_the_answer_is_one_row_per_bet_vegas_beside_claude(preview):
    """Storyboard 3A (2026-10-05; David: "saying the same thing many times", "Are you saying PIT is covering?"):
    Claude's score, then Moneyline, Spread and Total, Vegas's number in its own column beside Claude's call."""
    pv, errors = preview
    pv.show_game(2)                                                      # DET @ CAR
    assert pv.score() == "DET 30, CAR 19"
    assert pv.bet_heads() == ["", "VEGAS", "CLAUDE"]
    assert pv.bet_rows() == [["Moneyline", "DET 64%", "DET wins 74% chance"],
                             ["Spread", "DET by 3.5", "DET covers Confident wins by 4 or more"],
                             ["Total", "50.5", "Under Slight 50 points or fewer"]]
    pv.show_game(1)                                                      # JAX @ LA: Claude takes the underdog
    assert pv.bet_rows()[1][1:] == ["LA by 3", "JAX covers Very confident wins, or loses by 2 or less"]   # 3 is a push
    # Gone with 3A: the market's score, the bar, "getting / giving", where a line opened.
    ans = pv.answer_text()
    assert [gone for gone in ("market", "getting", "giving", "opened") if gone in ans] == []
    assert pv.answer_bar_count() == 0
    pv.show_game(4)                                                      # ATL @ NO: no take, Vegas only
    assert pv.score_count() == 0
    assert [r[2] for r in pv.bet_rows()] == ["–", "–", "–"]
    assert errors == []


@pytest.mark.render
def test_the_game_page_reads_like_a_newspaper(preview):
    """Storyboard option C (2026-09-29): headline and dek, the call, the box score, then the rest of
    the story. Section names are run-in words and plain bold names, never all-caps label rows."""
    pv, errors = preview
    pv.tap_game(2)                                                       # DET @ CAR
    # The answer first (2026-10-05, plan U3): pick, line, total and win chance above the headline.
    assert pv.parts() == ["pvn-ans", "pvn-head", "pvn-call", "pvn-box", "pvn-story"]
    assert pv.bet_ids() == ["ml", "spread", "total"]
    # "slip" since 2026-10-03: the take names Amon-Ra St. Brown, who has lines on the fixture's slate.
    # "ds" since 2026-10-06: Carolina is missing a lineman and a corner (tests/test_d_starters_view.py).
    assert pv.section_kinds() == ["matchup", "handoff", "inj", "ds", "wx", "rest"]
    assert pv.headline_font().startswith("Newsreader")
    # The story's paragraphs (2026-09-30), every one set alike: one voice, not a dek and smaller body copy.
    assert pv.dek_texts() == ["Rain keeps it on the ground, and Carolina allows the second-most RB points.",
                              "Gibbs gets the carries early and Detroit leans on him once it leads.",
                              "With Coker out, Young has one target he trusts, and the passing game stalls."]
    assert len(set(pv.dek_fonts())) == 1
    # Each player call's first mention is bold and opens his profile (2026-09-30); St. Brown is not named.
    assert pv.name_buttons() == ["Gibbs", "Young"]
    assert pv.first_name_weight() == "700"
    call = pv.call_text().replace("\n", " ")
    assert [want for want in ("The call.", "Carolina without Coker") if want not in call] == []
    ans = pv.answer_text().replace("\n", " ")
    assert [want for want in ("DET covers", "Confident", "Under", "Slight", "50.5", "DET by 3.5")
            if want not in ans] == []
    assert pv.risk_text().startswith("What could go wrong.")
    # Show, don't tell (2026-09-30): no research notes, no before-the-line process, no footnotes.
    dz = pv.dossier_text()
    assert [gone for gone in ("before seeing the line", "moved it to 11", "Research notes", "5.1 yards a carry",
                              "2011–2025", "Opinion, not a tested model", "WR is faded",
                              "1 gives up the fewest", "backtest") if gone in dz] == []
    assert pv.notes_and_footnotes() == 0
    assert pv.uppercase_labels() == 0
    assert pv.score_and_reason_lines() == (0, 0)
    pv.step(-1)
    pv.step(-1)                                                          # PIT @ CLE: no edge
    assert pv.bet_no_edge_count("spread") == 1 and pv.bet_no_edge_count("total") == 1
    assert pv.call_count() == 0                                          # no edge, no reason to print
    assert errors == []


@pytest.mark.render
def test_the_answer_is_above_the_fold_on_a_phone_and_the_story_starts_below_it(mount):
    """Plan U3 (2026-10-05): the line, total, win chance and Claude's pick were under five paragraphs. At
    390x844 the whole block ends above the fold and the headline starts under it."""
    page, errors = mount("preview", size=(390, 844), touch=True)
    pv = PreviewPage(page)
    pv.tap_game(2)                                                       # DET @ CAR: every cell
    box = pv.answer_box()
    assert box["ans"][1] <= box["vh"], box                               # the whole block is on the first screen
    assert box["head"] >= box["ans"][1] - 1 and box["dek"] > box["head"]
    assert pv.scroll_width() <= 390
    assert errors == [], errors


@pytest.mark.render
def test_past_games_opens_from_under_the_slate_and_back_closes_it(preview):
    """Storyboard 1A and 2A (2026-10-05, https://claude.ai/artifact/NTeV8W2N9mFnYgftfbuqPV): the record left the
    top of the slate (David: "randomly placed", wordy). It heads Past games, one row per bet, reached from a
    row under the games. The fixture's record runs through week 2, the page's own week, so week 1 is past."""
    pv, errors = preview
    assert pv.record.legacy_cards() == 0                                 # no record card on the slate
    assert pv.title() == "Game previews · Week 2"
    assert pv.fold_texts() == ["Past weeks · Claude's record ›"]
    fold_top, games_bottom = pv.fold_edges()
    assert fold_top > games_bottom - 1                                   # under the games, not above them
    # Scrolled down to the row: a phone's bottom tab bar (2026-10-05) covers the screen's last 64px, so a
    # fixed scroll could leave the row under it and the click would scroll the page again before it opens.
    pv.scroll_fold_into_view()
    y = pv.scroll_y()
    assert y > 0
    pv.open_record()
    assert not pv.slate_visible() and pv.record.visible()
    assert pv.hash() == "#preview"
    assert pv.record.season_title() == "CLAUDE THIS SEASON · THROUGH WEEK 2"
    assert pv.record.season_rows() == [["Moneyline", "5–3", "63%"], ["Spread", "4–2–1", "67%"], ["Total", "5–1", "83%"]]
    assert pv.record.season_conf() == "Spread by confidence: Very confident 1–0–1 · Confident 1–1 · Slight 2–1"
    record_text = pv.record.text()
    assert [gone for gone in ("closer than the market", "Fav picks", "Blind number") if gone in record_text] == []
    assert pv.record.week_label() == "Week 1"
    assert pv.record.game_count() == 4                                      # week 1's graded games, from the record
    pv.browser_back()
    pv.wait_for_record_closed()
    pv.wait_for_slate_at(y)
    assert pv.slate_visible() and pv.scroll_y() == y
    assert errors == []


@pytest.mark.render
def test_the_back_button_closes_past_games(preview):
    pv, errors = preview
    pv.open_record()
    assert pv.record.back_text() == "‹ Preview"
    pv.record.tap_back()
    assert pv.slate_visible() and pv.record.count() == 0
    assert pv.layers() == 0
    assert errors == []


@pytest.mark.render
def test_a_game_that_is_over_leaves_the_slate_for_past_games(preview):
    """1A: once a game is over (final, or 4 hours past kickoff) the slate drops it; This week's Final row
    holds it, and its page opens from there with the final's calls, back to Past games."""
    pv, errors = preview
    pv.end_games(0, 1)
    assert "PIT @ CLE" not in pv.matches() and "JAX @ LA" not in pv.matches()
    assert pv.fold_texts()[0] == "Final · 2 games this week ›"
    pv.open_record()                                                     # the first row: this week
    assert pv.record.week_label() == "Week 2"
    assert [t.split(" ")[0:3] for t in pv.record.game_matches()] == [["PIT", "@", "CLE"], ["JAX", "@", "LA"]]
    pv.record.tap_game(1)
    assert pv.is_open() and pv.match() == "JAX @ LA"
    assert pv.back_text() == "‹ Past games"
    assert pv.section_count("handoff") == 0                              # a finished game's lines are gone
    pv.tap_back()
    assert pv.record.visible() and pv.record.week_label() == "Week 2"
    assert errors == []


@pytest.mark.render
def test_every_game_over_says_so_on_the_slate(preview):
    pv, errors = preview
    pv.end_games(0, 1, 2, 3, 4)
    assert pv.window_count() == 0
    assert pv.all_over_text().startswith("Every game this week is over.")
    assert pv.fold_texts() == ["Final · 5 games this week ›", "Past weeks · Claude's record ›"]
    assert errors == []


@pytest.mark.render
def test_the_week_stepper_stays_in_range(preview):
    """David asked how 2A scales to 18 weeks: a stepper, one row wide at any count, from week 1 to this week."""
    pv, errors = preview
    pv.end_games(0)
    pv.open_record(2)
    assert pv.record.week_step_disabled(1)
    pv.record.step_week(-1)
    assert pv.record.week_label() == "Week 1" and pv.record.week_step_disabled(-1)
    assert pv.record.week_line() == "Moneyline 3–1 · Spread 3–0 · Total 2–1"
    assert errors == []


@pytest.mark.render
def test_an_earlier_weeks_game_opens_from_the_archive(preview):
    """An earlier week's previews come from preview_archive.json (design/preview_archive.py), fetched on first
    open. Here the fetched document is set by hand: one week-1 game, drawn by the same dossier."""
    pv, errors = preview
    pv.record.plant_archived_week_one()
    pv.open_record(1)
    assert pv.record.game_matches() == ["DET @ CAR"]
    pv.record.tap_archived_game()
    assert pv.is_open() and pv.match() == "DET @ CAR"
    assert pv.kickoff_text().startswith("Week 1 · ")
    assert pv.back_text() == "‹ Past games"
    assert pv.section_kinds() == []                                      # an archived game keeps only its take
    assert all(t == "" for t in pv.projections())                        # no projection was archived
    pv.tap_back()
    assert pv.record.visible() and not pv.record.archived_game_open()
    assert errors == []


@pytest.mark.render
def test_without_a_graded_week_there_is_no_season_block(preview):
    pv, errors = preview
    pv.record.drop_graded_weeks()
    assert pv.fold_texts() == []                                         # nothing over, nothing graded
    pv.record.drop_record()
    pv.end_games(0)
    pv.open_record()
    assert pv.record.season_count() == 0 and pv.record.game_count() == 1
    assert errors == []


@pytest.mark.render
def test_no_signed_spread_anywhere_in_the_preview(preview):
    """David: never a signed spread. A line is "PIT by 2.5", a call "CLE covers"."""
    pv, errors = preview
    seen = [pv.slate_text()]
    for i in range(5):
        pv.show_game(i)
        seen += pv.story_texts()
    pv.close_dossier()
    pv.open_record()
    seen.append(pv.record.text())
    signed = [m.group(0) for s in seen for m in re.finditer(r"(?<![\w.])[+\-−]\d+(\.\d)?", s)]
    assert signed == []
    assert " by " in " ".join(seen) and "covers" in " ".join(seen)
    assert errors == []


@pytest.mark.render
def test_a_tap_opens_the_dossier_and_back_returns_to_the_slate_where_it_was(preview):
    pv, errors = preview
    pv.scroll_to(120)
    y = pv.scroll_y()
    pv.tap_game(3)
    assert pv.is_open() and pv.match() == "SF @ NYJ"
    assert not pv.slate_visible()
    assert pv.hash() == "#preview"                               # the game is not in the URL
    lines = pv.answer_text()
    assert "NYJ by 1.5" in lines and "opened" not in lines              # storyboard 3A cut where a line opened
    assert "+3 zones east · kicks off at 1:25 PM body time" in pv.section_text("rest")
    pv.browser_back()
    pv.wait_for_dossier_closed()
    pv.wait_for_scroll(y)
    assert pv.scroll_y() == y
    assert pv.hash() == "#preview"
    assert errors == []


@pytest.mark.render
def test_the_all_games_button_closes_the_dossier(preview):
    pv, errors = preview
    pv.tap_game(0)
    pv.tap_back()
    assert not pv.is_open()
    pv.tap_game(1)                                              # and opening again still works
    assert pv.is_open() and pv.match() == "JAX @ LA"
    assert errors == []


@pytest.mark.render
def test_optional_rows_are_absent_without_data(preview):
    pv, errors = preview
    pv.tap_game(4)                                              # ATL @ NO: dome, no take, no rest
    assert pv.section_kinds() == ["inj", "ds", "wx"]            # no matchup or rest; a dome says Dome; New Orleans is short (2026-10-06)
    # The answer still gives Vegas on every bet: no take, so no score and no call.
    assert pv.bet_ids() == ["ml", "spread", "total"]
    assert pv.score_count() == 0
    assert pv.forecast_text() == "Dome" and "forecast" not in pv.section_text("wx").lower()
    assert pv.call_count() == 0 and pv.story_count() == 0
    assert "Claude's call on this game arrives" in pv.header_text()
    assert pv.players_count() == 0 and pv.risk_count() == 0
    pv.step(-1)
    pv.step(-1)                                                 # DET @ CAR: the one with defense ranks
    assert pv.match() == "DET @ CAR" and pv.matchup_count() == 1
    assert pv.dim_matchup_row().startswith("WR")
    assert "Rain" in pv.effects_text()                          # rain 56% is past the backtest's threshold
    assert "J. Coker" in pv.injury_text(1)
    assert errors == []


@pytest.mark.render
def test_claudes_confidence_words_say_untested(preview):
    """Claude's Slight / Confident / Very confident / No pick are its own word, scored as a record and not backtested:
    the tooltip says so (2026-10-06)."""
    pv, errors = preview
    pv.tap_game(0)
    titles = pv.conf_titles()
    assert titles and all(t.startswith("Untested") for t in titles), titles
    assert errors == []


@pytest.mark.render
def test_neutral_site_and_short_week(preview):
    pv, errors = preview
    pv.tap_game(1)
    assert "Neutral site: Wembley Stadium" in pv.section_text("rest")
    assert "Off a bye" in pv.section_text("rest")
    assert "OFF A BYE" not in pv.section_text("rest")
    bye = pv.rest_notes()
    assert [n["text"] for n in bye] == ["Off a bye"] and "pv-tag" not in bye[0]["cls"]
    pv.step(-1)
    shorts = pv.rest_notes()
    assert [n["text"] for n in shorts] == ["Short week"] * 2
    # 12.62: rest is priced into the line (Thursday total -0.06, off a bye -0.37 ATS), so the note is a fact in
    # plain text, never an amber tag (2026-10-06).
    tagged = [n for n in bye + shorts if "pv-tag" in n["cls"] or n["bg"] != "rgba(0, 0, 0, 0)"]
    assert tagged == []
    assert errors == []


@pytest.mark.render
def test_a_swipe_in_the_dossier_walks_the_games_and_stops_at_the_ends(preview):
    pv, errors = preview
    pv.tap_game(0)
    pv.swipe(-120)
    assert pv.match() == "JAX @ LA" and pv.is_open()
    pv.swipe(120)
    assert pv.match() == "PIT @ CLE"
    pv.swipe(120)                                     # past the first game: nothing
    assert pv.match() == "PIT @ CLE"
    pv.swipe(-20)                                     # a nudge is not a swipe
    assert pv.match() == "PIT @ CLE"
    assert errors == []


@pytest.mark.render
def test_a_player_row_opens_his_profile(preview):
    pv, errors = preview
    pv.tap_game(0)
    pv.spy_on_profile()
    pv.tap_player(0)
    assert pv.opened_profiles() == ["dk-metcalf"]
    assert errors == []


@pytest.mark.render
def test_a_bold_name_in_the_story_opens_his_profile(preview):
    pv, errors = preview
    pv.tap_game(2)                                                       # DET @ CAR
    pv.spy_on_profile()
    pv.tap_name("Young")
    assert pv.opened_profiles() == ["bryce-young"]
    assert errors == []


@pytest.fixture(scope="module")
def story(node_js):
    return node_js("surface/preview/dossier.js")


def test_a_shared_surname_is_never_bolded_alone(story):
    """IND @ WAS has two Warrens: "Warren" alone could be either, so only a full name marks one."""
    got = story("pvNamesHTML", ["Warren runs. Tyler Warren catches. Then Warren again."],
                [{"n": "Jaylen Warren"}, {"n": "Tyler Warren"}])
    assert got == ['Warren runs. <button type="button" class="pv-nm" data-pvp="1">Tyler Warren</button> catches. Then Warren again.']


@pytest.mark.render
def test_a_desktop_shows_the_rail_beside_the_dossier(mount):
    page, errors = mount("preview", size=(1280, 900), touch=True)
    pv = PreviewPage(page)
    assert pv.slate_visible() and pv.dossier_visible() and pv.match() == "PIT @ CLE"
    pv.tap_game(2)
    assert pv.match() == "DET @ CAR" and pv.current_row_match() == "DET @ CAR"
    assert pv.layers() == 0 and not pv.is_open()                  # a click on a desktop pushes no layer
    assert pv.edges("slate")[0] < pv.edges("dossier")[0]
    # The box score is a column right of the call, the two sharing a top edge (storyboard option C).
    call, box = pv.edges("call"), pv.edges("box")
    assert box[0] > call[2] and abs(box[1] - call[1]) < 2
    assert errors == [], errors


@pytest.mark.render
def test_a_desktop_opens_past_games_in_the_dossiers_place_and_a_rail_game_closes_it(mount):
    page, errors = mount("preview", size=(1280, 900), touch=True)
    pv = PreviewPage(page)
    # Past games opens in the dossier's place, the rail stays; a game in the rail closes it.
    pv.open_record()
    assert pv.slate_visible() and pv.record.visible() and pv.dossier_count() == 0
    assert pv.current_fold_count() == 1 and pv.current_row_count() == 0
    pv.tap_game(1)
    assert pv.match() == "JAX @ LA" and pv.record.count() == 0 and pv.layers() == 0
    assert errors == [], errors


@pytest.mark.render
def test_nothing_scrolls_sideways_at_360(preview):
    pv, errors = preview
    widths = []
    for i in range(5):
        pv.show_game(i)
        widths.append(pv.scroll_width())
    assert [i for i, w in enumerate(widths) if w > 360] == [], widths
    pv.record.show(2)
    assert pv.record.count() == 1 and pv.record.game_count() > 0
    assert pv.scroll_width() <= 360, "Past games"
    assert errors == []


@pytest.mark.render
@pytest.mark.journey
def test_the_dossier_hands_its_players_to_the_slip(browser, page_file):
    """From this game to your slip (2026-10-03): each player the take names with his lines in the
    player sheet's row; a side tapped lands in the same tray as Slips', and he is marked on slip;
    "All N players in Slips" opens Slips on the game's kickoff with its card. The fixture's preview games
    and its props slate are different games, so game 3 becomes the props slate's SEA @ SF and names Kittle.
    A journey: it leaves for Slips and Back returns, so it needs the whole page."""
    ctx, page, errors = open_at(browser, page_file, PHONE, "#preview")
    try:
        pv = PreviewPage(page)
        slips = pv.handoff.slips()
        assert pv.section_count("handoff") == 0, "no game of the props slate is open"
        pv.handoff.plant_game_as_sea_sf()
        pv.handoff.open_game_for_real(3)   # the real open: it pushes the dossier's history entry
        assert pv.handoff.title() == "From this game to your slip"
        assert pv.handoff.players() == 1 and pv.handoff.lines() == 1, "one line each, his position's own (REC)"
        assert pv.handoff.market().startswith("Rec yds"), "the primary line is his yards market"
        assert pv.handoff.lines_label().startswith("2 lines"), "TD and yards; LONG is no line"
        assert pv.handoff.tray_drawn() == 0, "no tray on Preview until a pick is in it"
        rec = pv.handoff.props_index("george-kittle", "REC")
        pv.handoff.pick(rec, "higher")
        assert slips.slip() == [[rec, "higher"]]
        assert slips.tray_count() == "1"
        assert pv.handoff.marked_count() == 1
        assert pv.scroll_width() <= 360
        n = pv.handoff.players_with_lines(3)
        assert pv.handoff.slip_all_text().startswith(f"All {n} players in Slips")
        pv.handoff.tap_slip_all()
        assert slips.surface() == "parlay" and slips.kickoff()["chosen"] == "evening-sun"
        assert slips.game_titles().count("SEA @ SF") == 1
        assert slips.row_on_slip("george-kittle") == 1
        # Back from Slips lands on the dossier it left, not the slate; Back again closes the dossier.
        pv.browser_back()
        pv.wait_for_view("preview")
        assert pv.handoff.dossier_open_state() is True and pv.section_count("handoff") == 1
        pv.browser_back()
        pv.handoff.wait_for_dossier_state_closed()
        assert errors == []
    finally:
        ctx.close()
