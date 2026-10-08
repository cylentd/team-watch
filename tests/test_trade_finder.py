"""League > Trades, the finder (design/src/js/surface/finder/, 2026-10-06): one chip per position with the reader's gap to
the league's median, opening on the most negative gap; the offers whose `get` holds that position; who is deep there; the
filtered state ("Trades with <team>"); Make your own. The pure logic (gaps, the default chip, which offers a chip shows,
the deep ranking) is test_js_finder.py, in Node; the offer cards' copy and the guard are test_trade_offers.py and
test_trade_edit.py; this file is what the screen draws and does. Every test mounts the Trades view alone
(tests/component.py) and reads it through tests/pages/finder.py.

Two kinds of data. A league planted into LIVE_TEAMS with offers written for it, so every expected number is worked out
here: Me Team's columns are QB 20, RB 15, WR 24, TE 7 against the medians 18, 22, 20, 7, so the gaps are +2.0, -7.0, +4.0
and 0.0 and RB opens. And the fixture's own ESPN league (Purdy Big in Japan and Run It Back, offers in
tests/fixtures/data/trade_offers.json), where Purdy's offers get only RB and WR: QB and TE are the empty states."""
import copy

import pytest

from component import mount  # noqa: E402,F401  (the fixture)
from pages.finder import COPY_REFUSED, FinderPage, finder, serve, FIXTURE  # noqa: E402
from wording import words  # noqa: E402

MEDIAN = {"QB": 18.0, "RB": 22.0, "WR": 20.0, "TE": 7.0, "FLX": 8.0}
RULES = {"top": 3, "per_pos": 5, "per_partner_pos": 2, "max_out": 3, "max_in": 2, "min_gain": 6.5, "min_gain_week": 0.5,
         "unit": "rest of season points"}


def starter(slot, name, pos, pts):
    return {"slot": slot, "n": name, "pos": pos, "pts": pts, "team": "XXX", "bye": False}


def team(key, name, cols, lineup, w, l):
    return {"key": key, "name": name, "w": w, "l": l, "t": 0, "tot": sum(cols[c] for c in ("QB", "RB", "WR", "TE")),
            "cols": {**cols, "FLX": 8.0}, "spare": [], "lineup": lineup, "bench": []}


LEAGUE = {"key": "espn", "name": "Test League", "slots": {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1}, "median": MEDIAN, "teams": [
    team("espn", "Me Team", {"QB": 20.0, "RB": 15.0, "WR": 24.0, "TE": 7.0}, [starter("RB", "Mia Me", "RB", 15.0)], 3, 1),
    team("espn-alpha", "Alpha", {"QB": 16.0, "RB": 30.0, "WR": 18.0, "TE": 9.0},
         [starter("RB", "Rob Alpha", "RB", 17.0), starter("RB", "Ray Allen", "RB", 13.0), starter("WR", "Walt Alpha", "WR", 18.0)], 3, 1),
    team("espn-beta", "Beta", {"QB": 19.0, "RB": 22.0, "WR": 26.0, "TE": 5.0},
         [starter("RB", "Rae Beta", "RB", 22.0), starter("WR", "Wes Beta", "WR", 14.0), starter("WR", "Wen Bell", "WR", 12.0)], 2, 2),
    team("espn-gamma", "Gamma", {"QB": 18.0, "RB": 28.0, "WR": 20.0, "TE": 7.0},
         [starter("RB", "Rudy Gamma", "RB", 28.0), starter("WR", "Wil Gamma", "WR", 20.0)], 2, 2),
    team("espn-delta", "Delta", {"QB": 14.0, "RB": 12.0, "WR": 15.0, "TE": 3.0}, [starter("RB", "Ron Delta", "RB", 12.0)], 1, 3),
]}


def p(name, pos, **kw):
    return {"name": name, "pos": pos, "team": "XXX", "slug": name.lower().replace(" ", "-"), "seen": 10.0, "injury": None,
            "last2": 10.0, "chips": [], **kw}


