"""The Digest's day cards, set B (2026-10-06, storyboard "Digest by Day"; STYLE.md "Answer first, research one tap
away"): Claude vs Vegas and Start in this game (Thursday, Monday), SMASH, Bold calls, Top calls and Weather
(Saturday, with Weather also on Sunday).

Component tests on `mount("digest")` (`DigestCardsPage`, tests/pages/digest_cards_b.py), one card per behaviour: it
draws from the fixture, puts its answer on the right, opens its research on a tap (one open at a time across the
page), draws nothing without its data, and says what is untested where it makes a call (tests/test_flag_marks.py
holds the copy; each pick word and confidence word carries it as a tooltip here).

The fixture's clock is Saturday 2026-09-12 (week 2). Thursday is 2026-09-17 noon Pacific, when the preview game
PIT @ CLE (5:15 PM PT) is still to play; Monday is 2026-09-14. Expected values come from the fixture files
(tests/fixtures/data) and from content.json, never from the card's own code.
"""
import json
import pathlib

import pytest

from component import mount  # noqa: E402,F401  (the fixture)
from pages.digest_cards_b import DigestCardsPage
from wording import words

pytestmark = pytest.mark.render

ROOT = pathlib.Path(__file__).resolve().parent
COPY = json.loads((ROOT.parent / "design" / "src" / "content.json").read_text(encoding="utf-8"))
DEFENSE = json.loads((ROOT / "fixtures" / "data" / "defense_form.json").read_text(encoding="utf-8"))["teams"]
PHONE = (360, 800)
THU, MON = "2026-09-17T19:00:00Z", "2026-09-14T19:00:00Z"
TNF_KICK, MNF_KICK = "2026-09-18T00:15:00Z", "2026-09-15T00:15:00Z"
RECORD = COPY["digest.foot.mu"].format(wk=5, smash="7-3", start="2-2", sit="4-1") + " " + COPY["digest.foot.muMark"]


def cards(mount, size=PHONE):
    page, errors = mount("digest", size=size)
    return DigestCardsPage(page), errors


def nth(n):
    """1 -> 1st, 22 -> 22nd, 11 -> 11th: the ordinal the page prints."""
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


# ------------------------------------------------------------------ Claude vs Vegas (Thursday)

@pytest.mark.req("Preview", ac="a game's answer is one row per bet, Vegas beside Claude")
def test_vegas_card_is_one_row_per_bet_with_vegas_beside_claude(mount):
    dg, errors = cards(mount)
    dg.at(THU)
    assert dg.title("vegas") == words("digest.card.vegas.title")
    assert dg.table_head() == ["Bet", "Vegas", "Claude"]
    assert [(b["bet"], b["vegas"], b["claude"]) for b in dg.bets()] == [
        ("Winner", "PIT 56%", "PIT wins 58% chance"), ("Spread", "PIT by 2.5", "No pick"), ("Total", "38.5", "No pick")]
    assert dg.more("vegas")["leaf"] == "preview"
    assert dg.fits()
    assert errors == []


@pytest.mark.req("Preview", ac="a game's answer is one row per bet, Vegas beside Claude")
def test_vegas_card_names_the_game_it_is_about(mount):
    dg, errors = cards(mount)
    dg.at(THU)
    assert dg.game_line().startswith("PIT @ CLE")
    assert errors == []


@pytest.mark.req("Preview", ac="Claude's own words carry what was tested")
def test_vegas_claude_cells_carry_the_untested_marks(mount):
    dg, errors = cards(mount)
    dg.at(THU)
    bets = dg.bets()
    assert bets[0]["claude_title"] == COPY["preview.call.mark"]
    no_call = [[COPY["preview.conf.none"], COPY["preview.conf.mark"]]]
    assert bets[1:], "the spread and total bets are drawn"
    # no spread or total call: the "No pick" chip says it too
    assert [bet for bet in bets[1:] if bet["chips"] != no_call] == []
    assert errors == []


@pytest.mark.req("Preview", ac="a call carries its confidence word")
def test_vegas_spread_and_total_calls_show_the_side_and_the_word(mount):
    dg, errors = cards(mount)
    dg.page.evaluate("""() => { const k = LIVE_PREVIEW.games[0].take;
      k.ats = {side: 'PIT', conf: 'solid', edge: 'x'}; k.total = {call: 'under', conf: 'strong'}; }""")
    dg.at(THU)
    spread, total = dg.bets()[1:]
    assert spread["claude"].startswith("PIT covers") and spread["chips"] == [[COPY["preview.conf.solid"], COPY["preview.conf.mark"]]]
    assert total["claude"].startswith("Under") and total["chips"] == [[COPY["preview.conf.strong"], COPY["preview.conf.mark"]]]
    assert errors == []


