"""design/digest.py: the Digest block, from ff-jarvis's weekly_digest.json."""
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "design"))
sys.path.insert(0, str(REPO / "api"))

import pytest  # noqa: E402

from _espn import slugify  # noqa: E402
import contract  # noqa: E402
from digest import kicks, live_digest, report  # noqa: E402
from sources import load_digest  # noqa: E402
from test_render import browser, drive, go, open_page  # noqa: E402,F401  (the suite's one Chromium)


def _block(schedule=None):
    return live_digest(load_digest(), slugify, schedule)


SCHEDULE = {"alias": {"LA": "LAR", "WAS": "WSH"}, "games": [
    {"home": "DEN", "away": "LAR", "kickoff": "2026-09-28T00:20:00Z", "week": 3},
    {"home": "WSH", "away": "SEA", "kickoff": "2026-09-27T17:00:00Z", "week": 3},
    {"home": "HOU", "away": "LAR", "kickoff": "2026-10-04T17:00:00Z", "week": 4}]}


def test_kicks_answers_in_both_dialects_for_the_packets_week():
    ko = kicks(SCHEDULE, 3)
    assert ko["LA"] == ko["LAR"] == "2026-09-28T00:20:00Z"
    assert ko["WAS"] == ko["WSH"] == "2026-09-27T17:00:00Z"
    assert "HOU" not in ko and kicks(None, 3) == {}


def test_game_rows_carry_their_kickoff_for_the_browser():
    b = _block(SCHEDULE)
    assert b["hurt"][0]["game"]["ko"] == "2026-09-28T00:20:00Z"
    assert b["wx"][0]["ko"] == "2026-09-27T17:00:00Z"
    assert all(r["ko"] is None or r["ko"].endswith("Z") for r in b["best"] + b["top5"])


def test_results_cut_to_finals_stars_and_busts():
    b = _block()
    assert b["finals"] == [{"away": "MIA", "home": "BUF", "away_pts": 17.0, "home_pts": 27.0}]
    assert b["pending"] == 2
    assert [(r["pos"], r["n"], r["actual"]) for r in b["stars"]] == [("QB", "Josh Allen", 24.6), ("RB", "James Cook", 19.4)]
    assert b["busts"][0]["slug"] == slugify("De'Von Achane")
    assert [(r["n"], r["diff"]) for r in b["smashed"]] == [("Khalil Shakir", 9.7)]
    # A tagged headline gives the injury; an untagged one loses his name, suffix and all.
    # His newest headline since, when there is one, is `later`, without his name or tag.
    assert [(r["n"], r["injury"], r["rest"], r["later"]) for r in b["left"]] == [
        ("Tua Tagovailoa", "concussion", "ruled out for the remainder", None),
        ("De'Von Achane", "knee", "questionable to return", "suffers season-ending torn ACL"),
        ("Travis Etienne", None, "exits early Sunday", None)]
    assert b["asof_words"] == "Fri 10:40 PM"


def test_a_reason_is_rounded_as_the_row_says_it():
    b = _block()
    assert b["smashed"][0]["why"] == {"kind": "role", "luck": 5, "expected": 12, "stat": "targets",
                                      "share": 31, "delta": 10}
    assert [r["why"]["kind"] for r in b["busts"]] == ["hurt", "luck"]


