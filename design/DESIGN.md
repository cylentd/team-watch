# Team Watch — design mock

Four surfaces, one console:

| # | Surface | Question it answers |
|---|---|---|
| 01 | My teams | What moved on my two rosters, and what do I do about it |
| 02 | The Board | Who leads each stat (Leaders), and who anywhere is taking over a role (Movers, the old Pool) |
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

A roster row's signals come from `data/signals.js` (since 2026-09-16; the hand-typed `SIGNALS`
map is gone). Nothing is typed by hand. Since 2026-09-25 the row draws only the first and the
projection at every width; the rest are read elsewhere:

| Signal | Source | Drawn where |
|---|---|---|
| Trend line | `watch.json` `series`, weekly snap % (`LIVE_SIGNALS`) | the row; last week's % is its title |
| Projection | `LIVE_PROJECTIONS` `pts` | the row's pill |
| Market delta, rank | `market.stock` `d_pts`, `rank`/`d_rank` | the profile's market block |
| Verdict word | `watch.json` `verdict` and `why`, hidden for NEW and hold | the profile head's second line, with "On 2 of your teams" (`profile/tags.js`) |
| News count | scanner stories naming him, last 72 h | the This week brief |

None of the three sources is backtested. The verdict word is watch's own; the page adds none.

## Phone layout (2026-09-24)

Storyboard: https://claude.ai/artifact/1S2qLgCTvmMxASpaUZK4q3. Every list row answers one
question: who, which way, one number.

