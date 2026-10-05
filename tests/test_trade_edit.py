"""League > Teams > Find trades, edit mode (2026-10-05): the scorer (js/surface/lboard/tbscore.js, a port of
ff-jarvis's rules.scoring and rules.drop) against tests/fixtures/data/trade_offers.json, the "To IR" and "You drop"
lines on an offer, the edit state (Edit on a card, Make your own under the list), and the guard that shuts Edit when
the page cannot reproduce the file's own numbers.

The fixture's ESPN league began as a cut of the file ff-jarvis's real writer made (branch trade-edit, 29e54f2): Purdy Big
in Japan and TeamMinh, TeamMinh shown as the page fixture's "Run It Back". Its AYO league is hand-made. The drop rule's
fields (lineup.ir, keep, ir_ok, protect, ir_moves; spec drop-rule-spec, 2026-10-05) are hand-made too, derived by the
rule: IR moves first, then the lowest `keep`. Change a roster and the offers' gains, moves and drops have to be
re-derived. The page is driven in Chromium with the fetch replaced, as test_trade_offers.py does."""
import copy
import json

import pytest

import trade_offers
from conftest import FIXTURES
from test_trade_offers import FIXTURE, PLANT, builder, reader, roster

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


def serve(body):
    """An init script that makes the page fetch `body` for trade_offers.json instead of the fixture."""
    return ("(() => { const prev = window.fetch; window.fetch = (u, ...r) => String(u).includes('trade_offers.json') ? "
            f"Promise.resolve(new Response(JSON.stringify({json.dumps(body)}), {{status: 200}})) : prev(u, ...r); }})();")


# ---- the scorer: every fixture offer, exactly; drops, floors, flex, ties, IR ------------------------------------

SCORE_ALL = """(data) => {
  const out = [];
  for (const [key, lg] of Object.entries(data.leagues)) for (const [owner, ps] of Object.entries(lg.teams))
    for (const [partner, kinds] of Object.entries(ps)) for (const kind of ["bold", "fair"]) for (const o of kinds[kind]){
      const mine = lg.values[owner], theirs = lg.values[partner];
      const r = tbGain(mine, tbResolve(o.send, mine), tbResolve(o.get, theirs), lg.lineup, tbOther(lg, owner));
      out.push({at: `${key} ${owner} ${partner} ${kind}`, js: r.gain, file: o.gain, ok: r.ok,
                drop: r.drop.map(p => p.name), want: o.drop.map(p => p.name),
                moves: r.irMoves.map(p => p.name), wantMoves: o.ir_moves.map(p => p.name)});
    }
  return out;
}"""


@pytest.mark.render
def test_the_scorer_reproduces_every_fixture_gain_ir_move_and_drop_exactly(browser, page_file):
    ctx, page, errors = reader(browser, page_file, "espn")
    rows = page.evaluate(SCORE_ALL, FIXTURE)
    assert len(rows) == 11
    for r in rows:
        assert r["js"] == r["file"] and r["ok"], r
        assert r["drop"] == r["want"] and r["moves"] == r["wantMoves"], r
    assert [r["drop"] for r in rows if r["drop"]] == [["Ollie Gordon II"]]
    assert [r["moves"] for r in rows if r["moves"]] == [["Marcus Mariota"]] * 5, "an injured player goes to IR, not to the waiver wire"
    ctx.close()
    assert errors == []


REAL = json.loads((FIXTURES / "trade_offers_ffjarvis.json").read_text(encoding="utf-8"))

