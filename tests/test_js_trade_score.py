"""The trade builder's pure JavaScript (surface/lboard/tbscore.js, offers.js, tbcard.js) in Node, with no build and no
browser: the scorer (a port of ff-jarvis's rules.scoring and rules.drop, rest-of-season points since 2026-10-06) over every
fixture offer, the room rule, the partner's room and gain (`their`), the pitch text, the chips and the IR / drop lines as
strings, and the guard (`tbMismatch`) that shuts Edit when the page cannot reproduce the file.

Moved out of test_trade_edit.py 2026-10-05: each was a page load and a build to call a function with data. What the
page draws from them (the Edit button, the edit state, the copied message on a real clipboard) is still
test_trade_edit.py and test_trade_offers.py, in the browser.

Two files hold the oracle. tests/fixtures/trade_offers_ffjarvis.json is the producer's own file (ff-jarvis trade-ros,
1b1fe82: 381 offers in three leagues, every gain, drop, IR move and `their` as the producer's search wrote them), so a
port that reproduces all of it follows `rules.scoring` and `rules.drop`. tests/fixtures/data/trade_offers.json is a cut of
it for the page (ESPN's Purdy Big in Japan and Run It Back); its AYO offers and every package hand-built below were worked
out by an independent pure-Python reading of the two rule texts (the producer's own test holds one), not by this port."""
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
    return node_js("surface/lboard/lboard.js", "surface/lboard/tbscore.js", "surface/lboard/offers.js", "surface/lboard/tbcard.js")


def mine(doc):
    """OWNER's offers in the fixture, the flat list v2 writes (best gain first, each with its `partner`)."""
    return doc["leagues"]["espn"]["teams"][OWNER]


def mismatch(tb, doc):
    lg = doc["leagues"]["espn"]
    return tb("tbMismatch", lg, {"name": OWNER}, lg["teams"][OWNER])


def each_offer(doc):
    for lg in doc["leagues"].values():
        for offers in lg["teams"].values():
            yield from offers


# ---- the scorer: every offer of both files, exactly --------------------------------------------------------------

SCORE_ALL = """(data) => {
  const out = [], names = list => list.map(p => p.name);
  for (const [key, lg] of Object.entries(data.leagues)) for (const [owner, list] of Object.entries(lg.teams))
    for (const o of list){
      const partner = o.partner, mine = lg.values[owner], theirs = lg.values[partner];
      const send = tbResolve(o.send, mine), get = tbResolve(o.get, theirs);
      const r = tbGain(mine, send, get, lg.lineup, tbOther(lg, owner), lg.weeks_left);
      const th = tbTheir(theirs, send, get, lg.lineup, tbOther(lg, partner), lg.weeks_left);
      out.push({at: `${key} ${owner} ${partner}`, owner, ok: r.ok, js: r.gain, file: o.gain,
                drop: names(r.drop), want: names(o.drop), moves: names(r.irMoves), wantMoves: names(o.ir_moves),
                theirGain: th.gain, wantTheirGain: o.their.gain, short: th.short,
                theirMoves: names(th.irMoves), wantTheirMoves: names(o.their.ir_moves),
                theirDrop: names(th.drop), wantTheirDrop: names(o.their.drop)});
    }
  return out;
}"""


def reproduced(row):
    return bool(row["ok"] and not row["short"]
                and row["js"] == row["file"] and row["theirGain"] == row["wantTheirGain"]
                and row["drop"] == row["want"] and row["moves"] == row["wantMoves"]
                and row["theirMoves"] == row["wantTheirMoves"] and row["theirDrop"] == row["wantTheirDrop"])


def test_the_scorer_reproduces_every_fixture_gain_drop_ir_move_and_their_exactly(tb):
    rows = tb(SCORE_ALL, FIXTURE)
    assert len(rows) == 8
    assert [r for r in rows if not reproduced(r)] == []
    assert [r["drop"] for r in rows if r["drop"]] == [["Isaiah Davis"]] * 3 + [["Kalif Raymond"]], "Run It Back's three offers and AYO's first put the owner over his cap"
    assert [r["theirDrop"] for r in rows if r["theirDrop"]] == [["Isaiah Davis"]] * 3, "Purdy's three offers put Run It Back over his"


