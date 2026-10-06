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

## The page's week and its kickoffs (2026-10-05)

**One page week (2026-10-05, David): the whole site has one week, `schedWeek()` in `data/schedule.js`, ff-jarvis's `page_week` block read into `LIVE_SCHEDULE.week` by `design/schedule.py`.**
It turns at the first rebuild after the week's last game is final (the 9:15 PM PT Monday run), never on the
reader's clock. Three consequences:

| Views | Before the turn (Monday night, week W) | After the turn |
|---|---|---|
| Forward: Ranks, Teams, D/ST and K, Start/Sit, Bets, the pack, Highlights, Preview | week W's games still to play (Monday night), not W+1 | week W+1 |
| Backward: Recap, Accuracy, League recap, Slips record, autograph | week W | "Week W · final tomorrow" until the stats land (Tuesday 2:00) |
| A forward block written for another week (its producer has not run since the turn) | | not posted: that view's own empty state (`schedIsPageWeek`) |

`design/projections.py` `slate` marks every player whose projected game is not in the page week, so a file
written before Monday night leaves Ranks and Teams once the page turns; Ranks names what is left once more
than 8 teams are off (`schedOffLine`). Tests: `tests/test_js_page_week.py`, `tests/test_slate_week.py`,
`tests/test_page_week_build.py`. A document names the week it was written for (Recap, the Digest packet, a
Preview take) and says so.

Superseded 2026-10-05: the week of the projections, `slateWeek()`, read off the projection file's own rows (week N
while a non-Monday game of N was still some team's next game, so Monday said N+1), with `schedWeek()` as the
list views' week and `tests/test_js_week.py` (deleted) pinning it. Two weeks on one page is what the rule above removes.

**One kickoff format: "Sun 1:00 PM" in the reader's clock** (`lib/kick.js`: `kickFmt`, `kickTime`, `kickDate`,
`kickClock`, `kickPast`). No zone letters, no "ET", no "5:15p". A window keeps the league's own Eastern name
("Sunday early") and prints its times in the reader's clock. Python hands the page an ISO time (`at`, `ko`,
`commence`, `kickoff`) and the page writes the words; the Pacific `kick` labels from `design/slate.py`,
`design/digest.py` and `design/news.py` are only the fallback for a row with no ISO time. A body clock (the
travel row) is a team's own and is the same words, not the reader's zone. `tests/test_js_kick.py`.

## Page width (2026-09-27)

Every view sits in one frame, so a tab change never moves the nav bar's edges.

