"""League > Trades, the finder's edit mode (2026-10-05; the finder since 2026-10-06), what the page draws and does: the "To IR"
and "You drop" lines on an offer, the chips, the edit state (Edit on a card, Make your own under the list), the message Copy
offer puts on the clipboard, and the guard's outcome (Edit gone, the offers still there). The scorer, the room rule, the
strings they build and the guard's own checks are plain functions of data and live in test_js_trade_score.py, in Node.
Each test mounts the Trades view alone (tests/component.py); `builder(page, key)` filters the finder to the team `key` from
Who's deep, so the cards are every offer with him, as the old per-partner page showed them.

The fixture's ESPN league began as a cut of the file ff-jarvis's real writer made (branch trade-edit, 29e54f2): Purdy Big
in Japan and TeamMinh, TeamMinh shown as the page fixture's "Run It Back". Its AYO league is hand-made. The drop rule's
fields (lineup.ir, keep, ir_ok, protect, ir_moves; spec drop-rule-spec, 2026-10-05) and option B's (last2, chips, their;
spec option-b-spec) are hand-made too, derived by the rule: IR moves first, then the lowest `keep`. Change a roster and
the offers' gains, moves, drops and `their` have to be re-derived. The page is driven in Chromium with the fetch
replaced, as test_trade_offers.py does."""
import copy
import json

import pytest

import trade_offers
from conftest import FIXTURES
from component import mount  # noqa: E402,F401  (the fixture)
from pages.finder import COPY_REFUSED, FIXTURE, builder, finder, serve  # noqa: E402

RUN = "espn-run-it-back"
ESPN = FIXTURE["leagues"]["espn"]
PROJ = {p["name"]: p["proj"] for p in ESPN["values"]["Purdy Big in Japan"]}


def open_edit(page, which=0):
    page.wait_for_selector(".tb-card .tb-gain")
    page.locator(f"[data-tbedit='{which}']").click()
    page.wait_for_selector(".tb-body.tb-ed .tb-edfoot")


def gain(page):
    return page.locator(".tb-edfoot .tb-gain").inner_text()


def pick(page, name):
    page.locator(f".tb-r[data-tbpick='{name}']").click()


# ---- the scorer, the room rule, the lines as strings and the guard's own checks are in test_js_trade_score.py (Node) ----

REAL = json.loads((FIXTURES / "trade_offers_ffjarvis.json").read_text(encoding="utf-8"))


def test_the_producers_own_file_passes_the_contract_with_the_drop_rule_required(monkeypatch):
    monkeypatch.setattr(trade_offers, "DROP_RULE_REQUIRED", True)
    monkeypatch.setattr(trade_offers, "OPTION_B_REQUIRED", False)   # this file predates option B; its own test is below
    assert trade_offers.problems(REAL) == []


def test_the_producers_option_b_file_passes_the_contract_with_option_b_required(monkeypatch):
    """ff-jarvis option-b (b23bf06): last2 and chips on every player, their on every offer. What flipping the flag will enforce."""
    monkeypatch.setattr(trade_offers, "OPTION_B_REQUIRED", True)
    doc = json.loads((FIXTURES / "trade_offers_ffjarvis_optionb.json").read_text(encoding="utf-8"))
    assert trade_offers.problems(doc) == []


# ---- the drop line on an offer ------------------------------------------------------------------------------

