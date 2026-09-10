/* ------------------------------------------------------------------
   BUILDER — parlay slip and DFS lineup, both fed by the pool.
------------------------------------------------------------------ */
/* The market is every priced player in the league, not my roster. `mine` only decides whether a
   row gets a lime edge, and whether the "my players" filter keeps it. */
const MKT = {RUSH:t("market.name.RUSH"), REC:t("market.name.REC"), RECS:t("market.name.RECS"),
             PASS:t("market.name.PASS"), TD:t("market.name.TD")};
const MKT_SHORT = {RUSH:t("market.short.RUSH"), REC:t("market.short.REC"), RECS:t("market.short.RECS"),
                   PASS:t("market.short.PASS"), TD:t("market.short.TD")};
/* Sample rows: what the card looked like before a market existed. They render only when the
   build found no BettingPros pull; `model` and `edge` on them are invented numbers. */
const PROPS_SAMPLE = [
  {n:"Bhayshul Tuten",    slug:"bhayshul-tuten",   pos:"RB", mkt:"RUSH", line:44.5, game:"JAX @ TEN", book:"-112", model:64, edge:+10.9},
  {n:"De'Von Achane",     slug:"devon-achane",     pos:"RB", mkt:"RUSH", line:59.5, game:"MIA @ IND", book:"-115", model:62, edge:+8.5, mine:1},
  {n:"Amon-Ra St. Brown", slug:"amonra-st-brown",  pos:"WR", mkt:"RECS", line:5.5,  game:"DET vs GB", book:"-130", model:64, edge:+7.5, mine:1},
  {n:"Denzel Boston",     slug:"denzel-boston",    pos:"WR", mkt:"REC",  line:38.5, game:"LV @ NE",   book:"-110", model:60, edge:+7.2},
  {n:"Brenton Strange",   slug:"brenton-strange",  pos:"TE", mkt:"RECS", line:3.5,  game:"JAX @ TEN", book:"+105", model:56, edge:+6.9},
  {n:"Jared Goff",        slug:"jared-goff",       pos:"QB", mkt:"PASS", line:249.5,game:"DET vs GB", book:"-105", model:57, edge:+5.8, mine:1},
  {n:"Jalen Coker",       slug:"jalen-coker",      pos:"WR", mkt:"REC",  line:41.5, game:"CAR @ ATL", book:"-114", model:58, edge:+5.1},
  {n:"Isaiah Likely",     slug:"isaiah-likely",    pos:"TE", mkt:"TD",   line:null, game:"BAL vs CLE",book:"+165", model:44, edge:+4.9},
  {n:"Chase Brown",       slug:"chase-brown",      pos:"RB", mkt:"TD",   line:null, game:"CIN @ CLE", book:"+140", model:46, edge:+4.3},
  {n:"Blake Corum",       slug:"blake-corum",      pos:"RB", mkt:"RUSH", line:31.5, game:"LA vs SEA", book:"-108", model:56, edge:+4.1},
  {n:"George Kittle",     slug:"george-kittle",    pos:"TE", mkt:"TD",   line:null, game:"SF vs ARI", book:"+185", model:39, edge:+3.9, mine:1},
  {n:"Derrick Henry",     slug:"derrick-henry",    pos:"RB", mkt:"RUSH", line:82.5, game:"BAL vs CLE",book:"-115", model:56, edge:+3.4, mine:1},
  {n:"Braelon Allen",     slug:"braelon-allen",    pos:"RB", mkt:"RUSH", line:36.5, game:"NYJ @ BUF", book:"-110", model:55, edge:+2.8},
  {n:"Carnell Tate",      slug:"carnell-tate",     pos:"WR", mkt:"RECS", line:3.5,  game:"CHI vs MIN",book:"+120", model:50, edge:+2.4},
  {n:"Dylan Sampson",     slug:"dylan-sampson",    pos:"RB", mkt:"TD",   line:null, game:"CIN @ CLE", book:"+210", model:35, edge:+2.1},
  {n:"Amon-Ra St. Brown", slug:"amonra-st-brown",  pos:"WR", mkt:"REC",  line:74.5, game:"DET vs GB", book:"-112", model:54, edge:+1.9, mine:1},
  {n:"Tetairoa McMillan", slug:"tetairoa-mcmillan",pos:"WR", mkt:"REC",  line:58.5, game:"CAR @ ATL", book:"-110", model:53, edge:+1.4, mine:1},
  {n:"Alec Pierce",       slug:"alec-pierce",      pos:"WR", mkt:"REC",  line:47.5, game:"IND vs MIA",book:"-110", model:48, edge:-1.8},
  {n:"Adonai Mitchell",   slug:"adonai-mitchell",  pos:"WR", mkt:"RECS", line:4.5,  game:"IND vs MIA",book:"-105", model:47, edge:-2.6},
  {n:"Tee Higgins",       slug:"tee-higgins",      pos:"WR", mkt:"REC",  line:69.5, game:"CIN @ CLE", book:"-110", model:49, edge:-3.2, mine:1},
];
/* The live market: `design/build.py` folds `market.props_bp` (BettingPros, DraftKings + Underdog)
   into one row per player and market, newest line per book, `mine` joined against both rosters.
   A row has `books` = {DraftKings:{line,over,under}, Underdog:{...}} and `ref` = BettingPros'
   consensus, and no `model`/`edge` until the per-stat projection in ff-jarvis lands: the card
   shows the book-implied probability and says the model is pending, the slip prices in book
   terms only. */
const LIVE_MARKET = (typeof LIVE_PROPS !== "undefined" && LIVE_PROPS && LIVE_PROPS.props.length) ? LIVE_PROPS : null;
const PROPS = LIVE_MARKET ? LIVE_MARKET.props : PROPS_SAMPLE;
const BOOKS = LIVE_MARKET ? LIVE_MARKET.books : ["DraftKings","FanDuel","BetMGM","Caesars","Pinnacle"];