# The producer's own file for the drop rule (ff-jarvis drop-rule, f22e6ac, 2026-10-05): ESPN, 12 teams' values, owners
# Purdy Big in Japan (no moves or drops), FAFO! (5 IR moves, 22 drops) and Larry's World (3 moves, 3 drops, 7 protected).
# Every gain, ir_moves and drop in it is the producer's, so a port that reproduces them all follows `rules.drop`.
REAL_ALL = """(data) => {
  const out = [], plain = (lg, owner, o, protect) => {
    const strip = rows => protect ? rows : rows.map(p => Object.assign({}, p, {protect: false}));
    const mine = strip(lg.values[owner]), theirs = strip(lg.values[o.partner]);
    return tbGain(mine, tbResolve(o.send, mine), tbResolve(o.get, theirs), lg.lineup, tbOther(lg, owner));
  };
  for (const [key, lg] of Object.entries(data.leagues)) for (const [owner, ps] of Object.entries(lg.teams))
    for (const [partner, kinds] of Object.entries(ps)) for (const kind of ["bold", "fair"]) for (const o of kinds[kind]){
      const r = plain(lg, owner, Object.assign({partner}, o), true), n = plain(lg, owner, Object.assign({partner}, o), false);
      out.push({at: `${key} ${owner} ${partner} ${kind}`, js: r.gain, file: o.gain, ok: r.ok,
                drop: r.drop.map(p => p.name), want: o.drop.map(p => p.name),
                moves: r.irMoves.map(p => p.name), wantMoves: o.ir_moves.map(p => p.name),
                unprotected: n.drop.map(p => p.name), owner});
    }
  const guard = [];
  for (const [key, lg] of Object.entries(data.leagues)) for (const [owner, ps] of Object.entries(lg.teams))
    for (const [partner, pair] of Object.entries(ps)){
      const why = tbMismatch(lg, {name: owner}, {name: partner}, pair);
      if (why) guard.push(`${owner} to ${partner}: ${why}`);
    }
  return {out, guard};
}"""


@pytest.mark.render
def test_the_scorer_reproduces_every_offer_of_ff_jarvis_own_drop_rule_file_exactly(browser, page_file):
    ctx, page, errors = reader(browser, page_file, "espn")
    got = page.evaluate(REAL_ALL, REAL)
    rows = got["out"]
    assert len(rows) == 121
    for r in rows:
        assert r["js"] == r["file"] and r["ok"], r
        assert r["drop"] == r["want"] and r["moves"] == r["wantMoves"], r
    assert got["guard"] == [], "the guard accepts every pair of the producer's own file"
    assert sum(1 for r in rows if r["moves"]) == 8 and sum(1 for r in rows if r["drop"]) == 25
    assert all(not r["moves"] and not r["drop"] for r in rows if r["owner"] == "Purdy Big in Japan")
    # No offer in the producer's file is changed by a protected player (the unprotected rule drops the same ones), so
    # protect is exercised by hand: protect each dropped player in turn and the next lowest keep goes instead.
    assert all(r["unprotected"] == r["drop"] for r in rows)
    hand = page.evaluate("""(data) => {
      const lg = data.leagues.espn, res = [];
      for (const [owner, ps] of Object.entries(lg.teams)) for (const [partner, kinds] of Object.entries(ps))
        for (const o of kinds.bold.concat(kinds.fair)) if (o.drop.length){
          const mine = lg.values[owner].map(p => Object.assign({}, p, {protect: p.protect || o.drop.some(d => d.name === p.name)}));
          const theirs = lg.values[partner];
          const r = tbGain(mine, tbResolve(o.send, mine), tbResolve(o.get, theirs), lg.lineup, tbOther(lg, owner));
          res.push({was: o.drop.map(p => p.name), now: r.drop.map(p => p.name), ok: r.ok, moves: r.irMoves.map(p => p.name)});
        }
      return res;
    }""", REAL)
    assert len(hand) == 25
    for h in hand:
        assert not set(h["was"]) & set(h["now"]), h                      # a protected player is never dropped
        assert not h["ok"] or len(h["now"]) == len(h["was"]), h          # the same count, other players, or no legal drop
    assert all(h["ok"] and h["now"] for h in hand), "someone else goes instead (no legal drop is the synthetic test's)"
    ctx.close()
    assert errors == []


def test_the_producers_own_file_passes_the_contract_with_the_drop_rule_required(monkeypatch):
    monkeypatch.setattr(trade_offers, "DROP_RULE_REQUIRED", True)
    assert trade_offers.problems(REAL) == []


def score(page, send, get):
    return page.evaluate("""([d, send, get]) => {
      const L = d.leagues.espn, mine = L.values["Purdy Big in Japan"], theirs = L.values["Run It Back"];
      const r = tbGain(mine, mine.filter(p => send.includes(p.name)), theirs.filter(p => get.includes(p.name)), L.lineup, tbOther(L, "Purdy Big in Japan"));
      return {gain: r.gain, drop: r.drop.map(p => p.name), ir: r.irMoves.map(p => p.name), ok: r.ok};
    }""", [FIXTURE, send, get])


