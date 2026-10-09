# team-watch

A single self-contained HTML page, deployed on Vercel from the committed root `index.html`.
Vercel **is** git-connected: a push to `main` deploys within a minute, so `main` must always
carry a current build. Data comes from the sibling `ff-jarvis` repo; this repo renders it.

Global architecture rules apply here: `~/Github/agent-config/shared/architecture.md`.
Every new or changed view passes `design/STYLE.md` (controls, layout, motion) before it lands.

## Source vs generated

| File | |
|---|---|
| `design/src/shell.html` | **source** — the document: head, static markup, the two slots, `{{copy:key}}` |
| `design/src/content.json` | **source** — every user-facing string, `area.component.slot` -> text; the JS says `t("key")` and `--check` fails on a missing or unreferenced one |
| `design/src/css/**`, `design/src/js/**` | **source** — one concern per file, none over ~200 lines |
| `design/src/order.css.txt`, `order.js.txt` | the only order authority; `# pin:` lines say why an order is load-bearing |
| `design/src/scope.json` | **source** — every `css/surface/` file is `fenced` to the views that use it (`design/scope_css.py` rewrites its selectors at assembly, so it cannot style another view) or `shared` with the reason. A new surface file fails `--check` until it is one or the other (since 2026-09-27) |
| `design/assemble.py` | joins the parts into the template string; `--check` fails on an unlisted or missing part |
| `design/build.py` | inlines live data into the assembled template, writes both outputs, copies headshots to `heads/` |
| `api/_yt_channels.json` | **generated**, committed — the YouTube uploads playlist and embed flag per club for `api/clips.py`, from ff-jarvis's `youtube_channels.json` and `youtube_embed.json` by `python design/yt_channels.py`; rerun it when either changes (`tests/test_yt_channels.py` fails until you do; since 2026-10-05) |
| `preview_archive.json` | **generated**, committed at land like `trade_offers.json` — Preview's earlier weeks (frozen takes from ff-jarvis history `previews`) by `design/preview_archive.py`, fetched when a reader opens Past games, never injected (since 2026-10-05) |
| `trade_pins/` | **generated**, committed at land like `trade_offers.json` — ff-jarvis's pinned trade files (`index.json` and `<league>/<name>.json` per owner, ~4.5 MB) copied whole by `design/trade_pins.py`, each shape-checked where it enters; a player's trade page fetches the index, then the owner's file it names (ledger #65, since 2026-10-08) |
| `heads/` | **generated** — every ff-jarvis headshot, `<slug>.webp` (96px); the page names them by path (since 2026-09-24). `heads/lg/` holds the 256px ones ff-jarvis cuts for its board players (~230); the trading cards use those (since 2026-09-25) |
| `icons/` | **generated**, committed — the favicon and apple-touch icon, cut from Smug Blip (`lib/blip.js`) by `python design/icons.py`; rerun it after a change to the smug poses or the colour tokens (since 2026-09-29) |
| `index.html` | **generated** — full document, what Vercel serves |
| `design/index.html` | **generated** — fragment, what the Artifact publisher takes |

Never hand-edit the generated files. The pages are ~2.6 MB each (all live data inlined), and
`build.py` rewrites both in full on every run.

## Build and land

```
python design/build.py      # rebuild both outputs
.\scripts\land.ps1          # rebase, test-first gate, test what the diff can break, rebuild, fold into the commit, land
.\scripts\land.ps1 -Full    # the same, testing everything
```

The build fails on a lint error (`design/lint_css.py`), a contract violation (`design/contract.py`:
an injected block missing a field the JS reads), or a part the manifests do not agree on.

## Testing

TDD is the default; standards live in the `testing` skill. **Before writing any test, read
`tests/README.md`**: layers, markers, page objects, exemplars, building blocks, how land picks
tests, goldens, test history.