@pytest.mark.render
def test_an_offer_that_drops_a_player_says_so_in_one_line_and_the_others_say_nothing(mount):
    page, errors = finder(mount, "espn")
    builder(page, RUN)
    page.wait_for_selector(".tb-card .tb-gain")
    cards = page.locator(".tb-card")
    assert cards.count() == 3
    assert [cards.nth(i).locator(".tb-drop").count() for i in range(3)] == [0, 0, 1]
    line = cards.nth(2).locator(".tb-drop")
    assert line.inner_text() == "You drop: O. Gordon II"
    assert line.evaluate("e => getComputedStyle(e).color") != "rgb(255, 176, 32)", "quiet, never amber"
    assert "roster" not in cards.nth(2).inner_text().lower(), "nothing about the partner's room"
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page, _ = finder(mount, RUN)
    builder(page, "espn")
    page.wait_for_selector(".tb-card .tb-gain")
    assert page.locator(".tb-drop").count() == 0, "his injured QB goes to IR, so there is no drop"
    assert page.locator(".tb-ir").all_inner_texts() == ["To IR: M. Mariota"] * 5, "the other direction: his own IR move"
    assert [page.locator(".tb-card").nth(i).locator(".tb-ir").count() for i in range(6)] == [0, 1, 1, 1, 1, 1], "six offers with Purdy, the best first"
    assert page.locator(".tb-ir").first.evaluate("e => getComputedStyle(e).color") != "rgb(255, 176, 32)", "quiet, never amber"
    assert errors == []


# ---- the chips (option B) ------------------------------------------------------------------------------------

TOKEN = "(v => { const e = document.createElement('i'); e.style.color = `var(${v})`; document.body.append(e); const c = getComputedStyle(e).color; e.remove(); return c; })"


@pytest.mark.render
def test_chips_tag_players_on_the_cards_and_both_rosters_in_the_tokens_colours_and_cost_no_room(mount):
    page, errors = finder(mount, "espn")
    builder(page, RUN)
    page.wait_for_selector(".tb-card .tb-gain")
    cards = page.locator(".tb-card")
    assert cards.nth(0).locator(".tb-chip").count() == 0, "plain players carry none"
    assert cards.nth(2).locator(".tb-chip").all_inner_texts() == ["Hot", "Early pick"], "Watson: Hot and an early pick"
    assert cards.nth(1).locator(".tb-chip").all_inner_texts() == ["Cold"], "Raymond: Cold"
    color = lambda loc: loc.evaluate("e => getComputedStyle(e).color")   # noqa: E731
    assert color(cards.nth(2).locator(".tb-chip.hot")) == page.evaluate(TOKEN + "('--heat')")
    assert color(cards.nth(1).locator(".tb-chip.cold")) == page.evaluate(TOKEN + "('--sky')")
    early = cards.nth(2).locator(".tb-chip.early")
    assert color(early) not in (page.evaluate(TOKEN + "('--heat')"), page.evaluate(TOKEN + "('--sky')")), "neutral"
    row = cards.nth(2).locator(".tb-p", has_text="C. Watson")
    assert row.locator(".tb-n").evaluate("e => e.getBoundingClientRect().width") >= 40, "the name keeps room"
    assert row.evaluate("e => e.querySelector('.tb-tags').getBoundingClientRect().top >= e.querySelector('.tb-n').getBoundingClientRect().bottom - 1"), "chips under the name"
    assert row.evaluate("e => e.querySelector('.tb-tags').getBoundingClientRect().right <= e.getBoundingClientRect().right"), "inside the column"
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    open_edit(page, 2)
    assert page.locator(".tb-pkg .tb-chip").count() == 0, "the package keeps its rows one line tall; the rosters under it carry the chips"
    watson = page.locator(".tb-r[data-tbpick='Christian Watson']")
    assert watson.locator(".tb-chip").all_inner_texts() == ["Hot", "Early pick"], "the rosters wear them too"
    mason = page.locator(".tb-r[data-tbpick='Jordan Mason']")
    assert mason.locator(".tb-inj").count() == 1 and mason.locator(".tb-chip").all_inner_texts() == ["Early pick"], "the status pill and a chip share a row"
    assert page.locator(".tb-list").nth(0).locator(".tb-chip.hot").count() == 0
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert page.evaluate("[...document.querySelectorAll('.tb-r .tb-n, .tb-pkg .tb-n')].every(e => e.getBoundingClientRect().width >= 40)")
    assert errors == []


# ---- the edit state ----------------------------------------------------------------------------------------