@pytest.mark.render
def test_a_package_over_the_cap_drops_the_lowest_keep_non_starters_and_ir_never_counts(browser, page_file):
    ctx, page, _ = reader(browser, page_file, "espn")
    # Purdy's side holds 15 players, one on IR, and two K/DST: 14 + 2 = 16, the cap.
    assert score(page, ["Brock Purdy", "Kalif Raymond"], ["Chase Brown", "Christian Watson"]) == {"gain": 5.5, "drop": [], "ir": [], "ok": True}
    assert score(page, ["Brock Purdy"], ["Chase Brown", "Christian Watson"]) == {"gain": 5.5, "drop": ["Ollie Gordon II"], "ir": [], "ok": True}
    assert score(page, [], ["Chase Brown", "Christian Watson"])["drop"] == ["Ollie Gordon II", "Kalif Raymond"], "two over: lowest keep first"
    assert score(page, ["Jordan Mason"], ["Chase Brown"])["drop"] == ["Ollie Gordon II"], "sending the player on IR frees no room"
    assert score(page, [], ["Adonai Mitchell"]) == {"gain": 0, "drop": [], "ir": [], "ok": True}, "a player on IR does not count toward the cap"
    assert score(page, ["Tee Higgins"], []) == {"gain": -4.2, "drop": [], "ir": [], "ok": True}, "a gain can be negative"
    # Purdy's IR has one free slot (lineup.ir 2, Mason in one): Mariota (Out, not on IR) takes it, nobody is dropped.
    assert score(page, [], ["Marcus Mariota"]) == {"gain": 0, "drop": [], "ir": ["Marcus Mariota"], "ok": True}
    ctx.close()


@pytest.mark.render
def test_ir_moves_come_before_drops_and_protect_and_keep_decide_who_is_dropped(browser, page_file):
    ctx, page, _ = reader(browser, page_file, "espn")
    got = page.evaluate("""() => {
      const P = (name, pos, proj, o) => Object.assign({name, pos, proj, seen: proj, ir: false, keep: proj, ir_ok: false, protect: false}, o || {});
      const lu = ir => ({slots: {QB: 1}, flex: [{n: 1, pos: ["RB", "WR"]}], floor: {QB: 10, RB: 4, WR: 5, TE: 6}, cap: 4, ir});
      const base = () => [P("q", "QB", 15), P("r", "RB", 8), P("w", "WR", 6), P("low", "WR", 2),
                          P("inj", "WR", 0, {keep: 12, ir_ok: true})];     // five players, cap 4: one over
      const room = (ros, ir, other, get) => { const r = tbRoom(ros, get || [], lu(ir), other || 0);
                                              return {ir: r.irMoves.map(p => p.name), drop: r.drop.map(p => p.name), short: r.short}; };
      const full = base().concat([P("old", "TE", 0, {ir: true, ir_ok: true})]);              // the one IR slot is taken
      const two = base().concat([P("inj2", "RB", 0, {keep: 5, ir_ok: true})]);               // two over, two eligible
      const ties = [P("q", "QB", 15), P("r", "RB", 8), P("a", "WR", 3, {keep: 3, seen: 5}), P("b", "WR", 3, {keep: 3, seen: 2}),
                    P("c", "WR", 3, {keep: 3, seen: 2}), P("x", "WR", 9, {keep: 1, protect: true})];
      return {
        move: room(base(), 1),                                                          // IR first: nobody is dropped
        moveNeeded: room(base(), 2),                                                    // two free slots, one over: one move
        full: room(full, 1),                                                            // IR full: the lowest keep is dropped
        protectOne: room(full.map(p => p.name === "low" ? Object.assign({}, p, {protect: true}) : p), 1),
        protectAll: room(full.map(p => p.ir ? p : Object.assign({}, p, {protect: true})), 1),
        highest: room(two, 1),                                                          // two over, one slot: the higher keep moves
        both: room(two, 2),                                                             // two slots: both move, no drop
        oneThenDrop: room(two.concat([P("extra", "WR", 1)]), 1),                         // three over: one move, two drops
        none: room(base(), 0),                                                          // a league with no IR slot
        keepNotProj: room(full.map(p => p.name === "w" ? Object.assign({}, p, {keep: 1}) : p).concat([P("hi", "WR", 0, {keep: 20})]), 1),
        ties: room(ties.concat([P("y", "WR", 1, {keep: 3, seen: 2})]), 0),              // cap 4, six players: two over
        gain: tbGain(base(), [], [P("new", "RB", 9)], lu(1), 0), gainFull: tbGain(full, [], [P("new", "RB", 9)], lu(1), 0),
        empty: tbGain(base(), [], [], lu(1), 0),
      };
    }""")
    assert got["move"] == {"ir": ["inj"], "drop": [], "short": False}
    assert got["moveNeeded"] == {"ir": ["inj"], "drop": [], "short": False}, "no more moves than it takes to reach the cap"
    assert got["full"] == {"ir": [], "drop": ["low"], "short": False}
    assert got["protectOne"] == {"ir": [], "drop": ["w"], "short": False}, "a protected player is never dropped: the next lowest keep goes"
    assert got["protectAll"]["short"] is True and got["protectAll"]["drop"] == [], "all protected: no legal drop"
    assert got["highest"] == {"ir": ["inj"], "drop": ["low"], "short": False}, "the higher keep takes the one slot, the rest is dropped"
    assert got["both"] == {"ir": ["inj", "inj2"], "drop": [], "short": False}
    assert got["oneThenDrop"] == {"ir": ["inj"], "drop": ["extra", "low"], "short": False}
    assert got["none"] == {"ir": [], "drop": ["low"], "short": False}, "no IR slot at all: a drop, never a move"
    assert got["keepNotProj"]["drop"] == ["w", "low"], "keep, not this week's projection, orders the drops: the proj-0 players stay"
    # ties on keep 3: lower seen first, then name. a (seen 5) is the last to go though it sorts first by name.
    assert got["ties"]["drop"] == ["b", "c", "y"], got["ties"]
    assert got["gain"]["irMoves"][0]["name"] == "inj" and got["gainFull"]["drop"][0]["name"] == "low"
    assert got["gain"]["gain"] == got["gainFull"]["gain"] and got["gain"]["gain"] > 0, "a moved or dropped player never changes the lineup"
    assert got["empty"] == {"gain": 0, "drop": [], "irMoves": [], "ok": False}
    ctx.close()


