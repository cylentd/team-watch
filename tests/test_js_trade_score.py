"""The trade builder's pure JavaScript (surface/lboard/tbscore.js, offers.js, tbpage.js) in Node, with no build and no
browser: the scorer (a port of ff-jarvis's rules.scoring and rules.drop) over every fixture offer, the room rule, the
partner's room (`their`, option B), the pitch text, the chips and the IR / drop lines as strings, and the guard
(`tbMismatch`) that shuts Edit when the page cannot reproduce the file.

Moved out of test_trade_edit.py 2026-10-05: each was a page load and a build to call a function with data. What the
page draws from them (the Edit button, the edit state, the copied message on a real clipboard) is still
test_trade_edit.py and test_trade_offers.py, in the browser.

The fixture (tests/fixtures/data/trade_offers.json) began as a cut of the file ff-jarvis's real writer made (branch
trade-edit, 29e54f2). Its drop-rule fields and its option-B fields (`last2`, `chips`, `their`) are hand-made: `their` was
worked out by an independent Python port of the room rule, so these tests check the JS port against something that is
not itself. Change a roster and the offers' gains, moves, drops and `their` have to be re-derived."""
import copy
import json

import pytest

from conftest import FIXTURES

FIXTURE = json.loads((FIXTURES / "data" / "trade_offers.json").read_text(encoding="utf-8"))
REAL = json.loads((FIXTURES / "trade_offers_ffjarvis.json").read_text(encoding="utf-8"))
ESPN = FIXTURE["leagues"]["espn"]
OWNER, PARTNER = "Purdy Big in Japan", "Run It Back"


@pytest.fixture(scope="module")
def tb(node_js):
    # lboard.js for lbNum, then the scorer, the offers' data and guard, and the page's string builders, as on the page.
    return node_js("surface/lboard/lboard.js", "surface/lboard/tbscore.js", "surface/lboard/offers.js", "surface/lboard/tbpage.js")


def bold(doc):
    return doc["leagues"]["espn"]["teams"][OWNER][PARTNER]["bold"]


def mismatch(tb, doc):
    lg = doc["leagues"]["espn"]
    return tb("tbMismatch", lg, {"name": OWNER}, {"name": PARTNER}, lg["teams"][OWNER][PARTNER])


def each_offer(doc):
    for lg in doc["leagues"].values():
        for ps in lg["teams"].values():
            for kinds in ps.values():
                for offers in kinds.values():
                    yield from offers


# ---- the scorer: every fixture offer, exactly; drops, floors, flex, ties, IR ------------------------------------

SCORE_ALL = """(data) => {
  const out = [];
  for (const [key, lg] of Object.entries(data.leagues)) for (const [owner, ps] of Object.entries(lg.teams))
    for (const [partner, kinds] of Object.entries(ps)) for (const kind of ["bold", "fair"]) for (const o of kinds[kind]){
      const mine = lg.values[owner], theirs = lg.values[partner];
      const r = tbGain(mine, tbResolve(o.send, mine), tbResolve(o.get, theirs), lg.lineup, tbOther(lg, owner));
      const th = tbTheir(theirs, tbResolve(o.send, mine), tbResolve(o.get, theirs), lg.lineup, tbOther(lg, partner));
      out.push({at: `${key} ${owner} ${partner} ${kind}`, js: r.gain, file: o.gain, ok: r.ok,
                drop: r.drop.map(p => p.name), want: o.drop.map(p => p.name),
                moves: r.irMoves.map(p => p.name), wantMoves: o.ir_moves.map(p => p.name),
                theirMoves: th.irMoves.map(p => p.name), wantTheirMoves: o.their.ir_moves.map(p => p.name),
                theirDrop: th.drop.map(p => p.name), wantTheirDrop: o.their.drop.map(p => p.name)});
    }
  return out;
}"""


def test_the_scorer_reproduces_every_fixture_gain_ir_move_and_drop_exactly(tb):
    rows = tb(SCORE_ALL, FIXTURE)
    assert len(rows) == 11
    for r in rows:
        assert r["js"] == r["file"] and r["ok"], r
        assert r["drop"] == r["want"] and r["moves"] == r["wantMoves"], r
    assert [r["drop"] for r in rows if r["drop"]] == [["Ollie Gordon II"]]
    assert [r["moves"] for r in rows if r["moves"]] == [["Marcus Mariota"]] * 5, "an injured player goes to IR, not to the waiver wire"


