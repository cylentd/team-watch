"""The roster's Cards view (2026-09-25): the tier is this week's rank at the position, K and DST are
support cards with no tier, the Sheet / Cards choice survives a reload, and the week's pack opens
once. The ranks and the implied points are computed at build time; the rest renders."""
import re

import pytest

from lines import live_lines
from projections import position_ranks
from test_render import drive, go, open_page, watch_errors  # noqa: F401


def slug(n):
    return n.lower().replace(" ", "-")


def test_rank_is_within_the_position_over_everyone_projected():
    players = [{"name": "A One", "pos": "RB", "pts": 20}, {"name": "B Two", "pos": "RB", "pts": 12},
               {"name": "C Three", "pos": "WR", "pts": 15}, {"name": "D Four", "pos": "RB", "pts": None},
               {"name": "B Two", "pos": "RB", "pts": 9}]          # a duplicate keeps his best number
    r = position_ranks(players, slug)
    assert r["a-one"] == (1, 2) and r["b-two"] == (2, 2) and r["c-three"] == (1, 1)
    assert "d-four" not in r


def test_a_player_not_playing_has_no_points_no_rank_and_the_rest_move_up():
    from projections import live_projections
    raw = {"players": [{"name": "A One", "pos": "RB", "pts": 20, "src": "model"},
                       {"name": "B Two", "pos": "RB", "pts": 12, "src": "model"},
                       {"name": "C Three", "pos": "RB", "pts": 9, "src": "model"}]}
    status = {"a one": {"name": "A One", "injury": "NA"}, "b two": {"name": "B Two", "injury": "Questionable"}}
    got = live_projections(raw, slug, {"a-one", "b-two", "c-three"}, status)["players"]
    assert got["a-one"]["pts"] is None and got["a-one"]["rank"] is None and got["a-one"]["out"] == "NA"
    assert got["b-two"]["rank"] == 1 and got["b-two"]["pts"] == 12 and got["b-two"]["out"] is None
    assert got["c-three"]["rank"] == 2 and got["c-three"]["of"] == 2


def test_implied_points_split_the_total_by_the_spread():
    pool = {"games": {"BAL@DAL": {"odds": {"overUnder": 52.5, "homeSpread": 3.5, "awaySpread": -3.5}},
                      "LA@SF": {"odds": {"overUnder": 44.0, "homeSpread": -2.0, "awaySpread": 2.0}},
                      "X@Y": {"odds": {"overUnder": None}}}}
    t = live_lines(pool, {"LA": "LAR"})["teams"]
    assert t["BAL"] == {"implied": 28.0, "opp": "DAL", "spread": -3.5, "total": 52.5}
    assert t["DAL"]["implied"] == 24.5
    assert t["LAR"]["opp"] == "SF" and t["SF"]["implied"] == 23.0
    assert "X" not in t
    assert live_lines({"games": {}}, {}) is None


