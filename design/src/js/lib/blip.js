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
