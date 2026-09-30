/* Blip, the page's mascot (2026-09-29, the "Digest Banner and Mascot" draft, option A; first used
   2026-09-29 for the Digest's wait, storyboard https://claude.ai/artifact/UDoWgLMrzUHup5tX53zaue):
   a small screen on legs that watches the games so the reader does not have to. Its face is a
   screen, so a mood is two eyes and a mouth in lime.

   Drawn in code, from classes (wait.css), so it takes the tokens like everything else. A sketch:
   public-launch art would replace these shapes and keep the classes. Still, no idle motion.

   Poses: awake (the wait card), "asleep", eyes shut and a z or two, for a Digest row with
   nothing new (the empty Starters row, 2026-09-29), and "bored", eyes rolled up to the corner and a
   flat mouth, for Takes with no experts to argue with yet (2026-09-29). No label = decoration,
   when the words beside it already name him. Shared by every view since then (lib/, not digest/). */
const BLIP_FACE = {
  awake: `<circle class="blip-eye" cx="47" cy="52" r="5"/><circle class="blip-eye" cx="73" cy="52" r="5"/>
    <path class="blip-mouth" d="M50 64q10 6 20 0"/>`,
  bored: `<circle class="blip-eye" cx="51" cy="46" r="4"/><circle class="blip-eye" cx="77" cy="46" r="4"/>
    <path class="blip-mouth" d="M49 64h22"/>`,
  asleep: `<path class="blip-mouth" d="M40 52h13M67 52h13"/><path class="blip-mouth dim" d="M54 64h12"/>
    <text class="blip-z" x="90" y="16">z</text><text class="blip-z sm" x="102" y="6">z</text>`,
};
/* Smug (2026-09-29, per David; logo storyboard round 2): the logo mark. The head alone and lit: a
   lime screen, half-lidded eyes, one brow raised at the slash angle, a sideways smirk, and the
   wordmark's // for an antenna, leaning forward 22deg like .brand-name .slashes. On a 100 box.
   "smug-app" sets it in its case on the page ground (the 180px apple-touch icon); "smug-16" is the
   favicon, where the antenna and brow drop and the lids and smirk grow. design/icons.py cuts both
   icon files from these, so the icons are this drawing too. Still at rest, like every pose. */
const BLIP_SMUG_ANT = `<path class="blip-bulb" d="M35.65 29.5H42.15L51.85 5.5H45.35ZM48.15 29.5H54.65L64.35 5.5H57.85Z"/>`;
const BLIP_SMUG_FACE = `<g transform="translate(50 62.5)"><path class="blip-eye" d="M-26 -1A10 10 0 0 0 -6 -1Z"/>
    <path class="blip-eye" d="M6 -1A10 10 0 0 0 26 -1Z"/><path class="blip-mouth" d="M7 -14.6L26 -22.3"/>
    <path class="blip-mouth" d="M-10 15.5Q4 18.5 13 10"/></g>`;
const BLIP_SMUG = {
  smug: `${BLIP_SMUG_ANT}<rect class="blip-screen" x="4" y="30" width="92" height="65" rx="17"/>${BLIP_SMUG_FACE}`,
  "smug-app": `<rect class="blip-ground" width="100" height="100"/><g transform="translate(13 13) scale(.74)">${BLIP_SMUG_ANT}
    <rect class="blip-case" x="1.5" y="27" width="97" height="70" rx="20"/>
    <rect class="blip-screen" x="8" y="33" width="84" height="58" rx="13"/>${BLIP_SMUG_FACE}</g>`,
  "smug-16": `<rect class="blip-screen" x="1" y="12" width="98" height="76" rx="21"/><g transform="translate(50 50)">
    <path class="blip-eye" d="M-33 -5A14 14 0 0 0 -5 -5Z"/><path class="blip-eye" d="M5 -5A14 14 0 0 0 33 -5Z"/>
    <path class="blip-mouth" d="M-12 20Q6 23 18 12"/></g>`,
};
/* Reactions (2026-09-29, storyboard https://claude.ai/artifact/RKkFYVa7asD65uWfvLMVLU, all five kept by
   David): the League recap's lead when its joke names no player. Each holds the awake face (.br-f0)
   and the reaction (.br-f1) so the swap can play once; at rest only the reaction shows. The build
   picks the pose (design/league_back.py blip_of) from the lead game's place in the week.
   Drawn and played by css/surface/league/blip-lead.css. */
