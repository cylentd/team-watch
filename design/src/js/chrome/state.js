/* ---------------------------- views ---------------------------- */
/* Navigation is two levels: a group in the nav bar, a leaf under it. SURFACE is always the
   leaf, never the group, because every render branch asks "which view am I drawing" and none
   of them asks "which group" -- deriving the group from the leaf keeps one source of truth. */
let SURFACE = "roster";
/* The team on screen: the reader's own pick when they made one (data/mates.js), else David's. */
let VIEW = myTeamLoad() || "yahoo";
/* How the roster draws: "sheet" (the lineup sheet) or "cards" (surface/teams/cards.js). Remembered
   per phone (cardmotion.js rosterModeLoad); cards is the default since 2026-09-28. */
let ROSTER_MODE = rosterModeLoad();
