/* The archetype on the profile (2026-09-29, David: "It should be on the player profile"). Until
   now its two words -- ROLE, what he is asked to do this season, and STYLE, what he does with the
   ball over his career -- showed only under a Leaders comparison pick, and most readers never made
   one. The data is ff-jarvis's model.season.archetype (LIVE_ARCHETYPE, 346 players); the rules
   behind each word are ff-jarvis model/season/ARCHETYPE.md.

   Two places, one record. The head carries the words as a skill bar under his name -- a tile per
   word with the word beneath, so a reader sees "early down, complete" without opening anything; a
   tap opens Usage, where the same words sit with what each means and the numbers that produced it
   (the Leaders card's own markup, board/label.js bdFieldHTML). A word the model withholds (under
   its floor) is no tile in the head, and its reason stands in its place in Usage.

   The tiles (2026-09-29, storyboard v2, David: "B ... since you can actually see the icon"): a
   game-icons.net glyph (archglyphs.js, CC BY 3.0, credited in the footer) engraved on a bevelled
   stone, steel for a Role word and bronze for a Style word (tokens --arch-role / --arch-style). */
function archTileHTML(v, field){
  const g = ARCH_GLYPH[v];
  return g ? `<span class="pf-sk pf-sk-${field}"><svg viewBox="0 0 512 512" aria-hidden="true"><path d="${g[1]}"/></svg></span>` : "";
}

/* What each word means, in one clause. Spelled out one literal t() per word, the same reason
   AXIS_DEF is (statcard.js): assemble.py --check finds a copy key by its literal form. */
const ARCH_MEAN = {
  every_down:  pos => pos === "RB" ? t("profile.arch.mean.everyDownRb") : t("profile.arch.mean.everyDownRec"),
  early_down:  () => t("profile.arch.mean.earlyDown"),
  satellite:   () => t("profile.arch.mean.satellite"),
  goal_line:   () => t("profile.arch.mean.goalLine"),
  committee:   () => t("profile.arch.mean.committee"),
  rotational:  () => t("profile.arch.mean.rotational"),
  situational: () => t("profile.arch.mean.situational"),
  move:        () => t("profile.arch.mean.move"),
  in_line:     () => t("profile.arch.mean.inLine"),
  power:       () => t("profile.arch.mean.power"),
  home_run:    () => t("profile.arch.mean.homeRun"),
  complete:    pos => pos === "RB" ? t("profile.arch.mean.completeRb") : t("profile.arch.mean.completeRec"),
  one_cut:     () => t("profile.arch.mean.oneCut"),
  deep_threat: () => t("profile.arch.mean.deepThreat"),
  possession:  () => t("profile.arch.mean.possession"),
  yac:         () => t("profile.arch.mean.yac"),
  dual_threat: () => t("profile.arch.mean.dualThreat"),
  pocket:      () => t("profile.arch.mean.pocket"),
  scrambler:   () => t("profile.arch.mean.scrambler"),
};
const archMean = (v, pos) => ARCH_MEAN[v] ? ARCH_MEAN[v](pos) : "";

/* The head's chips: one per word he has, role first, each a button to the Usage block. Drawn twice,
   `where` "in" (under the name) and "side" (beside the sphere), and the CSS shows one per width
   (storyboard v4, 2026-09-29): beside the sphere on a desktop, where under the name read as busy,
   and under the name on a phone, which has no room beside its sphere. The hidden copy is
   display:none, so it is out of the tab order and the accessibility tree. */
function archTagsHTML(p, where){
  const a = bdArch(p.slug);
  if (!a || (!a.role && !a.style)) return "";
  const slot = (field, v, word) => `<button type="button" class="pf-arch-slot" data-pfarch="${field}"
    aria-label="${field === "role" ? t("profile.arch.roleIs", {w: word}) : t("profile.arch.styleIs", {w: word})}"
    >${archTileHTML(v, field)}<span>${word}</span></button>`;
  return `<div class="pf-arch pf-arch-${where}">${a.role ? slot("role", a.role, bdRoleWord(a.role)) : ""}${a.style ? slot("style", a.style, bdStyleWord(a.style)) : ""}</div>`;
}

/* Usage: the Leaders card's two fields, each word on its tile, the clause it means, and the
   numbers behind it. The caveat closes it when there is a style, as it does on Leaders. */
function archBlockHTML(p){
  const a = bdArch(p.slug);
  if (!a) return "";
  const word = (v, w) => v ? `${archTileHTML(v, v === a.role ? "role" : "style")}${w}` : "";
  const body = bdFieldHTML({field: "role", pos: a.pos, label: t("board.label.role"),
      word: word(a.role, a.role ? bdRoleWord(a.role) : ""), why: a.role_null, ev: a.role_evidence,
      nums: bdRoleNums(a.pos), say: a.role ? archMean(a.role, a.pos) : ""})
    + bdFieldHTML({field: "style", pos: a.pos, label: t("board.label.style"),
      word: word(a.style, a.style ? bdStyleWord(a.style) : ""), why: a.style_null, ev: a.style_evidence,
      nums: bdStyleNums(a.pos), flag: bdFlagsHTML(a.flags), say: a.style ? archMean(a.style, a.pos) : ""})
    + (a.style ? `<p class="note bd-say">${t("board.label.caveat")}</p>` : "");
  return secHTML(t("profile.arch.label"), body, "", "pf-sec-arch");
}