@pytest.mark.render
def test_results_reads_as_the_storyboard(browser, page_file):
    """The badge counts games still to play; each smashed or busted line says why and shows its
    points over its projection, no gap (2026-09-29); a bust who left hurt borrows Left hurt's
    freshest word."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.goto(page_file.as_uri())
    for _, sel in go("digest"):
        page.click(sel)
    got = page.evaluate("""() => {
      const d = dgD(), host = document.createElement('div');
      host.innerHTML = dgResBody(d);
      const rows = [...host.querySelectorAll('.dg-rlow .dg-rr')];
      const lines = rows.map(b => b.querySelector('.dg-rr-n').textContent.replace(/\\s+/g, ' ').trim());
      const nums = rows.map(b => [...b.querySelectorAll('.dg-rv > *')].map(x => x.textContent));
      const pill = s => { const h = document.createElement('div'); h.innerHTML = dgOutPill(s); return h.textContent; };
      return {badge: dgCount('res', d)[0], lines, nums,
              pills: {season: [...host.querySelectorAll('.dg-rlow .dg-pill.out')].filter(p => p.textContent === 'Season').length,
                      weeks: pill('Baker Mayfield expected to miss three weeks')}};
    }""")
    assert errors == []
    ctx.close()
    assert got["badge"] == "2 to play"
    # every reason is a pill (DESIGN.md "Say it in a shape"); innerText has no gaps between flex cells
    assert "31% tgt +10" in got["lines"][0] and "TD luck +5" in got["lines"][0]
    assert got["nums"][0] == ["17.8", "8.1"]                   # points over projection, no gap
    assert all(len(n) <= 2 for n in got["nums"])
    assert "Hurt · Knee" in got["lines"][1]
    assert "TD luck −6" in got["lines"][2]
    assert "Concussion" in got["lines"][3] and got["nums"][3] == ["3.2", "18.4"]
    assert "Left early" in got["lines"][5]
    assert got["pills"]["season"] == 1 and got["pills"]["weeks"] == "Out 3 wks"


@pytest.mark.render
def test_the_results_lists_are_one_panel_under_tabs_on_a_phone(browser, page_file):
    """2026-09-29, storyboard Ms6FbdvynVPoRTKEidPGAz 2A (David: "clicking on smashed, busts, and left hurt
    opens up all 3 panels anyways ... just opens a big panel"): on a phone one tab bar, each tab its
    list's count, one list showing. A tap swaps the list in place, and the pick survives a repaint."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.goto(page_file.as_uri())
    drive(page, go("digest"))
    page.wait_for_selector(".dg-row[data-dgrow='res']")
    if page.locator(".dg-row[data-dgrow='res'][data-open]").count() == 0:
        page.click(".dg-row[data-dgrow='res'] .dg-head")
        page.wait_for_timeout(600)
    visible = lambda sel: page.locator(sel).evaluate_all("els => els.filter(e => e.checkVisibility({visibilityProperty: true})).length")
    tabs = page.locator("[data-dgset='res'] .dg-tab")
    n = page.evaluate("(() => { const d = dgD(); return [d.smashed.length, d.busts.length, d.left.length]; })()")
    assert tabs.count() == 3
    assert [tabs.nth(i).locator(".dg-tab-n").inner_text() for i in range(3)] == [str(x) for x in n]
    assert tabs.first.get_attribute("aria-selected") == "true"
    assert visible("[data-dgset='res'] .dg-rr") == n[0]
    assert visible("[data-dgset='res'] .dg-tabh") == 0          # the tab names the list; no second heading
    tabs.nth(2).click()
    assert tabs.nth(2).get_attribute("aria-selected") == "true" and tabs.first.get_attribute("aria-selected") == "false"
    assert visible("[data-dgset='res'] .dg-rr") == n[2]
    page.evaluate("render()")
    assert page.locator("[data-dgset='res'] .dg-tab").nth(2).get_attribute("aria-selected") == "true"
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_the_wall_opens_all_three_results_lists_on_the_boards_columns(browser, page_file):
    """2026-09-29 (David: "I still feel the tab list to be awkward"): on the wall no tab bar; Smashed,
    Busts and Left hurt all open, each under its own heading with its count, on the board's four columns
    (Smashed under QB, Busts under RB, Left hurt across WR and TE, read down two). Every row can be
    tapped, and each leads with its points right against the name."""
    ctx, page, errors = open_page(browser, page_file, (1705, 1000))
    page.goto(page_file.as_uri())
    drive(page, go("digest"))
    page.wait_for_selector(".dg-rs")
    got = page.evaluate("""(() => {
      const set = document.querySelector('[data-dgset="res"]'), vis = e => e.checkVisibility({visibilityProperty: true});
      // The board's four column lefts, from its grid (the fixture fills fewer than four positions).
      const bd = document.querySelector('.dg-bd'), cs = getComputedStyle(bd), w = cs.gridTemplateColumns.split(' ').map(parseFloat);
      const col = w.map((_, i) => Math.round(bd.getBoundingClientRect().left + w.slice(0, i).reduce((a, b) => a + b, 0) + i * parseFloat(cs.columnGap)));
      const panels = [...set.querySelectorAll('.dg-tabp')].map(p => ({key: p.dataset.dgpanel, shown: vis(p),
        left: Math.round(p.getBoundingClientRect().left), width: Math.round(p.getBoundingClientRect().width),
        head: [p.querySelector('.dg-tabh').firstChild.textContent.trim(), p.querySelector('.dg-tabh b').textContent].join(' '), rows: p.querySelectorAll('.dg-rr').length}));
      const rows = [...set.querySelectorAll('.dg-rr')];
          rows.at(-1).scrollIntoView({block: 'center'});   // below the fold since Need to know took the first band
      return {bar: vis(set.querySelector('.dg-tabs')), col, panels,
              gap: Math.max(...rows.map(r => r.querySelector('.dg-rr-n').getBoundingClientRect().left - r.querySelector('.dg-rv').getBoundingClientRect().right)),
              leftCols: getComputedStyle(set.querySelector('[data-dgpanel="left"] .dg-rlist')).gridTemplateColumns.split(' ').length,
              top: document.elementFromPoint(...(r => [r.left + 8, r.top + 8])(rows.at(-1).getBoundingClientRect())) === rows.at(-1)
                   || rows.at(-1).contains(document.elementFromPoint(...(r => [r.left + 8, r.top + 8])(rows.at(-1).getBoundingClientRect())))};
    })()""")
    n = page.evaluate("(() => { const d = dgD(); return {smashed: d.smashed.length, busts: d.busts.length, left: d.left.length}; })()")
    ctx.close()
    assert errors == []
    assert not got["bar"]
    by = {p["key"]: p for p in got["panels"]}
    assert all(p["shown"] for p in got["panels"])
    assert {k: p["rows"] for k, p in by.items()} == n
    assert by["smashed"]["head"] == f"Smashed {n['smashed']}" and by["left"]["head"] == f"Left hurt {n['left']}"
    assert by["smashed"]["left"] == got["col"][0] and by["busts"]["left"] == got["col"][1] and by["left"]["left"] == got["col"][2]
    assert by["left"]["width"] > 1.8 * by["smashed"]["width"] and got["leftCols"] == 2
    assert 0 <= got["gap"] <= 24                      # the points lead, right against the name
    assert got["top"], "a row on the wall is tappable, not covered or inert"


@pytest.mark.render
def test_results_on_the_wall_keep_each_number_by_its_name(browser, page_file):
    """On a desktop the board sits in four position columns, each a heading
    over rows of name, his day and points, with no face (2026-09-29, storyboard Ms6FbdvynVPoRTKEidPGAz
    1B: "should the categories be bigger? Should we consider not using headshots?"). A board row is one column wide, so its points sit within 350px of its name at
    the 1,680px frame. A phone sets the board two positions a row."""
    got = {}
    for size in ((1705, 1000), (360, 740)):
        ctx, page, errors = open_page(browser, page_file, size)
        page.goto(page_file.as_uri())
        drive(page, go("digest"))
        if page.locator(".dg-row[data-dgrow='res'][data-open]").count() == 0:
            page.click(".dg-row[data-dgrow='res'] .dg-head")
        page.wait_for_selector(".dg-rs")
        got[size[0]] = page.evaluate("""() => {
          const cols = s => getComputedStyle(document.querySelector(s)).gridTemplateColumns.split(' ').length;
          const rows = [...document.querySelectorAll('.dg-bd-r')].map(r => {
            const n = r.querySelector('b').getBoundingClientRect(), v = r.querySelector('i').getBoundingClientRect();
            return {gap: v.left - n.left, day: getComputedStyle(r.querySelector('.dg-bd-s')).display};
          });
          const head = document.querySelector('.dg-bd-p'), name = document.querySelector('.dg-bd-r b');
          return {tiles: document.querySelectorAll('.dg-rs .dg-tiles').length, board: cols('.dg-bd'), list: cols('.dg-rlist'), rows,
                  faces: document.querySelectorAll('.dg-bd .dg-hd').length,
                  headPx: parseFloat(getComputedStyle(head).fontSize), namePx: parseFloat(getComputedStyle(name).fontSize)};
        }""")
        ctx.close()
        assert errors == []
    wall, phone = got[1705], got[360]
    # No tiles in Results since 2026-09-29: each restated a list's first row. Smashed: one column, under QB.
    assert (wall["tiles"], wall["board"], wall["list"]) == (0, 4, 1)
    assert wall["rows"] and max(r["gap"] for r in wall["rows"]) < 350
    assert {r["day"] for r in wall["rows"]} == {"block"}
    assert wall["faces"] == 0 and phone["faces"] == 0
    assert wall["headPx"] > wall["namePx"] and phone["headPx"] > phone["namePx"]   # the position leads
    assert (phone["board"], phone["list"]) == (2, 1)


@pytest.mark.render
def test_two_players_one_team_one_short_name_keep_their_first_names(browser, page_file):
    """ATL has Bijan and Brian Robinson (2026-09-29, David: "two B. Robinson on ATL ... confusing"):
    a short form two players on one team share keeps the first name; one on two teams stays short."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.goto(page_file.as_uri())
    got = page.evaluate("""() => {
      SEARCH_INDEX = [...searchIndex(),
        {n: 'Bijan Robinson', slug: 'bijan-robinson', team: 'ATL'}, {n: 'Brian Robinson Jr.', slug: 'brian-robinson', team: 'ATL'},
        {n: 'Zed Quill', slug: 'zed-quill', team: 'SF'}, {n: 'Zack Quill', slug: 'zack-quill', team: 'NYJ'}];
      DG_CLASH = null;
      return [dgShort('Bijan Robinson'), dgShort('Brian Robinson Jr.'), dgShort('Zed Quill')];
    }""")
    ctx.close()
    assert errors == []
    assert got == ["Bijan Robinson", "Brian Robinson", "Z. Quill"]


@pytest.mark.render
def test_worth_knowing_never_repeats_the_banner_or_itself(browser, page_file):
    """Worth knowing (2026-09-29, storyboard 96B1dMss6vfyhhsQLUSK4x B): one fact from each Players view,
    a tap opens that view. The banner's player is never a tile, a player is in one tile at most, and
    when the most over-performing player leads the banner, the next one takes his tile. This is the
    fallback for a build without a Highlights packet (test_highlights.py covers the packet's tiles)."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.goto(page_file.as_uri())
    got = page.evaluate("""() => {
      LIVE_HIGHLIGHTS.views.splice(0);
      const d = dgD(), over = [...LIVE_ROLE.rows].sort((a, b) => b.gap - a.gap);
      const read = dd => { const h = document.createElement('div'); h.innerHTML = dgFactsHTML(dd);
        return [...h.querySelectorAll('.dg-fact')].map(t => [t.dataset.dgfact, t.dataset.dggo]); };
      const plain = read({...d, lead: null});
      // The banner as the top score, made the top over-performer's own row.
      const star = {...d.stars[0], slug: over[0].slug, actual: 99};
      const led = read({...d, stars: [star, ...d.stars.slice(1)], lead: {rule: 'results', index: 0}});
      return {over: over.slice(0, 2).map(r => r.slug), plain, led};
    }""")
    ctx.close()
    assert errors == []
    assert got["plain"] and got["plain"][0] == [got["over"][0], "movers"]
    assert got["led"][0] == [got["over"][1], "movers"]
    for tiles in (got["plain"], got["led"]):
        slugs = [s for s, _ in tiles]
        assert len(slugs) == len(set(slugs))
        assert {v for _, v in tiles} <= {"movers", "usage", "matchups"}
    assert got["over"][0] not in [s for s, _ in got["led"]]


@pytest.mark.render
def test_the_call_picks_its_verb_from_his_day(browser, page_file):
    """Week 3's real lines (Sleeper and nflverse agree, 2026-09-29): the verb follows what his day was
    made of, the TDs ride at the end, a receiver's one throw does not make him a passer, and with no
    box line yet it says the score."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    got = page.evaluate("""() => {
      const box = (o) => ({car: 0, rush_yd: 0, rec: 0, rec_yd: 0, td: 0, cmp: null, att: null, pass_yd: null, pass_td: null, int: null, ...o});
      const call = (n, line, week, actual) => { const h = document.createElement('i'); h.innerHTML = dgCall({n, line, actual: actual || 30}, week); return h.textContent; };
      const gibbs = box({car: 20, rush_yd: 99, rec: 7, rec_yd: 65, td: 3});
      return {calls: [call('Jahmyr Gibbs', gibbs, 3),
                      call('Jaxon Smith-Njigba', box({rec: 10, rec_yd: 128, td: 2, cmp: 1, att: 1, pass_yd: 14, pass_td: 0}), 3),
                      call('Brock Purdy', box({car: 2, rush_yd: 34, cmp: 15, att: 27, pass_yd: 297, pass_td: 4}), 3),
                      call('Konata Mumpfield', box({rec: 4, rec_yd: 93, td: 1}), 3),
                      call('Kyren Williams', box({car: 9, rush_yd: 31, td: 3}), 3),
                      call('Travis Etienne Jr.', null, 3, 21.4)],
              again: call('Jahmyr Gibbs', gibbs, 3),
              weeks: [...new Set([1, 2, 3, 4, 5, 6, 7, 8].map(w => call('Jahmyr Gibbs', gibbs, w)))].length};
    }""")
    ctx.close()
    assert errors == []
    rush, rec, pas, short = (r"(rumbles for|runs wild for|bulldozes for|churns out)", r"(hauls in \d+ for|reels in \d+ for|torches them for|racks up)",
                             r"(slings|airs it out for|carves them up for|lights it up for)", r"(punches in|plunges in for|cashes in|owns the goal line:)")
    c = got["calls"]
    assert re.match(rf"^Gibbs {rush} 164 yards and 3 TDs$", c[0]), c[0]
    assert re.match(rf"^Smith-Njigba {rec} 128 yards and 2 TDs$", c[1]), c[1]      # one throw is not a passer
    assert re.match(rf"^Purdy {pas} 297 yards and 4 TDs$", c[2]), c[2]
    assert re.match(rf"^Mumpfield {rec} 93 yards and a TD$", c[3]), c[3]
    assert re.match(rf"^Williams {short} 3 TDs$", c[4]), c[4]
    assert c[5] == "Etienne scores 21.4"
    assert got["again"] == c[0] and got["weeks"] > 1        # fixed for his week, fresh across weeks


@pytest.mark.render
def test_a_finished_week_folds_the_preview_rows_into_the_wait(browser, page_file):
    """Once every game of the packet's week has kicked off (the fixture's week 3 ends with KC @ SF,
    2026-09-21), Hurt and Matchups have nothing left to preview and next week's are not written: they
    leave the ticker for one card, Blip's, with a line each (2026-09-29, storyboard
    UDoWgLMrzUHup5tX53zaue option B). Weather and Top 5 read next week's data and stay out of the wait
    since 2026-09-29 (storyboard Ms6FbdvynVPoRTKEidPGAz 5A, 6A). Hurt is Need to know since 2026-09-29,
    above the rows: with nobody hurt it says so, and once the week is over it waits on next week's report."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.goto(page_file.as_uri())
    for _, sel in go("digest"):
        page.click(sel)
    page.wait_for_selector(".dg-row")
    at = lambda when: page.evaluate("""(at) => { Date.now = () => Date.parse(at); LIVE_DIGEST.hurt = []; LIVE_DIGEST.starters = [];
      DG_CUT = null; render();
      return [...document.querySelectorAll('.dg-ticker > [data-dgrow]')].map(e => e.dataset.dgrow); }""", when)
    before = at("2026-09-20T12:00:00Z")
    assert "wait" not in before and "mu" in before and "hurt" not in before
    assert page.locator(".dg-need .dg-nd-none").inner_text() == "Nobody new is out since Tuesday."
    after = at("2026-09-22T12:00:00Z")
    assert "wait" in after and not {"hurt", "mu"} & set(after)
    assert page.locator(".dg-need .dg-nd-none").inner_text() == "Week 4's injury report is still in the trainer's room."
    card = page.locator(".dg-wait")
    assert card.locator(".dg-wait-h").inner_text().upper() == "WAITING ON WEEK 4"
    assert card.locator("svg.blip").count() == 1
    lines = {li.locator("b").inner_text().upper(): li.locator("span").inner_text() for li in card.locator("li").all()}
    assert list(lines) == ["HURT", "MATCHUPS"]
    assert lines["HURT"] == "Week 4's injury report is still in the trainer's room."
    # Blip's voice, not the record (2026-09-29, David: "say something funny ... instead of boring stats")
    jokes = page.evaluate("[t('digest.wait.mu1', {week: 4}), t('digest.wait.mu2'), t('digest.wait.mu3')]")
    assert lines["MATCHUPS"] in jokes and not re.search(r"\d\.\d", lines["MATCHUPS"])
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_every_wall_row_has_its_area(browser, page_file):
    """On a desktop the ticker is a grid of named bands, and a band set per state (wall.css). A row whose
    area the state's template lacks makes the grid invent columns for it, and every band shrinks to a
    sliver: the Starters row and the finished-week wait card landed on two branches, each passing, and
    together broke the wall (2026-09-29). So every state the fixture week reaches, from before its first
    game to after its last, and with each band that comes and goes: each row's area is in the template."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    drive(page, go("digest"))
    seen = {}
    for at in ("2026-09-10T12:00:00Z", "2026-09-14T18:00:00Z", "2026-09-17T12:00:00Z", "2026-09-18T12:00:00Z",
               "2026-09-21T20:00:00Z", "2026-09-22T00:30:00Z", "2026-09-22T12:00:00Z", "2026-09-24T12:00:00Z"):
        got = page.evaluate("""(at) => { Date.now = () => Date.parse(at); DG_CUT = null; render();
          const tk = document.querySelector('.dg-ticker'), cs = getComputedStyle(tk);
          const names = new Set(cs.gridTemplateAreas.replace(/"/g, ' ').split(/\\s+/).filter(Boolean));
          const rows = [...tk.children].filter(e => getComputedStyle(e).display !== 'none');
          return {cls: tk.className, missing: rows.map(e => [e.dataset.dgrow || e.className, getComputedStyle(e).gridRowStart])
            .filter(([, a]) => !names.has(a)), cols: cs.gridTemplateColumns.split(' ').length}; }""", at)
        seen[got["cls"]] = at
        assert got["missing"] == [], f"{at} ({got['cls']}): rows with no area in the template: {got['missing']}"
        assert got["cols"] == 12, f"{at} ({got['cls']}): {got['cols']} columns, the wall has 12"
    # The fixture week must reach the finished-week layout, or the check above never saw it.
    assert any("wk-done" in c for c in seen), seen
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_every_player_opens_his_profile(browser, page_file):
    """A lead about one player and a name in Top 5 open his profile, like every other Digest row
    (2026-09-29, David: "should we be able to click on players to open their profile?"). Top 5 took
    this from Risers & fallers, which left the Digest the same day."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    page.evaluate("Date.now = () => Date.parse('2026-09-18T12:00:00Z')")   # inside the fixture week
    drive(page, go("digest"))
    lead = page.locator(".dg-lead-go")
    assert lead.count() == 1
    slug = lead.get_attribute("data-dgslug")
    lead.click()
    assert "on" in page.locator("#modal").get_attribute("class")
    assert page.evaluate("document.querySelector('#modal .pf-orb, #modal #pf-title') !== null")
    page.keyboard.press("Escape")
    page.evaluate(EARLY)                                                   # Ranks' fixture week is ahead of it
    mover = page.locator(".dg-rk").first
    name = mover.locator(".dg-rk-t b").inner_text()
    mover.click()
    assert name.split(". ")[-1].upper() in page.locator("#pf-title").inner_text().upper()
    assert slug
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_top_5_links_to_ranks_and_one_call_is_singular(browser, page_file):
    """Top 5 is next week's projections, so it goes to Ranks, the same projections for every player
    (2026-09-29; it went to Leaders, the season's stat leaders). A lone call reads "1 call"."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    drive(page, go("digest"))
    assert page.locator('.dg-row[data-dgrow="t5"] [data-dggo]').get_attribute("data-dggo") == "ranks"
    got = page.evaluate("""() => { LIVE_DIGEST.calls = 1; LIVE_DIGEST.best = []; DG_CUT = null; render();
      return [document.querySelector('.dg-row[data-dgrow="mu"] [data-dggo]').textContent.trim(),
              document.querySelector('.dg-row[data-dgrow="mu"] .dg-s').textContent.trim()]; }""")
    assert got == ["1 take vs FantasyPros", "1 call this week"]   # Matchups became Takes, 2026-09-29
    ctx.close()
    assert errors == []


def test_every_news_line_opens_its_story(browser, page_file):
    """2026-09-30 (David: "For the news on the digest, it should link to the news source"): each line is
    a link to its story in a new tab, the story's own page when ff-jarvis kept one, else a search for the
    headline; the face and name still open the profile, and no link sits inside a button."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    page.goto(page_file.as_uri())
    for _, sel in go("digest"):
        page.click(sel)
    page.wait_for_selector(".dg-nws")
    got = page.evaluate("""() => {
      const lines = [...document.querySelectorAll('.dg-nws li')];
      const links = lines.map(li => li.querySelector('a'));
      const d = dgD(), want = d.news.map(it => it.link || 'https://www.google.com/search?tbm=nws&q=' + encodeURIComponent(it.headline));
      return {n: lines.length, all: links.every(a => a && a.target === '_blank' && /noopener/.test(a.rel)),
              hrefs: links.map(a => a.getAttribute('href')), want,
              nested: document.querySelectorAll('.dg-nws button a, .dg-nws a button').length,
              names: [...document.querySelectorAll('.dg-nw.who .dg-nw-who')].every(b => b.dataset.dgslug)}; }""")
    assert got["n"] > 0 and got["all"] and got["nested"] == 0 and got["names"]
    assert sorted(got["hrefs"]) == sorted(got["want"])
    ctx.close()
    assert errors == []


def test_need_to_know_leads_with_new_starters_then_who_sits(browser, page_file):
    """Need to know (2026-09-29, storyboard 96B1dMss6vfyhhsQLUSK4x B) lies open under the banner: Sleeper's
    new #1s and team moves first, tagged "New QB1" or "New team" with over whom (with his status), then
    the packet's out, IR and doubtful, then one line of the questionable. Five lines, then "N more".
    News no longer carries the starters, and they go with the team's kickoff."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.goto(page_file.as_uri())
    for _, sel in go("digest"):
        page.click(sel)
    page.wait_for_selector(".dg-need")
    got = page.evaluate("""() => { Date.now = () => Date.parse("2026-09-17T12:00:00Z"); DG_CUT = null; DG_NEED_ALL = false; render();
      const need = document.querySelector('.dg-need'), d = dgD(), lead = d.lead && d.lead.rule === 'hurt' ? d.hurt[d.lead.index] : null;
      const hurt = d.hurt.filter(r => r !== lead);
      // A line's second row: the tag, what happened, then " · QB21" when Ranks carries him.
      const what = s => { const c = s.cloneNode(true); c.firstElementChild.remove(); c.querySelectorAll('i').forEach(i => i.remove());
        return c.textContent.replace(/\\s*·\\s*$/, '').trim(); };
      return {tags: [...need.querySelectorAll('.dg-nd-t > span')].map(s => s.firstElementChild.textContent.trim()),
              lines: [...need.querySelectorAll('.dg-nd-t > span')].map(what),
              faces: [...need.querySelectorAll('.dg-nd')].every(b => b.firstElementChild.classList.contains('dg-hd')),
              more: (need.querySelector('.dg-nd-more') || {}).textContent || '',
              total: d.starters.length + hurt.filter(r => r.status !== 'Questionable').length,
              q: hurt.some(r => r.status === 'Questionable'), also: !!need.querySelector('.dg-q'),
              // Each questionable name is its own tap to his profile (2026-09-30).
              qTaps: [...need.querySelectorAll('.dg-q-p')].every(b => b.dataset.dgslug),
              newsStarts: document.querySelectorAll('.dg-nw.start').length}; }""")
    assert got["tags"][:4] == ["New QB1", "New QB1", "New team", "New RB1"]
    # The tag says "New QB1", so the line starts at "over" (2026-09-29); every line leads with a face.
    assert got["lines"][:4] == ["over S. Sanders", "over J. Daniels (Out)", "MIN → NYG · QB3", "over J. Mason"]
    assert got["faces"]
    assert len(got["tags"]) == min(5, got["total"])
    assert got["more"] == (f"{got['total'] - 5} more" if got["total"] > 5 else "")
    assert got["also"] == got["q"] and got["qTaps"] and got["newsStarts"] == 0
    gone = page.evaluate("""() => { LIVE_DIGEST.starters.forEach(r => { r.ko = "2026-09-20T17:00:00Z"; });
      Date.now = () => Date.parse("2026-09-20T17:01:00Z"); DG_CUT = null; render();
      return [...document.querySelectorAll('.dg-need .dg-nw-tag')].length; }""")
    assert gone == 0, "a started game takes its starters out of Need to know"
    ctx.close()
    assert errors == []


def test_a_starter_row_leaves_at_the_teams_next_kickoff_after_its_game():
    """ff-jarvis measures a row from the team's latest game (`since`); the page drops it at the next
    one, in the schedule's dialect whatever the packet's (LA is LAR there)."""
    from digest import next_kick
    assert next_kick(SCHEDULE, "LA", "2026-09-20 17:00:00") == "2026-09-28T00:20:00Z"
    assert next_kick(SCHEDULE, "LA", "2026-09-28 00:20:00") == "2026-10-04T17:00:00Z", "Monday night's trade waits for week 4"
    assert next_kick(SCHEDULE, "WAS", "2026-09-27 17:00:00") is None
    assert next_kick(None, "LA", "2026-09-20 17:00:00") is None


def test_fixture_block_is_whole():
    b = _block()
    contract.validate("LIVE_DIGEST", b)
    assert b["week"] == 3 and b["lead"] == {"rule": "hurt", "index": 0}
    assert [len(b[k]) for k in ("hurt", "best", "wx", "adds", "top5", "up", "down", "gems", "news")] == \
        [12, 4, 1, 6, 20, 5, 5, 5, 10]


def test_kickoffs_are_pacific_words():
    b = _block()
    assert b["hurt"][0]["game"] == {"away": "LA", "home": "DEN", "kick": "Sun 5:20 PM",   # 00:20 UTC Monday
                                    "ko": "2026-09-28T00:20:00Z"}
    assert b["wx"][0]["kick"] == "Sun 10:00 AM"
    assert b["hurt"][4]["game"] is None                                                    # Dart, on IR


def test_best_spots_keep_position_order_and_slugs():
    b = _block()
    assert [(r["pos"], r["n"]) for r in b["best"]] == [
        ("QB", "C.J. Stroud"), ("RB", "Quinshon Judkins"), ("WR", "CeeDee Lamb"), ("TE", "Pat Freiermuth")]
    assert b["best"][2]["slug"] == slugify("CeeDee Lamb") and b["best"][2]["home"] is True


def test_headline_splits_at_its_tag_and_takes_a_news_kind():
    news = _block()["news"]
    assert news[0]["n"] == "Jaylen Wright" and news[0]["rest"] == "doubtful to play Sunday"
    assert news[0]["when"] == "8:31 AM" and news[0]["kind"] == "injury"
    assert news[7]["kind"] == "out"                         # "Josh Simmons (back) ruled out for Sunday"
    assert news[0]["slugs"][0] == "jaylen-wright"


def test_tonight_carries_the_card_facts_with_slugs_and_kickoff():
    b = _block()
    assert b["tonight_last"] is True
    g = b["tonight"][0]
    assert (g["away"], g["home"], g["kick"], g["ko"]) == ("PHI", "CHI", "Mon 5:15 PM", "2026-09-29T00:15:00Z")
    assert g["wx"] == {"roof": "outdoor", "temp_f": 64, "wind_mph": 5, "precip_pct": 1, "short": "Mostly Clear"}
    assert [(r["n"], r["status"], r["injury"]) for r in g["out"]][0] == ("Caleb Williams", "Out", "Hamstring")
    assert g["next_up"][0]["for"] == "Caleb Williams" and g["next_up"][0]["n"] == "Case Keenum"
    assert {"team": "CHI", "group": "pass", "d_pts": -9.8} in g["groups"]
    assert [r["call"] for r in g["tcalls"]] == ["BEST", "BEST", "START"]
    assert g["projected"][0]["slug"] == slugify("Jalen Hurts") and g["moved"][0]["d_pts"] == -3.97
    assert live_digest({**load_digest(), "tonight": {"games": [], "last": False}}, slugify)["tonight"] == []


@pytest.mark.render
def test_monday_night_is_one_card_and_the_preview_rows_go(browser, page_file):
    """Monday 6 AM Pacific, PHI @ CHI tonight and all the week has left: the card says who is out and
    what the books moved, its rows leave the ticker, and the five preview rows go (2026-09-28)."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.goto(page_file.as_uri())
    page.evaluate('Date.now = () => Date.parse("2026-09-28T13:00:00Z")')
    for _, sel in go("digest"):
        page.click(sel)
    page.wait_for_selector(".dg-tn")
    story = page.locator(".dg-tn-story").inner_text()
    assert story.startswith("Caleb Williams is out (hamstring). Case Keenum is CHI's projected QB.")
    assert "CHI's pass catchers −9.8 combined: C. Loveland −4.0, L. Burden −3.2, R. Odunze −1.7." in story
    assert story.endswith("PHI is flat (+0.3).")
    rows = page.evaluate("[...document.querySelectorAll('.dg-row')].map(r => r.dataset.dgrow)")
    assert not {"hurt", "mu", "wx", "t5", "st"} & set(rows) and "adds" in rows
    # After kickoff the card is one line and the way to the live board.
    page.evaluate('Date.now = () => Date.parse("2026-09-29T00:30:00Z"); DG_CUT = null; render()')
    assert page.locator(".dg-tn.on [data-dggo='live']").count() == 1
    assert errors == []
    ctx.close()


SLEEPER_ADDS = {"source": "sleeper", "hours": 24, "fetched": "2026-09-28 05:52", "weeks": [], "rows": [
    {"key": "ollie gordon", "name": "Ollie Gordon II", "pos": "RB", "team": "MIA", "count": 4039301,
     "was": None, "now": None, "delta": None},
    {"key": "kenyon sadiq", "name": "Kenyon Sadiq", "pos": "TE", "team": "NYJ", "count": 832977,
     "was": None, "now": 35.2, "delta": None}]}


def test_sleeper_adds_carry_their_source_and_count():
    b = live_digest({**load_digest(), "adds": SLEEPER_ADDS}, slugify)
    contract.validate("LIVE_DIGEST", b)
    assert (b["adds_source"], b["adds_hours"], b["adds_weeks"]) == ("sleeper", 24, [])
    assert [(r["n"], r["count"], r["now"]) for r in b["adds"]] == [("Ollie Gordon II", 4039301, None),
                                                                  ("Kenyon Sadiq", 832977, 35.2)]
    # A packet from before 2026-09-28 has no source: it was the ESPN cut.
    old = {**load_digest(), "adds": {"weeks": [2, 3], "rows": []}}
    assert live_digest(old, slugify)["adds_source"] == "espn"


@pytest.mark.render
def test_sleeper_adds_read_as_counts_on_the_digest(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.goto(page_file.as_uri())
    page.evaluate("""Object.assign(LIVE_DIGEST, {adds_source: "sleeper", adds_hours: 24, adds_weeks: [], adds: [
        {n: "Ollie Gordon II", slug: "ollie-gordon-ii", pos: "RB", team: "MIA", count: 4039301, was: null, now: null, delta: null},
        {n: "Kenyon Sadiq", slug: "kenyon-sadiq", pos: "TE", team: "NYJ", count: 832977, was: null, now: 35.2, delta: null}]});
        DG_CUT = null; Date.now = () => Date.parse("2026-09-22T12:00:00Z")""")   # a Tuesday: adds lies open
    for _, sel in go("digest"):
        page.click(sel)
    page.wait_for_selector(".dg-row[data-dgrow='adds']")
    row = page.locator(".dg-row[data-dgrow='adds']")
    assert row.locator(".dg-n").inner_text() == "4.0M"
    assert row.locator(".dg-s").inner_text() == "Ollie Gordon II 4.0M adds"
    assert "Sleeper trending" in row.locator(".dg-foot").inner_text()
    assert row.locator(".dg-plus").all_inner_texts() == ["4.0M", "833K"]
    assert errors == []
    ctx.close()


def test_an_untagged_headline_does_not_say_his_name_twice():
    """The Monday 2026-09-28 page read "Travis Etienne Travis Etienne Jr. exits early Sunday"."""
    p = json.loads(json.dumps(load_digest()))
    p["news"] = [{"created": "2026-09-27 20:47:00", "headline": "Travis Etienne Jr. exits early Sunday",
                  "key": "travis etienne", "name": "Travis Etienne"}]
    it = live_digest(p, slugify)["news"][0]
    assert (it["n"], it["rest"]) == ("Travis Etienne", "exits early Sunday")


def test_top5_flattens_by_position():
    top5 = _block()["top5"]
    assert [r["pos"] for r in top5[::5]] == ["QB", "RB", "WR", "TE"]
    assert top5[0]["n"] == "Josh Allen"


def test_empty_sections_are_empty_lists_not_errors():
    p = json.loads(json.dumps(load_digest()))
    p.update(lead=None, hurt=[], news=[], gems=[], top5={}, stock={"up": [], "down": []},
             adds={"weeks": [2, 3], "rows": []}, weather={"games": [], "near": None},
             matchups={"calls": 0, "best": {}, "record": None})
    b = live_digest(p, slugify)
    contract.validate("LIVE_DIGEST", b)
    assert b["lead"] is None and b["near"] is None and b["best"] == [] and b["record"] is None


@pytest.mark.render
def test_a_started_game_drops_its_rows_live_and_the_lead_gives_way(browser, page_file):
    """The Friday packet read on Monday morning: nothing about a Sunday game survives in the
    browser, the lead falls to the week's results, and the stamp says how old the packet is."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.goto(page_file.as_uri())
    page.evaluate('Date.now = () => Date.parse("2026-09-28T13:00:00Z")')   # after load: the page pins its own
    for _, sel in go("digest"):
        page.click(sel)
    page.wait_for_selector(".dg-row")
    # the week's top score, called like a game on his box line, washed in his team's colour
    assert re.match(r"^Allen (slings|airs it out for|carves them up for|lights it up for) 204 yards and 2 TDs$",
                    page.locator(".dg-lead-h").inner_text())
    assert page.locator(".dg-lead .dg-lpill").all_inner_texts() == ["24.6 pts", "16/26 · 204 yds", "8 car · 22 yds"]
    assert "--team:#00338d" in page.locator(".dg-lead").get_attribute("style")
    assert page.locator(".dg-lead .dg-ghost").inner_text() == "BUF"
    assert page.locator(".dg-lead-when").inner_text() == "Week 3 · updated Fri 10:40 PM"
    assert page.locator(".dg-row[data-dgrow='res'][data-open]").count() == 1
    left = page.evaluate("dgD().hurt.map(r => r.game && r.game.away + '@' + r.game.home)")
    assert "LA@DEN" not in left
    # The fixture schedule holds one week-3 game, so give one top-5 row a Sunday kickoff by hand.
    n = page.evaluate("dgD().top5.length")
    page.evaluate("LIVE_DIGEST.top5.find(r => !r.ko).ko = '2026-09-27T17:00:00Z'; DG_CUT = null")
    assert page.evaluate("dgD().top5.length") == n - 1
    assert page.locator(".dg-row[data-dgrow='res'] .dg-foot").inner_text().startswith("1 game final, 2 to play.")
    assert errors == []
    ctx.close()


def test_no_packet_is_no_block():
    assert live_digest(None, slugify) is None
    contract.validate("LIVE_DIGEST", None)
    assert "no weekly_digest.json" in report(None)


@pytest.mark.render
def test_the_wall_opens_every_panel_and_a_head_is_not_a_toggle(browser, page_file):
    """From 1100px the Digest is a wall (2026-09-26): every topic open, the day's row marked, the
    lead's ghost naming why he leads. A tap on a panel's head must not close it."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    page.goto(page_file.as_uri() + "#digest")
    page.wait_for_selector(".dg-row")
    rows = page.locator(".dg-row:not(.empty)")
    assert rows.count() == page.locator(".dg-row[data-open]").count() > 0
    page.locator(".dg-row[data-dgrow='adds'] .dg-head").click()
    assert page.locator(".dg-row[data-dgrow='adds'][data-open]").count() == 1
    assert page.locator(".dg-ghost").inner_text() == "WR2"
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert errors == []
    ctx.close()


# The clock before the fixture's first ranked kickoff, so every Ranks row is still ahead of it.
EARLY = """(() => { const ks = LIVE_RANKS.rows.map(r => Date.parse(r.kick)).filter(Boolean);
  const at = Math.min(...ks) - 3600e3; Date.now = () => at; DG_CUT = null; render(); return at; })()"""


@pytest.mark.render
def test_top_5_is_ranks_own_rows_under_position_tabs(browser, page_file):
    """2026-09-29, storyboard Ms6FbdvynVPoRTKEidPGAz 5A (David: "it's supposed to be forward looking ...
    like a mini feed of our rankings"): Top 5 reads LIVE_RANKS, the rows Ranks draws, never the packet,
    so the two cannot disagree. A tab per position and FLEX, five rows each, a tap swaps them."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.goto(page_file.as_uri())
    drive(page, go("digest"))
    page.wait_for_selector(".dg-row")
    page.evaluate(EARLY)
    page.click(".dg-row[data-dgrow='t5'] .dg-head")
    want = page.evaluate("""Object.fromEntries(DG_T5_POS.map(p => [p, rkList(p).slice(0, 5).map(r => r.slug)])
      .filter(([, s]) => s.length))""")
    tabs = page.locator("[data-dgset='t5'] .dg-tab")
    assert [tabs.nth(i).inner_text() for i in range(tabs.count())] == list(want)
    for i, pos in enumerate(want):
        tabs.nth(i).click()
        shown = page.locator(f"[data-dgset='t5'] [data-dgpanel='{pos}']:not([data-off]) .dg-rk")
        assert shown.evaluate_all("els => els.map(e => e.dataset.dgslug)") == want[pos], pos
    first = page.evaluate("rkList('QB')[0].pts.toFixed(1)")
    tabs.first.click()
    assert page.locator("[data-dgpanel='QB'] .dg-rk .dg-rk-p").first.inner_text() == first
    assert page.locator(".dg-row[data-dgrow='t5'] .dg-go").get_attribute("data-dggo") == "ranks"
    # Tiers in Ranks' colours (2026-09-29, David: "colors for T1, T2, T3 so it's easily scannable"):
    # Tier 1 filled lime, a lower tier an outline, a different colour per tier.
    tiers = page.evaluate("""(() => { const p = document.querySelector('[data-dgset="t5"] [data-dgpanel]:not([data-off])');
      return [...p.querySelectorAll('.dg-rk-tier')].map(e => [e.textContent, getComputedStyle(e).backgroundColor, getComputedStyle(e).color]); })()""")
    lime = page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--lime-rgb').trim().split(/\\s+/).join(', ')")
    assert all(bg == f"rgb({lime})" for name, bg, _ in tiers if name == "T1")
    colours = {name: c for name, _, c in tiers if name != "T1"}
    assert len(set(colours.values())) == len(colours)
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_start_of_the_week_heads_the_matchups_card(browser, page_file):
    """2026-10-03, David: yes to a Start of the week: our most confident START (graded, backed,
    widest gap), first in the Matchups card, ours / FantasyPros on the right. None: no row."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.goto(page_file.as_uri())
    drive(page, go("digest"))
    page.wait_for_selector(".dg-row")
    page.evaluate("""(() => { LIVE_STARTSIT.calls.forEach((r, i) => { r.backed = true; r.graded = true; r.gap = i; });
      const s = LIVE_STARTSIT.calls.filter(r => r.tag === 'start'); s[s.length - 1].gap = 50; s[0].gap = 99; s[0].backed = false;
      DG_CUT = null; render(); })()""")
    want = page.evaluate("""(() => { const s = LIVE_STARTSIT.calls.filter(r => r.tag === 'start'); return s[s.length - 1]; })()""")
    row = page.locator(".dg-row[data-dgrow='mu']")
    if row.locator(".dg-head").count():
        row.locator(".dg-head").click()
    first = row.locator(".dg-ln").first
    assert first.locator(".dg-sotw").inner_text() == "Start of the week"
    assert first.get_attribute("data-dgslug") == want["slug"]
    assert first.locator(".dg-ln-r").inner_text() == f"{want['rank']} / {want['ecr'] if want['ecr'] is not None else '—'}"
    page.evaluate("LIVE_STARTSIT.calls.forEach(r => { r.backed = false; }); DG_CUT = null; render()")
    assert page.locator(".dg-sotw").count() == 0
    assert not errors
    ctx.close()


@pytest.mark.render
def test_weather_is_the_weather_tabs_own_games(browser, page_file):
    """2026-09-29, 6A (David: "the next tab over is the weather and it's actually already live"): the
    row counts the games the Weather view says move scoring (wtRows().moves, still to kick off) and
    links there. A calm week draws no row on a phone and one quiet sentence on the wall."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.goto(page_file.as_uri())
    drive(page, go("digest"))
    page.wait_for_selector(".dg-row")
    page.evaluate(EARLY)
    page.evaluate("""(() => { const g = LIVE_SCHEDULE.games.find(x => Date.parse(x.kickoff) > Date.now());
      wtRows = () => ({week: 4, moves: [{g, done: false, conds: ['precip'], effects: [{pos: 'WR', pts: -0.5}],
        fc: {precip_pct: 60, temp_f: 65}, mph: 6}], indoor: [], open: []}); DG_CUT = null; render(); })()""")
    row = page.locator(".dg-row[data-dgrow='wx']")
    assert row.locator(".dg-n").inner_text() == "1"
    assert row.locator(".dg-s").inner_text() == "Rain in 1 game"
    row.locator(".dg-head").click()
    assert row.locator(".dg-wx").count() == 1 and row.locator(".dg-wx .dg-ln-r").inner_text() == "60%"
    assert row.locator(".dg-go").get_attribute("data-dggo") == "weather"
    page.evaluate("wtRows = () => ({week: 4, moves: [], indoor: [], open: []}); DG_CUT = null; render()")
    assert page.locator(".dg-row[data-dgrow='wx']").evaluate("e => getComputedStyle(e).display") == "none"
    page.set_viewport_size({"width": 1400, "height": 900})
    calm = page.locator(".dg-row[data-dgrow='wx']")
    assert calm.evaluate("e => getComputedStyle(e).display") != "none"
    assert calm.locator(".dg-s").inner_text() == "No game's weather moves scoring"
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_every_topic_label_carries_its_icon(browser, page_file):
    """2026-09-29, 3A: a drawn icon beside every topic's label, stroked in the label's own colour."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.goto(page_file.as_uri())
    drive(page, go("digest"))
    page.wait_for_selector(".dg-row")
    got = page.evaluate("""[...document.querySelectorAll('.dg-row')].map(r => {
      const l = r.querySelector('.dg-l'), i = l.querySelector('svg.dg-lico');
      return [r.dataset.dgrow, !!i && getComputedStyle(i).stroke === getComputedStyle(l).color];
    })""")
    assert got and all(ok for _, ok in got), got
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_a_headline_naming_no_player_keeps_the_digest_up(browser, page_file):
    """2026-09-29, David: "the digest is broken". A defender's IR move came through with a slug and no
    name; News keyed a block to the slug, avatarHTML read the missing name, and the throw blanked the
    whole Digest. A headline naming no player is a plain block of its own, whatever it carries."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
    page.goto(page_file.as_uri())
    drive(page, go("digest"))
    page.wait_for_selector(".dg-row")
    got = page.evaluate("""(() => {
      LIVE_DIGEST.news = [{n: null, rest: null, headline: 'Jalen Davis placed on IR', slugs: ['jalen-davis'], when: '9:08 PM', kind: 'out'},
                          ...LIVE_DIGEST.news];
      DG_CUT = null; render();
      const row = document.querySelector('.dg-row[data-dgrow="news"]');
      const first = row && [...row.querySelectorAll('.dg-nw')].find(b => b.textContent.includes('Jalen Davis'));
      return {rows: document.querySelectorAll('.dg-row').length, tag: first && first.tagName,
              text: first && first.textContent.trim()}; })()""")
    ctx.close()
    assert errors == []
    assert got["rows"] > 0
    assert got["tag"] == "DIV" and "Jalen Davis placed on IR" in got["text"]   # a plain block, not a profile button


# ---- the Digest after kickoff (2026-10-04, storyboard JrM6hBMrAL2hjFzYPgKitV) ----

from test_render import LIVE_PLANT  # noqa: E402

SUN, MON = "2026-10-04T12:00:00Z", "2026-10-05T15:00:00Z"


def _scorer(n, pos, team, pts, **s):
    return {"n": n, "pos": pos, "team": team, "pts": pts, "s": s}


# Seven scorers, league-wide, as GD_STATS.lead (api/stats.py lead=1); five have TDs worth counting.
LEAD = {
    "7547": _scorer("Amon-Ra St. Brown", "WR", "DET", 31.4, rec=10, rec_tgt=12, rec_yd=180, rec_td=2),
    "9226": _scorer("De'Von Achane", "RB", "MIA", 27.1, rush_att=18, rush_yd=130, rush_td=1, rec=4, rec_tgt=5, rec_yd=40),
    "8183": _scorer("Brock Purdy", "QB", "SF", 24.0, pass_cmp=22, pass_att=30, pass_yd=290, pass_td=3),
    "12481": _scorer("Cam Skattebo", "RB", "NYG", 19.2, rush_att=20, rush_yd=90, rush_td=2),
    "6801": _scorer("Tee Higgins", "WR", "CIN", 17.8, rec=6, rec_tgt=8, rec_yd=98),
    "4217": _scorer("George Kittle", "TE", "SF", 15.5, rec=6, rec_tgt=7, rec_yd=85, rec_td=1),
    "12526": _scorer("Tetairoa McMillan", "WR", "CAR", 12.0, rec=5, rec_tgt=7, rec_yd=70),
}

# Plants week 2 of both leagues (tests/fixtures/gameday.json), keeps the ESPN one, and gives every club
# a game: Sunday's, or the Monday pair `mon` ([home, away]). cfg: at, sunState, monState, mon, lead, stats, clock.
PLANT_WEEK = """(cfg) => {
  PLANT
  GD.leagues.splice(1);
  const lineup = Object.values(GD.leagues[0].teams).flatMap(tm => tm.lineup.map(r => r.team));
  const clubs = [...new Set(lineup)].filter(c => !cfg.mon.includes(c));
  const games = clubs.map(c => ({home: c, away: 'O' + c, kickoff: cfg.sun, week: 2}));
  if (cfg.mon.length) games.push({home: cfg.mon[0], away: cfg.mon[1], kickoff: cfg.monKick, week: 2});
  GD_GAMES.splice(0, GD_GAMES.length, ...games);
  Date.now = () => Date.parse(cfg.at);
  GD_STATS.games = {};
  for (const g of games) for (const c of [g.home, g.away]) GD_STATS.games[c] = cfg.mon.includes(c) ? cfg.monState : cfg.sunState;
  GD_STATS.lead = cfg.lead;
  Object.assign(GD_STATS.stats, cfg.stats || {});
  GD_AT = Date.now(); GD_CLOCK = cfg.clock || {};
  if (cfg.noHurt) { LIVE_DIGEST.hurt = []; LIVE_DIGEST.starters = []; }
  DG_CUT = null; render();
}""".replace("PLANT", LIVE_PLANT())


def _live_cfg(**over):
    cfg = {"at": "2026-10-04T14:00:00Z", "sun": SUN, "monKick": MON, "mon": [], "sunState": "in_game",
           "monState": "pre_game", "lead": LEAD, "stats": {}, "clock": {}, "noHurt": False}
    cfg.update(over)
    return cfg


def _digest_page(browser, page_file, viewport=(390, 844)):
    ctx, page, errors = open_page(browser, page_file, viewport)
    drive(page, go("digest"))
    page.wait_for_selector(".dg")
    return ctx, page, errors


@pytest.mark.render
def test_during_a_game_the_headline_is_the_top_score_and_right_now_lists_five(browser, page_file):
    """David, 2026-10-04: "Sometimes something big happens like injury or top scores. The headline should
    change accordingly. Need to know and Highlights become old news on kickoff." With a game on, the banner
    names the top scorer in GD_STATS.lead and says where his game is; Highlights becomes Right now, the top
    five and a touchdown count that opens Live's TDs tab; Need to know, with nothing left in it, is gone."""
    ctx, page, errors = _digest_page(browser, page_file)
    page.evaluate(PLANT_WEEK, _live_cfg(noHurt=True, clock={"DET": {"state": "in", "q": 3, "clock": "4:12", "half": False, "detail": "", "clubs": ["DET"]}}))
    assert page.locator(".dg-lead-h").inner_text() == "St. Brown has 31.4 points"
    fact = page.locator(".dg-lead-fact").inner_text()
    assert "180 yds" in fact and fact.endswith("Q3 4:12")
    now = page.locator("[data-dgnow]")
    assert now.locator(".dg-sec").text_content() == "Right now"
    assert page.locator(".dg-facts").count() == 1                    # Right now stands where Highlights did
    rows = now.locator(".dg-now-r")
    assert rows.count() == 5
    first = rows.first.inner_text().replace("\n", " ")
    assert "A. St. Brown" in first and "WR" in first and "DET" in first and "Q3 4:12" in first and "31.4" in first
    assert [rows.nth(i).locator(".dg-now-p").inner_text() for i in range(5)] == ["31.4", "27.1", "24.0", "19.2", "17.8"]
    tds = sum(int(v["s"].get("rush_td", 0)) + int(v["s"].get("rec_td", 0)) for v in LEAD.values())
    assert now.locator(".dg-now-td").inner_text() == f"{tds} touchdowns so far"
    assert page.locator(".dg-need").count() == 0 and "no-need" in page.locator(".dg-ticker").get_attribute("class")
    # A scorer opens his profile; the count opens Live's TDs tab.
    rows.first.click()
    assert "on" in page.locator("#modal").get_attribute("class")
    page.keyboard.press("Escape")
    page.locator(".dg-now-td").click()
    assert page.evaluate("localStorage.getItem('tw-live-tab')") == "tds"
    assert page.evaluate("location.hash") == "#live"
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_a_poll_repaints_the_headline_in_place(browser, page_file):
    """paintDigestLive swaps the banner and Right now when their words change and never rebuilds the page
    under a thumb; off the Digest it does nothing."""
    ctx, page, errors = _digest_page(browser, page_file)
    page.evaluate(PLANT_WEEK, _live_cfg())
    got = page.evaluate("""() => {
      const root = document.querySelector('.dg'); root.dataset.keep = '1';
      GD_STATS.lead['9226'].pts = 40.2; paintDigestLive();
      const kept = document.querySelector('.dg').dataset.keep === '1';
      const head = document.querySelector('.dg-lead-h').textContent;
      const rows = [...document.querySelectorAll('.dg-now-p')].map(e => e.textContent);
      SURFACE = 'ranks'; GD_STATS.lead['9226'].pts = 1.0; paintDigestLive(); SURFACE = 'digest';
      return {kept, head, rows, still: document.querySelector('.dg-lead-h').textContent}; }""")
    ctx.close()
    assert errors == []
    assert got["kept"] and got["head"] == "Achane has 40.2 points"
    assert got["rows"][0] == "40.2" and got["still"] == got["head"]


@pytest.mark.render
def test_before_the_first_kickoff_the_digest_is_unchanged(browser, page_file):
    """Nothing about the week's live data may change the Digest until a game starts."""
    ctx, page, errors = _digest_page(browser, page_file)
    page.evaluate(PLANT_WEEK, _live_cfg(at="2026-10-04T08:00:00Z", sunState="pre_game"))
    drawn = page.evaluate("document.querySelector('.dg').outerHTML")
    assert page.locator("[data-dgnow], [data-dgmnf]").count() == 0
    head = page.locator(".dg-lead-h").inner_text()
    assert "going into" not in head and "points" not in head
    page.evaluate("(() => { GD_STATS.lead = {}; DG_CUT = null; render(); })()")
    assert page.evaluate("document.querySelector('.dg').outerHTML") == drawn
    ctx.close()
    assert errors == []


def _gap(page):
    return page.evaluate("""() => { const lg = GD.leagues[0], g = lg.games.find(x => x.includes(lg.me));
      const a = gdSide(lg, lg.me, GD_STATS.stats, GD_STATS.games), b = gdSide(lg, g[0] === lg.me ? g[1] : g[0], GD_STATS.stats, GD_STATS.games);
      return Math.round((a.total - b.total) * 100) / 100; }""")


@pytest.mark.render
def test_the_last_game_is_its_own_card_and_the_headline_goes_into_it(browser, page_file):
    """Every game but the Monday one is final: a card above the ticker holds my matchup in each league,
    who is left on each side with their projections, and what the game needs. The banner reads "You're
    up 1.6 going into Monday night". During the game the card stays and the banner is the top score."""
    ctx, page, errors = _digest_page(browser, page_file)
    n = lambda v: page.evaluate("v => dgN1(Math.abs(v))", v)      # the page's own rounding, not Python's
    # Colston Loveland (theirs) plays Monday, none of my starters: ahead, "stay under".
    page.evaluate(PLANT_WEEK, _live_cfg(at="2026-10-05T09:00:00Z", sunState="complete", mon=["CHI", "DEN"],
                                         stats={"4217": {"rec": 5, "rec_yd": 600}}))
    gap = _gap(page)
    assert gap > 0
    assert page.locator(".dg-lead-h").inner_text() == f"You're up {n(gap)} going into Monday night"
    card = page.locator(".dg-mnf")
    assert card.count() == 1 and "has-tn" in page.locator(".dg-ticker").get_attribute("class")
    # The title is one line; the time and the game sit on a small second line (2026-10-04, 360px).
    head = re.sub(r"\s+", " ", card.locator(".dg-mnf-h").inner_text()).strip()
    assert re.fullmatch(r"Monday night \d{1,2}:\d\d [AP]M · DEN @ CHI", head)
    assert card.locator(".dg-mnf-h b").bounding_box()["y"] < card.locator(".dg-mnf-sub").bounding_box()["y"]
    assert card.locator(".dg-mnf-lead").inner_text() == f"UP {n(gap)}"
    assert card.locator(".dg-mnf-say").inner_text() == f"To win, C. Loveland must score under {n(gap)}"
    assert card.locator(".dg-mnf-lg.done").count() == 0                              # someone is left: the full block
    assert page.locator(".dg-lead-fact").inner_text() == card.locator(".dg-mnf-say").inner_text()
    assert card.locator(".dg-mnf-c").nth(1).locator(".dg-mnf-p").count() == 1       # theirs: one man to play
    assert card.locator(".dg-mnf-c").nth(0).inner_text().endswith("Nobody left")     # mine: none
    assert card.locator(".dg-mnf-med").count() == 1                                   # the ESPN league has a median
    assert page.locator("[data-dgnow]").count() == 1
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    # Down, with one of mine (Cam Skattebo) still to play and none of theirs: "You need".
    page.evaluate(PLANT_WEEK, _live_cfg(at="2026-10-05T09:00:00Z", sunState="complete", mon=["NYG", "DAL"],
                                         stats={"9488": {"rec": 5, "rec_yd": 3000}}))
    gap = _gap(page)
    assert gap < 0
    assert page.locator(".dg-lead-h").inner_text() == f"You're down {n(gap)} going into Monday night"
    assert page.locator(".dg-mnf-lead").inner_text() == f"DOWN {n(gap)}"
    assert page.locator(".dg-mnf-say").inner_text() == f"You need {n(gap)} from C. Skattebo"
    # The game is on: the card stays, with its clock, and the top scorer has the banner back.
    page.evaluate(PLANT_WEEK, _live_cfg(at="2026-10-05T15:30:00Z", sunState="complete", monState="in_game", mon=["NYG", "DAL"]))
    assert page.locator(".dg-mnf").count() == 1
    assert "going into" not in page.locator(".dg-lead-h").inner_text()
    assert page.locator(".dg-mnf-h time").inner_text() == "Live"
    page.set_viewport_size({"width": 1400, "height": 900})
    assert page.locator(".dg-mnf").bounding_box()["width"] > 600
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    ctx.close()
    assert errors == []


# Three games on the last day make it the main slate, not the standalone last game: no card, and the
# packet's own lead stands between windows.
EXTRA_LATE = """() => {
  for (const [h, a] of [['XA', 'XB'], ['XC', 'XD']]) GD_GAMES.push({home: h, away: a, kickoff: GD_GAMES[GD_GAMES.length - 1].kickoff, week: 2});
  const h = LIVE_DIGEST.hurt[0];
  h.game = {away: 'XA', home: 'XB', ko: '2026-10-06T00:30:00Z', kick: 'Mon 5:15 PM'};
  LIVE_DIGEST.lead = {rule: 'hurt', index: 0};
  DG_CUT = null; render();
}"""
BANNER_AT = """([at, state]) => {
  Date.now = () => Date.parse(at);
  for (const g of GD_GAMES) if (['NYG', 'DAL', 'XA', 'XB', 'XC', 'XD'].includes(g.home)) GD_STATS.games[g.home] = GD_STATS.games[g.away] = state;
  paintDigestLive();
}"""


def _tap_banner(page):
    page.locator(".dg-lead-go").click()
    page.wait_for_selector("#modal.on")
    page.keyboard.press("Escape")
    page.wait_for_selector("#modal.on", state="detached")


@pytest.mark.render
def test_the_banner_opens_its_player_after_swapping_between_the_packets_lead_and_a_live_one(browser, page_file):
    """The band is a data-dgslug button (wired once, when the page renders) or a data-dglv one (the page's
    one listener). Between windows the packet's hurt lead stands; once a game is on the top scorer takes
    it. The swap must render again, or the button swapped in is dead."""
    ctx, page, errors = _digest_page(browser, page_file)
    page.evaluate(PLANT_WEEK, _live_cfg(at="2026-10-05T09:00:00Z", sunState="complete", mon=["NYG", "DAL"]))
    page.evaluate(EXTRA_LATE)
    assert page.locator(".dg-lead-go[data-dgslug]").count() == 1 and page.locator(".dg-mnf").count() == 0
    _tap_banner(page)
    page.evaluate(BANNER_AT, ["2026-10-05T15:30:00Z", "in_game"])
    assert page.locator(".dg-lead-go[data-dglv]").count() == 1 and "points" in page.locator(".dg-lead-h").inner_text()
    _tap_banner(page)
    page.evaluate(BANNER_AT, ["2026-10-05T09:00:00Z", "pre_game"])
    assert page.locator(".dg-lead-go[data-dgslug]").count() == 1 and "points" not in page.locator(".dg-lead-h").inner_text()
    _tap_banner(page)
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_the_tds_link_opens_lives_tds_tab_even_when_storage_throws(browser, page_file):
    ctx, page, errors = _digest_page(browser, page_file)
    page.evaluate(PLANT_WEEK, _live_cfg(noHurt=True))
    page.evaluate("() => { const no = () => { throw new Error('blocked'); }; Storage.prototype.setItem = no; Storage.prototype.getItem = no; }")
    page.locator(".dg-now-td").click()
    assert page.evaluate("location.hash") == "#live"
    assert page.evaluate("gdTab()") == "tds"
    ctx.close()
    assert errors == []


def test_the_digests_data_layer_calls_no_surface_function():
    """model -> contract -> view: data/digest.js (dgWaiting reads the last game's slot) names nothing
    that surface/digest/ declares, so it works with the surface files gone."""
    src = pathlib.Path(__file__).resolve().parents[1] / "design" / "src" / "js"
    data = (src / "data" / "digest.js").read_text(encoding="utf-8")
    declared = set()
    for f in (src / "surface" / "digest").glob("*.js"):
        declared |= set(re.findall(r"^(?:function|const|let)\s+([A-Za-z_]\w*)", f.read_text(encoding="utf-8"), re.M))
    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", data, flags=re.S)
    leaked = sorted(n for n in declared if re.search(rf"(?<![\w.]){n}\b", code)
                    and not re.search(rf"^(?:function|const|let)\s+{n}\b", code, re.M))
    assert leaked == []
    assert "function dgMnfSlot" in data and "function dgWeek" in data


@pytest.mark.render
def test_a_league_with_nobody_left_is_one_line_and_one_with_a_player_left_is_the_block(browser, page_file):
    """Monday's card (360px): a decided league collapses to its name, the score and won or lost (plus the
    median gap); the full block is only for a league with someone still to play. A long team name ends in
    an ellipsis and the title stays on one line."""
    ctx, page, errors = _digest_page(browser, page_file, viewport=(360, 800))
    # Neither side has anyone in the late game (two clubs no lineup holds): decided.
    page.evaluate(PLANT_WEEK, _live_cfg(at="2026-10-05T09:00:00Z", sunState="complete", mon=["ZZA", "ZZB"]))
    gap = _gap(page)
    card = page.locator(".dg-mnf")
    assert card.count() == 1
    done = card.locator(".dg-mnf-lg")
    assert done.count() == 1 and "done" in done.get_attribute("class")
    assert card.locator(".dg-mnf-c, .dg-mnf-say, .dg-mnf-score").count() == 0
    text = done.inner_text().replace("\n", " ")
    assert re.search(r"\d+\.\d – \d+\.\d", text) and ("won" in text if gap > 0 else "lost" in text)
    assert done.locator(".dg-mnf-med").count() == 1                                    # the ESPN league has a median
    assert done.bounding_box()["height"] < 70
    # Someone is left on a side, and the team names are long: the full block, ellipsized, inside the card.
    page.evaluate(PLANT_WEEK, _live_cfg(at="2026-10-05T09:00:00Z", sunState="complete", mon=["CHI", "DEN"],
                                         stats={"4217": {"rec": 5, "rec_yd": 600}}))
    page.evaluate("""() => { for (const tm of Object.values(GD.leagues[0].teams)) tm.name = '\\u{1F3C8} The Very Long Team Name That Will Not Fit \\u{1F3C6}';
      DG_CUT = null; render(); }""")
    assert page.locator(".dg-mnf-lg:not(.done)").count() == 1 and page.locator(".dg-mnf-c").count() == 2
    box = page.locator(".dg-mnf").bounding_box()
    names = page.locator(".dg-mnf-score .dg-mnf-nm")
    assert names.count() == 2
    for i in range(2):
        b = names.nth(i).bounding_box()
        assert b["x"] + b["width"] <= box["x"] + box["width"]
        assert names.nth(i).evaluate("e => getComputedStyle(e).textOverflow") == "ellipsis"
        assert names.nth(i).evaluate("e => e.scrollWidth > e.clientWidth")
    assert page.locator(".dg-mnf-h b").bounding_box()["height"] < 30                  # "Monday night" on one line
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    ctx.close()
    assert errors == []