@pytest.mark.req("Digest", ac="a card with no data draws nothing")
def test_vegas_card_is_absent_without_a_game_today(mount):
    dg, errors = cards(mount)
    dg.plant_no_preview_games()
    dg.at(THU)
    assert not dg.has_card("vegas")
    assert errors == []


@pytest.mark.req("Digest", ac="a card with no data draws nothing")
def test_vegas_card_is_absent_when_the_game_has_neither_a_line_nor_a_take(mount):
    dg, errors = cards(mount)
    dg.plant_bare_game()
    dg.at(THU)
    assert not dg.has_card("vegas")
    assert errors == []


# ------------------------------------------------------------------ Start in this game (Thursday), Start tonight (Monday)

def test_game_card_leads_with_smash_then_bold_starts_and_answers_with_the_pill_and_rank(mount):
    dg, errors = cards(mount)
    dg.plant_game(THU, "CIN", "PIT", TNF_KICK)
    assert dg.title("game") == words("digest.card.game.title")
    assert [(r["name"], r["pill"], r["answer"], r["meta"]) for r in dg.rows("game")] == [
        ("J. Burrow", "SMASH", "SMASH QB3", "CIN @ PIT"), ("C. Brown", "SMASH", "SMASH RB5", "CIN @ PIT"),
        ("J. Chase", "SMASH", "SMASH WR5", "CIN @ PIT"), ("T. Higgins", "START", "START WR16", "CIN @ PIT")]
    assert dg.more("game") == {"leaf": "matchups", "text": "Start/Sit"}
    assert errors == []


def test_game_card_is_start_tonight_on_monday(mount):
    dg, errors = cards(mount)
    dg.plant_game(MON, "CIN", "PIT", MNF_KICK)
    assert dg.title("game") == words("digest.card.game.tonight")
    assert dg.rows("game")[0]["name"] == "J. Burrow"
    assert errors == []


def test_game_card_foot_is_the_start_sit_record_with_its_marks(mount):
    dg, errors = cards(mount)
    dg.plant_game(THU, "CIN", "PIT", TNF_KICK)
    assert dg.foot("game") == RECORD
    assert errors == []


@pytest.mark.req("Digest", ac="a pick word carries what its model has been through")
def test_game_card_pills_carry_their_models_marks(mount):
    dg, errors = cards(mount)
    dg.plant_game(THU, "CIN", "PIT", TNF_KICK)
    marks = {r["pill"]: r["mark"] for r in dg.rows("game")}
    assert marks == {"SMASH": COPY["matchups.takes.markSmash"], "START": None}, "a bold START is a take: no test-status label"
    assert errors == []


def test_game_card_research_is_our_rank_the_season_average_the_line_and_the_td_price(mount):
    dg, errors = cards(mount)
    dg.plant_game(THU, "CIN", "PIT", TNF_KICK)
    burrow, higgins = dg.rows("game")[0], dg.rows("game")[3]
    assert burrow["research"] == [["Our rank", "QB3"], [words("digest.card.game.avg"), "QB5"], ["Line", "262.5 pass yds"], ["TD price", "+120"]]
    assert higgins["research"] == [["Our rank", "WR16"], [words("digest.card.game.avg"), "WR41"],
                                   ["Why", "PIT D vs WRs: 3rd softest"], ["Why", "Team total 27.5, 3rd of 32"]]
    assert errors == []


@pytest.mark.req("Digest", ac="a tap opens a row's research in place, one open at a time")
def test_game_card_row_opens_on_tap_and_one_open_at_a_time(mount):
    dg, errors = cards(mount)
    dg.plant_game(THU, "CIN", "PIT", TNF_KICK)
    assert dg.open_rows() == []
    dg.tap("game", 0)
    assert dg.open_rows() == ["game:J. Burrow"]
    dg.tap("game", 3)
    assert dg.open_rows() == ["game:T. Higgins"]
    dg.tap("game", 3)
    assert dg.open_rows() == []
    assert errors == []


def test_game_card_shows_only_players_of_the_game_still_to_kick_off(mount):
    dg, errors = cards(mount)
    dg.plant_game(THU, "HOU", "TEN", TNF_KICK)
    assert [r["name"] for r in dg.rows("game")] == ["C. Stroud"]      # the one bold START in HOU @ TEN, no SMASH there
    dg.plant_game("2026-09-18T01:00:00Z", "HOU", "TEN", TNF_KICK)      # kickoff has passed: the call is moot
    assert not dg.has_card("game")
    assert errors == []


@pytest.mark.req("Digest", ac="a card with no data draws nothing")
def test_game_card_is_absent_when_no_call_is_in_the_game(mount):
    dg, errors = cards(mount)
    dg.plant_game(THU, "MIA", "NYG", TNF_KICK)
    assert not dg.has_card("game")
    assert errors == []