| Do | Run |
|---|---|
| One test | `python -m pytest tests/test_ranks.py::test_running_backs_are_ordered_and_ranked_by_the_books_number` |
| One file | `python -m pytest tests/test_<area>.py` |
| While working | `python scripts/run_tests.py` (what your edits can break, in parallel, ~12-15 s) |
| Full suite | `python scripts/run_tests.py --full` (in parallel, ~43-110 s) |
| One golden slice | `python -m pytest tests/test_render.py --areas ranks` (~10 s) |
| Regenerate golden | `python -m pytest --update-golden` (rewrites `tests/golden/<area>.json` for the areas it ran; add `--areas x` to limit; never with `-n`: an area's slices share one file) |
| Mutation | `python $HOME/.agents/skills/testing/scripts/mutate.py --files <file>` (`.testing.json` picks the files, `scripts/mutate_tests.py` the tests) |
| Before land | `.\scripts\land.ps1` runs the testing skill's `land_gate.py` itself |
| Where a run's time went | `python scripts/testlog.py --profile` (harness vs tests, fixtures, workers; `--last` for any run) |

- **Workers are shared** (since 2026-10-07): `run_tests.py` claims its `-n` from loadgate, the one
  budget for heavy work on this PC (agent-config `testsched/SPEC.md`; code at `$LOADGATE_CODE`, else
  `~/.agents/testsched`). A dev run gets what is free (at least 2), a land a fair share, the
  after-land run what is left. testsched also skips a test file whose inputs have not changed since
  its last pass (dev reads the cache; land and postland only write it, and postland checks it).
  `LOADGATE=off` bypasses both (`TESTSCHED=off`, `TW_SLOTS=off` are aliases). Time a change only
  with no other run holding workers: `python scripts/run_tests.py --dry-run` shows the claim.

- **E2e only if needed** (since 2026-10-07): a shared-file change runs every test but the browser
  ones outside its own areas; those run after the land (`scripts/postland.py`, Discord on failure).
  tests/README.md "How land picks tests".
- **Never a bare `python -m pytest`:** all ~3,600 tests one at a time, ~10 min (2026-10-05).
- **Land gate** (since 2026-10-06; what each check does: tests/README.md "Frozen tests and the
  backlog"): a landed test is frozen. Editing one fails the land unless a commit says
  `Test-Reapproved: <entry> <reason>`, written only after David says yes. Source with no test
  needs `Test-Exempt: <reason>`. `$TESTING_SKILL` points the scripts at an uninstalled skill checkout.
- **A new test file** is listed in `tests/impact.json` (`test_impact.py` fails otherwise).
- **Protected:** `tests/golden/*.json` (only through `--update-golden`, diff read as the review);
  `tests/fixtures/` (only with the golden regenerated); the ratchet numbers in `test_budgets.py`
  and `test_layer_ratchet.py`, which only shrink.

**Feature branches do not commit `index.html` or `design/index.html`.** The build runs once, at
land time, via `scripts/land.ps1`. This is not tidiness: both files are single blobs that change
completely on every build, so two branches that each carry one conflict on a million lines that
cannot be merged, only chosen. `.gitattributes` marks them `-diff merge=ours` (the `merge=ours`
attribute needs `git config --local merge.ours.driver true`, which `land.ps1` sets if missing).

**If they ever do conflict, never merge them.** Take either side and rebuild:

```
git checkout --ours index.html design/index.html
git rebase --continue
python design/build.py
```

## Two sessions at once

More than one Claude session works this repo. Two sessions in one checkout interleave edits in
the same source file and overwrite each other's `index.html` — it has already happened. So every
feature, not only the second, starts in its own worktree (`EnterWorktree` before the first edit),
and the main checkout stays on `main`, unedited. Notes that cost time to learn:

- `.\scripts\land.ps1` lands from the worktree itself (since 2026-09-24 `git land` pushes
  `HEAD:main` and never checks `main` out). A diff outside `tests/` and `*.md` changes the live
  page, so it needs `-Yes`, passed only after the user says yes. Landing ends the feature:
  `ExitWorktree` with `remove` puts the session back in the main checkout, and the session goes on.
- Lands queue (`scripts/land-queue.ps1`, since 2026-09-26): a ticket in `.git/land-queue`, shared by
  every worktree, holds `main` from after the first test run to the push, so a second land waits,
  printing whose it is behind, then rebases onto the first. Since 2026-10-05 the tests run before the
  queue, and again inside it only if `origin/main` moved meanwhile. The scheduled rebuild (the last step of the 5:50
  and 14:30 daily jobs and Tuesday's 2:00 week turn, in agent-config) takes the same queue. A dead session's ticket clears itself; a wait over 20 min
  gives up with nothing landed. A push from outside the queue still gets exit 2 from `git land`,
  and `land.ps1` rebases, rebuilds and retries once.
- Since fix 3 (2026-09-29) the build reads ff-jarvis's jobs' data checkout, `~/.ff-jarvis-history/data`
  (`sources.JOBS_DATA`, held to ff-jarvis's `model.JOBS_DATA` by a test), once its `.jobs-data` marker
  exists; before that, and with `TEAM_WATCH_DATA` set, the old path.
- `land.ps1` fetches the ff-jarvis checkout and refuses to build when it is behind origin/main
  (2026-09-29: the 2018 Records lineups landed in ff-jarvis and a build shipped without them). Fix it
  with ff-jarvis's `python scripts/sync-main.py`; `-AllowStaleData` builds anyway. `build.py` prints a
  WARNING line for the same case (`sources.ff_jarvis_behind`), so the scheduled rebuild's log shows it.
- A fresh worktree has no `data/feed.json` (untracked). The build falls back to reading
  `ff-jarvis` directly, so it still works; copy the file in if you want the freshness badges.
- Before touching a file the other session may hold, ask it. `git stash show --name-only` is the
  cheap way to prove a file really is dirty before claiming it is.

## Navigation

Two levels since 2026-09-21. **Five groups since 2026-10-08: Home · Team · Matchup · Players · League**
(David, storyboard home draft B, ledger #52; superseding Team · Matchup · Players · League · Bets, nav draft B,
ledger #32, the same day). Home is its own group of one view, the Digest; Bets' three views moved under Matchup
and the `bets` group is gone. Every leaf id, hash and `NAV_ALIAS` unchanged. A renamed group keeps its id:
Matchup is `week`, Players is `scouting`. Before: Week, League, Stats, Bets (2026-10-05). `NAV` in
`js/data/navmap.js` is the authority.

| group (id) | views in the row, left to right |
|---|---|
| Home (`home`) | Digest only, so no tab row |
| Team (`team`) | Roster, Waivers, Trades (Waivers leads on a Tuesday) |
| Matchup (`week`) | Live, Start/Sit (leaf `matchups`), Preview, Results (leaf `weekrecap`), Slips (leaf `parlay`), All lines (leaf `build`), DFS; Weather hidden. Highlights dropped 2026-10-08; `#highlights` opens Ranks |
| Players (`scouting`) | News, Ranks, Leaders, Work vs points, Usage, Schedule |
| League (`league`) | Recap, Teams, Records, Trade history (leaf `tradehist`, hash `#tradehist`, Yahoo's Madden Curse only; a tab of Records until 2026-10-08, David ledger #74) |

The table below is each view's history and detail; where it names a group, read the table above.
Each group holds the views that answer one question; `SURFACE` is always the **leaf**, never the group, and the group is derived from it.
A group with no view to show draws no button; a league that lacks a leaf (ESPN has no Records) shows fewer, and a link to the missing one lands on its nearest (`navFallback`).

| group | views |
|---|---|
| This week (id `week`, since 2026-09-26) | Digest (leaf `digest`, the default page except Tuesday, when Waivers leads): **since 2026-10-06 one job per Pacific weekday (DG_PLAN; DESIGN.md "Digest by day"): a 128px banner with the day's answer, the day's job card first, then the cards with data that day, five at most (since 2026-10-07; Tue adds, Wed usage movers, Thu Claude vs Vegas, Fri practice report, Sat SMASH, Sun Need to know, Mon tonight's game), then Rest of the week chips; the ticker rows below (Gems, Top 5, News, Recap rows) are superseded.** Before that: the league-wide week as a lead, then Need to know (new starters and who sits), then one-line rows, from ff-jarvis `weekly_digest.json` (no Highlights section since 2026-10-04: it was each Players view's first line, named Worth knowing until 2026-09-30; the Players > Highlights view was dropped 2026-10-08); from the week's first kickoff (2026-10-04) the headline is the top scorer, Right now appears beside Need to know, Need to know keeps only games not yet started, and the last game's block appears (Monday or Thursday night, one 80px block per game that opens its sheet, since 2026-10-05), all from Live's poll (DESIGN.md "After kickoff"); Right now shows 3 rows and More; the Digest and Recap banners never name the same subject (`js/data/leadsplit.js`: Claude's finished-week story about the top scorer leads Recap, the Digest then leads with the coming week); Recap (leaf `weekrecap`, hash `#weekrecap`, label Recap; `recap` is League's; since 2026-10-05): the week's results from ff-jarvis's recap file via `design/recap.py` (`LIVE_RECAP`), a banner (top scorer by yards and TDs, or Claude's story about him) over a Players / Scores / Claude / Accuracy bar (`tw-recap-tab`, Live's `.gd-tabs`): leaders with K and DST, Smashed / Busts / Left hurt, touchdowns; every game by window with Claude's pick and Hit or Miss, a game opening Preview's dossier; Claude's week; Accuracy (since 2026-10-05, hash `#accuracy`, plan U4): our average miss beside FantasyPros' on the same players per week and position, who was closer, season to date with its 95% range, from ff-jarvis `accuracy.json` via `design/accuracy.py` (`LIVE_ACCURACY`); drawn by `surface/recap/` (prefix `wr`), DESIGN.md "Recap"; News (leaf `news`, moved from Players 2026-09-29); Start/Sit (leaf `matchups`, labelled Matchups since 2026-10-06 with the picker behind the board's Compare two button, a full page Back closes; was Takes until 2026-10-03, moved from Players 2026-09-29): **since 2026-10-09 (ledger #94, draft A) the reader's lineup leads with our one swap, then our calls a kind and a page at a time with the record in their head, last week, the board last (DESIGN.md "Start/Sit"); the order below is superseded.** Before: a two-or-three player picker that says START or Coin flip, a matchup board per position with each position's best spot, then the record (SMASH, START, SIT graded apart since week 5; FantasyPros and Pitcher List for fun only), the SMASH card (our top 3 QB/TE, top 6 RB/WR, with main line and TD price, to Slips) and the bold calls (START/SIT where our rank and his season average disagree by 6+ spots; our own model only, since 2026-10-04, ff-jarvis METHODOLOGY 12.75; `LIVE_SS3` via `design/startsit_v3.py`); `LIVE_SSB` via `design/startsit_board.py`; DESIGN.md "Start/Sit"; Preview (leaf `preview`, since 2026-09-29): a slate of every game by kickoff window, a tap opens the game's dossier (Claude's take, opus/high, lines, matchup ranks, injuries, weather, rest and travel), the slate a rail beside it on a desktop, from ff-jarvis `game_previews.json` via `design/preview.py`; since 2026-10-05 a game that is over leaves the slate for Past games (Claude's season by Moneyline / Spread / Total, a ‹ Week N › stepper, every earlier week's previews from `preview_archive.json`), and a game's answer is one row per bet, Vegas beside Claude; DESIGN.md "Preview"; Weather (leaf `weather`, since 2026-09-26; out of the sub-row since 2026-10-05, `NAV_HIDDEN` in `chrome/nav.js`, to fit Recap at 360px: `#weather` and `navGo("weather")` still open it, from the Digest's Weather card and Preview): the games whose forecast moves scoring (proven positions only, from ff-jarvis's `weather_backtest.json`) with who they hit (each side's top QB, WRs and TE from the projections; no roster, the page is public), then every other game as one row; Live (leaf `live`; its own Gameday group until 2026-09-28; three tabs since 2026-10-05, `tw-live-tab`: My league, NFL, TDs (superseded: Matchup, Games, TDs, League, 2026-10-04); its league follows the picked team, so the league chips and `tw-live-league` are gone, My league leads with a scoreboard strip of the league's matchups (`data/gameday/strip.js`) and the picker sits inside Live; each game's clock is ESPN's scoreboard read in the browser; the clock line opens the game sheet, a centred modal since 2026-10-05 (STYLE.md "Overlays"; a phone adds a Prev · Close · Next footer), whose play lines bold every name; a live card shows who has the ball, the down and distance and a red-zone tag, from the same scoreboard's `situation` (verified live 2026-10-05; none at halftime); since 2026-10-05 a TD clips reel of official YouTube clips heads the TDs feed, fresh ones from `api/clips.py` every 5 min, DESIGN.md "Clips"; DESIGN.md "Live") |
| League (id `league`, since 2026-09-28; **Teams and League merged into it 2026-10-05**, plan U8) | Six leaves, the most a 360px sub-row holds: Roster, Waivers, Teams, Trades, Recap, Records (ESPN shows 5, with no Records; AYO 6, since Trades is the finder, 2026-10-06; ESPN 4 and AYO 5 until then: `navLeavesFor` in `js/data/navmap.js`). **One team line** (`surface/league/switch.js` `lgChipHTML`, on all six leaves since 2026-10-05, Roster's and Waivers' heroes gone: the team switch as the title, the league and record under it; a phone hides the switch, the header bar's is the one there): pick your team and every leaf draws its league (`lgFocusKey`, `data/league.js`); the Madden Curse / AYO / ESPN chips and `tw-league` are gone. A reader with no team: Roster asks, Waivers opens on the league's Most added list, the rest open for everyone. `#myrecap` and `#league` are `NAV_ALIAS` entries for Recap. **From the old My teams row:** Roster (since 2026-10-05 with a Week plays rail of the starters' NFL YouTube clips above the This week list, one card per clip that drags sideways, and a lime ring on a headshot; both open a full-screen player that keeps one YouTube player warm (Clips v2); ff-jarvis `clips.json` via `design/yt_clips.py`; DESIGN.md "Clips"), Waivers, then the team's league page, both leaves folded into Recap on 2026-10-05: League (ESPN teams: the week's recap and awards, the rivalry with this week's opponent, all-time records and champions since 2014) or My recap (leaf `myrecap`, Yahoo teams, since 2026-09-27: the team's own result, box score, standing, grudge and record-book lines). All from ff-jarvis `espn_league*.json` / `yahoo_league*.json` via `design/league_recap.py` and `design/league_back.py`, drawn by `surface/league/`; DESIGN.md "League" **From the old League row:** Recap (leaf `recap`) and Records (leaf `records`): the Yahoo league's week and all-time book, the same for every reader whatever team is picked (Claude's weekly roast, standings, every game with its box score, next week's grudge; trophy case and Halls of Fame and Shame by manager); Trades (leaf `trades`, the **trade finder** since 2026-10-06; it was the trade history until then): a chip per position (QB RB WR TE) with the reader's gap to the league median, opening on the most negative; the top 5 offers whose `get` holds that position (partner and record, You send / You get, the gain, To IR and You drop lines, Copy offer, Edit), then "Who's deep at <POS>" (every other team ranked by that column, tinted, its starters there; a team's name opens the finder filtered to it, "Trades with <team>", a button back to the chips), then Make your own offer (the edit page); no team picked shows the picker and one line; for all three leagues; the offers are `trade_offers.json` v2 (owner -> one flat list of offers, each with its `partner`), fetched on first open, never injected, `design/trade_offers.py`; drawn by `surface/finder/` and `surface/lboard/`; DESIGN.md "Trade finder". The old trade history is **League > Trade history**, leaf `tradehist` since 2026-10-08 (was Records' second tab, `rctabs.js`, gone; Records is only its records; the leaf shows where `LG_TRADES` has the league, the Madden Curse; `navFacts().tradehist`), from ff-jarvis `yahoo_trade_verdicts.json` via `design/league_trades.py`, drawn by `surface/trades/`; DESIGN.md "Trade history"); `#trades` opens the finder. Teams (leaf `teams`, since 2026-10-05; roster cards since 2026-10-06): one card per team in the league, over sort chips (Total, QB, RB, WR, TE): header, strength strip tinted against the league median (spare starters marked), starters one 20px row each, the bench as one line, and a foot ("Your team"; "This is my team", a quiet text link, for a reader with no team there; "Trades with them ›" at the right end of every other card once a team is picked, which opens the finder on it); all three leagues (ESPN too), the reader's own team pinned; `LIVE_TEAMS` via `design/teams.py`, drawn by `surface/lboard/`; DESIGN.md "Teams". Recap since 2026-10-05 puts the reader's own game first under a Yahoo league's masthead (`lgMineWeekHTML`, from My recap, 2026-09-27: the team's result, box score, standing, grudge and record-book lines), and keeps an ESPN league's plain recap, rivalry and history (was My teams > League). |
| Stats (id `scouting`; labelled Stats since 2026-10-05, Players from 2026-09-25, Scouting before; every leaf id and hash stays) | Sub-tabs by what they hold: Ranks, Leaders (leaf `board`), Work vs points (leaf `movers`, was Role), Usage (leaf `usage`, was Grid), Schedule (leaf `schedule`, in the row since 2026-10-06), each with one line saying what it holds (`navCaptionHTML`); any view reaches a player's row in Grid or Role with `navGoRow(leaf, slug)` (chrome/nav.js; the Digest's Gems rows carried a Grid link until 2026-10-06, Usage movers link Usage since). Views, unchanged: ~~Highlights (leaf `highlights`, 2026-09-29 to 2026-10-08)~~ dropped 2026-10-08 with its data (`highlights.json`, `LIVE_HIGHLIGHTS`); `#highlights` is a `NAV_ALIAS` entry for Ranks. Ranks (this week's projected rank per position and FLEX, in tiers; since 2026-09-26; the RB list, tiers and rank follow the books' implied points where a back has them, shown points unchanged, with a "No line" tag on a back the books left unpriced, since 2026-10-05, ff-jarvis METHODOLOGY 12.86 and 12.87; since 2026-10-05 each row carries the floor and ceiling, 8 in 10 games, from ff-jarvis `ranges`, and D/ST and K tabs on the picked league's scoring, K for Yahoo leagues only, with the next 3 weeks, who holds each and Streamer tags, from ff-jarvis `dst_projections.json`, METHODOLOGY 12.85, `LIVE_DST`; a second view tab, Rest of season, since 2026-10-06, via `navModes("ranks")`: a bump chart of the top 10 at QB/RB/WR/TE, rank by week, then rank, name and team, ROS points, from ff-jarvis `ros_value.json` via `design/ros.py` (`LIVE_ROS`, null without the file: no tab), METHODOLOGY 12.97; the profile's Season pane gains a Rest of season block; DESIGN.md "Rest of season"), Leaders (leaf `board`: who leads each stat, the #1's card then a list paged to one screen), Work vs points (leaf `movers`, labelled Role until 2026-10-05, Movers until 2026-09-29: RB/WR/TE ranked by what their work is worth, beside what they scored and last season's same gap, from ff-jarvis `role_board.json` via `design/role.py`), Usage (leaf `usage`, the weekly usage grid, labelled Grid until 2026-10-05), Schedule (leaf `schedule`, since 2026-10-05, plan U7; back in the sub-row since 2026-10-06, six tabs that scroll as one row at 360px, superseding: out of the sub-row, `NAV_HIDDEN`, because Stats' five tabs fill a 360px row, so `#schedule` and `navGo("schedule")` open it, from a link in Ranks): the 32 teams easiest first by the points the opposing defenses allow a position per game, next 4 weeks / rest of season / fantasy playoffs, the opponents by week with byes marked, from ff-jarvis `sos.json` via `design/sos.py` (`LIVE_SOS`, passed through; the page computes nothing), labelled context only, not tested as a predictor; drawn by `surface/sos/`, DESIGN.md "Schedule" |
| Bets | Slips (leaf `parlay`; since 2026-10-05 led by Top calls: the model's strongest lines in games still to play, side, chance and tier word, no edge vs the book's break-even since 2026-10-06, one tap to add; `surface/parlay/topcalls.js`), All lines (leaf `build`, was Build; its "Better price" chip was "Best odds"), DFS. The Slips player sheet is a centred modal since 2026-10-05 (STYLE.md "Overlays"); two legs from one game say the combined chance is not shown. DESIGN.md "Bets" |

The view is in the hash (`#usage`, `#roster`), so a reload, a bookmark and Back all land where they
point; the group is derived from the leaf, and only the view is in the URL (the grid's position and
week reset on purpose). `tests/test_render.py::test_a_hash_opens_its_view` pins it. Old names still
land: `#highlights` opens Ranks (2026-10-08), `#myrecap` and `#league` open Recap (2026-10-05), `#pool` opens Role (leaf `movers`, `NAV_ALIAS`), `#takes` and `#startsit` open Start/Sit (leaf `matchups`), and
Leaders keeps the leaf and hash `board`. Role has its own surface (`js/surface/role/`) since
2026-09-29; before that Movers was a mode of the Board (`test_movers_hash_opens_role`).
Every part shares one script scope, so a view's function names must be unique
(`test_js_syntax.py::test_no_top_level_function_is_declared_twice`).

A group click (phone `#tabbar` or desktop bar, the same `#nav` buttons) opens the same view every time, Tuesday
too (since 2026-10-07; it returned to the last leaf seen there before, and on a Tuesday it led with Waivers). The
view is `landingLeaf` in `js/data/landing.js` (pure, Node-tested, since 2026-10-09, ledger #91): the row's first
leaf, except **Matchup opens Preview** (Live while any NFL game is in progress, and on Sunday from the first
kickoff to the last game's end; a game is on for `LANDING_GAME_MS`, 4 h, after its kickoff) and **Players opens
Ranks**. The row's order is unchanged (Live still first in Matchup's). A view's own tab is not remembered between
visits either (`navForget`/`navLeft` in `data/tabrow.js`): leaving Live (My league / NFL / TDs and the TD feed),
Recap, Ranks (This week / Rest of season) or Slips (kickoff) forgets it, and a new visit's load clears the stored
Live and Recap tabs, so a visit opens the first tab; a reload or Back keeps it. A hash still wins.

With no hash, `navDefaultLeaf` in `js/chrome/nav.js` opens the Digest (the week league-wide; it was
Leaders, then briefly Ranks, on 2026-09-26) except on a Tuesday, when Waivers still leads.

Leaders pages instead of scrolling: `board/fit.js` measures, in the reader's browser, how many rows
fit under the #1's card (page 1, `BD_FIRST_SIZE`) and on a page without it (`BD_PAGE_SIZE`), so the
card and its Prev / Next end above the bottom edge (`test_leaders_page_fits_the_screen`).

`NAV` in `js/data/navmap.js` (drawn by `js/chrome/nav.js`, tested in Node by `tests/test_js_nav.py`) is the whole table; a group of one draws no sub-row. Every copy key is
spelled out literally, because `assemble.py --check` finds orphaned keys by scanning for literal
lookups and cannot see one built from a template. The sub-row (`#subnav`) lives **outside** `.navbar` and
sticks on its own. **Phone layout since 2026-10-05** (`css/chrome/phonenav.css`; the navbar was the bottom
bar until 2026-09-24, then the top bar, superseded): a header bar (`#hdrteam`: the reader's team as the team
switch, "Pick your team" with no pick; Ask on the right), one tab row (`#subnav`: the group's views as pills,
the open view's own tabs opening in place inside it: Live, Recap, Slips; each view declares them with
`navModes`, `js/data/tabrow.js`, and draws no bar of its own on a phone), and a bottom tab bar (`#tabbar`:
Home, Team, Matchup, Players, League since 2026-10-08; Team, Matchup, Players, League, Bets earlier that day; Week, League, Stats, Bets, Search before; one-handed
reach, David 2026-10-05). A desktop keeps the one bar of words.
Adding a view = one entry in `NAV`, one copy key, one branch in `render()`.

Player search (2026-09-22) is not a view: no `NAV` entry, no hash. On a phone it sits in the header
beside Ask (since 2026-10-08; the bar's fifth slot before), on a desktop it is the field after the groups and `/`; `js/data/search.js` joins every live player row by slug and ranks,
`js/chrome/search.js` is the sheet. Overlays push a URL-less history entry (`js/chrome/layers.js`),
so Back closes the profile, then search, before it ever changes the view. The slide-over drawer ("How this works") is a layer too since 2026-10-09, and a connected league opens its Roster through `navGo`, which writes the hash (`tests/test_back_button_flows.py`; the walk is `docs/back-button-walk.md`).

## Staying current in an open tab

The page carries its data inside itself, so a tab left open holds the build it loaded with, however
long it sits there. No cache header helps — the tab never asks again, and Vercel already serves the
page `max-age=0, must-revalidate`, so a reload is always fresh. **Do not add a `max-age`**: it would
only introduce staleness that does not exist today.

`build.json` (written by `design/build.py`, folded in by `land.ps1` like the two pages) holds a hash
of the injected data — never a clock, or every rebuild would claim new data. `js/chrome/fresh.js`
fetches it on a tab click and on the window regaining focus, never on a timer: the refresh runs once
a day and the week turns on a Tuesday. A different hash turns the DATA pill into a reload control,
naming the new week when there is one. Only over http(s); from `file://` there is nothing to ask.

The page's week is data, not the reader's clock (2026-09-28): `LIVE_SCHEDULE.week` is ff-jarvis's `page_week`
block (since 2026-10-05; `design/schedule.py` only reads it), and `schedWeek()` returns it. The whole site turns
at the first rebuild after the week's last game is final (the 9:15 PM PT Monday run), so every forward view says
that week and Monday night is still its game to play; backward views say "final tomorrow" until Tuesday 2:00
(DESIGN.md "One page week").

## Data

`design/sources.py` owns every read of an ff-jarvis file or feed block (feed first, file as
fallback); `design/build.py` orchestrates and no longer loads. It reads rosters, props, prop model,
player projections, Sleeper status, the DFS pool, and `usage_weekly.json` (the Grid, via
`design/usage.py`, whose feed key is `usage_grid` — plain `usage` is already watch.json), and
A visitor's own ESPN league is read at runtime by `api/league.py`, never baked in (DESIGN.md,
"Connected leagues"). `d_starters` (which defenses are missing starters this week, via `design/d_starters.py` as LIVE_D_STARTERS, 2026-10-06: a chip per short defense in Preview's box score and a note under the rank in the profile's Matchup pane; a fact, not a call, DESIGN.md "Defenders out"), `wire_watch` (the Waivers Breaking rail, via `design/wire_watch.py`; its field lists live in `contract.py`), `waiver_teams` (every other team's own Waivers cards, via `design/waiver.py` as LIVE_WAIVER_TEAMS keyed like `design/mates.py`, null without the file; a team with no entry shows the view it had before, ledger #22, 2026-10-07), `clips` (the Roster's YouTube clips, via `design/yt_clips.py`, 2026-10-05), `player_names` (jersey numbers and nicknames, via `design/player_names.py` as LIVE_NAMES, 2026-10-05), `usage_movers` (the Wednesday Digest, via `design/usage_movers.py` as LIVE_USAGE_MOVERS, null without the file; a row's `line` is Claude's sentence or the template fact, 2026-10-06), `weekly_digest` `gains` and `hurt[].practice` (passed through `design/digest.py`, 2026-10-06), `sos` `K` and `k_allowed` (kicker schedule and points each defense allowed, 2026-10-06), and `ros_value` (rest-of-season value, via `design/ros.py` as LIVE_ROS, whose loader lives there, 2026-10-06), and `player_tags` (the pills on Roster and Ranks rows and the profile's list, via `design/player_tags.py` as LIVE_PLAYER_TAGS, null without the file; ff-jarvis's own SLEEPER tag is dropped, POTENTIAL shows as Sleeper; DESIGN.md "Player tags", 2026-10-08). DFS projections come from ff-jarvis's `model.market.projections`; the page never
computes model numbers itself. Ranks' tiers (`design/ranks.py`, `LIVE_RANKS`) are cut at build
time from those same projections by natural breaks (1-D k-means, a fixed tier count per position),
and its rank is the one the roster cards use (`ranks.ranks_places`). Since 2026-10-09 (ledger #81) one projection has one home: Ranks prints the projections row's `pts` that every other view prints, orders and tiers each week_ranks list by it (the books' `rank_pts` and the producer's order no longer decide a row), and the cards' rank is the place Ranks draws. See `README.md` for the DFS CSV import and `design/DESIGN.md` for
the design system and the field contract.
