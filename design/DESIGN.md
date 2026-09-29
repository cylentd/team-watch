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

## Page width (2026-09-27)

Every view sits in one frame, so a tab change never moves the nav bar's edges.

| Token | Value | What it sets |
|---|---|---|
| `--page-w` | 1680px | the frame: `.wrap`, so the nav row, the view tabs, every view and the footer |
| `--page-pad` | 26px, 40px from 1100px | the frame's side gutter |
| `--list-w` | 1128px | a view that is one list (Ranks, News): the list's column, left on the frame's edge |

- **One width, in `base/tokens.css`.** A view never sets its own `max-width` on the frame. A
  view built outside `.wrap` (`.dg`, `.mu`) takes `var(--page-w)` and `var(--page-pad)`.
- **Fill the width** (STYLE.md). A view with columns (Roster, Waivers, League, Grid, the Digest
  wall) grows into it. A single list stops at `--list-w`, because a row with its number 1,400px
  from its name reads as two rows. Leaders splits instead: the #1 beside two lists (2026-09-27,
  "Leaders on a wide screen").
- **Why 1680:** the Digest wall was the one view designed for a wide screen, and at 1920 it cut the
  side margin from ~370px to 120px. Superseded: the 1180px frame with the Digest alone widening to
  1680 (2026-09-26), which moved the nav bar on every tab change into or out of This week.

## Phone layout (2026-09-24)

Storyboard: https://claude.ai/artifact/1S2qLgCTvmMxASpaUZK4q3. Every list row answers one
question: who, which way, one number.

