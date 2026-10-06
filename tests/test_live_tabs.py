"""This week > Live, the tabs, the strip and the mirrored lineups (2026-10-05, storyboard
https://claude.ai/artifact/ArF53Lvh12QV8fbL3mr9KP, option 2A): My league, NFL, TDs in one segmented
control (Matchup and League merged into My league that day); My league leads with a strip of the
league's matchups, then one row per starter slot, my starter against theirs, then the ranking.
Browser tests on the week 2 fixture (tests/fixtures/gameday.json): SF's game is on, DET's has not
started, every other game is final. The reader's team is David's ESPN one unless a test says not."""
import re

import pytest

from test_render import LIVE_PLANT as plant, go, open_page  # noqa: F401

pytestmark = pytest.mark.render

PHONE = (360, 780)


def live(browser, page_file, viewport=PHONE, states=None, team="espn"):
    ctx, page, errors = open_page(browser, page_file, viewport)
    page.evaluate(f"localStorage.setItem('tw-team', '{team}');" + plant(states))
    for kind, sel in go("live"):
        page.click(sel)
    # The board's own tab bar is a desktop's; a phone carries the tabs in the tab row (data/tabrow.js).
    page.wait_for_selector("[data-gdboard] .gd-tabs", state="attached")
    return ctx, page, errors


def test_three_tabs_and_my_league_is_a_mirrored_row_per_starter_slot(browser, page_file):
    ctx, page, errors = live(browser, page_file)
    # A phone (2026-10-05): the Live pill opens in place into the three tabs, and the board draws no bar of its own.
    names = [re.sub(r"\d+$", "", s).strip() for s in page.locator("#subnav .tr-x .tr-seg").all_inner_texts()]
    assert names == ["My league", "NFL", "TDs"]
    assert page.locator("#subnav .tr-x .mode-sub[aria-pressed='true']").inner_text() == "Live"
    assert page.locator("#subnav .tr-seg[aria-pressed='true']").get_attribute("data-gdtab") == "league"
    assert page.locator(".gd-tabs").is_hidden()
    # nine starters in the reader's ESPN lineup: nine rows, each a slot pill between two halves
    starters = page.evaluate("gdMineLineup(gdLeague()).filter(gdStarter).length")
    rows = page.locator(".gd-mirror:not(.bn) .gd-mr")
    assert starters == 9 and rows.count() == 9
    assert rows.evaluate_all("rs => rs.every(r => r.querySelectorAll('.gd-h').length === 2 && r.querySelectorAll('.gd-sl').length === 1)")
    # every half with a game carries a clock button that opens the game sheet on his game
    clocks = page.locator(".gd-mirror .gd-ck[data-gdnfl]")
    assert clocks.count() >= 1      # the fixture schedule holds only some of week 2's clubs
    assert clocks.evaluate_all("bs => bs.every(b => b.tagName === 'BUTTON' && /^[^,]*,[A-Z]+,[A-Z]+$/.test(b.dataset.gdnfl) && b.dataset.gdfocus)")
    assert page.locator(".gd-mirror button button").count() == 0            # never a button in a button
    # the slot pill wears the position's colour; FLEX wears the RB-WR-TE blend
    col = lambda slot: page.locator(f".gd-mr .gd-sl:text-is('{slot}')").first.evaluate("e => getComputedStyle(e).color")
    assert len({col("QB"), col("RB"), col("TE"), col("WR")}) == 4
    assert page.locator(".gd-sl.qb").count() >= 1 and page.locator(".gd-sl.def").count() >= 1
    flex = page.locator(".gd-mr .gd-sl:text-is('FLEX')").first
    assert flex.get_attribute("class").split() == ["gd-sl", "mix", "flex"]
    assert "linear-gradient" in flex.evaluate("e => getComputedStyle(e).backgroundImage")
    # the median line sits under the score in a league that pays the top half
    assert re.match(r"^League median \d+\.\d · you [+−]\d+\.\d$", page.locator(".gd-medline").inner_text())
    # benches are shut until the Benches row opens them, mirrored the same way
    assert page.locator(".gd-mirror.bn").count() == 0
    page.click("[data-gdbench]")
    assert page.locator(".gd-mirror.bn .gd-mr").count() >= 1
    # a row's name opens his profile; a row's clock opens that game's sheet
    page.locator(".gd-mirror .gd-nb").first.click()
    page.wait_for_selector("#modal.on")
    page.keyboard.press("Escape")
    page.locator(".gd-mirror .gd-ck[data-gdnfl]").first.click()
    page.wait_for_selector("#gamesheet.on")
    page.keyboard.press("Escape")
    ctx.close()
    assert errors == []