@pytest.mark.render
def test_edit_opens_on_the_offer_it_started_from_and_back_returns_to_the_offers(mount):
    page, errors = finder(mount, "espn")
    builder(page, RUN)
    open_edit(page, 0)                                           # Higgins, Purdy, Gordon for Smith-Njigba and Brown
    cols = page.locator(".tb-pkg .tb-col")
    assert cols.nth(0).locator(".tb-h").inner_text() == "YOU SEND" and cols.nth(1).locator(".tb-h").inner_text() == "YOU GET"
    assert [r.replace("\n", " ") for r in cols.nth(0).locator(".tb-p").all_inner_texts()] == ["WR T. Higgins Q", "QB B. Purdy", "RB O. Gordon II"]
    assert [r.replace("\n", " ") for r in cols.nth(1).locator(".tb-p").all_inner_texts()] == ["WR J. Smith-Njigba", "RB C. Brown"]
    assert gain(page) == "+8.5 pts a week for you"
    assert page.locator(".tb-edfoot .tb-gain b").evaluate("e => getComputedStyle(e).color") == "rgb(55, 224, 139)"
    assert page.locator(".tb-lists h2").all_inner_texts() == ["YOUR ROSTER", "RUN IT BACK ROSTER"]
    assert page.locator(".lbp-back").inner_text() == "Offers", "the edit state has its own back step"
    mine, theirs = page.locator(".tb-list").nth(0), page.locator(".tb-list").nth(1)
    assert mine.locator(".tb-r").count() == 15 and theirs.locator(".tb-r").count() == 16
    assert mine.locator(".tb-r").first.inner_text().replace("\n", " ").startswith("QB "), "positions in order, QB first"
    purdy = mine.locator(".tb-r", has_text="B. Purdy").inner_text().replace("\n", " ")
    assert purdy == f"QB B. Purdy {PROJ['Brock Purdy']:.1f}", "position, initials, projection to one decimal"
    assert mine.locator(".tb-r").last.inner_text().replace("\n", " ").startswith("RB J. Mason IR"), "an IR player is last and wears the pill"
    assert mine.locator(".tb-r", has_text="T. Higgins").locator(".tb-inj").inner_text() == "Q"
    assert theirs.locator(".tb-r", has_text="A. Mitchell").locator(".tb-inj").inner_text() in ("O", "IR")
    assert page.locator(".tb-r[aria-pressed='true']").count() == 5, "the offer's five players read as picked"
    page.go_back()
    page.wait_for_selector(".tb-card .tb-gain")
    assert page.locator(".tb-body.tb-ed").count() == 0
    assert page.get_by_test_id("finder-with").inner_text() == "Trades with Run It Back", "Back closed the edit page only: the finder is still filtered to him"
    assert page.evaluate("document.activeElement.dataset.tbedit") == "0", "focus returns to the Edit button"
    open_edit(page, 0)
    page.locator(".lbp-back").click()                                         # the link is the same step as Back
    page.wait_for_selector(".tb-card .tb-gain")
    assert page.evaluate("history.state") is None, "and it took the edit page's history entry back"
    assert page.get_by_test_id("finder-with").inner_text() == "Trades with Run It Back"
    assert errors == []


@pytest.mark.render
def test_a_tap_on_a_player_puts_him_in_or_out_and_the_gain_follows(mount):
    page, errors = finder(mount, "espn")
    builder(page, RUN)
    open_edit(page, 2)                                                       # Purdy for Brown and Watson, +5.5, drops Gordon
    assert gain(page) == "+5.5 pts a week for you"
    pick(page, "Christian Watson")                                           # out of the package: one for one
    assert page.locator(".tb-r[data-tbpick='Christian Watson']").get_attribute("aria-pressed") == "false"
    assert gain(page) == "+3.5 pts a week for you"
    assert page.locator(".tb-pkg .tb-col").nth(1).locator(".tb-p").count() == 1
    pick(page, "Brock Purdy")
    pick(page, "Chase Brown")
    assert page.locator(".tb-pkg .tb-hint").count() == 2 and gain(page) == "— pts a week for you"
    pick(page, "Tee Higgins")                                                # Higgins for nothing: red
    assert gain(page) == "−4.2 pts a week for you"
    assert page.locator(".tb-edfoot .tb-gain b").evaluate("e => getComputedStyle(e).color") == "rgb(255, 90, 82)"
    page.locator(".tb-pkg [data-tbpick='Tee Higgins']").click()              # taken out from the package itself
    assert page.locator(".tb-r[data-tbpick='Tee Higgins']").get_attribute("aria-pressed") == "false"
    assert page.evaluate("document.activeElement.dataset.tbpick") == "Tee Higgins", "focus lands on his row below"
    assert errors == []


