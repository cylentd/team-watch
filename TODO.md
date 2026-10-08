# TODO

Tick an item in the commit that finishes it. Newest at the top of each section. Started 2026-10-06; supersedes `~/.claude/plans/team-watch-next.md` (units 1-7, kept there as history).

## Now

- [ ] **Bets > Slips redesign or polish.** Add headshots; fix the ugly grey bars; Top calls look ugly. Too many players: organise them (by game, kickoff window, position or tier). On Sunday the page is endless scrolling. Top calls don't change from day to day: check whether that's stale data (prop lines refetch at 5:50, 2:30, Sat 8:45pm, Sun 8:45am) or a selection that never moves, before the redesign. Storyboard first, at 360px; code `surface/parlay/`, `topcalls.js`. (2026-10-07)
- [ ] **Too many tabs; Recap and Live as tabs.** David isn't sold on Recap's and Live's tab bars (Players / Scores / Claude / Accuracy; My league / NFL / TDs), and the site may have too many tabs overall. Count every tab level per view at 360px, then storyboard fewer (pairs with the nav-names item). (2026-10-07)
- [ ] **Professional polish: chrome stands apart from content.** The bottom tab bar and the tab row are about the same colour as most cards, so they blend in. Give the chrome its own surface (colour, border or shadow tokens), then a site-wide polish pass for the same kind of thing (impeccable). (2026-10-07)
- [x] **Tab row jumps on scroll.** Header and tab row now stay put (2026-10-07). On a phone, scrolling up slides the tab row up over the header bar (team name, Ask) and scrolling down brings the header back; it feels jarring. Make the header and tab row move as one, or stay put. Code: `css/chrome/phonenav.css`, `#hdrteam`, `#subnav`. (2026-10-07)
- [x] **Late scratches reach the preview takes.** Done in ff-jarvis 943b20f (2026-10-07). The intraday inactives runs (Sun 8:45 / 12:00 / 4:30, Mon and Thu 4:00; agent-config `ff-jarvis-status.ps1` -> ff-jarvis refresh group `status_now`) do not run `game_preview`, so a late scratch never reaches Claude's take (checked 2026-10-07). Fix in ff-jarvis: add `game_preview` to `status_now`; it rewrites only games not yet kicked off whose material changed. Check its 2400 s timeout fits the job. (2026-10-07)
- [ ] **Preview dossier cleanup.** The players section is the best part and is buried; consider moving it to the top. Clean up or redesign everything below it: defense rank, parlays, injuries, defenders out, weather, rest & travel, what could go wrong. The Moneyline / Spread / Total rows (Vegas beside Claude) are hard to read; redo them too. Storyboard first (STYLE.md), at 360px. (2026-10-07)
- [ ] **Digest previews the night games.** One preview card, two days: Wednesday's Digest previews Thursday night's game, Sunday's previews Sunday night's (DG_PLAN, DESIGN.md "Digest by day"). Claude's take and the lines from Preview's dossier (`game_previews.json`), opening Preview on that game. Keep the five-card cap; Wednesday leads with usage movers, Sunday with Need to know, and Sunday's card drops once the night game kicks off. Timing checked 2026-10-07: every game's take is in the file from the week turn, so Sunday's card is there at the 5:50 build. (2026-10-07)
- [ ] **DFS on the Sunday main slate only.** David's contest is the Sunday early + afternoon games (no Thursday, Sunday night or Monday). Limit the DFS pool, builder and lineups to those games; check whether ff-jarvis's DFS pool already carries a slate field before filtering by kickoff time. (2026-10-07)
- [ ] **Player tags instead of more numbers.** Players carry many metrics; fold them into a few tags the way usage became icons (Every Down, Complete). Candidates: POTENTIAL / SLEEPER, RISING, LUCKY, TRENDING. Each tag needs one rule from data ff-jarvis already has (usage, role board's work vs points, ROS value) and a backtest before it claims anything predictive; LUCKY = scored above his work's worth. Inventory today's metrics per view first, then storyboard. Pairs with the trade item below. (2026-10-07)
- [ ] **Trade offers: sell the partner's side, and price potential.** A reader asked whether the finder makes sure the trade helps the other team. It does: since 2026-10-06 (ff-jarvis METHODOLOGY 12.99) an offer is written only when the partner's ROS gain is positive (`their.gain`), and the card shows their side. Open: (1) make the partner's gain as prominent as yours, so the offer is a pitch you can paste; (2) value players by potential, not only straight ROS points: a usage-based score (snaps, routes, targets, carries trending up) so a rising player is priced before his points catch up. (2) is ff-jarvis model work and needs a backtest against 12.97/12.99; (3) ROS gain is one lens, not the gate (David, 2026-10-07): keep an offer when a side gains on at least one of Now (lineup points next 1-2 weeks, e.g. a bye crunch), Push (next 3-4 weeks, a bubble team), Playoff run (weeks 15-17), ROS; weight by standing (a 1-4 team wants Now, a 5-1 team wants Playoff run, your own side too) and name the lens on the card ("Helps them now: 2 starters on bye in wk 7"); (4) byes are already priced (`games_left` drops them, `trades_value` gives a bye week to the backup, then the wire), so change no value, but say it on the card ("His bye is done", "Covers your wk 7 byes"); (5) later: score by change in playoff odds from a season sim (standings, schedule, weekly projections), which weighs Now vs Playoff run itself and flags an offer that puts a direct playoff rival over the top. (3)-(5) are ff-jarvis `trade_offers.py` work first. (2026-10-07)
- [ ] **Nav names like Yahoo, ESPN and Sleeper.** "Week" / "This week" and "Stats" don't land with David. Those apps all use TEAM/ROSTER, MATCHUP, PLAYERS, LEAGUE; years of habit should carry over. Candidates: Home for the Week group, Players for Stats (Players was its label 2026-09-25 to 2026-10-05). Storyboard a nav that maps to those four before renaming; leaf ids and hashes stay. (2026-10-07)
- [x] **A group tab opens its first view, every time.** Today the page returns to the last leaf a reader saw in a group. David expects League -> Roster and This week -> Digest on every click. Make a group click open its default leaf; the hash still restores a reload or bookmark. (2026-10-07)
- [ ] **Week ranks on the Digest.** Readers come to see where their players rank this week, and the Digest has no Week 5 ranks. Ideas: a booster-pack card that opens the reader's Roster; tier ranks on the Roster itself. Reference: Boris Chen's tiers, the community favourite for being easy to follow (borischen.co/p/05-half-ppr-flex-tier-rankings.html). Storyboard first. (2026-10-07)
- [ ] **D. Henry in Tier 4 despite a high projection.** Check Ranks' tier cut for RBs this week (`design/ranks.py`, natural breaks; RB rank follows books' implied points since 2026-10-05, METHODOLOGY 12.86-12.87). Find whether the tier, the rank or the shown points is wrong. (2026-10-07)
- [ ] **Matchups redesign.** The first card's purpose is unclear to David. Redesign the view from a storyboard. (2026-10-07)
- [ ] **Bold calls' failed-test line.** "Failed test (12.75): 10 of 24 right in-sample, under a coin flip. Reviewed after week 9" reads awkwardly on the page. Rewrite it in plain words or drop it. (2026-10-07)
- [ ] **Stats > Highlights.** Cards are too big and the lines aren't interesting enough. Shrink the cards and raise the bar for what counts as a highlight, or cut the view. (2026-10-07)
- [ ] **Back button assessment.** Back in some places lands somewhere unexpected; the breadcrumb is probably broken. Walk every view, tab, drill-in and overlay at 360px, press Back after each, and log each wrong landing as from / expected / got. History code: `js/chrome/layers.js`, `js/chrome/nav.js`, `js/surface/recap/state.js`, `js/surface/profile/gridlink.js`, `js/data/owner.js`. Done when each wrong landing is fixed and pinned by a test like `test_a_hash_opens_its_view`. (2026-10-06)
- [ ] **Team logo assessment.** Find where a team logo makes a view easier to read; League > Teams is the first candidate. Open question: fantasy team logos (Yahoo/ESPN avatars), NFL club logos, or both. Rank the views yes/no, storyboard the yes ones (STYLE.md), check what ff-jarvis already fetches before adding a source. (2026-10-06)