# A virtual clock for the pack's motion (2026-10-05). The stage times itself with setTimeout (pkSleep) and
# the Web Animations API (pkAnim), a dozen seconds of both per pack. Installed after the page loads, it
# replaces setTimeout and clearTimeout and parks every finite animation, then moves page time on only
# when a test asks, jumping from one event (a timer, an animation's end) to the next at the animation's
# own playbackRate. So a tap that hurries the deal (rate 6) still shortens the page's time, the best
# card's reveal is still not hurried, and a test reads how long the page says it took, not the host's
# wall clock. Infinite animations (the orbiting line) are left alone: nothing awaits them.
VCLOCK = """
(() => {
  if (window.__vc) return;
  const realST = window.setTimeout.bind(window);
  const yieldNow = () => new Promise(r => { const c = new MessageChannel(); c.port1.onmessage = () => r(); c.port2.postMessage(0); });
  const vc = window.__vc = {now: 0, seq: 0, timers: new Map(), anims: new Set()};
  window.setTimeout = (fn, ms, ...args) => {
    const id = ++vc.seq;
    vc.timers.set(id, {id, at: vc.now + Math.max(0, +ms || 0), fn: () => fn(...args)});
    return id;
  };
  window.clearTimeout = id => { vc.timers.delete(id); };
  const animate = Element.prototype.animate;
  Element.prototype.animate = function (frames, opts) {
    const a = animate.call(this, frames, opts);
    if (a.effect.getComputedTiming().endTime !== Infinity) { a.pause(); vc.anims.add(a); }
    return a;
  };
  const left = a => (a.effect.getComputedTiming().endTime - (a.currentTime ?? 0)) / a.playbackRate;
  const next = () => {
    let d = Infinity;
    for (const t of vc.timers.values()) d = Math.min(d, t.at - vc.now);
    for (const a of vc.anims) if (a.playState === "paused" && a.playbackRate > 0) d = Math.min(d, left(a));
    return d === Infinity ? null : Math.max(0, d);
  };
  const step = dt => {
    vc.now += dt;
    for (;;) {
      let n = null;
      for (const t of vc.timers.values()) if (t.at <= vc.now + 1e-6 && (!n || t.at < n.at || (t.at === n.at && t.id < n.id))) n = t;
      if (!n) break;
      vc.timers.delete(n.id);
      try { n.fn(); } catch (e) { realST(() => { throw e; }, 0); }
    }
    for (const a of [...vc.anims]) {
      if (a.playState === "idle" || a.playState === "finished") { vc.anims.delete(a); continue; }
      if (a.playbackRate <= 0) continue;
      const to = (a.currentTime ?? 0) + dt * a.playbackRate;
      if (to >= a.effect.getComputedTiming().endTime - 1e-6) a.finish(); else a.currentTime = to;
    }
  };
  vc.run = async ms => {
    const end = vc.now + ms;
    for (let i = 0; vc.now < end - 1e-6 && i < 100000; i++) {
      const d = next();
      step(d === null ? end - vc.now : Math.min(d, end - vc.now));
      await yieldNow();
    }
    return vc.now;
  };
  vc.until = async (cond, limit) => {
    const ok = new Function("return (" + cond + ")"), t0 = vc.now;
    let idle = 0;
    while (!ok()) {
      if (vc.now - t0 >= limit) return -1;
      const d = next();
      if (d === null) {   // nothing of ours is pending: something real (a decode, a frame) has to land
        if (++idle > 1500) return -2;
        await new Promise(r => realST(r, 10));
        continue;
      }
      idle = 0;
      step(Math.min(d, t0 + limit - vc.now));
      await yieldNow();
    }
    return vc.now - t0;
  };
})()
"""


def vc_install(page):
    page.evaluate(VCLOCK)


def vc_run(page, ms):
    """Move the page's time on by `ms`; returns the page clock in ms."""
    return page.evaluate("ms => window.__vc.run(ms)", ms)


def vc_until(page, cond, limit=60000):
    """Move the page's time on until the JS expression `cond` holds; fails if `limit` page-ms pass first.
    Returns the page-ms it took."""
    took = page.evaluate("([c, l]) => window.__vc.until(c, l)", [cond, limit])
    assert took >= 0, f"the page's clock ran {limit} ms ({took}) and never saw: {cond}"
    return took


def vc_now(page):
    return page.evaluate("window.__vc.now")


def cards_page(browser, page_file, viewport=(360, 660), keep_stage=False):
    """The ESPN roster in Cards view. An unopened pack opens its stage by itself a moment after the
    view draws; unless the test wants it, the stage is closed (Escape before a rip puts the pack
    back on the page)."""
    ctx, page, errors = open_page(browser, page_file, viewport)
    drive(page, go("roster"))
    page.evaluate("VIEW='espn'; render()")
    page.click("[data-rmode='cards']")
    if page.locator(".pack .pack-seal").count():          # a pack waits on the page: its stage opens by itself
        page.wait_for_selector(".pk-stage")
    if not keep_stage and page.locator(".pk-stage").count():
        page.keyboard.press("Escape")
    return ctx, page, errors


