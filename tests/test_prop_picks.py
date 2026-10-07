"""Prop picks on the page (2026-10-05, storyboards "Prop Picks" A and "Slips Board" A): the line sheet
outlines the model's side with its tier word under it, the Slips board shows a player's most confident
line, the matchup and teammate-out chips, and the tiers' record leads the board. The data wiring is in
tests/test_slip_reasons.py.

The fixture's slate, with ff-jarvis's tier on each priced line: Chase Brown RUSH Higher, Very confident;
Burrow PASS Lower, Confident; Purdy PASS Lower, Slight; St. Brown REC Higher, Slight; Kittle REC No pick;
Gibbs RUSH Lower, Very confident (the book moved that line, so the board hides it). The fixture's four
defences give Brown, Burrow and Kittle an easy matchup and Purdy a tough one; St. Brown has two teammates
out. The record is the real week 4 totals."""
import pytest

from test_render import open_page

pytestmark = pytest.mark.render

RESET = """() => { 'use strict';
  PROPS.splice(0, PROPS.length, ...JSON.parse(__PROPS));
  for (const k of Object.keys(LIVE_REASONS)) delete LIVE_REASONS[k];
  Object.assign(LIVE_REASONS, JSON.parse(__REASONS));
  LIVE_PREVIEW.games.splice(0, LIVE_PREVIEW.games.length, ...JSON.parse(__PV));
  Object.assign(LIVE_PROPS_RECORD, JSON.parse(__REC));
  SLIP.length = 0; SL_CHIP = {}; SL_FOCUS = null; SL_REC_OPEN = false; PV_OPEN = false; PV_I = null;
  PARLAY_BOOK = 'dk'; GAL_WIN = 'evening-mon'; SURFACE = 'parlay'; render(); }"""

# The fixture's preview games and its props slate are different games (tests/test_preview.py), so game 3
# becomes the slate's SEA @ SF.
AS_SEA_SF = "() => { const g = LIVE_PREVIEW.games[3]; g.away = 'SEA'; g.home = 'SF'; GAL_WIN = 'evening-sun'; render(); }"


@pytest.fixture(scope="module")
def shared(browser, page_file):
    ctx, pg, errors = open_page(browser, page_file, (360, 780))
    pg.evaluate("""() => { window.__PROPS = JSON.stringify(PROPS); window.__REASONS = JSON.stringify(LIVE_REASONS);
      window.__PV = JSON.stringify(LIVE_PREVIEW.games); window.__REC = JSON.stringify(LIVE_PROPS_RECORD); }""")
    assert errors == []
    yield pg, errors
    ctx.close()


@pytest.fixture
def page(shared):
    pg, errors = shared
    left, errors[:] = list(errors), []
    assert left == []
    pg.evaluate(RESET)
    yield pg
    assert errors == [], errors


def open_sheet(page, slug):
    page.evaluate(f"playerSheetOpen({slug!r})")
    return page.locator("#legsheet.on")


def close_sheet(page):
    page.keyboard.press("Escape")
    page.wait_for_function("LEG_SHEET === null")


def line(sheet, label):
    return sheet.locator(f".sl-ln:has(.sl-mk:has-text('{label}'))").first


def centre(loc):
    b = loc.bounding_box()
    return b["x"] + b["width"] / 2


def right(loc):
    b = loc.bounding_box()
    return b["x"] + b["width"]


def all_chips(page):
    page.locator("[data-slchip='all']").first.click()


def test_the_models_side_is_outlined_with_its_tier_under_it(page):
    """A slight pick: Higher outlined, "Slight" under it and centred on it; the fill is still the reader's."""
    sheet = open_sheet(page, "amonra-st-brown")
    rec = sheet.locator(".sl-ln.tiered")
    assert rec.count() == 1
    assert rec.locator(".sl-side.pick").all_inner_texts() == ["Higher"]
    assert rec.locator(".sl-conf").all_inner_texts() == ["Slight"] and rec.locator(".sl-conf.slight").count() == 1
    # "55% Slight" is wider than one side, so it spans both under the buttons, to their right edge (2026-10-05)
    assert rec.locator(".sl-tp .sl-pc").all_inner_texts() == ["55%"]
    assert abs(right(rec.locator(".sl-side.lower")) - right(rec.locator(".sl-tp"))) <= 1
    assert rec.locator(".sl-side[aria-pressed='true']").count() == 0
    rec.locator(".sl-side.higher").click()
    both = sheet.locator(".sl-ln.tiered .sl-side.higher")
    assert both.get_attribute("aria-pressed") == "true" and "pick" in both.get_attribute("class"), "filled and outlined"
    close_sheet(page)