@pytest.mark.req("Digest", ac="a card with no data draws nothing")
@pytest.mark.parametrize("name", ["Vegas", "Game", "Smash", "Bold"])
def test_a_card_with_every_block_missing_draws_nothing(mount, name):
    dg, errors = cards(mount)
    assert dg.card_html_without_data(name) == ""
    assert errors == []


# ------------------------------------------------------------------ SMASH (Saturday)

def test_smash_card_is_the_top_play_at_each_position_with_his_points_on_the_right(mount):
    dg, errors = cards(mount)
    assert dg.title("smash") == "SMASH"
    assert [(r["name"], r["meta"], r["answer"], r["pill"]) for r in dg.rows("smash")] == [
        ("J. Allen", "#1 QB · BUF vs MIA", "24.1 pts", None), ("J. Gibbs", "#1 RB · DET vs CHI", "19.8 pts", None),
        ("P. Nacua", "#2 WR · LA @ PHI", "16.6 pts", None), ("T. McBride", "#1 TE · ARI vs SEA", "13.4 pts", None)]
    assert errors == []


@pytest.mark.req("Digest", ac="a pick word carries what its model has been through")
def test_smash_title_carries_the_smash_mark(mount):
    dg, errors = cards(mount)
    assert dg.title_mark("smash") == COPY["matchups.takes.markSmash"]
    assert errors == []


def test_smash_foot_counts_the_rest_links_to_matchups_and_carries_the_record(mount):
    dg, errors = cards(mount)
    assert dg.foot("smash") == "+6 more " + RECORD
    assert dg.foot_more("smash") == {"leaf": "matchups", "text": "+6 more"}
    dg.tap_foot_more("smash")
    assert dg.view_leaf() == "#matchups"
    assert errors == []


def test_smash_research_is_what_the_opponent_allows_the_line_and_the_td_price(mount):
    dg, errors = cards(mount)
    te = DEFENSE["SEA"]["current"]["pos"]["TE"]
    of = max(v["current"]["pos"]["TE"]["rank"] for v in DEFENSE.values())
    mcbride, allen = dg.rows("smash")[3], dg.rows("smash")[0]
    assert mcbride["research"] == [
        ["Our rank", "TE1"], ["SEA allows", f"{te['pts_pg']} a game, {nth(of - te['rank'] + 1)} most of {of} teams"],
        ["Line", "66.5 rec yds"], ["TD price", "+150"]]
    assert allen["research"] == [["Our rank", "QB1"], ["Line", "251.5 pass yds"], ["TD price", "-105"]]    # MIA has no defense row
    assert errors == []


@pytest.mark.req("Digest", ac="a tap opens a row's research in place, one open at a time")
def test_a_row_in_another_card_closes_the_open_one(mount):
    dg, errors = cards(mount)
    dg.tap("smash", 0)
    assert dg.open_rows() == ["smash:J. Allen"]
    dg.tap("bold", 0)
    assert dg.open_rows() == ["bold:R. Stevenson"]
    assert errors == []


# ------------------------------------------------------------------ Bold calls (Saturday)

@pytest.mark.req("Digest", ac="a pick word carries what its model has been through")
def test_bold_card_is_the_two_widest_starts_then_the_two_widest_sits(mount):
    dg, errors = cards(mount)
    assert dg.title("bold") == words("digest.card.bold.title")
    assert [(r["name"], r["pill"], r["mark"], r["meta"]) for r in dg.rows("bold")] == [
        ("R. Stevenson", "START", None, "NE · RB · Our rank 15 · his season 36"),
        ("T. Higgins", "START", None, "CIN · WR · Our rank 16 · his season 41"),
        ("D. Moore", "SIT", None, "CHI · WR · Our rank 33 · his season 12"),
        ("E. Engram", "SIT", None, "DEN · TE · Our rank 20 · his season 8")]
    assert errors == []


def test_bold_research_is_the_reasons_the_call_carries(mount):
    dg, errors = cards(mount)
    stevenson, higgins, moore = dg.rows("bold")[0], dg.rows("bold")[1], dg.rows("bold")[2]
    assert stevenson["research"] == [["Our rank", "RB15"], [words("digest.card.bold.avg"), "RB36"], ["Why", "Work up 3.1 a game over his last 2"]]
    assert [x for x in higgins["research"] if x[0] == "Why"] == [["Why", "PIT D vs WRs: 3rd softest"], ["Why", "Team total 27.5, 3rd of 32"]]
    assert moore["research"][2:] == [["Why", "Team total 17.0, 28th of 32"]]
    assert errors == []