def stage_opens(page):
    """The motion page's stage opens by itself (the page's 350 ms timer, run on the page's clock)."""
    vc_until(page, "!!document.querySelector('.pk-stage')", 2000)


def rip(page, part=.9):
    """Drag along the stage pack's strip, `part` of its width. A tap no longer rips (2026-09-25).
    With motion on, the pack spins in first (2026-09-26); a finger waits for it to land. The pack
    stands turned, so its box is wider than its strip: the grip is the first point from the left
    that is on the strip. On a page with the virtual clock, the wait and the tear's own 220 ms
    are run on it."""
    still = "!document.querySelector('.pk-center .pack-glow')?.getAnimations().length"
    clocked = page.evaluate("!!window.__vc")
    if clocked:
        vc_until(page, still)
    else:
        page.wait_for_function(still)
    box = page.locator(".pk-stage .pack-seal").bounding_box()
    y = box["y"] + box["height"] * .07
    x = page.evaluate("""([l, w, y]) => { for (let f = .02; f < .5; f += .02){
      const e = document.elementFromPoint(l + w * f, y); if (e && e.closest('.pack-top')) return l + w * (f + .02); } return l + w * .15; }""",
      [box["x"], box["width"], y])
    part = min(part, .8)
    page.mouse.move(x, y)
    page.mouse.down()
    for k in range(1, 7):
        page.mouse.move(x + box["width"] * part * k / 6, y)
    page.mouse.up()
    if clocked:
        vc_run(page, 250)


def motion_page(browser, page_file):
    """The same, with motion on, as a reader without reduced motion sees it, on the virtual clock."""
    from test_render import SEED
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="no-preference")
    page = ctx.new_page()
    page.set_default_timeout(5000)
    errors = watch_errors(page)
    page.route(re.compile(r"^https?://"), lambda route: route.abort())
    page.add_init_script(SEED)
    page.goto(page_file.as_uri() + "#roster")
    page.wait_for_function("document.getElementById('view').children.length > 0")
    vc_install(page)
    page.evaluate("VIEW='espn'; render()")
    page.click("[data-rmode='cards']")
    return ctx, page, errors


@pytest.mark.render
def test_cards_draw_every_player_and_the_choice_survives_a_reload(browser, page_file):
    ctx, page, errors = cards_page(browser, page_file)
    n = page.evaluate("TEAMS.espn.roster.length")
    assert page.locator(".cards .tc").count() == n
    support = page.evaluate("TEAMS.espn.roster.filter(p => p.pos === 'K' || p.pos === 'DST').length")
    assert page.locator(".cards .tc.tier-k, .cards .tc.tier-dst").count() == support
    page.reload()
    page.wait_for_function("document.getElementById('view').children.length > 0")
    drive(page, go("roster"))
    assert page.evaluate("ROSTER_MODE") == "cards"
    assert errors == []
    ctx.close()


def fresh_page(browser, page_file):
    """A reader who never touched the Sheet / Cards switch, on their team's roster (Yahoo)."""
    from test_render import CHOSE_SHEET, SEED
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
    page = ctx.new_page()
    page.set_default_timeout(5000)
    errors = watch_errors(page)
    page.route(re.compile(r"^https?://"), lambda route: route.abort())
    page.add_init_script(SEED.replace(CHOSE_SHEET, ""))
    page.goto(page_file.as_uri() + "#roster")
    page.wait_for_function("document.getElementById('view').children.length > 0")
    return ctx, page, errors