def test_each_tier_has_its_word_and_its_side(page):
    got = {}
    for slug, label in (("chase-brown", "Rush yds"), ("joe-burrow", "Pass yds"), ("george-kittle", "Rec yds")):
        sheet = open_sheet(page, slug)
        ln = line(sheet, label)
        # a side Claude picked carries its "C" badge after the word (tests/test_claude_calls.py)
        got[slug] = (ln.locator(".sl-conf").inner_text(), ln.locator(".sl-conf").get_attribute("class").split()[-1],
                     [x.split("\n")[0] for x in ln.locator(".sl-side.pick").all_inner_texts()])
        close_sheet(page)
    assert got == {"chase-brown": ("Very confident", "very", ["Higher"]),
                   "joe-burrow": ("Confident", "confident", ["Lower"]),
                   "george-kittle": ("No pick", "none", [])}, "no pick: no outline"
    page.evaluate("document.getElementById('view').insertAdjacentHTML('beforeend', `<div id=probe>${PROPS.map((p, i) => p.n === 'George Kittle' && p.mkt === 'REC' ? slLineHTML(i) : '').join('')}</div>`)")
    unders = page.locator("#probe .sl-under").all_inner_texts()
    assert unders == ["", "No pick"], "No pick sits under Lower, the right-hand side"


def test_a_touchdown_says_its_chance_and_has_no_tier(page):
    sheet = open_sheet(page, "amonra-st-brown")
    td = line(sheet, "Anytime TD")
    assert td.locator(".sl-md").inner_text() == "28% to score"
    assert td.locator(".sl-conf, .sl-under, .pick").count() == 0 and "tiered" not in td.get_attribute("class").split()
    assert td.locator(".sl-side").all_inner_texts() == ["Yes"]
    assert "of 4" not in sheet.inner_text() and "model" not in sheet.inner_text()
    close_sheet(page)


def test_the_tier_is_the_one_ff_jarvis_sent_never_one_cut_from_the_chance(page):
    page.evaluate("""() => { const p = PROPS.find(p => p.n === 'Amon-Ra St. Brown' && p.mkt === 'REC');
      p.model = 99; p.tier = 'none'; render(); }""")
    sheet = open_sheet(page, "amonra-st-brown")
    assert sheet.locator(".sl-conf").all_inner_texts() == ["No pick"] and sheet.locator(".pick").count() == 0
    close_sheet(page)


def test_a_tier_word_says_it_failed_its_test_and_no_pick_does_not(page):
    """12.31 and 12.82: every tier hit under its stated chance. The tooltip says so (2026-10-06); "No pick" names no tier."""
    sheet = open_sheet(page, "amonra-st-brown")
    assert sheet.locator(".sl-conf").first.get_attribute("title").startswith("Failed test (12.31, 12.82)")
    close_sheet(page)
    page.evaluate("""() => { const p = PROPS.find(p => p.n === 'Amon-Ra St. Brown' && p.mkt === 'REC'); p.tier = 'none'; render(); }""")
    sheet = open_sheet(page, "amonra-st-brown")
    assert sheet.locator(".sl-conf").first.get_attribute("title") is None
    close_sheet(page)


def test_no_tier_from_the_producer_means_no_pick_drawn(page):
    page.evaluate("PROPS.forEach(p => { delete p.tier; delete p.side; for (const b of Object.values(p.books)) { delete b.tier; delete b.side; } }); render()")
    sheet = open_sheet(page, "amonra-st-brown")
    assert sheet.locator(".sl-side").count() == 3 and sheet.locator(".pick, .sl-conf, .sl-under, .tiered").count() == 0
    close_sheet(page)
    all_chips(page)
    assert page.locator(".sl-pick, .sl-conf").count() == 0
    assert page.locator(".sl-go").first.inner_text().endswith("lines")


