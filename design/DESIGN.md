# Team Watch — design mock

Four surfaces, one console:

| # | Surface | Question it answers |
|---|---|---|
| 01 | My teams | What moved on my two rosters, and what do I do about it |
| 02 | The pool | Which player anywhere in the league is taking over a role |
| 03 | Parlay | Which of the model's best slips do I take, or what do I build myself |
| 04 | DFS | Which precomputed lineup do I load, or what do I build myself |

Build after editing anything under `design/src/`:

```
python design/build.py
```

## Live data in, live signals on top

`build.py` reads the real roster files from `ff-jarvis` and injects them:

| Source | Injected as | Carries |
|---|---|---|
| `data/espn_rosters.json` | `LIVE_ESPN` | name, pos, team, **lineup slot**, injury status |
| `data/league_rosters.json` | `LIVE_YAHOO` | name, pos, team — **no slot, no status** |

The Yahoo file comes from a website scrape, so lineup slots are inferred by filling the league
lineup in roster order. The board says so in a caption rather than passing the guess off as fact.

A roster row's Trend, Rank and News cells come from `data/signals.js` (since 2026-09-16; the
hand-typed `SIGNALS` map is gone). Nothing is typed by hand:

| Cell | Source | Shows from |
|---|---|---|
| Trend line | `watch.json` `series`, weekly snap % (`LIVE_SIGNALS`) | week 2: a line needs two weeks |
| Trend delta | `market.stock` `d_pts`, points vs his previous game's price | a priced prop market |
| Rank | `market.stock` `rank`/`d_rank`, position rank among priced players | a priced prop market |
| Verdict tag | `watch.json` `verdict`, hidden for NEW and hold | week 2 |
| News | scanner stories whose headline starts with his name, team agreeing, last 72 h | now |

None of the three sources is backtested. The verdict word is watch's own; the page adds none.

## Waivers (sub-tab of My Teams, 2026-09-16)

A Roster | Waivers toggle under the team name, not a sixth nav tab: waivers are per league like
the roster, so the league switch carries over, and the phone's bottom bar keeps five thumb-sized
columns. The data is ff-jarvis's `model.season.waiver_packet`, built daily by the refresh
(`LIVE_WAIVER`, `design/waiver.py`), and the tab only formats it.

**Cards since 2026-09-22** (superseding the rows, Suggested moves and drops list). One card per
candidate across both leagues, tiered by ff-jarvis: Must claim (all), Worth a claim (top 5),
Watch (top 5), Speculative and Stash folded shut. On a Tuesday (local) an empty hash opens
Waivers and Waivers leads My teams.

| Part | Shows | Source field |
|---|---|---|
| Hero line | clear time, must-claims open in this league, FAAB left | `leagues_meta[league]` |
| Headline | the best swap across his open leagues, else the need he fills | `leagues[*].verdict`, `need` |
| Summary | two sentences; a RULE mark when the LLM text failed its fact check | `summary.src` |
| Proof | 3 stats by position, rank that week, arrow vs the week before | the usage grid (`LIVE_USAGE`) |
| League rows | status, verdict, drop, margin, per league he is available in | `leagues[*]`, in `leagues_meta` order |

