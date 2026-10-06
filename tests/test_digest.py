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
from test_render import LOAD_MS, drive, go, open_page  # noqa: E402,F401


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


def test_the_packet_carries_no_results_but_recap_still_cuts_left_hurt_rows():
    """2026-10-05: the week's results moved to This week > Recap (LIVE_RECAP), so the Digest's packet no
    longer carries finals, stars, smashed, busts or left. design/recap.py still cuts its left-hurt rows with
    digest._left: a tagged headline gives the injury, an untagged one loses his name, suffix and all, and his
    newest headline since, when there is one, is `later`, without his name or tag."""
    from digest import _left
    b = _block()
    assert not {"finals", "pending", "stars", "smashed", "busts", "left"} & set(b)
    left = [_left(x, slugify) for x in load_digest()["results"]["left_hurt"]]
    assert [(r["n"], r["injury"], r["rest"], r["later"]) for r in left] == [
        ("Tua Tagovailoa", "concussion", "ruled out for the remainder", None),
        ("De'Von Achane", "knee", "questionable to return", "suffers season-ending torn ACL"),
        ("Travis Etienne", None, "exits early Sunday", None)]
    assert b["asof_words"] == "Fri 10:40 PM"


@pytest.fixture(scope="module")
def _phone(browser, page_file):
    """One 390px page for the pure-function checks below (they call a draw function and read what it
    returns): loaded once per file per worker. A test that mutates a global puts it back."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    assert errors == []                 # whatever the load raised fails here, not lost to a later clear
    yield page, errors
    ctx.close()


@pytest.fixture
def phone(_phone):
    page, errors = _phone
    left, errors[:] = list(errors), []  # each test answers for its own page errors only,
    assert left == []                   # and an error raised or left over since the last one fails this
    return page, errors


@pytest.mark.render
def test_the_digest_has_no_results_row_banner_board_or_wait_card(browser, page_file):
    """2026-10-05 (David: "we probably need a recap section for the week instead of dumping it into the
    Digest. The Digest should be a curated list of content for readers to enjoy and not just a results
    section that stays there for the whole week and quickly become stale"). On a phone and on the wall,
    before the week, on a Monday after games and once the week is over: no Results row, no board, no
    Smashed / Busts / Left hurt tabs, no "Waiting on week N" card. Monday opens no row of its own. The
    banner the packet's "results" rule used to draw falls to the top headline."""
    states = ("2026-09-18T12:00:00Z", "2026-09-22T12:00:00Z", "2026-09-28T13:00:00Z", "2026-10-02T12:00:00Z")
    for size in ((390, 844), (1400, 900)):
        ctx, page, errors = open_page(browser, page_file, size)
        drive(page, go("digest"))
        page.wait_for_selector(".dg-row")
        for at in states:
            got = page.evaluate("""(at) => { Date.now = () => Date.parse(at); DG_CUT = null; DG_OPEN = null;
              // The old packet still says its lead is the results rule: it must not draw one.
              LIVE_DIGEST.lead = {rule: 'results', index: 0}; render();
              const d = dgD();
              return {rows: [...document.querySelectorAll('.dg-row')].map(r => r.dataset.dgrow),
                      parts: document.querySelectorAll('.dg-rs, .dg-bd, .dg-rr, .dg-rlist, [data-dgset="res"], .dg-wait, .dg-lead-pills').length,
                      lead: d.lead, head: document.querySelector('.dg-lead-h').textContent,
                      news: d.news.length ? d.news[0].headline : null,
                      open: document.querySelectorAll('.dg-row[data-open]').length,
                      day: new Date(Date.now()).getDay()}; }""", at)
            assert "res" not in got["rows"] and got["parts"] == 0, (size, at, got)
            assert got["lead"] is None or got["lead"]["rule"] != "results", (size, at, got)
            if got["news"] and got["lead"] and got["lead"]["rule"] == "news":
                assert got["head"] == got["news"], (size, at, got)
            if size[0] < 1100 and got["day"] == 1:
                assert got["open"] == 0, (size, at, got)
        ctx.close()
        assert errors == []


@pytest.mark.render
def test_the_parts_the_recap_view_draws_with_still_draw(phone):
    """2026-10-05: the Results row is gone from the Digest, but the functions that drew a call, a box line, a
    board, a reason and a left-hurt row stay under their names (surface/digest/parts.js, lead.js) for the Recap
    view, which draws them from LIVE_RECAP. A LIVE_RECAP row has no `why`, so dgWhy takes a planted one."""
    page, errors = phone
    got = page.evaluate("""() => {
      const text = html => { const h = document.createElement('div'); h.innerHTML = html; return h.textContent.replace(/\\s+/g, ' ').trim(); };
      const R = LIVE_RECAP, top = R.top;
      const left = R.left_hurt.length ? R.left_hurt[0] : {injury: 'knee', later: 'suffers season-ending torn ACL', slug: 'x', n: 'Test Player', proj: 10, actual: null};
      const why = {kind: 'role', luck: 5, expected: 12, stat: 'targets', share: 31, delta: 10};
      const board = (() => { const h = document.createElement('div'); h.innerHTML = dgBoardHTML({stars: R.stars}); return h; })();
      return {board: board.querySelectorAll('.dg-bd-r').length, stars: R.stars.length,
              boardText: board.querySelector('.dg-bd-r') ? board.querySelector('.dg-bd-r').textContent.replace(/\\s+/g, ' ').trim() : '',
              first: R.stars.length ? dgShort(R.stars[0].n) + ' ' + dgStatLine(R.stars[0]) + ' ' + R.stars[0].actual.toFixed(1) : '',
              call: text(dgCall({n: 'Jahmyr Gibbs', line: {car: 20, rush_yd: 99, rec: 7, rec_yd: 65, td: 3, att: null}, actual: 30}, 4)),
              box: [...(() => { const h = document.createElement('div'); h.innerHTML = dgBoxPills({...top, actual: top.actual}); return h.querySelectorAll('.dg-lpill'); })()].map(e => e.textContent),
              topLine: dgTopLine({rush_yd: 99, rec_yd: 65, rush_td: 1, rec_td: 2}),
              why: text(dgWhy({why, diff: 9.7, slug: 'x'}, [])),
              leftRow: text(dgResRow(left, dgLeftPills(left), dgResNum(left))),
              out: [text(dgOutPill('Baker Mayfield expected to miss three weeks')), text(dgOutPill('suffers season-ending torn ACL'))],
              games: [dgGames(1), dgGames(15)]};
    }""")
    assert errors == []
    assert got["board"] == got["stars"] > 0
    assert got["boardText"] and got["first"].split(" ")[0] in got["boardText"]
    assert re.match(r"^Gibbs (rumbles for|runs wild for|bulldozes for|churns out) 164 yards and 3 TDs$", got["call"]), got["call"]
    assert got["box"] and not any(b.endswith("pts") for b in got["box"])    # yards, never points (2026-10-05)
    assert got["topLine"] == "164 yards, 3 TDs"
    assert got["why"] == "31% tgt +10TD luck +5"
    assert got["out"] == ["Out 3 wks", "Season"]
    assert got["leftRow"].startswith("L. Jackson") and "Ankle" in got["leftRow"]      # his injury as an amber word, then how long
    assert got["games"] == ["1 game", "15 games"]


@pytest.mark.render
def test_two_players_one_team_one_short_name_keep_their_first_names(phone):
    """ATL has Bijan and Brian Robinson (2026-09-29, David: "two B. Robinson on ATL ... confusing"):
    a short form two players on one team share keeps the first name; one on two teams stays short."""
    page, errors = phone
    got = page.evaluate("""() => {
      const was = [SEARCH_INDEX, DG_CLASH];
      SEARCH_INDEX = [...searchIndex(),
        {n: 'Bijan Robinson', slug: 'bijan-robinson', team: 'ATL'}, {n: 'Brian Robinson Jr.', slug: 'brian-robinson', team: 'ATL'},
        {n: 'Zed Quill', slug: 'zed-quill', team: 'SF'}, {n: 'Zack Quill', slug: 'zack-quill', team: 'NYJ'}];
      DG_CLASH = null;
      const out = [dgShort('Bijan Robinson'), dgShort('Brian Robinson Jr.'), dgShort('Zed Quill')];
      [SEARCH_INDEX, DG_CLASH] = was;
      return out;
    }""")
    assert errors == []
    assert got == ["Bijan Robinson", "Brian Robinson", "Z. Quill"]


@pytest.mark.render
def test_before_kickoff_the_digest_has_no_highlights_section(browser, page_file):
    """David, 2026-10-04: bored of the Digest's Highlights. Before kickoff nothing stands beside Need to
    know, which takes the wall's band; the Players tab keeps the Highlights."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.evaluate("dgLiveMode = () => false")
    drive(page, go("digest"))
    page.wait_for_selector(".dg-need")
    assert page.locator(".dg-facts, .dg-fact, [data-dgfact]").count() == 0
    assert "no-facts" in page.locator(".dg-ticker").get_attribute("class")
    assert "Highlights" not in page.locator(".dg-sec").all_inner_texts()
    assert page.evaluate("NAV.find(([g]) => g === 'scouting')[1][0]") == "highlights"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_call_picks_its_verb_from_his_day(phone):
    """Week 3's real lines (Sleeper and nflverse agree, 2026-09-29): the verb follows what his day was
    made of, the TDs ride at the end, a receiver's one throw does not make him a passer, and with no
    box line yet it says the score."""
    page, errors = phone
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
def test_a_finished_week_drops_the_preview_rows_and_draws_no_wait_card(browser, page_file):
    """Once every game of the packet's week has kicked off (the fixture's week 3 ends with KC @ SF,
    2026-09-21), Hurt and Matchups have nothing left to preview and next week's are not written: they
    leave the ticker (2026-09-29). The card that stood in for them, Blip's "Waiting on week N" (storyboard
    UDoWgLMrzUHup5tX53zaue option B), left on 2026-10-05 with the Results row: the Recap row takes that
    slot of the page. Weather and Top 5 read next week's data and stay. Hurt is Need to know since
    2026-09-29, above the rows: with nobody hurt it says so, and once the week is over it waits on next
    week's report."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    for _, sel in go("digest"):
        page.click(sel)
    page.wait_for_selector(".dg-row")
    # The fixture's page week is 2, the packet's is 3: the page week is set to the packet's, as it is live.
    at = lambda when: page.evaluate("""(at) => { Date.now = () => Date.parse(at); LIVE_DIGEST.hurt = []; LIVE_DIGEST.starters = [];
      LIVE_SCHEDULE.week = LIVE_DIGEST.week; DG_CUT = null; render();
      return [...document.querySelectorAll('.dg-ticker > [data-dgrow]')].map(e => e.dataset.dgrow); }""", when)
    before = at("2026-09-20T12:00:00Z")
    assert "mu" in before and "hurt" not in before
    assert page.locator(".dg-need .dg-nd-none").inner_text() == "Nobody new is out since Tuesday."
    after = at("2026-09-22T12:00:00Z")
    assert not {"hurt", "mu", "wait"} & set(after) and ("wx" in after or "t5" in after)
    # The page week is the packet's (3) and every game of it has kicked off: the row waits for the next
    # week's report, never "Week 3's" for a week that is over (2026-10-05).
    assert page.locator(".dg-need .dg-nd-none").inner_text() == "Week 4's injury report is still in the trainer's room."
    assert page.locator(".dg-wait").count() == 0 and page.locator(".dg svg.blip").count() == 0
    # Blip's voice for a Matchups row with nothing to call stays (digest.js dgMuNone): one of three lines,
    # never the record (2026-09-29, David: "say something funny ... instead of boring stats").
    jokes = page.evaluate("[t('digest.wait.mu1', {week: 4}), t('digest.wait.mu2'), t('digest.wait.mu3')]")
    assert page.evaluate("dgMuNone(4)") in jokes
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
    clocks = ("2026-09-10T12:00:00Z", "2026-09-14T18:00:00Z", "2026-09-17T12:00:00Z", "2026-09-18T12:00:00Z",
              "2026-09-21T20:00:00Z", "2026-09-22T00:30:00Z", "2026-09-22T12:00:00Z", "2026-09-24T12:00:00Z")
    # Each clock with the Recap link, then two without it (a recap under half final draws no link).
    for at, hide in [(c, False) for c in clocks] + [("2026-09-18T12:00:00Z", True), ("2026-09-22T12:00:00Z", True)]:
        got = page.evaluate("""([at, hide]) => { Date.now = () => Date.parse(at); DG_CUT = null;
          window.__nf = window.__nf ?? LIVE_RECAP.n_final; LIVE_RECAP.n_final = hide ? 0 : window.__nf; render();
          const tk = document.querySelector('.dg-ticker'), cs = getComputedStyle(tk);
          const names = new Set(cs.gridTemplateAreas.replace(/"/g, ' ').split(/\\s+/).filter(Boolean));
          const rows = [...tk.children].filter(e => getComputedStyle(e).display !== 'none');
          return {cls: tk.className, missing: rows.map(e => [e.dataset.dgrow || e.className, getComputedStyle(e).gridRowStart])
            .filter(([, a]) => !names.has(a)), cols: cs.gridTemplateColumns.split(' ').length}; }""", [at, hide])
        seen[got["cls"]] = at
        assert got["missing"] == [], f"{at} ({got['cls']}): rows with no area in the template: {got['missing']}"
        assert got["cols"] == 12, f"{at} ({got['cls']}): {got['cols']} columns, the wall has 12"
    # The fixture week must reach the finished-week layout, with and without the Recap link, or the
    # check above never saw it (the recap fixture's week ends Monday 2026-10-05, so the link shows all of September).
    assert any("wk-done" in c for c in seen), seen
    assert any("wk-done" in c and "has-recap" in c for c in seen) and any("wk-done" in c and "has-recap" not in c for c in seen), seen
    assert any("has-recap" in c and "wk-done" not in c for c in seen) and any("has-recap" not in c for c in seen), seen
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
    assert got == ["Start/Sit", "1 call this week"]   # the link names the view, not a count of takes against FantasyPros (2026-10-04)
    ctx.close()
    assert errors == []


