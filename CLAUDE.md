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
| `heads/` | **generated** — every ff-jarvis headshot, `<slug>.webp` (96px); the page names them by path (since 2026-09-24). `heads/lg/` holds the 256px ones ff-jarvis cuts for its board players (~230); the trading cards use those (since 2026-09-25) |
| `icons/` | **generated**, committed — the favicon and apple-touch icon, cut from Smug Blip (`lib/blip.js`) by `python design/icons.py`; rerun it after a change to the smug poses or the colour tokens (since 2026-09-29) |
| `index.html` | **generated** — full document, what Vercel serves |
| `design/index.html` | **generated** — fragment, what the Artifact publisher takes |

Never hand-edit the generated files. The pages are ~2.6 MB each (all live data inlined), and
`build.py` rewrites both in full on every run.

## Build, test, land

```
python design/build.py      # rebuild both outputs
python -m pytest tests/test_<area>.py         # while working: the files for what you touched, seconds
python -m pytest -n auto --dist loadgroup     # everything, ~43 s on a quiet machine (was 68-91 s), 2026-10-05
python -m pytest --update-golden              # never with -n: every area rewrites the one golden file
python -m pytest -m "not render"              # no browser, ~30 s
python -m pytest tests/test_render.py --areas ranks   # one area's golden slice, ~10 s
.\scripts\land.ps1          # rebase, test what the diff can break, rebuild, fold into the commit, land
.\scripts\land.ps1 -Full    # the same, testing everything
```

Land tests by impact (2026-09-27). `scripts/impact.py` maps the branch's paths to areas through
`tests/impact.json`: a change fenced to one view runs that view's tests, the core and its golden
slice (a Ranks change: ~14 s, against ~65 s for everything). A path no area claims, shared CSS,
and shared test setup run everything; `content.json`, the order files, `scope.json` and the golden
are read by what changed inside them (since 2026-10-05; the docstring of `scripts/impact.py` says
how). The scheduled rebuild runs the whole suite twice a day, the net for whatever the map misses.
A new test file must be listed in `tests/impact.json` (`test_impact.py` fails otherwise); a new
golden state belongs to the area its name starts with. Fixture files are never claimed by an area:
the build injects all of them into one page.

