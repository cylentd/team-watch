/* DraftKings pool. Salaries are the whole contest, not my league. Sample only — no live
   DraftKings export is wired yet (see DFSPOOL_YAHOO below for the Yahoo side). */
const DFSPOOL_DK = [
  {n:"De'Von Achane",     slug:"devon-achane",     pos:"RB", team:"MIA", sal:8400, proj:21.1, own:32, mine:1},
  {n:"Amon-Ra St. Brown", slug:"amonra-st-brown",  pos:"WR", team:"DET", sal:8100, proj:19.8, own:27, mine:1},
  {n:"Derrick Henry",     slug:"derrick-henry",    pos:"RB", team:"BAL", sal:7900, proj:18.9, own:24, mine:1},
  {n:"Tee Higgins",       slug:"tee-higgins",      pos:"WR", team:"CIN", sal:6800, proj:15.4, own:16, mine:1},
  {n:"Jared Goff",        slug:"jared-goff",       pos:"QB", team:"DET", sal:6200, proj:18.4, own:14, mine:1},
  {n:"Chase Brown",       slug:"chase-brown",      pos:"RB", team:"CIN", sal:5900, proj:14.2, own:19},
  {n:"Tetairoa McMillan", slug:"tetairoa-mcmillan",pos:"WR", team:"CAR", sal:5600, proj:13.1, own:12, mine:1},
  {n:"Brock Purdy",       slug:"brock-purdy",      pos:"QB", team:"SF",  sal:5400, proj:17.2, own:9,  mine:1},
  {n:"George Kittle",     slug:"george-kittle",    pos:"TE", team:"SF",  sal:5200, proj:13.6, own:21, mine:1},
  {n:"Brenton Strange",   slug:"brenton-strange",  pos:"TE", team:"JAX", sal:4400, proj:11.8, own:8},
  {n:"Isaiah Likely",     slug:"isaiah-likely",    pos:"TE", team:"BAL", sal:4200, proj:11.2, own:11},
  {n:"Braelon Allen",     slug:"braelon-allen",    pos:"RB", team:"NYJ", sal:4100, proj:10.4, own:14},
  {n:"Bhayshul Tuten",    slug:"bhayshul-tuten",   pos:"RB", team:"JAX", sal:3900, proj:11.9, own:7},
  {n:"Jalen Coker",       slug:"jalen-coker",      pos:"WR", team:"CAR", sal:3600, proj:9.8,  own:6},
  {n:"Blake Corum",       slug:"blake-corum",      pos:"RB", team:"LA",  sal:3500, proj:9.1,  own:10},
  {n:"Carnell Tate",      slug:"carnell-tate",     pos:"WR", team:"CHI", sal:3300, proj:9.4,  own:5},
  {n:"Denzel Boston",     slug:"denzel-boston",    pos:"WR", team:"LV",  sal:3100, proj:8.6,  own:4},
  {n:"Dylan Sampson",     slug:"dylan-sampson",    pos:"RB", team:"CLE", sal:2900, proj:7.9,  own:6},
  {n:"Seahawks",          slug:null, abbr:"SEA",   pos:"DST",team:"SEA", sal:2700, proj:7.4,  own:9},
];
/* Yahoo pool. `LIVE_DFS_YAHOO` comes from a contest's own "Export Player List" CSV
   (data/dfs_yahoo.csv, refetched by hand — Yahoo has no public API for this), injected by
   build.py. Yahoo's cap is $200, not DraftKings' $50,000, so salaries here are a different
   scale; `own` isn't in Yahoo's export, so live rows carry none. Sample below (DK scale / 42,
   roughly matching Yahoo's $10-$40 range) is the fallback. */
const LIVE_YAHOO_DFS = (typeof LIVE_DFS_YAHOO !== "undefined" && LIVE_DFS_YAHOO) ? LIVE_DFS_YAHOO : null;
const DFSPOOL_YAHOO_SAMPLE = DFSPOOL_DK.map(p => ({...p, sal: Math.round(p.sal/200)}));
const DFSPOOL_YAHOO = LIVE_YAHOO_DFS ? LIVE_YAHOO_DFS.players : DFSPOOL_YAHOO_SAMPLE;