| Token | Value | What it sets |
|---|---|---|
| `--page-w` | 1680px | the frame: `.wrap`, so the nav row, the view tabs, and every view |
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
| Nav | top: five groups as words since 2026-09-26 (This week leads; the words step down to `--t-3` with 5px sides, because at `--t-4` the search icon covered "Live" at 360px), search + chat icons (the chat bubble carries the word "Ask" under it on a phone, 2026-10-05, plan U3: a bare bubble was not found; `chat.css`); view tabs underlined below; both hide on scroll down | `responsive/760.css`, `js/chrome/hidebar.js` |
| Brand row | hidden; shown only when a newer build makes DATA a reload control | `responsive/760.css` |
| Ground | slate `#111418`, surfaces one step up each; no pure black, no radial glow | `base/tokens.css` |
| Roster row | a lineup sheet since 2026-09-25 (storyboard https://claude.ai/artifact/AqRomyQsQfd7TjYRiJkmhd): starter = slot, 28px head, name over "RB · BAL @ DAL", trend line, projection in ink with a green/red arrow. Bench two to a row with short names ("D. Goedert"), no line. The whole Yahoo team fits 360×660. Desktop: the bench column sits beside the starters, 44px heads, full names | `component/roster.css`, `responsive/lists.css` |
| Roster cards | **Since 2026-10-05 (David's pick of the round-4 storyboard; `cards.js`, `cards.css`).** Tiers are three metals and the stock: #1 at his position **holo**, #2-3 **gold**, #4-6 **silver**, everything else **base**; K, DST and anyone unranked are base (`cardTier`; measured over 36 teams that is 1.8 metal cards a team, the old #1-12 cut gave 3.4; violet and blue retire). The face is "3G": the photo full bleed on the club's colour (`teamColourStyle`) inside a card-stock border that is the metal for silver, gold and holo (`--m-silver`, `--m-gold`, `--m-holo`, `base/tokens.css`; holo is static, no spinning, and tints the photo); the projection chip top right; the club-colour banner across the foot with the last name in Big Shoulders (`--tab`, shrunk to fit by `fitBanner`); a round badge, position over rank, bottom right, its ring the metal. Nothing is printed on the photo's middle but the autograph. OUT greys the photo and turns the projection red: no red bar, no red frame. Weather and Q/D chips sit on a row of their own under the projection (`.tc-flags`), never on it, the badge or the banner. The matchup is the first line of the back ("#7 RB", "BAL @ DAL"). K and DST wear the same stock, banner and badge (the badge says just K or DST). Grid gap 12px, three across on a phone. A `.fx` layer sweeps a light band over the border once when a card gets class `shine` (no idle loop, none under reduced motion). The autograph is still last week's top-3 finish (`LIVE_SIGNED`), but the face keeps only the gold script name, sized to fit by `fitSig` (min 12px), above the badge: `<div class="tc-auto"><span class="sgw"><span class="sg cool">NAME</span><span class="sg hot">NAME</span><i class="tip"></i></span></div>`. Static, only `.cool` shows; `.hot` (the pen's white-hot ink) and `.tip` (the nib) are hidden for the pack's motion to write it "on metal", left to right with sparks, the ink cooling to gold behind the pen. Its words, "Signed for week 3: #2 TE, 22.6 pts", are on the back as one row and in the pack's label. A back that does not fit drops its why line below 150px of card and, for a signed card, its last stat row below 180px (measured at 360, 390 and 430px). **Superseded 2026-10-05, the tiers, the front's layout and the autograph's look below; the rest of the row (support cards' art, weather, injuries, the back's stats) stands:** the Cards half of a Sheet / Cards switch (2026-09-25, remembered per phone; Cards is the default since 2026-09-28, so a new reader meets the pack, and a stored Sheet wins). Tier = this week's projected rank at the position (`LIVE_PROJECTIONS` rank/of, ranked over every projected player in `design/projections.py`): Five tiers, one colour family each (2026-09-25; it had gold twice and silver beside grey): #1 Legendary holo (turning rainbow frame, glow, foil and glitter behind the photo, signed), #2-5 Epic violet (etched), #6-12 Rare gold, #13-24 Uncommon blue, the rest plain. A stamp in the photo's corner gives the rank ("#10") in the tier's colour. A player Sleeper lists as not playing (Out, IR, PUP, Sus, NA) shows OUT, no rank, no tier (`design/projections.py` OUT_INJURY). Tiers are earned by rank only. The autograph is a separate axis (2026-09-25, David's pick; it was every #1-5): a player who finished top 3 at his position in the last completed week (`LIVE_SIGNED`, `design/signed.py`; "completed" = every team scheduled that week has a game-log row) is signed on any tier, in gold foil ink (`--sig` script, never a real autograph) with a moving shine, a glow and a small holo seal; a roster with nobody in a top 3 has none, by design. An IR spot is a bench spot, never a starter (ESPN's `IR` slot maps to OUT, like Yahoo's). The front is slot, points, photo, name, game; "#7 RB" is the back's first line, never a tier code. K and DST are support cards with no tier (`cardsupport.js`): turf with the posts off to his right and one weather chip (dome, else wind); the club code large in its colours (`data/teamcolors.js`) with the opponent's implied points as a chip (`LIVE_LINES`, `design/lines.py`). Tap flips to the rank, the role stats and the profile; a skill player's back is washed in his position colour, and every back fits a 360px phone. Weather (`cardweather.js`, 2026-09-25): ff-jarvis forecasts the hour of each open-air stadium's next home kickoff; a card whose game it touches gets it moving over the art (wind streaks from 15 mph, rain from a 40% chance, snow), an amber chip ("RAIN 70%") and a back line ("RAIN · pass ↓"). Wind skips RBs; wet weather reads "run ↑" for them. Not on an OUT player, a dome or a retractable roof. Injuries (`LIVE_INJURY`, `design/injury.py`, `surface/teams/injury.js`, 2026-09-25): Sleeper's code in three levels, OUT (Out/IR/PUP/Sus/NA), D (Doubtful), Q (Questionable). A starter who is OUT or D is named in a red strip above the roster ("1 starter will likely sit: J. Jacobs OUT · Personal") and marked in it, Sheet (red edge) or Cards (red ring that breathes). A card: OUT greys the photo, OUT and D lay a band across its foot, Q is an amber chip; the back's second line gives the reason. Questionable never raises the strip: most of them play. Three across on a phone; on a desktop the nine starters are a 3x3 block with the bench three across beside them, the card width set by the window height so the roster fits one screen (104-150px) | `surface/teams/cards.css`, `js/surface/teams/cards.js`, `cardmotion.js` |
| Week's pack | **Since 2026-10-05 (David's pick of the round-4 storyboard; `pack.js`, `packgate.js`, `packdeal.js`, `cardsign.js`, `packgate.css`).** The pack holds the nine starters. On a team the reader follows (`followLoad`), in Cards mode, until this week's pack is ripped or skipped, it waits in the starters' place (`packGated`): the grid keeps its size with every starter face down on the set's one back (`.tc.down`, `.tc-cb`: stock border, lime-striped panel, "TW"), dimmed, and the sealed pack, 132x185 (the stage's pack zoomed .66), stands near its top with Rip and Skip under it; the bench and the This week row draw as always. It makes one slow turn in 14 s, then rests 2 s facing the reader, only on screen and with the tab visible, still under reduced motion (STYLE.md motion rule 1); a drag turns it and it springs back; a tap or Rip grows it from its place to the stage's centre (FLIP, `pkGrow`), where the tear works as before. Skip shrinks it into the Starters rule's chip, "Open week N" with a small pack, and the starters turn face up in a wave (60 ms apart, the metals shining as they land); a tap on the chip grows the pack back onto the stage. Opened `tw-pack-<team>-<wk>`, skipped `tw-pack-skip-<team>-<wk>`, a Set when localStorage refuses. A team only browsed, and Sheet mode, never wait: the roster, with the chip. Once opened the chip is "Rip again". The deal, worst first, best last (`packScore`: stock by rank, then hits by metal and rank; a signed stock card counts as a hit): each card rises straight up to the stage's centre (its x is the centre throughout); a stock card flicks to the pile (~0.4 s); a metal holds ~1.3 s under its label ("GOLD", "#2 TE THIS WEEK", the metal's colour, the holo spectrum for a #1) while a shine crosses its border; a signed card holds again under "SIGNED", "#2 TE IN WEEK 3 · 22.6 PTS" while it is signed on metal (`cardSign`: a white-hot nib writes left to right, sparks fly off it, the ink cools to gold behind it; Web Animations only, sparks remove themselves; a 25 ms buzz); the best card, if a hit, keeps its moment (charge, flash, turn) before its label. A pack with no hit says "No metal this week" before the cards go home. Then the pile flies home as before. **Superseded 2026-10-05, what follows:** the stage that opened by itself for the first unopened pack of the week (`tw-pack-auto-<wk>`), the pack of only the top 6 above the cards, every card dealt face down and turned, "Rip again" only after a rip, and the empty pack shaken upside down. Once per league per week in Cards view (rebuilt 2026-09-25): a sealed pack of the players ranked top 12 at their position, glowing in its best card's colour (gold, pearl, or pink for a #1: how good, never who). It opens by itself on a black stage for the first unopened pack a reader meets in a week, whichever team it is (2026-09-28; it was every team, and a reader browsing leaguemates sat through a stage per team); the rest wait sealed for a tap; ✕ before the rip puts it back on the page (David's storyboard, 2026-09-25). Drag across the top to tear it (the strip follows the finger, the seam lights; past half it finishes) or tap. Foil flakes burst in the tier's colours (`packfx.js`, canvas); the cards come out one at a time in the centre, worst first, turn by themselves and shrink into a pile at the foot; the best card last with rays, shake, flash and a size up. The stage is a dark room, not a flat black (2026-09-25): the roster blurred and dimmed behind it, a vignette to near-black, and one light behind the centre card in that card's tier colour (blue, gold, violet, holo; stronger the rarer, `--pl`/`--pa`) with its pool on the floor under the card; the card is sized by the window (200-320px). The sealed pack leans toward the mouse in 3D (sways by itself on a phone), its strip flies off in 3D, the pack tips back, and the first card rises out of its mouth before the empty pack drops away. Only a drag that starts on the strip tears it (a tap anywhere only tugs the strip): the torn length lifts off at the finger, a lit edge marks the tear, every eighth ticks (buzz and foil), and a release eases back or finishes (registered `--tear`). Cards turn in real 3D from a TEAM//WATCH back, a signed card's autograph writes itself in after it turns (hidden until then) with a gold burst, and each card drops to the pile on an arc, leaning into a fan; then the stage fades to the roster, whose pack slots were left empty, and the pile flies home into them. ✕, Escape or Back after the rip skips to the roster. "Rip again" on the Sheet / Cards row puts the opened pack back, sealed. Android buzzes. Reduced motion lays it all out at once | `surface/teams/pack.css`, `packgate.css`, `packshow.css`, `js/surface/teams/pack.js`, `packgate.js`, `packshow.js`, `packdeal.js`, `cardsign.js`, `packland.js`, `packfx.js` |
| Gallery slip | after Underdog's share card since 2026-09-25 (was printed paper, which read as a bright panel in spaced capitals): a dark rounded card; headline number on top; legs grouped under game and kickoff; one rounded row per leg with photo, name, the call as a sentence ("Lower 4.5 Receptions") and one number at the right (Underdog %, DK price); a perforation, then Load slip | `surface/builder/ticket.css` |
| League team line | **Supersedes the Roster hero below and Waivers' full hero (2026-10-05, David: "the team selector is on every single tab and is also different").** One shape on all six League leaves at every width, at the same height on each (`test_every_league_leaf_draws_the_same_team_line`): the team switch as the title (24px, `--t-5`) with a chevron, the league line under it ("Madden Curse ⓘ · 1-2", one line, the league's name takes the cut, the ⓘ opens the league's format), and a view's own control at the right end (Roster's Sheet / Cards icons; Waivers' wire line, which drops under the league on a phone). A phone hides the switch: the header bar's is the one there. Recap's kicker no longer names the league. Storyboard https://claude.ai/artifact/WBatgHQtCYuVBPHykJcEQo | `surface/league/switch.js` `lgChipHTML`, `chrome/navrow.css` `.lgchip` |
| Roster hero | **Superseded 2026-10-05 by the League team line above.** one row at every width (2026-10-05, Roster redesign unit C; 116px tall on a phone before, 63px now): the team switch is the title at 21px (`--hero-name`) with a chevron, the league line under it ("ESPN · 3-1 · league ⓘ", one line, the league name takes the cut), and at the row's right end the Sheet / Cards switch as two icon buttons in one frame (list = Sheet, grid = Cards, `aria-label` each, the picked one lit; `rosterModeHTML`, `.rmode` in `chrome/hero.css`). "Rip again" stays on the Starters rule, never in the switch. Waivers keeps its full hero; My recap and League drew the same one-row hero with no switch until 2026-10-05, when Recap took the League chip instead. ~~One line at every width since 2026-09-25 with the Sheet / Cards word chips on a line of their own under the league on a phone~~ | `chrome/hero.css` `.hero.team`, `.rmode`; `js/surface/teams/cardmotion.js` |
| This week | the roster's brief (`js/surface/teams/brief.js`): a starter's status (red out, amber other), a must-claim (lime), who the news names (grey). Desktop from 1100px: up to three lines in a sticky column beside the rows; 761-1099px: above the rows; phone: one line, a decision only, else nothing. **The sit pill** (2026-10-05): a starter who is out or doubtful is a red pill in the row's heading, after "This week" ("S. Barkley out", the reason in its tooltip; several: "2 starters out"), in Sheet and Cards, in the folded row under the clips rail and in the open list; the count beside it shortens to "N to check" (`injWarnHTML`, `surface/teams/injury.css`). From 1100px the column's heading drops the count and keeps the pill and "Got it". ~~A red full-width strip above the roster ("1 starter will likely sit: ..."), 50px, Sheet and Cards~~ (superseded 2026-10-05). The red edge on the player's Sheet row stays; on a card the grey photo and red OUT mark him (the red ring went 2026-10-05) | `surface/teams/brief.css`, `surface/teams/injury.css` |
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
| Live: every matchup in both leagues, theirs included (superseded the per-team follow, 2026-09-28) | `design/gameday.py`, `api/stats.py`; see "Live" (tabs since 2026-10-04) and "The game sheet" below |

**My teams asks first (2026-09-27).** With no pick in this browser (`tw-team`), every My teams view
draws "Which team is yours?": all 24 teams by league, 48px buttons, and "Add your ESPN league"; no
"none", since each view is about one team. The Waivers count stays off the sub-row until a pick. It
replaced the "Not your team? Pick yours" nudge under David's team name, which left every leaguemate on
David's roster and claim advice by default. Connecting a league counts as the pick.

**"Mine" is the reader's pick, never David's (2026-10-04).** David: "Make sure that the site registers
the roster(s) that the user picks as the 'yours' or 'mine'. I don't want it to default to my personal
rosters." The page is public; his three teams are three of ~36. Until a reader picks or stars a team,
`followLoad()` is empty (it was David's three, and the pick when it was a leaguemate's), then the picked
team alone; the switch's first screen says "No teams yet" and shows a league row for every league, so a
reader can always reach a team. Live reads the same pick (see "Live", "Whose team is mine").
~~`followLoad()` defaulting to David's own teams~~ (superseded 2026-10-04).

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

## Navigation: one League group, Stats (2026-10-05, plan U8)

Top bar **Week · League · Stats · Bets**. Table in `js/data/navmap.js` (pure, Node-tested by
`tests/test_js_nav.py`), drawn by `js/chrome/nav.js`, whose header holds the dated history.

| Change | Why | Where |
|---|---|---|
| **Teams and League are one group, League** (David). Leaves: Roster, Waivers, Teams, Trades, Recap, Records | "League" was a group and a leaf under Teams, "Teams" a group and a leaf under League; the league was picked twice (team switch, Madden Curse / AYO / ESPN chips) | `NAV`, `navLeavesFor` |
| **One chip: the team switch.** Pick your team and the league follows: Recap, Records, Trades and Teams all read `lgFocusKey()`, the league of the reader's team (`lgMine()`; the team on screen when none is picked). The Madden Curse / AYO / ESPN chips and `tw-league` are gone; the league's name sits under the team's (the League team line, every League leaf since 2026-10-05) | one place to say "my league" | `surface/league/switch.js` `lgChipHTML`, `data/league.js` |
| **Recap is one leaf.** `#myrecap` and `#league` are `NAV_ALIAS` entries for it. A Yahoo league draws Recap B (2026-10-06, "Recap became direction B" below): the week stepper, YOUR GAME (the reader's game, grudge and record-book lines in one box), then LEAGUE, the same for every reader; superseded: the masthead with the reader's game under it and his lines at the bottom. An ESPN league keeps its plain recap, rivalry and history | one Recap, your game first | `surface/league/back.js`, `myrecap.js`, `league.js` |
| **Fewer leaves where a league lacks data**: ESPN has no record book or graded trades (4 leaves), AYO no graded trades (5). A link to a missing leaf lands on its nearest (`navFallback`: Recap, or Roster for Waivers) | six is the most a 360px phone holds | `navFacts` |
| **A reader with no team**: Roster still asks (the picker); Waivers opens on the league's public Most added list under the chip, Recap, Records, Trades and Teams open for everyone | the wire is the league's, not the team's. Tiered public verdicts are not built: David hid his tiers from leaguemates on 2026-09-27 (`data/owner.js`) and a roster-free tier needs ff-jarvis | `chrome/render.js` `renderAsk`, `teams/hot.js` |
| **Six leaves fit a phone**: League's sub-row takes an 8px gap (`.dense`; at 16px they took 366px with Waivers' count against a 332px row, at 8px 324px; measured at 360px, 2026-10-05) | | `chrome/navrow.css` |
| **Players is Stats** (group id `scouting` and every leaf id and hash stay). Sub-tabs named by what they hold: Highlights, Ranks, Leaders, **Work vs points** (leaf `movers`, was Role), **Usage** (leaf `usage`, was Grid), each view with one line saying what it holds (`stat-cap`; Role's is its head line). The draft's "Stat leaders" and "Usage grid" took 408px of the 332px row at 360px; these take 312px at the dense 8px gap | A + C of David's options; Highlights leads the group, Ranks second | `navmap.js` `navLabel`, `navCaptionHTML` |
| **Deep link to a row**: `navGoRow(leaf, slug)` opens Grid or Role on one player's row, sets the position, week and Show all so it is drawn, scrolls it to the middle and marks it (`.nav-hit`). The Digest's Gems rows carry a Grid link beside the profile line (1 tap); the profile and Start/Sit call it from plan U3 | a profile reaches its Grid row in 1 tap | `navrow.js` `navRowPlan`, `chrome/nav.js` |

Superseded below where marked: My teams as a group, My recap, the League switch.

### The phone's chrome (2026-10-05, game-day flow wave 2)

Storyboard: https://claude.ai/artifact/ArF53Lvh12QV8fbL3mr9KP. David: groups to a bottom tab bar (1B), a
header bar "like Yahoo and Sleeper", and "Tab opens in place". Up to 760px, top to bottom
(`css/chrome/phonenav.css`):

| Layer | Holds | Code |
|---|---|---|
| Header bar, 52px | the reader's team as the team switch ("Pick your team" in lime with no pick), Ask on the right; no brand, no Discord link, no week pill; slides away on a scroll down, back on a scroll up | `#hdrteam`, `paintHdrTeam` in `chrome/nav.js`; `chrome/hidebar.js` |
| Tab row | the group's views as pills; the open pill opens in place into its view's own tabs (Recap: Players, Scores, Claude, Accuracy; Live: My league, NFL, TDs, with the NFL games on now as a count; Slips: the kickoffs); the view draws no bar of its own on a phone (`#view .view-tabs` is hidden) | `#subnav`, `tabRowPlan` and `navModes` in `data/tabrow.js`; declared in `surface/live/tabs.js`, `surface/recap/recap.js`, `surface/parlay/bar.js` |
| Bottom bar, 64px | Week, League, Stats, Bets, Search: an icon over a word, the open group in lime | `#tabbar` |

- **Where things sit.** League's chip and the Roster and Waivers hero hide their team switch on a phone:
  the header's is the one. Live's score head shows the plain name on a phone and the switch from 761px. The slip tray, the trade builder's edit footer
  and the "new build" pill rise by `--dock-b` (the bar's height) so the bar never covers them.
- **Why.** The groups were the bottom bar until 2026-09-24, then the top bar (superseded), because Parlay's
  and DFS's switchers docked above the bar made the bottom 114px of every screen controls. Those switchers
  sit at the top of their views now, so the bar returned to where one thumb reaches it.
- A desktop keeps its one bar of words; `.tabbar` is `display:contents` there and `#hdrteam` is empty.
  Crossing 760px repaints the row (`NAV_PHONE`).

## League (Recap, ESPN and Yahoo; was a sub-tab of My teams, 2026-09-26)

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
| The page's layout, award tags (`lgGameTags`); the masthead and superlatives are superseded by Recap B, 2026-10-06 | `surface/league/back.js` |
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
- **My teams > My recap** (leaf `myrecap`, Yahoo teams; a stale `#league` lands here; **superseded 2026-10-05**:
  part of League > Recap, the reader's game first; both hashes still land there) follows the team
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
- **Blip when the joke names no player** (2026-09-29, David kept all five; storyboard
  https://claude.ai/artifact/RKkFYVa7asD65uWfvLMVLU): Blip takes the photo slot (`blip`, from
  `league_back.blip_of`), first that fits: biggest margin and lowest score KO (tips over, stars),
  biggest margin Wince, lowest score Flatline (NO SIGNAL), closest game Sweat, else Laugh. One reaction
  on the week's arrival (`.bp-in`), with the stamp on a stamped game, then still
  (`surface/league/blip-lead.css`, poses in `lib/blip.js` `blipReactSVG`).
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
- ~~**Trophy case and last-place case:** drawn cups and wooden spoons (`--gold-2`, `--wood`)~~ (superseded
  2026-09-28, below). One per season, with the manager and the team it was that year, a tally line for
  multiple titles. Last place is Yahoo's final 12th (ff-jarvis `yahoo_league finals`, which counts the
  consolation bracket); a season it was never read for falls back to the worst regular season, dimmed.

**The cases became cabinets (2026-09-28, storyboard https://claude.ai/artifact/8un5qeN8s5LwMaEKTfXGmV,
option A):** David found the flat panels didn't look like a case.
- **Trophy case:** a walnut cabinet behind glass, a downlight over each gold cup, a glass shelf of four, a
  brass plate with the year. **Last-place case:** the same cabinet bought cheap: laminate, a cracked pane,
  a porcelain toilet (David: "instead of spoon use a toilet"), the year on masking tape in marker.
- **The one exception to the flat console ("Cards" below):** shadows and gradients, each a material,
  from tokens named for it (`--walnut`, `--brass-*`, `--porc-*`, `--laminate-*`). `surface/league/cases.css`
  and `cases.js`, fenced to Records and the sheet.
- **A trophy or a toilet opens that season's final lineup** in the sheet: starters with points and their
  total, then the bench. From ff-jarvis `yahoo_case_rosters.json` (Yahoo's past team page, the season's
  last week). The team shown is the position only: Yahoo gives a moved player's team today, not then.
  2018's pages need a fresh Yahoo login, so its two slots draw the same shape and do not open.
- **Team names wrap to two lines**, never "…" (15 of 31 labels were cut at 360px).
- **Head to head's manager pick is a select** (12 chips wrapped to 4 rows; first record 404px -> 274px).
- **Desktop in two rows:** the cases side by side, then head to head beside the halls stacked (the case
  column had ended ~500px below head to head). A hall's first record spans two columns, so five fill
  the grid with no card alone on a row.
- **"Team Mahomie"** (Chanel's 2020 last place) is a chosen pun, kept past the rule that drops
  "Team <surname>" site defaults (`league_recap.CHOSEN_NAMES`).
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

**Recap became direction B, Scoreboard (2026-10-06, storyboard https://claude.ai/artifact/4GGAd3Xvk4sh8Sp2ktkDMU,
plan U2).** Superseded for Yahoo: the six superlative cards, the Streaks block, a stamp on every brief, the week
chips and the bottom `bp2-you` block (`back.js`, `lead.js`, `myrecap.js`; ESPN keeps its chips and awards).
- **Order, phone and desktop alike:** the team line, the `‹ Week 4 Final ›` stepper (44px targets, an end with no
  week beyond it disabled, `data-lgweek` like the chips), YOUR GAME, then LEAGUE.
- **Your game** (only with a team in the league): a lime-tinted box, the result, the score with managers as names and
  the team name small, the game's line, the three stats, then three disclosures closed by default: Box score (its
  summary the bench mistake), Next week vs <opponent> (the series), You in the record book (N lines).
- **League** is the same for every reader, so a screenshot or Share is the league's, not a person's: the reader's own
  game is an ordinary row, no lime anywhere, nothing reads the picked team (`test_league_back.py`). Header with the
  league's colour rule and Share; Claude's headline and dek; the lead (Blip or the photo, its one stamp, score, tags,
  line, facts, Box score); every other game as one row (score line, up to two award tags, the line, no stamp);
  "Going into week N+1" (the standings, each team's streak last, W3 green, L4 red); the biggest grudge.
- **Share** (`share.js` data and click, `share-draw.js` the Canvas picture): the League section as one 1080px PNG,
  games in the page's order (`lgGamesInOrder`). A phone that shares files gets the share sheet with a PNG drawn when
  the section drew (iOS drops the tap across an await); a desktop copies the image; then the text; then a modal.
- **Award tags** (`lgGameTags(w, g)`): top, low, unluck, luck, bench, close, two at most, flat in the row's flow. The
  Nail-biter is the week's closest game, so close always keeps one of the two places. No cheer/roast label or colour
  and no legend (David, 2026-10-06).
- **Desktop (1100px, the breakpoints lint allows):** Your game as one wide row; headline and dek side by side; the lead
  with the next game under it, the other four games 2x2 beside it; the standings and the grudge side by side.

**A third league, AYO (2026-09-29, David: "Everything"; for the League group "a switch on the page").**
AYO is a second Yahoo login in the first Yahoo league's shape, read from ff-jarvis's `ayo_<kind>.json`.

| Part | Where |
|---|---|
| The league list (key, platform, label, file names, blocks), held to ff-jarvis's `model/common/registry.py` | `design/leagues.py`, `tests/test_leagues.py` |
| Each Yahoo league's roster, League and Trades blocks (`LIVE_AYO`, `LIVE_LEAGUE_AYO`, `LIVE_TRADES_AYO`) | `design/myteams.py` |
| The team: third in the switch, tint `--ayo` (cyan, 9.1:1 on the slate); gone from TEAMS without `LIVE_AYO` | `js/data/teams.js`, `hydrate.js` |
| Madden Curse / AYO chips above Recap, Records and Trades; kept in `localStorage` `tw-league` (the hash stays the view's); hidden with one Yahoo league | `surface/league/switch.js` |

- **Records** needs a past-seasons file (`history` on the block). AYO's arrived as podiums only: the
  trophy case names each champion by the team it won as, once; head to head is this season's. With
  no history file, Records says so under the switch. **Trades** without a verdicts file says the same.
- **First data** moves down one chip row (~50px on a phone) on the three League views when the switch
  shows. It is the one row of controls STYLE.md allows, and the page must say which league it is.
- The back page's rule and kicker take the picked league's colour (`--lg-tint`).

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
- **One card system, the box score** (David chose A of two, 2026-09-28, storyboard
  https://claude.ai/artifact/57FSz4b4TrAxrb79EJJXjp): every card is a header strip, a body and a
  footnote (`trBox`, cards.js). A trade's body is its two sides as rows with the scores in one right
  column; a card with one number keeps it beside its label. Best/worst, heists, decided, curses and a
  manager's trades all use it.
- **Alive, with guards** (`alive.js`): the ranking row crossing the middle of a phone screen lights;
  a tapped curse fire flares, its skulls pop in one by one and the card's mist swells; a manager's
  trades drop in on open; the decided cards shuffle every 10 s on a desktop, with no progress bar
  (STYLE.md rule 1's dated exception). A curse card wears purple mist around it, off every edge,
  drifting slowly behind its panel (the second exception), plus a violet mist inside along its bottom
  that swells on a tap. The first mist, `--hex-1` at .28 inside the card, was invisible on the panel.
- **Layout, third pass** (2026-09-28, David): the top row is five cards, best, worst and the three
  heists, each heist headed "Heist #n" then who robbed whom; the ranking pairs with the curses; the
  decided trades run three across. No luck sentence on best/worst: the strip holds the record, the
  ranking's line says how sure. A tied trade (0.0 both ways) shows as T and a record as W–L–T.
- **One story per card** (David chose B, the back page, 2026-09-29, storyboard
  https://claude.ai/artifact/PxyR3tAZs9LeaioEPEz9Gq): every card is strip (what, when), headline (the
  story in `--tab` caps), deck (its numbers), proof (the trade's two sides), payoff (only a
  consequence, in ink). Best and worst carry their defining trade as proof, so the top row matches by
  content. Headlines never brag for the winner of a decided trade ("The trade that decided 2021") and
  root for the worst trader ("Chanel is due": David, "trading is healthy, we should promote it"). The
  curse's count lives in its skulls and deck, not the strip. Superseded: the "a trade" lead card and
  the grey "After:" footnote.
- **Ranking, second pass** (2026-09-29): place, manager, per-trade number beside the name, likely range,
  W–L–T, under column heads instead of a legend; sorted by the number shown (David: "sort by shown"),
  not ff-jarvis's shrunk figure. PAR's meaning moved under the page title, before the first number.
- **Aligned cards** (2026-09-29, David: "the top part should be bigger", "the body section should
  align"): the strip's label is `--t-3` with an 18px icon, every card kind has one (the heists a gold
  burglar mask); on a desktop each row's cards share four subgrid tracks (strip, headline, proof,
  payoff), so trade rows start on one line and payoffs share the bottom. A curse shows only with 3+
  trades of its player (2 of 2 happens 1 time in 4 by chance), so "Also cursed" and "Hot potatoes"
  are gone. The fire mark's button reset now comes before its grid, which had left the skulls off
  centre.
- **Phone: swipe rows** (2026-09-28): the top row, the decided cards and the curses each scroll
  sideways one card wide with the next peeking in, a "1 of 5 · swipe" pager over each; ~4,600px became
  ~2,400px at 390px. A phone shows every decided card, with no shuffle and no Show all.
- **The curse mark** (David picked E of five, storyboard v7): the face drained of colour before black
  fire (`--hex-*` tokens), and one skull per trade under it, red lost, hollow amber still open.

## Teams (League group, 2026-10-05)

Storyboard https://claude.ai/artifact/BXCJdmWfC87Z7VCAgdVC3Y, option B. Leaf `teams`, hash `#teams`, last in the
League group. One row per team in a league, one column per position (QB, RB, WR, TE, FLX).

| Part | Rule |
|---|---|
| A cell | the sum of the team's starters' projected points for each one's next game, in its best legal lineup; FLX is what the league's flex slots take, the best RB/WR/TE left over. The key says "Week N projected points" with the projections' own week (`LIVE_TEAMS.week`, the week most players' next games fall in, `projections.slate`), never the page's week (2026-10-05): after Sunday the projections are already week N+1 while the page's week is N until Monday night's game is final. A player on a bye that week counts 0 |
| The sort | the pressed header is lime; no caret, which read as a dropdown (2026-10-05) |
| Tint | `--up` at 8% or more over the league's median for the column, `--down` at 8% or more under, else plain (`LB_EDGE`) |
| Spare starter | a lime "+" in a cell's corner: a bench player at that position who projects above the median team's weakest starter there. The flex slots count as starters when finding the weakest one. QB, RB, WR and TE columns only |
| Pin | the reader's own team (`tw-team`, never David's) is the top row with a lime outline, whatever the sort; no team of theirs in the league, no pin |
| Sort | total of the lineup, best first, by default (the team column's button, "Team · Total"). A column header sorts by that column; a second tap goes back to the total. Real buttons, one always pressed |
| Team page | a row opens that team as a full page in the view (`lbpage.js`, David 2026-10-05: no pop-ups from the bottom, so no sheet, no scrim, no motion), nav bar and League sub-row still on screen: a "‹ Teams" link, the name, record and total, one action in a fixed-height slot, then LINEUP by slot and BENCH (position, name as initials, projection). A page is a history entry (`layers.js`, no URL change: the hash stays `#teams`, so a reload lands on the board). Back and the ‹ link each step back one page, and the board returns at the scroll the reader left (`LB_Y`). Content keeps to one 560px column, left on the frame's edge (a name and its number stay within STYLE.md's 560px). The action is above the lineup, not below the bench as first asked: under 16 rows it was a screen away on a phone. Data starts ~235px down at 360px, over the ~200px budget for that reason |
| Action | "Find trades with <team>" when the reader's team is in this league and is another; "This is my team" when the reader has no team in this league; a quiet "Your team" chip on their own. "This is my team" calls `pickTeam`, the team switch's own function and storage (`tw-team`), so My teams, Live and the rest follow, and the page redraws as theirs. A reader who already has a team here never sees it on another team: they switch with the team switch |
| No team yet | while the reader has no team in the league on screen, one quiet line above the grid says "Tap your team to set it" |
| Leagues | all three. **Superseded 2026-10-05:** the board is the league of the reader's team, whichever of the three, set by the one chip (`surface/league/switch.js`, the team switch); the league switch and `tw-league` are gone. Records and Trades are the Yahoo leagues' alone |
| Empty | a league whose roster file is missing or names no starting slots gets the shared dashed empty block under the switch |

- **Data:** `design/teams.py` -> `LIVE_TEAMS`, from the three roster files (`espn_rosters.json`,
  `league_rosters.json`, `ayo_rosters.json`), `player_projections.json` and each league file's standings. Starting
  slots are read from the data: ESPN's `starters`, else the most players any team has in a slot (Yahoo's
  `W/R/T` is flex). K, D/ST, IR and anyone Sleeper lists as not playing are left out; no projection counts 0. The
  lineup rule is ff-jarvis's `model.season.leagues` (`counts`, `fills`), re-written in `teams.py` and not imported:
  nothing in this repo imports `model.*`. Dedicated slots take the top players at their position, then the flex
  slots take the best left, which is the optimum for a flex open to several positions. The page computes only the tint.
- **First data at ~145px** on a phone, 12 rows in one screen at 360x800; five 38px columns, tabular figures, the
  team's name takes the rest and ends in an ellipsis. Desktop: the grid stops at 720px, left on the frame's edge,
  cells 84px.
- **Not built:** a median row, a total column (the total is under each name), the team's week-by-week line.

### Trade builder (League > Teams, 2026-10-05)

Storyboard https://claude.ai/artifact/BXCJdmWfC87Z7VCAgdVC3Y, frames 1-4 (frame 4, Edit, since 2026-10-05). A lime
"Find trades with <team>" button on the team's page opens the builder as the next full page (`tbpage.js`; it was a sheet
over a sheet until 2026-10-05, when David dropped every pop-up from the bottom). Its link reads "‹ <team>", and Back and the
link return to that team's page, which is still there after (`layers.js`, one history entry per page).

| Part | Rule |
|---|---|
| Button | On the team's page, in its action slot. Shown when the reader's own team (`tw-team`, never David's) is in that team's league and is not that team. A reader with no team in the league gets "This is my team" instead (see Teams, "Action"); the reader's own team gets a "Your team" chip |
| Head | "You ⇄ <team>", the swap a drawn icon |
| Bold | The offers that gain the reader the most, ranked by their gain, that the other manager would also see as a gain at his price (option B, 2026-10-05; ff-jarvis `rules.perceived`: season average, plus half the last-2 streak, plus a leash for round 1-3 picks; an untested guess). Never an offer for a player the partner's team name is built on (`rules.namesake`: Honey Bijan keeps Bijan) |
| Fair | The Bold test, and the partner's real gain by projection is not below 0. Ranked by the reader's gain. A pair can have none |
| Perceived filter | The producer's, not the page's: the page re-checks the reader's gain only, so a partner who sees a loss is never recomputed here. It is not labelled on screen; the chips and the pitch are its only trace |
| Chips | Hot (`--heat`), Cold (`--sky`), Early pick (neutral), small and flat like the status pill, on every player of an offer card and of both Edit rosters. Hot and Cold are the last 2 games' average 4+ points off the season's; Early pick is a round 1-3 draft pick (`rules.chips`). On a card they sit on a line under the name, because a card column is ~140px at 360px and a name plus two chips does not fit one line; on an Edit roster row they trail the name; the Edit package shows none, so its rows stay one line tall |
| Tabs | Two chips, Bold then Fair, one pressed. Bold opens first; the last tab is kept in memory for the visit. One line under them names the tab: "Biggest gain for you" / "Both lineups gain" |
| Offer card | At most 3 per tab. Two columns, YOU SEND and YOU GET, a row per player: position, name as initials, an amber pill (O, IR, Q, D) where a status is set. Under them one number, the reader's gain, "+8.5 pts a week for you", mono and green. No partner gain, no season averages on the card |
| Room lines | The reader's roster room only: nothing on the card says whether the partner has room (David, 2026-10-05); the copied pitch does (Copy offer, below). **The rule (fixed 2026-10-05, after David: "IR is not a drop candidate"):** over the cap, an injured player eligible for IR moves to a free IR slot first; only then are the lowest-`keep` non-starters dropped, never a `protect` player (early picks, anyone who would start for half the league). Two quiet lines under the columns, each only when it has someone, IR above: "To IR: C. Williams" (an offer's `ir_moves`), then "You drop: O. Gordon II" (`drop`). Initials, comma-separated, never amber |
| Edit | A button beside Copy offer on every card, two equal halves under the gain. Opens the edit state on the same page, its own history entry: Back and the page's link (now "‹ Offers") each return to the offers first, and focus goes back to the Edit button |
| Make your own | A full-width outlined button under the offers, on both tabs and in the "none" empty states. Opens the same edit state with an empty package |
| Edit state | Three parts that never move or resize: the package on top (YOU SEND / YOU GET, three rows tall, a fourth scrolls inside, a row is a button that takes the player out), the two rosters under it (the page scrolls past them: "Your roster" and "<team> roster", a card each, stacked on a phone and side by side from 760px within 720px, position, initials, IR/injury pill, projection to one decimal, a lime tint with a 1px outline of it and a tick on a picked row, no one-sided edge), and the foot, a tray stuck to the bottom edge (STYLE.md: what the reader builds lives there; `position:sticky`, so it rests under the last row at the page's end and hides none). The foot: the live gain ("+5.5 pts a week for you", green above 0, red below, grey at 0, a dash for an empty package), two rows for the "To IR" and drop lines (kept empty so nothing shifts), Reset (back to the offer it started from, disabled while there is no change) and Copy offer (lime, the same message as a card's, disabled until both sides have a player). A package the cap cannot take (nobody left to drop) shows a dash and "Over the roster limit, no one to drop". Gains of any sign show, unlike the offers the producer writes (>= `rules.min_gain`) |
| Copy offer | Per card. Puts "Trade? I send Purdy (28.8 a game), Higgins (14.4) for Smith-Njigba (25.3) and Brown (11.4)." on the clipboard: surnames and true 2026 points a game in that league's scoring (`seen`), nothing projected. **A Hot player the reader sends is quoted on his last 2** ("McMillan (20.5 a game his last 2)", `last2`), selling high, because the other manager prices the streak; **every player the reader gets is quoted on his season average, Hot or not** (his last 2 would inflate the ask; David, 2026-10-05); the "a game" unit goes on the side's first season average. Then one sentence on the partner's room from the offer's `their` (option B, 2026-10-05): "D. Smith can go to your IR slot, so you don't cut anyone." or "You'd only need to cut K. Johnson."; with both, "D. Smith can go to your IR slot. You'd only need to cut K. Johnson." (no "you don't cut anyone" before a cut; deviation from the spec's two sentences, which contradicted each other). Nothing when `their` is empty. In Edit the sentence is worked out live for the package (`tbTheir`, the room rule run on the partner's roster, `values[partner]`), and left out when the partner has nobody to cut. Where the clipboard is refused the text shows in a box, selected (on a card; in the edit state, in the tray). The button says "Copied" for 1.6 s |
| States | Loading: three card-shaped placeholders (no motion). Error (offline, file://, a missing file): one dashed block and Try again. A tab with none: "No fair offer this week" / "No bold offer this week". A pair with no entry: "No offers this week", no tabs. The `updated` date in a footer line |
| Size | Phone, 360px: the first offer card starts at ~285px (a two-line team name; ~255px with one), over the ~200px budget (STYLE.md) because the link, the head, the tabs and their line come first. The tabs sit at the same place on Bold and Fair, so a tab never moves them. Desktop: one 560px column on the frame's edge; the edit state's rosters sit side by side within 720px |

- **Data:** ff-jarvis `trade_offers.json` (`model.season.trade_offers`, nightly, feed block `trade_offers`; ~650 KB).
  `design/sources.py` `load_trade_offers()` (feed first, file second), checked at build time by `contract.py`
  `TRADE_OFFERS`, written compact beside the page by `design/trade_offers.py` as `trade_offers.json`. **Never injected**:
  the page fetches it the first time a reader opens the builder and keeps it in memory for the session
  (`surface/lboard/offers.js`). `.vercelignore` is an allowlist and lists it; `.gitattributes` marks it generated and
  `land.ps1` folds it into the land commit like `build.json`, so a feature branch never commits it.
- **The scorer and its guard (2026-10-05):** Edit scores the reader's package in the browser, so the rule is ported:
  `surface/lboard/tbscore.js` is a pure port of ff-jarvis's `rules.scoring` and `rules.drop` (written in the file's own
  `rules`), over each league's `lineup` (with `ir`, the IR slots), `values` (every rostered QB/RB/WR/TE of every team, with
  `proj`, `ir`, `keep`, `ir_ok`, `protect`) and `other` (K/DST per team, which count toward `lineup.cap`), and each offer's
  `ir_moves` and `drop`. The drop rule in two lines: over the cap, IR-eligible players move to free IR slots first, the
  highest `keep` first; then the lowest-`keep` non-starters outside `get` go, never a `protect` player, and with nobody left
  to drop there is no offer ("Over the roster limit, no one to drop"). The page never owns the rule: the
  file's `rules` text does. `offers.js` re-scores every offer of the open pair when the builder first draws it
  (`tbEditOk`); if one gain is more than 0.15 off, a drop or an IR move differs, or `lineup.ir`, `keep`, `ir_ok`, `protect`,
  `ir_moves` or `drop` is missing (a file from before the rule, 2026-10-05, or older), **Edit and Make your own are hidden for the session**, the offers and Copy offer still show, and the console
  names the offer. Fail closed: a wrong number on a package the reader built is worse than no Edit. The test fixture is
  a cut of the producer's own file and `tests/test_trade_edit.py` asserts the port reproduces every gain, drop and IR move in it
  exactly, and in `tests/fixtures/trade_offers_ffjarvis.json`, ff-jarvis's own drop-rule file (ESPN, 121 offers, 8 with
  IR moves, 25 with drops, 2026-10-05), which the guard also accepts pair by pair. A rule change on either side shows up there first. `trade_offers.py` `DROP_RULE_REQUIRED` has been True since 2026-10-05 (the ~~"False until the live file carries the rule" note was superseded~~ when ff-jarvis 4e69378 landed).