## Checks on a date

- [ ] Tue 2026-10-06, after the week turn: Preview > Past games shows week 4.
- [ ] Sun 2026-10-11: the Live TD reel matches the day's real touchdowns.
- [ ] Mon 2026-10-12, ~9:15 PM PT: the whole page turns to week 6 after the last final (One page week).
- [ ] On/after 2026-10-21: run the season scorecard trials once (`python -m model.season.season_scorecard --trials` in ff-jarvis) and record them in METHODOLOGY 12.60. Rerun the week-3 recap first: it lacks PHI @ CHI.
- [ ] 2026-11-11: review Start/Sit v3's record.

## Needs an iPhone

- [ ] Recap's Share PNG.
- [ ] Sound on the Roster clips player.
- [ ] Live clock and ESPN play wording, last planned for Mon ATL @ NO (2026-10-05); not confirmed.

## Waiting

- [ ] **Yahoo sign-in.** Blocked on Yahoo approving app `UuR5CedM` (last checked 2026-09-24). Spec: unit 2 in `~/.claude/plans/team-watch-next.md`.
- [ ] **ROS value.** ff-jarvis 12.97 passed its backtest on branch `ros-value`, unlanded; Ranks > Rest of season is storyboarded (2026-10-06).
- [ ] **Chain trades.** Storyboard started 2026-10-05.
- [ ] **Follow a game, part 2.** Part 1 landed 2026-09-28.
- [ ] **Third league.** Menu drill-in landed; the league-ID data work is open.

## Parked

- [ ] **ESPN QR fallback.** Only when a friend cannot use the league-manager setting or the phone bookmark.