def offer(partner, send, get, gain):
    return {"partner": partner, "send": send, "get": get, "gain": gain, "drop": [], "ir_moves": [], "their": {"ir_moves": [], "drop": [], "gain": 0.0}}


OFFERS = [
    offer("Alpha", [p("Wally Smith", "WR")], [p("Rob Alpha", "RB")], 6.1),
    offer("Beta", [p("Ray Jones", "RB")], [p("Wes Beta", "WR")], 5.2),
    offer("Gamma", [p("Quinn Day", "QB")], [p("Rex Gamma", "RB"), p("Tom Gamma", "TE")], 4.8),
    offer("Alpha", [p("Ted Fox", "TE")], [p("Quinn Alpha", "QB")], 3.0),
    offer("Gamma", [p("Walt Hill", "WR")], [p("Wil Gamma", "WR")], 2.2),
    offer("Delta", [p("Will Ames", "WR")], [p("Rudy Delta", "RB")], 1.2),
]
BODY = {"updated": "2026-10-05T14:07", "season": 2026, "rules": RULES, "leagues": {"espn": {"week": 4, "weeks_left": 13, "teams": {"Me Team": OFFERS}}}}


def planted(mount, size=(360, 740), league=LEAGUE):
    """The finder for Me Team in the planted league, with its offers served."""
    page, errors = finder(mount, "espn", size=size, body=BODY)
    # The fixture's league drew first and the chip it opened on is kept for the visit: start the planted one over.
    page.evaluate("b => { LIVE_TEAMS.leagues = LIVE_TEAMS.leagues.filter(l => l.key !== b.key); LIVE_TEAMS.leagues.push(b);"
                  " TF = {lg: null, me: null, pos: null, partner: null}; render(); }", league)
    f = FinderPage(page)
    f.wait_offers()
    return f, errors


# ---- the chips ----------------------------------------------------------------------------------------------------

@pytest.mark.req("Trade finder", ac="the chip row opens on the most negative gap, each chip showing the signed gap")
def test_the_chip_row_is_each_position_with_the_readers_gap_and_opens_on_the_most_negative(mount):
    f, errors = planted(mount)
    assert [(c["pos"], c["gap"]) for c in f.chips()] == [("QB", "+2.0"), ("RB", "−7.0"), ("WR", "+4.0"), ("TE", "0.0")]
    assert [c["tone"] for c in f.chips()] == ["up", "dn", "up", ""], "red below the median, green above, plain at it"
    assert f.pressed() == ["RB"], "RB is the only position he is short at"
    assert f.offers_heading().lower() == "best offers at rb"
    assert errors == []


@pytest.mark.req("Trade finder", ac="a chip shows only the offers whose get holds that position")
def test_a_chip_shows_only_offers_with_that_position_in_get_best_gain_first(mount):
    f, errors = planted(mount)
    assert [(c["partner"], c["gain"]) for c in f.cards()] == [
        ("Alpha", "+6.1 pts rest of season"), ("Gamma", "+4.8 pts rest of season"), ("Delta", "+1.2 pts rest of season")], "RB: three of the six"
    f.pick("WR")
    assert [(c["partner"], c["gain"]) for c in f.cards()] == [("Beta", "+5.2 pts rest of season"), ("Gamma", "+2.2 pts rest of season")]
    assert f.pressed() == ["WR"] and f.offers_heading().lower() == "best offers at wr"
    f.pick("QB")
    assert f.partners() == ["Alpha"]
    f.pick("TE")
    assert [(c["partner"], c["get"]) for c in f.cards()] == [("Gamma", ["RB R. Gamma", "TE T. Gamma"])], "an offer for a RB and a TE is a TE offer too"
    assert errors == []


@pytest.mark.req("Trade finder", ac="an offer card: partner and record on top, you send, you get, the gain")
def test_an_offer_card_has_the_partner_and_his_record_on_top_then_what_moves_and_the_gain(mount):
    f, _ = planted(mount)
    first = f.cards()[0]
    assert (first["partner"], first["record"]) == ("Alpha", "3–1")
    assert first["send"] == ["WR W. Smith"] and first["get"] == ["RB R. Alpha"]
    assert first["gain"] == "+6.1 pts rest of season" and first["ir"] is None and first["drop"] is None


