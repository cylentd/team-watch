/* ---------------------------- views ---------------------------- */
/* Navigation is two levels: a group in the nav bar, a leaf under it. SURFACE is always the
   leaf, never the group, because every render branch asks "which view am I drawing" and none
   of them asks "which group" -- deriving the group from the leaf keeps one source of truth. */
let SURFACE = "roster";
/* The team on screen: the reader's own pick when they made one (data/mates.js), else David's. */
let VIEW = myTeamLoad() || "yahoo";
/* The leaf each group was last left on. Coming back to Scouting returns you to the view you
   were reading rather than resetting to Movers, which matters most for Grid: the week and
   position you had picked survive, so the tab is where you left it. */
let LAST_LEAF = {};
/* How the roster draws: "sheet" (the lineup sheet) or "cards" (surface/teams/cards.js). Remembered
   per phone (cardmotion.js rosterModeLoad); the sheet is the default. */
let ROSTER_MODE = rosterModeLoad();
