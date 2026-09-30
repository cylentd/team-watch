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
@pytest.mark.parametrize("viewport", [(390, 844), (1705, 1000)])
def test_the_results_lists_are_one_panel_under_tabs(browser, page_file, viewport):
    """2026-09-29, storyboard Ms6FbdvynVPoRTKEidPGAz 2A (David: "clicking on smashed, busts, and left hurt
    opens up all 3 panels anyways ... just opens a big panel"): one tab bar, each tab its list's count,
    one list showing. A tap swaps the list in place, and the pick survives a repaint.
    On the wall the box keeps one height whatever tab is up (David: "clicking on the tabs expand and
    shrinks the container"), and a list runs five across with the points leading, right against the
    name ("it's too wide. The name and the number gap", then "still think it looks weird")."""
    ctx, page, errors = open_page(browser, page_file, viewport)
    page.goto(page_file.as_uri())
    drive(page, go("digest"))
    page.wait_for_selector(".dg-row[data-dgrow='res']")
    if page.locator(".dg-row[data-dgrow='res'][data-open]").count() == 0:
        page.click(".dg-row[data-dgrow='res'] .dg-head")
        page.wait_for_timeout(600)
    visible = lambda sel: page.locator(sel).evaluate_all("els => els.filter(e => e.checkVisibility({visibilityProperty: true})).length")
    box = lambda: page.locator("[data-dgset='res'] .dg-tabps").evaluate("e => e.getBoundingClientRect().height")
    gap = lambda: page.evaluate("""Math.max(...[...document.querySelectorAll('[data-dgset="res"] .dg-rr')]
      .filter(e => e.checkVisibility({visibilityProperty: true}))
      .map(r => r.querySelector('.dg-rr-n').getBoundingClientRect().left - r.querySelector('.dg-rv').getBoundingClientRect().right))""")
    tabs = page.locator("[data-dgset='res'] .dg-tab")
    n = page.evaluate("(() => { const d = dgD(); return [d.smashed.length, d.busts.length, d.left.length]; })()")
    assert tabs.count() == 3
    assert [tabs.nth(i).locator(".dg-tab-n").inner_text() for i in range(3)] == [str(x) for x in n]
    assert tabs.first.get_attribute("aria-selected") == "true"
    assert visible("[data-dgset='res'] .dg-rr") == n[0]
    heights = [box()]
    for i in (1, 2):
        tabs.nth(i).click()
        heights.append(box())
    assert tabs.nth(2).get_attribute("aria-selected") == "true" and tabs.first.get_attribute("aria-selected") == "false"
    assert visible("[data-dgset='res'] .dg-rr") == n[2]
    if viewport[0] >= 1100:
        assert max(heights) - min(heights) < 1, heights
        assert 0 <= gap() <= 24                      # the points lead, right against the name
    page.evaluate("render()")
    assert page.locator("[data-dgset='res'] .dg-tab").nth(2).get_attribute("aria-selected") == "true"
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_results_on_the_wall_keep_each_number_by_its_name(browser, page_file):
    """On a desktop the four tiles sit in a row and the board in four position columns, each a heading
    over rows of name, his day and points, with no face (2026-09-29, storyboard Ms6FbdvynVPoRTKEidPGAz
    1B: "should the categories be bigger? Should we consider not using headshots?"). The list under the
    tabs runs two columns. A board row is one column wide, so its points sit within 350px of its name at
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
          return {tiles: cols('.dg-tiles'), board: cols('.dg-bd'), list: cols('.dg-rlist'), rows,
                  faces: document.querySelectorAll('.dg-bd .dg-hd').length,
                  headPx: parseFloat(getComputedStyle(head).fontSize), namePx: parseFloat(getComputedStyle(name).fontSize)};
        }""")
        ctx.close()
        assert errors == []
    wall, phone = got[1705], got[360]
    assert (wall["tiles"], wall["board"], wall["list"]) == (4, 4, 5)
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
def test_the_tiles_never_repeat_the_banner_or_each_other(browser, page_file):
    """When the banner is the week's top score, the first tile is the runner-up (David, 2026-09-29);
    when something else leads, it is the top score. A player is in one tile at most."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.goto(page_file.as_uri())
    got = page.evaluate("""() => {
      const d = dgD(), top = [...d.stars].sort((a, b) => b.actual - a.actual);
      const read = lead => { const h = document.createElement('div'); h.innerHTML = dgTilesHTML({...d, lead});
        return [...h.querySelectorAll('.dg-tile')].map(t => [t.querySelector('.dg-tile-k').textContent, t.dataset.dgslug]); };
      return {top: top.map(r => r.slug), res: read({rule: 'results', index: 0}), news: read({rule: 'news', index: 0})};
    }""")
    ctx.close()
    assert errors == []
    assert got["res"][0] == ["Runner-up", got["top"][1]]
    assert got["news"][0] == ["Top score", got["top"][0]]
    for tiles in (got["res"], got["news"]):
        slugs = [s for _, s in tiles]
        assert len(slugs) == len(set(slugs))
    assert got["top"][0] not in [s for _, s in got["res"]]


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
    since 2026-09-29 (storyboard Ms6FbdvynVPoRTKEidPGAz 5A, 6A). Before that, an empty Hurt row still
    says "Nothing new"."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.goto(page_file.as_uri())
    for _, sel in go("digest"):
        page.click(sel)
    page.wait_for_selector(".dg-row")
    at = lambda when: page.evaluate("""(at) => { Date.now = () => Date.parse(at); LIVE_DIGEST.hurt = []; DG_CUT = null; render();
      return [...document.querySelectorAll('.dg-ticker > [data-dgrow]')].map(e => e.dataset.dgrow); }""", when)
    before = at("2026-09-20T12:00:00Z")
    assert "wait" not in before and "hurt" in before
    assert page.locator('.dg-row[data-dgrow="hurt"] .dg-s').inner_text() == "Nothing new"
    after = at("2026-09-22T12:00:00Z")
    assert "wait" in after and not {"hurt", "mu"} & set(after)
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


def test_new_starters_lead_news_and_name_who_they_replaced(browser, page_file):
    """Sleeper's new #1s and team moves are News since 2026-09-29 (David: "merge starters"; the row of
    its own sat empty most days). Each is a block before the headlines, tagged "New QB1" or "New team",
    its line QB1 over whom (with his status) or the two teams; the closed line leads with the newest,
    News counts them, and they go with the team's kickoff. No Starters row is drawn."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.goto(page_file.as_uri())
    for _, sel in go("digest"):
        page.click(sel)
    page.wait_for_selector(".dg-row")
    got = page.evaluate("""() => { Date.now = () => Date.parse("2026-09-17T12:00:00Z"); DG_CUT = null; DG_OPEN = "news"; render();
      const row = document.querySelector('.dg-row[data-dgrow="news"]'), s = [...row.querySelectorAll('.dg-nw.start')];
      return {line: row.querySelector('.dg-s').textContent.trim(), n: row.querySelector('.dg-n').textContent.trim(),
              first: row.querySelector('.dg-nws').firstElementChild.classList.contains('start'),
              tags: s.map(b => b.querySelector('.dg-nw-tag').textContent.trim()),
              lines: s.map(b => b.querySelector('li span').textContent.trim()),
              days: s.map(b => b.querySelector('time').textContent),
              news: dgD().news.length, startRow: !!document.querySelector('.dg-row[data-dgrow="start"]')}; }""")
    assert got["line"] == "Watson QB1 over Sanders" and got["n"] == str(4 + got["news"])
    assert got["first"] and not got["startRow"]
    assert got["tags"] == ["New QB1", "New QB1", "New team", "New RB1"]
    assert got["lines"] == ["QB1 over S. Sanders", "QB1 over J. Daniels (Out)", "MIN → NYG · QB3", "RB1 over J. Mason"]
    assert got["days"] == ["Tue", "Tue", "Mon", "Mon"]
    gone = page.evaluate("""() => { LIVE_DIGEST.starters.forEach(r => { r.ko = "2026-09-20T17:00:00Z"; });
      Date.now = () => Date.parse("2026-09-20T17:01:00Z"); DG_CUT = null; render();
      return document.querySelectorAll('.dg-nw.start').length; }""")
    assert gone == 0, "a started game takes its starters out of News"
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
    page.locator(".dg-row[data-dgrow='hurt'] .dg-head").click()
    assert page.locator(".dg-row[data-dgrow='hurt'][data-open]").count() == 1
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