# ---- who is deep --------------------------------------------------------------------------------------------------

@pytest.mark.req("Trade finder", ac="who is deep at the chip's position: every other team ranked, tinted, with its starters there")
def test_who_is_deep_ranks_every_other_team_by_the_column_and_names_its_starters(mount):
    f, errors = planted(mount)
    assert f.deep_title().lower() == "who's deep at rb"
    assert [(d["name"], d["val"], d["tone"]) for d in f.deep()] == [
        ("Alpha", "30.0", "up"), ("Gamma", "28.0", "up"), ("Beta", "22.0", ""), ("Delta", "12.0", "dn")], "the reader is not in his own list"
    assert [d["starters"] for d in f.deep()] == ["R. Alpha, R. Allen", "R. Gamma", "R. Beta", "R. Delta"]
    assert f.deep()[0]["record"] == "3–1"
    f.pick("WR")
    assert [(d["name"], d["val"]) for d in f.deep()] == [("Beta", "26.0"), ("Gamma", "20.0"), ("Alpha", "18.0"), ("Delta", "15.0")]
    assert f.deep()[0]["starters"] == "W. Beta, W. Bell", "initials, every starter at the position"
    assert errors == []


@pytest.mark.req("Trade finder", ac="a team's name opens the finder filtered to him, with a way back to the chips")
def test_a_partner_name_filters_the_finder_to_him_and_all_positions_comes_back(mount):
    f, errors = planted(mount)
    f.pick("WR")
    f.open_partner("Alpha")
    assert f.is_filtered() and f.with_title() == "Trades with Alpha"
    assert [(c["partner"], c["gain"]) for c in f.cards()] == [("Alpha", "+6.1 pts rest of season"), ("Alpha", "+3.0 pts rest of season")], "every offer with him, whatever the position"
    assert f.chips() == [] and f.deep() == [], "no chips and no deep list while filtered"
    f.all_positions()
    assert not f.is_filtered() and f.pressed() == ["WR"], "back to the chips on the position he left"
    assert f.partners() == ["Beta", "Gamma"]
    assert errors == []


# ---- empty and no team --------------------------------------------------------------------------------------------

@pytest.mark.req("Trade finder", ac="a position with no offer says so in one line and keeps who's deep and Make your own")
def test_a_position_with_no_offer_says_so_and_keeps_whos_deep_and_make_your_own(mount):
    page, errors = finder(mount, "espn")                            # Purdy's offers get only RB and WR
    f = FinderPage(page)
    f.wait_offers()
    f.pick("TE")
    assert f.cards() == [] and f.empty_text() == "No offer at TE this week"
    assert [d["name"] for d in f.deep()] == ["Run It Back"], "who's deep stays"
    assert f.has_own(), "and so does Make your own"
    assert f.fits()
    assert errors == []


@pytest.mark.req("Trade finder", ac="a partner with no offer says so in one line")
def test_a_partner_with_no_offer_says_so_in_one_line_and_the_way_back_stays(mount):
    league = copy.deepcopy(LEAGUE)
    league["teams"].append(team("espn-epsilon", "Epsilon", {"QB": 10.0, "RB": 10.0, "WR": 10.0, "TE": 1.0}, [], 0, 4))
    f, errors = planted(mount, league=league)
    f.open_partner("Epsilon")
    assert f.cards() == [] and f.empty_text() == "No offers with Epsilon this week"
    f.all_positions()
    assert f.pressed() == ["RB"] and len(f.deep()) == 5
    assert errors == []


@pytest.mark.req("Trade finder", ac="with no team the picker stands in for the chips, with one line saying a trade needs your team")
def test_with_no_team_one_line_and_the_picker_stand_in_for_the_chips(mount):
    page, errors = finder(mount, None)
    f = FinderPage(page)
    assert f.need_text() == words("finder.need")
    assert f.chips() == [] and f.cards() == [], "nothing to offer without a team"
    assert "Run It Back" in f.picker_teams() and len(f.picker_teams()) >= 4
    f.pick_team("Run It Back")
    f.wait_offers()
    assert page.evaluate("localStorage.getItem('tw-team')") == "espn-run-it-back", "the team switch's own pick"
    assert f.need_text() is None and len(f.chips()) == 4
    assert errors == []


