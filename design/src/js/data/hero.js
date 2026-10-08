/* Home's hero (2026-10-08, David: "bring back the hero ... we added this cool scoreboard flip animation"): what the
   split-flap ghost wall behind the headline spells. Pure, so Node tests it (tests/test_js_home.py); the band is
   surface/digest/lead.js, its flip digest/hero.css. */

/* The ghost: the lead's own (his rank, the wind, his club), else the home side of the day's game, else the week. */
function dgHeroGhost(lead, week){
  if (lead && lead.ghost) return lead.ghost;
  if (lead && lead.vs && lead.vs[1]) return String(lead.vs[1]);
  return week ? `WK${week}` : "";
}

/* A string as split-flap cells: [{c, i}] one per character, a space kept as a gap (c " ", no tile). `i` counts every
   cell, so the flip runs left to right. An HTML entity (&amp;) is one cell. */
const dgFlapCells = s => (String(s || "").match(/&[^;\s]+;|\s|./gu) || []).map((c, i) => ({c, i, gap: !c.trim()}));
