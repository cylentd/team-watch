/* The profile head's rail (2026-09-30, storyboard https://claude.ai/artifact/1q2rFmEudfwzyKdf5mgoCy;
   David: "build the rail, centred"). His role and style words, his stat sphere and Compare, as one
   row of round medallions with their labels under them, the sphere's own shape. On a phone it sits
   under the name and frees the name block of the two tiles and Compare that used to stack there
   (Higgins 302px to 247px tall, Zay Flowers 289 to 220).

   Always in this order; a player with fewer keeps the order and the row centres, so a missing word
   is no hole. With nothing but Compare (deep bench, 227 of 540 skill players on 2026-09-30) there is
   no rail at all, and Compare stays a small button in the name block (panel.js). */
function pfRailHTML(p){
  const slots = archSlotsHTML(p), orb = orbBadgeHTML(p);
  if (!slots.length && !orb) return "";
  return `<div class="pf-rail" data-testid="profile-rail">${slots.join("")}${orb}${cmpButtonHTML(true)}</div>`;
}