@pytest.mark.render
def test_a_package_with_no_legal_drop_is_not_ok(browser, page_file):
    ctx, page, _ = reader(browser, page_file, "espn")
    got = page.evaluate("""() => {
      const P = (name, pos, proj, o) => Object.assign({name, pos, proj, seen: proj, ir: false, keep: proj, ir_ok: false, protect: true}, o || {});
      const lu = {slots: {QB: 1}, flex: [], floor: {QB: 10, RB: 4, WR: 5, TE: 6}, cap: 2, ir: 1};
      const r = tbGain([P("q", "QB", 15), P("r", "RB", 8)], [], [P("n", "WR", 7)], lu, 0);
      return {ok: r.ok, gain: r.gain, drop: r.drop.length};
    }""")
    assert got == {"ok": False, "gain": 0, "drop": 0}
    ctx.close()


@pytest.mark.render
def test_candidates_ties_floors_flex_and_other_follow_the_rule_in_the_file(browser, page_file):
    ctx, page, _ = reader(browser, page_file, "espn")
    got = page.evaluate("""() => {
      const P = (name, pos, proj, seen, ir) => ({name, pos, proj, seen, ir: !!ir, keep: proj, ir_ok: false, protect: false});
      const lu = {slots: {QB: 1}, flex: [{n: 2, pos: ["RB", "WR"]}, {n: 1, pos: ["QB", "RB", "WR", "TE"]}],
                  floor: {QB: 10, RB: 4, WR: 5, TE: 6}, cap: 3};
      const lone = tbLineup([P("q", "QB", 15, 1), P("r", "RB", 8, 1), P("w", "WR", 3, 1)], lu);
      const wide = {slots: {QB: 1}, flex: [{n: 2, pos: ["RB", "WR"]}], floor: {QB: 10, RB: 4, WR: 5, TE: 6}, cap: 5};
      const ros = [P("q", "QB", 15, 1), P("a", "RB", 8, 1), P("w1", "WR", 6, 3), P("w2", "WR", 6, 9), P("w3", "WR", 6, 9),
                   P("x", "TE", 1, 7), P("y", "TE", 1, 2), P("z", "TE", 1, 2), P("ir", "RB", 0, 1, true)];
      const names = (cap, other) => tbDrops(ros, [], Object.assign({}, wide, {cap}), other).drop.map(p => p.name);
      return {lone: [lone.total, [...lone.used].sort()], starters: [...tbLineup(ros, wide).used].sort(),
              dropOne: names(7, 0), dropThree: names(5, 0), dropWithOther: names(6, 1),
              none: tbGain(ros, [], [], wide, 0), short: tbDrops(ros, [], Object.assign({}, wide, {cap: 1}), 0).short};
    }""")
    # QB 15.00; the RB/WR flex takes r 8.00 and w (3.00 under the 5.00 bar: 5.00); the any-position flex is empty: 10.00 bar.
    assert got["lone"] == [1500 + 800 + 500 + 1000, ["q", "r", "w"]]
    # Candidates: proj desc, seen desc, name asc. So a, w2 start (w2 and w3 tie on proj and seen, w2 first by name).
    assert got["starters"] == ["a", "q", "w2"]
    # Drops (keep = proj here): keep asc, seen asc, name asc, never a starter nor a player on IR: y and z (1.00, seen 2), x (1.00, seen 7), w1, w3.
    assert got["dropOne"] == ["y"]
    assert got["dropThree"] == ["y", "z", "x"]
    assert got["dropWithOther"] == ["y", "z", "x"], "a K/DST the roster also holds counts toward the cap and is never released"
    assert got["none"] == {"gain": 0, "drop": [], "irMoves": [], "ok": False}, "an empty package is not scored"
    assert got["short"] is True, "a cap that the non-starters cannot reach is reported, not hidden"
    ctx.close()


