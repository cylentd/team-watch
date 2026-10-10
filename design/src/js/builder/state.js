let MKT_POS = "ALL", MKT_KIND = "ALL", MKT_MINE = false, MKT_BEST = false, DFS_POS = "ALL";   // kickoff is GAL_WIN (slips.js)
/* The pool can run to 700+ rows (a full Yahoo slate), so it's paginated — nobody, least of all on
   mobile, wants to scroll past hundreds of rows to reach the lineup or the optimizer. */
let DFS_PAGE = 1;
const DFS_PAGE_SIZE = 25;
/* The full props board can run to 900+ lines across every market and player, so it's paginated
   too, by player (BUILD_PAGE_SIZE, surface/parlay/lines.js). */
let MKT_PAGE = 1;
/* Card order. "edge" ranks by what the price leaves on the table; "model" by the model's chance
   alone ("who scores?" on a touchdown list). The choice sticks until changed: a market chip
   never moves it. Unmodelled rows go last either way, and a tie goes to the reader's own players
   (`mine`, mineSlugs(): the caller reads it once, not per comparison). */
let MKT_SORT = "conf";
// The sort a market chip or book switch starts on. Anytime TD on DraftKings: the book's chance (2026-10-09; was
// the model's, and edge before that). Underdog prices no TD, so its TD list stays on the model.
const kindSort = (kind, book) => kind === "TD" ? (book === "underdog" ? "model" : "book") : (book === "underdog" ? "conf" : "edge");
const NO_MINE = new Set();
const mineFirst = (a, b, mine) => lineMine(mine, b) - lineMine(mine, a);
const SORTS = {
  edge:  (a,b,mine=NO_MINE) => (typeof b.edge === "number") - (typeof a.edge === "number") || (b.edge||0) - (a.edge||0) || mineFirst(a, b, mine),
  model: (a,b,mine=NO_MINE) => (typeof b.model === "number") - (typeof a.model === "number") || (b.model||0) - (a.model||0) || mineFirst(a, b, mine),
  // Anytime TD legs on DraftKings order by the book's own chance (2026-10-09), the number the TD card prints.
  book:  (a,b,mine=NO_MINE) => (typeof overPrice(b) === "number") - (typeof overPrice(a) === "number")
    || (overPrice(b) == null ? 0 : amToProb(overPrice(b))) - (overPrice(a) == null ? 0 : amToProb(overPrice(a))) || mineFirst(a, b, mine),
  conf:  (a,b,mine=NO_MINE) => (udPick(b)?udPick(b).conf:-1) - (udPick(a)?udPick(a).conf:-1) || mineFirst(a, b, mine),
  // Slip-ready first: the rows a gallery card could be built from (every gate in legOKInBook,
  // any scope), then the book's own metric within each half. Answers "why is the top of the
  // confidence sort not on the card" by putting the card's candidates on top.
  ready: (a,b,mine=NO_MINE) => legOKInBook(b, "mix", PARLAY_BOOK) - legOKInBook(a, "mix", PARLAY_BOOK)
    || (PARLAY_BOOK === "underdog" ? SORTS.conf(a,b,mine) : SORTS.edge(a,b,mine)),
};