@pytest.mark.render
def test_an_empty_package_is_a_dash_and_reset_goes_back_to_the_offer_it_started_from(mount):
    page, _ = finder(mount, "espn")
    builder(page, RUN)
    open_edit(page, 1)
    assert page.locator("[data-tbreset]").is_disabled(), "nothing to reset yet"
    for n in ("Brock Purdy", "Kalif Raymond", "Ollie Gordon II", "Jaxon Smith-Njigba"):
        page.locator(f".tb-pkg [data-tbpick='{n}']").click()
    assert gain(page) == "— pts a week for you"
    assert page.locator(".tb-edfoot .tb-gain b").evaluate("e => getComputedStyle(e).color") != "rgb(55, 224, 139)"
    assert page.locator("[data-tbedcopy]").is_disabled(), "an empty package has nothing to copy"
    pick(page, "Tee Higgins")
    assert page.locator("[data-tbedcopy]").is_disabled(), "one side alone is not an offer to copy"
    page.locator("[data-tbreset]").click()
    assert gain(page) == "+7.7 pts a week for you"
    assert page.locator(".tb-r[aria-pressed='true']").count() == 4 and page.locator("[data-tbreset]").is_disabled()


@pytest.mark.render
def test_the_drop_line_shows_when_the_package_puts_the_reader_over_the_cap_and_goes_when_it_does_not(mount):
    page, _ = finder(mount, "espn")
    builder(page, RUN)
    open_edit(page, 2)
    assert page.locator(".tb-edrop").inner_text() == "You drop: O. Gordon II"
    pick(page, "Tee Higgins")                                                # two out, two in: nobody to drop
    assert page.locator(".tb-edrop").inner_text() == ""
    assert page.locator(".tb-edrop").evaluate("e => e.offsetHeight") >= 18, "the row keeps its height"
    pick(page, "Tee Higgins")
    assert page.locator(".tb-edrop").inner_text() == "You drop: O. Gordon II"
    pick(page, "Brock Purdy")                                                # two in, nobody out: two drop
    assert page.locator(".tb-edrop").inner_text() == "You drop: O. Gordon II, K. Raymond"
    assert page.locator(".tb-eir").inner_text() == ""


@pytest.mark.render
def test_the_to_ir_line_sits_above_the_drop_line_and_the_foot_keeps_its_size(mount):
    page, _ = finder(mount, "espn")
    builder(page, RUN)
    open_edit(page, 2)
    foot = "document.querySelector('.tb-edfoot').getBoundingClientRect().height"
    before = page.evaluate(foot)
    assert page.locator(".tb-eir").inner_text() == "" and page.locator(".tb-edrop").inner_text() == "You drop: O. Gordon II"
    pick(page, "Marcus Mariota")          # Out, not on IR: two over (16 + 2 other - 16), one IR slot free, so one move and one drop
    assert page.locator(".tb-eir").inner_text() == "To IR: M. Mariota"
    assert page.locator(".tb-edrop").inner_text() == "You drop: O. Gordon II"
    assert page.evaluate("(() => { const a = document.querySelector('.tb-eir').getBoundingClientRect(), b = document.querySelector('.tb-edrop').getBoundingClientRect(); return a.bottom <= b.top + 1 && a.left === b.left; })()")
    assert page.evaluate(foot) == before, "the two rows are always there, so nothing shifts"
    assert page.locator(".tb-eir").evaluate("e => getComputedStyle(e).color") != "rgb(255, 176, 32)"