def test_underdog_shows_the_tier_of_underdogs_own_line(page):
    """Underdog's line is its own row in the model: its side and tier come with it. Where Underdog has no
    tier for the number it shows, none is drawn rather than the other book's."""
    page.evaluate("""() => { const p = PROPS.find(p => p.n === 'Amon-Ra St. Brown' && p.mkt === 'REC');
      p.books.Underdog.line = 78.5; p.books.Underdog.side = 'lower'; p.books.Underdog.tier = 'confident';
      PARLAY_BOOK = 'underdog'; render(); }""")
    sheet = open_sheet(page, "amonra-st-brown")
    ln = line(sheet, "Rec yds")
    assert ln.locator(".sl-mk b").inner_text() == "78.5"
    assert ln.locator(".sl-side.pick").all_inner_texts() == ["Lower"] and ln.locator(".sl-conf").inner_text() == "Confident"
    close_sheet(page)
    page.evaluate("PROPS.find(p => p.n === 'Amon-Ra St. Brown' && p.mkt === 'REC').books.Underdog.tier = undefined; render()")
    sheet = open_sheet(page, "amonra-st-brown")
    assert line(sheet, "Rec yds").locator(".sl-conf, .pick").count() == 0, "Underdog's 78.5 has no tier, the row's 75.5 is not it"
    close_sheet(page)
    page.evaluate("PARLAY_BOOK = 'dk'; render()")
    sheet = open_sheet(page, "amonra-st-brown")
    assert line(sheet, "Rec yds").locator(".sl-conf").inner_text() == "Slight", "DraftKings: the row's own line"
    close_sheet(page)


def row(page, slug):
    return page.locator(f".sl-row[data-slplayer='{slug}']")


def test_a_row_is_work_bars_chips_and_the_best_line(page):
    """St. Brown: his three bars (targets 7, 9, 11) with all three numbers, none of them green (12.33: a rise in
    work is priced into the line), his snaps absent (no usage log), no chip for his two teammates out (12.55: the
    book prices it) and none for the matchup (GB is mid-table); the pick is his one priced yards line,
    outlined, its tier under it."""
    all_chips(page)
    r = row(page, "amonra-st-brown")
    assert r.locator(".sl-who b").inner_text() == "A. St. Brown" and r.locator(".sl-pos").inner_text() == "WR · DET"
    assert r.locator(".sl-use .sl-ul").first.inner_text() == "Targets"
    assert r.locator(".sl-spark em").all_inner_texts() == ["7", "9", "11"]
    assert r.locator(".sl-spark > span").evaluate_all("els => els.map(e => e.classList.contains('up'))") == [False, False, False]
    assert r.locator(".sl-f").count() == 0
    assert r.locator(".sl-pick").inner_text() == "Higher rec yds" and r.locator(".sl-r .sl-conf").inner_text() == "Slight"
    assert r.locator(".sl-go").inner_text() == "2 lines"
    assert r.locator(".sl-why, .sl-odds").count() == 0
    assert r.evaluate("e => e.tagName") == "BUTTON", "the whole row is one tap"
    assert abs(right(r.locator(".sl-pick")) - right(r.locator(".sl-r .sl-conf"))) <= 1, "the pick and its word share the right edge"


def test_no_bar_is_green_even_when_ff_jarvis_tags_the_work_as_rising(page):
    """12.33: rising work is in the line, so a `work_up` tag colours nothing (removed 2026-10-06)."""
    page.evaluate("LIVE_REASONS['amonra-st-brown'].tags = ['work_up']; render()")
    all_chips(page)
    assert row(page, "amonra-st-brown").locator(".sl-spark > span.up").count() == 0
    assert page.locator(".sl-spark > span.up").count() == 0


def test_a_teammate_out_draws_no_chip(page):
    """12.55: the book prices a teammate ruled out, and the fix made the error worse; the "{name} out" chip
    went (2026-10-06). The reason's `vacated` still arrives from ff-jarvis; nothing draws it."""
    page.evaluate("LIVE_REASONS['amonra-st-brown'].vacated = [{name: 'J. Reed', last: 'Reed', status: 'Out', work: 'tgt'}]; render()")
    all_chips(page)
    assert page.locator(".sl-f.out").count() == 0 and "Reed out" not in page.locator(".sl-board").inner_text()


