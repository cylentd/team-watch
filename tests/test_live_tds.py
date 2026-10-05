"""Live's TDs tab (2026-10-04): who has scored (a rushing or receiving TD, from the league-wide
`lead`) and who of Parlay's top TD chances is still alive, with his game's state."""
import pytest

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
