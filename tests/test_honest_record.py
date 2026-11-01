"""S10, an honest record: "Our calls lose to Pitcher List or to the books; a reader views the record or
Accuracy: the record is shown as it is, including a losing one, and an untested number says 'not backtested'"
(PRODUCT.md Positioning, Principles 1 and 5; David ruled the label a hard rule on 2026-10-31).

Part 1, a losing record is drawn as it is. The inputs are written by hand here, each number chosen so that
we lose, and the page must print those numbers and name the other side as the closer: Accuracy in Node
(`acView` into `acHTML`), the Start/Sit record line on the mounted page.
Part 2, the label. Every place the page already marks a number as untested draws its mark: the Schedule's
label (the file's own words, read from the fixture), and the usage movers' mark (the Wednesday card's foot,
the Wednesday banner's headline, a Tuesday add's foot), whose words come from content.json through `words`.
"""
import json
import pathlib
import re

import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.digest_cards import DigestCardsPage
from pages.matchups import MatchupsPage
from pages.schedule import SchedulePage
from wording import words

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "data"

# One week where FantasyPros beats us on every number: a bigger average miss, a worse rank order, a lower hit rate.
LOSING_WEEK = {"weeks": [{"week": 6, "model": "pre-blend", "by_pos": {
    "QB": {"shared": {"n": 30, "ours": {"mae": 7.0, "rho": 0.4, "hit": 0.33}, "fp": {"mae": 5.0, "rho": 0.6, "hit": 0.58},
                      "hit_n": 12, "rank_n": 30}},
    "RB": {"shared": {"n": 28, "ours": {"mae": 6.5, "rho": None, "hit": None}, "fp": {"mae": 6.0, "rho": None, "hit": None},
                      "hit_n": None, "rank_n": None}}}}]}

# The season to date, our miss 1.6 over theirs with a range that leaves 0 out: FantasyPros was clearly closer.
LOSING_SEASON = {"weeks": [5, 6], "stale": False, "by_pos": {
    "QB": {"shared": {"n": 60, "mae_ours": 7.1, "mae_fp": 5.5, "d": 1.6, "d_ci": [0.9, 2.3]}}}}


@pytest.fixture(scope="module")
def ac(node_js):
    return node_js("data/accuracy.js", "surface/recap/accuracy.js")


def rows(html):
    """{position: (the row's markup, what a reader sees in it)} for every position row of a card."""
    seen = lambda m: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m)).strip()  # noqa: E731
    return {pos: (body, seen(body.split(">", 1)[1])) for body, pos in re.findall(r'(data-acpos="(\w+)"[^>]*>.*?)</div>', html, re.S)}


# ---- 1. a losing record is drawn as it is ----

def test_a_week_we_lost_prints_both_misses_and_names_fantasypros_closer(ac):
    qb_html, qb_text = rows(ac("acHTML", ac("acView", LOSING_WEEK)))["QB"]
    assert qb_text.startswith(f"QB {words('weekrecap.acc.n').format(n=30)} 7.00 5.00 {words('weekrecap.acc.who.fp')}")
    assert '<b class="wr-ac-v win">5.00</b>' in qb_html, "the lit number is FantasyPros', the closer"
    assert '<b class="wr-ac-v">7.00</b>' in qb_html, "ours is printed, unlit"
    assert words("weekrecap.acc.who.ours") not in qb_text.split("5.00")[1]


def test_a_week_we_lost_by_a_hair_still_names_fantasypros(ac):
    row_html, row_text = rows(ac("acHTML", ac("acView", LOSING_WEEK)))["RB"]
    assert row_text.startswith(f"RB {words('weekrecap.acc.n').format(n=28)} 6.50 6.00 {words('weekrecap.acc.who.fp')}")
    assert 'data-closer="fp"' in row_html


def test_a_week_we_lost_prints_the_lower_rank_order_and_hit_rate(ac):
    qb_text = rows(ac("acHTML", ac("acView", LOSING_WEEK)))["QB"][1]
    assert words("weekrecap.acc.rank").format(o="0.40", f="0.60") in qb_text
    assert words("weekrecap.acc.hits").format(n=12, o="33%", f="58%") in qb_text


def test_a_season_we_lost_prints_the_gap_the_range_and_fantasypros_closer(ac):
    html = ac("acHTML", ac("acView", {**LOSING_WEEK, "season_to_date": LOSING_SEASON}))
    season = html.split("data-acseason")[1].split("data-acweek=")[0]
    qb_html, qb_text = rows(season)["QB"]
    ci = words("weekrecap.acc.ci").format(level=95, lo="0.90", hi="2.30")
    assert qb_text == (f"QB {words('weekrecap.acc.n').format(n=60)} 7.10 5.50 {words('weekrecap.acc.who.fp')} "
                       f"{words('weekrecap.acc.by').format(d='1.60')} · {ci} · {words('weekrecap.acc.clear')}")
    assert 'data-closer="fp"' in qb_html and 'data-clear="1"' in qb_html


@pytest.mark.render
def test_a_losing_startsit_record_shows_its_hit_miss_counts_and_the_others_lead(mount):
    page, errors = mount("ranks")
    losing = {"since_week": 5, "weeks": [], "last_week": [], "smash": {"hit": 3, "miss": 9, "void": 0},
              "start": {"hit": 1, "miss": 4, "void": 0}, "sit": {"hit": 2, "miss": 3, "void": 0},
              "fun": {"fantasypros": {"hit": 8, "miss": 2}, "pitcherlist": {"hit": 7, "miss": 3}}}
    record = MatchupsPage(page).open(f"Object.assign(LIVE_SS3.record, {json.dumps(losing)})").record()
    call = {k: words(f"matchups.call.{k}") for k in ("smash", "start", "sit")}
    head = f"{words('matchups.record.label')} {words('matchups.record.since').format(wk=5)}"
    lines = [line.strip() for line in record.splitlines() if line.strip()]
    assert lines == [f"{head}: 3-9 {call['smash']} · 1-4 {call['start']} · 2-3 {call['sit']}",
                     words("matchups.record.fun").format(fp="8-2", pl="7-3")]
    assert errors == []


# ---- 2. an untested number says so ----

@pytest.mark.render
def test_schedule_draws_the_files_context_only_label_under_its_heading(mount):
    file_label = json.loads((FIXTURES / "sos.json").read_text(encoding="utf-8"))["label"]
    page, errors = mount("schedule", size=(360, 800))
    assert SchedulePage(page).label() == file_label
    assert errors == []


@pytest.mark.render
def test_the_usage_movers_card_foot_carries_the_untested_mark(mount):
    page, errors = mount("digest", size=(360, 800))
    dg = DigestCardsPage(page)
    dg.on("wed")
    assert dg.card_foot_tip("usage") == words("digest.card.usage.mark")
    assert errors == []


@pytest.mark.render
def test_a_shrinking_adds_foot_carries_the_untested_mark(mount):
    page, errors = mount("digest", size=(360, 800))
    dg = DigestCardsPage(page)
    dg.on("tue")
    dg.plant_a_shrinking_add()
    dg.open_row("adds", 0)
    assert words("digest.card.usage.mark") in dg.research("adds", 0)
    assert errors == []


@pytest.mark.render
def test_wednesdays_banner_head_carries_the_untested_mark(mount):
    page, errors = mount("digest", size=(360, 800))
    dg = DigestCardsPage(page)
    dg.on("wed")
    assert dg.banner_marks()["head"] == words("digest.card.usage.mark")
    assert errors == []
