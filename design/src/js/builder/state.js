let MKT_POS = "ALL", MKT_KIND = "ALL", MKT_WIN = "ALL", MKT_MINE = false, DFS_POS = "ALL";
/* The pool can run to 700+ rows (a full Yahoo slate), so it's paginated — nobody, least of all on
   mobile, wants to scroll past hundreds of rows to reach the lineup or the optimizer. */
let DFS_PAGE = 1;
const DFS_PAGE_SIZE = 25;
/* The full props board can run to 900+ lines across every market and player, so it's paginated too. */
let MKT_PAGE = 1;
const MKT_PAGE_SIZE = 25;
/* Card order. "edge" ranks by what the price leaves on the table; "model" by the model's chance
   alone ("who scores?" on a touchdown list). The choice sticks until changed: a market chip
   never moves it. Unmodelled rows go last either way, mine first among them. */
let MKT_SORT = "conf";
const SORTS = {
  edge:  (a,b) => (typeof b.edge === "number") - (typeof a.edge === "number") || (b.edge||0) - (a.edge||0) || (b.mine||0) - (a.mine||0),
  model: (a,b) => (typeof b.model === "number") - (typeof a.model === "number") || (b.model||0) - (a.model||0) || (b.mine||0) - (a.mine||0),
  conf:  (a,b) => (udPick(b)?udPick(b).conf:-1) - (udPick(a)?udPick(a).conf:-1) || (b.mine||0) - (a.mine||0),
  // Slip-ready first: the rows a gallery card could be built from (every gate in legOKInBook,
  // any scope), then the book's own metric within each half. Answers "why is the top of the
  // confidence sort not on the card" by putting the card's candidates on top.
  ready: (a,b) => legOKInBook(b, "mix", PARLAY_BOOK) - legOKInBook(a, "mix", PARLAY_BOOK)
    || (PARLAY_BOOK === "underdog" ? SORTS.conf(a,b) : SORTS.edge(a,b)),
};