@pytest.mark.req("Trade finder", ac="the scorer reproduces every gain, drop and IR move of the producer's own file exactly")
def test_the_scorer_reproduces_all_381_offers_of_ff_jarvis_own_file_with_no_mismatch(tb):
    rows = tb(SCORE_ALL, REAL)
    assert len(rows) == 381
    bad = [r for r in rows if not (r["ok"] and not r["short"] and r["js"] == r["file"] and r["theirGain"] == r["wantTheirGain"]
                                   and r["drop"] == r["want"] and r["moves"] == r["wantMoves"]
                                   and r["theirMoves"] == r["wantTheirMoves"] and r["theirDrop"] == r["wantTheirDrop"])]
    assert bad == [], bad[:3]
    # the file does exercise every branch of the rule, on both sides of the trade
    assert sum(1 for r in rows if r["wantMoves"]) == 19 and sum(1 for r in rows if r["want"]) == 41
    assert sum(1 for r in rows if r["wantTheirMoves"]) == 48 and sum(1 for r in rows if r["wantTheirDrop"]) == 127
    assert any(r["file"] != 0 and r["wantTheirGain"] == 0 for r in rows), "a partner who breaks even"


GUARD_ALL = """(data) => {
  TB_DATA = data;
  const shut = [], open = [];
  for (const [key, lg] of Object.entries(data.leagues)) for (const owner of Object.keys(lg.values)){
    const why = tbMismatch(lg, {name: owner}, lg.teams[owner] || []);
    if (why) shut.push(`${key} ${owner}: ${why}`);
    TB_GUARD = {data: null, shut: false, seen: {}};
    if (tbEditOk({key}, {name: owner})) open.push(`${key} ${owner}`);
  }
  return {shut, open};
}"""


@pytest.mark.req("Trade finder", ac="the fail-closed guard passes every owner of the producer's real file")
def test_the_guard_passes_every_owner_of_the_whole_producer_file(tb):
    got = tb(GUARD_ALL, REAL)
    assert got["shut"] == [], got["shut"]
    owners = sum(len(lg["values"]) for lg in REAL["leagues"].values())
    assert len(got["open"]) == owners == 36, "all 36 owners, the ones with no offer included (Larry's World has none)"
    assert any("Larry's World" in o for o in got["open"])


# ---- the rule, case by case, on players made for the case --------------------------------------------------------

def ros(tb, roster, lu, weeks=10):
    return tb("""([roster, lu, weeks]) => tbRos(roster, lu, weeks)""", [roster, lu, weeks])


def pl(name, pos, pg, **o):
    return {"name": name, "pos": pos, "proj": pg, "ros_pg": pg, "games": 10.0, "priced": True, "seen": pg, "ir": False,
            "keep": round(pg * 10, 2), "ir_ok": False, "protect": False, **o}


LU = {"slots": {"QB": 1}, "flex": [], "floor": {"QB": 0, "RB": 0, "WR": 0, "TE": 0},
      "ros_floor": {"QB": 15, "RB": 4, "WR": 5, "TE": 6}, "cap": 4, "ir": 1}
FLEXLU = {**LU, "slots": {"QB": 1}, "flex": [{"n": 1, "pos": ["RB", "WR"]}]}


def test_a_starter_fills_the_slot_for_his_games_in_thousandths_of_a_point(tb):
    # 20 a game over 10 games (W = 10 weeks, one slot: 100 tenths of a game): 2000 hundredths x 100 tenths.
    assert ros(tb, [pl("q", "QB", 20.0)], LU) == 200000


def test_a_starters_missed_games_go_to_the_next_candidate_then_to_the_wire(tb):
    q = pl("q", "QB", 20.0, games=8.0)
    assert ros(tb, [q], LU) == 160000 + 15 * 100 * 20, "8 games at 20, the other 2 on the wire at 15 (the bar)"
    assert ros(tb, [q, pl("b", "QB", 17.0)], LU) == 160000 + 1700 * 20, "the backup takes the missed 2 games"
    assert ros(tb, [q, pl("b", "QB", 15.0)], LU) == 160000 + 1500 * 20, "a backup no better than the wire is the wire"
    assert ros(tb, [], LU) == 150000, "an empty slot is worth the wire for every game"