| Part | Phone | Where |
|---|---|---|
| Nav | top: four groups as words, search + chat icons; view tabs underlined below; both hide on scroll down | `responsive/760.css`, `js/chrome/hidebar.js` |
| Brand row | hidden; shown only when a newer build makes DATA a reload control | `responsive/760.css` |
| Ground | slate `#111418`, surfaces one step up each; no pure black, no radial glow | `base/tokens.css` |
| Roster row | a lineup sheet since 2026-09-25 (storyboard https://claude.ai/artifact/AqRomyQsQfd7TjYRiJkmhd): starter = slot, 28px head, name over "RB · BAL @ DAL", trend line, projection in ink with a green/red arrow. Bench two to a row with short names ("D. Goedert"), no line. The whole Yahoo team fits 360×660. Desktop: the bench column sits beside the starters, 44px heads, full names | `surface/teams/roster.css`, `responsive/lists.css` |
| Roster cards | the Cards half of a Sheet / Cards switch (2026-09-25, remembered per phone). Tier = this week's projected rank at the position (`LIVE_PROJECTIONS` rank/of, ranked over every projected player in `design/projections.py`): Five tiers, one colour family each (2026-09-25; it had gold twice and silver beside grey): #1 Legendary holo (turning rainbow frame, glow, foil and glitter behind the photo, signed), #2-5 Epic violet (etched), #6-12 Rare gold, #13-24 Uncommon blue, the rest plain. A stamp in the photo's corner gives the rank ("#10") in the tier's colour. A player Sleeper lists as not playing (Out, IR, PUP, Sus, NA) shows OUT, no rank, no tier (`design/projections.py` OUT_INJURY). Tiers are earned by rank only. The autograph is a separate axis (2026-09-25, David's pick; it was every #1-5): a player who finished top 3 at his position in the last completed week (`LIVE_SIGNED`, `design/signed.py`; "completed" = every team scheduled that week has a game-log row) is signed on any tier, in gold foil ink (`--sig` script, never a real autograph) with a moving shine, a glow and a small holo seal; a roster with nobody in a top 3 has none, by design. An IR spot is a bench spot, never a starter (ESPN's `IR` slot maps to OUT, like Yahoo's). The front is slot, points, photo, name, game; "#7 RB" is the back's first line, never a tier code. K and DST are support cards with no tier (`cardsupport.js`): turf with the posts off to his right and one weather chip (dome, else wind); the club code large in its colours (`data/teamcolors.js`) with the opponent's implied points as a chip (`LIVE_LINES`, `design/lines.py`). Tap flips to the rank, the role stats and the profile; a skill player's back is washed in his position colour, and every back fits a 360px phone. Weather (`cardweather.js`, 2026-09-25): ff-jarvis forecasts the hour of each open-air stadium's next home kickoff; a card whose game it touches gets it moving over the art (wind streaks from 15 mph, rain from a 40% chance, snow), an amber chip ("RAIN 70%") and a back line ("RAIN · pass ↓"). Wind skips RBs; wet weather reads "run ↑" for them. Not on an OUT player, a dome or a retractable roof. Injuries (`LIVE_INJURY`, `design/injury.py`, `surface/teams/injury.js`, 2026-09-25): Sleeper's code in three levels, OUT (Out/IR/PUP/Sus/NA), D (Doubtful), Q (Questionable). A starter who is OUT or D is named in a red strip above the roster ("1 starter will likely sit: J. Jacobs OUT · Personal") and marked in it, Sheet (red edge) or Cards (red ring that breathes). A card: OUT greys the photo, OUT and D lay a band across its foot, Q is an amber chip; the back's second line gives the reason. Questionable never raises the strip: most of them play. Three across on a phone; on a desktop the nine starters are a 3x3 block with the bench three across beside them, the card width set by the window height so the roster fits one screen (104-150px) | `surface/teams/cards.css`, `js/surface/teams/cards.js`, `cardmotion.js` |
| Week's pack | once per league per week in Cards view (rebuilt 2026-09-25): a sealed pack of the players ranked top 12 at their position, glowing in its best card's colour (gold, pearl, or pink for a #1: how good, never who). It opens by itself on a black stage the first time Cards draws it in a page load; ✕ before the rip puts it back on the page (David's storyboard, 2026-09-25). Drag across the top to tear it (the strip follows the finger, the seam lights; past half it finishes) or tap. Foil flakes burst in the tier's colours (`packfx.js`, canvas); the cards come out one at a time in the centre, worst first, turn by themselves and shrink into a pile at the foot; the best card last with rays, shake, flash and a size up. The stage is a dark room, not a flat black (2026-09-25): the roster blurred and dimmed behind it, a vignette to near-black, and one light behind the centre card in that card's tier colour (blue, gold, violet, holo; stronger the rarer, `--pl`/`--pa`) with its pool on the floor under the card; the card is sized by the window (200-320px). The sealed pack leans toward the mouse in 3D (sways by itself on a phone), its strip flies off in 3D, the pack tips back, and the first card rises out of its mouth before the empty pack drops away. Only a drag that starts on the strip tears it (a tap anywhere only tugs the strip): the torn length lifts off at the finger, a lit edge marks the tear, every eighth ticks (buzz and foil), and a release eases back or finishes (registered `--tear`). Cards turn in real 3D from a TEAM//WATCH back, a signed card's autograph writes itself in after it turns (hidden until then) with a gold burst, and each card drops to the pile on an arc, leaning into a fan; then the stage fades to the roster, whose pack slots were left empty, and the pile flies home into them. ✕, Escape or Back after the rip skips to the roster. "Rip again" on the Sheet / Cards row puts the opened pack back, sealed. Android buzzes. Reduced motion lays it all out at once | `surface/teams/pack.css`, `packshow.css`, `js/surface/teams/pack.js`, `packshow.js`, `packdeal.js`, `packfx.js` |
| Gallery slip | after Underdog's share card since 2026-09-25 (was printed paper, which read as a bright panel in spaced capitals): a dark rounded card; headline number on top; legs grouped under game and kickoff; one rounded row per leg with photo, name, the call as a sentence ("Lower 4.5 Receptions") and one number at the right (Underdog %, DK price); a perforation, then Load slip | `surface/builder/ticket.css` |
| Roster hero | one line at every width since 2026-09-25: the team switch is the title, "Yahoo · 0-0 · league" beside it; Waivers keeps its full hero | `chrome/hero.css` `.hero.team` |
| This week | the roster's brief (`js/surface/teams/brief.js`): a starter's status (red out, amber other), a must-claim (lime), who the news names (grey). Desktop from 1100px: up to three lines in a sticky column beside the rows; 761-1099px: above the rows; phone: one line, a decision only, else nothing | `surface/teams/brief.css` |
| Topbar (desktop) | one pill: the week, its dot the sources' health; the live badge shows only on sample data | `js/chrome/feed.js`, `js/chrome/render.js` |
| Movers row | 52px head, name over verdict chip, share-change pill (role share before week 2) | `responsive/lists.css` |
| Value pill | filled green/red by direction, grey when flat; Movers only since 2026-09-25 | `component/vpill.css` |
| KPI tiles | removed at every width (roster and parlay) | — |

## Connected leagues (2026-09-24)

A visitor adds an ESPN league from the team switch ("+ Add a league"). Plan and decisions:
https://claude.ai/artifact/4ynPcsonQ7NkyUV8CNsNJM. David's two leagues stay baked in and default.

| Part | Where |
|---|---|
| Endpoint: GET lists, POST connects, DELETE forgets | `api/league.py` |
| ESPN host, id maps, slug (shared with `live.py` and `build.py`) | `api/_espn.py` |
| Connection: HttpOnly cookie `tw_leagues`, 400 days, browser only | `api/league.py` |
| Runtime state, added to `TEAMS` with `connected: true` | `js/data/connect.js` |
| The sheet: link, league-manager tip, phone bookmark, pasted cookies | `js/chrome/connect.js` |

A connected league has no Waivers tab: ff-jarvis builds the packet for David's leagues only. The
phone bookmark works because neither `espn_s2` nor `SWID` is HttpOnly (checked 2026-09-24). Yahoo
sign-in is phase 2.

## Waivers (sub-tab of My Teams, 2026-09-16)

A Roster | Waivers toggle under the team name, not a sixth nav tab: waivers are per league like
the roster, so the league switch carries over. (The phone's bottom bar this protected became a
top nav on 2026-09-24.) The data is ff-jarvis's `model.season.waiver_packet`, built daily by the refresh
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
counts are plain ("Must claim · 2"), never zero-padded. ~~The floating chat button covers the
page's right edge on a phone, so the rail rows and card footers keep `--fab-clear` free.~~
Superseded 2026-09-24: the chat launcher is in the nav row and covers nothing. The rail is three
rows + Show all on every day, not only Tuesday (the Mode row above is superseded on that point),
and a phone card front drops the proof stats and lane tag; the back still has both.

## The Board (Scouting's first view, 2026-09-23)

One lane per stat, the position's whole field on it. One component, three jobs, which is why it
is the whole surface:

| Picked | What a lane is |
|---|---|
| none | a leaderboard — the head names that lane's leader and his number |
| one | that player against the field |
| two | a duel; the distance between the dots is the answer on that stat |

**The lane's x is the stat's own value, never a rank.** A rank axis is uniform by construction —
every tick evenly spaced, the middle always dead centre, the gap between two players a count of
who is between them rather than the distance between them. On a value axis the pack clusters
where the pack is. The rank still gets said, in the head, because "#3" is what a reader repeats.

**The scale stops at Tukey's fence** (`q3 + 1.5·IQR`), **never tighter than the 97th and the
3rd**. Both halves are load-bearing. One receiver ran a route, caught it for 40, and holds a YPRR
of 13.64 against a position whose middle half is 0.78 to 2.20: drawn to the maximum he owned 80%
of the rail and the other 110 piled into the left edge. But the fence alone over-cuts a stat
whose middle half is narrow — RYOE's quartiles are 0.00 and 0.24 across 74 backs, which put 20 of
them on the two walls, and two players both pinned read as level when one is twice the other.
With the percentile floor the worst case anywhere is 4 pinned per end. A lane that was cut draws
a rule at that end; the number itself is never lost, because the head carries it in full.

| Part | What it is | Why not the alternative |
|---|---|---|
| Field | one tick per qualified player, fading leftward | direction is a property of the rail, not a caption saying which way is more — the radar's hub-to-rim move |
| Band | the middle half of the position, shaded | a median line needs a word; a region shows whether a dot is in the pack or out past it |
| Elite | dashed rule, named **with its number** in the head | on the rail the word wants the band a pick's initials own, and at 360px the two ran through each other ("ELIBRTE") |
| Dot | filled = ahead on this lane | lime keeps its one job; green/red would read as a verdict on a top-five back |
| Tag | his initials, first pick above the axis, second below | collision avoidance, not a code — the chips above carry the same two letters, so the rail needs no legend |

**"Overall" is a count of lanes, not a score.** Six stats ff-jarvis publishes separately, weighted
into one number by this page, would be this page inventing a model, and nothing here is
backtested. Counting the lanes each player is ahead on says the same thing out of numbers already
on the screen, and a reader can check it by looking. Only lanes where both have a number count.

### Role and style: two words under the picks (2026-09-23)

A lane is the position's whole field; a label is one player's, and most of the board has no
archetype record at all — so the two words sit under the picks and never on a lane. Each carries the
two or three numbers that produced it and the window they were measured over, because a word without
them is a verdict. `surface/board/label.js`, from ff-jarvis's `model.season.archetype`.

| Field | Window | Moves when | Card |
|---|---|---|---|
| Role | this season | the depth chart moves | opp share, route rate, goal line (RB); route rate, WOPR, TPRR (WR); snaps too (TE) |
| Style | his career | barely — it is a trait | before/after contact, breakaway (RB); aDOT, YAC share, catch (WR/TE); designed, scrambles, goal line (QB) |

They are separate on purpose: a back's style does not change when his guard goes out, his context
does. **A null is not a blank.** ff-jarvis's envelope guarantees exactly one of `role`/`role_null` is
set, and the reason stands where the word would — "not a field for quarterbacks", "career carries <
250". A number the evidence has nothing for drops out of the line rather than dashing, the same rule
a lane follows for an unmeasured axis. Why a flag (`goal_line_runner`) is a pill beside the style
and never a fourth style: ff-jarvis `model/season/ARCHETYPE.md`, "Quarterback".

Type follows the house rule as of 2026-09-23: the field's name and its window are labels and take
`.lbl`; the line of evidence under the word is a sentence and takes `.note`. The word is `t-4` and
nothing in the block is lime — lime means active, and a label is no contest anybody is winning.

The block closes on the Grid's own sentence, *what he did, not what he will do*, and not on a new
one. Why the style axes aren't equally sturdy: ff-jarvis `model/season/ARCHETYPE.md`, "`style` —
four, career, and the axes are not equally sturdy" — a data point to fold into a read, never a
forecast. Nothing is summed — no composite, no grade, no ranking, the same rule "overall" follows.

`LIVE_TRENCHES` (team-level OL continuity and injury exposure) stays off the Board: the Board's
unit is a player against his position, and a team number on a player's card would be read as his.
Since 2026-09-23 it renders in one place, the profile's Matchup pane, under the opponent's defense,
as a block headed with the team — "DET offensive line", never his name — so it answers "is his line
down starters this week" without posing as his stat. Since 2026-09-24 the lead cell is
`ol_starters_out`: of the five usual starters (ranked by snaps through last week), how many this
week's injury report lists Out or Doubtful — `2/5 starters out`, the names on a tooltip, amber from
one out and up (a real `0/5` stays plain). It is the before-kickoff read; `ol_continuity` (usual
starters who actually played) only fills in after the game, and keeps its own cell, `4/5`. The
plain injury-report count — every lineman on the report, starter or not — is the weaker signal, so
it only shows when `ol_starters_out` is null (no starting five known yet). QB/RB/WR/TE only; a null
field is a count ff-jarvis could not take and draws nothing, a real 0 draws.

Reuses rather than rebuilds. `sheetValues()` (`profile/sheet.js`) is the one definition of who
counts on an axis — the radar's denominator and the Board's are the same number. The picker is
the app's own search sheet, handed a slot to fill instead of a profile to open: `searchOpen(fn)`.
Axes are position-specific (a back has no YPRR), so a pick of another position moves the board to
his position and keeps only him; refusing it would make the reader undo a search he meant.

~~On a phone the chat button's reservation is measured from both boxes at render.~~ Superseded
2026-09-24: the button left the page's edge for the nav row, so the lanes keep no reservation.
The lane head is two fixed rows at every width: letting it wrap
fitted 360px, but only the lanes whose axis publishes a threshold wrapped, so three heads were one
line and three were two and the six stopped sharing a baseline down the card.

### Two modes: Leaders · Movers (2026-09-25)

Movers was its own view (the old Pool, `#pool`) until 2026-09-25. It is now the Board's second
mode: two readings of one position, so they share the position chip.

| Mode | What it answers | Controls under the chip |
|---|---|---|
| Leaders | who leads each stat (the lanes above) | "+ Add player", the picks |
| Movers | whose role is growing, week on week | the pager; a row opens the drawer |

- **The switch** sits directly under the position chips. It is the builder's `.modes-sub.dock`,
  the same control Parlay and DFS switch books with: a full-width segmented pill on a phone, the
  mono boxed toggle on a desktop.
- **One filter.** Movers has no chips and no ALL of its own; the Board's chip filters it. A chip
  is offered when the mode has something to draw for it.
- **The hash** is the one exception to "only the view is in the URL": Movers is `#movers`, and
  the old `#pool` still opens it, so a bookmark survives. Leaders is `#board`. A switch writes the
  hash, so Back undoes it.

**Movers, the mode.** Ranked on usage, never points: the rows sort by share change, largest rise
first, a row with no move below every row with one. The anchor is a quadrant scatter: **x =
change in snap/target share, y = points still owed (luck, sign flipped).** Best is top-right,
worst bottom-left; plotting luck itself put the sells on top and read as an upside-down V.

| Quadrant | Meaning | Action |
|---|---|---|
| upper right (green wash) | role growing, points not caught up | **buy low** |
| lower right | role and box score agree | confirmed, hold |
| upper left | role shrinking, points were unlucky anyway | fade |
| lower left (red wash) | points ran ahead of a shrinking role | sell high |

**Before a second week.** A share move needs two weeks. While no row anywhere has one, there is
no chart, the list ranks by role share, and one plain line above it says so (`pool.wait.line`).

**Live since 2026-09-17** (`LIVE_POOL`, `design/pool.py`): watch.json's league-wide pool, every
back and quarterback with 8+ opportunities and every receiver with 4+. The share a row shows is the
one watch's verdict reads (carries for a back, targets for a receiver or tight end, snaps for a
quarterback). "Free in" comes from watch's `rostered_by`: Mine, Both, ESPN, Yahoo, or a dash. The
16 hand-typed rows in `data/pool.js` are only the fallback when watch.json is missing.

Dot size is snaps; a lime ring means he is on one of my rosters. The list pages 10 at a time. A
desktop row has every column: snaps, Δ snaps, share, Δ share, verdict, free in. A phone row is
head, the name ("B. Allen") over the verdict chip, and the number the list sorts on in a `.vpill`:
the signed share change, or role share before one exists. The rest is the drawer's.

On a phone the chart draws to a taller, narrower geometry sized close to 1:1 with the screen,
per-dot names dropped (the list below names every player); dots stay tappable into the drawer.

## Matchups (Players, 2026-09-25)

Start or sit, for the players past the obvious starters. `LIVE_STARTSIT` (`design/startsit.py`) carries
ff-jarvis's own calls as frozen for the record (`model.season.startsit_calls`), Pitcher List's column
for the same week, and the season record (`model.season.grade`). The page computes nothing.

| part | what it shows |
|---|---|
| Record strip | Ours against Pitcher List through the last graded week, and the 1 / 0.5 / 0 scale |
| Position chips | QB RB WR TE, the one control row; WR opens |
| Start | Our starts outside the top 12 (QB/TE) or 24 (RB/WR), by our rank |
| Sit | Our sits on players the experts rank in that band, 40%+ rostered |
| Best spot | The softest matchup among our starters at the position, lime |
| Pitcher List | Their calls at the position, their words clamped to two lines, a link to the column |

- **The record leads.** It is the trust question. Through week 2 of 2026 ours reads 0.32 against
  Pitcher List's 0.67, and the strip says so without softening; the higher score is the lime one.
- **Every graded call is shown.** A call with no backing stat says "No stat this season backs this
  call" in amber rather than being hidden: hiding it would make the page and the record disagree.
- **Evidence chips carry a sign.** Up to three that argue the call, then one "but" against it. The
  defense-vs-WR chip is dashed: ff-jarvis's backtest found no WR matchup effect, so it is colour.
- **First data at ~180px on a 360×800 phone, the first call at ~305px.** Over the 200px budget for the
  first call, on purpose: the record is data, and a call read before the record is a call trusted
  without the one number that says whether to.
- **Desktop:** our start and sit on the left, best spot and Pitcher List on the right, so the two
  sources read side by side. A phone stacks them in that order.
- **Rows open the profile**, the same modal every other view opens.

Not built yet: Bets > Games (every game with its implied totals and each offense against the other
defense by position), the storyboard's second view.

## Parlay and DFS

**Superseded for Parlay 2026-09-25: Slips and Build.** Parlay is two views, Slips (leaf `parlay`,
the ready-made tickets stacked down the page) and Build (leaf `build`, the line market). Each has
one row of controls; its last chip names the book and kickoff and opens a panel with them (and
Build's market, sort and "my players"). Kickoff is one setting, `GAL_WIN`, for both views. The slip
is a tray on the bottom edge that opens into a sheet: a bar per leg's chance, the all-hit bar, then
the slip. At 360px the first slip moved from 303px to 154px. Motion: `surface/parlay/flight.js`,
per `design/STYLE.md`. DFS keeps the layout below.

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

The market is a card grid (2026-09-25, `css/surface/builder/grid.css`): two cards to a row on a
phone, as many 220px cards as fit from 760px up, so a screen holds twice the players the list did.
Opening a line's chevron widens its card to the whole row. Page sizes are multiples of 2 and 3
(12 players, 24 lines) so a page ends on a full row. ~~The gallery slip's paper was toned down the
same day (`--paper` #f1efe8 → #cbc4b4); it glowed against the dark page.~~ Superseded the same day:
the slip went dark (below).

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

**Microinteractions (2026-09-25)**, after motion.dev's gestures but in plain CSS
(`css/chrome/micro.css`). The springs are `--spring` and `--spring-pop` in `tokens.css`, `linear()`
curves sampled from a real damped spring, so no library loads.

| Beat | What moves |
|---|---|
| Press | every chip, button, nav tab, card and market line squashes under a finger and springs back |
| Lift | a market card rises under a pointer (hover devices only) |
| Enter | a new view's cards, slips and market cards rise in, staggered; meters fill from empty |
| Land | the tapped line flashes and its % pops; the slip count ticks; the new slip leg slides in |
| Card | the flip overshoots and settles; the photo drifts against the tilt |

Enter fires only when what the view shows changed (`markEnter` in `js/chrome/motion.js`), never on
a tap that only adds a leg, because `render()` rebuilds the whole view on every tap.
`tests/test_parlay_grid.py` pins both halves.

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

**The Bio pane carries the athletic profile** (2026-09-23), beside the pedigree it already shows:
three percentiles as bars — Speed from the forty against his weight, Burst from vertical plus broad,
Agility from cone plus shuttle — then the drills behind them and the pool they are ranked in. The
pool is the combine's own position, not always his fantasy one, so a fullback is ranked among
fullbacks and the block says which. Never summed into an athleticism number: the combine says what a
player can do, not what he does, and a fast heavy back is not thereby a power back. **A missing
drill draws no bar.** 277 players in the set have no agility score, and a bar at the floor would
read as the slowest man who tested; the score is named as unmeasured under the bars instead. No
record at all says so — "Not yet measured" for a rookie, "No combine record" for a veteran who ran
at his pro day or went undrafted. It joins the pedigree rather than standing alone, so the rule
above holds: no pedigree, no Bio tab.

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