@pytest.mark.render
def test_a_package_the_cap_cannot_take_says_so_and_cannot_be_copied(mount):
    page, _ = finder(mount, "espn")
    builder(page, RUN)
    page.wait_for_selector(".tb-card .tb-gain")
    page.locator("[data-tbown]").click()
    page.wait_for_selector(".tb-body.tb-ed")
    rows = page.locator(".tb-list").nth(1).locator(".tb-r")
    for i in range(rows.count()):
        rows.nth(i).click()
    assert gain(page) == "— pts a week for you"
    assert page.locator(".tb-edrop").inner_text() == "Over the roster limit, no one to drop"
    assert page.locator("[data-tbedcopy]").is_disabled()


@pytest.mark.render
def test_copy_offer_in_edit_is_the_same_message_as_a_cards(mount):
    page, errors = finder(mount, "espn")
    builder(page, RUN)
    open_edit(page, 0)
    page.locator("[data-tbedcopy]").click()
    page.wait_for_function("document.querySelector('[data-tbedcopy]').textContent === 'Copied'")
    assert page.evaluate("navigator.clipboard.readText()") == (
        "Trade? I send Higgins (14.4 a game), Purdy (28.8), Gordon II (10.2) for Smith-Njigba (25.3) and Brown (11.4)."
        " M. Mariota can go to your IR slot, so you don't cut anyone.")
    pick(page, "Ollie Gordon II")                  # three for two becomes two for two: his roster fits, so the sentence goes
    page.locator("[data-tbedcopy]").click()
    page.wait_for_function("document.querySelector('[data-tbedcopy]').textContent === 'Copied'")
    assert page.evaluate("navigator.clipboard.readText()") == (
        "Trade? I send Higgins (14.4 a game) and Purdy (28.8) for Smith-Njigba (25.3) and Brown (11.4).")
    assert errors == []


def tail(page):
    """Press Copy offer in the edit state and return what the message says after Watson, the last name in it: the partner's room."""
    page.locator("[data-tbedcopy]").click()
    page.wait_for_function("document.querySelector('[data-tbedcopy]').textContent === 'Copied'")
    return page.evaluate("navigator.clipboard.readText()").split("Watson (16.5).")[1].strip()


@pytest.mark.render
def test_copy_offer_in_edit_works_out_the_partners_room_for_the_package_it_holds(mount):
    page, errors = finder(mount, "espn")
    builder(page, RUN)
    open_edit(page, 2)                                           # Purdy for Brown and Watson (Hot)
    page.locator("[data-tbedcopy]").click()
    page.wait_for_function("document.querySelector('[data-tbedcopy]').textContent === 'Copied'")
    assert page.evaluate("navigator.clipboard.readText()") == (
        "Trade? I send Purdy (28.8 a game) for Brown (11.4) and Watson (16.5).")      # Watson is Hot but the reader gets him: season average
    pick(page, "Kalif Raymond")                                  # two for two: nobody to make room for
    assert tail(page) == ""
    pick(page, "Tee Higgins")                                    # three for two: his IR slot takes Mariota, nobody is cut
    assert tail(page) == "M. Mariota can go to your IR slot, so you don't cut anyone."
    pick(page, "Ollie Gordon II")                                # four for two: one more than the slot can take
    assert tail(page) == "M. Mariota can go to your IR slot. You'd only need to cut J. Hill."
    page.locator("[data-tbedcopy]").click()
    page.wait_for_function("document.querySelector('[data-tbedcopy]').textContent === 'Copied'")
    assert page.evaluate("navigator.clipboard.readText()") == (
        "Trade? I send Purdy (28.8 a game), Raymond (9.4), Higgins (14.4), Gordon II (10.2) for Brown (11.4) and Watson (16.5)."
        " M. Mariota can go to your IR slot. You'd only need to cut J. Hill.")
    assert errors == []


@pytest.mark.render
def test_a_refused_clipboard_in_edit_shows_the_text_in_a_box(mount):
    page, _ = finder(mount, "espn")
    page.evaluate(f"() => {{ {COPY_REFUSED} }}")
    builder(page, RUN)
    open_edit(page, 1)
    page.locator("[data-tbedcopy]").click()
    page.wait_for_selector(".tb-edfoot .tb-box")
    assert page.locator(".tb-box").input_value() == ("Trade? I send Purdy (28.8 a game), Raymond (9.4), Gordon II (10.2) for Smith-Njigba (25.3)."
                                                     " M. Mariota can go to your IR slot. You'd only need to cut J. Hill.")
    assert page.locator("[data-tbedcopy]").inner_text() == "Copy offer", "no false Copied"