def test_a_phone_fits_the_score_and_nine_starters_in_780px(browser, page_file):
    ctx, page, errors = live(browser, page_file)
    page.wait_for_selector(".gd-mirror .gd-mr")
    m = page.evaluate("""() => {
      const rows = [...document.querySelectorAll('.gd-mirror:not(.bn) .gd-mr')];
      const box = e => e.getBoundingClientRect();
      const at = s => { const e = document.querySelector(s); return e ? [Math.round(box(e).top + scrollY), Math.round(box(e).height)] : null; };
      return {last: Math.round(box(rows[8]).bottom + scrollY), tallest: Math.round(Math.max(...rows.map(r => box(r).height))),
              head: Math.round(box(document.querySelector('.gd-head')).top + scrollY),
              parts: {tabs: at('.gd-tabs'), strip: at('.gd-strip'), head: at('.gd-head'), median: at('.gd-medline'), rows: at('.gd-mirror')}};
    }""")
    bar = page.evaluate("Math.round(document.querySelector('.tabbar').getBoundingClientRect().top)")
    # the header bar is the phone's team switch: the score head shows the reader's name, never a second switch
    assert page.locator(".gd-side.a.mine .gd-sw").is_hidden() and page.locator(".gd-side.a.mine .gd-me").is_visible()
    assert page.locator("#hdrswitch [data-tsbtn]").is_visible()
    ctx.close()
    print("9th starter row bottom:", m["last"], "tallest row:", m["tallest"], "parts [top, height]:", m["parts"], "bottom bar top:", bar)
    # Since 2026-10-05 the phone's bottom tab bar covers the screen's last 64px: the rows end above it.
    assert m["last"] <= bar, m
    assert m["tallest"] <= 52, m
    assert errors == []


def test_games_tab_lists_every_game_live_first_and_a_tile_opens_the_sheet(browser, page_file):
    ctx, page, errors = live(browser, page_file)
    n_games = page.evaluate("gdWeekGames().length")
    assert n_games >= 3
    # the first game of the week is on, the second has not kicked off, the rest are final
    page.evaluate("""() => {
      const gs = gdWeekGames(), st = GD_STATS.games;
      gs.forEach((g, i) => { for (const c of gdCodes(g.home).concat(gdCodes(g.away))) st[c] = i === 0 ? "in_game" : i === 1 ? "pre_game" : "complete"; });
      paintLive();
    }""")
    # NFL carries the lime count of games on now, in the tab row on a phone (repainted with each poll)
    assert page.locator("#subnav [data-gdtab='games'] .tr-n").inner_text() == "1"
    assert page.locator("#subnav [data-gdtab='games'] .tr-n").get_attribute("aria-label") == "1 game live now"
    page.evaluate("""() => { const st = GD_STATS.games; gdWeekGames().slice(0, 2).forEach(g => { for (const c of gdCodes(g.home).concat(gdCodes(g.away))) st[c] = "in_game"; }); paintLive(); }""")
    assert page.locator("#subnav [data-gdtab='games'] .tr-n").get_attribute("aria-label") == "2 games live now"
    assert page.locator(".gd-tabs [data-gdtab='games'] .gd-n").get_attribute("aria-label") == "2 games live now"   # and in the desktop's bar
    page.evaluate("""() => { const st = GD_STATS.games; gdWeekGames().forEach((g, i) => { for (const c of gdCodes(g.home).concat(gdCodes(g.away))) st[c] = i === 0 ? "in_game" : i === 1 ? "pre_game" : "complete"; }); paintLive(); }""")
    page.click("[data-gdtab='games']")
    assert page.evaluate("localStorage.getItem('tw-live-tab')") == "games"
    assert page.locator(".gd-mirror").count() == 0 and page.locator(".gd-nfl, .gd-now").count() == 0
    tiles = page.locator(".gd-tiles .gd-t")
    assert tiles.count() == n_games
    kinds = tiles.evaluate_all("ts => ts.map(t => t.classList.contains('in') ? 'in' : t.classList.contains('pre') ? 'pre' : 'post')")
    assert kinds[0] == "in" and kinds[1] == "pre" and set(kinds[2:]) == {"post"}
    # a tile with my starters has a lime edge and says how many; two tiles side by side on a phone
    mine = page.locator(".gd-t.mine")
    assert mine.count() >= 1 and re.match(r"^\d+ yours$", mine.first.locator(".gd-ts em").inner_text())
    lime = page.evaluate("(() => { const d = document.createElement('i'); d.style.color = getComputedStyle(document.body).getPropertyValue('--lime'); document.body.append(d); const c = getComputedStyle(d).color; d.remove(); return c; })()")
    assert mine.first.evaluate("e => getComputedStyle(e).borderTopColor") == lime
    xs = tiles.evaluate_all("ts => ts.slice(0, 2).map(t => Math.round(t.getBoundingClientRect().left))")
    assert xs[0] != xs[1]
    tiles.first.click()
    page.wait_for_selector("#gamesheet.on")
    page.keyboard.press("Escape")
    ctx.close()
    assert errors == []