**v2 since 2026-09-23** (supersedes the cross-league cards and league rows above). The team
dropdown picks ONE league: tiers (`leagues[VIEW].tier`, else the row's `tier`), swap, drop, hero
and the Breaking rail are that league's; the others are one line on the card back.

| Part | Shows | Source |
|---|---|---|
| Card front | tier stamp, name, "Bench over X · drop Y", first summary sentence, 3 proof stats | packet, usage grid |
| Card back | each proof stat week by week (sparkline), full summary, news, other leagues, Full profile | usage grid, packet |
| Breaking rail | path > drop > status > adds (adds capped at 3), still stacked rows | `wire_watch` (`LIVE_WIRE`, `design/wire_watch.py`) |
| Mode | Tuesday (local): rail under the hero, 3 rows + Show all. Wed–Mon: rail leads, every row | `navWaiverDay()` |

Motion (off under reduced motion): the deal on the first open of a day (`tw.waiver.dealt`), a
stamp slam on Must claim and a quieter mark on Worth during that deal, and rail rows newer than
the last visit (`tw.wire.seen`) lit once. The flip is a rotateY with both faces in one grid cell,
so the card never changes height; reduced motion swaps faces instantly.

A league `status` of `unknown` draws the card and says "Availability unknown", never FA. The
lane tag under a name (`leagues[VIEW].lane`: Beats a starter, Open work, Usage, Depth move,
Insurance, Out now) is that league's reason; a league that did not list him shows none. Section
counts are plain ("Must claim · 2"), never zero-padded. The floating chat button covers the
page's right edge on a phone, so the rail rows and card footers keep `--fab-clear` free on their
right, measured from both boxes at render and on resize.

## The pool

Ranked on usage, never points. The anchor is a quadrant scatter: **x = change in snap/target
share, y = points still owed (luck, sign flipped).** The four corners are the whole product.
Since 2026-09-16 it reads the usual way, best top-right to worst bottom-left; plotting luck itself
put the sells on top and the cloud read as an upside-down V.

| Quadrant | Meaning | Action |
|---|---|---|
| upper right (green wash) | role growing, points not caught up | **buy low** |
| lower right | role and box score agree | confirmed, hold |
| upper left | role shrinking, points were unlucky anyway | fade |
| lower left (red wash) | points ran ahead of a shrinking role | sell high |

**Live since 2026-09-17** (`LIVE_POOL`, `design/pool.py`): watch.json's league-wide pool, every
back and quarterback with 8+ opportunities and every receiver with 4+ (171 players in week 1; one
floor of 8 kept only 22 WRs and 5 TEs). The share a row shows is the one watch's verdict reads (carries for a
back, targets for a receiver or tight end, snaps for a quarterback), ranked by that share with
quarterbacks last. "Free in" comes from watch's `rostered_by`: Mine, Both, ESPN, Yahoo, or a dash.
Share moves need two weeks, so through week 1 the chart says when it fills in rather than plotting
nothing. The 16 hand-typed rows in `data/pool.js` are only the fallback when watch.json is missing.

Dot size is snaps. A lime ring means he is on one of my rosters. Table below repeats it as rows
so the numbers are readable, paginated 10 at a time (2026-09-09) once real usage data makes the
list run long — the sample data's 16 fits on two pages.

On mobile (2026-09-09) the chart draws to a taller, narrower geometry sized close to 1:1 with the
actual screen instead of the desktop box scaled down to ~35% (which is what forced a horizontal
swipe to read anything). Per-dot name labels drop at that size — 16 of them collide regardless of
box shape, and the table right below already names every player — dots stay tappable into the
same drawer. Quadrant corner labels shortened to one word each (`CONFIRMED`, `SELL HIGH`, `BUY
LOW`, `FADING`) at both sizes, the explanatory phrase folded into the intro line instead.

## Parlay and DFS

Split into their own top-level tabs (2026-09-09) so the cart, not the 900-row props pool, is the
first thing a mobile reader reaches. Each tab: a collapsed-by-default "how this works" banner,
a gallery of the model's precomputed picks, then the cart-style custom builder, then the pool.

