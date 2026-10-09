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

/* The headline as split-flap words (David 2026-10-08, "I also want the scoreboard animation back"): each word one tile
   knowing its place (--i), so the headline turns over left to right as the band lands (digest/hero.css). The headline
   arrives as HTML: a tag passes through whole, a space stays plain text, an entity stays inside its word, so the words
   read exactly as before. */
const dgFlapWords = html => {
  let i = 0;
  return String(html || "").split(/(<[^>]*>)/).map(part => part.startsWith("<") ? part
    : part.split(/(\s+)/).map(w => w && !/^\s+$/.test(w) ? `<i class="dg-hw" style="--i:${i++}">${w}</i>` : w).join("")).join("");
};

/* The headline's letters as split-flap tiles (David 2026-10-08, ledger #73: "on hover the headline doesnt flip like a
   scoreboard like the previous animation"): each letter one tile knowing its place across the whole headline (--c),
   so a pointer turns them over in turn, as b0284898's ghost letters did (digest/hero.css). Runs on dgFlapWords'
   output: a tag passes through whole, a space stays plain text, an entity is one letter. */
const dgFlapChars = html => {
  let c = 0;
  return String(html || "").split(/(<[^>]*>)/).map(part => part.startsWith("<") ? part
    : (part.match(/&[^;\s]+;|\s+|./gu) || []).map(ch => ch.trim() ? `<i class="dg-hc" style="--c:${c++}">${ch}</i>` : ch).join("")).join("");
};

/* The face's cuts as a srcset (David 2026-10-08, "the headshot is not clear. looks pixelated"): the pane draws the
   square head at its larger side, 232-300px on a phone, so a 2x screen needs ~460-600 device px and the 256px cut
   blurred there. `cuts` is [[slug -> path, px], ...] smallest first; the browser takes the smallest sharp at the
   drawn size, and `src`, for a browser without srcset, is the largest. Null when no cut has him. */
function dgHeroCuts(slug, cuts){
  const have = (cuts || []).filter(([m]) => m && m[slug]);
  if (!have.length) return null;
  return {src: have[have.length - 1][0][slug], srcset: have.map(([m, w]) => `${m[slug]} ${w}w`).join(", ")};
}

/* ---------------------------------------------------------------- the hero's face (ledger #63, David 2026-10-08 "face a")
   A headline about one player shows his head beside the tiles; any other headline shows Blip reacting to the day.
   {slug, src} or {pose}; the pose is one of League's (lib/blip.js BLIP_REACT, surface/league/lead.js LG_BLIP_LABEL). */
const DG_HERO_CLOSE = 3;    // Claude's score inside a field goal: a game to sweat
const DG_HERO_ROUT = 14;    // two touchdowns or more between the sides: a rout, Blip laughs
const DG_HERO_TONE = {quiet: "flatline", out: "ko", q: "wince", sky: "wince"};   // a hurt or weather lead outranks the call
const DG_HERO_JOB = {adds: "laugh", usage: "laugh", smash: "laugh", status: "wince",   // DG_PLAN's banner kinds
  tnf: "sweat", tonight: "sweat", kickoff: "sweat"};

/* The words a headline would name him by: his full name and his surname (a Jr. or II dropped). */
function dgHeroNames(n){
  const full = String(n || "").trim(), bare = full.replace(/\s+(Jr\.?|Sr\.?|II|III|IV|V)$/i, "").split(/\s+/);
  return [full, bare[bare.length - 1]].filter(Boolean);
}
const dgHeroSays = (head, word) => new RegExp(`(^|[^\\p{L}])${word.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}($|[^\\p{L}])`, "u").test(head);

/* The one player the headline is about: the lead's own (unless it is about several), else the one player of Claude's
   take whose name the take's head says. Two named is a game, not a player. */
function dgHeroSlug(lead){
  if (lead.slug) return (lead.slugs || []).length > 1 ? "" : lead.slug;
  const tk = lead.take, head = (tk && tk.head) || "";
  const named = [...new Set(((tk && tk.players) || []).filter(p => dgHeroNames(p.n).some(w => dgHeroSays(head, w))).map(p => p.slug))];
  return named.length === 1 ? named[0] : "";
}

/* Claude's margin from his pick's score, or null without one. */
function dgHeroMargin(pick){
  const s = (pick && pick.score) || {}, v = Object.values(s);
  return v.length === 2 ? Math.abs(v[0] - v[1]) : null;
}

function dgHeroPose(lead, job){
  const tone = String(lead.tone || "").split(" ").find(x => DG_HERO_TONE[x]);
  if (tone) return DG_HERO_TONE[tone];
  const m = dgHeroMargin(lead.take && lead.take.pick);
  if (m != null && m <= DG_HERO_CLOSE) return "sweat";
  if (m != null && m >= DG_HERO_ROUT) return "laugh";
  return DG_HERO_JOB[job] || "flatline";
}

/* `lg` and `sm`: slug -> head path, the 256px ones and the 96px ones (HEADS_LG, HEADS). */
function dgHeroFace(lead, job, lg, sm){
  const L = lead || {}, slug = dgHeroSlug(L), src = slug && ((lg || {})[slug] || (sm || {})[slug]);
  return src ? {slug, src} : {pose: dgHeroPose(L, job)};
}

/* The face's club, for the glow behind him (face.css): the lead's own club, a live scorer's, else the club of
   the take's row for him. The raw code as the data spells it; the view maps it to the colour table. */
function dgHeroTeam(lead, slug){
  const L = lead || {};
  if (L.team) return String(L.team);
  if (L.live && L.live.team) return String(L.live.team);
  const row = (((L.take || {}).players) || []).find(p => p.slug === slug);
  return row && row.team ? String(row.team) : "";
}
