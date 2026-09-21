/* ---------------------------- views ---------------------------- */
/* Navigation is two levels: a group in the nav bar, a leaf under it. SURFACE is always the
   leaf, never the group, because every render branch asks "which view am I drawing" and none
   of them asks "which group" -- deriving the group from the leaf keeps one source of truth. */
let SURFACE = "roster";
let VIEW = "yahoo";
/* The leaf each group was last left on. Coming back to Scouting returns you to the view you
   were reading rather than resetting to Movers, which matters most for Grid: the week and
   position you had picked survive, so the tab is where you left it. */
let LAST_LEAF = {};
