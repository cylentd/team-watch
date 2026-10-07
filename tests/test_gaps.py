"""design/STYLE.md "Gaps": every box says where its free space goes (David, 2026-10-07).

Every NAV leaf is mounted at 360px and at 1280px, and one page.evaluate measures the empty runs:

- **A row** (a flex or grid box, 2+ shown children side by side, under 120px tall, 200px wide or more):
  the widest run between neighbouring children's boxes, plus the run before the first child or after the
  last one when `justify-content` puts space there (center, end, space-around, space-evenly). Too wide:
  over max(33% of its content width, 48px) at 360, over 33% and over 160px at 1280.
- **A track** (a flex or grid box under 200px wide, 2+ children on one line, `justify-content` end): a
  fixed-width thing pushed to one end of its track, the run before it over max(33%, 24px). It centres in its
  track, or the track hugs it (rule 2).
- **A fixed-size card** (2+ shown children, 48px tall or more, under 75% of the screen tall, and taller
  than its content would make it): the run under its last child, or, with 3+ children, an inner run over
  twice the next biggest (the middle block hugs one end instead of centring), is over 15% of its height
  and over 16px (the origin case: 24px under the bars of a 138px card back on a phone, 17%).

Today's true violations are KNOWN, with the reason and the fix. The list only shrinks: a found run not in
it fails, and an entry that no longer violates fails too, so it is removed when its fix lands.
"""
import pathlib
import re
from unittest import mock

import pytest

import component
from component import Mounter, mount  # noqa: F401  (the fixture)
from pages.roster_motion import SHOW_CARDS
from test_style_rules import PerSize, settle

ROOT = pathlib.Path(__file__).resolve().parents[1]
NAVMAP = ROOT / "design" / "src" / "js" / "data" / "navmap.js"


def nav_leaves():
    """Every leaf of `NAV` in js/data/navmap.js, in its order."""
    table = NAVMAP.read_text(encoding="utf-8").split("const NAV = [", 1)[1].split("];", 1)[0]
    return [leaf for tabs in re.findall(r'\[\s*"\w+",\s*\[([^\]]*)\]', table) for leaf in re.findall(r'"(\w+)"', tabs)]


LEAVES = nav_leaves()
WIDTHS = {360: (360, 800), 1280: (1280, 900)}

# The measurement, one call per view. Each exclusion says why it is not a gap:
# - position absolute/fixed children: overlays, badges and stickers, out of the row's flow.
# - hidden or zero-size children, and anything under aria-hidden="true": decoration nobody reads.
# - anything inside a closed <details> but its summary: Chromium lays it out (it has a box) but nobody sees
#   it (2026-10-07: Waivers' folded Speculative and Stash cards read as empty cards).
# - a card that is only stretched to its grid row's tallest, with under 48px left at its bottom and no
#   lopsided middle: Share edges makes that space (2026-10-07: a News practice row, 21px of 129px at 1280).
# - a box that scrolls or clips sideways (overflow-x auto/scroll/hidden): a rail, its run is a scroll position.
# - a box off the screen sideways: a carousel's other pages.
# - the run after the last child of a start-justified row: left-aligned rows (chips, tags, a name with its
#   note) end where their words end, by the Alignment table; only space a row places on purpose is counted.
# - children that wrap onto a second line: a wrapped row is a grid of lines, not one row.
# - a row whose children reach both of its content edges (a title and its action, a name and its value, a
#   tab row and its Compare): its space goes between groups, as the rule asks (2026-10-07: 27 of 36 first
#   flags were these headers and toolbars, read from screenshots). A label far from its value on a desktop
#   is "A label stays within 560px" and its own test, not this one.
GAPS = r"""(phone) => {
  const css = e => getComputedStyle(e), px = v => parseFloat(v) || 0;
  const shown = e => { const s = css(e); if (s.display === 'none' || s.visibility === 'hidden' || +s.opacity === 0) return false;
    const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const counts = e => !['SCRIPT', 'STYLE', 'TEMPLATE', 'BR'].includes(e.tagName) && shown(e)
    && !/^(absolute|fixed)$/.test(css(e).position) && e.getAttribute('aria-hidden') !== 'true';
  const name = e => e.tagName.toLowerCase() + [...e.classList].slice(0, 2).map(c => '.' + c).join('');
  const sel = e => (e.parentElement && e.parentElement.id !== 'view' ? name(e.parentElement) + ' > ' : '') + name(e);
  const worst = new Map();
  const keep = (kind, e, run, size) => {
    const k = kind + ' ' + sel(e), was = worst.get(k);
    if (!was || run > was[2]) worst.set(k, [kind, sel(e), Math.round(run), Math.round(size)]);
  };
  for (const e of document.querySelectorAll('#view *')) {
    if (e.closest('[aria-hidden="true"]') || !shown(e)) continue;
    const fold = e.closest('details:not([open])');
    if (fold && !e.closest('summary')) continue;
    const r = e.getBoundingClientRect();
    if (r.right <= 0 || r.left >= innerWidth) continue;
    const kids = [...e.children].filter(counts);
    if (kids.length < 2) continue;
    const s = css(e), boxes = kids.map(k => k.getBoundingClientRect());
    const left = r.left + px(s.borderLeftWidth) + px(s.paddingLeft), right = r.right - px(s.borderRightWidth) - px(s.paddingRight);
    const oneLine = Math.max(...boxes.map(b => b.top)) < Math.min(...boxes.map(b => b.bottom));
    if (/flex|grid/.test(s.display) && !/(auto|scroll|hidden)/.test(s.overflowX) && r.height < 120 && r.width >= 200 && oneLine) {
      const xs = boxes.slice().sort((a, b) => a.left - b.left);
      let run = 0, reach = xs[0].right;
      for (const b of xs.slice(1)) { run = Math.max(run, b.left - reach); reach = Math.max(reach, b.right); }
      if (xs[0].left <= left + 6 && reach >= right - 6) run = 0;
      const j = s.justifyContent;
      if (/center|end|right|space-around|space-evenly/.test(j)) run = Math.max(run, xs[0].left - left);
      if (/center|space-around|space-evenly/.test(j)) run = Math.max(run, right - reach);
      const w = right - left;
      if (phone ? run > Math.max(w / 3, 48) : run > w / 3 && run > 160) keep('row', e, run, w);
    }
    if (/flex|grid/.test(s.display) && r.width < 200 && r.height < 120 && oneLine && /end|right/.test(s.justifyContent)) {
      const lead = Math.min(...boxes.map(b => b.left)) - left, w = right - left;
      if (lead > Math.max(w / 3, 24)) keep('track', e, lead, w);
    }
    if (r.height >= 48 && r.height < innerHeight * 0.75 && !/(auto|scroll)/.test(s.overflowY)) {
      // Seen ink counts here, aria-hidden too: a decorative foot still holds the card's bottom edge.
      const ys = [...e.children].filter(k => counts(k) || (k.getAttribute('aria-hidden') === 'true' && shown(k)
        && !/^(absolute|fixed)$/.test(css(k).position))).map(k => k.getBoundingClientRect()).sort((a, b) => a.top - b.top);
      const bottom = r.bottom - px(s.borderBottomWidth) - px(s.paddingBottom);
      let reach = ys[0].bottom; const runs = [];
      for (const b of ys.slice(1)) { runs.push(b.top - reach); reach = Math.max(reach, b.bottom); }
      const under = bottom - reach;
      // A card of 3+ items whose middle hugs one end: its biggest inner run is over twice the next one.
      const inner = ys.length > 2 ? runs.slice().sort((a, b) => b - a) : [0];
      const pile = inner[0] > 2 * Math.max(inner[1] || 0, 8) ? inner[0] : 0;
      const run = Math.max(under, pile);
      if (run > Math.max(r.height * 0.15, 16)) {
        const was = e.getAttribute('style');
        e.style.setProperty('height', 'auto', 'important'); e.style.setProperty('min-height', '0', 'important');
        e.style.setProperty('aspect-ratio', 'auto', 'important');
        const sized = e.getBoundingClientRect().height < r.height - run / 2;
        e.style.setProperty('align-self', 'start', 'important');
        const free = e.getBoundingClientRect().height;
        if (was === null) e.removeAttribute('style'); else e.setAttribute('style', was);
        // A card only stretched to its row's tallest (no size of its own) keeps a little trailing space, as
        // "Share edges" asks; it is a gap from 48px, or when its middle hugs one end.
        if (free < r.height - run / 2 && (sized || pile >= under || under > 48)) keep('card', e, run, r.height);
      }
    }
  }
  return [...worst.values()];
}"""

