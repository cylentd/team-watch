"""This week > Digest by day, cards of unit T3a (2026-10-06; STYLE.md "Answer first, research one tap away"):
Top adds and Out and who gains (Tuesday), Usage movers and Defenses giving up the most (Wednesday), Game status
and Injury watch (Friday, Thursday).

Component tests on `mount("digest")` (`DigestCardsPage`), each card drawn from tests/fixtures by the Digest at a
clock inside its day. A row's answer is at the right of its name; its research opens in place, one at a time; a
card with nothing to say draws nothing; a signal with no tested model carries its mark (test_flag_marks.py).
"""
import json
import pathlib
import re

import pytest

from component import mount  # noqa: E402,F401  (the fixture)
from pages.digest_cards import DigestCardsPage
from wording import words

pytestmark = pytest.mark.render

COPY = json.loads((pathlib.Path(__file__).resolve().parent.parent / "design" / "src" / "content.json").read_text(encoding="utf-8"))
SAYS = re.compile(r"Untested|Failed test \(12\.\d+(?:, 12\.\d+)*\)[:.] \S")


def day(mount, key):
    page, errors = mount("digest", size=(360, 800))
    dg = DigestCardsPage(page)
    dg.on(key)
    return dg, errors


@pytest.mark.req("Digest", ac="Tuesday's Top adds: five rows, the number behind each add at the right, Waivers one tap away")
def test_top_adds_are_five_rows_with_the_number_that_earned_each(mount):
    dg, errors = day(mount, "tue")
    assert dg.card_ids() == ["adds", "gains", "usage"]
    assert dg.card_head("adds") == {"title": words("digest.card.adds.title"), "more": "waivers"}
    rows = dg.card_rows("adds")
    assert [(r["name"], r["answer"], r["dir"]) for r in rows] == [
        ("D. Boston", "53% +27 rostered", "up"), ("B. Young", "58% +25 rostered", "up"),
        ("D. Schultz", "43% +23 rostered", "up"), ("T. Shough", "67% +17 rostered", "up"),
        ("J. Coleman", "37% +15 rostered", "up")]
    assert all(r["right"] and r["opens"] for r in rows), "the answer sits right of the name; every add has research"
    assert rows[0]["meta"] == "CLE"
    assert dg.fits() and errors == []


@pytest.mark.req("Digest", ac="a Sleeper add shows its count; an add whose role shrank is red with the snaps; research opens one at a time")
def test_an_adds_answer_is_sleepers_count_or_the_role_and_red_when_it_shrank(mount):
    dg, errors = day(mount, "tue")
    dg.plant_sleeper_adds()
    first = dg.card_rows("adds")[0]
    assert (first["answer"], first["dir"]) == ("4.0M adds", "flat")
    dg.open_row("adds", 0)
    assert "4.0M on Sleeper" in dg.research("adds", 0)
    dg.plant_a_shrinking_add()
    row = dg.card_rows("adds")[0]
    assert (row["answer"], row["dir"]) == ("41% snaps −12 pts", "down"), "a change in share is points, not snaps"
    assert dg.open_research("adds") == [True, False, False, False, False], "the open row stays open across a repaint"
    assert "60% · 53% · 41%" in dg.research("adds", 0) and "Untested" in dg.research("adds", 0)
    dg.open_row("adds", 1)
    assert dg.open_research("adds") == [False, True, False, False, False], "one open at a time"
    assert errors == []


@pytest.mark.req("Digest", ac="Out and who gains: the next man's face and snaps, the starter out and why, facts with no verdict word")
def test_gains_names_the_man_behind_the_starter_who_is_out(mount):
    dg, errors = day(mount, "tue")
    assert dg.card_head("gains") == {"title": words("digest.card.gains.title"), "more": None}
    row = dg.card_rows("gains")[0]
    assert (row["name"], row["meta"], row["answer"], row["right"]) == (
        "D. Robinson", "LA · P. Nacua doubtful · Hip", "61% snaps", True)
    dg.open_row("gains", 0)
    text = dg.research("gains", 0)
    assert words("digest.card.gains.targets") in text and "| 6" in text and "WR2" in text and "14%" in text
    dg.plant_gains_without_a_backup()
    row = dg.card_rows("gains")[0]
    assert (row["name"], row["meta"], row["pill"]) == ("P. Nacua", "LA · No clear backup", "D")
    assert dg.fits() and errors == []


@pytest.mark.req("Digest", ac="Monday's gains card says it holds tonight's game only: gains drops the teams whose game started")
def test_mondays_gains_card_is_about_tonight(mount):
    dg, errors = day(mount, "tue")
    assert dg.card_head("gains")["title"] == words("digest.card.gains.title")
    dg.at("2026-09-14T19:00:00Z")                      # a Monday inside the fixture packet's week
    assert dg.card_head("gains")["title"] == words("digest.card.gains.titleMon")
    assert errors == []