# ---- loading, the file ---------------------------------------------------------------------------------------------

@pytest.mark.req("Trade finder", ac="the file is fetched on first open, once; shapes while it loads; an error with a retry")
def test_the_finder_shows_shapes_while_loading_and_an_error_with_a_retry_and_fetches_once(mount):
    page, _ = finder(mount, "espn", init=("window.__tb = 'hold';",))
    assert page.locator(".tb-skel").count() == 3 and page.locator(".tb-line").inner_text() == words("lboard.offer.loading")
    assert page.get_by_test_id("finder-chip").count() == 4, "the chips do not wait for the file"
    page.evaluate("__tbRelease()")
    f = FinderPage(page)
    f.wait_offers()
    assert page.locator(".tb-skel").count() == 0
    f.pick("RB")
    f.pick("WR")
    assert page.evaluate("__tbFetches") == 1, "kept in memory for the visit"
    page, errors = finder(mount, "espn", init=("window.__tb = 'fail';",))
    f = FinderPage(page)
    page.wait_for_selector("[data-testid=finder-error]")
    assert words("lboard.offer.error") in page.get_by_test_id("finder-error").inner_text() and f.cards() == []
    assert f.deep(), "who's deep needs no file"
    page.evaluate("window.__tb = 'ok'")
    page.locator("[data-tbretry]").click()
    page.wait_for_selector("[data-testid=finder-card], [data-testid=finder-empty]")
    assert page.evaluate("__tbFetches") == 2
    assert errors == [], "a failed fetch is a state, not an exception"


@pytest.mark.req("Trade finder", ac="a file in another unit than rest-of-season points shows the error state, never a wrong number")
def test_a_file_in_another_unit_is_an_error_not_a_card_with_the_wrong_words(mount):
    """The build refuses a weekly file, so this is the stale-file case: an older trade_offers.json served beside this page."""
    weekly = copy.deepcopy(FIXTURE)
    weekly["rules"]["unit"] = "points a week"
    no_rules = {k: v for k, v in FIXTURE.items() if k != "rules"}
    page, errors = finder(mount, "espn", init=("window.__tb = 'fail';",))      # the loading test's page: its first fetch fails, then each retry is served below
    f = FinderPage(page)
    page.wait_for_selector("[data-testid=finder-error]")

    def retry_with(body):
        page.evaluate("b => { window.fetch = () => Promise.resolve(new Response(JSON.stringify(b), {status: 200})); }", body)
        page.locator("[data-tbretry]").click()

    seen = []
    for body in (weekly, no_rules):
        retry_with(body)
        page.wait_for_function("TB_BUSY === null && TB_ERR === true")
        seen.append({"held_nothing": page.evaluate("TB_DATA") is None and f.cards() == [],
                     "says_so": words("lboard.offer.error") in page.get_by_test_id("finder-error").inner_text(),
                     "deep_without_file": bool(f.deep())})
    # a file in the wrong unit is never held, and who's deep needs no file
    assert seen == [{"held_nothing": True, "says_so": True, "deep_without_file": True}] * 2
    retry_with(FIXTURE)
    page.wait_for_selector("[data-testid=finder-card]")
    assert page.evaluate("TB_DATA.rules.unit") == "rest of season points", "the right unit loads"
    assert errors == [], "a refused file is a state, not an exception"


# ---- copy offer ----------------------------------------------------------------------------------------------------