# Today's true violations: (leaf, width, kind, selector) -> why it is one, and where it is being fixed.
KNOWN = {
}


@pytest.fixture(scope="module")
def mounted(mount, built):
    """One page per size (test_style_rules' PerSize). Matchups and Highlights have no entry in
    component.SURFACES, a frozen file, so their pages are written here with the dict patched for the call
    and restored at once (collection of every other module is over by then)."""
    m = Mounter(mount.browser, mount.folder, built.fragment)
    m.pages = PerSize()
    with mock.patch.dict(component.SURFACES, {leaf: leaf for leaf in LEAVES if leaf not in component.SURFACES}):
        for leaf in LEAVES:
            m.url(leaf)
    for size in WIDTHS.values():        # each size's context opens here, not in its first test's call
        m.prepare(LEAVES[0], size=size)
    yield m
    m.pages.close()


def gaps(page, phone):
    return {(kind, sel): (run, size) for kind, sel, run, size in page.evaluate(GAPS, phone)}


# States a leaf's first draw does not show, as (surface, script): Roster in Cards mode with every starter's
# card turned to its back, where the points bars sat high over an empty bottom (the rule's origin,
# 2026-10-07). The ESPN team is followed, so its pack waits first: Skip puts the cards face up.
STATES = {
    "roster-cards": ("roster", f"""(a) => {{ ({SHOW_CARDS})(a);
      document.querySelectorAll('[data-testid="roster-card"]').forEach(c => c.click()); }}"""),
}
VIEWS = LEAVES + list(STATES)


@pytest.mark.render
@pytest.mark.parametrize("width", sorted(WIDTHS))
@pytest.mark.parametrize("leaf", VIEWS)
def test_no_box_piles_its_free_space_in_one_gap(mounted, leaf, width):
    surface, script = STATES.get(leaf, (leaf, None))
    page, errors = mounted(surface, size=WIDTHS[width])
    if script:
        page.evaluate(script, ["espn", "skip"])
    settle(page)
    found = gaps(page, width == 360)
    known = {(kind, sel) for (lf, w, kind, sel) in KNOWN if (lf, w) == (leaf, width)}
    new = [f"{leaf} at {width}px: {kind} {sel} has a {found[(kind, sel)][0]}px empty run in "
           f"{found[(kind, sel)][1]}px" for kind, sel in sorted(set(found) - known)]
    stale = sorted(known - set(found))
    assert new == [], "a box piles its free space in one gap (STYLE.md \"Gaps\"):\n" + "\n".join(new)
    assert stale == [], f"{leaf} at {width}px: fixed, remove from KNOWN: {stale}"
    assert errors == []