@pytest.mark.req("Digest", ac="Wednesday's Usage movers: Claude's line, a sparkline, the share now with its change; the card says it is untested")
def test_usage_movers_show_the_share_the_line_and_the_untested_mark(mount):
    dg, errors = day(mount, "wed")
    # Top calls is in Wednesday's plan but the fixture's lines all kicked off in September, so it draws nothing here.
    assert dg.card_ids() == ["usage", "gains", "defenses", "adds"]
    assert dg.card_head("usage") == {"title": words("digest.card.usage.title"), "more": "usage"}
    rows = dg.card_rows("usage")
    assert [(r["name"], r["answer"], r["dir"], r["spark"], r["right"]) for r in rows] == [
        ("B. Robinson", "78% snaps +23 pts", "up", True, True), ("H. Fannin", "28% targets +17 pts", "up", True, True)]
    assert rows[0]["meta"] == "Bijan Robinson played 78.0% of Atlanta's snaps in week 4, up from 55.0% in week 3."
    foot = dg.card_foot("usage")
    assert "weeks 2–4" in foot and SAYS.search(foot), foot
    dg.open_row("usage", 1)
    text = dg.research("usage", 1)
    assert words("digest.card.usage.tgtShare") in text and "11% · 12% · 28%" in text and "David Njoku" in text and "24% → 12%" in text
    assert dg.fits() and errors == []


@pytest.mark.req("Digest", ac="Defenses giving up the most: one row per position, points a game and 'most of N', the schedule's own mark")
def test_defenses_name_the_one_allowing_the_most_to_each_position(mount):
    dg, errors = day(mount, "wed")
    assert dg.card_head("defenses") == {"title": words("digest.card.defenses.title"), "more": "schedule"}
    assert dg.title_fits("defenses"), "the title is one line at 360px"
    rows = dg.card_rows("defenses")
    assert [(r["tile"], r["name"], r["answer"]) for r in rows] == [
        ("NYJ", "NY Jets", "21.4 most of 28"), ("NYJ", "NY Jets", "24.0 most of 26"), ("NYJ", "NY Jets", "31.2 most of 27"),
        ("SEA", "Seattle", "11.5 most of 22"), ("SEA", "Seattle", "9.3 most of 32")]
    assert [r["meta"].split(" · ")[0] for r in rows] == ["vs QBs", "vs RBs", "vs WRs", "vs TEs", "vs Ks"]
    assert all(r["right"] and r["opens"] for r in rows[:4]), "a skill position's row opens its research"
    assert not rows[4]["opens"], "the kicker row has no per-position numbers to open"
    assert dg.card_foot("defenses").endswith("Failed test (12.97): did not predict points.")
    dg.open_row("defenses", 0)
    text = dg.research("defenses", 0)
    assert "To WRs" in text and "31.2 a game" in text and "To TEs" in text and "most" in text
    assert dg.fits() and errors == []


@pytest.mark.req("Digest", ac="Friday's Game status: every hurt player, the status at the right, Wed/Thu/Fri practice marks between")
def test_game_status_shows_the_status_and_three_practice_marks(mount):
    dg, errors = day(mount, "fri")
    assert dg.card_head("status") == {"title": words("digest.card.status.title"), "more": "news"}
    rows = dg.card_rows("status")
    assert len(rows) == 12
    first, out, ir = rows[0], rows[1], rows[4]
    assert (first["name"], first["pill"], first["marks"], first["right"]) == ("P. Nacua", "D", ["DNP", "LTD", ""], True)
    assert (out["name"], out["pill"], out["marks"]) == ("N. Collins", "OUT", ["", "", ""])
    assert ir["pill"] == "IR" and rows[2]["pill"] == "Q"
    assert first["meta"] == "LA · Hip → D. Robinson" and rows[2]["meta"] == "PIT · Undisclosed", "the injury as the source wrote it"
    foot = dg.card_foot("status")
    assert foot == COPY["digest.card.status.foot"] and "FULL full" not in foot, "one word per mark"
    dg.plant_news_for("puka-nacua", "Puka Nacua (hip) doubtful to play Sunday")
    dg.open_row("status", 0)
    text = dg.research("status", 0)
    assert "Hip" in text and "Puka Nacua (hip) doubtful to play Sunday" in text and "D. Robinson" in text
    dg.plant_practice_missing()
    assert all(r["marks"] == [] and r["mid"] == "" for r in dg.card_rows("status")), "no practice log, no marks"
    assert dg.card_foot("status") is None, "no marks drawn, so no legend for them"
    dg.plant("LIVE_DIGEST.hurt.forEach(h => { h.practice = [{day: 'Wed', mark: null}, {day: 'Thu', mark: null}, {day: 'Fri', mark: null}]; })")
    assert dg.card_foot("status") is None, "a log with no report on any day draws only empty chips"
    dg.plant("LIVE_DIGEST.hurt[0].practice = [{day: 'Wed', mark: 'DNP'}, {day: 'Thu', mark: null}, {day: 'Fri', mark: null}]")
    assert dg.card_foot("status") == COPY["digest.card.status.foot"]
    assert dg.fits() and errors == []


