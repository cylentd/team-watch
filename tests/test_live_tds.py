"""Live's TDs tab (2026-10-04): who has scored (a rushing or receiving TD, from the league-wide
`lead`) and who of Parlay's top TD chances is still alive, with his game's state. Since 2026-10-05 a
switch (Feed, By game) and four chips (Mine, Pass, Rush, Rec) narrow it."""
import pytest

from test_live_tabs import live  # noqa: F401
from test_render import browser, open_page  # noqa: F401  (the suite's one Chromium)

# The page's own TD chances, ranked the way the board ranks them, and the lead rows planted around them.
PLANT = """() => {
  const board = PROPS.filter(p => p.mkt === "TD" && p.slug).sort(SORTS.model).slice(0, TD_ALIVE_N);
  const [a, b, c] = board;
  const lead = {
    "9001": {n: "Test Rusher", pos: "RB", team: "SF", s: {rush_td: 2, rush_yd: 80}, pts: 20},
    "9002": {n: "Test Passer", pos: "QB", team: "SF", s: {pass_td: 3, pass_yd: 300}, pts: 24},
    "9003": {n: "Test Nobody", pos: "WR", team: "SF", s: {rec: 4, rec_yd: 40}, pts: 8},
    "9004": {n: b.n, pos: b.pos, team: b.team, s: {rec_td: 1}, pts: 12}};
  GD_STATS = {week: 2, games: {}, stats: {}, lead};
  GD_CLOCK = {};
  return {a: [a.n, a.team], b: [b.n, b.team], c: [c.n, c.team], n: board.length};
}"""

CLOCK = """([club, state]) => {
  GD_CLOCK = {[club]: {state, q: 3, clock: "4:12", half: false, detail: "", clubs: [club]}};
  const host = document.createElement("div");
  host.innerHTML = gdTdsHTML(GD.leagues[0]);
  return [...host.querySelectorAll(".td-card")].map(card => [...card.querySelectorAll(".td-row")].map(r =>
    ({cls: r.className.replace("td-row", "").trim(), who: r.querySelector(".td-who b").firstChild.textContent.trim(),
      line: (r.querySelector(".td-line") || {}).textContent || "", clock: r.querySelector(".td-clock").textContent,
      slug: r.dataset.tdslug})));
}"""