@pytest.mark.req("Digest", ac="the Start/Sit record shows once a day, on the first card of calls")
def test_bold_card_answer_is_on_the_right_and_the_record_is_not_repeated_from_smash(mount):
    dg, errors = cards(mount)
    assert [r["answer"] for r in dg.rows("bold")] == ["START", "START", "SIT", "SIT"]
    assert dg.foot("smash").endswith(RECORD), "SMASH is first on Saturday and carries the record"
    assert dg.foot("bold") is None, "Bold calls does not say it again"
    dg.page.evaluate("() => { LIVE_SS3.smash = []; DG_CUT = null; render(); }")
    assert not dg.has_card("smash") and dg.foot("bold") == RECORD, "with no SMASH card, Bold calls carries it"
    assert dg.more("bold")["leaf"] == "matchups"
    assert errors == []


# ------------------------------------------------------------------ Top calls (Saturday)

def test_calls_card_is_the_three_strongest_lines_with_the_chance_and_its_word(mount):
    dg, errors = cards(mount)
    assert dg.title("calls") == words("digest.card.calls.title")
    assert [(r["name"], r["meta"], r["answer"], r["delta"]) for r in dg.rows("calls")] == [
        ("C. Brown", "CIN · over 65.5 rush yds", f"72% {words('slips.tier.very')}", "flat"),
        ("J. Burrow", "CIN · under 245.5 pass yds", f"64% {words('slips.tier.confident')}", "flat"),
        ("B. Purdy", "SF · under 220.5 pass yds", "59% Slight", "flat")]
    assert dg.more("calls") == {"leaf": "parlay", "text": "Slips"}
    assert errors == []


@pytest.mark.req("Parlay and DFS", ac="the tiers carry their failed test")
def test_calls_foot_is_the_top_tiers_record_and_the_slips_mark(mount):
    dg, errors = cards(mount)
    assert dg.foot("calls") == "Very confident, through week 4: 241–182, 57%. " + COPY["slips.tier.mark"]
    assert errors == []


def test_calls_row_research_is_the_game_the_kickoff_and_his_average_under_the_mark(mount):
    dg, errors = cards(mount)
    dg.tap("calls", 1)
    assert dg.open_rows() == ["calls:J. Burrow"]
    burrow = dg.rows("calls")[1]
    assert burrow["research"] == [["Game", "CIN @ NYJ"], ["Kickoff", "Sun 10:00 AM"], [words("digest.card.calls.avg"), "230 pass yds, last 12 games"]]
    assert burrow["foot"] == COPY["slips.tier.mark"]
    assert errors == []


@pytest.mark.req("Digest", ac="a card with no data draws nothing")
def test_calls_card_is_absent_without_a_line_to_call(mount):
    dg, errors = cards(mount)
    dg.plant_no_props()
    assert not dg.has_card("calls")
    assert errors == []


# ------------------------------------------------------------------ Weather (Saturday, Sunday)

def test_weather_card_is_the_game_whose_forecast_moves_scoring_with_the_effect_on_the_right(mount):
    dg, errors = cards(mount)
    assert dg.title("weather") == "Weather"
    rows = dg.rows("weather")
    assert [(r["name"], r["tile"], r["meta"], r["answer"], r["delta"]) for r in rows] == [
        ("DET @ SEA", "SEA", "15 to 22 mph wind · 70% chance of rain", "−1.5 pts per QB", "down")]
    assert dg.more("weather") == {"leaf": "weather", "text": "Weather"}
    assert errors == []


def test_weather_conditions_are_not_cut_short_at_360(mount):
    dg, errors = cards(mount, size=(360, 800))
    assert dg.meta_cut("weather") == [False]
    assert dg.fits()
    assert errors == []


def test_weather_research_is_the_effect_on_each_position(mount):
    dg, errors = cards(mount)
    research = dg.rows("weather")[0]["research"]
    assert research[:4] == [["QB", "−1.5 pts"], ["WR", "−1.0 pts"], ["TE", "−0.5 pts"], ["K", "−1.5 pts"]]
    assert research[4][0] == "Kickoff"
    dg.tap("weather", 0)
    assert dg.open_rows() == ["weather:DET @ SEA"]
    assert errors == []


def test_weather_cold_condition_carries_its_failed_test(mount):
    dg, errors = cards(mount)
    dg.page.evaluate("() => { const f = LIVE_WEATHER.teams.SEA; f.wind = '5 mph'; f.precip_pct = 10; f.temp_f = 20; render(); }")
    row = dg.rows("weather")[0]
    assert row["meta"] == "20°F" and row["answer"] == "−1.0 pts per K"
    assert dg.page.get_by_test_id("digest-card").locator("[title]").evaluate_all("els => els.map(e => e.getAttribute('title'))") \
        .count(COPY["weather.cond.coldMark"]) == 1
    assert errors == []


@pytest.mark.req("Digest", ac="a card with no data draws nothing")
def test_weather_card_is_absent_when_no_forecast_moves_scoring(mount):
    dg, errors = cards(mount)
    dg.plant_calm_week()
    assert not dg.has_card("weather")
    assert errors == []