**Parlay**: a Book toggle (2026-09-09, DraftKings/Underdog, same pattern as DFS's site toggle)
switches the gallery, pool rows, and cart between two different products, not just a price
column. **DraftKings**: one gallery card per kickoff window (never two calendar dates in one card
— `design/build.py`'s `assign_windows` splits a time-of-day bucket like "evening" into
per-weekday windows, e.g. "Thursday Night" / "Monday Night", when the week's games land on more
than one date) crossed with yards / TDs / mix scope, ranked by model edge, the best one badged.
Model %/edge and every book's price live behind each line's chevron, not on the row.
**Underdog**: pick'em, one stat and one tap — the row leads with the model's higher/lower call
and its confidence (that IS the primary info here, not noise the way DK's model%/edge is; Higher
green, Lower red, the same up/down tokens as everywhere else), a same set of gallery cards built
from Underdog-eligible legs (conf ≥ 58%) instead of DK edge, ranked by confidence. Underdog
carries no anytime-TD price in this feed at all (checked 2026-09-10: 0 of 430 TD rows), so a TD
pick derives from the model's own chance of scoring instead — tagged `MODEL` on the row and in
the cart's footer caption, never shown as an Underdog price. Switching the toggle clears the cart
(a leg's meaning doesn't carry across books). Either way: load a card into the cart or tap lines
by hand; the cart warns when two legs
share a game (correlated legs are one bet, not two).

**DFS**: a swipeable rail of precomputed lineups per strategy (an equal-width segmented control,
greedy = max points, non-chalk = for GPPs) each with a "Load into my lineup" button, then nine
cart slots against a cap, salary bar, summed ownership, and a styled empty slot — a second toggle
picks Yahoo ($200 cap, live from ff-jarvis's `data/dfs_pool.json`) or DraftKings ($50,000 cap,
sample). The cart is configurable (2026-09-09): tap a vacant slot to fill it or a filled one to
swap it, tap a pool row to add/assign (auto-picks the first open eligible slot when none is
selected), an "✕" removes. A wrong-position pick is rejected inline (`Josh is RB, not QB`) rather
than silently doing nothing.

The topbar's live/sample badge (2026-09-09) reflects what's actually loaded per tab instead of a
single static "Sample data" string: green "Props live" / "Pool live" when Parlay's BettingPros
props or DFS's Yahoo salary export are in, the amber sample warning otherwise. My Teams goes
green when `LIVE_SIGNALS` is in (2026-09-16); the Waivers sub-tab is live from the same day.

## Motion (2026-09-16)

Motion marks a change of context, never moves what is being read. All of it lives in
`css/chrome/motion.css` and `js/chrome/motion.js`, and all of it is off under reduced motion.

| Moment | Motion |
|---|---|
| Team switch | a football crosses the hero; the team name is one line, fitted, so the hero height holds |
| Tab or sub-tab switch | the `//` in TEAM//WATCH crosses into an X and back |
| Waivers, news list | rows arrive one at a time |
| Profile modal charts | every chart draws itself along the axis that carries its number (below) |

## The profile modal (rebuilt 2026-09-22)

Eleven blocks at one weight is a wall. Three tiers, and the order is the answer to "what do I do
with him this week":

| Tier | What | Where |
|---|---|---|
| **Lede** | three numbers at hero size, full width | `js/surface/profile/lede.js` |
| **Sheet** | the radar and the card under it | `sheet.js`, `statcard.js` |
| **Panes** | Usage / Matchup / Log / Bio, one at a time | `tabs.js` |

The lede is **projected · matchup · lead usage stat**, and it is numbers, never a word: the market
rule below bans a verdict, so choosing three numbers and sizing them is how this page answers a
start-or-sit question. A cell whose source has nothing for that player is left out rather than
dashed — two numbers read as two numbers, a dash reads as a number that failed. The one exception
is a bye, where the cell *is* the week and "none" is the honest answer.

The panes use `.modes-sub`, the app's sub-tab component (nav.css names the rule: a third caller is
a component; this is the fourth). Only the open pane is in the DOM — every chart animates on
insert, so a hidden pane would finish its entrance unseen. A pane that renders nothing draws no
tab at all: a back has no target depth, a passer no red zone, a player with no pedigree no Bio.
The bar is sticky inside the scrolling body, because the Matchup pane runs 1,200px and the way
back to the other two should not be a scroll to the top. `PF_TAB` survives an open, so reading two
players against each other opens the same pane twice.

The **Details disclosure is gone.** It was a second level of hiding underneath a first level
nobody had got through, and its five blocks are now ordinary sections inside the panes.

**The modal is a fixed box**, `min(860px, 90vh)`. Measured across every roster player and every
pane, it had been resizing between 277px and 874px tall — on every player, on every tab switch,
and by up to 63px from tapping a different stat on the radar. 860 is the 90th percentile of real
content: most players fill it, the Matchup pane scrolls, and the card's height is reserved by
measuring all six variants in the browser at open rather than guessing a wrap-dependent number in
CSS.

**Numbers have one home each.** The rank used to be in the lede, on the radar's own axis label,
*and* in the card under the radar — three copies of one number on one screen. The card now carries
the value, its elite bar and its weekly line; its header carries that axis's own "of N" and
follows the reader's pick, since a receiver ranks among everyone with a target on one stat and
only among those with routes on the next.