@pytest.mark.req("Trade finder", ac="Copy offer puts a message of true season averages on the clipboard")
def test_copy_offer_puts_a_message_of_true_season_averages_on_the_clipboard(mount):
    page, errors = finder(mount, "espn")
    f = FinderPage(page)
    f.wait_offers()
    f.open_partner("Run It Back")
    wants = (
            # Higgins is Hot and the reader sends him: his last 2 (19.8), Pollard carries the unit; Robinson is Hot but the reader gets him
            "Trade? I send Higgins (19.8 a game his last 2), Pollard (8.0 a game), Goff (28.4) for Robinson (24.2) and Coker (14.0),"
            " priced on the rest of the season. You'd only need to cut I. Davis.",
            "Trade? I send Higgins (19.8 a game his last 2), Pollard (8.0 a game), Goff (28.4) for Robinson (24.2) and Concepcion (4.9),"
            " priced on the rest of the season. You'd only need to cut I. Davis.",
            "Trade? I send Higgins (19.8 a game his last 2), Purdy (28.8 a game), Wilson (12.8 a game his last 2) for Williams (19.1) and Tuten (11.4),"
            " priced on the rest of the season. You'd only need to cut I. Davis.")
    got = []
    for i in range(len(wants)):
        page.locator(f"[data-tbcopy='{i}']").click()
        page.wait_for_function(f"document.querySelector(\"[data-tbcopy='{i}']\").textContent === 'Copied'")
        got.append(page.evaluate("navigator.clipboard.readText()"))
    assert got == list(wants)
    assert errors == []


@pytest.mark.req("Trade finder", ac="a refused clipboard shows the text selected in a box")
def test_a_refused_clipboard_shows_the_text_selected_in_a_box(mount):
    page, _ = finder(mount, "espn")
    f = FinderPage(page)
    f.wait_offers()
    page.evaluate(f"() => {{ {COPY_REFUSED} }}")                   # at run time, so this test shares the page the copy test loads
    f.open_partner("Run It Back")
    page.locator("[data-tbcopy='1']").click()
    page.wait_for_selector(".tb-box")
    assert page.locator(".tb-box").input_value() == (
        "Trade? I send Higgins (19.8 a game his last 2), Pollard (8.0 a game), Goff (28.4) for Robinson (24.2) and Concepcion (4.9),"
        " priced on the rest of the season. You'd only need to cut I. Davis.")
    assert page.evaluate("(() => { const b = document.querySelector('.tb-box'); return document.activeElement === b && b.selectionEnd - b.selectionStart === b.value.length; })()")
    assert page.locator("[data-tbcopy='1']").inner_text() == "Copy offer", "no false Copied"


# ---- the screen ----------------------------------------------------------------------------------------------------

@pytest.mark.req("Trade finder", ac="the first offer starts near the top at 360px and nothing scrolls sideways")
def test_the_first_offer_starts_under_the_chips_and_fits_a_phone_and_a_desktop(mount):
    f, _ = planted(mount)
    assert f.first_card_y() <= 260, f"the first offer starts at {f.first_card_y():.0f}px, under the team line and the chips"
    assert f.fits()
    assert f.page.evaluate("[...document.querySelectorAll('[data-testid=finder-chip], [data-testid=finder-deepname], .tb-copy, .tb-own')].every(b => b.getBoundingClientRect().height >= 44)"), "44px targets"
    f, _ = planted(mount, size=(1280, 900))
    assert f.fits()
    left = f.page.evaluate("document.querySelector('[data-testid=finder-card]').getBoundingClientRect().left - document.querySelector('.lgchip').getBoundingClientRect().left")
    assert abs(left) <= 1, f"left-aligned on the frame's edge, {left}px off the team line"
    assert f.page.evaluate("document.querySelector('[data-testid=finder-card]').getBoundingClientRect().width") <= 561, "a card keeps to one column"


# ---- the desktop: the offers and who is deep fill the frame, as the Teams cards do ---------------------------------
# The frame is what the team line spans (1185px at 1280). Teams draws as many 300px columns as it holds, so three
# at 1280 (DESIGN.md "Teams"); the finder draws its cards in the same columns, and a card stays within STYLE.md's
# 560px between its partner's name and his record.

def across(boxes):
    """How many columns the boxes sit in: their distinct left edges."""
    return len({round(b["x"]) for b in boxes})


def rows(boxes):
    """The boxes by row: lists of boxes sharing a top edge."""
    out = {}
    for b in boxes:
        out.setdefault(round(b["y"]), []).append(b)
    return list(out.values())


