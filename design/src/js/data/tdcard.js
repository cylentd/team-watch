// Anytime TDs card (2026-10-09): which LIVE_TD_RESEARCH rows show under the open kickoff tab, in what groups, and
// when Claude's picks arrive. Pure. A row's window is the PROPS window of a line with the same kickoff instant,
// so the card never windows the slate a second way (slate.py assign_windows is the one copy).

const TD_TIERS = ["LOCK", "VALUE", "MORE", "LONG"];
const TD_MIN_MS = 60000;
const TD_HOUR_MIN = 60;

// PROPS' commence is "2026-09-13 17:00:00", UTC with no zone; the packet's kickoff is ISO with Z.
const tdMs = x => Date.parse(/[zZ]$|[+-]\d\d:?\d\d$/.test(String(x)) ? x : String(x).replace(" ", "T") + "Z");

function tdWinOf(kickoff, props) {
  const at = tdMs(kickoff);
  if (!Number.isFinite(at)) return null;
  const hit = (props || []).find(p => p.win && tdMs(p.commence) === at);
  return hit ? hit.win : null;
}

const tdBookP = r => (r.book && typeof r.book.p === "number" ? r.book.p : -1);
const tdByBook = (a, b) => tdBookP(b) - tdBookP(a);

// The rows for the window keys `keys` whose game has not kicked off, the book's chance first.
function tdRows(block, keys, props, now) {
  const players = (block && block.players) || [];
  return players.filter(r => keys.includes(tdWinOf(r.kickoff, props)) && Date.parse(r.kickoff) > now).sort(tdByBook);
}

function tdGroups(rows) {
  const out = {};
  TD_TIERS.forEach(k => { out[k] = rows.filter(r => r.tier === k); });
  return out;
}

// The latest expected_at (ms) among Claude's pending games in these windows not yet kicked off, else null.
function tdPendingAt(pending, keys, props, now) {
  const at = (pending || []).filter(g => keys.includes(tdWinOf(g.kickoff, props)) && Date.parse(g.kickoff) > now)
    .map(g => Date.parse(g.expected_at)).filter(Number.isFinite);
  return at.length ? Math.max(...at) : null;
}

function tdLeft(ms, now) {
  const min = Math.ceil((ms - now) / TD_MIN_MS);
  if (min <= 0) return t("slips.td.left.now");
  const h = Math.floor(min / TD_HOUR_MIN), m = min % TD_HOUR_MIN;
  return h ? t("slips.td.left.hm", { h, m }) : t("slips.td.left.m", { m });
}

// The PROPS index of his anytime-TD line, or -1: no line, no + on the row.
// `slugOfRow` is the board's slSlug on the page (a row's slug can be null; his name is then the slug).
function tdPropIdx(slug, props, slugOfRow = p => p.slug) {
  return (props || []).findIndex(p => p.mkt === "TD" && slugOfRow(p) === slug);
}