def test_the_best_points_a_game_fills_first_whatever_his_games(tb):
    # 12 a game for 4 games, 10 a game for 10: the better player takes his 4 games, the other the remaining 6 (one slot, 10 weeks)
    assert ros(tb, [pl("a", "RB", 12.0, games=4.0), pl("b", "RB", 10.0)], {**LU, "slots": {"RB": 1}}) == 1200 * 40 + 1000 * 60


def test_a_flex_slot_takes_what_the_fixed_slot_left_and_its_bar_is_the_highest_wire_of_its_positions(tb):
    r1, r2, w = pl("r1", "RB", 12.0), pl("r2", "RB", 10.0), pl("w", "WR", 8.0)
    lu = {**FLEXLU, "slots": {"RB": 1}}
    assert ros(tb, [r1, r2, w], lu) == 1200 * 100 + 1000 * 100, "the RB slot takes r1, the RB/WR flex takes r2: w stays on the bench"
    short = pl("r1", "RB", 12.0, games=6.0)
    assert ros(tb, [short, r2, w], lu) == 1200 * 60 + 1000 * 40 + 1000 * 60 + 800 * 40, "the missed 4 games run down the candidates, and into the flex"
    assert ros(tb, [pl("w", "WR", 4.5)], {**FLEXLU, "slots": {}}) == 500 * 100, "a flex slot's bar is the larger of the RB (4) and WR (5) wires"


def test_an_ir_player_counts_for_the_games_he_is_expected_to_play(tb):
    hurt = pl("ir", "RB", 12.0, games=4.0, ir=True)
    lu = {**LU, "slots": {"RB": 1}}
    assert ros(tb, [hurt, pl("b", "RB", 10.0)], lu) == 1200 * 40 + 1000 * 60


def test_the_gain_is_points_to_one_decimal_half_away_from_zero(tb):
    assert [tb("tbPts", d) for d in (0, 49, 50, 149, 150, -49, -50, -150, 20000)] == [0, 0, 0.1, 0.1, 0.2, 0, -0.1, -0.2, 20.0]
    assert tb("() => Object.is(tbPts(-49), -0)") is False, "a loss that rounds to nothing is 0, not -0"


def score(tb, send, get):
    return tb("""([d, send, get]) => {
      const L = d.leagues.espn, mine = L.values["Purdy Big in Japan"], theirs = L.values["Run It Back"];
      const s = mine.filter(p => send.includes(p.name)), g = theirs.filter(p => get.includes(p.name));
      const r = tbGain(mine, s, g, L.lineup, tbOther(L, "Purdy Big in Japan"), L.weeks_left);
      const th = tbTheir(theirs, s, g, L.lineup, tbOther(L, "Run It Back"), L.weeks_left);
      return {gain: r.gain, drop: r.drop.map(p => p.name), ir: r.irMoves.map(p => p.name), ok: r.ok, their: th.gain};
    }""", [FIXTURE, send, get])


def test_a_package_over_the_cap_drops_the_lowest_keep_non_starters_and_ir_never_counts(tb):
    # Purdy's side holds 15 players, one on IR (the one slot), and two K/DST: 14 + 2 = 16, the cap. Every number below is the
    # independent Python reading's, worked from fixture rows.
    assert score(tb, ["Brock Purdy", "Kalif Raymond"], ["Bijan Robinson", "Kyren Williams"]) == {"gain": 158.2, "drop": [], "ir": [], "ok": True, "their": -172.8}
    assert score(tb, ["Brock Purdy"], ["Bijan Robinson", "Kyren Williams"])["drop"] == ["Ollie Gordon II"], "one over: the lowest keep goes"
    two = score(tb, [], ["Bijan Robinson", "Kyren Williams"])
    assert (two["gain"], two["drop"]) == (168.7, ["Ollie Gordon II", "Kalif Raymond"]), "two over: lowest keep first"
    assert score(tb, ["Jordan Mason"], ["Bijan Robinson"])["drop"] == ["Ollie Gordon II"], "sending the player on IR frees no room"
    assert score(tb, [], ["Jordyn Tyson"]) == {"gain": 0, "drop": [], "ir": [], "ok": True, "their": 0}, "a player on IR does not count toward the cap"
    assert score(tb, ["Tee Higgins"], [])["gain"] == -60.8, "a gain can be negative"
    assert score(tb, ["Tee Higgins"], [])["their"] == 60.5, "and the partner's is the other side of it here"
    # Mason (the one IR slot) goes: Coker (Out, ir_ok) takes the free slot, nobody is dropped
    assert score(tb, ["Jordan Mason"], ["Jalen Coker"]) == {"gain": 4.6, "drop": [], "ir": ["Jalen Coker"], "ok": True, "their": -12.5}
    assert score(tb, [], ["Jalen Coker"])["drop"] == ["Ollie Gordon II"], "the slot is full: a drop, not a move"