@pytest.mark.render
def test_scored_lists_rushers_and_receivers_not_passers_and_the_board_keeps_who_is_alive(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    planted = page.evaluate(PLANT)
    assert planted["n"] >= 3, "the fixtures carry too few TD lines for this test"
    club = planted["a"][1]
    scored, alive = page.evaluate(CLOCK, [club, "in"])
    names = [r["who"] for r in scored]
    assert names[0] == "T. Rusher" and scored[0]["line"] == "2 rush TD"          # most TDs first
    assert any(r["line"] == "1 rec TD" for r in scored)                            # a receiver counts
    assert not any("Passer" in n or "Nobody" in n for n in names)                  # a passing TD is no anytime TD
    # a board player who scored is in Scored and out of Still alive
    b_name = planted["b"][0].split(" ", 1)
    assert not any(r["who"].startswith(b_name[0][0] + ".") and r["who"].endswith(b_name[1]) for r in alive)
    # the top of the board, his game on and no TD: lime state with the game clock
    top = next(r for r in alive if r["who"].startswith(planted["a"][0][0] + "."))
    assert top["cls"] == "live" and top["clock"] == "Q3 4:12" and top["line"] == "No TD yet"
    # his game over with no TD: red, and at the bottom (a club-mate's row sinks with him)
    scored, alive = page.evaluate(CLOCK, [club, "post"])
    assert alive[-1]["cls"] == "missed" and alive[-1]["clock"] == "Final" and alive[-1]["line"] == "Missed"
    kinds = [r["cls"] == "missed" for r in alive]
    assert kinds == sorted(kinds)                                                  # missed rows are the tail
    # a scorer whose game is over is no miss: no `missed` class, a green TD line, a plain grey Final, a bright name
    colours = page.evaluate("""([clubs]) => {
      GD_CLOCK = Object.fromEntries(clubs.map(c => [c, {state: "post", q: 4, clock: "0:00", half: false, detail: "", clubs: [c]}]));
      const probe = v => { const d = document.createElement('i'); d.style.color = getComputedStyle(document.body).getPropertyValue(v);
        document.body.append(d); const c = getComputedStyle(d).color; d.remove(); return c; };
      const host = document.createElement('div');
      host.innerHTML = gdTdsHTML(null);
      const view = document.getElementById('view'), was = view.dataset.view;
      view.dataset.view = 'live';                      // the stylesheet is fenced to Live's view (design/scope.json)
      view.append(host);
      const row = host.querySelector('.td-row.scored'), miss = host.querySelector('.td-row.missed');
      const col = (el, sel) => getComputedStyle(el.querySelector(sel)).color;
      const out = {line: col(row, '.td-line'), clock: col(row, '.td-clock'), name: col(row, '.td-who b'),
                   scoredCls: [...host.querySelector('.td-card').querySelectorAll('.td-row')].map(r => r.className),
                   up: probe('--up'), grey: probe('--ink-3'), down: probe('--down'), missLine: miss ? col(miss, '.td-line') : null};
      host.remove();
      if (was === undefined) delete view.dataset.view; else view.dataset.view = was;
      return out;
    }""", [[club, "SF", planted["b"][1]]])
    assert colours["scoredCls"] and not any("missed" in c for c in colours["scoredCls"])
    assert colours["line"] == colours["up"] and colours["clock"] == colours["grey"]
    assert colours["name"] != colours["grey"]
    assert colours["missLine"] == colours["down"]                                  # only a Still-alive miss is red
    # before any kickoff everyone is later, and Scored says so
    page.evaluate("GD_STATS.lead = {}")
    scored, alive = page.evaluate(CLOCK, ["ZZZ", "pre"])
    assert scored == [] and alive and all(r["cls"] == "later" for r in alive)
    assert page.evaluate("(() => { const h = document.createElement('div'); h.innerHTML = gdTdsHTML(null); return h.querySelector('.td-empty').textContent; })()") == "No touchdowns yet."
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_without_stats_the_tab_says_it_is_reading_and_a_row_opens_a_profile(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.evaluate(PLANT)
    # a reply without `lead` (an older edge copy) is not "no touchdowns yet": the tab is still reading
    page.evaluate("GD_STATS = {week: 2, games: {}, stats: {}}")
    assert page.evaluate("(() => { const h = document.createElement('div'); h.innerHTML = gdTdsHTML(null); return [h.querySelectorAll('.td-row').length, h.textContent.trim()]; })()") \
        == [0, "Reading Sleeper's live stats…"]
    page.evaluate("GD_STATS = null")
    assert page.evaluate("(() => { const h = document.createElement('div'); h.innerHTML = gdTdsHTML(null); return [h.querySelectorAll('.td-row').length, h.textContent.trim()]; })()") \
        == [0, "Reading Sleeper's live stats…"]
    page.evaluate(PLANT)
    opened = page.evaluate("""() => {
      let got = null;
      openProfile = (p) => { got = p; };
      const host = document.createElement("div");
      host.innerHTML = gdTdsHTML(null);
      wireTds(host);
      host.querySelector(".td-row").click();
      return got;
    }""")
    assert opened["n"] == "Test Rusher" and opened["slug"] == "test-rusher" and opened["pos"] == "RB"
    ctx.close()
    assert errors == []


# Three games of week 2: KC at SF is on, MIN at DET went final early, BUF at MIA went final late. One
# of the reader's own players (the first of their lineups) scored for KC.
GAMES = """() => {
  const week = GD.leagues[0].week;
  GD_GAMES.splice(0, GD_GAMES.length,
    {home: "SF", away: "KC", kickoff: "2026-09-13T20:25:00Z", week},
    {home: "DET", away: "MIN", kickoff: "2026-09-13T17:00:00Z", week},
    {home: "MIA", away: "BUF", kickoff: "2026-09-13T17:30:00Z", week});
  GD_CLOCK = {SF: {state: "in", q: 3, clock: "4:12", half: false, detail: "", clubs: ["SF", "KC"]},
              DET: {state: "post", q: 4, clock: "0:00", half: false, detail: "", clubs: ["DET", "MIN"]},
              MIA: {state: "post", q: 4, clock: "0:00", half: false, detail: "", clubs: ["MIA", "BUF"]}};
  Object.assign(GD_STATS.stats, {SF: {pts_allow: 17}, KC: {pts_allow: 24}, DET: {pts_allow: 20}, MIN: {pts_allow: 13},
                                  MIA: {pts_allow: 10}, BUF: {pts_allow: 27}});
  const m = GD.leagues.flatMap(l => gdMineLineup(l)).find(r => r.sid && r.n);
  GD_STATS.lead = {
    "9001": {n: "Test Rusher", pos: "RB", team: "SF", s: {rush_td: 2}, pts: 20},
    "9002": {n: "Test Passer", pos: "QB", team: "SF", s: {pass_td: 3}, pts: 24},
    "9003": {n: "Test Catcher", pos: "WR", team: "KC", s: {rec_td: 1}, pts: 12},
    "9004": {n: "Detroit Catcher", pos: "WR", team: "DET", s: {rec_td: 1}, pts: 11},
    "9005": {n: "Miami Runner", pos: "RB", team: "MIA", s: {rush_td: 1}, pts: 10},
    [m.sid]: {n: m.n, pos: m.pos, team: "KC", s: {rush_td: 1}, pts: 9}};
  return nameInitial(m.n);
}"""

ROWS = "[...document.querySelectorAll('.td-row')].map(r => r.querySelector('.td-who b').firstChild.textContent.trim())"
CARDS = """[...document.querySelectorAll('.td-gcard')].map(c => ({head: c.querySelector('.td-gh').innerText.replace(/\\s+/g, ' ').trim(),
  rows: [...c.querySelectorAll('.td-row')].map(r => r.querySelector('.td-who b').firstChild.textContent.trim())}))"""


def tds(browser, page_file, viewport=(360, 780)):
    ctx, page, errors = live(browser, page_file, viewport)
    mine = page.evaluate(GAMES)
    page.click("[data-gdtab='tds']")
    return ctx, page, errors, mine


def test_the_switch_keeps_the_feed_and_by_game_is_one_card_per_game(browser, page_file):
    ctx, page, errors, mine = tds(browser, page_file)
    assert page.locator("[data-tdmode='feed']").get_attribute("aria-pressed") == "true"      # the list stays the default
    assert page.locator(".td-card").count() == 2 and page.locator(".td-gcard").count() == 0
    page.click("[data-tdmode='game']")
    assert page.locator("[data-tdmode='game']").get_attribute("aria-pressed") == "true"
    cards = page.evaluate(CARDS)
    # the game on now first, then the latest kickoff first; the header is the clubs, the score and the clock
    assert [c["head"] for c in cards] == ["KC 17 SF 24 Q3 4:12", "BUF 10 MIA 27 Final", "MIN 20 DET 13 Final"]
    assert [len(c["rows"]) for c in cards] == [3, 1, 1]
    assert cards[0]["rows"][0] == "T. Rusher" and "T. Passer" not in cards[0]["rows"]       # a passing TD is no anytime TD
    # a game's rows hold neither the clock nor the club; one card per subject, never a card in a card
    assert page.locator(".td-gcard .td-clock, .td-gcard .td-row small").count() == 0
    assert page.locator(".td-gcard .td-card, .td-gcard .gd-card").count() == 0
    assert page.locator(".td-gcard button button").count() == 0
    # the header opens that game's sheet
    page.locator(".td-gh").first.click()
    page.wait_for_selector("#gamesheet.on")
    page.keyboard.press("Escape")
    page.wait_for_selector("#gamesheet:not(.on)", state="attached")
    # the view is remembered; a store that will not answer still switches
    assert page.evaluate("localStorage.getItem('tw-live-tds')") == "game"
    page.evaluate("Storage.prototype.setItem = () => { throw new Error('blocked'); }; Storage.prototype.getItem = () => { throw new Error('blocked'); }; 0")
    page.click("[data-tdmode='feed']")
    assert page.locator(".td-gcard").count() == 0 and page.locator("[data-tdmode='feed']").get_attribute("aria-pressed") == "true"
    ctx.close()
    assert errors == []


def test_chips_narrow_both_views_and_an_empty_result_is_one_line(browser, page_file):
    ctx, page, errors, mine = tds(browser, page_file)
    chip = lambda k: page.click(f"[data-tdchip='{k}']")
    rows = lambda: page.evaluate(ROWS)
    alive = lambda: page.locator(".td-card:has(.td-head:has-text('Still alive'))").count()
    assert alive() == 1 and "T. Passer" not in rows()
    # a TD type: only that type, and Still alive (no TD type) steps aside
    chip("rush")
    assert set(rows()) == {"T. Rusher", "M. Runner", mine} and alive() == 0
    assert page.locator(".td-line").all_inner_texts().count("2 rush TD") == 1
    chip("rush")
    chip("pass")                       # the only way a passer appears
    assert rows() == ["T. Passer"] and page.locator(".td-line").inner_text() == "3 pass TD"
    chip("rec")
    assert set(rows()) == {"T. Passer", "T. Catcher", "D. Catcher"}
    chip("pass"); chip("rec")
    # Mine: only the reader's players, in both views; Still alive narrows to theirs
    chip("mine")
    assert len(rows()) >= 1 and "T. Rusher" not in rows() and page.locator("[data-tdchip='mine']").get_attribute("aria-pressed") == "true"
    page.click("[data-tdmode='game']")
    cards = page.evaluate(CARDS)
    assert len(cards) == 1 and cards[0]["rows"] == [mine]
    # nothing matches: one line, in either view
    chip("pass")
    assert page.locator(".td-empty").count() == 1 and page.locator(".td-empty").inner_text() == "No touchdowns match."
    page.click("[data-tdmode='feed']")
    assert page.locator(".td-empty").count() == 1 and page.locator(".td-row").count() == 0
    # filters clear on a visit; the view stays
    page.evaluate("TD_ON = {}; paintLive()")
    assert page.locator(".td-filters [aria-pressed='true']").count() == 0
    ctx.close()
    assert errors == []


def test_mine_is_the_readers_pick_and_with_none_it_says_to_pick(browser, page_file):
    ctx, page, errors, mine = tds(browser, page_file)
    page.evaluate("localStorage.removeItem('tw-team'); localStorage.removeItem('tw-follow'); TD_ON = {mine: true}; paintLive()")
    assert page.locator(".td-empty").inner_text() == "Pick your team to see your players."
    ctx.close()
    assert errors == []


def test_a_phone_holds_the_controls_in_two_rows_and_nothing_scrolls_sideways(browser, page_file):
    ctx, page, errors, mine = tds(browser, page_file)
    page.click("[data-tdmode='game']")
    m = page.evaluate("""() => {
      const box = s => document.querySelector(s).getBoundingClientRect();
      return {w: document.documentElement.scrollWidth, vw: innerWidth, mode: box('.td-mode'), chips: box('.td-filters'),
              tallest: Math.max(...[...document.querySelectorAll('.td-filters .chip')].map(c => c.getBoundingClientRect().height)),
              first: box('.td-gcard')};
    }""")
    assert m["w"] <= m["vw"]
    assert m["chips"]["height"] <= m["tallest"] + 1                           # four chips, one line at 360px
    assert m["tallest"] >= 36
    ctx.close()
    assert errors == []