@pytest.mark.req("Trade finder", ac="on a desktop the offer cards fill the frame in columns of equal height")
def test_on_a_desktop_the_offers_fill_the_frame_three_across_in_rows_of_one_height(mount):
    f, errors = planted(mount, size=(1280, 900))
    frame, cards = f.frame_box(), f.card_boxes()
    assert len(cards) == 3 and across(cards) == 3, "RB has three offers, and three columns of 387px are Teams' at 1280px"
    assert round(cards[0]["x"]) == round(frame["x"]) and round(cards[-1]["x"] + cards[-1]["w"]) == round(frame["x"] + frame["w"]), \
        "the row runs the frame's width, no gap at its right edge"
    assert len({round(c["y"]) for c in cards}) == 1 and len({round(c["h"]) for c in cards}) == 1, "one top and one height"
    assert all(abs(c["w"] - (frame["w"] - 2 * 12) / 3) <= 1 for c in cards), "three equal columns and two 12px gaps: the Teams grid's (387px each in the 1185px frame of a real 1280px page)"
    f.pick("WR")                                                       # two offers: a row of two
    assert across(f.card_boxes()) == 2
    assert f.fits() and errors == []


@pytest.mark.req("Trade finder", ac="the offers' feet rest on the cards' bottom edge, so a row's buttons line up")
def test_a_row_of_offer_cards_shares_its_bottom_and_its_buttons(mount):
    f, _ = planted(mount, size=(1280, 900))
    cards = f.card_boxes()                                             # Gamma's gets two players, so the cards' own heights differ
    feet = f.page.evaluate("[...document.querySelectorAll('[data-testid=finder-card] .tb-foot')].map(e => { const r = e.getBoundingClientRect(); return r.bottom + scrollY; })")
    assert all(abs(c["y"] + c["h"] - 1 - b) <= 1 for c, b in zip(cards, feet)), "each foot ends on its card's bottom edge (inside the 1px border)"
    assert len({round(c["y"] + c["h"]) for c in cards}) == 1, "and the three cards end on one line"


@pytest.mark.req("Trade finder", ac="on a desktop who is deep is a grid of one-team cards in the same columns")
def test_on_a_desktop_who_is_deep_is_a_grid_of_team_cards_in_the_same_columns(mount):
    f, errors = planted(mount, size=(1280, 900))
    deep, frame = f.deep_boxes(), f.frame_box()
    assert len(deep) == 4 and across(deep) == 3, "four teams in three columns: 3 then 1"
    assert round(deep[0]["x"]) == round(frame["x"]) and max(round(d["x"] + d["w"]) for d in deep) == round(frame["x"] + frame["w"])
    assert all(d["w"] <= 560 for d in deep), "a team's name and his number stay within 560px"
    assert all(len({round(d["h"]) for d in r}) == 1 for r in rows(deep)), "a row's cards share one height"
    assert f.page.evaluate("getComputedStyle(document.querySelector('[data-testid=finder-deep] ol')).borderTopWidth") == "0px", "no card around the cards"
    assert errors == []


@pytest.mark.req("Trade finder", ac="a team's name and its number share one line, clear of the card's top edge")
@pytest.mark.parametrize("size", [(360, 740), (1280, 900)], ids=["phone", "desktop"])
def test_who_is_deep_puts_the_name_level_with_its_number_and_off_the_top_edge(mount, size):
    # 2026-10-06, David's screenshot: the name hugged the card's top edge and the number sat lower than it.
    f, _ = planted(mount, size=size)
    row = f.page.get_by_test_id("finder-deeprow").first
    box = lambda sel: row.locator(sel).evaluate("e => { const r = e.getBoundingClientRect(); return [r.top, r.bottom]; }")
    top, _ = row.evaluate("e => { const r = e.getBoundingClientRect(); return [r.top, r.bottom]; }")
    name, val = box("[data-testid=finder-deepname] b"), box("[data-testid=finder-deepval]")
    assert abs((name[0] + name[1]) / 2 - (val[0] + val[1]) / 2) <= 2, f"{size[0]}px: the name and its number on one line"
    assert name[0] - top >= 10, f"{size[0]}px: the name sits clear of the card's top edge"


