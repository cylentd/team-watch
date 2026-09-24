/* ------------------------------------------------------------------
   THE BOARD — the two words under the picks: what he is asked to do, and what he does with it.

   The lanes are the measurement; these two words name a pattern in them, so neither is allowed to
   arrive bare. Each carries the two or three numbers that produced it and the window they were
   measured over. Type follows the house rule as of 2026-09-23: the field's name and its window are
   labels and take .lbl, the line of evidence under the word is a sentence and takes .note.

   ROLE is this season and moves when the depth chart moves. STYLE is his career and should barely
   move -- and its axes are not equally sturdy: year over year, breakaway is r=.37 and yards before
   contact r=.24 (ff-jarvis, model/season/ARCHETYPE.md). That is a data point a reader folds into a
   read, never a forecast, so the block closes on the sentence the Grid already uses for exactly
   this: what he did, not what he will do. No new sentence, no composite, no grade.

   A NULL LABEL IS NOT A BLANK. ff-jarvis's envelope guarantees exactly one of role/role_null is
   set, and the reason takes the word's place: "not a field for quarterbacks" answers the question
   a dash would only raise. A missing number inside an evidence line drops out instead of dashing,
   the same rule the lanes follow for an unmeasured axis. A player with no archetype record at all
   (most of the board) draws no block, which is why this is under the picks and not on a lane.
------------------------------------------------------------------ */
const bdArch = slug => typeof LIVE_ARCHETYPE !== "undefined" && LIVE_ARCHETYPE
  ? LIVE_ARCHETYPE.players[slug] || null : null;

function bdRoleWord(v){
  return ({every_down: t("board.role.everyDown"), early_down: t("board.role.earlyDown"),
    satellite: t("board.role.satellite"), goal_line: t("board.role.goalLine"),
    committee: t("board.role.committee"), rotational: t("board.role.rotational"),
    situational: t("board.role.situational"), move: t("board.role.move"),
    in_line: t("board.role.inLine")})[v] || esc(v);
}

function bdStyleWord(v){
  return ({power: t("board.style.power"), home_run: t("board.style.homeRun"),
    complete: t("board.style.complete"), one_cut: t("board.style.oneCut"),
    deep_threat: t("board.style.deepThreat"), possession: t("board.style.possession"),
    yac: t("board.style.yac"), dual_threat: t("board.style.dualThreat"),
    pocket: t("board.style.pocket"), scrambler: t("board.style.scrambler")})[v] || esc(v);
}

/* A flag layers on top of a style rather than replacing it, so it is a pill beside the word and
   never a fourth value: a passer the offence runs at the goal line is usually also one of the
   three styles, and picking between two true facts is what a fourth bucket would force. */
function bdFlagsHTML(flags){
  return flags.map(f => f === "goal_line_runner"
    ? `<span class="bd-flag">${t("board.label.flagGoalLine")}</span>` : "").join("");
}

/* Which numbers produced the word: the inputs the classifier's own ladder reads. Two or three,
   never the whole evidence dict. Named in words, not in the sheet's own column heads -- a lane
   can call it "Opp%" because the number sits in a column of its own, but in a sentence "Opp% 81%"
   says percent twice. WOPR and TPRR keep their initials; nobody expands those. */
function bdRoleNums(pos){
  if (pos === "RB") return [[t("board.num.oppShare"), "opp_pct", "pct"],
                            [t("board.num.routeRate"), "route_pct", "pct"],
                            [t("board.num.goalLine"), "gl_share", "pct"]];
  if (pos === "TE") return [[t("board.num.snapRate"), "snap_pct", "pct"],
                            [t("board.num.routeRate"), "route_pct", "pct"],
                            [t("board.num.wopr"), "wopr", "two"]];
  return [[t("board.num.routeRate"), "route_pct", "pct"],
          [t("board.num.wopr"), "wopr", "two"],
          [t("board.num.tprr"), "tprr", "pct"]];
}

