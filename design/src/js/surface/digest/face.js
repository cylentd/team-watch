/* ============================== HOME: THE HERO'S FACE ==============================
   Ledger #63 (David 2026-10-08, "face a"; the subject since the same evening: "flashy and cool... the first thing
   people see"): the hero's subject. A headline about one player shows his 256px cut-out (heads/lg/ where
   ff-jarvis cut one, else heads/), filling a pane at the band's right with his club's code on its edge (v3, below);
   any other headline shows Blip standing in the same pane and leaning into the headline. The pose is League's set (surface/league/lead.js LG_BLIP_LABEL, lib/blip.js
   blipReactSVG), picked by data/hero.js dgHeroFace from the day's job and Claude's call. The face sits outside
   the words (digest/face.css), so the headline keeps its full width and is never cut. Blip is drawn without a
   label: the headline beside him says what the day is about. His reaction plays once as the page lands
   (`bp-in`, league/blip-lead.css), still under reduced motion. */
/* The band's budget on a phone: a third of the screen (tests/pages/digest_day.py hero_fits), so the first card
   starts on the first screen. A headline that pushes the band past it takes a size down (hero.css `long`),
   measured in the reader's browser after the render, never guessed from its length (STYLE.md Layout). */
const DG_HERO_BUDGET = 3;  // nomutate: the budget itself; its tests read it back
function dgHeroFit(root){
  const bn = root && root.querySelector(".dg-bn.hero"), h = bn && bn.querySelector(".dg-bn-h");
  if (!h || h.classList.contains("long")) return;
  if (bn.getBoundingClientRect().height > window.innerHeight / DG_HERO_BUDGET) h.classList.add("long");
}

/* Hero v3, "the spread" (David 2026-10-08, ledger #70): the subject sits in a pane at the band's right (face.css),
   his club's code on the pane's outer edge when the lead knows his club. */
const dgHeroPane = (inner, club) => `<div class="dg-hpane" data-testid="digest-lead-pane" aria-hidden="true">${inner}${
  club ? `<span class="dg-hclub" data-testid="digest-lead-club">${esc(club)}</span>` : ""}</div>`;

function dgHeroFaceParts(L, plan){
  const lg = typeof HEADS_LG !== "undefined" && HEADS_LG ? HEADS_LG : {}, sm = typeof HEADS !== "undefined" ? HEADS : {};  // nomutate: a null HEADS_LG passes either way, dgHeroFace reads it as (lg || {})
  const f = dgHeroFace(L, plan && plan.banner, lg, sm);
  if (f.slug){
    const team = dgTeamCode(dgHeroTeam(L, f.slug));
    return {kind: "has-face", team,
      html: dgHeroPane(`<img class="dg-hface" data-testid="digest-lead-face" src="${esc(f.src)}" alt="" decoding="async" onerror="this.remove()">`, team)};
  }
  if (!LG_BLIP_LABEL[f.pose]) return {kind: "", team: "", html: ""};
  return {kind: "has-blip", team: "", html: dgHeroPane(`<figure class="dg-hblip bp-in" data-testid="digest-lead-blip" data-pose="${f.pose}">${
    blipReactSVG("", f.pose)}</figure>`, "")};
}
