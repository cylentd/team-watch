/* A hash in the address bar wins over the default view: a reload, a bookmark and a shared link
   all arrive this way, and all three should land where they point. Without one, the day picks
   (nav.js navDefaultLeaf: Waivers on a Tuesday, the roster otherwise). */
SURFACE = navFromHash() || navDefaultLeaf();

buildFeed();
buildNav();
render();
buildFresh();  // is /build.json still ours? asked on a tab click and on returning to the window
buildChat();   // the floating panel: outside #view, so it is wired once rather than per render
buildLive();   // one poll timer for the life of the page, inert unless the Live tab is on screen