def test_every_news_line_opens_its_story(browser, page_file):
    """2026-09-30 (David: "For the news on the digest, it should link to the news source"): each line is
    a link to its story in a new tab, the story's own page when ff-jarvis kept one, else a search for the
    headline; the face and name still open the profile, and no link sits inside a button."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
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
    # After kickoff the card is the game's one block (mnf.js), a tap away from its sheet.
    page.evaluate("""() => { GD_GAMES.push({home: 'CHI', away: 'PHI', kickoff: '2026-09-29T00:15:00Z', week: GD.leagues[0].week});
      Date.now = () => Date.parse("2026-09-29T00:30:00Z"); DG_CUT = null; render(); }""")
    assert page.locator(".dg-tn.on [data-dgblk]").count() == 1
    assert re.fullmatch(r"[A-Z]{3} · .+", page.locator(".dg-tn.on .dg-mnf-w").inner_text())
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
    browser, the lead falls to the top headline (it fell to the week's results until 2026-10-05, when
    those moved to Recap), and the stamp says how old the packet is."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.evaluate('Date.now = () => Date.parse("2026-09-28T13:00:00Z")')   # after load: the page pins its own
    for _, sel in go("digest"):
        page.click(sel)
    page.wait_for_selector(".dg-row")
    # the hurt starter's game has started, so the banner is the top headline, never a results call
    assert page.evaluate("dgD().lead") == {"rule": "news", "index": 0}
    assert page.locator(".dg-lead-h").inner_text() == page.evaluate("dgD().news[0].headline")
    assert page.locator(".dg-lead .dg-lpill").count() == 0
    assert page.locator(".dg-lead-when").inner_text() == "Week 3 · updated Fri 10:40 PM"
    assert page.locator(".dg-row[data-dgrow='res']").count() == 0 and page.locator(".dg-row[data-open]").count() == 0
    left = page.evaluate("dgD().hurt.map(r => r.game && r.game.away + '@' + r.game.home)")
    assert "LA@DEN" not in left
    # The fixture schedule holds one week-3 game, so give one top-5 row a Sunday kickoff by hand.
    n = page.evaluate("dgD().top5.length")
    page.evaluate("LIVE_DIGEST.top5.find(r => !r.ko).ko = '2026-09-27T17:00:00Z'; DG_CUT = null")
    assert page.evaluate("dgD().top5.length") == n - 1
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
    page.goto(page_file.as_uri() + "#digest", timeout=LOAD_MS)
    page.wait_for_selector(".dg-row")
    rows = page.locator(".dg-row:not(.empty):not(.link)")      # the Recap link is a band to tap, not a panel that opens
    assert rows.count() == page.locator(".dg-row[data-open]").count() > 0
    assert page.locator(".dg-row.link").count() == 1 and page.locator(".dg-row.link[data-open]").count() == 0
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
    """2026-10-03, David: yes to a Start of the week: our boldest START (Start/Sit v3: the widest gap
    between our rank and his season average), first in the Matchups card, our rank over his average
    on the right. None: no row. The foot is Start/Sit's record, SMASH, START and SIT as hit-miss."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    drive(page, go("digest"))
    page.wait_for_selector(".dg-row")
    want = page.evaluate("LIVE_SS3.takes.find(r => r.call === 'START')")
    row = page.locator(".dg-row[data-dgrow='mu']")
    if row.locator(".dg-head").count():
        row.locator(".dg-head").click()
    first = row.locator(".dg-ln").first
    assert first.locator(".dg-sotw").inner_text() == "Start of the week"
    assert first.get_attribute("data-dgslug") == want["slug"]
    assert first.locator(".dg-ln-r").inner_text().replace("\n", " ") == f"{want['pos']}{want['rank']} avg {want['pos']}{want['avg_rank']}"
    assert row.locator(".dg-foot > span").inner_text() == "Record since week 5: SMASH 7-3, START 2-2, SIT 4-1."
    page.evaluate("LIVE_SS3.takes = LIVE_SS3.takes.filter(r => r.call !== 'START'); Object.assign(LIVE_SS3.record, {weeks: [], smash: {hit: 0, miss: 0, void: 0}, start: {hit: 0, miss: 0, void: 0}, sit: {hit: 0, miss: 0, void: 0}}); DG_CUT = null; render()")
    assert page.locator(".dg-sotw").count() == 0
    assert row.locator(".dg-foot > span").inner_text() == "Record starts with week 5."
    assert not errors
    ctx.close()


