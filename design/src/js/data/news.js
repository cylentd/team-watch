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
   tab. Falls back to TICKER, reshaped to the same fields, when that file isn't there at all. */
const SAMPLE_NEWS = TICKER.map((t, i) => ({
  id: i, title: `${t.b} ${t.s}`, desc: null, impact: null, team: null,
  categories: [], link: t.url || null, when: null, kind: "news",
}));
const NEWS_ITEMS = (LIVE_NEWS && LIVE_NEWS.items) || SAMPLE_NEWS;

/* What a story means for a lineup: `kind` comes from design/news.py, read off the story's own
   words. Most severe first; that is also the filter order. Color carries severity only: red out,
   amber caution, everything else neutral with its own icon. */
const newsIcon = body => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${body}</svg>`;
const NEWS_KINDS = [
  {k:"out",      label: () => t("news.kind.out"),      icon: newsIcon(`<circle cx="12" cy="12" r="9"/><line x1="5.7" y1="5.7" x2="18.3" y2="18.3"/>`)},
  {k:"injury",   label: () => t("news.kind.injury"),   icon: newsIcon(`<path d="M12 3.5 2.8 19.5h18.4z"/><line x1="12" y1="10" x2="12" y2="14"/><circle cx="12" cy="16.9" r=".4" fill="currentColor"/>`)},
  {k:"practice", label: () => t("news.kind.practice"), icon: newsIcon(`<rect x="5" y="4.5" width="14" height="16" rx="1.5"/><path d="M9 3.5h6v3H9z"/><path d="m9 13 2 2 4-4"/>`)},
  {k:"move",     label: () => t("news.kind.move"),     icon: newsIcon(`<path d="M4 8h14l-3.5-3.5"/><path d="M20 16H6l3.5 3.5"/>`)},
  {k:"news",     label: () => t("news.kind.news"),     icon: newsIcon(`<path d="M5 5h14v14H5z"/><line x1="8.5" y1="9.5" x2="15.5" y2="9.5"/><line x1="8.5" y1="13" x2="15.5" y2="13"/><line x1="8.5" y1="16.5" x2="12.5" y2="16.5"/>`)},
];
const NEWS_KIND = Object.fromEntries(NEWS_KINDS.map(k => [k.k, k]));
const newsKind = it => NEWS_KIND[it.kind] ? it.kind : "news";
let NEWS_CAT = "all";