def test_ir_moves_come_before_drops_and_protect_and_keep_decide_who_is_dropped(tb):
    got = tb("""(src) => {
      const P = (name, pos, pg, o) => Object.assign({name, pos, proj: pg, ros_pg: pg, games: 10, priced: true, seen: pg, ir: false, keep: pg, ir_ok: false, protect: false}, o || {});
      const lu = ir => ({slots: {QB: 1}, flex: [{n: 1, pos: ["RB", "WR"]}], floor: {QB: 10, RB: 4, WR: 5, TE: 6}, ros_floor: {QB: 10, RB: 4, WR: 5, TE: 6}, cap: 4, ir});
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
        keepNotPg: room(full.map(p => p.name === "w" ? Object.assign({}, p, {keep: 1}) : p).concat([P("hi", "WR", 0, {keep: 20})]), 1),
        ties: room(ties.concat([P("y", "WR", 1, {keep: 3, seen: 2})]), 0),              // cap 4, six players: two over
        gain: tbGain(base(), [], [P("new", "RB", 9)], lu(1), 0, 10), gainFull: tbGain(full, [], [P("new", "RB", 9)], lu(1), 0, 10),
        empty: tbGain(base(), [], [], lu(1), 0, 10),
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
    assert got["keepNotPg"]["drop"] == ["w", "low"], "keep, not points a game, orders the drops: hi (0 a game, keep 20) outlasts low (2 a game, keep 2)"
    # ties on keep 3: lower seen first, then name. a (seen 5) is the last to go though it sorts first by name.
    assert got["ties"]["drop"] == ["b", "c", "y"], got["ties"]
    # new RB 9 replaces r (8): +1 a game over 10 games, +10.0 points. The IR move (inj) and the drop (low) change nothing: the
    # mover stays on the roster and `low` never played; with the IR slot full low and w are dropped instead, the same 10.0.
    assert got["gain"]["irMoves"][0]["name"] == "inj" and [p["name"] for p in got["gainFull"]["drop"]] == ["low", "w"]
    assert (got["gain"]["gain"], got["gainFull"]["gain"]) == (10.0, 10.0)
    assert got["empty"] == {"gain": 0, "drop": [], "irMoves": [], "ok": False}


def test_a_package_with_no_legal_drop_is_not_ok(tb):
    got = tb("""() => {
      const P = (name, pos, pg, o) => Object.assign({name, pos, proj: pg, ros_pg: pg, games: 10, priced: true, seen: pg, ir: false, keep: pg * 10, ir_ok: false, protect: true}, o || {});
      const lu = {slots: {QB: 1}, flex: [], floor: {QB: 10, RB: 4, WR: 5, TE: 6}, ros_floor: {QB: 10, RB: 4, WR: 5, TE: 6}, cap: 2, ir: 1};
      const r = tbGain([P("q", "QB", 15), P("r", "RB", 8)], [], [P("n", "WR", 7)], lu, 0, 10);
      return {ok: r.ok, gain: r.gain, drop: r.drop.length};
    }""")
    assert got == {"ok": False, "gain": 0, "drop": 0}


def test_starters_follow_points_a_game_then_games_then_name_and_the_drop_pool_leaves_them_alone(tb):
    got = tb("""() => {
      const P = (name, pos, pg, g, ir) => ({name, pos, proj: 0, ros_pg: pg, games: g, priced: true, seen: 1, ir: !!ir, keep: pg * g, ir_ok: false, protect: false});
      const wide = {slots: {QB: 1}, flex: [{n: 2, pos: ["RB", "WR"]}], floor: {QB: 10, RB: 4, WR: 5, TE: 6}, ros_floor: {QB: 10, RB: 4, WR: 5, TE: 6}, cap: 5, ir: 1};
      const ros = [P("q", "QB", 15, 10), P("a", "RB", 8, 10), P("w1", "WR", 6, 5), P("w2", "WR", 6, 9), P("w3", "WR", 6, 9),
                   P("x", "TE", 1, 7), P("y", "TE", 1, 2), P("z", "TE", 1, 2), P("ir", "RB", 20, 10, true)];
      const names = (cap, other) => tbDrops(ros, [], Object.assign({}, wide, {cap}), other).drop.map(p => p.name);
      return {starters: [...tbStarters(ros, wide)].sort(), dropOne: names(7, 0), dropThree: names(5, 0), dropWithOther: names(6, 1),
              none: tbGain(ros, [], [], wide, 0, 10), short: tbDrops(ros, [], Object.assign({}, wide, {cap: 1}), 0).short};
    }""")
    # Candidates: ros_pg desc, games desc, name asc, players on IR never start. a (8) and w2 (6, 9 games; w3 ties it, w2 first by name).
    assert got["starters"] == ["a", "q", "w2"]
    # Drops (keep = pg x games): lowest keep first, never a starter nor a player on IR: y and z (2), x (7), w1 (30), w3 (54).
    assert got["dropOne"] == ["y"]
    assert got["dropThree"] == ["y", "z", "x"]
    assert got["dropWithOther"] == ["y", "z", "x"], "a K/DST the roster also holds counts toward the cap and is never released"
    assert got["none"] == {"gain": 0, "drop": [], "irMoves": [], "ok": False}, "an empty package is not scored"
    assert got["short"] is True, "a cap that the non-starters cannot reach is reported, not hidden"


# ---- the partner's room and his gain (`their`) -------------------------------------------------------------------

def test_the_partners_room_runs_the_same_rule_on_his_roster_and_never_drops_who_he_just_received(tb):
    got = tb("""() => {
      const P = (name, pos, pg, o) => Object.assign({name, pos, proj: pg, ros_pg: pg, games: 10, priced: true, seen: pg, ir: false, keep: pg * 10, ir_ok: false, protect: false}, o || {});
      const lu = {slots: {QB: 1}, flex: [{n: 1, pos: ["RB", "WR"]}], floor: {QB: 10, RB: 4, WR: 5, TE: 6}, ros_floor: {QB: 10, RB: 4, WR: 5, TE: 6}, cap: 4, ir: 1};
      const theirs = [P("q", "QB", 15), P("r", "RB", 8), P("w", "WR", 6), P("low", "WR", 2)];          // four players, at the cap
      const mine = [P("a", "WR", 1), P("b", "RB", 1, {keep: 0}), P("hurt", "WR", 0, {keep: 9, ir_ok: true})];
      const names = r => ({ir: r.irMoves.map(p => p.name), drop: r.drop.map(p => p.name), short: r.short});
      return {
        // one in, none out: one over, the lowest keep who did not just arrive goes, never a, b or hurt (his)
        oneIn: names(tbTheir(theirs, [mine[0]], [], lu, 0, 10)),
        // an even swap: nobody is over
        swap: names(tbTheir(theirs, [mine[0]], [theirs[3]], lu, 0, 10)),
        // he receives an IR-eligible player already on IR: no room is needed
        onIr: names(tbTheir(theirs, [Object.assign({}, mine[2], {ir: true})], [], lu, 0, 10)),
        // his own injured player goes to the free IR slot before anyone is cut
        hurtHis: names(tbTheir(theirs.concat([P("inj", "WR", 0, {keep: 12, ir_ok: true})]), [mine[0]], [theirs[3]], lu, 0, 10)),
        // his K/DST count toward his cap
        other: names(tbTheir(theirs, [mine[0]], [theirs[3]], lu, 1, 10)),
        empty: names(tbTheir(theirs, [], [], lu, 0, 10)),
        // the received players are the only ones left to cut: protected by arriving, so nobody is released
        short: names(tbTheir([P("q", "QB", 15, {protect: true}), P("r", "RB", 8, {protect: true}), P("w", "WR", 6, {protect: true}), P("v", "WR", 5, {protect: true})],
                             [mine[0], mine[1]], [], lu, 0, 10)),
      };
    }""")
    assert got["oneIn"] == {"ir": [], "drop": ["low"], "short": False}
    assert got["swap"] == {"ir": [], "drop": [], "short": False}
    assert got["onIr"] == {"ir": [], "drop": [], "short": False}
    assert got["hurtHis"] == {"ir": ["inj"], "drop": [], "short": False}
    assert got["other"] == {"ir": [], "drop": ["w"], "short": False}, "the K/DST fills a spot, so an even swap needs a cut"
    assert got["empty"] == {"ir": [], "drop": [], "short": False}
    assert got["short"] == {"ir": [], "drop": [], "short": True}


def test_the_partners_gain_is_his_rest_of_season_lineup_after_the_trade_less_before(tb):
    got = tb("""() => {
      const P = (name, pos, pg, o) => Object.assign({name, pos, proj: pg, ros_pg: pg, games: 10, priced: true, seen: pg, ir: false, keep: pg * 10, ir_ok: false, protect: false}, o || {});
      const lu = {slots: {RB: 1}, flex: [], floor: {QB: 0, RB: 4, WR: 5, TE: 6}, ros_floor: {QB: 0, RB: 4, WR: 5, TE: 6}, cap: 9, ir: 1};
      const theirs = [P("r", "RB", 10)], x = P("x", "RB", 12), y = P("y", "RB", 8);
      return {up: tbTheir(theirs, [x], [theirs[0]], lu, 0, 10).gain,      // he swaps r (10) for x (12): +2 a game over 10 games
              down: tbTheir(theirs, [y], [theirs[0]], lu, 0, 10).gain,    // r (10) for y (8): -20.0
              none: tbTheir(theirs, [], [], lu, 0, 10).gain};
    }""")
    assert got == {"up": 20.0, "down": -20.0, "none": 0}


# ---- the lines on an offer: IR and drop; the chips; the pitch ----------------------------------------------------

def test_an_offer_with_both_lines_puts_to_ir_above_you_drop(tb):
    html = tb("""() => tbRoomHTML({ir_moves: [{name: "Caleb Williams"}, {name: "Saquon Barkley"}], drop: [{name: "Ollie Gordon II"}]})""")
    assert html.index("To IR: C. Williams, S. Barkley") < html.index("You drop: O. Gordon II")
    assert tb("""() => tbRoomHTML({ir_moves: [], drop: []}) + tbRoomHTML({})""") == "", "no line when there is nothing"


def test_the_card_says_the_gain_is_points_for_the_rest_of_the_season(tb):
    """"+18 pts rest of season": the unit the file's rules.unit names, never "a week"."""
    html = tb("tbCardHTML", mine(FIXTURE)[0], 0, {"teams": []}, False)
    assert "<b>+21.7</b> pts rest of season" in html.replace("\n", " ")
    assert "a week" not in html and "for you" not in html


def test_chips_are_small_tags_after_the_status_pill_and_nothing_when_there_are_none(tb):
    row = {"pos": "WR", "name": "T. Higgins", "injury": "Questionable"}
    assert tb("tbTagsHTML", {**row, "injury": None}) == ""
    assert tb("tbTagsHTML", {**row, "injury": None, "chips": []}) == ""
    hot = tb("tbTagsHTML", {**row, "injury": None, "chips": ["Hot"]})
    # Hot and Cold carry "Untested" in their tooltip (2026-10-06); Early pick is a draft round and carries none.
    assert hot.startswith('<span class="tb-tags"><i class="tb-chip hot" title="Untested: ') and hot.endswith('">Hot</i></span>')
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


TAG = ", priced on the rest of the season."


def test_the_pitch_quotes_a_hot_player_the_reader_sends_on_his_last_2_and_everyone_else_on_his_season_average(tb):
    cold = {"name": "Kalif Raymond", "seen": 9.4, "last2": 4.1, "chips": ["Cold"]}
    plain = lambda n, s: {"name": n, "seen": s, "last2": s + 0.4, "chips": []}   # noqa: E731
    # as today, when no one is Hot (a Cold player is quoted on his season average too)
    assert tb("tbText", {"send": [plain("Brock Purdy", 28.8), cold], "get": [plain("Chase Brown", 11.4)]}) == \
        "Trade? I send Purdy (28.8 a game) and Raymond (9.4) for Brown (11.4)" + TAG
    # a Hot player the reader GETS is quoted on his season average: his last 2 would inflate the ask
    assert tb("tbText", {"send": [plain("Brock Purdy", 28.8)], "get": [hot("Christian Watson", 16.5, 22.6)]}) == \
        "Trade? I send Purdy (28.8 a game) for Watson (16.5)" + TAG
    assert tb("tbText", {"send": [hot("Ollie Gordon II", 10.2, 15.2)], "get": [hot("Christian Watson", 16.5, 22.6)]}) == \
        "Trade? I send Gordon II (15.2 a game his last 2) for Watson (16.5)" + TAG, "sold on the streak, asked for on the season"
    # a Hot player ahead of the first season average: the unit lands on that average, not on a number that is a last-2
    assert tb("tbText", {"send": [hot("Ollie Gordon II", 10.2, 15.2), plain("Brock Purdy", 28.8)], "get": [plain("Chase Brown", 11.4)]}) == \
        "Trade? I send Gordon II (15.2 a game his last 2) and Purdy (28.8 a game) for Brown (11.4)" + TAG
    # a player with no last2 is quoted on his season average even with a stray Hot chip
    assert tb("tbText", {"send": [{"name": "Brock Purdy", "seen": 28.8, "last2": None, "chips": ["Hot"]}], "get": [plain("Chase Brown", 11.4)]}) == \
        "Trade? I send Purdy (28.8 a game) for Brown (11.4)" + TAG


def test_the_pitch_ends_with_one_sentence_on_the_partners_room_or_none(tb):
    side = {"send": [{"name": "Brock Purdy", "seen": 28.8, "chips": []}], "get": [{"name": "Chase Brown", "seen": 11.4, "chips": []}]}
    base = "Trade? I send Purdy (28.8 a game) for Brown (11.4)" + TAG
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

def test_the_guard_accepts_every_owner_of_the_fixture(tb):
    refused = {(lgk, owner): why for lgk, lg in FIXTURE["leagues"].items() for owner, offers in lg["teams"].items()
               if (why := tb("tbMismatch", lg, {"name": owner}, offers)) != ""}
    assert refused == {}


def test_an_owner_with_no_offers_passes_the_guard_so_make_your_own_still_shows(tb):
    lg = FIXTURE["leagues"]["espn"]
    assert tb("tbMismatch", lg, {"name": OWNER}, []) == "" and tb("tbMismatch", lg, {"name": OWNER}, None) == ""


def test_each_offer_is_scored_against_its_own_partners_values(tb):
    """v2 mixes partners in one list: an offer re-pointed at another partner is not the one the file scored."""
    bad = copy.deepcopy(FIXTURE)
    lg = bad["leagues"]["espn"]
    lg["values"]["Third Team"] = [{**p, "ros_pg": 1.0, "keep": 10.0} for p in lg["values"][PARTNER]]      # the same players, priced lower
    mine(bad)[0]["partner"] = "Third Team"
    why = mismatch(tb, bad)
    assert "offers[0]" in why, why
    mine(bad)[0]["partner"] = "Nobody At All"
    assert tb("tbMismatch", lg, {"name": OWNER}, mine(bad)) == "offers[0] is with Nobody At All, who has no values the drop rule or the rest-of-season pricing reads"


def test_a_gain_the_page_cannot_reproduce_is_named_and_even_a_tenth_off_is_not_the_same_number(tb):
    bad = copy.deepcopy(FIXTURE)
    mine(bad)[1]["gain"] = 20.5                                               # the rule says 20.4
    why = mismatch(tb, bad)
    assert "offers[1]" in why and "20.4" in why and "20.5" in why, why
    near = copy.deepcopy(FIXTURE)
    mine(near)[1]["gain"] = 20.4 + 1e-9                                       # float noise is not a different number
    assert mismatch(tb, near) == ""


def test_a_partner_gain_the_page_cannot_reproduce_is_named(tb):
    bad = copy.deepcopy(FIXTURE)
    mine(bad)[2]["their"]["gain"] = 1.8                                       # the rule says 1.7
    why = mismatch(tb, bad)
    assert "offers[2]" in why and "1.7" in why and "1.8" in why, why


def test_a_different_drop_ir_move_or_partner_room_is_named(tb):
    wrong = copy.deepcopy(FIXTURE)
    mine(wrong)[2]["drop"] = [p for p in mine(wrong)[2]["send"][:1]]           # a player the rule keeps
    assert "offers[2]" in mismatch(tb, wrong)
    moved = copy.deepcopy(FIXTURE)
    mine(moved)[0]["ir_moves"] = mine(moved)[0]["send"][:1]                    # a move the rule does not make
    assert "offers[0]" in mismatch(tb, moved)
    theirs = copy.deepcopy(FIXTURE)
    mine(theirs)[1]["their"]["drop"] = []                                      # the rule says Isaiah Davis goes
    assert "offers[1]" in mismatch(tb, theirs) and "them differently" in mismatch(tb, theirs)
    theirs = copy.deepcopy(FIXTURE)
    mine(theirs)[0]["their"]["ir_moves"] = mine(theirs)[0]["get"][:1]          # the rule makes no move
    assert "offers[0]" in mismatch(tb, theirs)


def test_a_file_without_their_fails_closed_as_one_without_a_drop_does(tb):
    old = copy.deepcopy(FIXTURE)
    for o in each_offer(old):
        o.pop("their")
    assert "no drop, ir_moves or their" in mismatch(tb, old)
    half = copy.deepcopy(FIXTURE)
    del mine(half)[0]["their"]["drop"]
    assert "offers[0]" in mismatch(tb, half)
    no_gain = copy.deepcopy(FIXTURE)
    del mine(no_gain)[0]["their"]["gain"]
    assert "offers[0]" in mismatch(tb, no_gain), "their.gain is checked, so a file without it shuts Edit"


def test_the_old_shapes_say_why_there_is_no_edit(tb):
    old = copy.deepcopy(FIXTURE)
    lg = old["leagues"]["espn"]
    for k in ("lineup", "values", "other"):
        lg.pop(k)
    assert mismatch(tb, old) == "no lineup or values for this owner"
    before = copy.deepcopy(FIXTURE)
    lg = before["leagues"]["espn"]
    lg["lineup"].pop("ir")
    assert "predates the drop rule" in mismatch(tb, before)


@pytest.mark.parametrize("cut", ["weeks_left", "ros_floor", "ros_pg", "games"])
def test_a_weekly_file_before_rest_of_season_pricing_says_so_and_shuts_edit(tb, cut):
    """2026-10-06: no weeks_left, no lineup.ros_floor, no ros_pg or games on a player. Scoring those as zeros would be a wrong number."""
    old = copy.deepcopy(FIXTURE)
    lg = old["leagues"]["espn"]
    if cut == "weeks_left":
        del lg["weeks_left"]
    elif cut == "ros_floor":
        del lg["lineup"]["ros_floor"]
    else:
        del lg["values"][OWNER][0][cut]
    assert "rest-of-season" in mismatch(tb, old), cut


def test_a_partner_priced_without_ros_pg_shuts_edit_on_that_offer(tb):
    partner = copy.deepcopy(FIXTURE)
    del partner["leagues"]["espn"]["values"][PARTNER][0]["ros_pg"]
    assert "offers[0]" in mismatch(tb, partner) and "is with Run It Back" in mismatch(tb, partner)