- **Option B, the partner's price (2026-10-05, spec `option-b-spec.md`):** each player carries `last2` (null with under 2 games) and `chips`, each offer `their` (the partner's `ir_moves` and `drop` by the same room rule). The guard re-derives `their` with `tbTheir` and compares names per offer, so a missing `their` or a different one shuts Edit like a wrong gain: **the page lands after ff-jarvis, or Edit stays off until it does**. `trade_offers.py` `OPTION_B_REQUIRED` is False (TODO beside it: flip it the day the live file carries the fields); until then the fields are checked only when present.
- **Producer's option-B file (`tests/fixtures/trade_offers_ffjarvis_optionb.json`, ff-jarvis b23bf06, ESPN, 3 owners):** the Node tests assert the port reproduces every gain, drop, `ir_moves` and `their` in it exactly (10 offers move a partner's player to IR, 27 cut one) and that the guard accepts every pair unstamped; the contract passes with `OPTION_B_REQUIRED` on. Nothing disagreed with the port.
- **Tests, in Node (2026-10-05):** the scorer, the room rule, `tbTheir`, the pitch text, the chips and room lines as strings, and the guard's checks are plain functions of data, so they run in `tests/test_js_trade_score.py` through the `node_js` fixture (no build, no browser, ~0.2 s for 18 tests). `test_trade_edit.py` and `test_trade_offers.py` keep what is drawn or clicked, in Chromium.
- **Keys:** an owner and a partner are team names as `LIVE_TEAMS` has them, the names in ff-jarvis's roster files; the
  offers are keyed by them, so a team renamed between a nightly run and a rebuild has no offers until the next night.
- **Judgment, not backtested:** a gain is a projection difference (ff-jarvis METHODOLOGY says as much), shown as one number.
- **Superseded 2026-10-05:** the sheets (`#lbsheet`, `#tbsheet`, their scrims and the `.lbs-body` scroller, which once
  shrank an 8-man lineup to five and a half rows) are gone; the pages scroll with the document.

## Clips (Roster, 2026-10-05)

NFL YouTube clips of the reader's own players, picked from a storyboard (A reel + B ring,
https://claude.ai/artifact/9C4vZYmMkhSKLyTHenWpEv). Embedded, never hosted or downloaded.