@pytest.mark.req("Digest", ac="Thursday's status card is the Injury watch: Questionable only")
def test_thursdays_status_card_is_the_injury_watch_of_questionable_players(mount):
    dg, errors = day(mount, "thu")
    assert "status" in dg.card_ids()
    assert dg.card_head("status")["title"] == words("digest.card.status.titleThu")
    rows = dg.card_rows("status")
    assert len(rows) == 7 and {r["answer"] for r in rows} == {"Q"}
    assert "P. Nacua" not in [r["name"] for r in rows]
    assert errors == []


EMPTY = [("tue", "dgCardAdds", "ctx.d.adds = []"), ("tue", "dgCardAdds", "ctx.d = null"),
         ("tue", "dgCardGains", "ctx.d.gains = []"), ("tue", "dgCardGains", "ctx.d = null"),
         ("wed", "dgCardUsage", "ctx.usage = null"), ("wed", "dgCardUsage", "ctx.usage = {rows: []}"),
         ("wed", "dgCardDefenses", "ctx.def = null; ctx.sos = null"),
         ("fri", "dgCardStatus", "ctx.d.hurt = []"), ("fri", "dgCardStatus", "ctx.d = null"),
         ("thu", "dgCardStatus", "ctx.d.hurt.forEach(h => { h.status = 'Out'; })")]


@pytest.mark.req("Digest", ac="a card with nothing to show returns empty, so the day skips it")
@pytest.mark.parametrize("when,card,patch", EMPTY, ids=[f"{w}:{c}:{p}" for w, c, p in EMPTY])
def test_a_card_without_its_data_draws_nothing(mount, when, card, patch):
    dg, errors = day(mount, when)
    assert dg.drawn(card) != "", "the same ctx does draw it"
    assert dg.drawn(card, patch) == ""
    assert errors == []


@pytest.mark.req("Digest", ac="the defenses card drops a position the data lacks: no k_allowed, or null numbers, no K row")
def test_defenses_without_kickers_have_four_rows_and_without_the_defense_file_only_the_kicker(mount):
    dg, errors = day(mount, "wed")
    assert dg.drawn("dgCardDefenses", "ctx.def = null").count("dg-r-tile") == 1, "the kicker row alone"
    assert dg.drawn("dgCardDefenses", "ctx.sos = {...ctx.sos, k_allowed: null}").count("data-dgr=") == 4
    nulled = "ctx.sos = {...ctx.sos, k_allowed: Object.fromEntries(Object.keys(ctx.sos.k_allowed).map(k => [k, {pts_pg: null, games: 0, rank: null}]))}"
    assert dg.drawn("dgCardDefenses", nulled).count("data-dgr=") == 4
    assert dg.drawn("dgCardDefenses", "ctx.sos = {...ctx.sos}; delete ctx.sos.k_allowed").count("data-dgr=") == 4
    assert errors == []


@pytest.mark.req("Digest", ac="the K row is the defense with the most kicker points a game allowed, not a schedule")
def test_the_kicker_row_follows_the_highest_k_allowed(mount):
    dg, errors = day(mount, "wed")
    html = dg.drawn("dgCardDefenses", "ctx.sos = {...ctx.sos, k_allowed: {...ctx.sos.k_allowed, ATL: {pts_pg: 12.34, games: 4, rank: 32}}}")
    assert "12.3" in html and "Atlanta" in html and "vs Ks" in html
    assert errors == []


def test_the_untested_marks_say_so_in_the_repos_wording():
    assert SAYS.search(COPY["digest.card.usage.mark"]), "the usage change is descriptive and untested (12.105)"
    assert SAYS.search(COPY["digest.card.defenses.foot"]) and "(12.97): did not predict points." in COPY["digest.card.defenses.foot"]
    assert all("\n" not in COPY[k] and len(COPY[k]) < 220 for k in ("digest.card.usage.mark", "digest.card.defenses.foot"))