def test_the_best_line_is_the_most_confident_and_a_row_without_one_says_only_its_lines(page):
    page.evaluate("""() => { const p = PROPS.find(p => p.n === 'Amon-Ra St. Brown' && p.mkt === 'REC');
      PROPS.push({...p, mkt: 'RECS', line: 6.5, model: 20, side: 'lower', tier: 'very', books: {}}); render(); }""")
    all_chips(page)
    r = row(page, "amonra-st-brown")
    assert r.locator(".sl-pick").inner_text() == "Lower catches" and r.locator(".sl-r .sl-conf").inner_text() == "Very confident"
    assert r.locator(".sl-go").inner_text() == "3 lines"
    page.evaluate("GAL_WIN = 'evening-sun'; render()")
    all_chips(page)
    k = row(page, "george-kittle")
    assert k.locator(".sl-pick, .sl-r .sl-conf").count() == 0, "his only yards line is No pick, a touchdown never counts"
    assert k.locator(".sl-go").inner_text() == "2 lines"


def test_the_matchup_chip_follows_the_defence_rank(page):
    """Rank 1 allows the fewest points: the eight softest are Easy, the eight toughest Tough."""
    got = {}
    for win, slugs in (("morning", ["chase-brown", "joe-burrow"]), ("evening-sun", ["george-kittle", "brock-purdy"])):
        page.evaluate(f"GAL_WIN = {win!r}; render()")
        all_chips(page)
        for s in slugs:
            got[s] = row(page, s).locator(".sl-f").all_inner_texts()
    assert got == {"chase-brown": ["Easy matchup"], "joe-burrow": ["Easy matchup"],
                   "george-kittle": ["Easy matchup"], "brock-purdy": ["Tough matchup"]}


def test_a_phone_fits_every_row(page):
    for win in ("morning", "evening-sun", "evening-mon"):
        page.evaluate(f"GAL_WIN = {win!r}; render()")
        all_chips(page)
        assert page.evaluate("document.documentElement.scrollWidth") <= 360, win
        over = page.evaluate("[...document.querySelectorAll('.sl-row *')].filter(e => e.getBoundingClientRect().right > 360 - 8).length")
        assert over == 0, win


def test_a_game_card_is_a_headline_link_and_no_sentences(page):
    page.evaluate(AS_SEA_SF)
    g = page.locator(".sl-game[data-slgamecard='SEA @ SF']")
    assert g.locator(".sl-odds, .sl-script, .sl-why").count() == 0
    take = g.locator(".sl-take")
    assert take.evaluate("e => e.tagName") == "BUTTON" and take.locator("span").inner_text() == "›"
    assert page.locator(".bets-foot").count() == 0, "Slips has no footer"
    page.evaluate("SURFACE = 'build'; render()")
    assert page.locator(".bets-foot").count() == 1, "Build keeps its line count"


def test_the_headline_opens_that_games_dossier(page):
    page.evaluate(AS_SEA_SF)
    page.locator(".sl-game[data-slgamecard='SEA @ SF'] .sl-take").click()
    assert page.evaluate("SURFACE") == "preview" and page.evaluate("PV_I") == 3 and page.evaluate("PV_OPEN") is True
    assert page.locator(".pv-dz").count() == 1
    page.go_back()
    page.wait_for_function("PV_OPEN === false")