@pytest.mark.req("Trade finder", ac="the chips are one row, kept to a column's measure")
@pytest.mark.parametrize("size", [(360, 740), (1280, 900)], ids=["phone", "desktop"])
def test_the_chip_row_stays_one_row_at_every_width(mount, size):
    f, _ = planted(mount, size=size)
    chips = f.page.get_by_test_id("finder-chip").evaluate_all("bs => bs.map(b => { const r = b.getBoundingClientRect(); return [r.top, r.width]; })")
    assert len({round(t) for t, _ in chips}) == 1, f"{size[0]}px: four chips on one row"
    assert f.chips_box()["w"] <= 560 + 1


@pytest.mark.req("Trade finder", ac="the filtered state's offers are cards in columns too; an empty state spans the frame")
def test_the_filtered_state_and_the_empty_state_fill_the_desktop_frame(mount):
    league = copy.deepcopy(LEAGUE)
    league["teams"].append(team("espn-epsilon", "Epsilon", {"QB": 10.0, "RB": 10.0, "WR": 10.0, "TE": 1.0}, [], 0, 4))
    f, errors = planted(mount, size=(1280, 900), league=league)
    f.open_partner("Alpha")
    assert across(f.card_boxes()) == 2, "Alpha's two offers sit side by side"
    f.all_positions()
    f.open_partner("Epsilon")                                          # nobody offers anything with him
    empty, frame = f.empty_box(), f.frame_box()
    assert (round(empty["x"]), round(empty["w"])) == (round(frame["x"]), round(frame["w"])), "the dashed line runs the frame, as Teams' empty block does"
    assert f.fits() and errors == []


@pytest.mark.req("Trade finder", ac="at 1440px the cards are still in columns of at most 560px and nothing scrolls sideways")
def test_a_wider_desktop_widens_three_offers_to_the_frame_and_never_past_560(mount):
    f, errors = planted(mount, size=(1280, 900))                       # the page's own context, resized, so no new one opens
    try:
        f.page.set_viewport_size({"width": 1440, "height": 900})
        cards, frame = f.card_boxes(), f.frame_box()
        assert across(cards) == 3 and all(c["w"] <= 560 for c in cards)
        assert round(cards[-1]["x"] + cards[-1]["w"]) == round(frame["x"] + frame["w"]), "three offers still run the frame's width, not a fourth column's gap"
        assert f.fits() and errors == []
        f.page.set_viewport_size({"width": 900, "height": 900})        # a small laptop or a tablet: two columns, 3 + 2 becomes 2 + 1
        cards = f.card_boxes()
        assert across(cards) == 2 and f.fits(), "three columns would be under 300px each"
        assert across(f.deep_boxes()) == 2
    finally:
        f.page.set_viewport_size({"width": 1280, "height": 900})


@pytest.mark.req("Trade finder", ac="on a desktop the edit page's tray puts the gain at the left and the buttons in a pair at the right")
def test_on_a_desktop_the_edit_trays_buttons_sit_beside_the_gain_not_a_screen_away(mount):
    page, errors = finder(mount, "espn")                               # the fixture's own offers, which pass the guard
    f = FinderPage(page)
    f.wait_offers()
    try:
        page.set_viewport_size({"width": 1280, "height": 900})
        f.open_edit(0)
        b = f.edit_boxes()
        assert round(b["tray"]["x"]) == round(b["package"]["x"]) and round(b["tray"]["w"]) == round(b["package"]["w"]), "the tray runs the package's width"
        assert b["acts"]["w"] <= 420 + 1 and round(b["acts"]["x"] + b["acts"]["w"]) <= round(b["tray"]["x"] + b["tray"]["w"]), "the pair is 420px at the tray's right end"
        assert b["gain"]["y"] < b["acts"]["y"] + b["acts"]["h"] and b["acts"]["y"] < b["gain"]["y"] + b["gain"]["h"] + 40, "on the gain's rows, not under them"
        assert b["tray"]["h"] <= 120, "one band, not a stack of three"
        assert f.fits() and errors == []
    finally:
        page.set_viewport_size({"width": 360, "height": 740})