# ---- the drop line on an offer ------------------------------------------------------------------------------

@pytest.mark.render
def test_an_offer_that_drops_a_player_says_so_in_one_line_and_the_others_say_nothing(browser, page_file):
    ctx, page, errors = reader(browser, page_file, "espn")
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
    ctx.close()
    ctx, page, _ = reader(browser, page_file, RUN)
    builder(page, "espn")
    page.wait_for_selector(".tb-card .tb-gain")
    assert page.locator(".tb-drop").count() == 0, "his injured QB goes to IR, so there is no drop"
    assert page.locator(".tb-ir").all_inner_texts() == ["To IR: M. Mariota"] * 2, "the other direction: his own IR move"
    assert [page.locator(".tb-card").nth(i).locator(".tb-ir").count() for i in range(3)] == [0, 1, 1]
    assert page.locator(".tb-ir").first.evaluate("e => getComputedStyle(e).color") != "rgb(255, 176, 32)", "quiet, never amber"
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_an_offer_with_both_lines_puts_to_ir_above_you_drop(browser, page_file):
    ctx, page, errors = reader(browser, page_file, "espn")
    html = page.evaluate("""() => tbRoomHTML({ir_moves: [{name: "Caleb Williams"}, {name: "Saquon Barkley"}], drop: [{name: "Ollie Gordon II"}]})""")
    assert html.index("To IR: C. Williams, S. Barkley") < html.index("You drop: O. Gordon II")
    assert page.evaluate("""() => tbRoomHTML({ir_moves: [], drop: []}) + tbRoomHTML({})""") == "", "no line when there is nothing"
    ctx.close()
    assert errors == []


# ---- the edit state ----------------------------------------------------------------------------------------

@pytest.mark.render
def test_edit_opens_on_the_offer_it_started_from_and_back_returns_to_the_offers(browser, page_file):
    ctx, page, errors = reader(browser, page_file, "espn")
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
    assert page.locator("#tb-title").count() == 1, "Back closed the edit state only: the builder page is still there"
    assert page.evaluate("document.activeElement.dataset.tbedit") == "0", "focus returns to the Edit button"
    open_edit(page, 0)
    page.locator(".lbp-back").click()                                         # the link is the same step as Back
    page.wait_for_selector(".tb-card .tb-gain")
    assert page.evaluate("history.state && history.state.layer") == "lbtrade", "and it took the edit state's history entry back"
    page.locator(".lbp-back").click()
    page.wait_for_selector("[data-tbfind]")
    assert page.locator(".lbp-title").inner_text() == "Run It Back"
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_a_tap_on_a_player_puts_him_in_or_out_and_the_gain_follows(browser, page_file):
    ctx, page, errors = reader(browser, page_file, "espn")
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
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_an_empty_package_is_a_dash_and_reset_goes_back_to_the_offer_it_started_from(browser, page_file):
    ctx, page, _ = reader(browser, page_file, "espn")
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
    ctx.close()


@pytest.mark.render
def test_the_drop_line_shows_when_the_package_puts_the_reader_over_the_cap_and_goes_when_it_does_not(browser, page_file):
    ctx, page, _ = reader(browser, page_file, "espn")
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
    ctx.close()