@pytest.mark.render
def test_weather_is_the_weather_tabs_own_games(browser, page_file):
    """2026-09-29, 6A (David: "the next tab over is the weather and it's actually already live"): the
    row counts the games the Weather view says move scoring (wtRows().moves, still to kick off) and
    links there. A calm week draws no row on a phone and one quiet sentence on the wall."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
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
def test_every_topic_label_carries_its_icon(phone):
    """2026-09-29, 3A: a drawn icon beside every topic's label, stroked in the label's own colour."""
    page, errors = phone
    drive(page, go("digest"))
    page.wait_for_selector(".dg-row")
    got = page.evaluate("""[...document.querySelectorAll('.dg-row')].map(r => {
      const l = r.querySelector('.dg-l'), i = l.querySelector('svg.dg-lico');
      return [r.dataset.dgrow, !!i && getComputedStyle(i).stroke === getComputedStyle(l).color];
    })""")
    assert got and all(ok for _, ok in got), got
    assert errors == []


@pytest.mark.render
def test_a_headline_naming_no_player_keeps_the_digest_up(browser, page_file):
    """2026-09-29, David: "the digest is broken". A defender's IR move came through with a slug and no
    name; News keyed a block to the slug, avatarHTML read the missing name, and the throw blanked the
    whole Digest. A headline naming no player is a plain block of its own, whatever it carries."""
    ctx, page, errors = open_page(browser, page_file, (1400, 900))
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
    assert page.locator(".dg-lead-h").inner_text() == "St. Brown ERUPTS: 10 catches, 180 yards, 2 TDs"
    fact = page.locator(".dg-lead-fact").inner_text()
    assert fact == "12 tgt · Q3 4:12"                                # what the head (10 catches, 180 yards, 2 TDs) leaves out
    now = page.locator("[data-dgnow]")
    assert now.locator(".dg-sec").text_content() == "Right now"
    assert page.locator(".dg-facts").count() == 1                    # Right now is the one .dg-facts panel
    rows = now.locator(".dg-now-r")
    assert rows.count() == 3                                         # three rows, then More (2026-10-05)
    first = rows.first.inner_text().replace("\n", " ")
    assert "A. St. Brown" in first and "WR" in first and "DET" in first and "Q3 4:12" in first and "31.4" in first
    assert [rows.nth(i).locator(".dg-now-p").inner_text() for i in range(3)] == ["31.4", "27.1", "24.0"]
    more = now.locator("[data-dgmore]")
    assert more.inner_text() == "More" and more.get_attribute("aria-expanded") == "false"
    more.click()                                                     # the rest opens in place: no navigation, no rebuild
    rows = page.locator("[data-dgnow] .dg-now-r")
    assert rows.count() == 5 and page.evaluate("location.hash") != "#live"
    assert [rows.nth(i).locator(".dg-now-p").inner_text() for i in range(5)] == ["31.4", "27.1", "24.0", "19.2", "17.8"]
    assert page.locator("[data-dgmore]").inner_text() == "Less"
    page.locator("[data-dgmore]").click()
    assert page.locator("[data-dgnow] .dg-now-r").count() == 3
    page.locator("[data-dgmore]").click()
    now = page.locator("[data-dgnow]")
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
    assert got["kept"] and got["head"] == "Achane ERUPTS: 170 yards, 1 TD"
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
    assert page.locator(".dg-lead-go[data-dglv]").count() == 1 and "yards" in page.locator(".dg-lead-h").inner_text()
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


# ---- the Recap row (2026-10-05): the one link left of the Results row ----

# The recap fixture is week 4, 8 of 16 games final, its last kickoff Monday 2026-10-05 5:15 PM Pacific.
# These clocks hold in every zone from UTC-12 to UTC+11: the row goes at the end of Wednesday 10/7.
RECAP_ON, RECAP_LAST_DAY, RECAP_OFF = "2026-10-05T15:00:00Z", "2026-10-07T12:00:00Z", "2026-10-09T00:00:00Z"


def _recap_row(page, at, js=""):
    # Every call starts from the fixture's recap, so one case's edit never leaks into the next.
    page.evaluate("""([at, js]) => { window.__r = window.__r ?? JSON.stringify(LIVE_RECAP); window.__s = window.__s ?? LIVE_SCHEDULE.games;
      Object.assign(LIVE_RECAP, JSON.parse(window.__r)); LIVE_SCHEDULE.games = window.__s;
      Date.now = () => Date.parse(at); DG_CUT = null; eval(js); render(); }""", [at, js])
    return page.locator(".dg-row[data-dgrow='recap']")


@pytest.mark.render
def test_the_recap_row_links_to_recap_with_the_top_scorers_day_and_claudes_record(browser, page_file):
    """2026-10-05: one ticker row stands in for the Results row, in the other rows' shape: "Recap", the week,
    the top scorer's day and Claude's straight-up picks. It is a link to #weekrecap, opens nothing in place, and
    prints no fantasy points (David: Digest headlines show yards and TDs, never points)."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    drive(page, go("digest"))
    page.wait_for_selector(".dg-row")
    row = _recap_row(page, RECAP_ON)
    assert row.count() == 1
    assert page.evaluate("document.querySelector('.dg-ticker > .dg-row').dataset.dgrow") == "recap", "first in the ticker"
    link = row.locator("a.dg-head")
    assert link.get_attribute("href") == "#weekrecap" and link.locator("svg.dg-arrow").count() == 1
    assert row.locator(".dg-l").inner_text().upper() == "RECAP" and row.locator(".dg-n").inner_text() == "Wk 4"
    assert row.locator(".dg-body").count() == 0 and row.get_attribute("data-open") is None
    want = page.evaluate("[dgShort(LIVE_RECAP.top.n), dgStatLine(LIVE_RECAP.top), LIVE_RECAP.preview_record.su]")
    wins, losses = (int(x) for x in want[2].split("-")[:2])
    day = " · ".join(want[1].split(" · ")[:2])     # the first two parts of his line: the whole one cut off at 360px
    assert row.locator(".dg-s-w").inner_text() == f"{want[0]} {day}"
    assert row.locator(".dg-s-c").inner_text() == f"Claude {wins} of {wins + losses}"
    text = row.locator(".dg-s").inner_text()
    assert not re.search(r"\d\.\d|pts|point", text), f"no fantasy points on a Digest headline: {text!r}"
    # A tap on the row is a link, not a toggle: it opens no body, and the view's own hash does the rest.
    link.click()
    assert page.evaluate("location.hash") == "#weekrecap"
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_the_recap_row_drops_what_it_lacks_and_never_prints_a_missing_value(browser, page_file):
    """No box line: just his name. No Preview record: no Claude part. No scorer at all: the label and the week."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    drive(page, go("digest"))
    page.wait_for_selector(".dg-row")
    row = _recap_row(page, RECAP_ON, "LIVE_RECAP.top = {...LIVE_RECAP.top, line: null}")
    name = page.evaluate("dgShort(LIVE_RECAP.top.n)")
    assert row.locator(".dg-s-w").inner_text() == name and row.locator(".dg-s-c").count() == 1
    row = _recap_row(page, RECAP_ON, "LIVE_RECAP.preview_record = null")
    assert row.locator(".dg-s-c").count() == 0 and row.locator(".dg-s-w b").count() == 1
    row = _recap_row(page, RECAP_ON, "LIVE_RECAP.preview_record = {...LIVE_RECAP.preview_record, su: null}")
    assert row.locator(".dg-s-c").count() == 0
    row = _recap_row(page, RECAP_ON, "LIVE_RECAP.top = null")
    assert row.count() == 1 and row.locator(".dg-s-w").count() == 0 and "undefined" not in row.inner_text()
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_the_recap_row_shows_from_half_the_week_final_until_the_end_of_the_first_wednesday(browser, page_file):
    """Shows when n_final * 2 >= n_games, until local midnight at the end of the first Wednesday after the
    week's last kickoff; then hides. A recap file with no kickoff to count from draws no row."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    drive(page, go("digest"))
    page.wait_for_selector(".dg-row")
    shown = lambda at, js="": _recap_row(page, at, js).count() == 1
    assert shown(RECAP_ON) and shown(RECAP_LAST_DAY)                         # Monday; Wednesday noon
    assert not shown(RECAP_OFF)                                              # Thursday
    assert not shown(RECAP_ON, "LIVE_RECAP.n_final = 7")                     # under half final
    assert shown(RECAP_ON, "LIVE_RECAP.n_final = 8")                         # exactly half
    assert not shown(RECAP_ON, "LIVE_RECAP.n_games = 0")
    # The end is the reader's own midnight: Thursday 00:00 local, to the minute.
    end = page.evaluate("""(() => { const r = LIVE_RECAP; const e = dgRecapEnd(r); return [e, new Date(e).getDay(), new Date(e).getHours(),
      new Date(e).getMinutes(), Math.max(...r.games.map(g => Date.parse(g.kickoff)))]; })()""")
    assert end[1:4] == [4, 0, 0] and end[0] > end[4] and end[0] - end[4] < 4 * 86400e3
    gone = "LIVE_RECAP.games.forEach(g => { g.kickoff = null; }); LIVE_SCHEDULE.games = LIVE_SCHEDULE.games.filter(g => g.week !== LIVE_RECAP.week)"
    assert not shown(RECAP_ON, gone)
    # A kickoff on a Wednesday itself ends at the end of the NEXT one.
    wed = "LIVE_RECAP.games.forEach(g => { g.kickoff = '2026-10-07T20:00:00Z'; })"
    assert shown("2026-10-10T12:00:00Z", wed) and not shown("2026-10-16T12:00:00Z", wed)
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_the_recap_row_fits_a_phone_and_sits_in_a_wall_band(browser, page_file):
    """Nothing scrolls sideways at 360px, the row is one line at the ticker's 52px, and the wall draws it as a
    full-width band (its own named area) that is a link, not a toggle."""
    ctx, page, errors = open_page(browser, page_file, (360, 740))
    drive(page, go("digest"))
    page.wait_for_selector(".dg-row")
    _recap_row(page, RECAP_ON)
    got = page.evaluate("""(() => { const r = document.querySelector('.dg-row[data-dgrow="recap"]'), h = r.querySelector('.dg-head').getBoundingClientRect();
      const c = r.querySelector('.dg-s-c').getBoundingClientRect(), s = r.querySelector('.dg-s').getBoundingClientRect();
      return {h: Math.round(h.height), overflow: document.documentElement.scrollWidth > innerWidth, claudeInside: c.right <= s.right + 1}; })()""")
    assert got["h"] == 52 and not got["overflow"] and got["claudeInside"], got
    # Page turned past this week's stats (2026-10-05): the chip stays "Wk 4" and "Final tomorrow" opens the
    # wrapping text (a 192px chip left the text 31px at 360px).
    row = _recap_row(page, RECAP_ON, "LIVE_RECAP.complete = false; LIVE_SCHEDULE.week = LIVE_RECAP.week + 1")
    assert row.locator(".dg-n").inner_text() == "Wk 4"
    assert row.locator(".dg-s > :first-child").inner_text() == "Final tomorrow"
    got = page.evaluate("""(() => { const r = document.querySelector('.dg-row[data-dgrow="recap"]'), s = r.querySelector('.dg-s').getBoundingClientRect();
      const w = r.querySelector('.dg-s-w').getBoundingClientRect();
      return {text: Math.round(s.width), who: Math.round(w.width), overflow: document.documentElement.scrollWidth > innerWidth}; })()""")
    assert got["text"] >= 100 and got["who"] >= 60 and not got["overflow"], got
    row = _recap_row(page, RECAP_ON, "LIVE_RECAP.complete = true; LIVE_SCHEDULE.week = LIVE_RECAP.week + 1")
    assert row.locator(".dg-s-f").count() == 0, "stats landed: no note"
    ctx.close()
    ctx, page, errors = open_page(browser, page_file, (1705, 1000))
    drive(page, go("digest"))
    page.wait_for_selector(".dg-row")
    _recap_row(page, RECAP_ON)
    got = page.evaluate("""(() => { const tk = document.querySelector('.dg-ticker'), r = tk.querySelector('.dg-row[data-dgrow="recap"]');
      const cs = getComputedStyle(r), b = r.getBoundingClientRect(), t = tk.getBoundingClientRect();
      return {area: cs.gridRowStart, full: Math.abs(b.width - t.width) < 2, open: r.hasAttribute('data-open'),
              line: getComputedStyle(r.querySelector('.dg-s')).display, cur: getComputedStyle(r.querySelector('.dg-head')).cursor}; })()""")
    assert got["area"] == "recap" and got["full"] and not got["open"] and got["line"] != "none" and got["cur"] == "pointer", got
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