@pytest.mark.req("Trade finder", ac="with no team the picker's three leagues fill the desktop frame in the cards' three columns")
def test_with_no_team_the_pickers_leagues_sit_in_three_columns_on_a_desktop(mount):
    page, errors = finder(mount, None)
    f = FinderPage(page)
    try:
        page.set_viewport_size({"width": 1280, "height": 900})
        leagues, frame = f.picker_boxes(), f.frame_box()
        assert len(leagues) == 3 and across(leagues) == 3, "the Madden Curse, AYO and the ESPN league side by side"
        assert round(leagues[0]["x"]) == round(frame["x"]) and max(round(b["x"] + b["w"]) for b in leagues) == round(frame["x"] + frame["w"])
        assert f.fits() and errors == []
        page.set_viewport_size({"width": 360, "height": 740})
        assert across(f.picker_boxes()) == 1, "a phone stacks them"
    finally:
        page.set_viewport_size({"width": 360, "height": 740})


@pytest.mark.req("Trade finder", ac="a phone keeps one column of offers and of teams")
def test_a_phone_keeps_one_column_of_cards_and_of_teams(mount):
    f, _ = planted(mount, size=(360, 740))
    two_columns = [boxes for boxes in (f.card_boxes(), f.deep_boxes())
                   if not (across(boxes) == 1 and all(round(2 * b["x"] + b["w"]) == 360 for b in boxes))]
    assert two_columns == [], "one column, the screen less one gutter a side"
    assert f.page.evaluate("getComputedStyle(document.querySelector('[data-testid=finder-deep] ol')).borderTopWidth") == "1px", "the list is one card on a phone"




# ---- journeys: across views ---------------------------------------------------------------------------------------

@pytest.mark.render
@pytest.mark.journey
def test_trades_with_them_on_a_teams_card_opens_the_finder_on_that_team_and_back_returns(browser, page_file):
    from test_render import open_at
    ctx, page, errors = open_at(browser, page_file, (360, 800), "#teams", init=(
        'try { localStorage.setItem("tw-team", "espn"); } catch (e) {}', serve(FIXTURE)))
    page.wait_for_selector("[data-lbtrade='espn-run-it-back']")
    assert page.locator("[data-lbtrade]").count() == 1, "only the other team's card has the link; the reader's own says Your team"
    page.locator("[data-lbtrade='espn-run-it-back']").click()
    page.wait_for_selector("[data-testid=finder-with]")
    assert page.evaluate("location.hash") == "#trades"
    assert page.get_by_test_id("finder-with").inner_text() == "Trades with Run It Back"
    page.wait_for_selector("[data-testid=finder-card]")
    assert len(page.get_by_test_id("finder-card").all()) == 3
    page.go_back()
    page.wait_for_selector(".lb-grid")
    assert page.evaluate("location.hash") == "#teams"
    ctx.close()
    assert errors == []


@pytest.mark.render
@pytest.mark.journey
def test_a_trades_link_opens_the_finder_for_every_league_and_the_history_is_under_records(browser, page_file):
    from test_render import open_at
    ctx, page, errors = open_at(browser, page_file, (360, 800), "#trades", init=(
        'try { localStorage.setItem("tw-team", "espn"); } catch (e) {}', serve(FIXTURE)))
    page.wait_for_selector("[data-testid=finder-chip]")
    assert page.locator(".mode-sub[aria-pressed='true']").inner_text().lower() == "trades"
    assert page.locator(".mode-sub[data-leaf='records']").count() == 0, "ESPN has no record book, so no Records and no history"
    page.evaluate("pickTeam('yahoo')")                                  # the Madden Curse: a record book, so Records
    page.wait_for_selector(".mode-sub[data-leaf='records']")
    page.locator(".mode-sub[data-leaf='records']").click()
    page.wait_for_selector("#view .rc")
    ctx.close()
    assert errors == []