function bdStyleNums(pos){
  if (pos === "RB") return [[t("board.num.beforeContact"), "ybc_att", "two"],
                            [t("board.num.afterContact"), "yac_att", "two"],
                            [t("board.num.breakaway"), "brk_rate", "pct"]];
  if (pos === "QB") return [[t("board.num.designed"), "designed_pct", "pct"],
                            [t("board.num.scramble"), "scr_rate", "pct"],
                            [t("board.num.goalLine"), "gl_pct", "pct"]];
  return [[t("board.num.adot"), "adot", "one"],
          [t("board.num.yacShare"), "yac_share", "share"],
          [t("board.num.catchRate"), "catch", "share"]];
}

/* usageFmt is the page's number formatter and the sheet's own fmt names come straight from it, so
   a stat reads the same here as on its lane. "share" is the one addition: the career blocks
   publish yac_share and catch as fractions where the season sheet publishes percents. */
function bdNum(v, fmt){
  if (v === null || v === undefined) return null;
  return fmt === "share" ? Math.round(v * 100) + "%" : usageFmt(v, fmt);
}

function bdEvLine(ev, nums){
  return nums.map(([lab, key, fmt]) => {
    const n = bdNum(ev[key], fmt);
    return n === null ? null : `${lab} ${n}`;
  }).filter(Boolean).join(" · ");
}

/* How much the label rests on, beside the window it was measured over: both answer "can I check
   this", so they share the label row rather than taking a line of their own. */
function bdSampleText(field, pos, ev){
  const n = k => bdNum(ev[k], "int");
  if (field === "role")
    return n("touch") !== null ? t("board.label.touches", {n: n("touch")})
      : n("games") !== null ? t("board.label.games", {n: n("games")}) : "";
  if (pos === "RB") return n("car") === null ? "" : t("board.label.carries", {n: n("car")});
  if (pos === "QB") return n("dropbacks") === null ? "" : t("board.label.dropbacks", {n: n("dropbacks")});
  return n("tgt") === null ? "" : t("board.label.targets", {n: n("tgt")});
}

/* One field: its name and window, then the word (or the reason there is none), then the numbers.
   `f.ev` is null for a field a position does not have at all -- a quarterback's role -- and the
   reason alone is the whole answer there. */
function bdFieldHTML(f){
  const meta = f.ev ? [esc(f.ev.window || ""), bdSampleText(f.field, f.pos, f.ev)].filter(Boolean).join(" · ") : "";
  const line = f.ev ? bdEvLine(f.ev, f.nums) : "";
  return `<div class="bd-fld">
    <div class="bd-fld-h"><span class="lbl">${f.label}</span
      >${meta ? `<span class="lbl bd-win">${meta}</span>` : ""}</div>
    <div class="bd-line">${f.word ? `<b class="bd-word">${f.word}</b>`
      : `<span class="bd-why">${esc(f.why || "")}</span>`}${f.flag || ""}</div>
    ${line ? `<p class="note bd-ev">${line}</p>` : ""}
  </div>`;
}

/* Under the picks, one card per picked player, because the record is his and most of the board has
   none. The card is headed only when there are two: with one pick the chip directly above already
   names him, and repeating it would put the same name on the screen twice in 40px. */
function bdLabelsHTML(picks){
  const recs = picks.map(p => [p, bdArch(p.slug)]).filter(x => x[1]);
  if (!recs.length) return "";
  const cards = recs.map(([p, a]) => `<section class="bd-lab">
    ${recs.length > 1 ? `<div class="bd-lab-h"><span class="bd-key">${esc(initials(p.n))}</span
      ><b>${esc(nameInitial(p.n))}</b></div>` : ""}
    ${bdFieldHTML({field: "role", pos: a.pos, label: t("board.label.role"), word: a.role ? bdRoleWord(a.role) : "",
                   why: a.role_null, ev: a.role_evidence, nums: bdRoleNums(a.pos)})}
    ${bdFieldHTML({field: "style", pos: a.pos, label: t("board.label.style"), word: a.style ? bdStyleWord(a.style) : "",
                   why: a.style_null, ev: a.style_evidence, nums: bdStyleNums(a.pos),
                   flag: bdFlagsHTML(a.flags)})}
  </section>`).join("");
  const say = recs.some(([, a]) => a.style) ? `<p class="note bd-say">${t("board.label.caveat")}</p>` : "";
  return `<div class="bd-labels">${cards}</div>${say}`;
}
