/* ============================== LEAGUE > TRADES: THE FINDER'S LOGIC ==============================
   2026-10-06 (trade finder, unit U4). Pure, no DOM: data in, data out (tests/test_js_finder.py, in Node).
   The finder (finder.js) draws a chip per position the league starts, each with the reader's gap to the league's
   median there; opens on the most negative gap; shows the offers whose `get` holds that position; then ranks every
   other team by that column. The numbers are LIVE_TEAMS' (design/teams.py: `cols`, `median`) and the offers' own
   (`gain`): nothing here scores a trade. The 8% tint and the record are the Teams cards' (lboard.js lbTone, lbRecord). */
const TF_POS = ["QB", "RB", "WR", "TE"];
const TF_TOP = 5;                                  // offers a chip shows

/* The positions this league starts, in chip order: a league with no TE slot has no TE chip. */
const tfPositions = lg => TF_POS.filter(p => lg.slots[p]);

/* [{pos, gap}]: the reader's column minus the league's median, so a negative gap is a position he is short at. */
const tfGaps = (lg, tm) => tfPositions(lg).map(pos => ({pos, gap: tm.cols[pos] - lg.median[pos]}));

/* The chip that opens first: the most negative gap, the first in chip order on a tie; with nobody short, the
   smallest lead. null with no chips. `offered` (the positions some offer brings back, null until the file is in)
   narrows it to positions with an offer, so a reader short at TE with no TE offer opens where a trade exists
   (2026-10-06); with no offer anywhere, the plain rule. */
function tfStartPos(gaps, offered){
  const some = offered ? gaps.filter(g => offered.includes(g.pos)) : [];
  const pool = some.length ? some : gaps;
  return pool.length ? pool.reduce((a, b) => b.gap < a.gap ? b : a).pos : null;
}

/* The positions at least one of the owner's offers brings back, in chip order. */
const tfOffered = list => TF_POS.filter(p => (list || []).some(o => o.get.some(x => x.pos === p)));

/* "+2.0", "−7.0", "0.0": one decimal, a true minus, and no sign on what rounds to zero. */
function tfSigned(g){
  const n = Math.abs(g).toFixed(1);
  return Number(n) === 0 ? "0.0" : (g > 0 ? "+" : "−") + n;
}

/* The owner's offers (offers.js: the file's flat list for him) the finder shows. A chip: those whose `get` holds the
   position, best gain first, at most TF_TOP. A partner (the finder filtered to one team, `partnerName`): every offer
   with him, whatever the position. Equal gains go to the smaller trade, then the partner's name. */
function tfOffersFor(list, pos, partnerName){
  const size = o => o.send.length + o.get.length;
  return (list || []).filter(o => partnerName ? o.partner === partnerName : o.get.some(p => p.pos === pos))
    .sort((a, b) => tfRank(b) - tfRank(a) || size(a) - size(b) || a.partner.localeCompare(b.partner))
    .slice(0, partnerName ? undefined : TF_TOP);
}

/* ---- The lenses (ledger #44, 2026-10-08; ff-jarvis 3cf9002, its `rules.lenses`): each side of an offer is judged on
   the lens its standing cares about most, Now (next 2 weeks), Push (next 4), Playoff run or ROS. The file names that
   lens (`lens.me`, `lens.them`), each lens's gain for both sides (`lenses`) and the owner's weighted `score`, which
   orders his list. An offer from before the lenses has none of them: the card is the ROS card it was. ---- */
const TF_LENSES = ["now", "push", "playoffs", "ros"];
const TF_NOTE_MAX = 2;         // bye notes a card shows, the nearest first (about 4 an offer exist; David, ledger #44)
const TF_NOTE_WEEKS = 4;       // "near-term" when the file has no windows: the Push lens's window, rules.lenses

/* What an offer ranks on: the owner's lens score where the file has one, else his ROS gain. */
const tfRank = o => typeof o.score === "number" ? o.score : o.gain;

/* A team's tier (contender, bubble, chaser) from the league's `standing`, or null when the league does not place him. */
const tfTier = (standing, team) => ((standing || {})[team] || {}).tier || null;

/* One side's judge, `side` "me" or "them": the lens that judges it (ROS when the file names none), its gain there and
   the side's tier. null for an offer from before the lenses. */
function tfJudge(o, side, tier){
  if (!o.lenses || !o.lens) return null;
  const lens = o.lens[side] || "ros", cell = o.lenses[lens] || {};
  return {lens, gain: (side === "me" ? cell.gain : cell.their) ?? null, tier: tier || null};
}

/* The four lenses in order with both sides' gains (null for a blank lens) and which lens judges each side. */
const tfLensRows = o => TF_LENSES.map(lens => {
  const cell = o.lenses[lens] || {};
  return {lens, me: cell.gain ?? null, them: cell.their ?? null, onMe: (o.lens.me || "ros") === lens, onThem: (o.lens.them || "ros") === lens};
});

/* The bye notes a card shows: weeks from the league's `week` to the end of the Push window (`windows.push`, else
   TF_NOTE_WEEKS), nearest first, at most TF_NOTE_MAX; a tie keeps the file's order. */
function tfNotes(notes, week, windows){
  const end = week + ((windows || {}).push ?? TF_NOTE_WEEKS);
  return (notes || []).filter(n => n.week >= week && n.week < end).sort((a, b) => a.week - b.week).slice(0, TF_NOTE_MAX);
}

/* Who is deep at `pos`: every team but the reader's (`meKey`), best column first, ties to the higher lineup total.
   Each row: the team, its column's sum, the Teams cards' tint, its record and its starters there (the flex slot's
   included) as initials. */
function tfDeep(lg, pos, meKey){
  return lg.teams.filter(tm => tm.key !== meKey)
    .sort((a, b) => b.cols[pos] - a.cols[pos] || b.tot - a.tot || a.name.localeCompare(b.name))
    .map(tm => ({key: tm.key, name: tm.name, val: tm.cols[pos], tone: lbTone(tm.cols[pos], lg.median[pos]), record: lbRecord(tm),
      starters: tm.lineup.filter(r => r.pos === pos).map(r => nameInitial(r.n))}));
}
