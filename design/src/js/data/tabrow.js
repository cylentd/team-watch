/* ============================== THE PHONE'S ONE TAB ROW ==============================
   2026-10-05 (game-day flow wave 2, storyboard https://claude.ai/artifact/ArF53Lvh12QV8fbL3mr9KP,
   David: "Tab opens in place"). On a phone the group's views are pills in one row under the header,
   and the open view's pill opens in place into that view's own tabs:
     Recap  News  Preview  [Live: My league | NFL | TDs]
   so a view with tabs draws no second bar of its own there. A desktop keeps the words and the views'
   own bars. Pure and DOM-free (tests/test_js_tabrow.py); chrome/nav.js draws what this decides.

   A view with tabs declares them once, at load, with navModes(leaf, () => declaration):
     ids     its tabs, in order
     cur     the one open now
     attr    the data attribute its own bar's buttons carry ("gdtab" -> data-gdtab), so a segment
             in the row answers to the same selector as the view's own button
     label   id -> the words on the tab (literal copy keys in the view, for assemble.py --check)
     count   optional, id -> a small number beside the words (Live's NFL games on now)
     select  id -> opens that tab; the row repaints after it
   Declared today (2026-10-05): Live (surface/live/tabs.js), This week > Recap (surface/recap/recap.js)
   and Slips' kickoffs (surface/parlay/bar.js). */
const NAV_MODES = {};
function navModes(leaf, declare){ NAV_MODES[leaf] = declare; }
const navModesOf = leaf => (NAV_MODES[leaf] ? NAV_MODES[leaf]() : null);

/* tabRowPlan(tabs, leaf, modes, phone) -> {shown, pills: [{leaf, on, segs}]}
   tabs: the group's leaves in the row; leaf: the view open (SURFACE); modes: its declaration or null.
   segs is null except on the open pill, on a phone, when its view has two tabs or more: then
   [{id, on}], the current one pressed (the first when the current is not one of them). A view opened
   off the row (Weather, Schedule) presses no pill. The row shows with two pills, or with one that
   opens into tabs. */
function tabRowPlan(tabs, leaf, modes, phone){
  const ids = phone && modes && tabs.includes(leaf) && modes.ids.length > 1 ? modes.ids : [];
  const cur = ids.includes(modes && modes.cur) ? modes.cur : ids[0];
  const segs = ids.length ? ids.map(id => ({id, on: id === cur})) : null;
  return {
    shown: tabs.length > 1 || !!segs,
    pills: tabs.map(k => ({leaf: k, on: k === leaf, segs: k === leaf ? segs : null})),
  };
}

/* tabRowStep(plan, d) -> {leaf} | {seg} | null. A sideways swipe on a view is a tap on the next thing
   in the row (2026-10-06, David: the row is out of thumb reach; DESIGN.md "Swipe between tabs"). The
   stops are the row left to right: each pill, except that an opened pill is its tabs instead. d is +1
   (swipe left: the stop to the right) or -1. Null at either end, with no row, or on a view off the row. */
function tabRowStep(plan, d){
  if (!plan.shown) return null;
  const stops = plan.pills.flatMap(p => p.segs ? p.segs.map(s => ({seg: s.id, on: s.on})) : [{leaf: p.leaf, on: p.on}]);
  const at = stops.findIndex(s => s.on), next = at < 0 ? null : stops[at + d];
  if (!next) return null;
  return next.seg ? {seg: next.seg} : {leaf: next.leaf};
}

/* tabRowEnter(modes, d, phone) -> the tab to open | null. A swipe into a view whose pill opens into tabs
   lands on the tab nearest where it came from: its first on a swipe left, its last on a swipe right
   (2026-10-06, David: Digest -> Recap opened on the tab Recap remembered, and read as a skipped tab). Null
   when there is nothing to select: no tabs, one, the view already on that tab, or a desktop, where the
   tabs are the view's own bar and not stops in the row. A tap on the pill still opens the remembered tab. */
function tabRowEnter(modes, d, phone){
  if (!phone || !modes || modes.ids.length < 2) return null;
  const want = d > 0 ? modes.ids[0] : modes.ids[modes.ids.length - 1];
  const cur = modes.ids.includes(modes.cur) ? modes.cur : modes.ids[0];
  return want === cur ? null : want;
}

/* Where the row scrolls so the pressed pill shows, `pad` px clear of the edge: left alone when it
   already shows; else just far enough. A pill wider than the row (opened into its tabs) shows its start. */
function tabRowScroll(left, width, scroll, view, pad){
  if (width + 2 * pad >= view || left - pad < scroll) return Math.max(0, left - pad);
  if (left + width + pad > scroll + view) return left + width + pad - view;
  return scroll;
}

/* After a swipe the row aims at the pressed pill as tabRowScroll does, then, when the tab the swipe landed
   on (`seg`, null for a plain pill) is still past an edge there, just far enough on to show it whole
   (2026-10-06: News -> Recap's last tab left Accuracy 22px off a 360px row). {left, width} each, in the
   row's own coordinates. A tap keeps tabRowScroll alone. */
function tabRowAim(pill, seg, scroll, view, pad){
  const to = tabRowScroll(pill.left, pill.width, scroll, view, pad);
  if (!seg || seg.left >= to && seg.left + seg.width <= to + view) return to;
  return tabRowScroll(seg.left, seg.width, to, view, pad);
}