def test_games_tiles_read_by_state_and_the_leader_wears_its_club_colour(browser, page_file):
    ctx, page, errors = live(browser, page_file)
    page.evaluate("""() => {
      const gs = gdWeekGames(), st = GD_STATS.games;
      gs.forEach((g, i) => { for (const c of gdCodes(g.home).concat(gdCodes(g.away))) st[c] = i === 0 ? "in_game" : i === 1 ? "pre_game" : "complete"; });
      paintLive();
    }""")
    page.click("[data-gdtab='games']")
    tiles = page.locator(".gd-tiles .gd-t")
    style = lambda sel, prop: page.locator(sel).first.evaluate(f"e => getComputedStyle(e).{prop}")
    # three states, three looks: a live tile has a lime stripe and wash, a final one is dimmer, an
    # upcoming one is the plain panel
    live_t, pre_t, post_t = (style(f".gd-t.{k}", "backgroundColor") for k in ("in", "pre", "post"))
    assert len({live_t, pre_t, post_t}) == 3
    assert "200, 255, 46" in style(".gd-t.in", "boxShadow") and style(".gd-t.pre", "boxShadow") == "none"
    # mine stays a ring: a lime border on every side, never the live stripe alone
    mine = page.locator(".gd-t.mine:not(.in)")
    assert mine.count() >= 1 and mine.first.evaluate("e => getComputedStyle(e).boxShadow") == "none"
    # who leads is read off the score: the trailer is grey, the leader is not, a tie is plain
    rows = tiles.evaluate_all("""ts => ts.map(t => {
      const [a, h] = [...t.querySelectorAll('.gd-tr')], n = r => +r.querySelector('b').textContent;
      if (isNaN(n(a)) || isNaN(n(h))) return null;
      const cls = r => r.classList.contains('lead') ? 'lead' : r.classList.contains('behind') ? 'behind' : 'plain';
      return [n(a), n(h), cls(a), cls(h)];
    }).filter(Boolean)""")
    assert rows
    for a, h, ca, ch in rows:
        assert (ca, ch) == (("lead", "behind") if a > h else ("behind", "lead") if h > a else ("plain", "plain"))
    # the leader's club code and score share one colour; it is the club's own when readable on the
    # panel (set as --tc), else the page's ink; the trailer is --ink-3
    ink, ink3 = page.evaluate("""(() => { const g = n => { const d = document.createElement('i'); d.style.color = getComputedStyle(document.body).getPropertyValue(n); document.body.append(d); const c = getComputedStyle(d).color; d.remove(); return c; }; return [g('--ink'), g('--ink-3')]; })()""")
    cols = page.locator(".gd-tr.lead").evaluate_all("rs => rs.map(r => [getComputedStyle(r.querySelector('span')).color, getComputedStyle(r.querySelector('b')).color, r.style.getPropertyValue('--tc')])")
    assert cols and all(c == b for c, b, _ in cols)
    assert all((tc != "") == (c != ink) for c, _, tc in cols)
    assert set(page.locator(".gd-tr.behind b").evaluate_all("bs => bs.map(b => getComputedStyle(b).color)")) <= {ink3}
    # every club colour the tab can pick holds 3:1 against the panel; a near-black one falls back
    bad = page.evaluate("""() => {
      const lum = h => { const c = [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16) / 255).map(v => v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4); return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]; };
      const panel = lum('#171b21');
      return Object.keys(TEAM_COLOURS).filter(k => { const t = gdClubTint(k); return t && (lum(t) + 0.05) / (panel + 0.05) < 2.8; });
    }""")
    assert bad == []
    assert page.evaluate("gdClubTint('KC')") == "#e31837"
    # a navy primary is lifted in its own hue, not dropped to ink: blue stays the strongest channel
    nyg = page.evaluate("gdClubTint('NYG')")
    assert nyg and int(nyg[5:7], 16) > int(nyg[1:3], 16)
    uncoloured = page.evaluate("Object.keys(TEAM_COLOURS).filter(k => !gdClubTint(k))")
    assert len(uncoloured) <= 2, uncoloured
    assert page.evaluate("gdClubTint('WSH')") == page.evaluate("gdClubTint('WAS')")
    ctx.close()
    assert errors == []