@pytest.mark.render
def test_the_to_ir_line_sits_above_the_drop_line_and_the_foot_keeps_its_size(browser, page_file):
    ctx, page, _ = reader(browser, page_file, "espn")
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
    ctx.close()


@pytest.mark.render
def test_a_package_the_cap_cannot_take_says_so_and_cannot_be_copied(browser, page_file):
    ctx, page, _ = reader(browser, page_file, "espn")
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
    ctx.close()


@pytest.mark.render
def test_copy_offer_in_edit_is_the_same_message_as_a_cards(browser, page_file):
    ctx, page, errors = reader(browser, page_file, "espn")
    builder(page, RUN)
    open_edit(page, 0)
    page.locator("[data-tbedcopy]").click()
    page.wait_for_function("document.querySelector('[data-tbedcopy]').textContent === 'Copied'")
    assert page.evaluate("navigator.clipboard.readText()") == (
        "Trade? I send Higgins (14.4 a game), Purdy (28.8), Gordon II (10.2) for Smith-Njigba (25.3) and Brown (11.4).")
    pick(page, "Ollie Gordon II")
    page.locator("[data-tbedcopy]").click()
    page.wait_for_function("document.querySelector('[data-tbedcopy]').textContent === 'Copied'")
    assert page.evaluate("navigator.clipboard.readText()") == (
        "Trade? I send Higgins (14.4 a game) and Purdy (28.8) for Smith-Njigba (25.3) and Brown (11.4).")
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_a_refused_clipboard_in_edit_shows_the_text_in_a_box(browser, page_file):
    ctx, page, _ = reader(browser, page_file, "espn",
                          init="navigator.clipboard.writeText = () => Promise.reject(new DOMException('no', 'NotAllowedError'));")
    builder(page, RUN)
    open_edit(page, 1)
    page.locator("[data-tbedcopy]").click()
    page.wait_for_selector(".tb-edfoot .tb-box")
    assert page.locator(".tb-box").input_value() == "Trade? I send Purdy (28.8 a game), Raymond (9.4), Gordon II (10.2) for Smith-Njigba (25.3)."
    assert page.locator("[data-tbedcopy]").inner_text() == "Copy offer", "no false Copied"
    ctx.close()


@pytest.mark.render
def test_make_your_own_is_under_the_offers_on_both_tabs_and_in_the_empty_states_and_starts_empty(browser, page_file):
    ctx, page, errors = reader(browser, page_file, "espn-run-it-back")        # bold and fair both have offers
    builder(page, "espn")
    page.wait_for_selector(".tb-card .tb-gain")
    assert page.locator("[data-tbown]").inner_text() == "Make your own offer"
    assert page.evaluate("(() => { const b = document.querySelector('[data-tbown]'), c = [...document.querySelectorAll('.tb-card')].pop();"
                         " return b.getBoundingClientRect().top >= c.getBoundingClientRect().bottom; })()"), "under the last offer"
    page.locator("[data-tbtab='fair']").click()
    assert page.locator("[data-tbown]").count() == 1
    page.locator("[data-tbown]").click()
    page.wait_for_selector(".tb-body.tb-ed")
    assert page.locator(".tb-r[aria-pressed='true']").count() == 0
    assert page.locator(".tb-pkg .tb-hint").count() == 2
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
    ctx.close()
    assert errors == []
    ctx, page, _ = reader(browser, page_file, "espn")                          # bold only: the fair tab is empty
    builder(page, RUN)
    page.wait_for_selector(".tb-card .tb-gain")
    page.locator("[data-tbtab='fair']").click()
    assert page.locator(".tb-empty").count() == 1 and page.locator("[data-tbown]").count() == 1
    ctx.close()
    ctx, page, _ = reader(browser, page_file, "ayo-don-wick")                 # a pair with no entry at all
    page.locator("[data-lgpick='ayo']").click()
    builder(page, "ayo")
    page.wait_for_selector(".tb-empty")
    assert page.locator("[data-tbown]").count() == 1
    page.locator("[data-tbown]").click()
    page.wait_for_selector(".tb-body.tb-ed")
    assert page.locator(".tb-list").count() == 2
    ctx.close()


@pytest.mark.render
def test_the_edit_state_keeps_its_parts_still_with_the_foot_on_the_bottom_edge_and_fits_both_screens(browser, page_file):
    for w, h in ((360, 800), (1280, 900)):
        ctx, page, _ = reader(browser, page_file, "espn", w=w, h=h)
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
        ctx.close()


