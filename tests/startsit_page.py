"""The shared Start/Sit page for tests/test_startsit.py and tests/test_startsit_v3.py: one loaded page per
module, put back to a fresh load's state before every test (RESET_JS). Not a test file."""
import re

from test_render import LOAD_MS, PICKED, SEED, watch_errors

PRISTINE_JS = """() => {
  const live = {LIVE_RANKS, LIVE_PROJECTIONS, LIVE_STARTSIT, LIVE_SS3, TEAMS};
  const hadSSB = typeof LIVE_SSB === 'object' && !!LIVE_SSB;
  if (hadSSB) live.LIVE_SSB = LIVE_SSB;
  window.__pristine = {live, hadSSB, snap: Object.fromEntries(Object.entries(live).map(([k, v]) => [k, structuredClone(v)]))};
}"""

# Puts the shared page back to what a fresh load shows: the live blocks the tests mutate, the picker's
# state, localStorage, open layers (the profile modal) and the view. Every test starts from here,
# whichever worker it lands on. Strict, so a global the page renames throws instead of the assignment
# quietly making a new one.
RESET_JS = """() => {
  'use strict';
  document.querySelectorAll('.modal.on').forEach(d => modalShut(d));
  LAYERS.length = 0; LAYER_SKIP.length = 0;
  // A fresh load's entry has no state. A test that leaves a layer open (Compare two) leaves its entry
  // {layer} current, and a later Back would land on it; take the state off so no test inherits it.
  history.replaceState(null, '');
  const p = window.__pristine;
  for (const [k, v] of Object.entries(p.live)) {
    const s = structuredClone(p.snap[k]);
    if (Array.isArray(v)) { v.length = 0; v.push(...s); } else { for (const key of Object.keys(v)) delete v[key]; Object.assign(v, s); }
  }
  if (!p.hadSSB && typeof LIVE_SSB !== 'undefined') delete window.LIVE_SSB;
  delete window.__takes;
  try { localStorage.clear(); } catch (e) {}
  %s
  SS_PICKS = null; SS_OPEN = false; SS_Q = ''; SS_BTAB = ''; SS_CMP = false;
  window.scrollTo(0, 0);
  navGo('matchups');
}""" % PICKED


def open_view(browser, page_file, js="", w=360, h=800, hash_="#matchups", errors=None):
    """A touch page on the Start/Sit view, its page errors appended to `errors` when a list is given."""
    ctx = browser.new_context(viewport={"width": w, "height": h}, reduced_motion="reduce", has_touch=True)
    pg = ctx.new_page()
    pg.set_default_timeout(5000)
    watch_errors(pg, errors)
    pg.route(re.compile(r"^https?://"), lambda route: route.abort())
    pg.add_init_script(SEED)
    pg.goto(page_file.as_uri() + hash_, timeout=LOAD_MS)
    pg.wait_for_function("document.querySelector('.mu') !== null")
    if js:
        pg.evaluate("() => {" + js + "; render(); }")
    return ctx, pg