Writing a browser test (2026-10-05): take `browser` from `tests/conftest.py` (one Chromium per
worker), never your own. A full page load costs about 1 s, so a file's tests share a module-scoped
page that resets what a test changed (`'use strict'` in the reset, so a renamed global throws) and
asserts no page error after load; a test about loading itself opens its own. Every browser test
asserts no page errors (`test_render.watch_errors`). A missing fixture element is an `assert`, never
a `pytest.skip`. A test waits for a condition, never a duration: no `wait_for_timeout` or sleep
(animations run on the page's clock, `test_roster_cards.py` VCLOCK); `tests/test_honest_tests.py`
enforces both. Logic with no layout is not a browser test. `conftest.py` runs each file in groups of
12 tests, so a shared page loads once per group and a long file still spreads out.
Every context has an owner (`conftest.keep`, 2026-10-05): one a test opens is closed when the test
ends, pass or fail; pages a module opens lazily and shares go through `SharedPages`, which remembers a
failed load so the module's later tests fail at once. More than 6 contexts open after a test errors.

Writing a unit test (2026-10-05): a JS function from data to data runs in Node, Python logic in
Python. The `node_js` fixture loads named files from `design/src/js` and calls a function in about a
millisecond, no build (`tests/jsunit.py`; `tests/test_js_hurt.py`: 0.07 s, 7.7 s in the browser).

Test history (2026-10-05): every pytest run and land is one JSON line in `.git/test-history/`, shared
by all worktrees; `python scripts/testlog.py` summarizes layers, trend, slowest files, flaky tests and
land phases. Read it before test-speed or flakiness work (it supersedes the hand-timed 2026-10-05 note:
browser 830 of 3,122 tests, 725 of 782 worker-s). A nightly job runs the suite 3 times for flakes.

New logic, test first (2026-10-05): a view's logic goes in `js/data/` with its failing Node test
written first; the surface only draws it, and its browser test covers layout and taps. Touching an
area moves its logic-only browser tests to Node. `tests/test_layer_ratchet.py` counts pure `data/`
calls made through `page.evaluate` per file (108 when set): only down, and a new file has none.

The build fails on a lint error (`design/lint_css.py`), a contract violation (`design/contract.py`:
an injected block missing a field the JS reads), or a part the manifests do not agree on. The
suite builds against `tests/fixtures/` (never ff-jarvis) and compares the rendered page, in
Chromium, to `tests/golden/render.json`. A refactor proves "no visual change" with an empty diff;
an intended change regenerates the golden with `pytest --update-golden` and the diff is the
review. `tests/test_budgets.py` holds the size ratchets: what is over budget today is listed
with its size and may only shrink.

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

Two levels since 2026-09-21. Four groups in the nav bar since 2026-10-05 (Week, League, Stats, Bets; five before Teams and League merged), each holding the views that answer one
question; `SURFACE` is always the **leaf**, never the group, and the group is derived from it.
A group with no view to show draws no button; a league that lacks a leaf (ESPN has no Records or Trades) shows fewer, and a link to the missing one lands on its nearest (`navFallback`).

| group | views |
|---|---|
| This week (id `week`, since 2026-09-26) | Digest (leaf `digest`, the default page except Tuesday, when Waivers leads): the league-wide week as a lead, then Need to know (new starters and who sits), then one-line rows, from ff-jarvis `weekly_digest.json` (no Highlights section since 2026-10-04: it was each Players view's first line, named Worth knowing until 2026-09-30, and it stays in Players > Highlights); from the week's first kickoff (2026-10-04) the headline is the top scorer, Right now appears beside Need to know, Need to know keeps only games not yet started, and a Monday night card appears for the last game, all from Live's poll (DESIGN.md "After kickoff"); Recap (leaf `weekrecap`, hash `#weekrecap`, label Recap; `recap` is League's; since 2026-10-05): the week's results from ff-jarvis's recap file via `design/recap.py` (`LIVE_RECAP`), a banner (top scorer by yards and TDs) over a Players / Scores / Claude / Accuracy bar (`tw-recap-tab`, Live's `.gd-tabs`): leaders with K and DST, Smashed / Busts / Left hurt, touchdowns; every game by window with Claude's pick and Hit or Miss, a game opening Preview's dossier; Claude's week; Accuracy (since 2026-10-05, hash `#accuracy`, plan U4): our average miss beside FantasyPros' on the same players per week and position, who was closer, season to date with its 95% range, from ff-jarvis `accuracy.json` via `design/accuracy.py` (`LIVE_ACCURACY`); drawn by `surface/recap/` (prefix `wr`), DESIGN.md "Recap"; News (leaf `news`, moved from Players 2026-09-29); Start/Sit (leaf `matchups`, was Takes until 2026-10-03, moved from Players 2026-09-29): a two-or-three player picker that says START or Coin flip, a matchup board per position with each position's best spot, then the record (SMASH, START, SIT graded apart since week 5; FantasyPros and Pitcher List for fun only), the SMASH card (our top 3 QB/TE, top 6 RB/WR, with main line and TD price, to Slips) and the bold calls (START/SIT where our rank and his season average disagree by 6+ spots; our own model only, since 2026-10-04, ff-jarvis METHODOLOGY 12.75; `LIVE_SS3` via `design/startsit_v3.py`); `LIVE_SSB` via `design/startsit_board.py`; DESIGN.md "Start/Sit"; Preview (leaf `preview`, since 2026-09-29): a slate of every game by kickoff window, a tap opens the game's dossier (Claude's take, opus/high, lines, matchup ranks, injuries, weather, rest and travel), the slate a rail beside it on a desktop, from ff-jarvis `game_previews.json` via `design/preview.py`; DESIGN.md "Preview"; Weather (leaf `weather`, since 2026-09-26; out of the sub-row since 2026-10-05, `NAV_HIDDEN` in `chrome/nav.js`, to fit Recap at 360px: `#weather` and `navGo("weather")` still open it, from the Digest's Weather row and Preview): the games whose forecast moves scoring (proven positions only, from ff-jarvis's `weather_backtest.json`) with who they hit (each side's top QB, WRs and TE from the projections; no roster, the page is public), then every other game as one row; Live (leaf `live`; its own Gameday group until 2026-09-28; four tabs since 2026-10-04, `tw-live-tab`: Matchup with mirrored lineups, Games, TDs, League; each game's clock is ESPN's scoreboard read in the browser; the clock line opens the game sheet, a centred modal since 2026-10-05 (STYLE.md "Overlays"), whose play lines bold every name; a live card shows who has the ball, the down and distance and a red-zone tag, from the same scoreboard's `situation` (verified live 2026-10-05; none at halftime); since 2026-10-05 a TD clips reel of official YouTube clips heads the TDs feed, fresh ones from `api/clips.py` every 5 min, DESIGN.md "Clips"; DESIGN.md "Live") |
| League (id `league`, since 2026-09-28; **Teams and League merged into it 2026-10-05**, plan U8) | Six leaves, the most a 360px sub-row holds: Roster, Waivers, Teams, Trades, Recap, Records (ESPN shows 4, AYO 5: `navLeavesFor` in `js/data/navmap.js`). **One chip** (`surface/league/switch.js`, the team switch): pick your team and every leaf draws its league (`lgFocusKey`, `data/league.js`); the Madden Curse / AYO / ESPN chips and `tw-league` are gone. A reader with no team: Roster asks, Waivers opens on the league's Most added list, the rest open for everyone. `#myrecap` and `#league` are `NAV_ALIAS` entries for Recap. **From the old My teams row:** Roster (since 2026-10-05 with a Week plays rail of the starters' NFL YouTube clips above the This week list, one card per clip that drags sideways, and a lime ring on a headshot; both open a full-screen player that keeps one YouTube player warm (Clips v2); ff-jarvis `clips.json` via `design/clips.py`; DESIGN.md "Clips"), Waivers, then the team's league page, both leaves folded into Recap on 2026-10-05: League (ESPN teams: the week's recap and awards, the rivalry with this week's opponent, all-time records and champions since 2014) or My recap (leaf `myrecap`, Yahoo teams, since 2026-09-27: the team's own result, box score, standing, grudge and record-book lines). All from ff-jarvis `espn_league*.json` / `yahoo_league*.json` via `design/league_recap.py` and `design/league_back.py`, drawn by `surface/league/`; DESIGN.md "League" **From the old League row:** Recap (leaf `recap`) and Records (leaf `records`): the Yahoo league's week and all-time book, the same for every reader whatever team is picked (Claude's weekly roast, standings, every game with its box score, next week's grudge; trophy case and Halls of Fame and Shame by manager); Trades (leaf `trades`): who won every trade 2018 on, from ff-jarvis `yahoo_trade_verdicts.json` via `design/league_trades.py`, drawn by `surface/trades/`; DESIGN.md "Trades"; Teams (leaf `teams`, since 2026-10-05): every team's projected lineup by position, tinted against the league median, spare starters marked, a row opens that team as a full page (no bottom sheets; Back or ‹ steps back), whose lime button finds bold and fair trades with it as the next page, or "This is my team" for a reader with no team in that league (the offers are `trade_offers.json`, fetched on first open, never injected; `design/trade_offers.py`); all three leagues (ESPN too), the reader's own team pinned; `LIVE_TEAMS` via `design/teams.py`, drawn by `surface/lboard/`; DESIGN.md "Teams". Recap since 2026-10-05 puts the reader's own game first under a Yahoo league's masthead (`lgMineWeekHTML`, from My recap, 2026-09-27: the team's result, box score, standing, grudge and record-book lines), and keeps an ESPN league's plain recap, rivalry and history (was My teams > League). |
| Stats (id `scouting`; labelled Stats since 2026-10-05, Players from 2026-09-25, Scouting before; every leaf id and hash stays) | Sub-tabs by what they hold: Highlights, Ranks, Leaders (leaf `board`), Work vs points (leaf `movers`, was Role), Usage (leaf `usage`, was Grid), each with one line saying what it holds (`navCaptionHTML`); any view reaches a player's row in Grid or Role with `navGoRow(leaf, slug)` (chrome/nav.js; the Digest's Gems rows carry a Grid link). Views, unchanged:  Highlights (leaf `highlights`, since 2026-09-29, the group's first: two Claude-written, number-checked lines each from Ranks, Leaders, Role and Grid, from ff-jarvis `highlights.json` via `design/highlights.py`, drawn as the Reel since 2026-09-30: one card per line, the number and its unit beside the player on his club's colour; the Digest showed each view's first line until 2026-10-04), Ranks (this week's projected rank per position and FLEX, in tiers; since 2026-09-26; the RB list, tiers and rank follow the books' implied points where a back has them, shown points unchanged, with a "No line" tag on a back the books left unpriced, since 2026-10-05, ff-jarvis METHODOLOGY 12.86 and 12.87; since 2026-10-05 each row carries the floor and ceiling, 8 in 10 games, from ff-jarvis `ranges`, and D/ST and K tabs on the picked league's scoring, K for Yahoo leagues only, with the next 3 weeks, who holds each and Streamer tags, from ff-jarvis `dst_projections.json`, METHODOLOGY 12.85, `LIVE_DST`), Leaders (leaf `board`: who leads each stat, the #1's card then a list paged to one screen), Work vs points (leaf `movers`, labelled Role until 2026-10-05, Movers until 2026-09-29: RB/WR/TE ranked by what their work is worth, beside what they scored and last season's same gap, from ff-jarvis `role_board.json` via `design/role.py`), Usage (leaf `usage`, the weekly usage grid, labelled Grid until 2026-10-05), Schedule (leaf `schedule`, since 2026-10-05, plan U7; out of the sub-row, `NAV_HIDDEN`, because Stats' five tabs fill a 360px row, so `#schedule` and `navGo("schedule")` open it, from a link in Ranks): the 32 teams easiest first by the points the opposing defenses allow a position per game, next 4 weeks / rest of season / fantasy playoffs, the opponents by week with byes marked, from ff-jarvis `sos.json` via `design/sos.py` (`LIVE_SOS`, passed through; the page computes nothing), labelled context only, not tested as a predictor; drawn by `surface/sos/`, DESIGN.md "Schedule" |
| Bets | Slips (leaf `parlay`; since 2026-10-05 led by Top calls: the model's strongest lines in games still to play, side, chance and tier word, edge vs the book's break-even, one tap to add; `surface/parlay/topcalls.js`), All lines (leaf `build`, was Build; its "Better price" chip was "Best odds"), DFS. The Slips player sheet is a centred modal since 2026-10-05 (STYLE.md "Overlays"); two legs from one game say the combined chance is not shown. DESIGN.md "Bets" |

The view is in the hash (`#usage`, `#roster`), so a reload, a bookmark and Back all land where they
point; the group is derived from the leaf, and only the view is in the URL (the grid's position and
week reset on purpose). `tests/test_render.py::test_a_hash_opens_its_view` pins it. Old names still
land: `#myrecap` and `#league` open Recap (2026-10-05), `#pool` opens Role (leaf `movers`, `NAV_ALIAS`), `#takes` and `#startsit` open Start/Sit (leaf `matchups`), and
Leaders keeps the leaf and hash `board`. Role has its own surface (`js/surface/role/`) since
2026-09-29; before that Movers was a mode of the Board (`test_movers_hash_opens_role`).
Every part shares one script scope, so a view's function names must be unique
(`test_js_syntax.py::test_no_top_level_function_is_declared_twice`).

With no hash, `navDefaultLeaf` in `js/chrome/nav.js` opens the Digest (the week league-wide; it was
Leaders, then briefly Ranks, on 2026-09-26) except on a Tuesday, when Waivers still leads.

Leaders pages instead of scrolling: `board/fit.js` measures, in the reader's browser, how many rows
fit under the #1's card (page 1, `BD_FIRST_SIZE`) and on a page without it (`BD_PAGE_SIZE`), so the
card and its Prev / Next end above the bottom edge (`test_leaders_page_fits_the_screen`).

`NAV` in `js/data/navmap.js` (drawn by `js/chrome/nav.js`, tested in Node by `tests/test_js_nav.py`) is the whole table; a group of one draws no sub-row. Every copy key is
spelled out literally, because `assemble.py --check` finds orphaned keys by scanning for literal
lookups and cannot see one built from a template. The sub-row lives **outside** `.navbar`: on a
phone the navbar is fixed to the bottom edge, and a `.modes-sub.dock` inside it lands in the slot
Parlay's and DFS's own switchers already occupy. Adding a view = one entry in `NAV`, one copy key,
one branch in `render()`.

Player search (2026-09-22) is not a view: no `NAV` entry, no hash. It is the bar's fifth slot on a
phone and `/` on a desktop; `js/data/search.js` joins every live player row by slug and ranks,
`js/chrome/search.js` is the sheet. Overlays push a URL-less history entry (`js/chrome/layers.js`),
so Back closes the profile, then search, before it ever changes the view.

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

The page's week is data, not the reader's clock (2026-09-28): `LIVE_SCHEDULE.week` is the week of
the next game with no final score (`design/schedule.py` `page_week`), and `schedWeek()` returns it.
So the pack, the brief and Weather turn with the recap and projections, at the Tuesday 2:00 week-turn rebuild.

## Data

`design/sources.py` owns every read of an ff-jarvis file or feed block (feed first, file as
fallback); `design/build.py` orchestrates and no longer loads. It reads rosters, props, prop model,
player projections, Sleeper status, the DFS pool, and `usage_weekly.json` (the Grid, via
`design/usage.py`, whose feed key is `usage_grid` — plain `usage` is already watch.json), and
A visitor's own ESPN league is read at runtime by `api/league.py`, never baked in (DESIGN.md,
"Connected leagues"). `wire_watch` (the Waivers Breaking rail, via `design/wire_watch.py`; its field lists live in `contract.py`), `clips` (the Roster's YouTube clips, via `design/clips.py`, 2026-10-05), and `player_names` (jersey numbers and nicknames, via `design/player_names.py` as LIVE_NAMES, 2026-10-05). DFS projections come from ff-jarvis's `model.market.projections`; the page never
computes model numbers itself. Ranks' tiers (`design/ranks.py`, `LIVE_RANKS`) are cut at build
time from those same projections by natural breaks (1-D k-means, a fixed tier count per position),
and its rank is the one the roster cards use (`projections.position_ranks`). See `README.md` for the DFS CSV import and `design/DESIGN.md` for
the design system and the field contract.