| Part | Phone | Where |
|---|---|---|
| Nav | top: five groups as words since 2026-09-26 (This week leads; the words step down to `--t-3` with 5px sides, because at `--t-4` the search icon covered "Live" at 360px), search + chat icons; view tabs underlined below; both hide on scroll down | `responsive/760.css`, `js/chrome/hidebar.js` |
| Brand row | hidden; shown only when a newer build makes DATA a reload control | `responsive/760.css` |
| Ground | slate `#111418`, surfaces one step up each; no pure black, no radial glow | `base/tokens.css` |
| Roster row | a lineup sheet since 2026-09-25 (storyboard https://claude.ai/artifact/AqRomyQsQfd7TjYRiJkmhd): starter = slot, 28px head, name over "RB · BAL @ DAL", trend line, projection in ink with a green/red arrow. Bench two to a row with short names ("D. Goedert"), no line. The whole Yahoo team fits 360×660. Desktop: the bench column sits beside the starters, 44px heads, full names | `component/roster.css`, `responsive/lists.css` |
| Roster cards | the Cards half of a Sheet / Cards switch (2026-09-25, remembered per phone; Cards is the default since 2026-09-28, so a new reader meets the pack, and a stored Sheet wins). Tier = this week's projected rank at the position (`LIVE_PROJECTIONS` rank/of, ranked over every projected player in `design/projections.py`): Five tiers, one colour family each (2026-09-25; it had gold twice and silver beside grey): #1 Legendary holo (turning rainbow frame, glow, foil and glitter behind the photo, signed), #2-5 Epic violet (etched), #6-12 Rare gold, #13-24 Uncommon blue, the rest plain. A stamp in the photo's corner gives the rank ("#10") in the tier's colour. A player Sleeper lists as not playing (Out, IR, PUP, Sus, NA) shows OUT, no rank, no tier (`design/projections.py` OUT_INJURY). Tiers are earned by rank only. The autograph is a separate axis (2026-09-25, David's pick; it was every #1-5): a player who finished top 3 at his position in the last completed week (`LIVE_SIGNED`, `design/signed.py`; "completed" = every team scheduled that week has a game-log row) is signed on any tier, in gold foil ink (`--sig` script, never a real autograph) with a moving shine, a glow and a small holo seal; a roster with nobody in a top 3 has none, by design. An IR spot is a bench spot, never a starter (ESPN's `IR` slot maps to OUT, like Yahoo's). The front is slot, points, photo, name, game; "#7 RB" is the back's first line, never a tier code. K and DST are support cards with no tier (`cardsupport.js`): turf with the posts off to his right and one weather chip (dome, else wind); the club code large in its colours (`data/teamcolors.js`) with the opponent's implied points as a chip (`LIVE_LINES`, `design/lines.py`). Tap flips to the rank, the role stats and the profile; a skill player's back is washed in his position colour, and every back fits a 360px phone. Weather (`cardweather.js`, 2026-09-25): ff-jarvis forecasts the hour of each open-air stadium's next home kickoff; a card whose game it touches gets it moving over the art (wind streaks from 15 mph, rain from a 40% chance, snow), an amber chip ("RAIN 70%") and a back line ("RAIN · pass ↓"). Wind skips RBs; wet weather reads "run ↑" for them. Not on an OUT player, a dome or a retractable roof. Injuries (`LIVE_INJURY`, `design/injury.py`, `surface/teams/injury.js`, 2026-09-25): Sleeper's code in three levels, OUT (Out/IR/PUP/Sus/NA), D (Doubtful), Q (Questionable). A starter who is OUT or D is named in a red strip above the roster ("1 starter will likely sit: J. Jacobs OUT · Personal") and marked in it, Sheet (red edge) or Cards (red ring that breathes). A card: OUT greys the photo, OUT and D lay a band across its foot, Q is an amber chip; the back's second line gives the reason. Questionable never raises the strip: most of them play. Three across on a phone; on a desktop the nine starters are a 3x3 block with the bench three across beside them, the card width set by the window height so the roster fits one screen (104-150px) | `surface/teams/cards.css`, `js/surface/teams/cards.js`, `cardmotion.js` |
| Week's pack | once per league per week in Cards view (rebuilt 2026-09-25): a sealed pack of the players ranked top 12 at their position, glowing in its best card's colour (gold, pearl, or pink for a #1: how good, never who). It opens by itself on a black stage for the first unopened pack a reader meets in a week, whichever team it is (2026-09-28; it was every team, and a reader browsing leaguemates sat through a stage per team); the rest wait sealed for a tap; ✕ before the rip puts it back on the page (David's storyboard, 2026-09-25). Drag across the top to tear it (the strip follows the finger, the seam lights; past half it finishes) or tap. Foil flakes burst in the tier's colours (`packfx.js`, canvas); the cards come out one at a time in the centre, worst first, turn by themselves and shrink into a pile at the foot; the best card last with rays, shake, flash and a size up. The stage is a dark room, not a flat black (2026-09-25): the roster blurred and dimmed behind it, a vignette to near-black, and one light behind the centre card in that card's tier colour (blue, gold, violet, holo; stronger the rarer, `--pl`/`--pa`) with its pool on the floor under the card; the card is sized by the window (200-320px). The sealed pack leans toward the mouse in 3D (sways by itself on a phone), its strip flies off in 3D, the pack tips back, and the first card rises out of its mouth before the empty pack drops away. Only a drag that starts on the strip tears it (a tap anywhere only tugs the strip): the torn length lifts off at the finger, a lit edge marks the tear, every eighth ticks (buzz and foil), and a release eases back or finishes (registered `--tear`). Cards turn in real 3D from a TEAM//WATCH back, a signed card's autograph writes itself in after it turns (hidden until then) with a gold burst, and each card drops to the pile on an arc, leaning into a fan; then the stage fades to the roster, whose pack slots were left empty, and the pile flies home into them. ✕, Escape or Back after the rip skips to the roster. "Rip again" on the Sheet / Cards row puts the opened pack back, sealed. Android buzzes. Reduced motion lays it all out at once | `surface/teams/pack.css`, `packshow.css`, `js/surface/teams/pack.js`, `packshow.js`, `packdeal.js`, `packfx.js` |
| Gallery slip | after Underdog's share card since 2026-09-25 (was printed paper, which read as a bright panel in spaced capitals): a dark rounded card; headline number on top; legs grouped under game and kickoff; one rounded row per leg with photo, name, the call as a sentence ("Lower 4.5 Receptions") and one number at the right (Underdog %, DK price); a perforation, then Load slip | `surface/builder/ticket.css` |
| Roster hero | one line at every width since 2026-09-25: the team switch is the title, "Yahoo · 0-0 · league" beside it; Waivers keeps its full hero | `chrome/hero.css` `.hero.team` |
| This week | the roster's brief (`js/surface/teams/brief.js`): a starter's status (red out, amber other), a must-claim (lime), who the news names (grey). Desktop from 1100px: up to three lines in a sticky column beside the rows; 761-1099px: above the rows; phone: one line, a decision only, else nothing | `surface/teams/brief.css` |
| Topbar (desktop) | one pill: the week, its dot the sources' health, never wrapped; the live badge shows only on sample data. 761-1099px (2026-09-27): search is its icon; under 960 the wordmark hides (the lime mark stays) and the groups step down to `--t-3`, so the groups never slide under search | `js/chrome/feed.js`, `js/chrome/render.js`, `chrome/nav.css` |
| Movers row | 52px head, name over verdict chip, share-change pill (role share before week 2) | `responsive/lists.css` |
| Value pill | filled green/red by direction, grey when flat; Movers only since 2026-09-25 | `component/vpill.css` |
| Lead panel | shared by Digest and Matchups since 2026-09-26: one fact on `--panel`, a top wash in its status colour (red will likely sit, amber questionable, sky weather, lime a call), Bricolage headline `--t-6` (`--t-5` for a sentence), one fact line, the headshot masked into the panel at its foot and left edge. Full-bleed on a phone; from 960px a 440px sticky column, headline `--t-7`, photo 260px | `component/lead.css` |
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

## Leaguemates (2026-09-25)

Every team in David's two leagues is on the page, so a leaguemate picks theirs from the team
switch. Plan: https://claude.ai/artifact/NENnnTRYduCTAZEnG2r9ue. Decided 2026-09-25: anyone may
pick any team, team names only (never an owner's), per-team waiver adds this season (phase 3).

| Part | Where |
|---|---|
| All 24 rosters, rows shared with David's own | `design/mates.py` -> `LIVE_MATES` |
| Added to `TEAMS` with `mate: true`; the pick, in `localStorage` `tw-team` | `js/data/mates.js` |
| The menu, grouped by league; "Not your team? Pick yours" until a pick | `js/chrome/teamswitch.js` |

`notMine(team)` (a leaguemate's or a connected league) hides every line of claim advice: it is
computed against David's roster. Search counts a leaguemate's players as "yours" only while their
team is on screen.

Phase 2 (2026-09-26):

| A leaguemate sees | How |
|---|---|
| Trend and news on their rows and Cards | `design/signals.py` reads every LIVE_MATES roster too |
| Waivers: their league's Breaking rail, no status rows, no verdicts, no cards | `waiverKey(team)` is the league; `wvMateEvents` (rail.js) |
| Live: every matchup in both leagues, theirs included (superseded the per-team follow, 2026-09-28) | `design/gameday.py`, `api/stats.py`; the design is in `js/surface/live/live.js`'s header |

**My teams asks first (2026-09-27).** With no pick in this browser (`tw-team`), every My teams view
draws "Which team is yours?": all 24 teams by league, 48px buttons, and "Add your ESPN league"; no
"none", since each view is about one team. The Waivers count stays off the sub-row until a pick. It
replaced the "Not your team? Pick yours" nudge under David's team name, which left every leaguemate on
David's roster and claim advice by default. Connecting a league counts as the pick.

Phase 3 (per-team waiver advice) is shelved, 2026-09-26: it would help leaguemates beat David.
(Built on 2026-09-27 and tabled the same night, unlanded: ff-jarvis branch `waiver-teams`, team-watch
branch `worktree-waiver-teams`.)

**David's waiver advice is his browser's alone (2026-09-27).** `data/owner.js`: a browser that opened
`#owner-<token>` once (the page ships only its SHA-256; the link is wiped from the address bar) is
David's. Anyone else, whatever team is picked, David's included, gets Waivers as the league-wide
**Most added** list (`surface/teams/hot.js`, the Digest's `adds`), a hero with the day and clear time
only, no tab count, no waiver line in the roster brief, and no waiver rows in search. The advice is
still in the page source (LIVE_WAIVER): hidden from the screen, not from DevTools, David's choice
over encrypting it. Tests seed the owner key (`test_render.PICKED`); `test_waiver_owner.py` clears it.
What a leaguemate sees stays fun and shared, never advice.

## League (sub-tab of My teams, 2026-09-26)

Each league's own story, for the team on screen. Storyboard:
https://claude.ai/artifact/Lf17QZYMoNJvmVHCT45xUJ. ESPN since 2026-09-26; Yahoo the same day, read
off the fantasy website (`model.clients.yahoo_league`, the API is still unapproved) as
`LIVE_LEAGUE_YAHOO`. `lgOf(team)` picks the league; a connected league has no tab.

Yahoo gives every team a new id each season and hides managers, so its block has `scope`
"season": head-to-head is this season's, there are no all-time records, and champions come from the
All Time tab under the name each won with (a default "Team X" name is dropped).

| Part | Where |
|---|---|
| This season and 2014-2025, from ff-jarvis `model.clients.espn_league` | `design/sources.py load_league` |
| Awards, head-to-head, champions, records: all computed at build time | `design/league_recap.py` -> `LIVE_LEAGUE` |
| Which team is on screen (by the team switch's key), today's names | `js/data/league.js` |
| The week: chips, the team's own game, six awards | `surface/league/recap.js` |
| Rivalry with this week's opponent; records; champions | `surface/league/history.js` |

A team is its ESPN id across seasons and is always named by today's name. Early seasons carry
ESPN's default "Team <surname>", so a past name never ships; a team that left draws as "a former
team". A week chip redraws only the recap; the rivalry and history below never move.

**Superseded for Yahoo, 2026-09-27: the back page.** (The `scope` paragraph above: since the owner
map, Yahoo's head-to-head and records run all-time.) David's friends read the Yahoo league weekly, and
the plain recap read as clinical, so Yahoo became a sports tabloid's back page. Storyboard:
https://claude.ai/artifact/LBKkjFWgJ1rLZGrKtQ1Fn3. ESPN is David's work league and keeps the view above.

| Part | Where |
|---|---|
| Headline, dek, per game a punchline, 1-3 facts and a stamp: `claude -p`, R-rated, checked against the facts | ff-jarvis `model.season.league_roast` |
| Box scores (starters, bench, the one bench mistake per side) | ff-jarvis `model.clients.yahoo_box` |
| Records after each week, the bench award, meetings, tape fields, the record book | `design/league_back.py` |
| Masthead, superlatives, the page's layout | `surface/league/back.js` |
| The lead, the briefs, the agate standings, a game's sheet | `surface/league/lead.js` |
| Game cards (My recap) and box scores (the winner's side on the left) | `surface/league/slate.js` |
| This week's grudge: series record, one sentence, last meetings as W/L chips | `surface/league/tape.js` |
| Records tab: head to head, trophy case, last-place case, Hall of Fame, Hall of Shame | `surface/league/records.js` |

**Revised the same day** (storyboard https://claude.ai/artifact/JAp2FLPRYAXSVxnNtR8HKU), on David's read
that it had too much data everywhere and the point got lost:
- **The roast:** a paragraph per game became a punchline in the display face with 1-3 facts under it,
  numbers bolded (a negative one red). A punchline must name who it is about: "The man cost you points
  for showing up" was about DJ Moore and never said so. ff-jarvis's check enforces it.
- **The rivalry** was a tale of the tape (6 stat rows, a bar per meeting, a legend, 2 footnotes). It
  became the grudge: the series record, one sentence built from the data (who owns it, who has won the
  last few) and the last 8 meetings as W/L chips. On a desktop it stays in view beside the slate.
- **The record book left the week** for its own tab, **Records** (`hasRecords`: a league whose block
  has a `book`, so Yahoo only). The tab has no inner tabs. It opens on a trophy case (titles by today's
  team, then one line naming every team with none), followed by the Hall of Fame and Hall of Shame as record cards. Each
  record is filed under today's team, with "as <name then>" under it. ESPN keeps its history in League.

**Split into a league recap and a personal one, the same day** (storyboard
https://claude.ai/artifact/5vFc7Js5EsqJY3EmxgQc84). David: the recap is the league's, and it should not
bend toward whoever is picked. **Superseded:** the League leaf and Records under My teams, above.
- **This week > League** (leaf `recap`) and **This week > Records** (leaf `records`) always show the
  Yahoo league and are identical whatever team is on screen: no team lit, no box open, a page head
  naming the league. League adds **standings** after each week, one table serving as both standings and
  power ranking (record orders it, points beside it, LUCKY/ROBBED only where the two disagree by 2+,
  ▲▼ the move since last week), keeps the slate in story order (stamped games, then margin), and closes
  on **next week's grudge**: the most lopsided series among next week's games, 3+ meetings.
- **My teams > My recap** (leaf `myrecap`, Yahoo teams; a stale `#league` lands here) follows the team
  switch: the result, the game with its box open (the bench mistake is the box's own line), this
  week's score rank / standing / points rank, the grudge with next week's opponent, and every
  record-book line with the team's name on it, Shame included. ESPN keeps its League leaf.
- **Records names managers** (David's call): first names as Yahoo shows them, from ff-jarvis
  `data/yahoo_league_managers.json`, keyed like the owner map; the two Crystals carry last initials
  (W., H.). Team names change every season and managers do not, so a record is filed under the manager
  with the team it was then underneath, and former managers keep their records by name.

**This week > League became a newspaper back page, the same day** (storyboard
https://claude.ai/artifact/5Sj3BRZqyfaVWkvCXCjgFV). David: "not presentable", the right side empty, the
standings not worth their space. **Superseded:** the standings table, the week strip and the six-card slate above.

| Measure (1440x900, week 2) | Before | After |
|---|---|---|
| Page height | 2,959px | ends 865px (week 1: 886px), under the fold |
| First game starts | 1,023px | 264px |
| Right column | 91% empty | the briefs |

- **One lead, five briefs** (`surface/league/lead.js`): the lead is the game the roast's headline is
  about (`lead`, else the biggest margin) with the photo of the player its joke is about (`photo`),
  greyed like an OUT headshot when the player flopped (at most 0, or under half the projection:
  `league_back.photo_of`). Briefs are one line of names and scores plus the joke; tapping one opens its
  facts and box score in the modal, so no card grows.
- **Managers carry the score lines**, the superlatives, the grudges and the standings; team names appear
  inside the jokes, where the puns need them.
- **Standings in agate**: rank, manager, record, two columns of six. No move arrows, no LUCKY/ROBBED.
- **Private pairs** (`design/league_private.json`): a series a manager asked to hide draws as a
  Classified grudge every week, names blacked out, no ids in the page. **Superseded 2026-09-27:** David
  cut the card as too obvious; the pair's record still never ships, and Records draws its row blacked out.
- **Fold budget** is pinned by `test_league_back_page_fits_one_desktop_screen`; the phone order is the
  story, the lead, the briefs, the superlatives, then the grudges and the standings.

**Revised again the same evening**, on David's read that the headline and the lead said the same thing
and the briefs, all in display caps, were hard to read:
- **One headline:** the lead's joke is the page's headline (an `h2` on the lead card); the roast's own
  headline shows only when the lead game has no joke. The masthead keeps the kicker, the week chips, the dek.
- **Briefs in sentence case**, Archivo 500, 15px on a phone and 18px on a desktop. Display caps stay on the
  one headline, the stamps and the section heads.
- **Streaks** replace the Classified grudge: the two longest winning and losing runs going into next
  week, counted across seasons and playoffs (`league_back.add_streaks`, weeks' `streaks`).

**Records became head to head and two shelves** (same storyboard, its Records section):
- **Head to head:** a chip per manager (default: the team picked, when it is in the league), then every
  leaguemate best to worst by win share, then points, as a W-L bar, the record and the point difference.
  A row opens that pair's grudge card, with Show margins, in the modal. A private pair's row stays, its
  record blacked out, and always sorts last so its place gives nothing away.
- **Trophy case and last-place case:** drawn cups and wooden spoons (`--gold-2`, `--wood`), one per
  season, with the manager and the team it was that year, a tally line for multiple titles. Last place is
  Yahoo's final 12th (ff-jarvis `yahoo_league finals`, which counts the consolation bracket); a season it
  was never read for (2018) falls back to the worst regular season, dimmed, and says so.
- **The halls** drop titles and last places, which the shelves already show.
- **A pair's sheet splits the record by kind** (regular season, playoffs, consolation bracket; each
  meeting's 4th field, `league_back.MEET_KIND`), under the grudge card. The series itself counts
  every game: Lateef and Theo's 16 read as a mistake until the 2 playoff games showed.
- **A manager can be kept out of the book** (`design/league_record_skip.json`, `record_skip`):
  jstncno (former-2) gave up and left, so he holds no record and the next one down holds each; his
  games still count for his opponents, and he keeps his 2018 last place. David, 2026-09-27.

- **Voice:** Big Shoulders Display (`--tab`) for the headline, stamps and section heads, in this view
  only. The masthead rule is the league's colour.
- **First data at 269px on a phone (budget ~200):** the headline is the first data and runs three
  lines at 34px. It is the reason people open the page, so it stays big. The week chips sit above it.
- **Motion:** a new week arrives once. The dots drop, the cards rise, each loser is struck through,
  then the stamps slam (`.bp-in`). The first tap takes the class off, so a box toggle never replays it.
- **Taps:** several boxes may be open at once, so closing one never moves another card. Each control
  redraws only its own part.
- **A week the roast skipped** (two rejected replies) draws scores, boxes and superlatives without words.

## Trades (League group, 2026-09-28)

Storyboard https://claude.ai/artifact/EhbDwDUZ7ERb2iNfAqaKjn. **League became a nav group** (Recap,
Records, Trades): those pages are about the league and its history, not this week's games. It took
Gameday's slot; Live joined This week. On a phone "League" is 23px wider than "Live", so the bar's
labels went from 5px to 2px sides (8px clear of the search icon at 360px, measured).

| Block | Answers | Basis |
|---|---|---|
| Best / worst | who trades best and worst, and whether it is proven (a 90% range clear of 0) | held weeks, per trade |
| Trader ranking | each manager's W–L, the dot (average PAR a trade) and its range; a row opens their trades | held weeks |
| The 3 biggest heists | the best and worst trade ever (each heist is both) | trade tree |
| Trades that decided a season | the title, then every playoff spot or bye a trade moved | trade tree + the swing check |
| Curses | players whose sender lost every trade (Godwin 3 of 3, Chase 2 of 2); hot potatoes the reverse | trade tree |

- **Every number is ff-jarvis's** (`model.season.trade_verdicts`): points above replacement (QB12,
  RB30, WR30, TE12 that week, floor 0) from the trade to season's end; `design/league_trades.py` only
  names, shortens and orders. David's calls on 2026-09-28: judge a trade on its **trade tree** ("the
  most honest"); split a flip's return by what each player sent earned, not 1/n; drops are fine to ignore.
- **One basis per row:** a manager's W–L, dot and trade list count held weeks only, so a row never
  disagrees with itself; a trade whose tree verdict differs says so in the list ("Trade tree: … won it").
- **Margins are numbers** (PAR). Words ("the biggest ever") on the top three were recommended and are
  not built; David has not chosen yet (2026-09-28). 2026 trades show in the lists as open and stay out
  of the ranking (David's call).
- **First data at 218px on a phone** (budget ~200): the league name wraps to two lines, as on Records.
- The fixture lifts Andrew's range clear of 0 so the green "proven good" track has an element; the real
  data has no proven-good trader.
- **Players are faces** (2026-09-28, David: "hard to see who got traded"): every traded player is a
  headshot and his name in the display face; 93 of 152 have a head, the retired rest show initials in
  the same circle. Slugs come from the build (`live_trades(..., slugify)`).
- **Readability rule** (2026-09-28): no sentence below `--t-2` and none in mono; mono is for numbers
  and labels of a word or two. A decided line leads with a trophy (title, gold), an arrow up (a spot or
  bye gained, green) or down (lost, red).
- **The curse mark** (David picked E of five, storyboard v7): the face drained of colour before black
  fire (`--hex-*` tokens), and one skull per trade under it, red lost, hollow amber still open.

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

### Leaders on a wide screen (2026-09-27)

Storyboard: https://claude.ai/artifact/GZzBAiovV45XPYSCzu7Tzr (option B, David's pick). From
1100px the #1 is a 440px column on every page and the page reads down two lists beside it
(`.bd-cols`); below 1100px it is the single 900px card, the #1 on page 1 only.

| RB workload, 64 players, live data 2026-09-27 | before | after |
|---|---|---|
| 1920×1080, page 1 | #1–16, 700px empty | #1–41 |
| 1440×900, page 1 | #1–11, 460px empty | #1–33 |
| pages to see all 64 at 1920 | about 4 | 2 |

- **Every page has the same shape**, so `fit.js` sets one count for page 1 and the rest: rows per
  list, times two. Crossing 1100px re-renders and re-measures.
- **The #1 card keeps a fixed height** (440px, less on a window under ~670px tall so it still ends
  above the edge). The side-by-side tried on 2026-09-26 stretched it to the list's full height.
- **A bar is half the page at most**: each list keeps the phone's row, so bars stay comparable.

## Digest (This week, 2026-09-26)

The front page: one fact leads, every other topic is one ticker row. Storyboard (v3):
https://claude.ai/artifact/QyeSKebCWdeCqA9YvxXsdX; direction contract
`.impeccable/surfaces/design-src-js-surface-digest-digest-js.md`. `LIVE_DIGEST` (`design/digest.py`)
cuts ff-jarvis's `data/weekly_digest.json`, the same packet the morning Discord post renders. The page
picks nothing and computes nothing; it only decides which row lies open. This week is the first nav
group and Digest the default leaf, except on a Tuesday, when Waivers leads.

| part | what it shows |
|---|---|
| Lead | ff-jarvis's pick (`lead.rule`): a hurt starter, else a game in bad weather, else the top headline. A headline, one fact line ("The WR2 this week. Hip. LA @ DEN, Sun 5:20 PM."), the photo; weather draws its wind or rain mark instead. No stats row |
| Hurt | red count; the next two who will likely sit, then how many are questionable |
| Matchups | the call count; the best spot at WR, else RB, TE, QB |
| Weather | sky count; the first game past the bar, in mph or % rain |
| Waiver adds | lime pill: the biggest rise in ESPN % rostered |
| Top 5 | the leader at each position |
| Stock | the biggest rise and drop in the books' implied points |
| Gems | count; the first high-usage player ranked outside the starters |
| News | count; the newest FantasyPros headline |

- **Eight rows, 52px each** (56px from 960px): uppercase label, mono count pill, one line with the
  single most important name, chevron. Top 5 and Stock are lists and carry no count. A section
  with nothing says "nothing new" and cannot open.
- **The day opens one row** (`DG_DAY`, `data/digest.js`): Tuesday and Wednesday Waiver adds; Sunday
  Hurt, then Weather if no designation is new; every other day Hurt. A row earns it only with news
  in it (Hurt: a designation changed in the last 24 hours). The reader's own tap overrides and is
  kept across views.
- **A row opens in place**, one at a time, on the house spring (grid rows 0fr to 1fr); the list is
  never redrawn under the reader. It lists its players (each opens the profile), then a foot: where
  the numbers come from and a link to the full view. The adds bars grow from last week's % rostered
  to this week's.
- **Thresholds come from the packet's `rules`, never copied.** The weather and gems feet quote
  `rules.wx_list` and `rules.gems`, and which bar a game crossed is the row's own `bar`.
  ff-jarvis's `weekly_digest_schema` owns the numbers.
- **First data:** the lead at 49px, the first ticker row at 285px on a 360x800 phone (fixture,
  measured 2026-09-26). Closed, the eight rows end near 700px, above the fold; the day's open row
  pushes the later ones below it.
- **Nothing to lead with** (no packet, or a quiet week): the lead shrinks to one short line
  (`.dg-lead.quiet`), so the rows start right under it instead of under a 200px empty band.
- **960-1099px:** the lead is a 440px sticky column (min 420px tall); the ticker scrolls beside it.
- **The wall (1100px+, 2026-09-26, `surface/digest/wall.css`):** a desktop shows the whole week at
  once. The lead is a full-width band (380px, headline at `--t-hero`, the xl photo standing on its
  floor) with the reason he leads behind the photo as a faint outlined ghost at `--t-ghost` ("WR2",
  "22 mph"), stroked in the lead's status colour. Under it every topic is an open panel on a
  12-column grid:

  | row | panels (columns) |
  |---|---|
  | 1-2 | Hurt (5, both rows) · Matchups (4) · Weather (3), then Waiver adds (4) · Stock (3) |
  | 3 | Top 5 (8, with heads) · Gems (4) |
  | 4 | News (12, two columns) |

  A panel's head is its title (label + count; no line, no chevron, not a toggle); the day's topic
  keeps the lime title. Hurt gives each questionable player a line, since the panel has the room.
  The wall fills the page frame (`--page-w`, 1680px since 2026-09-27 for every view; see Page
  width). Phone and tablet are unchanged.

Not backtested: Weather, Stock and Gems. Each says "Not backtested." in amber on its opened foot,
never on the closed line: the closed line is the fact, the caveat is for whoever reads on. Lead copy
for the weather and news rules has no real week yet (2026-09-26).

## Matchups (Players, redesigned 2026-09-26)

Start or sit, for the players past the obvious starters, in the Digest's language (storyboard
frames 4 and 5, same link). `LIVE_STARTSIT` (`design/startsit.py`) carries ff-jarvis's own calls as
frozen for the record (`model.season.startsit_calls`), Pitcher List's column for the same week, and
the season record (`model.season.grade`). The page computes nothing.

| part | what it shows |
|---|---|
| Record strip | Pitcher List and ours through the last graded week: one bar each, filled to the score (0 to 1), each count on its own bar ("0.67 · 12 calls"); the higher one lime |
| Position chips | QB RB WR TE, the one control row; WR opens |
| Lead | the best spot at the position, the shared lead panel: "Start" + his name in lime, a facts line (our rank, the experts', the projection), up to three evidence chips, the photo, a foot naming the game and kickoff. A position with none says so |
| Our calls | one line per call, starts then sits: tag, head, name over game and kickoff, ours / experts, projection |
| Pitcher List | their calls at the position, a PL mark where our ranks sit |
| Foot | what makes a call, and the 1 / 0.5 / 0 scale (week 1 counts half) |

- **The record leads.** It is the trust question. Through week 2 of 2026 ours read 0.32 against
  Pitcher List's 0.67 (2026-09-25), and the strip says so without softening.
- **The lead keeps its facts line**, unlike the Digest's: our rank beside the experts' is what the
  page is for.
- **Rows open in place**, one open across both lists, kept across a position change. Ours opens to
  up to four evidence chips (green for; the defense-vs-position chip dashed, because ff-jarvis's
  backtest found no such effect; amber "but ..." against), the projection's source and a link to the
  profile. Pitcher List's opens to their own words (clamped to five lines) and a link to the column.
  Nothing on the closed line argues.
- **Every graded call is shown.** A call with no backing stat says "No stat this season backs this
  call" in amber rather than being hidden: hiding it would make the page and the record disagree.
- **Kickoff times come from `LIVE_SCHEDULE`** (matched through its club-code alias). The meta line
  wraps to a second line rather than cut the time; the name stays one line. No schedule row: the
  game alone. A Pitcher List row with no opponent shows the team, never "vs null".
- **Measured first data (2026-09-26, fixture, WR, 360x800):**

  | element | top |
  |---|---|
  | Record strip | 89px |
  | Lead | 204px |
  | First call | 335px |

  Over the 200px budget for the first call, on purpose: a call read before the record is a call
  trusted without the one number that says whether to.
- **Desktop (960px+):** the record and chips span the width (bars capped at 560px, so a score never
  reads as a progress bar); the lead is a 440px sticky column; the calls sit beside it, ours and
  Pitcher List's side by side once their column is 600px wide (a container query on the lists, not
  the window), stacked below that. The page caps at `--page-w` (1180px until 2026-09-27, now 1680px).

Not backtested: the calls. The foot says so, and names the record as the test.

Not built yet: Bets > Games (every game with its implied totals and each offense against the other
defense by position), the storyboard's second view.

## Weather (This week, 2026-09-26)

Every game of this week (`schedWeek`, the pack's week) with the forecast at kickoff. League-wide
and public, so it reads no roster (decided 2026-09-26): the players named are the projections' own
(`LIVE_WX_HITS`), and a reader's own players carry their weather on the Roster cards. `LIVE_WEATHER` is joined on the home club through
the schedule's alias (LA is LAR there); a forecast counts only when its `kickoff` is this game's.
It sat in Players for its first hours; it moved to This week (after Digest) the same day, which
put Players back to six views and let the 7-tab phone rule go.

**Reworked 2026-09-26 (same day): say only what moves scoring.** The reader is a casual player
setting a lineup on a phone; a condition with no proven effect is noise, so it is not mentioned
on a card. Superseded: the per-game "Does it matter? / Already in our projections? / Why" lines.

| part | what it shows |
|---|---|
| Games where weather lowers scoring ("raises"/"changes" from the effects' sign; the count in words, "3 games") | one card per game whose forecast meets a proven condition, most points moved first: matchup, kickoff; the conditions in `--sky` ("22 mph wind · 75% chance of rain · 64°F", "roof may close" for a retractable roof); what it does, proven positions only, summed across conditions and rounded to 0.5 ("QBs about 1.5 fewer points · WRs about 1 fewer"); once, "Our projections already subtract this." (and "Kickers aren't projected on this site." when kickers are named; fresh-reader fix, 2026-09-26: without it a reader concluded "bench them"); the forecast's age only past 12h, in amber; "Who it hits": per side the top-projected QB, two WRs and TE (`design/wx_hits.py`, Sleeper's out-list skipped), away side first, each with team and what is already in his projection (`wx.adj`, "−0.5"; a book-priced row, `src: "line"`, says "in the odds" and a tap opens why: the sportsbook line already prices the forecast), under a plain column label; a tap opens the profile. None this week: one plain line |
| Outdoors, Indoors | every other game as one row: matchup over kickoff, temperature and wind (none for a dome). Outdoors first, since only those rows carry a forecast |
| Played | one muted line naming the games already kicked off. **Superseded 2026-09-27** (David: "dim out the games that are gone instead of removing it"): a game that has kicked off keeps its card or row, at half opacity, "kicked off" beside its time, after the games still to play; its forecast is the last one fetched before kickoff (`LIVE_WEATHER.kicked`, design/wx_kicked.py, from ff-jarvis history `weather`) |
| How we know | the one disclosure: the method (2011–2025, points against his recent games and opponent, arm a, METHODOLOGY 12.53/12.54), what was tested with no effect (built from the data: "domes, running backs, and cold weather except for kickers"), the forecast source |

- **Conditions** (`data/wxhistory.js`): wind and cold at the backtest's thresholds, rain at the
  projections' `weather_adjust.thresholds.precip_pct`; a condition counts only with a passing
  position. `LIVE_WX_HISTORY` (`design/wx_history.py`) ships per condition `matters` (pos, mean),
  `tested` and `inproj`. No adjust block: rain never applies. No backtest file: rows only.
- **Motion:** the condition icon is the site's own wind or rain icon, each stroke its own path, so
  a still frame reads as the icon; with motion allowed only those strokes move: the wind's lines gust
  the way it blows (`wxWindSide`) at the roster cards' speed (`wxGustS`, shared), rain drops
  one per 25% chance. The one idle loop, allowed because the motion is the forecast; reduced
  motion shows the still icon (`test_the_sky_moves_only_with_motion_allowed`). Player rows press
  on the spring; How we know opens with a height ease (grid rows, `@starting-style`).
- **First data:** the first card at 188px on a 360x800 phone (live data, 2026-09-26). Desktop: cards
  three across at 1400px, the two lists side by side.

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
~~Opening a line's chevron widens its card to the whole row.~~ Superseded 2026-09-27: the chevron
is an ⓘ that opens the leg sheet (below). Page sizes are multiples of 2 and 3
(12 players, 24 lines) so a page ends on a full row. ~~The gallery slip's paper was toned down the
same day (`--paper` #f1efe8 → #cbc4b4); it glowed against the dark page.~~ Superseded the same day:
the slip went dark (below).

### The leg sheet and the TD board (2026-09-27)

One bet, read in one screen, from the bottom edge (`surface/parlay/legsheet.js`, numbers in
`legdata.js`, tiles in `legtiles.js`). Storyboard "Leg Sheet Storyboard", option B + C, then slimmed
the same day ("too much, not scannable"). Measured at 360x780 on live data: a receptions sheet is
475px tall, a TD sheet 424px, so neither scrolls.

| Block | What | Hidden when |
|---|---|---|
| Header | face, "D. Metcalf", pos · team vs opp · kickoff, the call and book, the model's % | never |
| Model line | "Model 3.4 · line 4.5 · book 56%": the model's mean, the line, the book's own chance of the pick's side (Underdog's under/over price; DraftKings' over for a TD) | each part without data |
| Bars | last 10 games vs the line, lime where the pick's side hit (a lower bar under the line is lime); one row under them of the stat that drives the bet (targets, carries, RZ touches), per game | the row without `u` |
| Tiles | three per market: RECS targets/gm, target share, catch rate (read "≈ 4 catches a game", "deep aDOT 14" from 12); REC targets/gm, yards/target, aDOT; RUSH carries/gm, snap %, RZ touches/gm; TD RZ touches/gm, GL carries, team RZ share (TDs in last 10 without `u`); PASS attempts, dropbacks, RZ attempts a game | a tile with no number |
| Matchup | "vs CIN · allows 0.83× WR receptions · 2 starters out" (names on a tap) | no `opp_f` and no defense data |
| Add to slip | the Build tap's own path (`betsToggleLeg`, builder/wire.js); the sheet steps aside so the pick's flight to the tray is seen | never |

- **Where it opens.** A pick on a slip: the whole row, since a slip's pick had only a one-line
  note to open. A Build line: the ⓘ at the row's end, because the row is the slip toggle and that
  has to stay one tap; the ⓘ is the chevron's old slot. A TD board row: the whole row.
- **Sources.** The log (`LIVE_MARKET.logs`, `u` optional), this season's usage grid when `u` is
  absent, and `LIVE_DEFENSE` (`design/defense.py`: points allowed by position, starters out, team
  codes on the page's LAR spelling). A number neither has is not drawn; never a dash.
- **Matchup is context, not a price** (ff-jarvis METHODOLOGY 12.29): the line says what the defense
  allows and nothing about the bet, so no caveat paragraph sits on the sheet.
- **Overlay.** Outside `#view` (`shell.html`), so a render behind it never rebuilds it; one history
  entry (`chrome/layers.js`), so Back closes it before the view; focus goes to its handle and back
  to the pick. Escape and the scrim close it too.

**TD board** (`tdboard.js`): on Slips' TDs chip, under the TD slips, every anytime-TD line still to
play at the chosen kickoff and playing (not out, Q, backup, stale or moved), ranked by the model's
P(score). Columns: player, model, book (DraftKings' over), RZ touches a game, games with a score in
the last 10. Top 20, then "Show all". Under the slips, not behind a toggle: a toggle is a second row
of controls above the data (STYLE.md), and the TDs chip already asks "who scores".

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
