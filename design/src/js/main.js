buildFeed();
buildNav();
render();
buildChat();   // the floating panel: outside #view, so it is wired once rather than per render
buildLive();   // one poll timer for the life of the page, inert unless the Live tab is on screen
