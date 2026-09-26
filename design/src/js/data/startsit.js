/* The Matchups view's state and its one cut of LIVE_STARTSIT (design/startsit.py). The calls are
   ff-jarvis's, frozen there before each kickoff and graded there; the page only shows them. */
let MU_POS = "WR";
const MU_POSITIONS = ["QB", "RB", "WR", "TE"];
// Where "the obvious starters" end, per position: the same cut ff-jarvis's calls use.
const MU_CUT = {QB: 12, RB: 24, WR: 24, TE: 12};

const muCalls = (pos, tag) => (LIVE_STARTSIT ? LIVE_STARTSIT.calls : []).filter(r => r.pos === pos && r.tag === tag);
const muPl = pos => (LIVE_STARTSIT ? LIVE_STARTSIT.pl : []).filter(r => r.pos === pos);
const muVs = r => (r.home ? "vs " : "@ ") + r.opp;
const muScore = x => x == null ? "—" : x.toFixed(2);
