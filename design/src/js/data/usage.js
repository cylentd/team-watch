/* ------------------------------------------------------------------
   USAGE — what every player did, week by week, in the columns his own
   position is judged on. The Pool answers "who moved"; this answers
   "what did everyone do", which is where a breakout is visible before
   a verdict can name it.

   Colour is the player's percentile among QUALIFIED players at his
   position that week (ff-jarvis's model.season.usage). It is a fact
   about one week's distribution, never a claim that the week repeats,
   so no cell carries a word like "elite".
------------------------------------------------------------------ */
const SAMPLE_USAGE = {
  season: 2026, weeks: [1], through: 1, generated: null,
  rankBy: {QB:"dropbacks", RB:"car", WR:"tgt", TE:"tgt"},
  cols: {
    RB: [{id:"car",label:"Carries",fmt:"int"},{id:"tgt",label:"Targets",fmt:"int"},
         {id:"tgt_pct",label:"Tgt%",fmt:"pct"},{id:"rz",label:"RZ Touch",fmt:"int"},
         {id:"gl_car",label:"GL Carries",fmt:"int"},{id:"snap",label:"Snap%",fmt:"pct"}],
  },
  rows: [
    {n:"Jahmyr Gibbs", slug:"jahmyr-gibbs", pos:"RB", team:"DET", wk:1, q:true,
     v:{car:29,tgt:5,tgt_pct:12.8,rz:8,gl_car:5,snap:74}, p:{car:99,tgt:83,tgt_pct:71,rz:99,gl_car:99,snap:92}},
    {n:"Derrick Henry", slug:"derrick-henry", pos:"RB", team:"BAL", wk:1, q:true,
     v:{car:24,tgt:1,tgt_pct:4.0,rz:6,gl_car:2,snap:54}, p:{car:95,tgt:28,tgt_pct:19,rz:93,gl_car:86,snap:57}},
  ],
};

/* design/usage.py cuts ff-jarvis's usage_weekly.json to these fields. The sample above is only
   the fallback when that file is missing; it holds one position and one week on purpose, so an
   empty-looking grid is obviously the fallback rather than a bad build. */
const USAGE = (typeof LIVE_USAGE !== "undefined" && LIVE_USAGE && LIVE_USAGE.rows.length)
  ? LIVE_USAGE : SAMPLE_USAGE;
const USAGE_LIVE = typeof LIVE_USAGE !== "undefined" && !!LIVE_USAGE;

/* Five bands, three hues, all existing tokens. Green good, red bad, and a quiet middle so the
   eye lands on the extremes -- which is the only reason to colour a grid at all. A monochrome
   ramp reads as one smear at a glance; a six-hue rainbow reads as six categories, and these are
   an order, not categories. */
function usageBand(p){
  if (p === null || p === undefined) return "";
  if (p >= 90) return "b5";
  if (p >= 75) return "b4";
  if (p > 25)  return "b3";
  if (p > 10)  return "b2";
  return "b1";
}

/* Change mode colours by sign, not by a percentile of the change: ranking a delta would be a
   second percentile rule living in the view, and the size is already in the number. The deadband
   keeps a rounding-width move off the colour. */
function usageTone(d){
  if (d === null || d === undefined) return "";
  if (d > 0.05) return "u-up";
  if (d < -0.05) return "u-down";
  return "";
}

function usageFmt(v, fmt){
  if (v === null || v === undefined) return "—";
  if (fmt === "pct") return Math.round(v) + "%";
  if (fmt === "one") return Number(v).toFixed(1);
  if (fmt === "two") return Number(v).toFixed(2);
  return String(Math.round(v));
}

function usageFmtDelta(d, fmt){
  if (d === null || d === undefined) return "—";
  const n = fmt === "one" ? Number(d).toFixed(1) : String(Math.round(d));
  return (d > 0 ? "+" : "") + n + (fmt === "pct" ? "%" : "");
}

/* TEAMS.espn.roster is filled by hydrate.js from LIVE_ESPN, so this cannot be a load-time
   constant -- it is read on each render, which is cheap against two rosters. */
function usageMine(){
  const out = new Set();
  Object.values(TEAMS).forEach(tm => (tm.roster || []).forEach(p => out.add(p.slug)));
  return out;
}

const USAGE_POSITIONS = ["QB", "RB", "WR", "TE"];
let USAGE_POS = "RB";
let USAGE_WEEK = USAGE.through || (USAGE.weeks || [1])[0];
let USAGE_SORT = null;      // a column id, else the position's own rank column
let USAGE_DESC = true;
let USAGE_MODE = "level";   // "level" = what he did, "change" = the move from the week before
let USAGE_MINE = false;