# ---- the guard: Edit is hidden when the page cannot reproduce the file ----------------------------------------

def guarded(browser, page_file, body):
    ctx, page, errors = reader(browser, page_file, "espn", init=serve(body))
    warnings = []
    page.on("console", lambda m: warnings.append(m.text) if m.type == "warning" else None)
    builder(page, RUN)
    page.wait_for_selector(".tb-card .tb-gain")
    return ctx, page, errors, warnings


def assert_shut(page):
    assert page.locator(".tb-card").count() == 3, "the offers themselves still show"
    assert page.locator("[data-tbedit]").count() == 0 and page.locator("[data-tbown]").count() == 0
    assert page.locator("[data-tbcopy]").count() == 3, "Copy offer is untouched"


def bold(doc):
    return doc["leagues"]["espn"]["teams"]["Purdy Big in Japan"]["Run It Back"]["bold"]


@pytest.mark.render
def test_a_file_whose_gain_the_page_cannot_reproduce_shuts_edit_and_names_the_offer(browser, page_file):
    bad = copy.deepcopy(FIXTURE)
    bold(bad)[1]["gain"] = 7.9                                                # the rule says 7.7
    ctx, page, errors, warnings = guarded(browser, page_file, bad)
    assert_shut(page)
    assert any("Purdy Big in Japan to Run It Back" in w and "bold[1]" in w for w in warnings), warnings
    page.locator(".lbp-back").click()
    page.locator(".lbp-back").click()
    page.wait_for_selector(".lb-grid")
    builder(page, RUN)                                                        # a shut guard stays shut for the session
    page.wait_for_selector(".tb-card .tb-gain")
    assert page.locator("[data-tbedit]").count() == 0
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_a_gain_within_the_tolerance_keeps_edit_and_a_different_drop_shuts_it(browser, page_file):
    near = copy.deepcopy(FIXTURE)
    bold(near)[1]["gain"] = 7.8
    ctx, page, _, warnings = guarded(browser, page_file, near)
    assert page.locator("[data-tbedit]").count() == 3 and warnings == []
    ctx.close()
    wrong = copy.deepcopy(FIXTURE)
    bold(wrong)[2]["drop"] = []
    ctx, page, _, warnings = guarded(browser, page_file, wrong)
    assert_shut(page)
    assert any("bold[2]" in w for w in warnings), warnings
    ctx.close()


@pytest.mark.render
def test_a_different_ir_move_shuts_edit_and_names_the_offer(browser, page_file):
    wrong = copy.deepcopy(FIXTURE)
    bold(wrong)[0]["ir_moves"] = bold(wrong)[2]["drop"]               # a player the rule drops, not moves
    ctx, page, _, warnings = guarded(browser, page_file, wrong)
    assert_shut(page)
    assert any("bold[0]" in w for w in warnings), warnings
    ctx.close()


def each_offer(doc):
    for lg in doc["leagues"].values():
        for ps in lg["teams"].values():
            for kinds in ps.values():
                for offers in kinds.values():
                    yield from offers


@pytest.mark.render
def test_the_old_shape_with_no_lineup_values_other_or_drop_shows_offers_and_no_edit(browser, page_file):
    old = copy.deepcopy(FIXTURE)
    for lg in old["leagues"].values():
        for k in ("lineup", "values", "other"):
            lg.pop(k)
    for o in each_offer(old):
        o.pop("drop")
        o.pop("ir_moves")
    ctx, page, errors, warnings = guarded(browser, page_file, old)
    assert_shut(page)
    assert page.locator(".tb-drop").count() == 0 and page.locator(".tb-ir").count() == 0
    assert any("Edit is off" in w for w in warnings), warnings
    ctx.close()
    assert errors == [], "an old file is a state, not an exception"


@pytest.mark.render
def test_a_file_from_before_the_drop_rule_shows_its_drops_and_no_edit(browser, page_file):
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
    ctx, page, errors, warnings = guarded(browser, page_file, before)
    assert_shut(page)
    assert page.locator(".tb-drop").count() == 1, "the cards still say who is dropped, as the file has it"
    assert page.locator(".tb-ir").count() == 0
    assert any("predates the drop rule" in w for w in warnings), warnings
    ctx.close()
    assert errors == []


def test_the_plant_the_tests_share_still_serves_the_fixture():
    assert json.dumps(FIXTURE) in PLANT
