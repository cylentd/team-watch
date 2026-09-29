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
function blipSVG(label, pose){
  const a11y = label ? `role="img" aria-label="${esc(label)}"` : `aria-hidden="true"`;
  return `<svg class="blip" viewBox="0 0 120 120" ${a11y}>
    <path class="blip-ink" d="M60 20V10"/><circle class="blip-bulb" cx="60" cy="7" r="4"/>
    <rect class="blip-case" x="18" y="20" width="84" height="66" rx="15"/>
    <rect class="blip-screen" x="27" y="28" width="66" height="48" rx="10"/>
    ${BLIP_FACE[pose] || BLIP_FACE.awake}
    <path class="blip-ink" d="M44 86l-4 22M76 86l4 22M32 110h14M74 110h14"/></svg>`;
}
