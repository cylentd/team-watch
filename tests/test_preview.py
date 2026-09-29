"""This week > Preview (2026-09-29, storyboard option A): a slate of every game by kickoff window,
and a tap opens the game's dossier. Rendered from the fixture build.

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
from preview import _ats, _base, _blind, _total, live_preview
from test_render import SEED, browser  # noqa: F401  (browser is a fixture)

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
    assert w2["games"][1] == {"away": "SEA", "home": "LA", "pick": "LA", "side": "LA", "conf": "strong", "spread_home": -3.0,
                              "result": {"home": 27, "away": 24}, "hit": "push"}
    assert contract.problems("LIVE_PREVIEW", {**block, "record": rec}) == []


def test_before_a_final_week_the_record_is_empty():
    empty = json.loads(RECORD.read_text(encoding="utf-8"))
    empty.update(through_week=None, weeks=[])
    empty["totals"]["blind"] = {"n": 0, "ats": "0-0-0", "ats_pass": 0, "margin_mae": {"blind": None, "market": None, "final": None}}
    rec = live_preview(json.loads(FIXTURE.read_text(encoding="utf-8")), slug, empty)["record"]
    assert rec["weeks"] == [] and rec["through"] is None and (rec["closer"], rec["graded"]) == (0, 0)
    assert rec["blind"] is None
    assert live_preview(json.loads(FIXTURE.read_text(encoding="utf-8")), slug)["record"] is None


def open_preview(browser, page_file, w=360, h=800):
    ctx = browser.new_context(viewport={"width": w, "height": h}, reduced_motion="reduce", has_touch=True)
    pg = ctx.new_page()
    pg.set_default_timeout(5000)
    pg.route(re.compile(r"^https?://"), lambda route: route.abort())
    pg.add_init_script(SEED)
    pg.goto(page_file.as_uri() + "#preview")
    pg.wait_for_function("document.querySelector('.pv-row') !== null")
    return ctx, pg


@pytest.fixture
def page(browser, page_file):
    ctx, pg = open_preview(browser, page_file)
    yield pg
    ctx.close()


def is_open(pg):
    return pg.evaluate("document.querySelector('.pv').classList.contains('open')")


def match(pg):
    return pg.inner_text(".pv-mt")


@pytest.mark.render
def test_the_slate_lists_every_game_by_window(page):
    wins = page.evaluate("""() => [...document.querySelectorAll('.pv-win')].map(w => [
        w.querySelector('.pv-wh span').textContent, [...w.querySelectorAll('.pv-rm')].map(r => r.textContent)])""")
    assert wins == [["Thu night", ["PIT @ CLE"]], ["Sun morning", ["JAX @ LA"]], ["Sun early", ["DET @ CAR"]],
                    ["Sun late", ["SF @ NYJ"]], ["Mon night", ["ATL @ NO"]]]
    assert page.inner_text(".pv-wh em >> nth=0") .upper() == "8:15 PM ET"
    assert not is_open(page) and not page.is_visible(".pv-dz")


@pytest.mark.render
def test_a_row_says_the_spread_in_words_and_its_flags(page):
    metas = page.evaluate("() => [...document.querySelectorAll('.pv-meta')].map(m => m.innerText.replace(/\\s+/g, ' '))")
    assert metas[0] == "PIT by 2.5 Total 38.5 Short week"                # no edge: the spread stays in the meta
    assert metas[1] == "Total 46.5 UPSET Wind 17 mph"                    # a side says the spread ("JAX getting 3")
    assert metas[2] == "Total 50.5 Rain 56% J. Coker out"
    assert metas[3] == "Total 41.5 UPSET Line flipped"
    assert metas[4] == "NO by 2.5 Total 48.5"                             # no take
    assert not any(re.search(r"[-−]\d", m) for m in metas)
    assert "Claude's call arrives" in page.inner_text("[data-pvopen='4']")


def texts(pg, sel):
    return pg.evaluate("s => [...document.querySelectorAll(s)].map(e => e.innerText.replace(/\\s+/g, ' ').trim())", sel)


@pytest.mark.render
def test_a_row_carries_claudes_side_and_its_chip(page):
    assert texts(page, ".pv-ats") == ["NO EDGE", "JAX getting 3 STRONG", "DET giving 3.5 SOLID", "SF getting 1.5 LEAN"]
    chips = page.evaluate("() => [...document.querySelectorAll('.pv-row .pv-conf')].map(c => c.className)")
    assert chips == ["pv-conf none", "pv-conf strong", "pv-conf solid", "pv-conf lean"]
    assert page.locator("[data-pvopen='4'] .pv-ats").count() == 0      # no take, no chip
    assert page.locator("[data-pvopen='0'] .pv-side").count() == 0     # no edge: no side text


@pytest.mark.render
def test_the_win_bar_needs_the_markets_win_pct(page):
    has_bar = [page.locator(f"[data-pvopen='{i}'] .pv-pb").count() for i in range(5)]
    assert has_bar == [1, 1, 1, 0, 0]                                    # SF @ NYJ: no moneyline; ATL @ NO: no take
    assert texts(page, "[data-pvopen='2'] .pv-key") == ["DET wins 30–19 market 64% · Claude 74%"]
    assert texts(page, "[data-pvopen='3'] .pv-key") == ["SF wins 24–17 Claude 60%"]
    style = page.get_attribute("[data-pvopen='1'] .pv-pb", "style")
    assert "--mk:41.7%" in style and "--cl:54%" in style                 # JAX, the underdog Claude picks


@pytest.mark.render
def test_the_game_page_leads_with_claudes_call(page):
    page.click("[data-pvopen='2']")                                      # DET @ CAR
    rows = page.evaluate("() => [...document.querySelectorAll('.pvd-row')].map(r => r.classList[1])")
    assert rows[:3] == ["call", "pick", "lines"]
    pick = page.inner_text(".pvd-row.pick").replace("\n", " ")
    for want in ("CLAUDE'S CALL", "DET giving 3.5", "SOLID", "Carolina without Coker", "DET 74%", "market 64%",
                 "Under 50.5", "LEAN", "DET 30, CAR 19", "market DET 27, CAR 23.5",
                 "A 3.5-point favorite, 2011–2025: wins 67%, covers 49%, n 1,314."):
        assert want in pick, want
    assert "Claude before seeing the line: DET by 1.5, total 48.5" in pick
    assert "moved it to 11" in page.inner_text(".pvd-row.pick .pv-vsb")
    assert texts(page, ".pv-notes li") == ["Carolina has allowed 5.1 yards a carry since week 1. espn.com",
                                           "Gibbs took 11 of Detroit's 14 red-zone carries last week. play-by-play",
                                           "Coker was ruled out Friday."]
    links = page.evaluate("() => [...document.querySelectorAll('.pv-notes a')].map(a => [a.href, a.target, a.rel])")
    assert links == [["https://www.espn.com/nfl/story/_/id/1", "_blank", "noopener noreferrer"]]
    assert page.inner_text(".pv-nh") == "RESEARCH NOTES"
    assert "Claude" not in page.inner_text(".pvd-row.lines")             # the score folded into the call row
    assert page.locator(".pv-score").count() == 0 and page.locator(".pv-vs").count() == 0
    page.click("[data-pvstep='-1']")
    assert page.locator(".pv-blind").count() == 0 and page.locator(".pv-notes").count() == 0   # JAX @ LA: no research
    page.click("[data-pvstep='-1']")                                     # PIT @ CLE: no edge
    assert page.locator(".pvd-row.pick .pv-edge").count() == 0 and page.locator(".pvd-row.pick .pv-side").count() == 0
    assert page.locator(".pvd-row.pick .pv-conf.none").count() == 2      # the side and the total


def open_record(pg):
    pg.click("[data-pvrec]")
    pg.wait_for_function("document.querySelector('.pv').classList.contains('rec')")


@pytest.mark.render
def test_the_record_card_opens_every_week_and_back_closes_it(page):
    card = page.inner_text("[data-pvrec]").replace("\n", " ")
    for want in ("CLAUDE VS THE SPREAD", "EVERY WEEK", "4–2–1", "VS SPREAD", "67% hit", "STRONG 1–0–1", "SOLID 1–1",
                 "LEAN 2–1", "Win % closer than the market's on 4 of 7", "Blind number vs spread 4–3",
                 "Margin error: blind 9.1, market 8.4"):
        assert want in card, want
    assert page.locator(".pv-rec").evaluate("e => e.getBoundingClientRect().top") < page.locator(".pv-win").first.evaluate(
        "e => e.getBoundingClientRect().top")                             # the card heads the slate
    page.evaluate("window.scrollTo(0, 60)")
    y = page.evaluate("scrollY")
    open_record(page)
    assert not page.is_visible(".pv-slate") and page.is_visible(".pv-rz")
    assert page.evaluate("location.hash") == "#preview"
    assert page.inner_text(".pv-rz .pvd-rt") == "CLAUDE VS THE SPREAD, THROUGH WEEK 2"
    rows = page.evaluate("() => [...document.querySelectorAll('.pv-rt tr')].map(r => [...r.cells].map(c => c.innerText.trim()))")
    assert rows[1:] == [["2", "1–2–1", "0–0–1", "3 of 4", "2 of 3"], ["1", "3–0", "1–0", "3 of 4", "2 of 4"],
                        ["Season", "4–2–1", "1–0–1", "6 of 8", "4 of 7"]]
    opened = page.evaluate("() => [...document.querySelectorAll('.pv-rw')].map(d => d.open)")
    assert opened == [True, False]                                       # the newest week open
    assert texts(page, ".pv-rw[open] .pv-hit") == ["MISS", "PUSH", "HIT", "MISS"]
    assert page.locator(".pv-rw[open] .pv-hit.hit").count() == 1 and page.locator(".pv-rw[open] .pv-hit.miss").count() == 2
    assert texts(page, ".pv-rw[open] .pv-rg-a")[:2] == ["NYJ giving 1.5 SOLID", "LA giving 3 STRONG"]
    assert "NE 20–13" in page.inner_text(".pv-rw[open] .pv-rg >> nth=0")
    page.go_back()
    page.wait_for_function("!document.querySelector('.pv').classList.contains('rec')")
    page.wait_for_timeout(50)
    assert page.is_visible(".pv-slate") and page.evaluate("scrollY") == y
    assert page.evaluate("location.hash") == "#preview"


@pytest.mark.render
def test_the_records_back_button_closes_it(page):
    open_record(page)
    page.click("[data-pvrecback]")
    assert page.is_visible(".pv-slate") and page.locator(".pv-rz").count() == 0
    assert page.evaluate("LAYERS.length") == 0


@pytest.mark.render
def test_before_a_final_week_the_record_is_one_line(page):
    page.evaluate("() => { LIVE_PREVIEW.record.weeks.splice(0); render(); }")
    assert page.locator("[data-pvrec]").count() == 0
    assert page.inner_text(".pv-rec0") == "Claude's record against the spread starts once week 2 is final."
    page.evaluate("() => { LIVE_PREVIEW.record = null; render(); }")    # no record file at all: the same line
    assert page.inner_text(".pv-rec0").startswith("Claude's record")


@pytest.mark.render
def test_no_signed_spread_anywhere_in_the_preview(page):
    """David: never a signed spread. A side is "CLE getting 2.5" / "IND giving 3.5", a line "PIT by 2.5"."""
    seen = [page.inner_text(".pv-slate")]
    for i in range(5):
        page.evaluate(f"() => {{ PV_I = {i}; PV_OPEN = true; render(); }}")
        seen += texts(page, ".pvd-row.call, .pvd-row.pick, .pvd-row.lines")
    page.evaluate("() => { PV_OPEN = false; render(); }")
    open_record(page)
    page.evaluate("() => document.querySelectorAll('.pv-rw').forEach(d => d.open = true)")
    seen.append(page.inner_text(".pv-rz"))
    signed = [m.group(0) for s in seen for m in re.finditer(r"(?<![\w.])[+\-−]\d+(\.\d)?", s)]
    assert signed == []
    assert "giving" in " ".join(seen) and "getting" in " ".join(seen)


@pytest.mark.render
def test_a_tap_opens_the_dossier_and_back_returns_to_the_slate_where_it_was(page):
    page.evaluate("window.scrollTo(0, 120)")
    y = page.evaluate("scrollY")
    page.click("[data-pvopen='3']")
    assert is_open(page) and match(page) == "SF @ NYJ"
    assert not page.is_visible(".pv-slate")
    assert page.evaluate("location.hash") == "#preview"          # the game is not in the URL
    lines = page.inner_text(".pvd-row.lines")
    assert "NYJ by 1.5" in lines and "opened SF by 3" in lines and "opened 43.5" in lines
    assert "+3 zones east · kicks off at 1:25 PM body time" in page.inner_text(".pvd-row.rest")
    page.go_back()
    page.wait_for_function("!document.querySelector('.pv').classList.contains('open')")
    page.wait_for_timeout(50)
    assert page.evaluate("scrollY") == y
    assert page.evaluate("location.hash") == "#preview"


@pytest.mark.render
def test_the_all_games_button_closes_the_dossier(page):
    page.click("[data-pvopen='0']")
    page.click("[data-pvback]")
    assert not is_open(page)
    page.click("[data-pvopen='1']")                             # and opening again still works
    assert is_open(page) and match(page) == "JAX @ LA"


@pytest.mark.render
def test_optional_rows_are_absent_without_data(page):
    rows = lambda: page.evaluate("() => [...document.querySelectorAll('.pvd-row')].map(r => r.classList[1])")
    page.click("[data-pvopen='4']")                              # ATL @ NO: dome, no take, no rest
    assert rows() == ["call", "lines", "inj", "wx"]              # no matchup, rest, players or risk
    assert "Dome" in page.inner_text(".pvd-row.wx")
    assert page.locator(".pv-pl").count() == 0 and page.locator(".pv-risk").count() == 0
    page.click("[data-pvstep='-1']")
    page.click("[data-pvstep='-1']")                             # DET @ CAR: the one with defense ranks
    assert match(page) == "DET @ CAR" and page.locator(".pv-mx").count() == 1
    assert page.locator(".pv-mx tr.dim").inner_text().startswith("WR")
    assert "Rain" in page.inner_text(".pv-eff")                  # rain 56% is past the backtest's threshold
    assert "J. Coker" in page.inner_text(".pv-inj >> nth=1")


@pytest.mark.render
def test_neutral_site_and_short_week(page):
    page.click("[data-pvopen='1']")
    assert "Neutral site: Wembley Stadium" in page.inner_text(".pvd-row.rest")
    assert "OFF A BYE" in page.inner_text(".pvd-row.rest")
    page.click("[data-pvstep='-1']")
    assert page.locator(".pvd-row.rest .pv-tag.short").count() == 2


def swipe(pg, dx):
    pg.evaluate("""dx => {
        const el = document.querySelector('[data-pvswipe]');
        const t = x => new Touch({identifier: 1, target: el, clientX: x, clientY: 300});
        el.dispatchEvent(new TouchEvent('touchstart', {touches: [t(200)], changedTouches: [t(200)], bubbles: true}));
        el.dispatchEvent(new TouchEvent('touchend', {touches: [], changedTouches: [t(200 + dx)], bubbles: true}));
    }""", dx)


@pytest.mark.render
def test_a_swipe_in_the_dossier_walks_the_games_and_stops_at_the_ends(page):
    page.click("[data-pvopen='0']")
    swipe(page, -120)
    assert match(page) == "JAX @ LA" and is_open(page)
    swipe(page, 120)
    assert match(page) == "PIT @ CLE"
    swipe(page, 120)                                  # past the first game: nothing
    assert match(page) == "PIT @ CLE"
    swipe(page, -20)                                  # a nudge is not a swipe
    assert match(page) == "PIT @ CLE"


@pytest.mark.render
def test_a_player_row_opens_his_profile(page):
    page.click("[data-pvopen='0']")
    page.evaluate("() => { window.__opened = []; openProfile = p => window.__opened.push(p.slug); }")
    page.click(".pv-p >> nth=0")
    assert page.evaluate("window.__opened") == ["dk-metcalf"]


@pytest.mark.render
def test_a_desktop_shows_the_rail_beside_the_dossier(browser, page_file):
    ctx, pg = open_preview(browser, page_file, 1280, 900)
    try:
        assert pg.is_visible(".pv-slate") and pg.is_visible(".pv-dz") and match(pg) == "PIT @ CLE"
        pg.click("[data-pvopen='2']")
        assert match(pg) == "DET @ CAR" and pg.locator(".pv-row.cur .pv-rm").inner_text() == "DET @ CAR"
        assert pg.evaluate("LAYERS.length") == 0 and not is_open(pg)   # a click on a desktop pushes no layer
        slate, dz = pg.evaluate("""() => [document.querySelector('.pv-slate'), document.querySelector('.pv-dz')]
            .map(e => e.getBoundingClientRect().left)""")
        assert slate < dz
        # The record opens in the dossier's place, the rail stays; a game (or the card again) closes it.
        open_record(pg)
        assert pg.is_visible(".pv-slate") and pg.is_visible(".pv-rz") and pg.locator(".pv-dz").count() == 0
        assert pg.locator(".pv-rec.cur").count() == 1 and pg.locator(".pv-row.cur").count() == 0
        pg.click("[data-pvopen='1']")
        assert match(pg) == "JAX @ LA" and pg.locator(".pv-rz").count() == 0 and pg.evaluate("LAYERS.length") == 0
        open_record(pg)
        pg.click("[data-pvrec]")
        assert pg.locator(".pv-rz").count() == 0 and match(pg) == "JAX @ LA"
    finally:
        ctx.close()


@pytest.mark.render
def test_nothing_scrolls_sideways_at_360(page):
    for i in range(5):
        page.evaluate(f"() => {{ PV_I = {i}; PV_OPEN = true; render(); }}")
        assert page.evaluate("document.documentElement.scrollWidth") <= 360, f"game {i}"
    page.evaluate("() => { PV_OPEN = false; PV_REC = true; render(); document.querySelectorAll('.pv-rw').forEach(d => d.open = true); }")
    assert page.locator(".pv-rz").count() == 1
    assert page.evaluate("document.documentElement.scrollWidth") <= 360, "the record"