def test_the_partners_room_reproduces_every_fixture_their_exactly(tb):
    rows = tb(SCORE_ALL, FIXTURE)
    for r in rows:
        assert r["theirMoves"] == r["wantTheirMoves"] and r["theirDrop"] == r["wantTheirDrop"], r
    assert [(r["theirMoves"], r["theirDrop"]) for r in rows if r["theirMoves"] or r["theirDrop"]] == [
        (["Marcus Mariota"], []), (["Marcus Mariota"], ["Justice Hill"])], "two offers put the partner over his cap; the second cuts his lowest keep"


# The producer's own file for the drop rule (ff-jarvis drop-rule, f22e6ac, 2026-10-05): ESPN, 12 teams' values, owners
# Purdy Big in Japan (no moves or drops), FAFO! (5 IR moves, 22 drops) and Larry's World (3 moves, 3 drops, 7 protected).
# Every gain, ir_moves and drop in it is the producer's, so a port that reproduces them all follows `rules.drop`.
# It predates option B: the guard needs a `their` on every offer, so the page's own tbTheir stamps one. (The producer's
# own `their` is checked below, in its option-B file, where nothing is stamped.)
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
      const stamped = {};
      for (const kind of ["bold", "fair"]) stamped[kind] = pair[kind].map(o => {
        const mine = lg.values[owner], theirs = lg.values[partner], send = tbResolve(o.send, mine), get = tbResolve(o.get, theirs);
        const th = tbTheir(theirs, send, get, lg.lineup, tbOther(lg, partner));
        return Object.assign({}, o, {their: {ir_moves: th.irMoves, drop: th.drop}});
      });
      const why = tbMismatch(lg, {name: owner}, {name: partner}, stamped);
      if (why) guard.push(`${owner} to ${partner}: ${why}`);
    }
  return {out, guard};
}"""

HAND = """(data) => {
  const lg = data.leagues.espn, res = [];
  for (const [owner, ps] of Object.entries(lg.teams)) for (const [partner, kinds] of Object.entries(ps))
    for (const o of kinds.bold.concat(kinds.fair)) if (o.drop.length){
      const mine = lg.values[owner].map(p => Object.assign({}, p, {protect: p.protect || o.drop.some(d => d.name === p.name)}));
      const theirs = lg.values[partner];
      const r = tbGain(mine, tbResolve(o.send, mine), tbResolve(o.get, theirs), lg.lineup, tbOther(lg, owner));
      res.push({was: o.drop.map(p => p.name), now: r.drop.map(p => p.name), ok: r.ok, moves: r.irMoves.map(p => p.name)});
    }
  return res;
}"""


def test_the_scorer_reproduces_every_offer_of_ff_jarvis_own_drop_rule_file_exactly(tb):
    got = tb(REAL_ALL, REAL)
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
    hand = tb(HAND, REAL)
    assert len(hand) == 25
    for h in hand:
        assert not set(h["was"]) & set(h["now"]), h                      # a protected player is never dropped
        assert not h["ok"] or len(h["now"]) == len(h["was"]), h          # the same count, other players, or no legal drop
    assert all(h["ok"] and h["now"] for h in hand), "someone else goes instead (no legal drop is the synthetic test's)"


# ff-jarvis's own option-B file (branch option-b, b23bf06, 2026-10-05): ESPN, owners Purdy Big in Japan, Big Nasty Nate
# (`their.ir_moves` in 10 offers) and Half Asian Lives Matter (`their.drop` in 27), every partner, full values. Every
# gain, drop, ir_moves and `their` in it is the producer's, so a port that reproduces them all follows `rules.drop`
# for the partner as well. The guard is run on it as it is, with nothing stamped.
OPTION_B = json.loads((FIXTURES / "trade_offers_ffjarvis_optionb.json").read_text(encoding="utf-8"))

OPTION_B_ALL = """(data) => {
  const out = [], guard = [], names = list => list.map(p => p.name);
  for (const [key, lg] of Object.entries(data.leagues)) for (const [owner, ps] of Object.entries(lg.teams))
    for (const [partner, kinds] of Object.entries(ps)){
      const why = tbMismatch(lg, {name: owner}, {name: partner}, kinds);
      if (why) guard.push(`${owner} to ${partner}: ${why}`);
      for (const kind of ["bold", "fair"]) for (const o of kinds[kind]){
        const mine = lg.values[owner], theirs = lg.values[partner], send = tbResolve(o.send, mine), get = tbResolve(o.get, theirs);
        const r = tbGain(mine, send, get, lg.lineup, tbOther(lg, owner)), th = tbTheir(theirs, send, get, lg.lineup, tbOther(lg, partner));
        out.push({at: `${key} ${owner} ${partner} ${kind}`, owner, ok: r.ok, js: r.gain, file: o.gain,
                  drop: names(r.drop), want: names(o.drop), moves: names(r.irMoves), wantMoves: names(o.ir_moves),
                  theirMoves: names(th.irMoves), wantTheirMoves: names(o.their.ir_moves),
                  theirDrop: names(th.drop), wantTheirDrop: names(o.their.drop), short: th.short});
      }
    }
  return {out, guard};
}"""


def test_the_port_reproduces_every_gain_drop_ir_move_and_their_of_ff_jarvis_option_b_file_exactly(tb):
    got = tb(OPTION_B_ALL, OPTION_B)
    rows = got["out"]
    assert rows, "the file has offers"
    for r in rows:
        assert r["js"] == r["file"] and r["ok"], r
        assert r["drop"] == r["want"] and r["moves"] == r["wantMoves"], r
        assert r["theirMoves"] == r["wantTheirMoves"] and r["theirDrop"] == r["wantTheirDrop"], r
        assert not r["short"], r
    assert got["guard"] == [], "the guard accepts every pair of the producer's own file"
    # the file does exercise the partner's room, for both kinds of sentence
    assert sum(1 for r in rows if r["wantTheirMoves"]) >= 10 and sum(1 for r in rows if r["wantTheirDrop"]) >= 27


def test_the_option_b_file_has_chips_that_agree_across_its_players(tb):
    """last2 and chips are per player, so a player reads the same wherever he appears; Hot and Cold follow `rules.chips`."""
    lg = OPTION_B["leagues"]["espn"]
    seen = {p["name"]: (p["last2"], p["chips"], p["seen"]) for rows in lg["values"].values() for p in rows}
    for ps in lg["teams"].values():
        for kinds in ps.values():
            for offers in kinds.values():
                for o in offers:
                    for side in ("send", "get", "drop", "ir_moves"):
                        for p in o[side] + o["their"]["ir_moves"] + o["their"]["drop"]:
                            assert (p["last2"], p["chips"]) == seen[p["name"]][:2], p["name"]
    chips = {c for _, cs, _ in seen.values() for c in cs}
    assert chips <= {"Hot", "Cold", "Early pick"} and {"Hot", "Cold", "Early pick"} <= chips
    for name, (last2, cs, season) in seen.items():
        if last2 is None:
            assert "Hot" not in cs and "Cold" not in cs, name
        else:
            assert ("Hot" in cs) == (last2 - season >= 4) and ("Cold" in cs) == (season - last2 >= 4), (name, last2, season)


def score(tb, send, get):
    return tb("""([d, send, get]) => {
      const L = d.leagues.espn, mine = L.values["Purdy Big in Japan"], theirs = L.values["Run It Back"];
      const r = tbGain(mine, mine.filter(p => send.includes(p.name)), theirs.filter(p => get.includes(p.name)), L.lineup, tbOther(L, "Purdy Big in Japan"));
      return {gain: r.gain, drop: r.drop.map(p => p.name), ir: r.irMoves.map(p => p.name), ok: r.ok};
    }""", [FIXTURE, send, get])


def test_a_package_over_the_cap_drops_the_lowest_keep_non_starters_and_ir_never_counts(tb):
    # Purdy's side holds 15 players, one on IR, and two K/DST: 14 + 2 = 16, the cap.
    assert score(tb, ["Brock Purdy", "Kalif Raymond"], ["Chase Brown", "Christian Watson"]) == {"gain": 5.5, "drop": [], "ir": [], "ok": True}
    assert score(tb, ["Brock Purdy"], ["Chase Brown", "Christian Watson"]) == {"gain": 5.5, "drop": ["Ollie Gordon II"], "ir": [], "ok": True}
    assert score(tb, [], ["Chase Brown", "Christian Watson"])["drop"] == ["Ollie Gordon II", "Kalif Raymond"], "two over: lowest keep first"
    assert score(tb, ["Jordan Mason"], ["Chase Brown"])["drop"] == ["Ollie Gordon II"], "sending the player on IR frees no room"
    assert score(tb, [], ["Adonai Mitchell"]) == {"gain": 0, "drop": [], "ir": [], "ok": True}, "a player on IR does not count toward the cap"
    assert score(tb, ["Tee Higgins"], []) == {"gain": -4.2, "drop": [], "ir": [], "ok": True}, "a gain can be negative"
    # Purdy's IR has one free slot (lineup.ir 2, Mason in one): Mariota (Out, not on IR) takes it, nobody is dropped.
    assert score(tb, [], ["Marcus Mariota"]) == {"gain": 0, "drop": [], "ir": ["Marcus Mariota"], "ok": True}


def test_ir_moves_come_before_drops_and_protect_and_keep_decide_who_is_dropped(tb):
    got = tb("""() => {
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


def test_a_package_with_no_legal_drop_is_not_ok(tb):
    got = tb("""() => {
      const P = (name, pos, proj, o) => Object.assign({name, pos, proj, seen: proj, ir: false, keep: proj, ir_ok: false, protect: true}, o || {});
      const lu = {slots: {QB: 1}, flex: [], floor: {QB: 10, RB: 4, WR: 5, TE: 6}, cap: 2, ir: 1};
      const r = tbGain([P("q", "QB", 15), P("r", "RB", 8)], [], [P("n", "WR", 7)], lu, 0);
      return {ok: r.ok, gain: r.gain, drop: r.drop.length};
    }""")
    assert got == {"ok": False, "gain": 0, "drop": 0}


def test_candidates_ties_floors_flex_and_other_follow_the_rule_in_the_file(tb):
    got = tb("""() => {
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


# ---- the partner's room (`their`, option B) ----------------------------------------------------------------------

def test_the_partners_room_runs_the_same_rule_on_his_roster_and_never_drops_who_he_just_received(tb):
    got = tb("""() => {
      const P = (name, pos, proj, o) => Object.assign({name, pos, proj, seen: proj, ir: false, keep: proj, ir_ok: false, protect: false}, o || {});
      const lu = {slots: {QB: 1}, flex: [{n: 1, pos: ["RB", "WR"]}], floor: {QB: 10, RB: 4, WR: 5, TE: 6}, cap: 4, ir: 1};
      const theirs = [P("q", "QB", 15), P("r", "RB", 8), P("w", "WR", 6), P("low", "WR", 2)];          // four players, at the cap
      const mine = [P("a", "WR", 1), P("b", "RB", 1, {keep: 0}), P("hurt", "WR", 0, {keep: 9, ir_ok: true})];
      const names = r => ({ir: r.irMoves.map(p => p.name), drop: r.drop.map(p => p.name), short: r.short});
      return {
        // one in, none out: one over, the lowest keep who did not just arrive goes, never a, b or hurt (his)
        oneIn: names(tbTheir(theirs, [mine[0]], [], lu, 0)),
        // an even swap: nobody is over
        swap: names(tbTheir(theirs, [mine[0]], [theirs[3]], lu, 0)),
        // he receives an IR-eligible player already on IR: no room is needed
        onIr: names(tbTheir(theirs, [Object.assign({}, mine[2], {ir: true})], [], lu, 0)),
        // his own injured player goes to the free IR slot before anyone is cut
        hurtHis: names(tbTheir(theirs.concat([P("inj", "WR", 0, {keep: 12, ir_ok: true})]), [mine[0]], [theirs[3]], lu, 0)),
        // his K/DST count toward his cap
        other: names(tbTheir(theirs, [mine[0]], [theirs[3]], lu, 1)),
        empty: names(tbTheir(theirs, [], [], lu, 0)),
        // the received players are the only ones left to cut: protected by arriving, so nobody is released
        short: names(tbTheir([P("q", "QB", 15, {protect: true}), P("r", "RB", 8, {protect: true}), P("w", "WR", 6, {protect: true}), P("v", "WR", 5, {protect: true})],
                             [mine[0], mine[1]], [], lu, 0)),
      };
    }""")
    assert got["oneIn"] == {"ir": [], "drop": ["low"], "short": False}
    assert got["swap"] == {"ir": [], "drop": [], "short": False}
    assert got["onIr"] == {"ir": [], "drop": [], "short": False}
    assert got["hurtHis"] == {"ir": ["inj"], "drop": [], "short": False}
    assert got["other"] == {"ir": [], "drop": ["w"], "short": False}, "the K/DST fills a spot, so an even swap needs a cut"
    assert got["empty"] == {"ir": [], "drop": [], "short": False}
    assert got["short"] == {"ir": [], "drop": [], "short": True}


# ---- the lines on an offer: IR and drop; the chips; the pitch ----------------------------------------------------

def test_an_offer_with_both_lines_puts_to_ir_above_you_drop(tb):
    html = tb("""() => tbRoomHTML({ir_moves: [{name: "Caleb Williams"}, {name: "Saquon Barkley"}], drop: [{name: "Ollie Gordon II"}]})""")
    assert html.index("To IR: C. Williams, S. Barkley") < html.index("You drop: O. Gordon II")
    assert tb("""() => tbRoomHTML({ir_moves: [], drop: []}) + tbRoomHTML({})""") == "", "no line when there is nothing"


def test_chips_are_small_tags_after_the_status_pill_and_nothing_when_there_are_none(tb):
    row = {"pos": "WR", "name": "T. Higgins", "injury": "Questionable"}
    assert tb("tbTagsHTML", {**row, "injury": None}) == ""
    assert tb("tbTagsHTML", {**row, "injury": None, "chips": []}) == ""
    assert tb("tbTagsHTML", {**row, "injury": None, "chips": ["Hot"]}) == '<span class="tb-tags"><i class="tb-chip hot">Hot</i></span>'
    both = tb("tbTagsHTML", {**row, "chips": ["Cold", "Early pick"]})
    assert both.index("tb-inj") < both.index("tb-chip cold") < both.index("tb-chip early")
    assert 'class="tb-chip early">Early pick<' in both
    assert tb("tbTagsHTML", {**row, "injury": None, "chips": ["Burning"]}) == "", "a chip the page does not know is left out"


def test_a_player_row_carries_his_chips_and_the_card_says_nothing_of_the_partners_room(tb):
    html = tb("tbPlayerHTML", {"pos": "WR", "name": "Christian Watson", "injury": None, "chips": ["Hot", "Early pick"]})
    assert html.count("tb-chip") == 2 and "C. Watson" in html
    assert "roster" not in tb("tbRoomHTML", {"ir_moves": [], "drop": [], "their": {"ir_moves": [{"name": "Marcus Mariota"}], "drop": []}}).lower()


def hot(name, season, last2, chips=("Hot",)):
    return {"name": name, "seen": season, "last2": last2, "chips": list(chips)}


def test_the_pitch_quotes_a_hot_player_the_reader_sends_on_his_last_2_and_everyone_else_on_his_season_average(tb):
    cold = {"name": "Kalif Raymond", "seen": 9.4, "last2": 4.1, "chips": ["Cold"]}
    plain = lambda n, s: {"name": n, "seen": s, "last2": s + 0.4, "chips": []}   # noqa: E731
    # as today, when no one is Hot (a Cold player is quoted on his season average too)
    assert tb("tbText", {"send": [plain("Brock Purdy", 28.8), cold], "get": [plain("Chase Brown", 11.4)]}) == \
        "Trade? I send Purdy (28.8 a game) and Raymond (9.4) for Brown (11.4)."
    # a Hot player the reader GETS is quoted on his season average: his last 2 would inflate the ask
    assert tb("tbText", {"send": [plain("Brock Purdy", 28.8)], "get": [hot("Christian Watson", 16.5, 22.6)]}) == \
        "Trade? I send Purdy (28.8 a game) for Watson (16.5)."
    assert tb("tbText", {"send": [hot("Ollie Gordon II", 10.2, 15.2)], "get": [hot("Christian Watson", 16.5, 22.6)]}) == \
        "Trade? I send Gordon II (15.2 a game his last 2) for Watson (16.5).", "sold on the streak, asked for on the season"
    # a Hot player ahead of the first season average: the unit lands on that average, not on a number that is a last-2
    assert tb("tbText", {"send": [hot("Ollie Gordon II", 10.2, 15.2), plain("Brock Purdy", 28.8)], "get": [plain("Chase Brown", 11.4)]}) == \
        "Trade? I send Gordon II (15.2 a game his last 2) and Purdy (28.8 a game) for Brown (11.4)."
    # a player with no last2 is quoted on his season average even with a stray Hot chip
    assert tb("tbText", {"send": [{"name": "Brock Purdy", "seen": 28.8, "last2": None, "chips": ["Hot"]}], "get": [plain("Chase Brown", 11.4)]}) == \
        "Trade? I send Purdy (28.8 a game) for Brown (11.4)."


def test_the_pitch_ends_with_one_sentence_on_the_partners_room_or_none(tb):
    side = {"send": [{"name": "Brock Purdy", "seen": 28.8, "chips": []}], "get": [{"name": "Chase Brown", "seen": 11.4, "chips": []}]}
    base = "Trade? I send Purdy (28.8 a game) for Brown (11.4)."
    smith, johnson = {"name": "Darren Smith"}, {"name": "Kyle Johnson"}
    assert tb("tbText", {**side}) == base, "an offer from before option B has no `their`"
    assert tb("tbText", {**side, "their": {"ir_moves": [], "drop": []}}) == base, "nothing to say, nothing said"
    assert tb("tbText", {**side, "their": {"ir_moves": [smith], "drop": []}}) == base + " D. Smith can go to your IR slot, so you don't cut anyone."
    assert tb("tbText", {**side, "their": {"ir_moves": [], "drop": [johnson]}}) == base + " You'd only need to cut K. Johnson."
    both = tb("tbText", {**side, "their": {"ir_moves": [smith], "drop": [johnson]}})
    assert both == base + " D. Smith can go to your IR slot. You'd only need to cut K. Johnson.", "no 'you don't cut anyone' before a cut"
    two = tb("tbText", {**side, "their": {"ir_moves": [smith, {"name": "Amon-Ra St. Brown"}], "drop": []}})
    assert two.endswith(" D. Smith and A. St. Brown can go to your IR slots, so you don't cut anyone.")
    assert tb("tbText", {**side, "their": {"ir_moves": [], "drop": [johnson, smith]}}).endswith(" You'd only need to cut K. Johnson and D. Smith.")


# ---- the guard: Edit is shut when the page cannot reproduce the file -----------------------------------------------

def test_the_guard_accepts_every_pair_of_the_fixture(tb):
    for lgk, lg in FIXTURE["leagues"].items():
        for owner, ps in lg["teams"].items():
            for partner, pair in ps.items():
                assert tb("tbMismatch", lg, {"name": owner}, {"name": partner}, pair) == "", (lgk, owner, partner)


def test_a_gain_the_page_cannot_reproduce_is_named_and_one_within_the_tolerance_is_not(tb):
    bad = copy.deepcopy(FIXTURE)
    bold(bad)[1]["gain"] = 7.9                                                # the rule says 7.7
    why = mismatch(tb, bad)
    assert "bold[1]" in why and "7.7" in why and "7.9" in why, why
    near = copy.deepcopy(FIXTURE)
    bold(near)[1]["gain"] = 7.8
    assert mismatch(tb, near) == ""


def test_a_different_drop_ir_move_or_partner_room_is_named(tb):
    wrong = copy.deepcopy(FIXTURE)
    bold(wrong)[2]["drop"] = []
    assert "bold[2]" in mismatch(tb, wrong)
    moved = copy.deepcopy(FIXTURE)
    bold(moved)[0]["ir_moves"] = bold(moved)[2]["drop"]                       # a player the rule drops, not moves
    assert "bold[0]" in mismatch(tb, moved)
    theirs = copy.deepcopy(FIXTURE)
    bold(theirs)[1]["their"]["drop"] = []                                     # the rule says Raymond goes
    assert "bold[1]" in mismatch(tb, theirs) and "them differently" in mismatch(tb, theirs)
    theirs = copy.deepcopy(FIXTURE)
    bold(theirs)[0]["their"]["ir_moves"] = []                                 # the rule says Mariota goes to IR
    assert "bold[0]" in mismatch(tb, theirs)


def test_a_file_without_their_fails_closed_as_one_without_a_drop_does(tb):
    old = copy.deepcopy(FIXTURE)
    for o in each_offer(old):
        o.pop("their")
    assert "no drop, ir_moves or their" in mismatch(tb, old)
    half = copy.deepcopy(FIXTURE)
    del bold(half)[0]["their"]["drop"]
    assert "bold[0]" in mismatch(tb, half)


def test_the_old_shapes_say_why_there_is_no_edit(tb):
    old = copy.deepcopy(FIXTURE)
    lg = old["leagues"]["espn"]
    for k in ("lineup", "values", "other"):
        lg.pop(k)
    assert mismatch(tb, old) == "no lineup or values for this pair"
    before = copy.deepcopy(FIXTURE)
    lg = before["leagues"]["espn"]
    lg["lineup"].pop("ir")
    assert "predates the drop rule" in mismatch(tb, before)