**Every block states its own window, and they do not share one.** `routes_run.json` is whatever
week heatradar last published — one at a time — so Route%, TPRR, YPRR and 1D/RR can be a one-week
number sitting on the same chart as WOPR and RZ Tgts, which are season to date. Section heads
carry `2 wk`; the stat card carries `of 120 · wk 1–2` or `of 101 · wk 1`. A number whose window is
not stated cannot be checked, which is how a correct red-zone figure came to look wrong.

### Motion

Every chart draws itself along the axis that carries its meaning, so the motion is the
measurement, not an entrance. The radar's shape inflates from the centre, because the radius is
the rank; the depth columns grow from their baseline, because the height is the share; the
red-zone bar fills left to right in the order its key names; the matchup strip lands the lit cell
last, after the scale it sits on. All of it is CSS keyframes in `surface/profile/sheet.css` and
all of it collapses to the finished state under reduced motion.

### The chart itself

It is a dial, not a default radar. The grid rings are **circles**: concentric hexagons crossed by
spokes resolve into a drawn cube, with the tinted shape as a plane leaning in it, and a radius
that means a percentile is round anyway. The disc runs dark at the hub to lighter at the rim, so
"1st at the rim" is a property of the surface rather than a caption. The fill is a radial gradient
dense at the hub and thin at the rim, and the stroke carries a glow: the shape is the only lit
thing on the dial, which is the one distinction this chart has to make.

| Was | Is | Why |
|---|---|---|
| Six full spokes | ticks at the rim | a spoke's only job is saying where an axis is, and six of them crossed the translucent shape and showed through it, which is what made the fill look muddy |
| Elite bar: a dash on the axis | a **dashed arc across the axis's sector**, tagged `ELITE` | six dashes in open space read as scratches on the glass; a threshold is a contour, so the shape now visibly crosses outside it |
| A legend under the chart | the word on the arc | `1st at the rim · dashed arc = elite` was a code explained in a caption, which the reader has to carry back to the picture |
| Label 13.5px, rank 15px | label 12px quiet, rank 18px bright | twelve near-equal fragments of text; at a four-step gap the eye takes the six numbers first |
| Rank edge-aligned under its label | centred, measured with `getBBox` at open | a flank label anchors outward, so the rank inherited that anchor and hung off the end of the longer words |
| Under 3 measured axes: a 2-point `<polygon>` | no polygon, real vertices, and a count | two points render as a bare line, which reads as a broken chart rather than as a player heatradar has not covered yet |

### On a phone

The left column becomes `display:contents` and the parts reorder: **sheet, panes, then who he
is.** Side by side the sheet and the panes are read together; stacked, whatever comes second is a
scroll away, and the pedigree is the one part that answers nothing about Sunday. The head is 24px
over two lines rather than 34px over three — it is fixed above the scrolling body, so its height
is paid on every screen of the scroll, and at 34px it took a fifth of a 780px phone to repeat the
row the reader just tapped. The modal goes edge to edge below 430px (`100vw`/`100dvh`); at
96vw/92vh it left a sliver of the page showing on all four sides, which read as a window that
missed its target.

Measured on the WR fixture, 360×780 phone and 1400px desktop:

| | Before | After |
|---|---|---|
| Phone, first screen (px of chrome-free content) | 551 | 682 |
| Phone, total scroll to the end of the default view | 1,421 | 1,088 |
| Desktop, the default view | 856 in a 747 window | no scroll at 950px viewport and up |
| Dial diameter, desktop | 191 | 298 |
| Modal box height, across every player and pane | 277–874, resizing | 855, fixed |

The weekly log is built for eighteen weeks: a column group with nothing in it is never drawn (a
back had two columns of passing zeros), the head is sticky, the season total is a foot row, and
on a phone each week becomes a block of labelled chips rather than a sideways drag. Verified
against a fabricated 18-week season at 360px and 1400px — `tableScrolls: false` at both.

## News severity (2026-09-16)

