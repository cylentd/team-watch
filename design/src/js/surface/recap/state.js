/* ============================== RECAP: STATE AND READS ==============================
   This week > Recap (leaf `weekrecap`, 2026-10-05, storyboard option C,
   https://claude.ai/artifact/HVdkEL4YbiBKUJ3QbLH9gf; David: "otherwise that is a lot of scrolling").
   The newest week with half its games final, league-wide and public: LIVE_RECAP (design/recap.py).
   The page picks nothing: ff-jarvis chose who smashed, who busted and who left hurt (the Digest's own
   lists), and graded Claude's pick for every game. This file holds the state and the small reads the
   other recap parts share. Prefix wr / WR_ / .wr-; `rc` is League > Records'.

   The choice of tab is `tw-recap-tab` in localStorage, never the hash, like Live's (live/tabs.js).
   Switching repaints the body in place, never through render(). */

const WR_TAB_KEY = "tw-recap-tab";
const WR_TABS = ["players", "scores", "claude"];
let WR_TAB_MEM = null;      /* the tab when localStorage will not answer (private window, blocked data) */
let WR_LIST = "smashed";    /* Smashed / Busts / Left hurt on a phone: memory only */
let WR_TDS_ALL = false;     /* the touchdown list's "show all": memory only, folded on every visit */

const wrD = () => LIVE_RECAP || null;

/* Every key spelled out: assemble.py --check finds unused copy by scanning for literal lookups. */
const wrTabName = k => ({players: t("weekrecap.tab.players"), scores: t("weekrecap.tab.scores"),
  claude: t("weekrecap.tab.claude")})[k];

/* Claude's record for the week (preview_record), or null before a game is graded: no zeros. */
const wrRecord = d => (d.preview_record && d.preview_record.n ? d.preview_record : null);

/* A touchdown dot is a rushing, receiving or return score; a passing TD is the same score as the
   catch, so it is said once, in the note under the list. */
const wrDots = r => (r.rush_td || 0) + (r.rec_td || 0) + (r.ret_td || 0);
const wrTdRows = d => d.tds.filter(r => wrDots(r) > 0)
  .sort((a, b) => wrDots(b) - wrDots(a) || (b.actual || 0) - (a.actual || 0) || (a.n < b.n ? -1 : 1));

const wrHasPlayers = d => !!(d.stars.length || d.k.length || d.dst.length || d.smashed.length || d.busts.length
  || d.left_hurt.length || wrTdRows(d).length);
const wrHasClaude = d => !!(wrRecord(d) || d.games.some(g => g.preview && g.preview.su_hit !== null));

/* The tabs that have something in them, in order; with one left the bar hides. */
const wrAvail = d => WR_TABS.filter(k => k === "players" ? wrHasPlayers(d) : k === "scores" ? d.games.length > 0 : wrHasClaude(d));

function wrTab(d){
  let v = WR_TAB_MEM;
  /* A store that answers but has lost the key (cleared mid-visit) does not overrule memory. */
  try { v = localStorage.getItem(WR_TAB_KEY) || v; } catch (e) {}
  const open = wrAvail(d);
  return open.includes(v) ? v : open[0];
}
function wrSetTab(v){
  if (!WR_TABS.includes(v)) return;
  WR_TAB_MEM = v;
  try { localStorage.setItem(WR_TAB_KEY, v); } catch (e) {}
}

/* A kickoff's window, from its Eastern weekday and hour: design/preview.py's `_slot`, so a game falls in
   the same window here as on Preview's slate. Null without a kickoff (an old recap file has none). */
const WR_ET = new Intl.DateTimeFormat("en-US", {timeZone: "America/New_York", weekday: "short",
  hour: "numeric", minute: "2-digit", hourCycle: "h23"});
function wrSlot(iso){
  const ms = Date.parse(iso || "");
  if (isNaN(ms)) return null;
  const p = {};
  WR_ET.formatToParts(new Date(ms)).forEach(x => { p[x.type] = x.value; });
  const h = +p.hour, day = p.weekday;
  const slot = day === "Thu" ? "thu" : day === "Mon" ? "mon" : day === "Sun"
    ? (h < 13 ? "sunam" : h < 16 ? "sun1" : h < 19 ? "sunlate" : "sunnight") : "day";
  return {slot, day, et: `${h % 12 || 12}:${p.minute} ${h < 12 ? "AM" : "PM"}`};
}

/* The week's games in kickoff order, grouped by window: [{slot, day, times, rows: [{g, at}]}]. A game
   with no kickoff joins the window before it, or an unlabelled one first. */
function wrWindows(d){
  const out = [];
  [...d.games].sort((a, b) => String(a.kickoff || "").localeCompare(String(b.kickoff || ""))).forEach(g => {
    const at = wrSlot(g.kickoff), last = out[out.length - 1];
    if (last && (!at || (last.slot === at.slot && last.day === at.day))){
      last.rows.push({g, at});
      if (at && !last.times.includes(at.et)) last.times.push(at.et);
    } else out.push({slot: at ? at.slot : null, day: at ? at.day : "", times: at ? [at.et] : [], rows: [{g, at}]});
  });
  return out;
}

/* The Preview game this one opens, when Preview holds the same week; else -1 and the row is not a button. */
function wrPreviewIndex(d, g){
  if (!LIVE_PREVIEW || LIVE_PREVIEW.week !== d.week || (LIVE_PREVIEW.season && d.season && LIVE_PREVIEW.season !== d.season)) return -1;
  return pvGames().findIndex(x => x.away === g.away && x.home === g.home);
}

/* A player's profile, from any row the view drew: they all carry n, pos, team and slug. */
function wrFindRow(d, slug){
  return [d.top, ...d.stars, ...d.k, ...d.smashed, ...d.busts, ...d.tds, ...d.left_hurt].find(r => r && r.slug === slug);
}
function wrOpenPlayer(slug, el){
  const r = wrFindRow(wrD(), slug);
  if (r) openProfile({n: r.n, pos: r.pos, team: r.team, slug: r.slug}, el);
}
/* A kicker's page has little in it, and a defense has none: only a player the page knows is a button. */
const wrCanOpen = slug => !!slug && searchIndex().some(e => e.slug === slug);