def test_the_strip_leads_my_league_and_a_chip_shows_its_game_without_leaving_the_tab(browser, page_file):
    ctx, page, errors = live(browser, page_file)
    n = page.evaluate("gdLeague().games.length")
    chips = page.locator(".gd-strip .gd-chip")
    assert chips.count() == n and n >= 2
    # the strip sits on top, above the score head; the reader's game is first, ringed in lime, and on screen
    order = page.evaluate("[...document.querySelectorAll('.gd-match > *')].map(e => e.className.split(' ')[0])")
    assert order[:2] == ["gd-strip", "gd-head"]
    assert "mine" in chips.first.get_attribute("class") and "on" in chips.first.get_attribute("class")
    assert page.locator(".gd-chip.mine").count() == 1
    lime = page.evaluate("(() => { const d = document.createElement('i'); d.style.color = getComputedStyle(document.body).getPropertyValue('--lime'); document.body.append(d); const c = getComputedStyle(d).color; d.remove(); return c; })()")
    assert chips.first.evaluate("e => getComputedStyle(e).borderTopColor") == lime
    # each chip: a state word, then two short names with two scores
    assert chips.evaluate_all("cs => cs.every(c => c.querySelector('.gd-cs') && c.querySelectorAll('.gd-cr').length === 2 && c.querySelectorAll('.gd-cr b').length === 2)")
    assert all(re.match(r"^(LIVE|\d+ LEFT|FINAL)$", s.strip()) for s in page.locator(".gd-cs").all_inner_texts())
    # a tap on another game shows it in the score head and the lineups, on the same tab
    chips.nth(1).click()
    assert page.locator(".gd-chip.on").count() == 1 and "mine" not in page.locator(".gd-chip.on").get_attribute("class")
    assert page.locator(".gd-tabs [aria-pressed='true']").get_attribute("data-gdtab") == "league"
    assert re.match(r"^BY \d+\.\d$|^TIED$", page.locator(".gd-lead").inner_text())
    assert page.locator(".gd-mirror .gd-mr").count() >= 1 and page.locator(".gd-side.mine").count() == 0
    # the reader's own chip brings their game back
    page.locator(".gd-chip.mine").click()
    assert re.match(r"^(UP|DOWN) \d+\.\d$|^TIED$", page.locator(".gd-lead").inner_text())
    assert page.locator(".gd-chip.mine.on").count() == 1
    # the ranking sits below the lineups: the median line in a league that pays the top half
    assert page.evaluate("document.querySelector('.gd-ladder').getBoundingClientRect().top > document.querySelector('.gd-mirror').getBoundingClientRect().bottom")
    assert page.locator(".gd-ladder .gd-median:not(.quiet)").count() == 1
    ctx.close()
    assert errors == []


def test_live_draws_no_league_chips_and_the_picked_team_decides_the_league(browser, page_file):
    ctx, page, errors = live(browser, page_file, team="yahoo")
    assert page.evaluate("GD.leagues.length") >= 2, "the fixture needs two leagues"
    for tab in ("league", "games", "tds"):
        page.click(f"[data-gdtab='{tab}']")
        assert page.locator("[data-gdleague], .gd-leagues:not(.td-mode)").count() == 0, tab
    page.click("[data-gdtab='league']")
    assert page.evaluate("gdLeague().key") == "yahoo"
    assert "Chat Take the Wheel" in page.locator(".gd-side.a.mine").inner_text()
    # Live keeps no league setting of its own
    assert page.evaluate("localStorage.getItem('tw-live-league')") is None
    page.evaluate("localStorage.setItem('tw-team', 'espn'); paintLive()")
    assert page.evaluate("gdLeague().key") == "espn"
    assert "Purdy Big in Japan" in page.locator(".gd-side.a.mine").inner_text()
    ctx.close()
    assert errors == []