@pytest.mark.render
def test_make_your_own_is_under_the_offers_and_in_the_empty_states_and_starts_empty(mount):
    page, errors = finder(mount, "espn-run-it-back")        # six offers with Purdy
    builder(page, "espn")
    page.wait_for_selector(".tb-card .tb-gain")
    assert page.locator("[data-tbown]").inner_text() == "Make your own offer"
    assert page.evaluate("(() => { const b = document.querySelector('[data-tbown]'), c = [...document.querySelectorAll('.tb-card')].pop();"
                         " return b.getBoundingClientRect().top >= c.getBoundingClientRect().bottom; })()"), "under the last offer"
    assert page.locator(".tb-card").count() == 6
    page.locator("[data-tbown]").click()
    page.wait_for_selector(".tb-body.tb-ed")
    assert page.locator(".tb-r[aria-pressed='true']").count() == 0
    assert page.locator(".tb-pkg .tb-hint").count() == 2
    assert page.locator("[data-tbpartner]").count() == 0, "the partner was chosen: nothing to pick"
    assert gain(page) == "— pts a week for you"
    assert page.locator("[data-tbreset]").is_disabled()
    pick(page, "Drake Maye")
    pick(page, "Brock Purdy")
    pick(page, "Dalton Schultz")
    assert gain(page) == "+1.1 pts a week for you", "the first fair offer, built by hand"
    assert page.locator(".tb-eir").inner_text() == "To IR: M. Mariota", "an injured player takes the free IR slot"
    assert page.locator(".tb-edrop").inner_text() == "", "so nobody is dropped"
    page.go_back()
    page.wait_for_selector("[data-tbown]")
    assert page.evaluate("document.activeElement.hasAttribute('data-tbown')")
    assert errors == []
    page, _ = finder(mount, "ayo-don-wick")                 # no offer at all with Taylor Made, who is his own league's other team
    builder(page, "ayo")
    page.wait_for_selector(".tb-empty")
    assert page.locator(".tb-empty").inner_text() == "No offers with Taylor Made for Sundays this week"
    assert page.locator("[data-tbown]").count() == 1
    page.locator("[data-tbown]").click()
    page.wait_for_selector(".tb-body.tb-ed")
    assert page.locator(".tb-list").count() == 2


@pytest.mark.render
def test_make_your_own_from_the_chips_opens_against_the_deepest_team_and_lets_the_reader_change_it(mount):
    """With no team filtered the button has no partner: it takes the deepest team at the pressed position, and the page
    carries a select to change it, which clears what the reader gets from the old one and keeps what he sends."""
    body = copy.deepcopy(FIXTURE)
    espn = body["leagues"]["espn"]
    espn["values"]["Third Team"] = copy.deepcopy(espn["values"]["Run It Back"])         # a third team to change to, on Run It Back's players
    page, errors = finder(mount, "espn", body=body)
    page.wait_for_selector("[data-tbown]")
    page.evaluate("""() => { const lg = LIVE_TEAMS.leagues.find(l => l.key === 'espn');
      lg.teams.push({key: 'espn-third', name: 'Third Team', w: 0, l: 4, t: 0, tot: 0, cols: {QB: 0, RB: 0, WR: 0, TE: 0, FLX: 0}, spare: [], lineup: [], bench: []});
      TF = {lg: null, me: null, pos: null, partner: null}; render(); }""")
    page.wait_for_selector("[data-tbown]")
    page.locator("[data-tbown]").click()
    page.wait_for_selector(".tb-body.tb-ed")
    assert page.locator("#tb-title").get_attribute("aria-label") == "You and Run It Back", "the deepest team: Third Team has nothing"
    sel = page.locator("[data-tbpartner]")
    assert sel.locator("option").all_inner_texts() == ["Run It Back", "Third Team"], "every other team in the league"
    pick(page, "Brock Purdy")                                          # his own: stays when the partner changes
    pick(page, "Chase Brown")                                          # Run It Back's: goes
    assert gain(page) != "— pts a week for you"
    sel.select_option(label="Third Team")
    page.wait_for_selector("#tb-title[aria-label='You and Third Team']")
    assert page.locator(".tb-pkg .tb-col").nth(0).locator(".tb-p").all_inner_texts() == ["QB\nB. Purdy"], "what he sends stays"
    assert page.locator(".tb-pkg .tb-col").nth(1).locator(".tb-hint").count() == 1, "what he gets from the old partner is out"
    assert page.locator(".tb-lists h2").all_inner_texts() == ["YOUR ROSTER", "THIRD TEAM ROSTER"]
    assert page.evaluate("document.activeElement.hasAttribute('data-tbpartner')"), "focus stays on the select"
    assert errors == []


