const propLabel = p => p.line === null ? MKT[p.mkt] : `${MKT[p.mkt]} o${p.line}`;

/* Why a row the sort put on top is not on any gallery card: one pill, the first reason that
   applies, in the order legOKInBook would trip on it. A row can fail three gates at once (a
   backup, at a moved line, on a thin number) and three pills say "no" three times -- one is the
   answer. `u` is the Underdog pick when in that mode, for the line-size floor. Build's rows
   (lines.js, 2026-09-29) put it on the player and say a moved line on the line itself. */
function whyNotSlip(p, u){
  if (p.flag === "out") return `<span class="tag t-out">${t("parlay.tag.out")}${p.injury_note ? " · " + esc(p.injury_note) : ""}</span>`;
  if (p.flag === "q") return `<span class="tag t-q">${t("parlay.tag.q")}${p.injury_note ? " · " + esc(p.injury_note) : ""}</span>`;
  if (p.flag === "backup") return `<span class="tag t-bk" title="${t("parlay.tag.backupTitle", {pos: esc(p.pos), depth: p.depth})}">${esc(p.pos)}${p.depth}</span>`;
  if (p.norole) return `<span class="tag t-bk" title="${t("parlay.tag.noRoleTitle")}">${t("parlay.tag.noRole")}</span>`;
  if (p.moved) return `<span class="tag t-role" title="${t("parlay.tag.movedTitle", {team: esc(p.moved)})}">${t("parlay.tag.moved")}<span class="was"> · ${t("parlay.tag.movedWas", {team: esc(p.moved)})}</span></span>`;
  if (u ? u.stale : p.stale) return `<span class="tag t-role" title="${t("parlay.tag.staleTitle")}">${t("parlay.tag.stale")}</span>`;
  if (typeof p.model === "number" && (p.games||0) < 8) return `<span class="tag t-bk" title="${t("parlay.tag.gamesTitle", {n: p.games||0})}">${t("parlay.tag.games", {n: p.games||0})}</span>`;
  if (u && !u.synthetic && u.line !== null && (p.mkt === "RECS" ? u.line < 2.5 : u.line < 15)) return `<span class="tag t-bk" title="${t("parlay.tag.thinTitle")}">${t("parlay.tag.thin")}</span>`;  return "";
}

/* A hand-written role note (data/role_notes.json in ff-jarvis) already discounted this player's
   own model number -- it is not a reason to hide him from the slip the way whyNotSlip's pills
   are, so it renders alongside whatever whyNotSlip already says, never instead of it. */
function roleNoteTagHTML(p){
  return p.role_note
    ? `<span class="tag t-role" title="${esc(p.role_note)}">${t("parlay.tag.role")}</span>` : "";
}
