/* His share of his own team, first in Usage (2026-09-29, David: "his usage should have his
   teammates there for comparison so we know not only his usage ranked among the league but also
   his own team"). The radar ranks him against every player at his position; this says how much of
   his offense runs through him, and who takes the rest.

   From the game log, not watch's per-position share: the rows here are whole-team counts, so they
   sum to the team's total and a tight end and a back sit on one list. A receiver gets targets; a
   back gets carries, then targets. A passer gets no block: his team's throws are all his. */
const TEAM_SHARE_KEYS = {RB: ["car", "tgt"], WR: ["tgt"], TE: ["tgt"]};
const TEAM_SHARE_TOP = 5;   // named rows; the rest fold into one "others" row

// Each player's total on one stat for one team, most first, with the weeks the team has played.
function teamShareRows(team, key){
  const by = {}, weeks = new Set();
  (typeof LIVE_GAMELOG !== "undefined" && LIVE_GAMELOG ? LIVE_GAMELOG.rows : []).forEach(r => {
    if (r.team !== team) return;
    weeks.add(r.wk);
    if (!r[key]) return;
    const o = by[r.slug] = by[r.slug] || {slug: r.slug, n: r.n, pos: r.pos, team: r.team, v: 0};
    o.v += r[key];
  });
  const rows = Object.values(by).sort((a, b) => b.v - a.v || a.n.localeCompare(b.n));
  return {rows, total: rows.reduce((s, r) => s + r.v, 0), weeks: weeks.size};
}

/* One literal t() per stat: assemble.py --check finds a key by its literal form. */
const TEAM_SHARE_NOUN = {car: () => t("profile.team.carries"), tgt: () => t("profile.team.targets")};

/* The top five by volume, him among them wherever he falls, then everyone else as one row. His row
   is text in the position's tint; a teammate's is a button that opens that teammate's profile. */
function teamShareListHTML(d, slug){
  const shown = d.rows.slice(0, TEAM_SHARE_TOP);
  const me = d.rows.find(r => r.slug === slug);
  if (me && !shown.includes(me)) shown.push(me);
  const rest = d.total - shown.reduce((s, r) => s + r.v, 0), restN = d.rows.length - shown.length;
  const max = shown[0] ? shown[0].v : 1;
  const pct = v => Math.round(v / d.total * 100) + "%";
  const row = (r, i) => {
    const body = `<span class="pf-tm-n">${shortName(r.n)}<em>${esc(r.pos)}</em></span>
      <span class="pf-tm-bar"><i style="--w:${(r.v / max * 100).toFixed(0)}%;--i:${i}"></i></span><b>${pct(r.v)}</b>`;
    return r.slug === slug ? `<div class="pf-tm me">${body}</div>`
      : `<button type="button" class="pf-tm" data-tmslug="${esc(r.slug)}" aria-label="${t("profile.team.open", {n: esc(r.n)})}">${body}</button>`;
  };
  // No bar for the rest: it is several players, not one to compare him with, and their sum can
  // outgrow the leader's bar the scale is set by.
  const others = restN > 0 && rest > 0 ? `<div class="pf-tm rest"><span class="pf-tm-n">${t("profile.team.others", {n: restN})}</span>
      <span></span><b>${pct(rest)}</b></div>` : "";
  return `<div class="pf-team">${shown.map(row).join("")}${others}</div>`;
}

function teamShareBlockHTML(p, key, sub){
  const d = teamShareRows(p.team, key);
  const i = d.rows.findIndex(r => r.slug === p.slug);
  if (i < 0 || !d.total) return "";
  const noun = TEAM_SHARE_NOUN[key]();
  const lead = leadHTML(Math.round(d.rows[i].v / d.total * 100) + "%",
    t("profile.team.lead", {noun, team: esc(p.team), rank: ordinal(i + 1), n: d.rows[i].v, total: d.total}), sub ? "sub" : "");
  return lead + teamShareListHTML(d, p.slug);
}

function teamShareHTML(p){
  const keys = p && p.team ? TEAM_SHARE_KEYS[p.pos] : null;
  if (!keys) return "";
  const body = keys.map((k, i) => teamShareBlockHTML(p, k, i > 0)).join("");
  if (!body) return "";
  return secHTML(t("profile.team.label", {team: esc(p.team)}), body, "", "pf-sec-team", winText(teamShareRows(p.team, keys[0]).weeks));
}

/* A teammate's row opens his profile in place of this one; Back still closes the profile. */
document.getElementById("modal").addEventListener("click", e => {
  const b = e.target.closest("[data-tmslug]");
  if (!b) return;
  const r = LIVE_GAMELOG.rows.find(x => x.slug === b.dataset.tmslug);
  if (r) openProfile({n: r.n, pos: r.pos, team: r.team, slug: r.slug}, b);
});