def test_the_record_is_one_line_with_the_three_tiers(page):
    rec = page.locator(".pr-rec")
    assert rec.count() == 1
    btn = rec.locator("button.pr-rec-b")
    assert btn.get_attribute("aria-expanded") == "false"
    assert btn.locator(".pr-rec-l").all_text_contents() == ["Record", "Claude"], "Claude's row is the second line (tests/test_claude_record.py)"
    assert btn.locator(".pr-rq i").all_inner_texts() == ["Slight", "Confident", "Very"]
    assert btn.locator(".pr-rq b").all_inner_texts() == ["55%", "53%", "57%"]
    assert btn.locator(".pr-rq b").first.evaluate("e => getComputedStyle(e).fontFamily").lower().endswith("monospace")
    assert page.evaluate("document.querySelector('.pr-rec').compareDocumentPosition(document.querySelector('.sl-board')) & 4"), "above the board"
    assert btn.locator(".pr-rq.very i").evaluate("e => getComputedStyle(e).backgroundColor") != "rgba(0, 0, 0, 0)", "Very is a filled chip"
    assert btn.locator(".pr-rq.slight i").evaluate("e => getComputedStyle(e).backgroundColor") == "rgba(0, 0, 0, 0)"
    assert page.evaluate("document.documentElement.scrollWidth") <= 360
    page.evaluate("SURFACE = 'build'; render()")
    assert page.locator(".pr-rec").count() == 0, "Slips only"


def test_the_record_line_is_slim_and_never_wraps_at_360(page):
    """The Slips budget (design/STYLE.md): the first game card starts by 200px. The strip was a 117px card
    that put it at 289px; it is now one line (Claude's row under it, tests/test_claude_record.py, takes the button
    from 36px to 44px and the first card to 212px at most)."""
    box = page.locator(".pr-rec-b").bounding_box()
    assert 32 <= box["height"] <= 44, box
    assert page.evaluate("(() => { const b = document.querySelector('.pr-rec-b'); return b.scrollWidth <= b.clientWidth; })()"), "overflows its line"
    mids = page.evaluate("[...document.querySelectorAll('.pr-rec-r:first-child > .pr-rec-l, .pr-rec-r:first-child > .pr-rq')].map(e => { const r = e.getBoundingClientRect(); return r.top + r.height / 2; })")
    assert max(mids) - min(mids) < 3, f"all on one line: {mids}"
    # The first data is Top calls since 2026-10-05; the game cards follow it.
    top = page.locator(".tpc").bounding_box()["y"] + page.evaluate("window.scrollY")
    print("Top calls top:", top)
    assert top <= 212, f"Top calls at {top}px"


def test_the_record_line_opens_its_detail(page):
    btn = page.locator(".pr-rec-b")
    more = page.locator("#pr-rec-more")
    assert more.is_hidden()
    btn.click()
    assert btn.get_attribute("aria-expanded") == "true" and more.is_visible()
    assert page.locator(".pr-rec-s").inner_text() == "weeks 1-4"
    assert page.locator(".pr-rt b").all_inner_texts() == ["205-165", "305-275", "241-182"]
    assert page.locator(".pr-rt span").all_inner_texts() == ["SLIGHT", "CONFIDENT", "VERY"]
    assert page.locator(".pr-rt small").all_inner_texts() == ["55%", "53%", "57%"]
    page.evaluate("render()")
    assert page.locator("#pr-rec-more").is_visible(), "a re-render keeps it open"
    page.locator(".pr-rec-b").click()
    assert page.locator(".pr-rec-b").get_attribute("aria-expanded") == "false" and page.locator("#pr-rec-more").is_hidden()
    page.locator(".pr-rec-b").focus()
    page.keyboard.press("Tab")
    page.keyboard.press("Shift+Tab")
    assert page.evaluate("document.activeElement.className") == "pr-rec-b"
    assert page.locator(".pr-rec-b").evaluate("e => getComputedStyle(e).outlineStyle") == "solid", "a visible focus ring"


def test_nothing_graded_is_no_strip(page):
    page.evaluate("for (const t of Object.values(LIVE_PROPS_RECORD.tiers)) { t.w = 0; t.l = 0; } render()")
    assert page.locator(".pr-rec").count() == 0 and page.locator(".sl-board").count() == 1
    page.evaluate("LIVE_PROPS_RECORD.through_week = 1; LIVE_PROPS_RECORD.tiers.slight.w = 3; SL_REC_OPEN = true; render()")
    assert page.locator(".pr-rec-s").inner_text() == "week 1"
    assert page.locator(".pr-rt small").all_inner_texts() == ["100%", "", ""]
    assert page.locator(".pr-rq b").all_inner_texts() == ["100%"]