const BLIP_REACT = {
  wince: `<path class="blip-mouth" d="M41 46l8 6-8 6M79 46l-8 6 8 6"/><path class="blip-mouth" d="M46 67l4-3 4 3 4-3 4 3 4-3 4 3"/>`,
  flatline: `<g class="br-ekg"><path class="blip-mouth" pathLength="100" d="M31 50h13l3-10 5 20 4-14 3 4h32"/></g>
    <text class="br-nosig" x="60" y="70">NO SIGNAL</text>`,
  ko: `<path class="blip-mouth" d="M42 47l10 10M52 47l-10 10M68 47l10 10M78 47l-10 10"/><path class="blip-mouth" d="M49 68q3.5-4 7 0t7 0 7 0"/>`,
  sweat: `<circle class="blip-mouth" cx="47" cy="52" r="7"/><circle class="blip-mouth" cx="73" cy="52" r="7"/>
    <g class="br-pup"><circle class="blip-eye" cx="47" cy="52" r="2.8"/><circle class="blip-eye" cx="73" cy="52" r="2.8"/></g>
    <path class="blip-mouth" d="M47 68q3-3 6 0t6 0 6 0 6 0"/>`,
  laugh: `<path class="blip-mouth" d="M41 55q6-9 12 0M67 55q6-9 12 0"/><path class="blip-eye" d="M47 61h26q-1 12-13 12t-13-12z"/>`,
};
const blipStar = (x, y, s) => `<g transform="translate(${x} ${y}) scale(${s})"><path class="br-star" d="M0-6L1.5-1.5 6 0 1.5 1.5 0 6-1.5 1.5-6 0-1.5-1.5Z"/></g>`;
const BLIP_REACT_OUT = {
  ko: blipStar(34, 14, 1) + blipStar(88, 8, .8) + blipStar(100, 26, .6),
  sweat: `<path class="br-drop" d="M105 24q5 7 0 11q-5-4 0-11z"/>`,
};
function blipReactSVG(label, pose){
  const a11y = label ? `role="img" aria-label="${esc(label)}"` : `aria-hidden="true"`;
  return `<svg class="blip br br-${pose}" viewBox="0 0 120 120" ${a11y}><g class="br-bod">
    <path class="blip-ink" d="M60 20V10"/><circle class="blip-bulb" cx="60" cy="7" r="4"/>
    <rect class="blip-case" x="18" y="20" width="84" height="66" rx="15"/>
    <rect class="blip-screen" x="27" y="28" width="66" height="48" rx="10"/>
    <g class="br-f0">${BLIP_FACE.awake}</g><g class="br-f1">${BLIP_REACT[pose]}</g>
    <path class="blip-ink" d="M44 86l-4 22M76 86l4 22M32 110h14M74 110h14"/></g>${BLIP_REACT_OUT[pose] || ""}</svg>`;
}

function blipSVG(label, pose){
  const a11y = label ? `role="img" aria-label="${esc(label)}"` : `aria-hidden="true"`;
  if (BLIP_SMUG[pose]) return `<svg class="blip smug ${pose}" viewBox="0 0 100 100" ${a11y}>${BLIP_SMUG[pose]}</svg>`;
  return `<svg class="blip" viewBox="0 0 120 120" ${a11y}>
    <path class="blip-ink" d="M60 20V10"/><circle class="blip-bulb" cx="60" cy="7" r="4"/>
    <rect class="blip-case" x="18" y="20" width="84" height="66" rx="15"/>
    <rect class="blip-screen" x="27" y="28" width="66" height="48" rx="10"/>
    ${BLIP_FACE[pose] || BLIP_FACE.awake}
    <path class="blip-ink" d="M44 86l-4 22M76 86l4 22M32 110h14M74 110h14"/></svg>`;
}