FantasyPros tags almost no story, so `design/news.py` reads each headline into a `kind`: **out**
(red), **injury** (amber: questionable, a missed practice, a named hamstring/concussion-class
injury), **practice** (routine: limited, full, rest day, cleared), **move**, **other**. The kind leads
every row as an icon and a word, and the filters are the kinds. "How this works" on Parlay and DFS
is a small button in the hero that opens the drawer.

## Direction

Signal Desk — a dark trading-terminal console.

| Token | Meaning |
|---|---|
| lime `#c8ff2e` | active, starter, buy-low, brand |
| green `#37e08b` | trending up, confirmed |
| red `#ff5a52` | trending down, sell |
| amber `#ffb020` | caution, stale, correlated legs |
| violet / red marks | Yahoo / ESPN league identity only |

Positions are typographic, never coloured, with one exception decided 2026-09-21: the profile
modal's stat sheet (radar, its chips, the stat card) is tinted by position (`--pos-qb/rb/wr/te`),
so a run of profiles reads QB/RB/WR/TE at a glance. Rows, cells and badges stay typographic.
Type: Bricolage Grotesque (display), Archivo (UI),
JetBrains Mono (all numerals).

## Theme rules

`design/lint_css.py` fails the build on any of these (`python design/lint_css.py`):

- `hex-outside-tokens` — a colour literal anywhere but `base/tokens.css`.
- `rgba-token-triple` — `rgba(r,g,b,…)` spelling out a token's own channels by hand.
- `token-triple-agrees` — a token's `--x-rgb` triple must match its `--x` hex, and a hex token
  without a triple is an error too.
- `font-family-literal` — a `font-family` value that isn't a `var()`.
- `font-size-literal` — a `font-size` that isn't a step of the type scale (`--t-1` 12px through
  `--t-7` 40px, plus the hero's two ghost sizes) in `base/base.css`. Added 2026-09-21, when 217
  literals from 9px to 38px moved onto the scale in one pass; 12px is the floor.
- `breakpoint` — a `@media` width outside the four the page uses (1100/960/760/430). 1100 is
  Waivers' wide layout only (2026-09-23): the Breaking rail as a sticky right column. The
  Waivers cards answer to their own column's width instead, through a container query.
- `inline-colour-in-js` — a colour literal inside a `style=""` in the JS or the shell. Styling
  belongs in a class; the JS names the class.
- `duplicate-selector` — the same selector defined in two non-responsive parts. Either the
  override is deliberate and `src/css/_overrides.txt` says so, or the rule lives in one part.

Every colour token in `base/tokens.css` carries a channel triple next to it, e.g.
`--lime:#c8ff2e; --lime-rgb:200 255 46;`. `rgba()` needs bare channels, so a translucent lime
is `rgb(var(--lime-rgb) / .4)`, never `rgba(200,255,46,.4)`. A new colour means a new token plus
its triple in `base/tokens.css` — never a literal dropped into a component file.

**Spacing is px-literal, on purpose (decided 2026-09-10).** A spacing scale was considered and
rejected on the numbers: 397 px literals across 375 spacing declarations, and every integer from
1 to 16 is in regular use (14px appears 38 times, 7px 21, 9px 24, 11px 18). No 4px or 8px scale
covers more than 40% of them; moving the rest onto a scale is a visual redesign of a dense data
console, not a refactor. If a scale is ever wanted it is its own project with its own golden
diff. Colour, type and motion are tokens; spacing is not.

## States already styled

In-place variants: filtered-list and empty-cart empty states, the scatter's no-data axes,
`No data` trend chips, unranked players, and an empty DFS slot. The standalone "Component
states" showcase (empty/loading/error/stale reference boxes) was removed 2026-09-09 — it was
permanent staged content on the live page, not a real state, and read as dead/leftover UI to a
visitor. Loading/error/stale are still designed (see `.pill.warn`, `marketHead`'s no-fetch
pill), just not demonstrated in a standing block.

## Verified 2026-09-09

Desktop 1400px and phone 390px, no horizontal overflow on any of the four surfaces, no console
errors. Gallery/rail interactions checked headless: loading a gallery card or a strategy lineup
into the cart, expanding a leg's chevron without toggling it into the slip, tapping inside the
expanded detail without toggling it, the explainer's open state surviving a pagination re-render.
Rosters and team names are live. Trend, rank, news, pool, props and DFS content are sample.