@pytest.mark.render
def test_a_new_reader_gets_cards_and_one_pack_stage_a_week(browser, page_file):
    """2026-09-28: Cards is the default, so a new reader meets the pack. Only the first unopened pack
    of the week opens by itself; a leaguemate's, opened next, waits sealed for a tap."""
    ctx, page, errors = fresh_page(browser, page_file)
    assert page.evaluate("packHas(TEAMS.yahoo) && packHas(TEAMS.espn)"), "the fixture has a pack for both teams"
    assert page.evaluate("ROSTER_MODE") == "cards"
    assert page.evaluate("localStorage.getItem('tw-roster-mode')") is None, "a default is not a choice"
    page.wait_for_selector(".pk-stage")
    page.keyboard.press("Escape")
    wk = page.evaluate("schedWeek()")
    assert page.evaluate(f"localStorage.getItem('tw-pack-auto-{wk}')") == "1"
    vc_install(page)                                            # the wait for a stage that must not open runs on the page's clock
    page.evaluate("VIEW='espn'; render()")
    vc_run(page, 450)
    assert page.locator(".pk-stage").count() == 0, "a second team's pack does not open by itself"
    assert page.locator(".pack .pack-seal").count() == 1, "it waits on the page, sealed"
    page.click(".pack .pack-seal")
    page.wait_for_selector(".pk-stage")
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_stored_sheet_wins_over_the_default(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    vc_install(page)                                            # the wait for a stage that must not open runs on the page's clock
    drive(page, go("roster"))
    assert page.evaluate("ROSTER_MODE") == "sheet"
    vc_run(page, 450)
    assert page.locator(".pk-stage").count() == 0
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_tier_is_the_rank_and_support_cards_have_none(browser, page_file):
    ctx, page, errors = cards_page(browser, page_file)
    tiers = page.evaluate("[1,2,5,6,12,13,24,25,null].map(cardTier)")
    assert tiers == ["one", "sig", "sig", "ur", "ur", "r", "r", "c", "c"]
    # A support card, drawn directly: no rank line, no foil, whatever the fixture's roster holds.
    page.evaluate("""document.querySelector('.cards .cardgrid').insertAdjacentHTML('beforeend',
      cardHTML({n:'Bengals', pos:'DST', team:'CIN', slot:'DST', start:true, slug:null}, 0, 'espn'))""")
    dst = page.locator(".cards .tc.tier-dst").last
    assert dst.locator(".tc-foot").count() == 0 and dst.locator(".tc-spark, .tc-etch").count() == 0
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_every_card_back_fits_its_card_on_a_small_phone(browser, page_file):
    # A 360px screen: the support backs lost their values to a squeezed row, then overflowed.
    ctx, page, errors = cards_page(browser, page_file)
    page.evaluate("""document.querySelector('.cards .cardgrid').insertAdjacentHTML('beforeend',
      cardHTML({n:'Bengals', pos:'DST', team:'CIN', slot:'DST', start:true, slug:null}, 0, 'espn') +
      cardHTML({n:'Cam Little', pos:'K', team:'JAX', slot:'K', start:true, slug:null}, 0, 'espn'))""")
    over = page.evaluate("[...document.querySelectorAll('.cards .tc-back')].filter(b => b.scrollHeight > b.clientHeight + 1).length")
    assert over == 0
    # The defense's face is its club code.
    assert page.locator(".cards .tc.tier-dst .tc-abbr").last.inner_text() == "CIN"
    assert errors == []
    ctx.close()


def test_an_autograph_is_a_top_three_finish_in_the_last_completed_week():
    from signed import completed_week, live_signed
    games = [{"week": 2, "home": "A", "away": "B"}, {"week": 2, "home": "C", "away": "D"},
             {"week": 3, "home": "A", "away": "C"}, {"week": 3, "home": "B", "away": "D"}]
    rows = [{"name": f"R{i}", "pos": "RB", "week": 2, "team": "ABCD"[i % 4], "pts": 30 - i} for i in range(5)]
    rows += [{"name": "Q1", "pos": "QB", "week": 2, "team": "A", "pts": 25},
             {"name": "R9", "pos": "RB", "week": 3, "team": "A", "pts": 50}]      # Thursday's game alone
    assert completed_week(rows, games) == 2
    got = live_signed({"rows": rows}, {"games": games}, slug, {"r0", "r2", "r3", "q1", "r9"})
    assert got == {"wk": 2, "players": {"r0": {"rank": 1, "pts": 30}, "r2": {"rank": 3, "pts": 28},
                                        "q1": {"rank": 1, "pts": 25}}}
    assert live_signed({"rows": rows}, {"games": []}, slug, {"r0"}) is None


@pytest.mark.render
def test_only_a_signed_player_has_the_autograph_whatever_his_tier(browser, page_file):
    ctx, page, errors = cards_page(browser, page_file)
    # The fixtures log too few teams for any week to be complete: then nobody is signed, not even
    # an Epic or the #1 (it was every #1-5 until 2026-09-25).
    if page.evaluate("LIVE_SIGNED === null"):
        assert page.locator(".cards .tc-sig").count() == 0
        assert errors == []
        ctx.close()
        return
    got = page.evaluate("""(() => {
      const ps = TEAMS.espn.roster.filter(p => p.slug && ['QB','RB','WR','TE'].includes(p.pos)).slice(0, 2);
      if (ps.length < 2) return null;
      LIVE_SIGNED.players = {[ps[0].slug]: {rank: 2, pts: 30}};
      if (typeof LIVE_INJURY !== 'undefined' && LIVE_INJURY) LIVE_INJURY.players = {};
      ps.forEach(p => { p.status = null; });
      const sig = p => { const d = document.createElement('div'); d.innerHTML = cardHTML(p, 0, 'espn'); return d.querySelectorAll('.tc-sig').length; };
      return [sig(ps[0]), sig(ps[1])];
    })()""")
    assert got is not None, "the fixture's ESPN roster has two skill players"
    assert got == [1, 0]
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_an_ir_spot_is_not_in_the_starting_lineup(browser, page_file):
    ctx, page, errors = cards_page(browser, page_file)
    rows = page.evaluate("espnRows([{n:'A', pos:'RB', team:'X', slug:'a', slot:'IR'}, {n:'B', pos:'RB', team:'X', slug:'b', slot:'RB'}]).map(p => p.start)")
    assert rows == [False, True]
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_starter_who_will_sit_is_named_above_the_roster_and_marked_in_it(browser, page_file):
    ctx, page, errors = cards_page(browser, page_file)
    # On every team: the first starter out, a bench player questionable, everyone else healthy.
    page.evaluate("""(() => { LIVE_INJURY.players = {};
      for (const tm of Object.values(TEAMS)){
        const s = tm.roster.find(p => p.start && p.slug && !['K','DST'].includes(p.pos));
        const b = tm.roster.find(p => !p.start && p.slug);
        tm.roster.forEach(p => { p.status = null; });
        if (s) LIVE_INJURY.players[s.slug] = {s: 'OUT', code: 'IR', note: 'Knee'};
        if (b) LIVE_INJURY.players[b.slug] = {s: 'Q', code: 'Questionable', note: null};
      }
      render(); })()""")
    page.keyboard.press("Escape")
    warn = page.locator(".inj-warn")
    assert warn.count() == 1 and "Knee" in warn.inner_text()
    alert = page.locator(".cards .tc.inj-alert")
    assert alert.count() == 1 and alert.locator(".tc-inj").inner_text() == "OUT"
    # Questionable is only a chip, never the warning.
    assert page.locator(".cards .tc.inj-q .tc-chip.q").count() <= 1 and page.locator(".cards .tc.inj-q.inj-alert").count() == 0
    page.locator("[data-rmode=sheet]").click()
    assert page.locator(".inj-warn").count() == 1 and page.locator(".row.inj-alert").count() == 1
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_weather_shows_where_it_touches_a_player_and_nowhere_covered(browser, page_file):
    ctx, page, errors = cards_page(browser, page_file)
    got = page.evaluate("""(() => {
      const storm = {roof:'outdoor', wind:'15 to 20 mph', precip_pct:60, short:'Rain'};
      const gust = {roof:'outdoor', wind:'22 mph', precip_pct:0, short:'Sunny'};
      return {
        kStorm: cardWeatherFx(storm, 'K'),
        snow: cardWeatherFx({roof:'outdoor', wind:'5 mph', precip_pct:0, short:'Light Snow'}, 'QB'),
        fair: cardWeatherFx({roof:'outdoor', wind:'3 to 8 mph', precip_pct:5, short:'Sunny'}, 'WR'),
        dome: cardWeatherFx({roof:'dome', wind:'30 mph', precip_pct:90, short:'Snow'}, 'WR'),
        roof: cardWeatherFx(storm, 'TE') && cardWeatherFx({...storm, roof:'retractable'}, 'TE'),
        rbGust: cardWeatherFx(gust, 'RB'), rbGustNote: cardWeatherNote(gust, 'RB'),
        wrGustNote: cardWeatherNote(gust, 'WR'), rbRainNote: cardWeatherNote(storm, 'RB'),
      };
    })()""")
    assert "wind" in got["kStorm"] and "rain" in got["kStorm"]
    assert "snow" in got["snow"] and "wind" not in got["snow"]
    assert got["fair"] == "" and got["dome"] == "" and got["roof"] == ""
    # Wind does not hurt a runner; rain gives him carries.
    assert got["rbGust"] == "" and got["rbGustNote"] is None
    assert got["wrGustNote"] == {"what": "WIND 22", "kind": "WIND", "effect": "pass ↓"}
    assert got["rbRainNote"] == {"what": "RAIN 60%", "kind": "RAIN", "effect": "run ↑"}
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_tap_flips_the_card_and_its_back_opens_the_profile(browser, page_file):
    ctx, page, errors = cards_page(browser, page_file)
    card = page.locator(".cards .tc").first
    card.click()
    assert "back" in card.get_attribute("class")
    card.locator(".bk-open").click()
    assert page.locator("#modal").is_visible()
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_card_back_is_a_role_sheet_from_his_latest_game(browser, page_file):
    ctx, page, errors = cards_page(browser, page_file)
    # The first skill player the Grid has a row for: his back is three stats with percentile bars.
    got = page.evaluate("""(() => {
      const p = TEAMS.espn.roster.find(p => WV_PROOF[p.pos] && USAGE.rows.some(r => r.slug === p.slug));
      if (!p) return null;
      // Healthy and dry, so the heading's second line is the week (an injury or the weather outranks it).
      if (typeof LIVE_INJURY !== 'undefined' && LIVE_INJURY) LIVE_INJURY.players = {};
      p.status = null; if (typeof LIVE_WEATHER !== 'undefined' && LIVE_WEATHER) LIVE_WEATHER.teams = {};
      const d = document.createElement('div'); d.innerHTML = cardHTML(p, 0, 'espn');
      const last = Math.max(...USAGE.rows.filter(r => r.slug === p.slug).map(r => r.wk));
      return {stats: d.querySelectorAll('.bk-stat').length, bars: [...d.querySelectorAll('.bk-bar i')].map(i => i.style.getPropertyValue('--p')),
              week: d.querySelector('.bk-why').textContent.includes(String(last)), spark: d.querySelectorAll('.tc-back .spark').length};
    })()""")
    assert got is not None, "the fixture's usage grid has a rostered skill player"
    assert got["stats"] == 3 and all(b != "" for b in got["bars"])
    assert got["week"] and got["spark"] == 0
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_card_takes_the_256px_head_where_there_is_one(browser, page_file):
    ctx, page, errors = cards_page(browser, page_file)
    got = page.evaluate("""(() => {
      HEADS_LG['a-sharp-one'] = 'heads/lg/a-sharp-one.webp'; HEADS['a-sharp-one'] = 'heads/a-sharp-one.webp';
      HEADS['a-soft-one'] = 'heads/a-soft-one.webp';
      const src = slug => { const d = document.createElement('div'); d.innerHTML = cardHeadHTML({n: 'A One', slug, pos: 'WR'});
        return d.querySelector('img').getAttribute('src'); };
      return [src('a-sharp-one'), src('a-soft-one')];
    })()""")
    assert got == ["heads/lg/a-sharp-one.webp", "heads/a-soft-one.webp"]
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_photo_fills_the_art_from_its_bottom_edge(browser, page_file):
    ctx, page, errors = cards_page(browser, page_file)
    img = page.locator(".cards .tc-art > .head > img").first
    assert img.count() > 0, "the fixture build has a headshot file"
    art = img.locator("xpath=../..").bounding_box()
    box = img.bounding_box()
    assert box["height"] > art["height"] * 0.8
    assert abs((box["y"] + box["height"]) - (art["y"] + art["height"])) < 1.5
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_pack_opens_once_a_week(browser, page_file):
    ctx, page, errors = cards_page(browser, page_file)
    assert page.locator(".pack").count() > 0, "the fixture's schedule has a week ahead, so a pack to open"
    page.click(".pack .pack-seal")                              # the page's pack puts it back on the stage
    rip(page)                                                   # reduced motion: straight to the roster
    page.wait_for_selector(".pk-stage", state="detached")
    assert page.locator(".cards .tc.pk-slot").count() == 0
    assert page.locator(".pack").count() == 0
    vc_install(page)                                            # the wait for a stage that must not open runs on the page's clock
    page.evaluate("render()")
    vc_run(page, 450)
    assert page.locator(".pk-stage").count() == 0, "an opened pack never opens its stage again by itself"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_rip_again_puts_this_weeks_pack_back_on_the_stage(browser, page_file):
    ctx, page, errors = cards_page(browser, page_file)
    assert page.locator(".pack").count() > 0, "the fixture's schedule has a week ahead, so a pack to open"
    assert page.locator("[data-rerip]").count() == 0, "nothing to rip again before the pack is opened"
    page.click(".pack .pack-seal")
    rip(page)
    page.wait_for_selector(".pk-stage", state="detached")
    page.click("[data-rerip]")
    assert page.locator(".pk-stage .pack-seal").count() == 1
    assert page.locator("[data-rerip]").count() == 0, "the pack is on the stage, so the button steps aside"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_stage_opens_by_itself_and_its_cards_fly_home_to_their_slots(browser, page_file):
    ctx, page, errors = motion_page(browser, page_file)
    stage_opens(page)
    # While the stage holds the pack, its players' slots on the page are left empty, in place.
    empty = page.evaluate("[...document.querySelectorAll('.cards .tc.pk-slot .bk-open')].map(b => +b.dataset.ci).sort((a, b) => a - b)")
    want = page.evaluate("packCards(TEAMS.espn).map(c => c.i).sort((a, b) => a - b)")
    assert empty == want and len(want) > 0
    rip(page)
    vc_until(page, "!!document.querySelector('.pk-card')")
    page.keyboard.press("Escape")                               # after the rip, Escape skips to the roster
    vc_until(page, "!document.querySelector('.pk-stage')", 6000)
    assert page.locator(".cards .tc.pk-slot").count() == 0 and page.locator(".pk-card").count() == 0
    assert page.locator("[data-rerip]").count() == 1
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_first_card_comes_out_of_the_pack_and_the_pile_counts_it(browser, page_file):
    ctx, page, errors = motion_page(browser, page_file)
    stage_opens(page)
    rip(page)
    vc_until(page, "!!document.querySelector('.pk-card')")
    # The pack is still on the stage while its first card rises out of it, then it goes.
    assert page.locator(".pk-center").count() == 1
    vc_until(page, "!document.querySelector('.pk-center')", 4000)
    # Nothing says the pack's size before the rip (2026-09-27); the pile counts each card as it lands.
    assert page.locator(".pack-n").count() == 0
    vc_until(page, "document.querySelector('.pk-count')?.textContent.startsWith('1 ')", 8000)
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_tear_starts_under_the_finger_and_runs_its_way(browser, page_file):
    ctx, page, errors = cards_page(browser, page_file, keep_stage=True)
    assert page.locator(".pk-stage").count() > 0, "the fixture's schedule has a week ahead, so a pack on the stage"
    box = page.locator(".pk-stage .pack-seal").bounding_box()
    y = box["y"] + 14
    page.mouse.move(box["x"] + box["width"] * .6, y)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] * .45, y)
    page.mouse.move(box["x"] + box["width"] * .3, y)
    got = page.evaluate("['--ta','--tb','--tdir'].map(k => parseFloat(getComputedStyle(document.querySelector('.pk-stage .pack-seal')).getPropertyValue(k)))")
    page.mouse.up()
    assert abs(got[0] - .3) < .03 and abs(got[1] - .6) < .03 and got[2] == -1
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_grip_near_the_end_tears_from_the_very_edge(browser, page_file):
    """2026-09-27: a finger never lands on the edge itself, and the tear left a stub of strip."""
    ctx, page, errors = cards_page(browser, page_file, keep_stage=True)
    assert page.locator(".pk-stage").count() > 0, "the fixture's schedule has a week ahead, so a pack on the stage"
    box = page.locator(".pk-stage .pack-seal").bounding_box()
    y = box["y"] + box["height"] * .07
    page.mouse.move(box["x"] + box["width"] * .2, y)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] * .4, y)
    ta = page.evaluate("parseFloat(getComputedStyle(document.querySelector('.pk-stage .pack-seal')).getPropertyValue('--ta'))")
    page.mouse.up()
    assert ta == 0
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_stage_card_is_its_roster_card_scaled_up_whole(browser, page_file):
    ctx, page, errors = motion_page(browser, page_file)
    stage_opens(page)
    rip(page)
    vc_until(page, "document.querySelector('.pk-card .tc') && document.querySelector('.pk-msg').textContent.includes('#')", 8000)
    share = """(el => el.querySelector('.tc-art').getBoundingClientRect().height / el.getBoundingClientRect().height)"""
    stage = page.evaluate(f"{share}(document.querySelector('.pk-card .tc'))")
    roster = page.evaluate(f"{share}(document.querySelector('#view .cards .tc'))")
    assert abs(stage - roster) < .02, f"the photo is {stage:.2f} of a stage card, {roster:.2f} of a roster card"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_on_a_desktop_the_starters_are_three_by_three_with_the_bench_beside(browser, page_file):
    ctx, page, errors = cards_page(browser, page_file, viewport=(1400, 900))
    cols = page.evaluate("[...document.querySelectorAll('.cards .cardgrid')].map(g => getComputedStyle(g).gridTemplateColumns.split(' ').length)")
    assert cols[0] == 3
    starters, bench = page.locator(".cards-col").nth(0).bounding_box(), page.locator(".cards-col.bench").bounding_box()
    assert bench["x"] > starters["x"] + starters["width"] - 1 and abs(bench["y"] - starters["y"]) < 2
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_only_a_drag_along_the_strip_rips_and_a_short_one_springs_back(browser, page_file):
    ctx, page, errors = cards_page(browser, page_file, keep_stage=True)
    assert page.locator(".pk-stage").count() > 0, "the fixture's schedule has a week ahead, so a pack on the stage"
    box = page.locator(".pk-stage .pack-seal").bounding_box()
    tear ="getComputedStyle(document.querySelector('.pk-stage .pack-seal')).getPropertyValue('--tear').trim()"
    # A tap on the pack's body, and a tap on the strip, only nudge.
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] * .7)
    page.mouse.click(box["x"] + 20, box["y"] + 14)
    assert page.locator(".pk-stage .pack-seal").count() == 1, "a tap does not rip"
    # A drag across the body, below the strip, does not tear either.
    page.mouse.move(box["x"] + 10, box["y"] + box["height"] * .6)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] - 10, box["y"] + box["height"] * .6)
    page.mouse.up()
    assert page.locator(".pk-stage .pack-seal").count() == 1, "only the strip tears"
    rip(page, .3)
    page.wait_for_timeout(600)                                 # the spring back is eased, not a jump
    assert page.locator(".pk-stage .pack-seal").count() == 1, "a short drag does not rip"
    assert page.evaluate(tear) in ("0", "0.000")
    rip(page, .8)
    page.wait_for_selector(".pk-stage", state="detached")       # reduced motion: ripped, straight to the roster
    assert page.locator(".pack").count() == 0
    assert errors == []
    ctx.close()