def test_the_readers_name_on_the_score_head_switches_team_and_stays_on_live(browser, page_file):
    # A desktop: a phone's header bar holds the switch, so its score head shows the plain name (test above).
    ctx, page, errors = live(browser, page_file, (1400, 900), team="yahoo")
    assert page.locator(".gd-side.a.mine .gd-me").is_hidden()
    page.click(".gd-side.a.mine #switch [data-tsbtn]")
    page.wait_for_selector("#switch .ts-menu:not([hidden])")
    # a poll does not shut the open menu
    page.evaluate("paintLive()")
    assert page.locator("#switch .ts-menu:not([hidden])").count() == 1
    page.locator("#switch .ts-item[data-k='espn']:visible").first.click()
    page.wait_for_selector(".gd-strip")
    assert page.evaluate("[localStorage.getItem('tw-team'), SURFACE, gdLeague().key]") == ["espn", "live", "espn"]
    assert "Purdy Big in Japan" in page.locator(".gd-side.a.mine").inner_text()
    ctx.close()
    assert errors == []


def test_a_team_with_no_game_this_week_says_so_and_the_strip_leads_with_the_closest_game(browser, page_file):
    ctx, page, errors = live(browser, page_file)
    # a bye: the reader's game leaves the week (out of the fantasy playoffs and week 18 look the same)
    page.evaluate("(() => { const lg = gdLeague(), me = gdMine(lg); lg.games = lg.games.filter(g => !g.includes(me)); paintLive(); })()")
    assert page.locator(".gd-head.bye").inner_text().strip().endswith("No game this week")
    assert page.locator(".gd-head.bye #switch").count() == 1                      # the name still switches team
    assert page.locator(".gd-mirror").count() == 0 and page.locator(".gd-chip.mine").count() == 0
    # the order itself is tested in Node (test_js_gdstrip.py); here, the first chip's two scores are the closest
    gaps = page.locator(".gd-chip").evaluate_all("cs => cs.map(c => { const [a, b] = [...c.querySelectorAll('.gd-cr b')].map(x => +x.textContent); return Math.abs(a - b); })")
    assert len(gaps) >= 1 and gaps[0] == min(gaps)
    page.locator(".gd-chip").first.click()
    assert page.locator(".gd-head.bye").count() == 0 and page.locator(".gd-mirror .gd-mr").count() >= 1
    ctx.close()
    assert errors == []


def test_the_tab_survives_a_reload_of_the_view_and_a_blocked_store_still_switches(browser, page_file):
    ctx, page, errors = live(browser, page_file)
    page.click("[data-gdtab='tds']")
    assert page.locator("#subnav [data-gdtab='tds']").get_attribute("aria-pressed") == "true"
    # the TDs tab hosts surface/live/tds.js, or an empty state while that file is absent
    assert page.locator(".gd-card").count() >= 1 or page.locator(".state-empty").count() == 1
    assert page.evaluate("location.hash") in ("", "#live")                  # the tab is never in the hash
    page.click("[data-gdtab='league']")
    # another view sends the reader to a tab by setting it, then opening #live; the four tabs' old
    # values land on My league (matchup, league) and NFL (games)
    for old, tab in (("matchup", "league"), ("league", "league"), ("games", "games")):
        page.evaluate(f"localStorage.setItem('tw-live-tab', '{old}'); render()")
        assert page.locator(".gd-tabs [aria-pressed='true']").get_attribute("data-gdtab") == tab
    page.evaluate("localStorage.setItem('tw-live-tab', 'nonsense'); render()")
    assert page.locator(".gd-mirror").count() >= 1                           # anything else is the default
    page.evaluate("Object.defineProperty(window, 'localStorage', {get(){ throw new Error('blocked'); }})")
    page.click("[data-gdtab='games']")
    assert page.locator(".gd-tiles").count() == 1
    ctx.close()
    assert errors == []


def test_desktop_keeps_the_rows_one_reading_width(browser, page_file):
    ctx, page, errors = live(browser, page_file, (1400, 900))
    w = page.evaluate("Math.round(document.querySelector('.gd-mirror').getBoundingClientRect().width)")
    ctx.close()
    assert 400 < w <= 760
    assert errors == []