| Part | What it does |
|---|---|
| **Data** | ff-jarvis `clips.json` (`model/season/clip_match.py`), via `design/yt_clips.py` as `LIVE_CLIPS`. Best-plays videos are credited by title; other clips by Claude (sonnet) per game from the title, channel, post time, rosters with jersey numbers and the box score. Week 4 check: 9 of David's 9 TD scorers had a clip |
| **Week** | `LIVE_CLIPS.week`, never `schedWeek()` (that is the week coming up). The finished week stays up until the next kickoff |
| **Rail** (Roster redesign unit C, 2026-10-05, picked from the Roster storyboard) | Above the This week list, Sheet and Cards modes. **One card per starter** who has clips, best scorer first, two to a phone page and four from 760px, in a row the reader pages with ‹ › (a measured page: the cards that fit whole, so 2 at 360px) or swipes (touch scroll, a mouse drag, snap; STYLE.md's one exception to "no sideways scroll"). The card is a 16:10 picture of his first clip with his name (initials) left, his week's points right and his stat line under (the first clip's title when he has no week row) laid over its foot on a dark gradient, and a count chip top right (lime, play triangle and the number of his clips); nothing under the picture. A tap opens the theater on **his clips only**, from the first that plays. A card whose clips YouTube all refuses on other sites is a link to YouTube and wears the "YouTube ↗" chip where the count goes. Header on one line: "Week N plays", "N clips" (every clip once), **Play all** (the theater on every clip, from the first that plays; none when nothing plays here), ‹ ›. An end card, the same size, names starters with no clip and links their game's highlights. At 360x800 the card row is 101px high and the whole rail 146px. ~~One card per clip, 128×160 with a text block under each, the next card showing past the edge, "Play n", a disc and a duration on each card~~ (Clips v2, superseded 2026-10-05, storyboard https://claude.ai/artifact/Sg2r5qpzd9waPRi2U4Ptj4); ~~one card per starter, paged 2 to 4 at a time~~ (v1) came back with the picture's text moved over it |
| **Shape** | ff-jarvis tags each clip tall (a Short) or wide from the same `videos.list` call that reads durations; a tall thumbnail is YouTube's vertical `oar2.jpg`. ff-jarvis also keeps one copy of a play posted by both the NFL and the team, preferring the one that embeds |
| **Brief fold** | Below 1100px the This week list folds to its one-line form while the rail shows, so the first starter row does not drop. From 1100px the list is a side column and stays; the rail pushes the rows down by its height |
| **Ring** | Sheet rows only: lime ring and clip count on the headshot. The head opens the theater, the rest of the row the profile. Known exception: the head is a button inside a row that is a button; Tab and Enter reach it, a screen reader's browse mode may not |
| **Theater** (was the bottom sheet until Clips v2) | Full screen and opaque on `<body>` (`#clipsheet`): counter "2 / 4" and close on top, the video and its caption centred together, one bottom row ‹ Next: name ›. The box takes the clip's shape (9:16 at most 328px wide, else 16:9), cut by container units, never a guessed height. Nothing tappable under the video but that row: no clip list, no progress bars. Swipe sideways steps, pull down closes (outside the video: the iframe keeps its own touches). Runs the playable clips of the rail (or the ring's player) in order; after the last, an end card lists the YouTube-only ones as links. Where nothing can embed (file://, the Artifact frame) it opens on the end card |
| **One warm player** | `clipplayer.js`: one YT.Player for the page, every clip swapped in with `loadVideoById`. The first touch or scroll of the rail (or a press on a ring) preconnects, loads the IFrame API and builds it hidden. Nothing is cued ahead of a tap: on real YouTube a cue swallows the `loadVideoById` the click sends, and the clip stays cued. If the IFrame API script fails to load, the page stops embedding and the theater lists the clips as links. Measured 2026-10-05, desktop Chrome, 4 clips each: 889 ms tap to first frame with a new player per tap, 383 ms warm. If the browser blocks sound, the clip plays muted under a lime "Tap for sound" pill. Error 101/150 turns that clip's box into a link to YouTube |
| **Blocked channels** | NFL-channel, MIN, SEA and SF clips cannot be embedded (YouTube error 150, tested 2026-10-05 from the live site, from both youtube-nocookie and youtube.com; oEmbed answers 200 for them, so it cannot predict the block); ff-jarvis `model/clients/youtube_embed.json` lists them. Fan re-uploads (search.list `videoEmbeddable`) are pirated copies and are never used |
| **Live > TDs reel** (2026-10-05, storyboard https://claude.ai/artifact/5GZZ3GCcsp9znxzjiNrjKB, David picked A) | Feed mode, above Scored: the same rail and theater (`surface/teams/cliprail.js`, shared since then), cards newest first for the scorers the chips show, each card's second line his TD line. Clips are LIVE_CLIPS (this week only) plus fresh ones from `/api/clips`, deduped by id; an NFL-channel clip within 15 min of the scorer's own team's clip is the same play and drops. A card can be another play of a scorer's, not always the TD. No reel until a scorer has a clip |
| **Fresh clips** | `api/clips.py`: one channel per request (`?ch=DET`, the 32 nflverse codes or NFL), the uploads of the last 30 h at most 180 s long, with shape and embed, cached 5 min at Vercel's edge (`s-maxage=300`): every reader shares one YouTube call per channel per 5 min per region (2 quota units). A YouTube failure (quota included) is cached 60 s; a bad request or a missing key is not cached. The key is `YOUTUBE_DATA_API_KEY` in Vercel's Production env (set 2026-10-05), never sent to the page. `api/_yt_channels.json` is generated by `python design/yt_channels.py` from ff-jarvis's channel and blocked lists, held to them by a test. The page asks every 5 min, only while the TDs tab is on screen, for clubs whose game is live or ended under 1 h ago plus NFL, 4 at a time, and once on open when a game ended under 6 h ago. Replies merge by id and keep 30 h: the NFL channel posts 35 to 43 clips an hour on a Sunday, so its 50 newest reach back only about 2 h |
| **Matching a fresh clip** | From his team's or the NFL channel, posted after his kickoff. Other players' full names are blanked first ("Chase Brown" is not Ja'Marr Chase). On his own team's channel: last name, #FirstLast, a nickname, or his number opening the title ("88 in the end zone") or as "No. 88". On the NFL channel: first and last name, initial and last, #FirstLast or a nickname, never the bare last name ("let him cook"). Numbers and nicknames are `LIVE_NAMES` (`design/player_names.py`) from ff-jarvis's `player_names.json`, the one place a player's naming lives: jersey from Sleeper, nicknames seeded and learned from titles Claude credits, kept once seen in 2 different games and never a football word, a team name or another player's name. Week 4 (before these limits): last name 49 of 65 TDs with a clip, + hashtag 51, + jersey 54. A clip that plays here comes a median 12 min after the TD (46 of 75 TDs, 2026-10-05) |

Not built: clips on the Digest, Players > Highlights or the profile; a ring on trading cards.

## Waivers (a League leaf, 2026-10-05; a sub-tab of My Teams from 2026-09-16)

Waivers is a leaf of the League group beside Roster (My Teams merged into League on 2026-10-05); it began
as a Roster | Waivers toggle under the team name, not a sixth nav tab: waivers are per league like
the roster, so the league switch carries over. (The phone's bottom bar this protected became a
top nav on 2026-09-24.) A "Stream a D/ST" button above the rail opens Ranks on the D/ST tab (`rkOpenDst`,
`data/dst.js`): 3 taps from the Digest (League, Waivers, the button), 1 on a Tuesday. The data is ff-jarvis's `model.season.waiver_packet`, built daily by the refresh
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

## Ranks (Stats, 2026-09-26; D/ST and K 2026-10-05, plan U6c)

Ranks is a glance page: this week's projected rank at one position, in tiers, one row per player (face, game and
kickoff, injury tag, points; a desktop adds what the points are made of). Tabs: QB RB WR TE FLEX, then **D/ST**
and, in a Yahoo league only, **K**. One link out, **Schedule**, to the hidden leaf `schedule` (strength of
schedule, another unit's view; `navGo("schedule")`), top right of the headline on every tab.

| Decision | Why | Where |
|---|---|---|
| **D/ST and K are teams, so one panel, no tiers.** A row is a team: place (the file's rank), team, `vs`/`@` opponent and kickoff, this week's points; then one line of who holds it and the next three weeks as small cells (`W6 ~7.2`). 32 rows | tiers are natural breaks in a player list; a D/ST list is 32 teams in a 5-point band, and a break there would be noise | `surface/ranks/dst.js`, `css/surface/ranks/dst.css` |
| **The league is the reader's team's** (`lgFocusKey`, U8's one chip), **ESPN with no team picked**. Points are on that league's scoring (`LIVE_DST.leagues[lg].dst`: `dst_espn` or `dst_yahoo`). K is `leagues[lg].k`, null on ESPN (no K slot), so its tab is not drawn; a K tab left open when the team switches to ESPN falls back to RB | one place to say "my league"; ESPN's D/ST table is not Yahoo's, and The Madden Curse's K (distance ÷ 10) is not AYO's | `data/dst.js` `dstLeagueKey`, `dstTabs`, `dstPos`, `dstBoard` |
| **Rows are in ff-jarvis's rank order** (`rank[cell]`), byes last by team code. The page computes no points | the model's order is the board; a re-sort here would be a second model | `dstBoard` |
| **Who holds it:** MINE (lime), FREE (green), WAIVERS (grey: ESPN's `rostered.espn.waiver`, nobody's yet but only claimable, 2026-10-05), else the manager's team name; a **STREAMER** tag (lime fill) replaces FREE, since a streamer is free by definition. The flag is the file's (`streamer[lg]`: free, and top 12 that week); a team already kicked off is never tagged | the question is "can I add him"; one tag answers it | `rkHoldHTML`, `dstBoard` |
| **A week with `line: "rating"` is an estimate:** `~` before the number, a dimmer face, and a footnote under the list. A posted line has neither | the rating is this season's implied totals, not backtested (ff-jarvis 12.85) | `rkNextHTML`, `.rk-dc.est` |
| **One plain line on the model's gain:** "Mostly the opponent's expected score. The model's extra inputs cut the average miss by 0.02 to 0.04 points a game, so a close rank is a tie." (K: the team's own expected score, "by about 0.01", 12.85 measured 0.014 and 0.015; a cell the file ships as `baseline` says the model's extras are left out) | 12.85 passes 4 of 4 cells against the opponent's implied total alone, but the weekly order barely moves; the board must not read as sharper than that | `rkDstNote`, `ranks.dst.note*` |
| **Seven chips fit one row at 390px:** the Ranks position row takes a 6px gap and 10px chip padding (334px of chips and eight-pixel gaps overflowed 362px by 21px) | one row of controls (STYLE.md) | `css/surface/ranks/dst.css` |
| **`rkOpenDst()`** opens Ranks on D/ST, for a link in another view. The way in by name is Stats, Ranks, D/ST (3 taps); the Digest's Top 5 row is collapsed, so its Ranks link is also 3. Its one caller since 2026-10-05 is Waivers' "Stream a D/ST" button (`wvDstLinkHTML`): League, Waivers, the button = 3 taps from the Digest, 1 on a Tuesday, when Waivers opens first. A Digest link would make it 1 everywhere | the plan's "Stream a D/ST in 2 taps" needs a link in a view this unit does not own; the Waivers one is built, the Digest's is not | `surface/ranks/dst.js` |

Data: `LIVE_DST` (`design/dst.py`, a pass-through of ff-jarvis `dst_projections.json`; shape in its producer's
docstring, `model/market/dst.py`). Tests: `tests/test_js_dst.py` (Node: the league's cell, rank order, the
streamer flag, a bye, the estimate marker, K hidden on ESPN, the league rule), `tests/test_ranks_dst.py` (chips fit
one row, the tabs, the Schedule link).

### Running backs ordered by the books (2026-10-05, ff-jarvis METHODOLOGY 12.86 and 12.87)

The books' implied points for a back (`rank_pts`) order running backs better than our projection (weekly Spearman
0.527 to 0.551, 2024-2025 closing lines) but read about 0.5 high in level, so they **order and are never shown**.
Only backs were tested, against backs: every other position and FLEX order by `pts`. A back the books leave
unpriced beside a priced teammate scores about a third of his projection; ff-jarvis cuts his `pts` to 30%
(`unlined_backup`, `pts_before_unlined`) and the page tags him.

| Part | Rule | Where |
|---|---|---|
| RB list, tiers and rank | Sorted, tiered and ranked on `rank_pts` where a back has one, else `pts` (the roster cards' RB rank too). The number a row shows stays `pts`. A tier's label names its highest and lowest points, not its first and last row's | `design/projections.py` `order_key`, `design/ranks.py`, `rbTierSpan` |
| FLEX and other positions | `pts`, as before. A `rank_pts` on a non-back is never carried | `ranks.py` |
| Why a back can sit above one with more points | One sentence in the RB heading, only when the list is out of printed-points order (`rbReordered`): "Running backs are ordered by the sportsbooks' prices, which rank them better than our points do." Never on FLEX or another tab | `ranks.rb.note`, `rkRbNotes` |
| **No line** tag | An outline tag beside the injury tag on a Ranks row, under the name in a Start/Sit lane, and a note under the profile strip. Hover and screen readers get the tip; each view also says it in words once (the heading, under the call, under the strip): "The books priced a teammate, not him; backs like this score about a third of their projection." Three class names, one per view, because each CSS file is fenced to its own views | `rbNoLine`, `rbNoLineHTML`, `.rk-noline`, `.ssv-noline`, `.pf-noline` |

- **Data:** `LIVE_RANKS` rows and `LIVE_PROJECTIONS` players carry `rank_pts`, `unlined_backup`, `pts_before_unlined`,
  always present, null when ff-jarvis did not write them (an older file), for a non-back and with no points. The
  fixtures hold a back the books reorder (Breece Hall, points 15.0, books 16.6, over Chase Brown, 16.2 and 15.4) and
  an unlined backup (Kendre Miller, 3.1 points from 10.3).
- **One rule, two homes:** the build orders the list (`order_key`) and the page decides the Start/Sit call
  (`rbVerdict`): the same one-line rule, a back's `rank_pts` else `pts`. ff-jarvis's `rb_rules` block (its rank and unlined
  settings) is not read.
- Tests: `tests/test_js_rbrules.py` (Node: the order key, the call, the reorder test, the tier span, the tag and notes),
  `tests/test_ranks.py` (the build's order, tiers, rank, FLEX untouched, the fields; the Ranks list, notes and tag; the
  strip's tag), `tests/test_startsit.py` (the picker's call, note and tag).

### Floor and ceiling (2026-10-05, plan U5)

Every projection has a band: `floor` and `ceil`, the 10th and 90th percentile outcome in half-PPR points, given he
plays, so 8 in 10 of his games land between them. ff-jarvis `model/market/ranges.py` writes both on every
`player_projections` row (empirical quantiles of actual minus projection by position and projection bucket; holdout
on 2025: 82.3% inside, QB 74.6% too narrow, RB 81.8%, WR 84.8%, TE 82.1%). **A description, not a price**: it moves
no rank, tier or START/SIT call, and the page never computes one.

| View | Where | Words |
|---|---|---|
| Profile strip | `8.4–28.8` under the lime projection's "Proj." label (`.pf-lede-r`) | one line under the strip, the one string (`range.note`) every view uses: "Range: 8 in 10 of his games land here, if he plays." |
| Ranks row | small grey line under the points, above the matchup tag (`.rk-rng`); the points column is 72px on a desktop (was 56) | one sentence added to the list's subtitle |
| Start/Sit picker | under each lane's big number in the Projected row (`.ssv-rng`) | one note under the row's label, not one per player |

- **One source.** `rangeFrom(row)` and `rangeFor(p)` in `ui/player.js` beside `projFor`: the file's two numbers and
  their text, else null. Ranks rows carry `floor`/`ceil` themselves (`design/ranks.py`), the cards and the profile
  read LIVE_PROJECTIONS; one file feeds both, so a player's band is the same everywhere (fixture, Joe Burrow: 19.4,
  8.4–28.8 in all three).
- **Nothing drawn, no note, when there is no band:** a ruled-out, played or bye player (his `pts` is null, and
  `design/projections.py` nulls `floor`/`ceil` with it), a position the table does not cover, a file from before it,
  and a 0 to 0 band. The profile strip's Out, Played and Bye cells never carry a range.
- **Not drawn:** D/ST and K (no band), the Compare cards, the roster rows.
- Tests: `tests/test_js_range.py` (Node: the file's numbers, out/played/null/0-0 show nothing, the strip cell),
  `tests/test_range_view.py` (the same band in the three views, the note once, no band no note, 360px),
  `tests/test_ranks.py` (the build carries the fields). The fixtures hold real bands: ff-jarvis's shipped table applied
  with its own `ranges.apply` to `tests/fixtures/data/player_projections.json` and `tests/fixtures/feed.json`.

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

### Role (leaf `movers`, 2026-09-29; superseded: Movers, share cards by team)

Movers showed whose target or carry share moved, one card per team. Superseded 2026-09-29 (David:
"target share is just half the story"; the profile already carries share). The quadrant with
"buy low / sell high" corners described here before that was retired even earlier: METHODOLOGY
12.41 found buy-low no edge, and 12.44 that the gap does not beat our projection.

Role (storyboard https://claude.ai/artifact/DQK7e9SEqgdmLL8joh1fYu, option A) ranks RB/WR/TE by
what their work is worth a game: what an average player at the position scores with the same
targets, carries and passes (ff-jarvis `role_board.json`, the recap's expected points). `LIVE_ROLE`
(`design/role.py`) keeps 2+ games and 5+ a game; `js/surface/role/role.js` draws it.

| Row part | What it shows |
|---|---|
| Top line | face, name, position (tint), "20.5 → 29.8": the work's worth, then what he scored |
| Dumbbell | both on one scale shared by every row on screen; hollow = worth, filled = scored, green over, red under |
| Work | carries, targets, air yards, then scoring chances (inside the 5, else red zone) beside his TDs |
| Last season | the same gap in 2025, or "no 2025 season": the line that separates skill (JSN +3.8 in 2025) from a hot month |

- **Descriptive only.** No row says buy, sell or luck (`test_role.py` checks the words). The rank,
  his workload, is what carries forward; the gap has not predicted points better than the projection.
- **Touchdowns sit beside their chances**, not split out as luck: a goal-line back's TDs are his
  job (David, 2026-09-29: "TDs isn't always lucky").
- **The expected points price every target alike** (a flat rate per position); where a touch
  happens is not in the number yet, so the work line shows it. Weighting it is an ff-jarvis change
  that needs its own backtest.
- **Layout.** A phone: one list, 20 rows then "Show all". From 1100px, two columns read down then
  across, as Ranks' tiers do. `#movers` and the old `#pool` open it.

**The pool stays** (`LIVE_POOL`, `design/pool.py`, `data/pool.js`): the profile's points-per-game
rank reads it.

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
| Lead | until the week's first kickoff (the top scorer takes it then, see "After kickoff"), ff-jarvis's pick (`lead.rule`): a hurt starter, else a game in bad weather, else the top headline. A headline, one fact line ("The WR2 this week. Hip. LA @ DEN, Sun 5:20 PM."), the photo; weather draws its wind or rain mark instead. No stats row |
| Hurt | red count; the next two who will likely sit, then how many are questionable |
| Starters | count; the newest new #1 on Sleeper's depth chart ("Keenum QB1 over Williams") or team move with his new depth ("MIN → NYG · QB3"); empty, Blip asleep and one of three short lines (`surface/digest/blip.js`, pose "asleep", 2026-09-29). Opened: each with a green up mark (new #1, the old one's status in brackets) or sky arrows (new team), the weekday at the right. The foot quotes `rules.starters`. On the wall it sits under Hurt. Since 2026-09-29 |
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

**Recap leaves the Digest (2026-10-05, supersedes every Results, results-banner and Waiting paragraph
below; they stay as the record of the shapes Recap now draws).** David: "we probably need a recap section
for the week instead of dumping it into the Digest. The Digest should be a curated list of content for
readers to enjoy and not just a results section that stays there for the whole week and quickly become
stale." This week > Recap (leaf `weekrecap`, hash `#weekrecap`, `surface/recap/`, from `LIVE_RECAP`,
`design/recap.py`) holds the week. Storyboard: `recap-storyboard.html` (section 1, what leaves).

| Left the Digest | Where it went |
|---|---|
| The results banner (rule 3 of the lead; `dgLeadRes`) | Recap's banner. A packet whose `lead` is still "results" now falls to the top headline, else the quiet banner (`dgLeadAfter`) |
| The Results row: each position's top three, Smashed, Busts, Left hurt (`dgResBody`, `dgResTabs`, the `res` tabs and wall columns) | Recap's leaders board and three lists |
| The "Waiting on week N" card (`wait.js`, `wait.css`) | nothing: Hurt and Matchups still leave the ticker once the week is over (`dgWaiting`), and Need to know says the report is still to come |
| Monday's day-open Results row (`DG_DAY[1]`) | nothing: Monday opens no row |
| Packet fields `finals`, `pending`, `stars`, `smashed`, `busts`, `left` (`design/digest.py`, `contract.py`) | gone; `digest._left` stays, `design/recap.py` imports it |

Kept under their names for Recap, in `surface/digest/parts.js` (`dgStatLine`, `dgBoardHTML`, `dgWhy`,
`dgLeftPills`, `dgOutPill`, `dgPill`, `dgResRow`, `dgResNum`, `dgResFace`, `dgCap`, `dgGames`) and `lead.js`
(`dgCall`, `dgBoxPills`, `dgTopLine`). Their styles, `results.css` (rows, pills) and `headlines.css` (board),
are fenced to both views. A `LIVE_RECAP` row has no `why`, so `dgWhy` needs one added upstream before Recap
can pill a smashed or busted player. Still the Digest's: `dgCap`, `dgGames`, `dgResFace` and `dgResList`
(facts, need, the weather line, Tonight), `tabs.js` (Top 5), and `dgMuNone` (moved into `digest.js`).

**The Recap row (2026-10-05).** One 52px ticker row, first in the ticker, in the other rows' shape: the
Recap icon and label, the week ("Wk 4"), the week's top scorer and Claude's picks ("J. Allen 285 yds · 3 TD",
"Claude 5 of 8"), an arrow. It is a link (`<a href="#weekrecap">`), opens nothing in place, and on the wall
is a full-width band. No fantasy points: David, 2026-10-05, Digest headlines show yards and TDs, never
points, since every league scores differently, so the scorer's day is `dgStatLine` of `LIVE_RECAP.top`
(just his name when the recap has no box line yet; Claude's part is `preview_record.su`, "5-3" read as 5
of 8, left out when null). On a 360px phone the two parts wrap onto two lines inside the 52px.
**When it shows** (`dgRecap`, `data/digest.js`): `n_final * 2 >= n_games` of the recap's week, until the
end of the first Wednesday after that week's last kickoff (local midnight into Thursday, the reader's own
day); then it hides, and with no kickoff to count from there is no row. Measured on the fixture
(2026-10-05), at 360px, Monday with Sunday final: the Digest is 1,634px, the Results row's open card
having made it 1,921px (340px closed to 53px, 287px shorter).

**Results (2026-09-29, storyboard https://claude.ai/artifact/7gsPHebT4xTdo36N1QqqWD, option B;
superseded 2026-10-05, now Recap's).**
Every row is one shape: a 40px face, the name over its reason pills, the points over the projection
(Live's stack). The gap ("+14.9") is not printed: the list's name says which way, the pill says why.
The wall puts the top scores and the lists on the same four columns, Left hurt spanning two and read
down, so a number sits within ~300px of its name; before, two half-page lists put it ~600px away.
A phone sets the top scores two by two and stacks the lists. Faces went to 80px the same day (storyboard
https://claude.ai/artifact/S2fqkyWck5jtR4P6KFWdQi: at 40px you saw a jersey, not a player); a phone's
top scores become tiles (face over name over points), since a row beside 80px leaves a name no room.
Reasons lost their boxes the same day: thirty outlined pills made the card busy, so a reason is
coloured words parted by a dot, and only how long he is out keeps a filled red box.

**Results became headlines (2026-09-29, storyboard https://claude.ai/artifact/FYQES3vMxJ8ukZm7gLNNih,
option B; supersedes the top-scores grid above; the whole card superseded 2026-10-05, now Recap's).** David: "I don't like it". The card said scores with
no reason and two grids with two meanings.
- **Four tiles:** Top score, Out of nowhere (the biggest smash), Dud (the biggest bust), Carted off (the
  left-hurt player out longest). Each is a filled box with a face, one number, the name and one line
  of why. A player is in one tile at most, and when the banner is the week's top score the first tile
  is the Runner-up (David, 2026-09-29), so the page never says Gibbs twice.
- **The board:** each position's top three. A phone gives each position one line (name and points); the
  wall gives it a column of rows with a 36px face and the player's day ("297 yds · 4 TD · 34 rush").
- **The lists stay folded on the wall too:** Smashed, Busts and Left hurt three across, each a toggle.
  The tiles tell the week; the lists are the detail.
- Measured: desktop card 612px -> 499px; a phone's opened card 841px -> 803px.

**The results lead, called like a game (2026-09-29, storyboard
https://claude.ai/artifact/BvceuqtTkqyvzgjiHPGK7g; superseded 2026-10-05 as the Digest's banner, `dgCall`
and `dgBoxPills` stay for Recap's).** The week's top score is an announcer's call on
his real box line (ff-jarvis `results.*[].line`, from the cached play-by-play): "Gibbs rumbles for 164
yards and 3 TDs". The kind of call follows his day: 10+ throws is a passer, more rushing than
receiving a runner, else a catcher; three or more TDs on under 80 yards a goal-line day. Each kind
has four phrasings in `content.json` (`digest.call.*`: slings, airs it out, carves them up, lights it
up; rumbles, runs wild, bulldozes, churns out; ...), picked by his name and the week, so a reload
never reshuffles and next week reads fresh. A Claude-written line is the next step if these repeat. His box line sits under it as
pills (points, passing, rushing, receiving). The band is washed in his team's colour and the team's
code sits outlined behind him on a wide screen: a colour and a code, never a logo, so it survives a
public site. No projection, no TD luck, no "RB, DET" (David: the headline celebrates). Without a box
line yet it says "Allen scores 24.6".

Not backtested: Weather, Stock and Gems. Each says "Not backtested." in amber on its opened foot,
never on the closed line: the closed line is the fact, the caveat is for whoever reads on. Lead copy
for the weather and news rules has no real week yet (2026-09-26).

**The wait (2026-09-29; the card superseded 2026-10-05, Hurt and Matchups still leave the ticker, nothing
stands in for them).** Once every game of the packet's week has kicked off and Tonight's card is
gone, Hurt, Matchups, Weather and Top 5 have nothing left to preview until Tuesday's run. They leave
the ticker for one card, "Waiting on week N", with Blip (the mascot, `surface/digest/blip.js`) and one
deadpan line each; on the wall it sits in one row with Waiver adds, Risers & fallers and Gems. It
replaced about 1,000px of desktop panels saying "Nothing new". Storyboard:
https://claude.ai/artifact/UDoWgLMrzUHup5tX53zaue (option B). Top 5 links to Ranks, the same
projections for every player (it linked to Leaders until then).

**Six fixes (2026-09-29, storyboard https://claude.ai/artifact/Ms6FbdvynVPoRTKEidPGAz; David picked
1B 2A 3A 5A 6A, and cut 4).**
- **Risers & fallers cut (4):** its move (the books' implied points against his last game) cleared its
  0.5 bar for 45 of 64 priced players in week 4, only 11 moved past one sector's usual wobble, part
  of every move was the opponent changing, and it failed its backtest (ff-jarvis METHODOLOGY 12.46).
  The Stock row in the table above is superseded; Role reads a changing role from the work itself.
- **Board (1B; moved to Recap 2026-10-05):** each position a display heading (`--t-5`, `--t-6` on the wall) over rows of name, his
  day and points; no faces (the tiles keep them). Two positions a row on a phone, four on the wall.
  K and DST would take the same shape; ff-jarvis's results carry QB-TE only.
- **Lists (2A; superseded 2026-10-05, moved to Recap):** on a phone Smashed, Busts and Left hurt are one panel under one tab bar (`tabs.js`),
  counts in each list's colour; three toggles side by side read as one panel. On the wall, after three
  rounds the same day ("too wide", "expand and shrinks the container", "still looks weird", "the tab
  list to be awkward"), there are no tabs: all three lists are open on the board's four columns, each
  under a heading in the board's type and its list's colour (Smashed under QB, Busts under RB, Left
  hurt across WR and TE, read down two), entries leading with the points. A 1,600px card has room for
  all of them, so tabs there hid twelve of seventeen to solve a phone's problem. Top 5 keeps its tabs,
  in a fixed box.
- **Top 5 tiers** wear Ranks' colours: Tier 1 filled lime, lower tiers an outline stepping to grey.
- **Matchups with nothing to call** says one of three deadpan lines (`digest.wait.mu1-3`), not the record.
- **Starters folded into News** (David: "merge starters"): a new #1 or a team move is a News block before
  the headlines, tagged "New QB1" (green) or "New team" (sky), its line over whom; News counts it and its
  closed line leads with it. The Starters row, empty most days (a full-width Blip-asleep panel on the
  wall), is gone; the Starters row in the table above is superseded.
- **Icons (3A):** a 16px drawn icon before every topic's label (`icons.js`), stroked in the label's colour.
- **Top 5 (5A):** reads `LIVE_RANKS`, the rows Ranks draws, under QB RB WR TE FLEX tabs: place, name
  over his game, injury tag, tier, projection. The packet's top5 emptied once its week began, so the
  wait card said "projections land Tuesday" while Ranks already had next week.
- **Weather (6A):** reads the Weather view (`wtRows().moves`, games still to come): "Rain in 4 games",
  each game opened, a link to Weather. A calm week draws no row on a phone and one sentence on the wall.
  The packet's 15 mph / 50% list was a second rule beside the tab's backtested one.
- Top 5 and Weather left the wait card; on the wall they share its row.

**After kickoff (2026-10-04, storyboard https://claude.ai/artifact/JrM6hBMrAL2hjFzYPgKitV, option A).**
David: "Sometimes something big happens like injury or top scores. The headline should change
accordingly. Need to know and Highlights become old news on kickoff." The packet leads until the
week's first kickoff; from then the Digest shares Live's poll (`surface/digest/now.js`).

**Highlights left the Digest (2026-10-04, David: bored of it).** The section (each Players view's
first line, a tile each, a foot to the tab; named Worth knowing until 2026-09-30) is gone, with its
fallback of one fact each from Role, the Grid and Takes and its copy keys. Players > Highlights
(the Reel) is unchanged. Before the first kickoff nothing stands beside Need to know, so on the
wall it takes the whole band (`.dg-ticker.no-facts`, `need.css`).

| Part | Before the first kickoff | From the first kickoff |
|---|---|---|
| Headline | ff-jarvis's pick (`lead.rule`) | the top scorer so far, called by his yards and TDs ("Gibbs: 170 yards, 1 TD"; the 2026-10-04 "has 31.4 points" wording is superseded, see "The top scorer's call"); his box line and the game's clock under it, his team's colour behind him, a tap opens his profile |
| Right now (the old Highlights section, removed before kickoff 2026-10-04) | nothing | three rows (hurt starters first, then the top scorers: face, name, position, club and clock, line, points; five rows until 2026-10-05), then a foot: More on the left opens the rest in place (`DG_NOW_SHOW`, `data-dgmore`; kept while the page is open), the day's touchdown count on the right opens Live's TDs tab |
| Need to know | new starters and who sits | only games not yet started (`dgCut` drops a game's pre-game rows at its kickoff); gone when nothing is left |
| Tonight's card | the slot's preview | unchanged, except the last game's card (below) stands in for it |

- **Hurt starter lead holds** while no game is on and his own has not kicked off: no live injury
  source exists yet, so nothing live knows who got hurt since. Once a game is on, the top scorer
  takes the banner (superseded in part, same day: a player who leaves a game hurt beats the top
  scorer, see "Left the game hurt" below).
- **Numbers** are `/api/stats` `lead=1` (league-wide, half-PPR), the same reply Live and the
  profile read. The page adds nothing to it. A passing TD is the same score as the catch, so the
  count is rushing plus receiving TDs.
- **The poll starts only after the week's first kickoff** (`dgKicked`). A Tuesday's Digest asks
  neither `/api/stats` nor ESPN. Live parts repaint in place (`paintDigestLive`); only a change of
  phase (a section appears or leaves) renders the view again.
- **The Monday night card** (`mnf.js`, "the last game", David 2026-10-04: "The Monday game needs to be
  its own section"): once every game before the week's last day is final and one or two games
  remain, a card sits above the ticker and stays through the game. It is the game itself, generic,
  the same for every reader (rewritten 2026-10-04, below). One block per game, each opening with a
  line, "5:15 PM · NO @ ATL" (its clock mid-game, "Final" after):
  - before kickoff: each side's two best projections (QB/RB/WR/TE, `LIVE_RANKS`), name and number;
  - mid-game and after: the score (Sleeper's, `gdClubScore`) and the game's top three scorers from
    `GD_STATS.lead`, name and points.

  The headline before the game is the between-windows one, the week's top scorer ("St. Brown leads
  the week with 31.4 points"). The wait card does not start while this card shows.
  - **One 80px block per game (2026-10-05, storyboard https://claude.ai/artifact/ArF53Lvh12QV8fbL3mr9KP).**
    The 300-450px card above (projections before kickoff, three scorers after, a header and a foot link) is
    superseded. The whole block is one button that opens the game's sheet, the one Live's NFL tab opens
    (`dgMnfGame`, `data-dgblk`). Line 1 the day and the clock ("MON · Q3 4:12"; before kickoff "MON 8:15 PM ·
    ATL @ NO"), line 2 the score in mono ("ATL 17 · NO 21"), line 3 the game's top performer in yards and
    touchdowns, never fantasy points (`dgMnfNums`, `dgMnfTop`). Before kickoff there is no score and no
    line 3. Tonight's card draws the same block once its game is on (`dgMnfFor`, `tonight.js`), so a
    Thursday game reads like a Monday one; a poll repaints each block in place by its home club. From 960px
    two games sit side by side, each at most 560px wide.
  - **Superseded 2026-10-04** (David, the same evening: "The Digest is supposed to be GENERIC for the
    public. It shouldn't hone on to my roster or their roster."): the first card drew the reader's
    matchup in each league (both scores, who was left to play, "what the result needs", the median gap)
    and the headline "You're up 1.6 going into Monday night". Nothing in `surface/digest/` or
    `data/digest.js` reads `GD.leagues`, a roster or a matchup now; `test_digest_live.py` greps for it and
    asserts no league, team or opponent name reaches the page. Live is the personal view.

**Left the game hurt (2026-10-04).** While games are on, any QB, RB, WR or TE the projections rate 8 points or more this week, in any game, who left it ("B. Purdy left the game hurt", by-line "{club} · Q3 4:12") takes the headline from the top score and leads Right now in `--down`; the best projection if several (three rows at most); when "has returned to the game" is read, the top score is back. Live's Matchup row wears a red Hurt chip when one of mine is flagged. Source: the play text of ESPN's game summary, fetched by the reader's browser for every game that is on, each at most once per 180 s, one request at a time (`data/gameday/hurt.js`); the players to watch are `LIVE_RANKS` rows at 8 points or more, which keeps defenders and special teams out. ESPN's wording ("was injured during the play", "Injury Update: X has returned to the game") is nflverse's and was unverified on ESPN as of 2026-10-04: check Monday ATL @ NO.
- **Superseded 2026-10-04** (David: "The Digest is supposed to be GENERIC for the public. It shouldn't hone on to my roster or their roster."): the first version watched only my starters in my leagues, asked only for games that held one, every 120 s, and the by-line named my team in each league.

**Claude's story between games (2026-10-04).** David, after Sunday's games: the headline was "old news"; "claude should determine what is the best headline from Sunday's results, Injuries, etc". ff-jarvis's `digest_headline` step writes one pick (head, fact, kind result / injury / news / preview, the player and club it is about, an `asof`), number-checked and generic; `design/digest.py` keeps it as `LIVE_DIGEST.story`, only when its season and week are the packet's, and `sources.load_digest_headline` reads the feed block first, the file second. The banner order (`dgLeadLive`, `now.js`): a game in play keeps the live hurt or top-scorer lead; with no game on, the story takes the banner when its `asof` is newer than the packet's (both Pacific wall clock, `dgLeadStory` in `lead.js`); else the old rules. **Since 2026-10-05 a result story about the Recap's week and top scorer is Recap's banner, not the Digest's** (David: "they should never be the same content"; `data/leadsplit.js`): with no game on, the Digest then leads with the coming week, the packet's own lead (`dgLeadPacket`), and whatever it leads with never names the Recap banner's subject (`lspPick`). A story about anyone else, or of another kind (injury, preview), stays the Digest's. The head is the headline (a sentence, so the smaller size), the fact sits under it, a player draws his face on his club's colour and the band opens his profile; a preview with no player wears the club's colours, or sits quiet with none. The club's colour wash wins over the kind's (red injury, lime result), which only shows when no club is known. Every word is escaped; nothing in it is the reader's. Pinned by `tests/test_digest_story.py`.

**The top scorer's call (2026-10-04).** David, on "McMillan leads the week with 38.2 points": "38.2 is insane number in fantasy... Should be like NFL announcer to build the hype." The live and between-windows banner (`dgTopCall`, `lead.js`) scales with the day: big at 30+ points, 3+ touchdowns, 150+ yards (300+ passing), with "laps the field" when he is 10+ points clear of the second score; solid at 20+; plain under that. Two phrasings per tier, in the present while his game is on and the past after, fixed by his slug so a poll never reshuffles them. Only facts the page has; no caveats.

**Superseded 2026-10-05: the printed points.** David: the headline "should use yards and TDs" (every league scores differently; ff-jarvis's Claude-written headline already never prints points). The tiers are still chosen by points, which no longer print. The head carries his real line from `GD_STATS.lead` `s` (`dgTopLine`, `lead.js`): a passer's passing yards and his passing plus rushing TDs, anyone else's rushing plus receiving yards and TDs, catches first only at 10+ ("McMillan laps the field with 14 catches, 192 yards, 2 TDs", "St. Brown ERUPTS: 180 yards, 2 TDs", "Skattebo is rolling: 104 yards", plain "Higgins: 87 yards, 1 TD"; "1 TD" singular). A scorer with nothing to count (a kicker, a defense) is said without a number ("Butker is out in front"). The by-line under it keeps his full box line and the game's clock, which adds what the head leaves out (completions, targets); Right now keeps its points column, a table and not the headline.

## Recap (This week, 2026-10-05)

The week's results, league-wide and public: who went off, how every game ended, how Claude's calls did.
Leaf `weekrecap`, hash `#weekrecap`, second in This week (`recap` is League's). Storyboard, option C
(David: "otherwise that is a lot of scrolling"): https://claude.ai/artifact/HVdkEL4YbiBKUJ3QbLH9gf.
`LIVE_RECAP` (`design/recap.py`) cuts ff-jarvis's `data/recap/<season>-wNN.json`: the newest week with half its
games final (the Digest banner's rule, so Monday morning shows Sunday). It reads no roster, matchup or league;
the file's `leagues` block and each player's `rostered` and `slot` never cross (`tests/test_recap_data.py`).
Code: `surface/recap/` (prefix `wr`), CSS `css/surface/recap/` fenced to `weekrecap`.

**The banner says Claude's story (2026-10-05).** When ff-jarvis's finished-week story (`LIVE_DIGEST.story`,
kind result) is about the week's top scorer and the Recap holds a played week, the banner's headline and fact
are the story's words, in place of the template call (`wrBannerHTML`, `lspRecapStory`); the Digest then does
not carry it (DESIGN.md "Claude's story between games"). The words are number-checked upstream and drawn
escaped; a story headline is a sentence, so it takes the smaller `long` size. No story, or one about someone
else: the template call and box-line pills, as before. On a phone the Recap's four tabs open in the tab row.

| Part | What | Data |
|---|---|---|
| Banner | the week's top scorer called like an announcer ("Allen slings 285 yards and 4 TDs"), box line as pills, washed in his club's colour, its code behind him from 1100px. "Week 4 · top score so far" until the week is complete. Yards and TDs in the head, never fantasy points (David, 2026-10-05: every league scores differently). A tap opens his profile | `LIVE_RECAP.top`; the Digest's own `dgCall`, `dgBoxPills`, `dgPhotoHTML`, `dgGhostChars` on the same `.dg-lead` panel |
| Tab bar | Players / Scores / Claude / Accuracy: Live's `.gd-tabs` (`live.css` is fenced to both views), one column per tab that has data. Choice in `localStorage` `tw-recap-tab`, never the hash; a tap repaints the body in place. A tab with nothing hides; with one tab left the bar hides | `wrAvail` |
| Players | Leaders (QB, RB, WR, TE, K, DST: top three each, two columns on a phone, three from 960px); Smashed / Busts / Left hurt (one list under a tab bar on a phone, all three side by side from 960px, no bar); Touchdowns (a dot per rushing, receiving or return score, top five then Show all, one line for the most passing TDs) | `stars`, `k`, `dst`, `smashed`, `busts`, `left_hurt`, `tds` |
| Scores | a strip ("Claude picked 5 of 8 winners · 5-3 vs spread"), then every game under its kickoff window (Preview's `pvWinLabel` and `preview.win.*`; `wrSlot` ports `design/preview.py` `_slot`, Eastern time through `Intl`): winner bold; at the right "Picked CLE" and Hit or Miss; a game still to play shows "1:00 PM ET" and the pick. A game opens Preview's dossier when Preview holds the same week and the game matches by away and home; otherwise the row is plain text. From 960px windows of one or two games share a row, longer ones span it | `games`, `preview_record` |
| Claude | three tiles (winners, vs spread, over/under), the best call (a winner picked against the market, the biggest line first, else the longest shot) and the worst (the surest miss), a link to Preview's every-week record | `preview_record`, `games[].preview` |
| Accuracy (since 2026-10-05) | the fourth tab: one line saying what it measures ("Average miss in points, on players both of us projected. Lower is closer."), then a card for the season to date and one per graded week, newest first. A row per position (QB, RB, WR, TE; the season card adds All four): our average miss, FantasyPros' on the same players, and who was closer ("Ours" lime, "FantasyPros" amber, "Tie"), the smaller miss bold. A week's header names the model live then ("before the line blend" weeks 1-4, "with the line blend" from 5) and the file's note when it has one. The season card says by how much and the 95% range ("by 0.41 · 95% range 0.12 to 0.70 · clear gap", or "within noise" when the range holds 0). Misses stay in the report (FourthDown Lab's receipts idea, not its look): FantasyPros' wins draw as plainly as ours. Hash `#accuracy` opens Recap on this tab (`state.js` rewrites it to `#weekrecap`; nav.js knows only leaves) | `LIVE_ACCURACY` via `design/accuracy.py` (ff-jarvis `accuracy.json`); `data/accuracy.js` `acView`, `surface/recap/accuracy.js` |

- **Exception to STYLE.md "one job per view" (2026-10-05):** tabs, like Live's (2026-10-04). Three questions on one page measured 2,265px at 360px wide; with the bar the tallest tab is Players at 1,523px (Scores 1,348px; Claude fits one screen), measured on the fixture.
- **Cards (Material's rule):** Leaders, the three lists, Touchdowns, Every game, Claude's week: one card per subject, rows inside, none nested. Faces stay in the banner; lists scan by name.
- **Empty states:** no recap file is one line ("No recap yet"); a section with no data is not drawn; no zeros (no record, no tiles, no strip). An old recap file (weeks 1-3) has only its finals and no picks, so Scores shows them with no pick or grade.
- **First data (360x800, fixture):** the bar at 287px, the first card at 339px, over STYLE.md's 200px: the banner is the page's headline, as the Digest's is (a photo makes it 270px).
- **Smashed and Busts** are ff-jarvis's own picks (`smashed`, `busts_shown`), the Digest's lists, never a cut made here.
- **Accuracy never computes (2026-10-05).** Every number is ff-jarvis's, copied from its grade files and scorecard; the page only picks which of two printed misses is smaller. A field the file has as null is a sentence, not a zero: weeks graded before the rank fields shipped say "Rank order and top hits were not graded this week."; a null `season_to_date` says "Not available yet. The season line appears once the scorecard has run."; a null range says "no range yet"; a week the files hold but have not graded says "Week 4 is not graded yet."; a season line behind the weeks says so. With no `accuracy.json` the tab hides, like any empty tab. Order, a card per week and the two-across desktop pair follow the Recap's other tabs. Not measured against the 200px first-data budget: the tab sits under the banner and the bar, like the others.
- Tests: `tests/test_recap_view.py`, `tests/test_accuracy_view.py` (Node: the cut and the card against the fixture's digits; browser: the tab, `#accuracy`, the hidden tab); golden states `weekrecap`, `weekrecap-busts`, `weekrecap-tds-all`, `weekrecap-scores`, `weekrecap-claude`.

## Start/Sit (This week, 2026-10-03; was Takes; v3 2026-10-04)

The weekly question, "A or B?", then what we would call. Storyboards: v1
https://claude.ai/artifact/HUVUoVRF3wG6XCxQ3LxHuT (David picked option C); v3 (2026-10-04) option C
"Against his average" plus option B's SMASH card. David: "SMASH, START, SIT for only those we have
confidence in. No coin flips." Our own projections only: FantasyPros and Pitcher List never define a
call and appear only as a for-fun line of the record. Rule: ff-jarvis METHODOLOGY 12.75. Top down:

| part | what | data |
|---|---|---|
| Picker | 2-3 players; START for the higher projection, Coin flip within 0.5 pts (judged at the one decimal shown). **Running backs (2026-10-05, METHODOLOGY 12.86):** when every player compared is a back with a books number (`rank_pts`), the call and the coin flip follow that number instead, the gap printed stays in points (none when the books' pick has fewer points), and one sentence says why ("Running backs are ordered by the sportsbooks' prices...") only when the call differs from the points'; any other pair, or a back the books skipped, follows points. A back the books left unpriced wears a "No line" tag under his name, with its meaning under the call (see Ranks). Rows: projected, rank, defense vs his position, FantasyPros, teammate out, weather, his row in Usage (a link, `navGoRow`). The saved picks and the saved slips are both keyed by `schedWeek()`, the one page week (2026-10-05; the slips were keyed by the props' week, `SLATE_WEEK`, until then). Opens on the reader's closest bench-vs-starter call (`briefPairs`, shared with the brief) **only when he has picked a team** (`lgMine`); with none it opens empty, the search open and focused, and stays open until two are picked (2026-10-05, plan U3: it handed a first-time visitor David's pair, 8 taps from his own; now Start/Sit, a name, a name is 3). Picks kept for the week they were made in. When FantasyPros' ECR puts the loser ahead of our START, the row says so in one sentence (the call is the projection, not expert opinion; `ssFpCheck`, a coin flip never contradicts) | `LIVE_RANKS`, `LIVE_DEFENSE`, `LIVE_SSB.fp/out`, `LIVE_PROJECTIONS.wx` |
| Board | QB/RB/WR/TE tabs: each position's best spot (ff-jarvis `best`), then the four offenses facing the softest and toughest defenses, a bar against the league average | `LIVE_STARTSIT.best`, `LIVE_SSB.board` |
| Record | three tiles, SMASH, START, SIT, each its own hit-miss since week 5 (a void count beside a tile only above zero); under them, small, FantasyPros and Pitcher List hit-miss "for fun". Before a week is graded: "No week graded yet." in place of the tiles | `LIVE_SS3.record` |
| SMASH | one card: every player we project top 3 (QB, TE) or top 6 (RB, WR) at his position, in position order. Row: head, "P. Nacua", "WR2 · LA @ PHI · Sun 1:25 PM", the book's main yardage line over the TD price ("72.0 rec yds", "TD +135"). A player no book prices shows what he has. Foot: Build in Slips | `LIVE_SS3.smash` |
| Bold calls | one card, a Start group then a Sit group: our rank and his season-average rank disagree across the position's starter line by 6+ spots. Row: START/SIT tag, head, name, game and kickoff; right "WR16" bold over "avg WR41". A tap opens the reasons (green chips) and the profile link. An empty group is not drawn; none at all is one quiet line | `LIVE_SS3.takes` |
| Last week | "Week 5: how the calls did": a Hit / Miss / Void word, the name, the call and where he finished; a void call (ruled out after it froze) has no finish and is not in the record | `LIVE_SS3.record.last_week` |

- **One job per view still holds:** every part answers "who do I start this week".
- **No calls at all** (ff-jarvis has not posted the week, or no `startsit_v3` block yet): Blip says so in place of the two cards; the picker, board and record still draw. The build treats a missing block as an empty week (`design/startsit_v3.py`), never as an error.
- **Cards:** one card per subject, rows inside, none inside another (Material cards rule). SMASH and Bold calls sit side by side from 960px when both hold rows, `--list-w` wide, each card 560px or less when alone; at the fixture's 10 rows against 9 they end within 30px of each other (STYLE.md: within 150px).
- **Colour:** SMASH is lime, START green, SIT red (the Takes' one rule: green and red are start and sit). The result words on last week's list are Hit green, Miss red, Void grey.
- **Measured 2026-10-04 at 360x800** (fixture): the record's tiles are 64px; a call row is 52px, or 63px when its meta line wraps to carry the kickoff (the name stays one line). The picker and board lead, so the record is not the first data; the page was already over the 200px budget for them.
- WR defense matters little (METHODOLOGY 12.29, 12.70) and teammate out is a reason only (12.55, 12.71), as before.
- The This week sub-row's gap went 20px -> 16px at 760px and under, site-wide, so six views fit 332px at 360.
- **Data:** `design/startsit_v3.py` cuts ff-jarvis `startsit_v3` (feed block first, `data/startsit_v3.json` second; `sources.load_startsit_v3`) into `LIVE_SS3`: SMASH in position order, takes START first then SIT by margin, a record of zero counts when none. A reason is read as `{k, text}` (also `{kind, text_key}`). `design/startsit.py` keeps only each position's best spot, for the board.
- **Superseded 2026-10-04:** the v2 takes (higher/lower than FantasyPros), Pitcher List's column, the v2 record bars and splits, the pause rule, shadow takes and Claude's weekly read. Their data, copy and CSS are gone from this view; the weeks 1-4 grade files stay in ff-jarvis.
- Tests: `tests/test_startsit_v3.py` (the cut, the loader, every state of the page, the Slips link, the desktop edges, 360 overflow), `tests/test_startsit.py` (picker, board and best spot); golden states `matchups`, `matchups-open`, `matchups-modal`, `matchups-nograde`, `matchups-notakes`, `matchups-nocalls`.

Not built yet: Bets > Games (every game with its implied totals and each offense against the other
defense by position), the storyboard's second view.

## Preview (This week, 2026-09-29; slate and dossier since the same day)

A slate of every game, then one game's dossier. Storyboard option A (David, 2026-09-29), superseding
option C of that morning: David asked for "more research and evaluation of this matchup" and to
"show all slates so it's easy to find and click one", plus lines, matchup ranks, injuries, weather,
travel, rest and short weeks. One screen per game could not hold that. League-wide and public: no
roster is read, and the players named are the ones ff-jarvis's `game_preview` picked per side.

| part | what it shows |
|---|---|
| Slate | titled "Game previews · Week N" (pick 4A, 2026-10-05: the tab stays "Preview", the 360px sub-row is full). Every game not yet over by kickoff window (Thu night, Sun morning, Sun early, Sun late, Sun night, Mon night, else the weekday), headed with its Eastern times from the data (`design/preview.py` `_slot`). A game being played says Live (`--down`) where a confident pick's word sits. ~~A row: AWAY @ HOME, Claude's winner (`--lime`) and score, the headline, then the spread in words, the total and at most two flags~~ (two lines since 2026-09-29, "Front page") |
| Past games (2026-10-05, picks 1A and 2A of https://claude.ai/artifact/NTeV8W2N9mFnYgftfbuqPV; David: a finished game "keeps appearing", the record card was "randomly placed" and wordy) | a game leaves the slate once it is over (`pvOver`: the schedule's final, Live's clock saying Final, else 4 hours past kickoff). Under the games, up to two rows: "Final · N games this week ›" and "Past weeks · Claude's record ›". Either opens Past games (a layer on a phone, the dossier's place on a desktop): Claude's season as three rows, Moneyline / Spread / Total with record and hit %, the spread by confidence in one grey line; then a stepper ‹ Week N › (one row wide at any week count, week 1 to this week); that week's record in one line; its games, each the final and the three calls marked ✓ (`--up`) / ✗ (`--down`) / – push. A tap opens the game's preview as written, with the final on top and ✓ / ✗ in the answer table; back says "‹ Past games". Earlier weeks' takes are `preview_archive.json` (design/preview_archive.py, from ff-jarvis history `previews`), fetched on first open, never injected; until it arrives the rows come from the record. Replaced the record card and its every-week sheet (win % closer, fav picks and the per-week table are gone from the page) |
| Flags | ~~drawn on the slate~~ (off the slate since 2026-09-29, "Quiet slate"; `_flags` still ships them) by priority: UPSET (Claude's winner is not the market favourite, `--lime`), Line flipped / Line moved n (3+ points, `--amber`), Rain n% (50%+) or Wind n mph (15+, `--sky`), "J. Coker out" (the highest-average Out/IR player at 10+ points a game, `--down`), Short week (`--ink-2`). Computed in `preview.py` `_flags` |
| Dossier header | "‹ All games" (a phone), ‹ AWAY @ HOME › and the kickoff. Arrows and a sideways swipe walk the games in kickoff order |
| The answer, one row per bet (2026-10-05, pick 3A; David: "saying the same thing many times", "Are you saying PIT is covering?") | Claude's score, then a table: Moneyline, Spread, Total, each with Vegas's number (grey: the market favourite's win %, "PIT by 2.5", "38.5") beside Claude's call (white: "CLE wins" with his chance, "CLE covers" with its confidence word, "Under") and one grey line saying what the call needs in points ("wins, or loses by 2 or less"; a whole-number line's exact margin is a push and counts on neither side). A finished game adds the final above and a ✓ / ✗ per call. `pvAnswer` / `pvFinal` (data/preview.js, tested in Node). Cut: the market's implied score, "getting / giving", where a line opened, the win bar. Supersedes the row below |
| ~~The answer (2026-10-05, plan U3)~~ | a block under the header, above the headline: Claude's pick (score, the market's implied score beside it, his side and confidence), the spread and the total (each with where it opened when it moved, Claude's total call under the total), the win chance with the market's and the bar. Cells are `pvAnswer` (data/preview.js); a game with no take still gives the line, total and market win chance. It replaced the Win chance and Lines rows of the box score and the side in "The call." (the call is now its reason alone, absent without one). At 390x844 it ends above the fold (`test_the_answer_is_above_the_fold...`); the audit found the line under five paragraphs. From 1100px it spans both columns |
| Claude's call | headline and lean, the full width; then the call row (below, "Confidence and record"). ~~Claude's score over the market's implied score, how the two differ~~ (folded into the call row 2026-09-29; a take written before confidence still draws it) |
| Lines | spread in words ("ARI by 1.5", "opened NYG by 7"; even is "Even"), total ("opened 45.5"). Never a signed spread (David: "-1.5" was "kinda funky"). ~~Claude's margin and total~~ (the call row's Score, 2026-09-29) |
| Matchup | each offense against the defense it faces, rank with points allowed small beside; bottom 8 `--up` (soft), top 8 `--down` (tough); the WR row faded with the reason (the backtest finds the WR matchup moves nothing, QB/RB/TE 8-18%); pass EPA rank; "after N games" |
| Injuries | both teams: OUT / IR tags `--down` with the player's average, D / Q `--amber` |
| Weather | the stadium and roof, the forecast, and only the backtest's proven effects for the conditions met, read from `LIVE_WX_HISTORY` (the Weather view's cells and thresholds, so the numbers are never ours); a dome, or a forecast under every threshold, says it moves nothing |
| Rest & travel | facts: days since the last game, SHORT WEEK, OFF A BYE, zones travelled and the body-clock kickoff, miles, a neutral site. One line says the backtest found no edge past the line (ff-jarvis METHODOLOGY 12.62, 2026-09-29: 0 of 23 cells pass; it said "not tested yet" before) |
| Player calls, Risk | every call (up to 8), a tap opens the profile; the risk |

- ~~**One card, rows inside**: the rows are divided by the card's 1px `--line` showing through a grid
  gap.~~ (Superseded 2026-09-29 by "Front page": no card, a story and a box score.) A row whose data
  is absent is not drawn.
- **Back:** opening a dossier on a phone pushes a URL-less history entry (`chrome/layers.js`), so Back
  returns to the slate at the scroll it left (`test_a_tap_opens_the_dossier_and_back_returns_...`).
- **The game is not in the hash.** Only the view is in the URL (CLAUDE.md, Navigation); a reload lands
  on the slate, one tap from any game, and a game key in the hash would be a second thing to keep in
  step with Back, the swipe and the week turning over.
- **Desktop (960px+):** the slate is a sticky 330px rail beside the dossier, the game on screen on
  `--panel-2` with its matchup in `--lime`; a click only changes the game, no history entry. ~~From
  1100px the dossier's rows pair two across~~ (superseded 2026-09-29: the box score is a column
  beside the story, "Front page").
- **Measured 2026-09-29, week 4's 16 real games:** at 360x800 the first slate row starts at 112px and
  7 rows are on the first screen; any game is one tap away; a dossier is 1,468-1,585px (about two
  screens). `test_every_game_fits_one_screen` and the day marker are retired with option C.
- **Opens on** the slate; once the week has begun the phone slate scrolls to the next game to kick
  off, and the desktop dossier shows it.
- **No take yet:** the slate row says the call arrives with the next refresh; the dossier keeps every
  research row.

### Front page (2026-09-29, evening)

The slate and the game page read like a newspaper. Storyboard option C (David, 2026-09-29: "the left
side is super busy ... the right side has a lot of data. Make it clean so it reads like a newspaper or
newsletter"; https://claude.ai/artifact/8m6221CCeTerrxpwLVxTxy). Option A, a one-line index, lost the
headline; option B, one reading column, left ~500px empty on a desktop. No number was dropped: each
moved to the box score.

| part | what it shows |
|---|---|
| Slate row | two lines: AWAY @ HOME with Claude's side and chip, then the headline in serif (`--news`, Newsreader) ~~with the producer's first flag trailing it after a dot~~ (no flags since "Quiet slate"). Win %, the bar, the score, the total and the spread moved to the box score |
| Headline and dek | the take's `head` in serif at `--t-6` (`--t-5` under 760px), the `lean` under it as the dek, a rule below |
| Story | words, each part led by a bold run-in: "The call." (side, chip, the edge sentence), Claude before the line, "Research notes.", "Players.", "What could go wrong." |
| Box score | every number, small type, hairlines, no boxes, each section under a plain bold name: Win chance (Claude's win % in `--lime` over the market's, the bar, his score over the market's implied one, the base rate), Lines (spread, total, Claude's total with its chip), Defense rank, Injuries, Weather, Rest & travel |
| Order | a phone: headline, the call, the box score, the story (numbers by ~710px on a 360 phone). From 1100px the box score is a 340px column right of the call and the story; the story's grid row takes the slack so the call keeps its height |

- **One new face:** Newsreader, in Preview only, for the headlines and the dek (`--news` in `base.css`).
- **No card.** The game sits on the page's ground; the record sheet keeps its card (`record.css` now
  holds `.pvd-card`).
- **Measured 2026-09-29, week 4's 16 real games, 360x800:** slate rows 115px became 62–81px; the slate
  2,084px became 1,400px. The game page: 8 boxed rows and 13 all-caps labels became 0 of each. At
  1440x900 the rail shows about 8 games, was 6; the story and the box score end level (1,279px each for PIT @ CLE).
- Tests: `test_a_row_is_the_call_then_the_headline_and_one_flag`, `test_the_game_page_reads_like_a_newspaper`
  (part order, box score sections, run-ins, no uppercase labels), the desktop test's box-beside-call check.

### Quiet slate (2026-09-29, night)

Few things are loud on the slate: the kickoff window, then the matchup. Storyboard option B (David,
2026-09-29: "too many things screaming for attention. Keep only a few things highlighted", and "I
don't even see the Sun early"; https://claude.ai/artifact/MpjMnKmnJDKaJij6XLfiUc). Option A kept the
flags in grey; David picked no flags.

| part | what it shows |
|---|---|
| Window | a section head: "Sunday early" spelled out in bold serif on a 2px `--ink-2` rule, its kickoff times small and grey on the same line |
| Row | the matchup bold, 15px mono; Claude's side grey, regular; how sure he is in words; the headline in grey serif (white on the game on screen) |
| Lime | only the game on screen, Confident (text) and Very confident (fill) |
| Words | no jargon (David: "don't use jargons and terminology that the reader is not familiar with"). The confidence Claude gives itself in ff-jarvis's prompt ("slight", "clear reason", "would stake the record on it") reads Slight, Confident, Very confident; no side reads No pick. UPSET left with the flags |

- **Measured 2026-09-29, week 4, 360x800:** 10 boxed chips and 9 coloured flags on one screen became
  0 and 0; lime marks 7 became 2-3; rows 62-81px became 61-62px; the slate 1,400px became 1,354px.
- Tests: `test_a_row_is_the_call_then_the_headline` (no flags, lime only on the confident picks, the
  window head in serif), the plain words in the chip, game page and record tests.

### Newsprint and faces (2026-09-29, late)

Preview prints on paper and every game leads with a face. Storyboard option C (David, 2026-09-29:
"it's very clinical. So much black and white"; https://claude.ai/artifact/U5vPm4p1QXxXYVzsCxrBcC).
Option A, team colours on every code, was loud again; option B was the faces alone.

| part | what it shows |
|---|---|
| Palette | The site's own ground, surfaces and lines; the warmth is in the type (option A of https://claude.ai/artifact/517bzHZ7Cc24n2p4U7keZF, the same evening; David: the brown was "too brown", and it clashed with the site header above it). `--np-ink` (cream) on the day heads, the current row's headline and the game's headline; `--np-ink-2` (warm grey) on the slate headlines and the dek. Both in `base/newsprint.css`. On `--void`: cream 15.0:1, warm grey 12.1:1. ~~A warm charcoal-brown ground, `.pv` remapping every surface and ink, painted to the edges by a `border-image` fill~~ (superseded the same day) |
| Face | 40px round, left of both lines: the first of Claude's player calls whose first or last name the headline says ("Dak outguns ...", "Love's arm ..."), else his first call (`pvFacePlayer`). No photo: initials. No take: an empty slot |
| Right of the matchup | only a confident pick: "Confident" in lime text, "Very confident" a lime fill. ~~The side ("JAX getting 2.5") and Slight / No pick~~ (off the slate 2026-09-29, David: drop the getting/giving; the game page keeps both) |

- **Measured 2026-09-29, week 4, 360x800:** rows 61-62px became 60-80px (the face's column wraps
  some headlines); the slate 1,354px became 1,494px.
- Tests: `test_the_slate_has_warm_type_on_the_site_ground_and_a_face_per_game`, `test_a_row_shows_only_a_confident_pick`.

### Confidence and record (2026-09-29)

Every take says how sure it is against the spread, and a record keeps score. Storyboard option A
(David, 2026-09-29); option B, best bets first, was rejected because it breaks kickoff order. David's
reason: "going with safe is just saying we go with Vegas". Week 4's takes picked the favourite to
cover in 14 of 14; favourites cover 48% (2011–2025, n 3,915).

| part | what it shows |
|---|---|
| Slate row | right of the matchup: Claude's side against the spread and a chip. No edge: the NO EDGE chip and no side. ~~Under it "IND wins 27–19 · market 62% · Claude 71%" and the bar~~ (moved to the box score's Win chance, "Front page" above, 2026-09-29) |
| Side words | never signed. ~~"CLE getting 2.5" (underdog), "IND giving 3.5" (favourite), "CLE, even" (pick'em); `pvSideWords`~~ (superseded 2026-10-05 by "CLE covers" beside Vegas's "PIT by 2.5", pick 3A) |
| Chips | Very confident (lime fill), Confident (lime text), Slight and No pick (grey text), no boxes. ~~STRONG, SOLID, LEAN, NO EDGE~~ (plain words since 2026-09-29, "Quiet slate") |
| ~~Record card~~ (superseded 2026-10-05 by Past games, above) | atop the slate, one tap target: "4–2–1 vs spread", hit % (pushes out), by confidence, "Win % closer than the market's on 4 of 7" (per game, whose win % was nearer the result: a Brier score), and once graded the blind number's record and margin error. Before a graded game: one line, "Claude's record against the spread starts once week 4 is final", never zeros |
| ~~Every week~~ (superseded 2026-10-05 by Past games) | a tap on the card: in the slate's place on a phone (a layer, so Back closes it), the dossier's on a desktop (a click on a game, or the card again, closes it). A table (week, vs spread, STRONG, fav picks, win % closer, a Season row), what each column means, then each week's games, the newest open: matchup, final, HIT (`--up`) / MISS (`--down`) / PUSH / PASS, Claude's side and chip |
| Call row (game page) | after the headline: side and chip, the edge sentence, Win % (Claude beside the market), Total (over/under the line and its chip), Score (Claude's beside the market's implied), "Claude before seeing the line: WAS by 1.5, total 48.5" and how the final call moved from it, then the spread's base rate ("A 3.5-point favorite, 2011–2025: wins 67%, covers 49%, n 1,314") and research notes, each with a small source (the site, or "play-by-play") |

- **Colour map:** lime is Claude (the dot, his win %, STRONG's fill, SOLID's outline); grey is the
  market; `--up` / `--down` only a graded HIT / MISS in the record.
- **Data:** per game `market_win`, `base`, and a take's `win`, `ats`, `total`, `blind`, `vs_blind`,
  `notes` (`design/preview.py`); every field null (or []) from a producer written before it, and the
  row draws nothing then. The record is `LIVE_PREVIEW.record`, from ff-jarvis `preview_record`
  (`design/sources.py` `load_preview_record`, feed first). It lives inside LIVE_PREVIEW because only
  Preview reads it and it has no page without the week's games.
- **Measured 2026-09-29 at 360x800**, week 4's 16 real games with confidence injected (the producer
  had not written it yet): the first data starts at 86px (the record line); slate rows 81px to 115px,
  so 7 rows on the first screen became 5; a game page 1,932–2,173px became 2,067–2,290px.
- Tests: `tests/test_preview.py` (the chip and side words, the bar with and without a market, the
  record's empty state and graded weeks, every week opening and Back closing it, no signed spread
  anywhere); golden states `preview-record`, `preview-record-empty`.

### Option C, one game a screen (2026-09-29, superseded the same day)

One game a screen, for every game of the week, in kickoff order. Storyboard option C, picked by David
over a slate of rows and a stacked program (https://claude.ai/artifact/A5QvueyLecBFdFyYCcZbEH):
"It fits all one screen", plus swipe and a Thursday / Sunday / Monday marker. League-wide and public:
no roster is read, and the players named are the ones ff-jarvis's `game_preview` picked per side.

| part | what it shows |
|---|---|
| Day marker | one button per day (the reader's own weekday), one dot per game, the game on screen lit `--lime`; a tap jumps to that day's first game |
| Header | ‹ AWAY @ HOME › and the kickoff; "kicked off" once it has. The arrows turn the game, so there is no pager row |
| Claude's call | headline, lean, then Claude's score over the market's implied score (two rows on one set of columns), how the two differ, rain at 50%+ in `--sky`, who is out in one line, the risk |
| Players | 3-4 rows: face, call (▲ `--up` beats his projection, ▼ `--down` falls short, ● lands near it), "D. Swift", position and team, our projection, why. A tap opens the profile |
| Footer | once: whose call it is, that every number in it is checked, that it is opinion, not a tested model, and the key to the three marks |

- ~~**Fits one screen (measured 2026-09-29, week 4's 16 real takes):** the card ends at 703-772px on a
  360x800 phone and 420-489px on a 1400x900 desktop. To get there the ff-jarvis writer's limits came
  down (4 players, lean 180, market 110, why 70, risk 100 characters; it was 6 / 240 / 160 / 120 / 160,
  and the card ran to 877px), the pager row moved into the header, and three "Out" chips became one line.
  `test_every_game_fits_one_screen` held it on the fixture.~~ (retired)
- **Swipe:** the Board's touch delta (`board.js`), not scroll-snap: STYLE.md forbids sideways
  scroll inside a page that scrolls down. More than 48px and mostly sideways turns the game; past
  either end nothing happens. The new card slides 28px in from that side on the spring; reduced
  motion draws it in place.
- **No take yet** (a failed write, or before the first run): the header and "Claude's call on this game
  arrives with the next refresh.", with rain and who is out.
- **Opens on** the next game to kick off, not the first of the week.

## Weather (This week, 2026-09-26)

Every game of this week (`schedWeek`, the pack's week) with the forecast at kickoff. League-wide
and public, so it reads no roster (decided 2026-09-26): the players named are the projections' own
(`LIVE_WX_HITS`), and a reader's own players carry their weather on the Roster cards. `LIVE_WEATHER` is joined on the home club through
the schedule's alias (LA is LAR there); a forecast counts only when its `kickoff` is this game's.
It sat in Players for its first hours; it moved to This week (after Digest) the same day, which
put Players back to six views and let the 7-tab phone rule go.

**Out of the sub-row (2026-10-05).** Recap (below) took its place in This week's sub-row: seven views
measured 383px against the 332px row a 360px phone has, six fit in 316px (browser, 360px, 2026-10-05). Weather stays in `NAV`, so `#weather`,
`navGo("weather")` and `navGroupOf` work; `NAV_HIDDEN` (`chrome/nav.js`) only keeps it out of the row. It is one tap
away from the Digest's Weather row and every Preview dossier; with it open no sub button is pressed.

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

## Schedule (Stats, 2026-10-05, plan U7)

Which teams face the softest defenses at a position: the 32 teams ranked easiest first, the points the
opposing defenses allow that position per game, and the opponents week by week with the byes marked.
**Context, not backtested** (ff-jarvis METHODOLOGY 12.11 is the nearest finding): the file's own `label` is the one
line under the heading, no price or lineup call reads it, and no word on the page says start, sit, buy or sell
(`test_js_sos.py::test_the_view_has_no_verdict_word`). `LIVE_SOS` is ff-jarvis's `sos.json` passed through
(`design/sos.py`); the page computes no number. The order is the file's `rank` (ties by team code), the number
is its `pts_pg` to one decimal, the games its count, a bye its `bye` list (`data/sos.js`, `tests/test_js_sos.py`).

| part | what it shows |
|---|---|
| Control row | position (QB RB WR TE), then the weeks (Next 4, Rest, Playoffs): one line at 360px, 40px chips at 11px type (`.sos-ctl`); the full weeks are in the heading ("weeks 5-8"). It wraps only below ~330px |
| Heading and label | "Easiest RB schedules, weeks 5–8" over the file's label, three lines at 360px |
| Row | rank, team code and games, points allowed per game; under them one small cell per week of the window, the opponent over the week number, a dashed "BYE" cell for a bye. The cells run the row's full width and wrap (7 and 6 for the 13 rest-of-season weeks), so nothing scrolls sideways. From 760px the cells join the first line. Nothing to tap, and no colour for good or bad |
| No file | "NO SCHEDULE YET", no controls |

- **Where it lives.** A leaf in Stats (id `scouting`) kept out of the sub-row by `NAV_HIDDEN`, like Weather: Stats' five tabs
  end at 326 of the 332px a 360px phone holds. `#schedule` and `navGo("schedule")` open it; Ranks links to it. With it
  open no sub button is pressed.
- **First data at 226px** on a 360x800 phone (measured 2026-10-05), over STYLE.md's ~200px: the label is required
  on the page and is three lines there, the heading one, the control row 40px. Trimming the label to two lines would
  cost the METHODOLOGY pointer; `test_sos_view.py` holds the line at 240px.
- Position and weeks are this view's own choice; they are not shared with Ranks, which is one week.

## Live (This week, 2026-09-28; four tabs 2026-10-04; three tabs and a team-led league 2026-10-05)

Every matchup in the reader's league, scored live, and every NFL game of the week. **Game-day flow
(2026-10-05, storyboard https://claude.ai/artifact/ArF53Lvh12QV8fbL3mr9KP, option 2A):** three tabs, My
league, NFL and TDs; the league is the picked team's; a strip of the league's matchups leads My league; the
reader picks a team inside Live. Where a line below still names the Matchup or League tab, the league
chips or `tw-live-league`, it is the 2026-10-04 build and superseded by this paragraph. Storyboard
for the tabs, mirrored rows, clock, TDs and game sheet (option A, David 2026-10-04):
https://claude.ai/artifact/JrM6hBMrAL2hjFzYPgKitV. The first build (2026-09-28):
https://claude.ai/artifact/8qKDQUVxkz4F5naVPVQjhH. Lineups and each league's scoring rules are baked
in (`LIVE_GAMEDAY`, `design/gameday.py`); the numbers are Sleeper's, trimmed to our players by
`/api/stats`, and the page scores them itself. No ESPN cookies, no Yahoo API.

~~**One page, a score card, the lineups, the games, the ranking**~~ (superseded 2026-10-04 by the
tabs below; the NFL now card (`nflnow.js`) above the matchup went with it).

| Tab | Shows | Source |
|---|---|---|
| My league (id `league`, the default; Matchup and League merged 2026-10-05) | the strip (below), then the game on screen: both scores, who leads, the league median line, both lineups mirrored; then the ranking with the median. Matchup and League were separate tabs until 2026-10-05 (superseded; a stored `matchup` opens My league, `gdTabOf`) | `board.js` `gdMyLeagueHTML`, `mirror.js`, `league.js` |
| NFL (id `games`; named Games until 2026-10-05) | every NFL game of the week as a tile: live first, then the next kickoffs, then finals; a lime count of games on now rides the tab; a tile with starters of mine has a lime edge and "N yours"; a tap opens the game sheet. Since 2026-10-05 the states read apart (live: a lime stripe down the left edge and a faint lime wash, so it is a different shape from mine's ring; final: the panel at 40%; upcoming: plain), and the leader's code and score wear the club's colour (`gdClubTint`: its first colour at luminance 0.12+, about 3:1 on the panel, else the primary lifted toward white in its own hue) while the trailer greys | `nflnow.js`, `gdWeekGames` |
| TDs | Feed: a TD clips reel (DESIGN.md "Clips", since 2026-10-05), then Scored, then Still alive (below); or By game; with filters (below) | `tds.js`, `tdclips.js` |
| ~~League~~ | superseded 2026-10-05: every matchup as one row, then the ranking, a tap opening Matchup. The rows became the strip, the ranking stayed under My league | `league.js` |

- **The strip (2026-10-05).** A row of chips above the score head, one per matchup of the league, the
  reader's first and the rest in the league's order, so a poll never reshuffles them (`gdStripOrder`,
  `data/gameday/strip.js`; drawn by `gdStripHTML`, `surface/live/league.js`). A chip is 124px wide: the two
  team names in a few whole words (`gdShortName`), the scores, and a state word (`gdChipState`: LIVE while
  a starter plays, else how many are still to play, else final). A tap shows that game in the head and the
  lineups under it, no tab switch and no scroll; the reader's chip brings theirs back. The pick is memory
  only. The strip scrolls sideways (STYLE.md "Controls", dated exception) and keeps where it was scrolled
  across a poll. A team with no game this week (a bye, out of the fantasy playoffs, week 18) leads with
  the league's closest game instead, and its head says "No game this week" with the team's name, the
  team switch from 761px (`gdByeHTML`), never an empty matchup.
- **The league follows the team (2026-10-05).** Live's league is that of the first of the picked team and
  the followed teams that plays in a league here (`gdLeagueFor`); with none, the first league. The league
  chips (Yahoo, ESPN) and `tw-live-league` are gone: to change league, change team. From 761px the reader's
  name on the score head is the team switch, and a pick there keeps the reader on Live (`gdNameOn`); on a
  phone the header bar's switch is the one. With no team
  of theirs in any league, My league is one card, "whose game are you watching": each league with its
  team count, a league lists its teams, a tap picks (`gdWhoHTML`, `surface/live/mine.js`); it replaced
  the dashed line that sent the reader to My teams. A poll waits while the switch's menu is open.
- **Phone tab row.** On a phone the three tabs open in place in the tab row (DESIGN.md "The phone's
  chrome"); Live draws no tab bar of its own there, and the NFL tab keeps its count of games on now.
- **Swipe.** The sideways swipe between a league's games went with the Matchup and League tabs; the
  strip is the way now. The game sheet keeps its own swipe between games.

- **Whose team is "mine" (2026-10-04).** David: "Make sure that the site registers the roster(s) that
  the user picks as the 'yours' or 'mine'. I don't want it to default to my personal rosters." Live's
  "mine" (the left side and UP / DOWN, the median's "you", the League tab's highlight, the Games tab's
  "N yours", the sheet's "Yours in this game", the red Hurt chip) is `gdMine(lg)` (`mine.js`): the team
  picked in this browser (`tw-team`) if it plays in the league on screen, else a followed team
  (`tw-follow`) that does, else null; never the league's `me` (David's, kept in the data for the build).
  A team is found by the `key` `gameday.py` bakes in beside its name: the league's own key for David's
  ("espn"), the league plus the name's slug for any other ("espn-run-it-back", as `mates.py` keys it).
  With null, My league is the "whose game" card (above; superseded 2026-10-05: the Matchup tab showed the
  league's first game with neutral "BY n" chips and a dashed line, "Pick your team to see your matchup",
  that opened My teams). The NFL tab's count and the sheet's block are empty without a team.
- **The choice** is `tw-live-tab` in `localStorage` (`tabs.js`), never the hash, so another view
  sends the reader to a tab by setting it, then opening `#live` (the Digest's touchdown count does).
  Switching repaints in place (`paintLive`), never through `render()`. NFL and TDs are NFL-wide; the
  league chips that sat above Matchup and League are gone (superseded 2026-10-05, see "The league follows
  the team").
- **Mirrored rows (My league).** One row per starter slot, ESPN's way: my starter left, theirs right,
  the slot between as a pill. A half is his name with his points beside it, and under them his
  game's clock line and his projection (no label: under the points it can only be the projection).
  A row is 46px, so the score and nine starters fit one phone screen. My slot pairs with the
  opponent's starter in the same slot, then the rest pair in order; a short side gets an empty half.
  The benches sit behind one toggle row, mirrored the same way, dimmed and never in the total; open
  or closed lives in memory only and starts closed.
- **Slot pills** wear the position's colour: QB, RB, WR, TE, K sand, DEF violet (steel until
  2026-10-05: it read as grey). A flex slot wears a left-to-right blend of what it takes (David,
  2026-10-05): FLEX and W/R/T are RB-WR-TE, OP is QB-RB-TE, W/R and W/T their two. A half whose game is on is tinted lime and its points are lime (David, 2026-09-29:
  lime means his game is on); a smashed projection draws the flame beside the points.
- **The median line** sits under the score: "League median 101.7 · you +3.3", green above it and
  red below. Only a league that pays the top half a second win draws it; the other leagues rank for
  bragging and draw the line grey, in the League tab only.
- **The clock line** (2026-10-04) is the half's second line: the quarter and clock ("Q3 4:12",
  "Half", "OT 2:01", "Final", "Final/OT"), then the score from his club's side while it is on, the
  result once final, and before kickoff the opponent ("vs DEN", "at DEN") after the kickoff time.
  ESPN's public scoreboard says where a game is; Sleeper only says whether it is on. The reader's
  browser asks ESPN, one request per Live poll for every game (`gdClockFetch`,
  `data/gameday/clock.js`); ESPN answers a browser and refuses servers, so no `api/` function can.
  `gdClockOf(club)` is the one read every view uses, returning `{state, label, live}`. When ESPN is
  down, Sleeper's word stands ("Live", "Final") and the kickoff from the schedule, never a guessed
  clock. The score is Sleeper's: a club's defense row counts the points it allowed.
- **A tap on the clock line opens that game's sheet** on the player it came from (below); a tap on
  the name opens his profile. Two buttons, never nested.
- **The game is a centred modal (U9, 2026-10-05).** David: "why cant you do a centered modal?" The sheet
  was full screen on a phone and a bottom sheet from 960px (superseded, 2026-10-05; the list of the bottom
  sheets that remain is in STYLE.md "Overlays"); STYLE.md "Overlays" says a game is for
  reading, so it is now a modal with a 16px margin on all four sides on a phone (358px wide at 390px,
  max 560px) and a 1040px max-width from 960px, never docked to the bottom edge. Closed by the X, a tap on the scrim, Back,
  Escape or a pull down from the top; the sideways swipe between games (STYLE.md row 17) and the step
  row work inside it. The grab bar is gone. `tests/test_live_modal.py` pins the four margins at
  390 and 1280px.
  **The phone's footer (2026-10-05).** Up to 760px the step row is a bar pinned to the bottom of the
  modal, three 48px buttons: Prev game · Close · Next game, Close in lime as the primary
  (`gsFootHTML`, `data-gsclose`; `css/surface/live/gamesheet.css`). The body above it scrolls, the bar
  does not. The ✕ at the top stays, and the scrim, Back, Escape and the pull-down still close (STYLE.md
  "Overlays"). From 761px it is the quiet row under the title with no Close, as before; with one game
  only, the bar is Close alone.
- **Names in the plays are bold (U9).** David: "the game log should bold the players name." Every
  player named in a play line is bold: ESPN's play participants when the summary carries them, then
  the "J.Goff" initial-dot pattern for everyone else ("A.J.Brown", "A.St. Brown", "M.Harrison Jr.",
  a defender in brackets) (`data/gameday/plays.js`, `gsBoldNames`). The saved summary has no
  participants, so the pattern is what the tests read on real text; the participant path is pinned
  with ESPN's field names (`athlete.displayName`) and not seen live.
- **The ball and the red zone (U9).** David: "the live scoreboard should show the direction of the
  ball or team and the redzone." A live tile on the Games tab draws a small football before the club
  that has the ball, the down and distance under the scores ("3rd & 4"), and a red RED ZONE tag
  inside the opponent's 20. No request is added: ESPN's `situation` (possession, `downDistanceText`,
  `isRedZone`) rides in the scoreboard response the clock already reads (`gdClockShape` keeps it as
  `sit`; `data/gameday/situation.js`). **Unverified live:** no game was on when this was built and the
  one scoreboard request it was allowed returned no saved body, so the scoreboard's `situation` is
  ESPN's documented shape, as the summary's is, and not a response read. A missing `situation` draws
  nothing, never a guess. At the half the tag and ball are off. The game modal's scoreboard shows the
  same tag beside its "BUF ball · 3rd & 4 at DET 15" line (the summary's own `situation`, as before).
  Without `isRedZone` the spot decides: the opponent's 20 or closer.
- **The TDs tab** follows what David builds slips from, with no input: he will not enter slips, so
  nothing is saved. League-wide and public, so it reads no roster.

  | List | What | Rows |
  |---|---|---|
  | Scored | every player in `/api/stats` `lead=1` with a rushing or receiving TD (a passing TD is the same score as the catch, counted once); most TDs first, then points | position, name and club, "2 rush TD", the game's clock; green line |
  | Still alive | the top 15 of Parlay's anytime-TD list by the model's chance, minus whoever scored; live (his game is on, no TD yet, lime), later (the kickoff), missed (his game is final with none, red, sunk to the bottom) | position, name, the clock, the model's chance |

  No live market means no board: the sample rows are not TD chances. A row opens the profile.

  **Feed or By game (2026-10-05).** David: "group by game + filters. I also like the current list as
  well." A switch (`tw-live-tds` in `localStorage`; since 2026-10-05 the last chip of the filter row, a
  toggle with a divider before it, pressed = By game, so the TDs tab has one chip row, scrolling sideways
  when it does not fit; before that a segmented row of its own, Live's league-chip row) keeps the list
  above as Feed, the default, and adds By game: one card per game, games on now first then the latest kickoff
  (Sleeper gives no scoring time), the clubs, score and clock in the header (a tap opens the sheet),
  that game's scorers inside. Chips under it apply to both and clear on load: Mine (the reader's
  pick or follows, never David's; no team says "Pick your team"), Pass, Rush, Rec. With no type chip
  on the list is rush and rec, as before; Pass is the only way a passer shows. No Return chip:
  `/api/stats` carries only pass, rush and rec TDs. Since 2026-10-05 the
  controls are one row (filters at 107px at 360x780); the clips reel puts the Scored card at ~413px, over
  STYLE.md's 200px: accepted, because the reel is what a reader opens TDs for. (Superseded: two rows put
  the first card at 241px.)
- **The poll** (unchanged since 2026-09-28): a game on and Live (or the Digest, after kickoff) on
  screen, every 30 s; the edge caches the reply 15 s, so readers share one Sleeper read. Nothing on:
  once, if the reply is over 15 minutes old, then asleep until the next kickoff. Another view or a
  hidden tab: never; coming back asks at once. If `/api/stats` is down the page reads Sleeper
  directly (it allows a browser, checked 2026-09-28).
- **`/api/stats?lead=1`** (2026-10-04) adds `lead {id: {n, pos, team, s, pts}}`: every player with a
  touchdown and the week's top 25 by half-PPR, league-wide. Half-PPR is Sleeper's own total, else
  the standard sum: one yardstick for "who leads", whatever each league scores. Live's URL carries
  every club of the week in both spellings and `lead=1`, one reply for all readers.
- **Not measured:** the 46px row is the CSS `min-height`; the claim that the score and nine starters
  fit one 360x800 screen was not measured against live data on 2026-10-04.

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

**Superseded 2026-10-03: Slips is a research board** (`builder/board.js` reads, `surface/parlay/board.js`
draws, `css/surface/builder/board.css`; storyboard "Slips research board", picked A + B,
https://claude.ai/artifact/G1zpdnpWBDroeuwqkrVADX). David researches here and enters his slips on
Underdog; Kept went unused. The page answers "who is getting the work", not "deal me a slip".

| Part | What |
|---|---|
| Bar | the kickoff tabs, unchanged, then the book chip |
| Record | (2026-10-05) above the first card: a card, "RECORD" and "weeks 1-{through_week}", three tiles (W-L big, SLIGHT grey, CONFIDENT lime, VERY a lime chip, hit % small). ff-jarvis `props_record.json` (feed `market.props_record`) via `LIVE_PROPS_RECORD`, drawn by `surface/parlay/record.js`; absent or nothing graded, no strip. Start/Sit's record in this view's own class names |
| Top calls | (2026-10-05, plan "Bets UX" change 1) under the Record line, above the first game: "what should I bet" in one look. The model's strongest lines in games that have not kicked off, five, strongest first (tier, then the chance of its side, then the edge; `topCalls` in `data/topcalls.js`, Node-tested), one line per player, never a touchdown, an Out player, a moved line or a line with no pick. A row, two lines: name and club, the chance and tier word ("72% Very confident"); then the side and line as the outlined label ("Higher rush yds 65.5", Claude's lime C when it agrees) and the edge, "+20 vs 52% break-even" (the chance of the model's side less the break-even of that side's own price at the book in force; Underdog's over/under, DraftKings' primary book's; no price, "No price from the book"; a call priced worse than its break-even, edge under 0, is not listed, since 2026-10-05, because the "+" is fixed in the copy). The row opens the player's sheet; the round + puts that side on the slip (the same path as a side on the sheet, `slPick`; the same side again takes it off). Not a NAV entry and not behind the kickoff tabs: it reads across games. Draws nothing when no line has a tier (an older producer). `surface/parlay/topcalls.js`, `css/surface/builder/topcalls.css`. Measured 2026-10-05 at 390px: starts at 197px, each row 88px |
| Game card | matchup and kickoff; each side's implied points as one bar (`LIVE_LINES`, else Preview's line); Preview's headline as a link to that game's dossier (lime ›; the spread, total and script sentence went 2026-10-05); chips Work rising · TE · Role guys · All N |
| Player row | (2026-10-05, storyboard "Slips Board" A) two columns. Left: name, position · club; his work label and its last three games as bars, each number under its bar (the last bold, `--up` green when his work rose); "Snaps 72%"; chips only when one applies. Right: his most confident line (highest chance of the model's side among his non-TD lines with a tier) as an outlined label, "Lower rec yds", its tier word under it, then "N lines ›". No tier on any line: just "N lines ›". The `why` sentence and the footer are gone |
| Chips | a pill with a 6px dot, only when true. Matchup from `LIVE_DEFENSE` (`seasonDefRank`; rank 1 allows the fewest): the 8 softest defences green "Easy matchup", the 8 toughest red "Tough matchup". "{last} out" amber, one per teammate in `LIVE_REASONS[slug].vacated` (ff-jarvis: every teammate out whose work he inherits) |
| Player sheet | **a centred modal since 2026-10-05** (something to read, design/STYLE.md Overlays: a 16px margin on all four sides, max 560px wide, closed by its ✕, the scrim, Escape or Back; the leg sheet, one bet, an action, stays a bottom sheet, 475px of 780 on a receptions line, so it is not yet "half the screen" and is left as it was). In the leg sheet's overlay (`playersheet.js`, class `ls-read` on `#legsheet`; not `modal`, which is the profile's): his work week by week (snaps, targets, carries, RZ looks; an earlier season faded), then every line he has, Anytime TD included, then "Longest catch": his longest catch in each of the four games, history only (no line, no sides, no count; a game with no catch logged is a dash), because no source sells a Longest reception line we can read (plan update 2026-10-03) |
| Line row | `lineitem.js`, shared with Preview: market and line, Higher / Lower (a TD: Yes), last four games vs today's line (lime cleared, earlier season faded). The model's side is outlined in lime (`.pick`; the fill stays the reader's own pick, so a side can be both) with its tier word under it: Slight grey, Confident lime text, Very confident a lime fill, "No pick" muted under Lower and no outline. A TD keeps "{p}% to score" and no tier. "N of 4" and "model Lower 67%" went 2026-10-05. **Claude's pick** (2026-10-05, storyboard "Claude Calls" A, https://claude.ai/artifact/RZRK6c9XR2qXngfEJfELd8): an 18px round "C" on the top-right corner of the side Claude picked, ringed in the panel colour; lime on the model's outlined side when they agree, ink on the other side when they do not (or when the model has no pick), with Claude's `why` in one line under the row. No call, nothing; Claude's own confidence is never shown, the tier word stays the only one. A call is matched on player, market and the exact line shown (`slClaude`), so an Underdog line at another number gets none. The Slips board's best-pick label wears the lime badge on agreement and nothing on a disagreement. **One confidence vocabulary (2026-10-05):** the tier word is always printed with the chance of the model's side before it, "72% Very confident", on the line row (under both buttons, to their right edge, except "No pick", which has no chance and stays under Lower), the board's best-pick label, Top calls and Build's call (the word under its chance, `.bl-tier`). The tier words and their order live once, `PT_TIERS` / `PT_RANK` in `data/topcalls.js`. ff-jarvis `claude_props.json` (feed `claude_props`) via `LIVE_CLAUDE_PROPS` (`slips.claude_props`), optional in `contract.py` |
| Tray | count, who, Save slip; its sheet: the slip, the payout box, copy, then the slips saved this week (`localStorage` `tw.slips.saved.<week>`, guarded), each a tap to load and an x to delete. **Same-game legs (2026-10-05):** two legs of one game outside a whole stack (`betsSameGame`, `slipSameGame`) show each leg's own chance and no all-hit bar, no combined chance, no verdict against the payout, and the note "Same-game legs move together; the combined chance isn't shown." in the slip (replacing the old "two legs in {game}, correlated" warning). A stack, whose joint chance ff-jarvis measured (12.32, 23.1%), counts once. The joint number waits for the game-sim plan |

- **Who shows:** every player with a line still to play, not out, his line not moved far from the
  model (`lineMoved`). A WR3 or a backup back stays: David's wins on 2026-10-03 were role players.
  Rising work sorts first; a game where nobody's work rose opens on All, never empty.
- **Sides:** the reader picks the side (`SLIP_SIDE`); a Build tap still takes the model's call. A
  leg's graded chance follows its side (`legHit`: higher at most 42.3%, lower 56.3%); a LONG prop
  row, should one arrive, is no line on the board and has no chance, so a slip holding one (Build
  can add it) shows none, never a wrong one. No side gate anywhere: the old
  lower-only floor and the Safe/TDs/Mix deal are gone.
- **"on slip":** a player on the tray's slip or a saved one, on his board row and in Preview.
- **Preview hand-off:** the dossier's box score gains "From this game to your slip" (`preview/handoff.js`):
  the take's players with lines, in the line row, into the same tray, then "All N players in Slips",
  which opens Slips on that kickoff with the game's card in view.
- **Tiers (2026-10-05):** `tier` (none / slight / confident / very) and `side` come from ff-jarvis's
  props_model rows, one per line value, so each book's own line has its own: build.py puts them on the
  row (the primary line) and on each entry of `books`. The cutoffs (.55 / .60 / .70 on the chance of the
  model's side) live only in ff-jarvis; the page never cuts a tier from `model`. In Underdog mode the
  line sheet reads the Underdog entry (`slSrc`), the line it shows; an Underdog line with no tier of its
  own draws none, never the other book's. Absent fields (an older producer, an Out player, TD, LONG)
  draw no outline and no word. Fields optional in `contract.py`; unknown words fail the build.
- **Budget:** the first row sits under the game card's head (matchup, bar, take, chips), so it starts
  past STYLE.md's ~200px; the storyboard accepted ~330px for a game header first. Measured on
  2026-10-03 against the live build at 360x800: the first row at 340px, no sideways scroll.

~~**Slips is a deal table**~~ (superseded 2026-10-03 by the research board above; it superseded the
gallery 2026-09-29) (`builder/table.js`, `surface/parlay/table.js`, both deleted 2026-10-03,
`builder/table.css`; storyboard "Slips Redesign Storyboard", option C, with Keep added because
David builds several slips a kickoff). The gallery, its category tabs (All, Receptions, TDs, Long,
Stacks), Deal me 3 and the TD board are gone. The gallery showed 15 cards for the week because only
15 of 268 playable legs passed its gates (TD 50%+, receptions lower 65%+), one leg per game.

| Part | What |
|---|---|
| Bar | kickoff tabs `Thu · Sun · Early · Late · Night · Mon` (a day of several windows is its weekday, then its parts; "Sun AM" labels ran 82px over 360px). Windows are named by the league's Eastern slot, Preview's words (`slate.py` `et_slot`, `data/kickwin.js`), since 2026-10-05; they were AM · PM · Night by a Pacific hour beside times in the reader's clock. The London game joins the 1 PM wave's window, so the tabs stay six. Then the book chip |
| Slip | kind (TDs, Safe, Mix) and length (3-6) on its top row; a pick per row with a lock; stub: "1 in N" of the graded chance, the board's payout and verdict, Deal again, Keep |
| Kept | the slips kept this slate week, on this device (`localStorage`, legs as slug and market); a tap loads one into the tray; hidden on a phone until the first Keep |
| Pool | what it deals from, top 10 then Show all; a tap locks the pick onto the slip |

- **Floors** (David, 2026-09-29): a TD at 30%+ P(score); a yards or receptions leg at Underdog's
  own line, called lower at 58%+, receptions at 2.5+. Only TD 50%+ and receptions lower 65%+ are
  backtested; the stub's chance stays graded (`legHit`), so a looser pool never reads better than
  it grades. Live on 2026-09-29: 18 TDs and 57 yards legs on Sunday morning, 2 TDs on Thursday.
- **Dealing:** one leg per player; a game of its own per leg while games last, then any game (a
  one-game kickoff still deals); Mix is half TDs, rounding down, and its pool alternates TDs and
  yards so the TDs are not buried under 60-70% yards legs. An Underdog entry gets two teams.
- **Desktop:** the slip beside Kept, the pool under both, two picks across (TDs left, yards right in
  Mix). Measured at 360x800: the first pick starts at 206px.

**Superseded 2026-09-29: Build is a list of lines** (`surface/parlay/lines.js`, `builder/lines.css`;
storyboard v2 option A, picked over a copy of Underdog's layout). One column under a heading per
kickoff, one block per player, one row per line: the line, his last 12 games against it, the call.
Lime bars cleared the call's side, faded bars are an earlier season, the dashed rule is the line.
The line and bars open the leg sheet; the call adds the pick. A line the book moved far from the
model (`stale`) shows "Line moved" and no chance, sorts last and adds nothing: on 2026-09-29 all 21
Underdog picks at 80%+ were moved lines, the model's rate leaning on last season's role. **Best
odds** (renamed **Better price** 2026-10-05, since it filters and does not sort; and the view itself **All lines** in the nav, the leaf `build` and its hash unchanged) is the row's first chip (`bestOdds`, `lib/odds.js`): Underdog keeps a pick paying better
than −107 on the model's side or at a line easier than DraftKings' (68 of 467 that day);
DraftKings keeps an over easier than the consensus. Each kept row prints why. "All" left the row
so six chips fit 360px: a pressed position tapped again clears it.

The market is a card grid (2026-09-25, `css/surface/builder/grid.css`): two cards to a row on a
phone, as many 220px cards as fit from 760px up, so a screen holds twice the players the list did.
~~Opening a line's chevron widens its card to the whole row.~~ Superseded 2026-09-27: the chevron
is an ⓘ that opens the leg sheet (below). Page sizes are multiples of 2 and 3
(12 players, 24 lines) so a page ends on a full row. ~~The gallery slip's paper was toned down the
same day (`--paper` #f1efe8 → #cbc4b4); it glowed against the dark page.~~ Superseded the same day:
the slip went dark (below).

### The game sheet (2026-09-28; followed players and tabs 2026-10-04; a centred modal since 2026-10-05)

One NFL game, for following it without watching (`surface/live/gamesheet.js`, cards in
`gamecards.js`, ESPN shaping in `data/gameday/espn.js`). Storyboard "Follow a Game" (2026-09-28);
the 2026-10-04 rework is option A of https://claude.ai/artifact/JrM6hBMrAL2hjFzYPgKitV.
It opens from a Games tile or from the clock line under a player in Matchup (the sheet then leads
with that player). ~~Live's **NFL now** card listed the games on now, else the next kickoff's, and a
tap opened the sheet~~ (superseded 2026-10-04 by the Games tab; the card is gone).

~~**A phone gets it full screen (2026-10-04)**~~ Superseded 2026-10-05: the sheet is a centred modal at every
width (a 16px margin on a phone, 1040px max from 960px, never docked to the bottom edge; see "The game is a
centred modal" under Live above and STYLE.md "Overlays", which also lists the bottom sheets that remain).
~~From 960px it is a bottom sheet again with the plays tall on the left~~ (superseded the same day). What
stands from 2026-10-04: one scroll holds the scoreboard, "Yours in this game", then the tabs, which stick
to the top while the pane under them goes by. The tabs are Plays · Box score · Top scorers; the default is
Box score and the last pick is kept in memory for the session. From 960px the modal is wider with the plays tall
on the left, so the Plays tab is hidden and the Box score takes its place on the right. A pull down from the top closes it; a sideways swipe walks the
week's games in kickoff order.

| Card | Source | Notes |
|---|---|---|
| Scoreboard | ESPN summary, else Sleeper | on a live game: who has the ball, down and distance, a strip from the away goal line (left) to the home one; before the summary loads, the scoreboard's clock ("Q3 4:12") |
| Yours in this game | rosters + followed players | pinned above the tabs: every player of mine in this game in every league, then everyone followed; the player the reader came from leads, with a lime edge, wherever he is rostered; points in the league on screen's scoring, a dash before kickoff; a star on each row follows or unfollows |
| Plays | ESPN summary | drives newest first; the newest open, the rest one line each and kept open through a poll; timeouts and ends of quarters left out |
| Top scorers | Sleeper (`/api/stats?teams=`) | five, in the league on screen's own scoring; mine bold with lime points; a star on each |
| Box score | Sleeper (`/api/stats?teams=`) | one club at a time: passing, rushing, receiving, most yards first; a star beside each name |

- **Follow** (2026-10-04): the star adds a player to "Yours in this game" for this week, on this
  device. Stored in `localStorage` `tw-gs-follow.<week>` (not `tw-follow`, which is the team
  switch); keys of other weeks are deleted on open. A player's key is his Sleeper id, else his slug.

- **ESPN from the reader's browser only.** It answers a browser and refuses servers and headless
  browsers (403), so nothing server-side asks it; the tests shape the saved game instead.
- **Either source can go quiet.** ESPN down: a line above the plays, every other card keeps updating.
- **The Games score** is Sleeper's: a club's defense row counts the points it allowed. Live's one
  shared poll carries every club of the week for it, so a tile costs no request.
- **Polling.** Open, the game not final, the tab visible: both sources every 30 s, one request per
  host in flight. Closed: never.
- **Overlay**, as the leg sheet's: outside `#view`, one history entry, Escape and the scrim close it.
- **Part 2 (partly built 2026-10-04):** following a player from this sheet is built, without his
  Underdog lines as bars (not built). Replaying a drive in the strip is not built.

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

~~**TD board**~~ (superseded 2026-09-29 by the deal table's pool) (`tdboard.js`): on Slips' TDs chip, under the TD slips, every anytime-TD line still to
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

## The profile modal (rebuilt 2026-09-22; points first 2026-09-28)

### Points first (2026-09-28)

The order is the reader's five questions, in David's order: what did he score, who does he play
next, how much does he play, who has him, is he good. Storyboarded before it was built
(https://claude.ai/artifact/QXvtS37egxdAaPydDbStsa, the sphere at
https://claude.ai/artifact/HjEA4x7r7DRz3Z7Xes4u62).

| Block | Answers | Where |
|---|---|---|
| **Head** | name, bye, injury, and the rail: role, style, the sphere (the stat sheet as a solid, a tap from the flat radar) and Compare as one row of medallions (2026-09-30) | `rail.js`, `orb.js`, `orbsheet.js`, `headrail.css` |
| **Strip** | what we expect, is he good, how much he plays: this week's projection (lime, the headline since 2026-10-05; Out, Played or Bye when there is no number), ppg, rank by ppg, role share, snaps. A link under it opens his row in the Usage grid (`navGoRow`, only for a player the grid has) | `lede.js`, `data/lede.js` `ledeCells`, `gridlink.js` |
| **Owners** | who has him: one pill per league, "Yours", a team name, or free agent | `owners.js` |
| **Season** (first tab, always the default) | points per played week, next week's projection, every later opponent | `season.js` |

| At 360x800 | Before | After |
|---|---|---|
| First fantasy points on screen | 880px, behind a tap on Log | 440px, on open |
| Next week's matchup | lede, as a rank | the lime row, with kickoff and projection |
| Ownership | "On 2 of your teams" | each league's team by name |

- **This week's row is live (2026-10-04, `season.js`).** The game log is cut at build time and lags
  until the nightly rebuild, so on a Sunday the row said "No stats" while Live had scored him. For
  the page's week, with no log row and his game kicked off, the row is drawn from Live's poll
  (`gd:stats` repaints an open profile in place): lime with "Q3 4:12 · live" while the game is on, a
  played row once final. His stats come from his own row in the poll (a player on one of my rosters,
  by Sleeper id), else the league-wide leaders by name and club; with neither, the row stays as it
  was. QB, RB, WR and TE only; points are half-PPR, the log's own scoring. An open profile keeps the
  poll going over any other view.
- **The projection is the strip's headline (2026-10-05, plan U3).** The audit found "WR3 / 26.2 PPG", the
  strip's first two cells, read as this week's projection: they are the season to date. The strip now opens on
  `projFor` (one source since U1) in lime, season ppg second, the ppg rank third. The range joined it with U5 (see "Floor and ceiling" under Ranks).
- **The signal line is a sentence (2026-10-05).** Under the head, watch's reason ("snaps -5.0, share +19; buy or
  start") is written out by `signalWords` (data/signals.js): "Snaps down 5.0 points and his share of the work up 19
  points. Worth a start, or an add if he is free." A reason it does not know is shown as written. The verdict
  word beside it is unchanged.
- **The Season table never grows.** One row per week from week 1, played or still to come, so it
  is ~18 rows in week 1 and in week 18. The opponent's rank is LIVE_DEFENSE's points allowed to his
  position, counted from the easy end (1st allows the most); it is the one measure that exists for
  every week. The model's matchup factor stays in the Matchup pane, for next week only.
- **The rows are a subgrid**, so a phone and a desktop lay out one DOM: a phone reads each week as
  box-score shorthand (`24-144-3 · 1-19`), a desktop gets a column per stat.
- **The sphere** is his radar as a crystal in a glass sphere, drawn on a canvas: each stat a vertex
  on the equator at his rank's radius, poles at his mean reach. It turns once in 14 s and rests 2 s
  at the radar's own angle (STYLE.md rule 1, rewritten for it). Since 2026-09-30 it starts turning
  as the profile opens: the 2 s it used to hold still first read as a stall. The tap swings the camera overhead,
  where the crystal *is* the flat radar, and hands over to it.
- **Game results and past-week projections are not in the data** (Yahoo shows both). Adding them is
  ff-jarvis work.

### The head rail (2026-09-30)

Storyboard: https://claude.ai/artifact/1q2rFmEudfwzyKdf5mgoCy (David: "build the rail, centred";
option D of the same storyboard was dropped for stripping the tiles' look). On a phone the head
stacked five things in one column between the face and the sphere: 259-302px. Now the name block
holds the name, identity and injury, and one row under it holds role, style, the sphere and Compare
as round medallions of one size, each label under its medallion, the sphere's own shape.

| Player at 360px | Before | After |
|---|---|---|
| Zay Flowers (injured) | 289px | 226px |
| Amon-Ra St. Brown (long name) | 259px | 222px |
| Tee Higgins (signal line) | 302px | 245px |

- **Always role, style, sphere, Compare, centred.** A player with fewer keeps the order and the
  row centres, so a missing word is no hole (David chose centred over filled from either end).
  Of 540 skill players on 2026-09-30: 171 have all four, 109 three, 18 two.
- **Nothing but Compare, no rail.** A deep-bench player (227 of 540) keeps a small Compare button in
  his name block.
- **Desktop:** the rail sits right of the name. The sphere keeps its 148px at the rail's far right
  with its caption beside it (David, 2026-09-30: "keep the big sphere on desktop"); role, style and
  Compare are 56px medallions before it.

### Elite bars and the fluke filter (2026-09-30)

ff-jarvis 84c490b (METHODOLOGY 12.68) gives every radar stat a bar: the 90th percentile of
2018-2025 full seasons, TE apart from WR (`elite_src` "history"); per-route stats with no history
take this season's pool ("season") or keep the published 25% / 2.5 ("published"). Each row also
carries `ev`, the value pulled toward the position mean by how small the sample is, and `el`, the
stats whose pulled value clears the bar. David rejected a top-12 rank as the bar: three hot weeks
are a rank, not a standard.

- **Elite reads `el`** (`sheet.js sheetElite`): the label glow, the ladder row and the arc lit in
  the grow-in. With no `el` (data from before 84c490b) it falls back to the raw value.
- **Over the bar but filtered:** the ladder says so, neither green nor red.
- **Provisional bars are dotted,** and the ladder names where the bar comes from.

### Compare (2026-09-30; redesigned the same day)

A layer over the profile, like the stat sheet's, opened by the head's **Compare** button (`cmp.js`).
One history entry: Back closes the layer and leaves the profile. The first build (storyboard
https://claude.ai/artifact/LR2pMmjnZdSfcVsq6Qzt3o, option A) scored 22/40 in an impeccable critique:
lime meant five things, the first number sat at 446px, the radar was its own look. The redesign is
storyboard v5, https://claude.ai/artifact/BLusCqR3ZToXGQ8Kr3nVZM, built as drawn.

| Stage | What it holds | File |
|---|---|---|
| Picker | His team at this position, other FLEX spots on it, waivers (owner only), each by projection; search reaches anyone; a search pick shows under Picked; the tray on the bottom edge | `cmppick.js` |
| Cards | One centred card per player: face (48px, ringed in his colour), name, this week's projection, the gap to the leader as a signed number (his position rank was cut 2026-09-30, David: it is already in the profile). The leader sits on a filled box; the card in focus is edged in its colour. A card is the button that moves the graph's focus | `cmpshow.js` |
| Graph | The profile's own graph (`radarkit.js`, `sheet.js`): disc, rings, ticks, elite arcs, "#rank over the stat" labels. One shaded shape per player; the one in focus brighter, his ranks on the labels. Opens on the profile's player | `cmpgraph.js` |
| Strips | One bar per stat on the cards' columns, its name above: Matchup (the Season table's ordinal, 1st allows the most), Target or Carry share, Red zone, Last 3. Best of a strip bold | `cmprows.js` |

- **Show, don't tell (David, 2026-09-30).** No sentence says who is ahead and no caption explains
  the scale: the gap is "−2.5" under a projection, the scale is the profile's own.
- **Colour follows the pick order:** sky, orange, violet, from tray to card to graph to sparkline.
  Never lime, which kept its job on the controls; on the first player it read as "the winner".
- **One position per graph.** A position's six axes are its own, so a mixed set (RB beside WR)
  keeps the cards and the strips and draws no graph.
- **Opens without scrolling** (David, 2026-09-30). A desktop (960px and up) puts the graph beside
  the strips under the cards: 534px tall, fits 1024x768 and 1280x720 (stacked, it ran 850px). A 360x800 phone fits the
  stacked sheet. `test_compare_sheet_opens_without_scrolling` holds both.
- **Red zone** is the share of the team's red-zone plays (targets + carries) where the profile
  carries both team totals, else of targets. Receivers' profiles have no team carries yet (ff-jarvis
  `red_zone.team_carries` is null for WR/TE), so today they read targets.
- **Nothing says whom to start.** The numbers stand side by side; the gap is a number, not a call.

### The 2026-09-22 build (superseded 2026-09-28 where marked)

Eleven blocks at one weight is a wall. Three tiers, and the order is the answer to "what do I do
with him this week" (superseded 2026-09-28: the lede became the strip, the sheet moved into the
sphere, and Season replaced Log as the first pane):

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
players against each other opens the same pane twice. (Superseded 2026-09-28: every open starts on
Season.)

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
on a phone each week becomes a block of labelled chips rather than a sideways drag. (Superseded
2026-09-28 by the Season table: one line per week on a phone, no sticky head.) Verified
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
A second exception, 2026-10-04 (David): Live's slot pills wear the same tints, plus sand for K
(`--pos-k`) and steel for DEF (`--pos-def`). FLEX, OP and W/R/T stay neutral. The pill is the only
place; the rows around it stay typographic.
Extended 2026-09-29 (David: Usage "too black and white"): inside the profile, his own marks wear
the same tint -- his bar among his teammates', his depth bars, his red-zone segment, his middle and
outside shares, his combine percentiles (`.pf-body` sets `--tint`). One meaning: coloured is him;
teammates, averages and the defense stay grey.
Type: Bricolage Grotesque (display), Archivo (UI),
JetBrains Mono (all numerals).

Mark (2026-09-29, per David: "Let's just keep the original [wordmark]... Let's just add the smug
blip"): the lime block before TEAM//WATCH is Smug Blip, `lib/blip.js` pose "smug" (lit lime screen,
half-lidded eyes, one brow up at the slash angle, a sideways smirk, the wordmark's // leaning forward
as its antenna), 1.38em square beside the wordmark, still at rest. The wordmark is unchanged in
design and grew from 15px to `--t-brand` (22px), so it leads the 18px tabs. The favicon (pose
"smug-16": no antenna or brow) and the 180px apple-touch icon (pose "smug-app") are cut from the same
drawing by `design/icons.py` into `icons/`; the connect sheet carries the same brand at 18px.

### Cards: Material Design's rule (decided 2026-09-28)

Every view follows Material Design 3's guidance on containers. A card holds content and actions
about **one subject**; items of one kind that the reader scans and compares are a **list**. The
source is m3.material.io, Components > Cards and Lists; this wording is from memory (the site
renders in script and did not load for a check), so re-read it there before bending a rule.

| Rule | Here |
|---|---|
| One card per subject | Live: Matchup the score and the two lineups; League the games and the ranking (the same list on 2026-09-28, before the tabs) |
| Rows inside a card stay rows, divided by a 1px `--line` | a lineup's players, the ranking's teams; the Matchup's rows are shaded in turn instead, no rule between them (2026-10-04) |
| A card never holds a card | a nested block uses a filled box (`--panel-2`), no second border radius stack |
| A card is one tap target, or holds its own buttons, never both | a game box opens the game; a lineup row opens the player |
| One card style: `--panel` fill, 1px `--line` border, 16px radius; no shadow (the console is flat) | a filled box inside a card: `--panel-2`, 10px radius |
| Big-number tiles only when the number is the point | Live's score card; not the ranking |

A new or changed view names its cards against this table before it lands (`STYLE.md`, "Before a
view lands").

### Say it in a shape (decided 2026-09-28)

A reader on a phone scans; a sentence has to be read. So a state or a reason is a shape with a
word on it, and the prose lives one tap away in the profile.

| Rule | Why | Where it was learned |
|---|---|---|
| Every visual code is named on the screen, by a word on the thing or one key under the list. A tint, colour or mark nobody explains is removed. | An unexplained tint reads as a bug ("why is the QB row lit?"). | Live's in-game row tint, removed 2026-09-28 (a lime tint on a half whose game is on came back 2026-10-04, with its clock line beside it saying "Q3 4:12"; superseded as a rule only where the words sit next to it) |
| A state is a tag plus a picture of it: LIVE / n LEFT / a drawn lock and LOCKED, and a meter with one slot per player. Never a sentence to parse ("2 still to play or playing"). | The meter also shows which side still has a man going. | Live's league games |
| A reason is a short coloured label: a kind and a number ("TD luck +6", "16% tgt +10"), two parted by a dot. Only the one warning in a card gets a filled box ("Out 3 wks"). The producer stores the kind and the number; the page only labels them. ~~A reason is a pill~~ (superseded 2026-09-29: thirty outlined pills in one card were busy). | 23 lines of prose in one card was the busy part of Results; then 30 boxes were. | Digest Results |
| One colour means one thing inside a set of pills: green helped, red hurt, amber injury, filled red how long he is out, grey his role. | A reader learns it once for the whole card. | Digest Results |
| A feed is grouped by its subject, newest line first, not kept as a log. | A log repeats the same player; a group says the story once. | Digest News, 10 headlines to 7 players |
| Desktop fills its width with more of the same subject (cards across), never with wider lines. | One 560px column in a 1,120px card left half empty. | Digest News |
| A repeated item (a box, a row) carries two things; anything more moves to the card that owns it. | Six marks per box fought for attention; TOP/BOT already had the ranking card. | Live's league games, name and score only |
| Inside one card a colour means one thing. Lime on Live's games: LIVE, the trophy, the game on screen. | Lime meant four things in one card, so none of them stood out. | Live's league games |
| A label sits above what it labels, and the space between groups is wider than the space inside one. | A state line under its game read as the next game's header. | Live's league games, 6px inside, 16px between |
| Every item in a list has the same parts: if one game has a state line, all do. | One shape learned once scans faster than a list of exceptions. | FINAL on finished games |
| A highlight marks what is on screen now, and moves when the reader picks another; one outline per item, never one per part. | A fixed outline on your own game stayed lit while another game was open, and drew twice. | Live's picked game |
| Icons are drawn (inline SVG in `currentColor`), never emoji or Unicode glyphs. | A glyph renders differently per platform and reads as decoration. | Live's lock |

A new or changed view is checked against this table too (`STYLE.md`, "Before a view lands").

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
