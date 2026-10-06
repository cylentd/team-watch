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

MEDIAN = {"QB": 18.0, "RB": 22.0, "WR": 20.0, "TE": 7.0, "FLX": 8.0}
RULES = {"top": 3, "per_pos": 5, "per_partner_pos": 2, "max_out": 3, "max_in": 2, "min_gain": 1.0, "max_losses": 1}


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
    return {"partner": partner, "send": send, "get": get, "gain": gain, "drop": [], "ir_moves": [], "their": {"ir_moves": [], "drop": []}}


OFFERS = [
    offer("Alpha", [p("Wally Smith", "WR")], [p("Rob Alpha", "RB")], 6.1),
    offer("Beta", [p("Ray Jones", "RB")], [p("Wes Beta", "WR")], 5.2),
    offer("Gamma", [p("Quinn Day", "QB")], [p("Rex Gamma", "RB"), p("Tom Gamma", "TE")], 4.8),
    offer("Alpha", [p("Ted Fox", "TE")], [p("Quinn Alpha", "QB")], 3.0),
    offer("Gamma", [p("Walt Hill", "WR")], [p("Wil Gamma", "WR")], 2.2),
    offer("Delta", [p("Will Ames", "WR")], [p("Rudy Delta", "RB")], 1.2),
]
BODY = {"updated": "2026-10-05T14:07", "season": 2026, "rules": RULES, "leagues": {"espn": {"week": 4, "teams": {"Me Team": OFFERS}}}}


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
        ("Alpha", "+6.1 pts a week for you"), ("Gamma", "+4.8 pts a week for you"), ("Delta", "+1.2 pts a week for you")], "RB: three of the six"
    f.pick("WR")
    assert [(c["partner"], c["gain"]) for c in f.cards()] == [("Beta", "+5.2 pts a week for you"), ("Gamma", "+2.2 pts a week for you")]
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
    assert first["gain"] == "+6.1 pts a week for you" and first["ir"] is None and first["drop"] is None


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
    assert [(c["partner"], c["gain"]) for c in f.cards()] == [("Alpha", "+6.1 pts a week for you"), ("Alpha", "+3.0 pts a week for you")], "every offer with him, whatever the position"
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
    assert f.need_text() == "A trade needs your team. Pick yours."
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
    assert page.locator(".tb-skel").count() == 3 and page.locator(".tb-line").inner_text() == "Finding offers"
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
    assert "Offers did not load" in page.get_by_test_id("finder-error").inner_text() and f.cards() == []
    assert f.deep(), "who's deep needs no file"
    page.evaluate("window.__tb = 'ok'")
    page.locator("[data-tbretry]").click()
    page.wait_for_selector("[data-testid=finder-card], [data-testid=finder-empty]")
    assert page.evaluate("__tbFetches") == 2
    assert errors == [], "a failed fetch is a state, not an exception"


# ---- copy offer ----------------------------------------------------------------------------------------------------

@pytest.mark.req("Trade finder", ac="Copy offer puts a message of true season averages on the clipboard")
def test_copy_offer_puts_a_message_of_true_season_averages_on_the_clipboard(mount):
    page, errors = finder(mount, "espn")
    f = FinderPage(page)
    f.wait_offers()
    f.open_partner("Run It Back")
    for i, want in enumerate((
            "Trade? I send Higgins (14.4 a game), Purdy (28.8), Gordon II (10.2) for Smith-Njigba (25.3) and Brown (11.4)."
            " M. Mariota can go to your IR slot, so you don't cut anyone.",
            "Trade? I send Purdy (28.8 a game), Raymond (9.4), Gordon II (10.2) for Smith-Njigba (25.3)."
            " M. Mariota can go to your IR slot. You'd only need to cut J. Hill.",
            "Trade? I send Purdy (28.8 a game) for Brown (11.4) and Watson (16.5).")):     # Watson is Hot, but the reader gets him
        page.locator(f"[data-tbcopy='{i}']").click()
        page.wait_for_function(f"document.querySelector(\"[data-tbcopy='{i}']\").textContent === 'Copied'")
        assert page.evaluate("navigator.clipboard.readText()") == want
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
    assert page.locator(".tb-box").input_value() == ("Trade? I send Purdy (28.8 a game), Raymond (9.4), Gordon II (10.2) for Smith-Njigba (25.3)."
                                                     " M. Mariota can go to your IR slot. You'd only need to cut J. Hill.")
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
