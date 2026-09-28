/* Whose browser this is (2026-09-27, David: "Hide my waiver from my leaguemates"). The page is public
   and has no logins, so David's claim advice (Waivers' cards, its counts, the roster's waiver line,
   search's waiver rows) shows only in a browser that opened his private link, #owner-<token>, once.
   Everyone else's Waivers is the league-wide "Most added" list (surface/teams/hot.js).

   Only the token's SHA-256 ships here, never the token. The advice itself is still in the page's
   source (LIVE_WAIVER): this hides it from the screen, not from DevTools, which David chose over
   encrypting it. The link is wiped from the address bar at once, like #connect=. */
const OWNER_HASH = "54b415d2982e5a17819c4e9101540c5797d16753ad86237f3e077883cb8765b3";
const OWNER_KEY = "tw-owner";

function isOwner(){
  try { return localStorage.getItem(OWNER_KEY) === OWNER_HASH; } catch (e) { return false; }
}

/* true when the address bar carried David's link and this browser is now his. */
async function ownerClaim(){
  const m = /^#owner-([A-Za-z0-9]+)$/.exec(location.hash);
  if (!m) return false;
  history.replaceState(null, "", location.pathname + location.search + "#waivers");
  if (!(window.crypto && crypto.subtle)) return false;
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(m[1]));
  const hex = [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, "0")).join("");
  if (hex !== OWNER_HASH) return false;
  try { localStorage.setItem(OWNER_KEY, OWNER_HASH); } catch (e) { return false; }
  return true;
}