@pytest.mark.render
def test_the_edit_state_keeps_its_parts_still_with_the_foot_on_the_bottom_edge_and_fits_both_screens(mount):
    for w, h in ((360, 740), (1280, 900)):
        page, _ = finder(mount, "espn", size=(w, h))
        builder(page, RUN)
        open_edit(page, 0)
        geo = "(() => { const g = s => document.querySelector(s).getBoundingClientRect(); return [g('.tb-pkg').top, g('.tb-pkg').height, g('.tb-edfoot').height, g('.tb-edfoot').bottom, g('.tb-lists').top]; })()"
        before = page.evaluate(geo)
        for name in ("George Kittle", "Tee Higgins", "Brock Purdy", "Jared Goff", "Chase Brown", "Drake Maye", "Juwan Johnson"):
            page.locator(f".tb-r[data-tbpick='{name}']").click()
        page.evaluate("window.scrollTo(0, 0)")
        assert page.evaluate(geo) == before, "the package, the foot and the rosters do not move or resize when the package changes"
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), "no sideways scroll"
        assert page.evaluate("document.documentElement.scrollHeight > innerHeight"), "the rosters scroll with the page"
        assert page.evaluate(f"document.querySelector('.tb-edfoot').getBoundingClientRect().bottom <= {h} - 8"), "the foot is a tray on the bottom edge"
        assert page.evaluate("[...document.querySelectorAll('.tb-r, .tb-pr, .tb-edfoot .tb-copy')].every(b => b.getBoundingClientRect().height >= 40)")
        assert page.evaluate("[...document.querySelectorAll('.tb-pkg ul, .tb-lists, .tb-edfoot')].every(e => e.scrollWidth <= e.clientWidth)")
        page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
        rest = page.evaluate("(() => { const r = [...document.querySelectorAll('.tb-r')].pop().getBoundingClientRect(), f = document.querySelector('.tb-edfoot').getBoundingClientRect(); return [f.top, r.bottom, innerHeight, scrollY, document.documentElement.scrollHeight]; })()")
        assert rest[0] >= rest[1] - 1, f"at the end the tray rests under the last row: {rest}"
        side = page.evaluate("(() => { const t = [...document.querySelectorAll('.tb-roster')].map(e => Math.round(e.getBoundingClientRect().top + scrollY)); return t[0] === t[1]; })()")
        assert side == (w >= 760), "the two rosters sit side by side on a desktop and stack on a phone"


# ---- the guard: Edit is hidden when the page cannot reproduce the file ----------------------------------------

def guarded(mount, body):
    """The finder on the fixture's page, then `body` swapped in for the file the page holds: the guard runs on it as it draws the
    cards (the finder is on Purdy's chips, so Who's deep names Run It Back and the cards are his offers)."""
    page, errors = finder(mount, "espn")
    page.wait_for_selector("[data-testid=finder-card]")
    warnings = []
    page.on("console", lambda m: warnings.append(m.text) if m.type == "warning" else None)
    page.evaluate("b => { TB_DATA = b; render(); }", body)
    builder(page, RUN)
    page.wait_for_selector(".tb-card .tb-gain")
    return page, errors, warnings


