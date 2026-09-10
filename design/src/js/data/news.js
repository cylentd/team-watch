/* url is the article link. The skill supplies it once wired; sample rows fall back to a
   news search for the same query so every tick still opens something real. */
const TICKER = [
  {t:"up",   b:"De'Von Achane", s:"snap share up to 71% in the joint practice report", src:"BEAT · 2h"},
  {t:"down", b:"Rashee Rice", s:"limited Wednesday, listed questionable for week 1", src:"WIRE · 4h"},
  {t:"flat", b:"Josh Jacobs", s:"exempt-list hearing scheduled for Sept 10", src:"LEAGUE · 1d"},
  {t:"up",   b:"Jordan Mason", s:"first-team reps continue while the RB1 sits", src:"BEAT · 6h"},
  {t:"down", b:"Jerry Jeudy", s:"third on the depth chart after the preseason finale", src:"WIRE · 9h"},
  {t:"up",   b:"Xavier Worthy", s:"red-zone target share leads the room this camp", src:"BEAT · 11h"},
];

/* ff-jarvis's own scanner (data/breaking_news.json), watched via LIVE_NEWS the same two-tier
   feed/file pattern as every other live source -- feeds both the My Teams ticker and the News
   tab, so a real breaking story shows up in both places, not just one. Falls back to TICKER,
   reshaped to the same fields, when that file isn't there at all. */
const SAMPLE_NEWS = TICKER.map((t, i) => ({
  id: i, title: `${t.b} ${t.s}`, desc: null, impact: null, team: null,
  categories: [], link: t.url || null, when: null,
}));
const NEWS_ITEMS = (LIVE_NEWS && LIVE_NEWS.items) || SAMPLE_NEWS;
const CAT_CLASS = {Breaking:"breaking", Injury:"injury", News:"news", Commentary:"commentary"};
const NEWS_FILTERS = ["All", "Breaking", "Injury", "News", "Commentary"];
let NEWS_CAT = "All";
/* The row itself carries the severity, not just its tags -- a left stripe you catch scrolling
   past, before you've read a single tag. Breaking outranks Injury when a story is both. */
const newsSeverity = it => (it.categories || []).includes("Breaking") ? "breaking"
  : (it.categories || []).includes("Injury") ? "injury" : "";

const WIRE = [
  {out:{n:"Tyrone Tracy Jr.",slug:"tyrone-tracy",m:"RB · NYG · BN",pos:"RB47",d:-7.2},
   in_:{n:"Chase Brown",slug:"chase-brown",m:"RB · CIN · 41% rostered",pos:"RB22",d:+12.6},
   team:"ESPN", gain:"+18.4 proj/wk", faab:"12% FAAB"},
  {out:{n:"Deebo Samuel Sr.",slug:"deebo-samuel",m:"WR · WAS · BN",pos:"WR46",d:-9.7},
   in_:{n:"Jalen Coker",slug:"jalen-coker",m:"WR · CAR · 28% rostered",pos:"WR39",d:+8.1},
   team:"YAHOO", gain:"+6.2 proj/wk", faab:"5% FAAB"},
];

