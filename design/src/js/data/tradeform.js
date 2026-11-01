/* The strip on Trade history's Best and Worst cards (2026-11-01, David: "People vs trades"): a manager's closed
   trades, one mark each, oldest first. Won, lost or tied on held weeks, the basis of the W-L printed beside it
   (ff-jarvis by_manager); a trade's own verdict is the tree, which the heists show. Open trades are out of the
   record, so they are out of the strip. Checked on both leagues' real files 2026-11-01: 24 managers, no mismatch. */

/* The fewest columns: a short strip keeps a mark's size, rather than swelling to fill the card. */
const TR_FORM_MIN_COLS = 6;
/* The most marks on one line: at 12 a mark is ~20px at 360px and ~14px in a desktop's top-row card. */
const TR_FORM_LINE = 12;
/* The most columns that still take the bigger letter: 8 leaves a mark ~25px wide in a desktop's top-row card. */
const TR_FORM_BIG = 8;

function trFormOf(trades, key){
  return trades.filter(x => !x.open && (x.win.m === key || x.lose.m === key))
    .sort((a, b) => a.season - b.season || a.week - b.week)
    .map(x => ({id: x.id, r: !x.held.margin ? "t" : x.held.win === key ? "w" : "l"}));
}

function trFormCounts(marks){
  const n = r => marks.filter(m => m.r === r).length;
  return {w: n("w"), l: n("l"), t: n("t")};
}

/* One line up to TR_FORM_LINE, then two lines of even length. */
const trFormCols = n => n > TR_FORM_LINE ? Math.ceil(n / 2) : Math.max(n, TR_FORM_MIN_COLS);
const trFormBig = n => trFormCols(n) <= TR_FORM_BIG;