def assert_shut(page):
    assert page.locator(".tb-card").count() == 3, "the offers themselves still show"
    assert page.locator("[data-tbedit]").count() == 0 and page.locator("[data-tbown]").count() == 0
    assert page.locator("[data-tbcopy]").count() == 3, "Copy offer is untouched"


def purdy(doc):
    return doc["leagues"]["espn"]["teams"]["Purdy Big in Japan"]


@pytest.mark.render
def test_a_file_whose_gain_the_page_cannot_reproduce_shuts_edit_and_names_the_offer(mount):
    bad = copy.deepcopy(FIXTURE)
    purdy(bad)[1]["gain"] = 7.9                                               # the rule says 7.7
    page, errors, warnings = guarded(mount, bad)
    assert_shut(page)
    assert any("Edit is off, Purdy Big in Japan" in w and "offers[1]" in w for w in warnings), warnings
    page.locator("[data-tfall]").click()
    page.wait_for_selector("[data-testid=finder-chip]")
    builder(page, RUN)                                                        # a shut guard stays shut for the session
    page.wait_for_selector(".tb-card .tb-gain")
    assert page.locator("[data-tbedit]").count() == 0
    assert errors == []


def each_offer(doc):
    for lg in doc["leagues"].values():
        for offers in lg["teams"].values():
            yield from offers


@pytest.mark.render
def test_the_old_shape_with_no_lineup_values_other_or_drop_shows_offers_and_no_edit(mount):
    old = copy.deepcopy(FIXTURE)
    for lg in old["leagues"].values():
        for k in ("lineup", "values", "other"):
            lg.pop(k)
    for o in each_offer(old):
        o.pop("drop")
        o.pop("ir_moves")
    page, errors, warnings = guarded(mount, old)
    assert_shut(page)
    assert page.locator(".tb-drop").count() == 0 and page.locator(".tb-ir").count() == 0
    assert any("Edit is off" in w for w in warnings), warnings
    assert errors == [], "an old file is a state, not an exception"


@pytest.mark.render
def test_a_file_from_before_the_drop_rule_shows_its_drops_and_no_edit(mount):
    """Today's live file: lineup, values, other and drop, but no IR slots, keep, ir_ok, protect or ir_moves."""
    before = copy.deepcopy(FIXTURE)
    for lg in before["leagues"].values():
        lg["lineup"].pop("ir")
        for rows in lg["values"].values():
            for p in rows:
                for k in ("keep", "ir_ok", "protect"):
                    p.pop(k)
    for o in each_offer(before):
        o.pop("ir_moves")
    page, errors, warnings = guarded(mount, before)
    assert_shut(page)
    assert page.locator(".tb-drop").count() == 1, "the cards still say who is dropped, as the file has it"
    assert page.locator(".tb-ir").count() == 0
    assert any("predates the drop rule" in w for w in warnings), warnings
    assert errors == []


@pytest.mark.render
def test_a_file_from_before_option_b_shows_its_offers_with_no_chips_no_edit_and_the_old_pitch(mount):
    """The live file the day before ff-jarvis lands option B: no last2, chips or their."""
    before = copy.deepcopy(FIXTURE)
    for lg in before["leagues"].values():
        for rows in lg["values"].values():
            for p in rows:
                p.pop("last2"), p.pop("chips")
    for o in each_offer(before):
        o.pop("their")
        for side in ("send", "get", "drop", "ir_moves"):
            for p in o[side]:
                p.pop("last2"), p.pop("chips")
    page, errors, warnings = guarded(mount, before)
    assert_shut(page)
    assert page.locator(".tb-chip").count() == 0
    assert any("their" in w for w in warnings), warnings
    page.locator("[data-tbcopy='2']").click()
    page.wait_for_function("document.querySelector(\"[data-tbcopy='2']\").textContent === 'Copied'")
    assert page.evaluate("navigator.clipboard.readText()") == "Trade? I send Purdy (28.8 a game) for Brown (11.4) and Watson (16.5).", \
        "no last2, so Watson is quoted on his season average, and nothing about their room"
    assert errors == []


