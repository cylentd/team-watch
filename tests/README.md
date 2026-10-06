# Tests: design and conventions

A test lives in the cheapest layer that can catch its defect. Commands are in the repo's
`CLAUDE.md` ("Testing"); this file says how to write a test. The standards behind it are the
`testing` skill's (`~/.claude/skills/testing/references/design.md`); this file is how team-watch
applies them.

## Layers, cheapest first

| Layer | Fixture that marks it | What belongs here | Cost |
|---|---|---|---|
| **python** | none | build-side logic in `design/*.py`, scripts, contracts | ms |
| **node** | `node_js` | `design/src/js/data/` logic: data in, data out | ~1 ms a call |
| **component** | `mount` (`tests/component.py`) | one surface drawn from a fixture slice: its rows, its taps, its layout at 360px | ~53 ms a load; full page 64 kept, 148 new (2026-10-05) |
| **build** | `built`, `page_file` | the assembled page's markup and injected blocks, no browser | one build a session |
| **browser** (e2e) | `browser` | journeys across views, navigation, the hash, overlays, Back | ~1 s a page load |
| **golden** | `snapshot` in `test_render.py` | the whole page per state, both viewports; review its diff, never regenerate blind | the slowest |

`conftest.layer_of` returns python, node, component, build or browser, from the test's fixtures:
a test that asks for `mount` is `component` even though `mount` uses Chromium underneath. Golden
is not a layer value: it is the browser tests in `test_render.py`. `mount` cannot load a partial
page (every view's draw function shares one script scope): it loads all JS and the CSS not
fenced to other views, and the saving is the kept context.

Moving down: a rule a Node test can prove is not asserted again in a browser test; the browser
test only proves the screen draws it. `tests/test_layer_ratchet.py` counts the full page loads
per test file, loaders in `tests/pages/` included; the count only goes down, and a new file's
allowance is 0. A test marked `journey` is not counted: it needs the full page. A module fixture
that opens one shared page for journey tests is counted once; list it with a note
(`test_profile_journeys.py`, 2026-10-06).

## New logic, test first

(2026-10-05) A view's logic goes in `js/data/` with its failing Node test written first; the
surface only draws it, and its browser test covers layout and taps. Touching an area moves its
logic-only browser tests to Node. `tests/test_layer_ratchet.py` counts pure `data/` calls made
through `page.evaluate` per file (108 when set): only down, and a new file has none.

## Writing a unit test

(2026-10-05) A JS function from data to data runs in Node, Python logic in Python. The `node_js`
fixture loads named files from `design/src/js` and calls a function in about a millisecond, no
build (`tests/jsunit.py`; `tests/test_js_hurt.py`: 0.07 s, 7.7 s in the browser).

## Writing a browser test

(2026-10-05) Take `browser` from `tests/conftest.py` (one Chromium per worker), never your own. A
full page load costs about 1 s, so a file's tests share a module-scoped page that resets what a
test changed (`'use strict'` in the reset, so a renamed global throws) and asserts no page error
after load; a test about loading itself opens its own. Every browser test asserts no page errors
(`test_render.watch_errors`). A missing fixture element is an `assert`, never a `pytest.skip`. A
test waits for a condition, never a duration: no `wait_for_timeout` or sleep (animations run on
the page's clock, `test_roster_cards.py` VCLOCK); `tests/test_honest_tests.py` enforces both.
Logic with no layout is not a browser test. `conftest.py` runs each file in groups of 12 tests, so
a shared page loads once per group and a long file still spreads out.

Every context has an owner (`conftest.keep`, 2026-10-05): one a test opens is closed when the test
ends, pass or fail; pages a module opens lazily and shares go through `SharedPages`, which
remembers a failed load so the module's later tests fail at once. More than 6 contexts open after
a test errors.

## Markers

| Marker | Meaning |
|---|---|
| `@pytest.mark.req("Ranks", ac="tiers break where points gap")` | the `design/DESIGN.md` section this test proves (its `## ` heading up to the first ` (`), and optionally which behaviour. `python scripts/trace.py` lists every section with its tests and the sections no test claims |
| `@pytest.mark.quarantine("2026-10-05 flaky: chat panel race")` | a known-flaky test: still runs everywhere except a gating run (`--no-quarantine`, which `run_tests.py` passes at land). Give a date and cause; `trace.py` lists quarantined tests with their age |
| `@pytest.mark.journey` | an end-to-end test that needs the full page: navigation, hash, Back, cross-view. Its page loads are not counted by the full-load ratchet |
| `@pytest.mark.area("ranks")` | impact area (`tests/impact.json`); test_render.py only |
| `@pytest.mark.render` | needs Chromium; `-m "not render"` skips it |

## Page objects (`tests/pages/<view>.py`)

- One class per view or surface, built from a Playwright page: `RanksPage(page)`.
- Intent-level methods: `pick_position("RB")`, `rows()`, `open_player(slug)`. A method returns
  plain data (dicts, lists, strings) the test asserts on; it never asserts.
- Every locator for that view is defined once, in its page object, by `data-testid` first, then
  role and label. A test file holds no selector.
- `data-testid` values are `<view>-<thing>`, kebab-case (`ranks-row`, `ranks-pos-tab`). They are
  test hooks only: no CSS or JS reads them.

## Proving a test

- **It fails when the behaviour breaks.** The testing skill's `mutate.py` (since 2026-10-06; the
  repo's own copy is gone) mutates the `js/data/` and `design/*.py` lines the branch changed, one
  operator at a time, and reports the share of mutants killed. `.testing.json` `mutate` names the
  files and the pytest command (`-m "not render"`); `scripts/mutate_tests.py` picks each file's
  tests: the ones naming it plus `impact.py`'s pick, minus the core and the whole-repo checks,
  light layers first. Land prints the score; below 60% it warns (`--gate` makes it fail). One file:
  `python $HOME/.agents/skills/testing/scripts/mutate.py --files design/src/js/data/stock.js`
- **It passes 10 times in a row.** `python scripts/run_tests.py --repeat-new 10` runs every test
  function the branch added or changed 10 times in parallel. Land runs it; one failure blocks.

## Goldens

The suite builds against `tests/fixtures/` (never ff-jarvis) and compares the rendered page, in
Chromium, to `tests/golden/render.json`. A refactor proves "no visual change" with an empty diff;
an intended change regenerates the golden with `pytest --update-golden` and the diff is the
review. `tests/test_budgets.py` holds the size ratchets: what is over budget today is listed with
its size and may only shrink.

## How land picks tests

(2026-09-27) `scripts/impact.py` maps the branch's paths to areas through `tests/impact.json`: a
change fenced to one view runs that view's tests, the core and its golden slice (a Ranks change:
~14 s, against ~65 s for everything). A path no area claims, shared CSS, and shared test setup
run everything; `content.json`, the order files, `scope.json` and the golden are read by what
changed inside them (since 2026-10-05; the docstring of `scripts/impact.py` says how). The
scheduled rebuild runs the whole suite twice a day, the net for whatever the map misses. A new
golden state belongs to the area its name starts with. Fixture files are never claimed by an
area: the build injects all of them into one page.

`scripts/run_tests.py` runs the same selection `land.ps1` does, on the files on disk, uncommitted
ones included; anything after `--` goes to pytest. `python -m pytest -m "not render"` runs
everything without a browser, ~30 s.

## Test history

(2026-10-05) Every pytest run and land is one JSON line in `.git/test-history/`, shared by all
worktrees; `python scripts/testlog.py` summarizes layers, trend, slowest files, flaky tests and
land phases. Read it before test-speed or flakiness work (it supersedes the hand-timed 2026-10-05
note: browser 830 of 3,122 tests, 725 of 782 worker-s). A nightly job runs the suite 3 times for
flakes.

## Exemplars and building blocks

Agents copy the patterns they see, bad ones included. Copy these.

| Layer | Exemplar | Why |
|---|---|---|
| python | `test_ranks.py::test_running_backs_are_ordered_and_ranked_by_the_books_number` | Exact lists; each `assert` message says the rule; `req` marker names the behaviour |
| node | `test_js_range.py` | `node_js` loader lists its files; one behaviour a test; missing-data cases beside the happy path |
| component | `test_ranks.py::test_the_back_list_follows_the_books_and_says_why_once_and_flex_does_not` | `mount` + `RanksPage`, no selector in the file, exact values, `errors == []` last |
| browser journey | `test_profile_journeys.py::test_the_sphere_opens_the_sheet_over_the_profile` | `journey`-marked, a page shared per viewport, every read through `ProfilePage`, Back checked |
| error path | `test_weather.py::test_no_backtest_file_means_no_cards_and_no_error` | A missing input still builds and draws the fallback rows; page errors asserted empty |

## Do not copy

The files with the most full page loads left (2026-10-06). They hold inline selectors and load the
page per test; `BACKLOG` and `FULL_LOADS` are in `test_layer_ratchet.py` and only shrink.

| File | Tracked by |
|---|---|
| `test_waiver_owner.py` | `FULL_LOADS` 5, `BACKLOG` 6 |
| `test_weather.py` | `FULL_LOADS` 5, `BACKLOG` 3 |
| `test_live_modal.py` | `FULL_LOADS` 5 |
| `test_roster_sheet.py` | `FULL_LOADS` 5 |
| `test_left_hurt.py` | `FULL_LOADS` 4, `BACKLOG` 9 |

`test_trade_edit.py` and `test_trade_offers.py` moved to `mount` with the trade finder; `test_teams_board.py`
moved with the Teams cards, `test_live_tabs.py` with Live's tabs, `test_live_tds.py` and `test_gamesheet_v2.py`
with Live's TDs tab and the game sheet (2026-10-06; the full-page `live` loader is gone).

Migrated, copy these instead: Ranks, profile, Digest, roster cards, Bets, the strip, Live TD clips,
the clip reel, the pack stage, Recap, the trade finder, Records tabs, Teams, Live tabs, Live's TDs tab
and the game sheet, Schedule, the Roster's brief, the League leaves, the leg sheet, Live for a new
reader, the team switch (their page objects are in `tests/pages/`).
`BACKLOG` counts `tests/pages/` too (since 2026-10-06): moving a `page.evaluate` call into a page
object does not lower it; moving the test to Node does.

## Building blocks

| Block | Where | Use it for |
|---|---|---|
| `node_js` | `conftest.py` | Call a `design/src/js` function in Node, ~1 ms |
| `built` | `conftest.py` | One in-process build of `tests/fixtures`, no browser |
| `page_file` | `conftest.py` | Path of the built page, for a browser to open |
| `browser` | `conftest.py` | The worker's one Chromium; never launch your own |
| `keep`, `SharedPages` | `conftest.py` | `keep` hands a context to the module; `SharedPages` opens a page once per key and remembers a failed open |
| `mount` | `component.py` | One surface on a kept context: `page, errors = mount("ranks")` |
| Page objects | `pages/`: `ranks`, `profile` + `profile_head` + `profile_sheet`, `digest` + `digest_live` + `digest_story`, `roster` + `roster_pack` + `roster_motion` + `roster_brief`, `schedule`, `parlay` + `parlay_build` + `legsheet`, `strip`, `live` + `live_tabs` + `live_tds` + `live_mine`, `gamesheet`, `teams`, `finder`, `records`, `league_recap`, `teamswitch` | The only place each view's locators live; `RanksPage` is the smallest model for a new one |
| `clips` | `pages/clips.py` | The Roster's Week plays rail and the "This week" list under it (`ClipsPage`); the clip theater's stubs |
| `recap` | `pages/recap.py` | This week > Recap: banner, tabs, leaders, touchdowns, games, Claude's calls (`RecapPage`), and the nav row it sits in (`RecapNav`) |
| `digest_story` | `pages/digest_story.py` | The Digest's story banner and Monday block with a planted game day (`DigestStoryPage`) |
| `league_chip` | `pages/league_chip.py` | The League's one team line on any leaf (`LeagueChip`); class selectors until `surface/league/switch.js` has test ids |
| `open_at`, `open_page` | `test_render.py` | A full page at a size and hash: `(ctx, page, errors)` |
| `watch_errors`, `LOAD_MS` | `test_render.py` | Collect page errors; the 30 s page-load timeout |
| `open_view` | `startsit_page.py` | A touch page already on Start/Sit |
| `VCLOCK` | `pages/roster_pack.py` | A virtual clock so motion tests wait on a condition, not a duration |
| `jsunit` | `jsunit.py` | The Node host behind `node_js`; read its docstring for the file-order rules |
| `req`, `quarantine`, `journey`, `area`, `render` | markers, above | Trace, flake quarantine, full-page journey, impact area, Chromium |

**Adding a block:** a page object goes in `tests/pages/<view>.py`; a new fixture goes in
`conftest.py` only when 3 or more files need it; list it in this table in the same change.

