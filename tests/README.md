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
| **integration** | `@pytest.mark.integration` (a fixture's layer wins) | a python test that runs a subprocess, git or a throwaway pytest, builds the page, or scans the whole repo; a slow one for a fixable reason is fixed, not marked | up to ~1 s |
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
  light layers first. The land gate prints the score and fails below 75% (target 90; since
  2026-10-06, `.testing.json` `mutate` holds both and a 120 s budget). One file:
  `python $HOME/.agents/skills/testing/scripts/mutate.py --files design/src/js/data/stock.js`
- **It passes 10 times in a row.** `python scripts/run_tests.py --repeat-new 10` runs every test
  function the branch added or changed 10 times in parallel. Land runs it; one failure blocks.

## Frozen tests and the backlog

(2026-10-06) The testing skill's land gate (`land.ps1` calls it once, after the tests) holds an
approved test still and lets bad ones only shrink in number. Its checks, in order: test-first,
backlog, lint, freeze, mutate (the skill's SKILL.md section 4 has each one's way out).

- **Test-first.** Source changed with no test changed fails, unless a commit says
  `Test-Exempt: <reason>`.
- **Mutation.** The branch's changed lines in `.testing.json` `mutate.include` are mutated; fewer
  than 75% killed fails (90% is the target). `-SkipMutate` leaves it out.

- **Frozen.** `tests/.frozen.json` hashes every top-level test, fixture and helper in `tests/`
  (by AST: comments and docstrings do not count), every `tests/golden/<area>.json` (listed one by one
  in `.testing.json` `freeze.files`: a new area's file is added there), and nothing else.
  Land writes it after the gate passes and folds it into the landed commit like `index.html`; a
  branch never commits it. Deleting an expected value, or a test, changes its hash and fails the
  land naming the entry. `.testing.json` `freeze.shrink` lists the ratchet constants
  (`test_budgets.py`, `test_layer_ratchet.py`) that may go down without reapproval. A test new on
  the branch is free until it lands. To change a frozen one on purpose: ask David, and after his
  yes add `Test-Reapproved: <entry> <reason>` to a commit message.
- **Backlog.** `.testing-backlog.json` lists today's tolerated violations under two keys and can
  only shrink: `lint` (the testing skill's `honest_tests.py`: fixed waits, tests with no assertion,
  conditional asserts; entries are `path::test::CODE`) and `limits` (tests over their layer's time
  limit; entries are node ids). A new violation fails. A fixed `lint` entry must leave the file
  (the gate says so): fix it and delete it in the same commit. A branch that only shrinks the
  backlog lands without `-Yes`.
- **Time limits** (`.testing.json` `limits`): per test, unit 50 ms, component 200 ms, integration
  1 s, e2e 15 s, all x2 because the suite runs in parallel; a layer is the `layer` property
  conftest records. `scripts/run_tests.py` loads the plugin, nothing else does. An ordinary or
  full run only lists the tests over their limit; one noisy timing never fails it. The land's
  10-run of new and changed tests (`--repeat-new 10`) fails a test whose fastest of the 10 runs is
  over its limit, unless it is in the `limits` backlog. Two wall-time budgets (`limits.suites`,
  2026-10-06): fast (unit + integration, so python, node and build) 10 s, component 35 s, which only
  goes down. Wall time swings 15-49 s with other sessions' load, so no land checks it. The weekly
  flake job (`scripts/flake_run.py`, Wednesday 3:30 am) runs each suite 3 times
  (`pytest -p pytest_limits --limits-suite <name>`), takes the fastest, logs it, and posts to
  Discord when a suite is over budget. First measure, loaded machine: fast 12.4 s, component 36.7 s.

## Goldens

The suite builds against `tests/fixtures/` (never ff-jarvis) and compares the rendered page, in
Chromium, to `tests/golden/<area>.json`, one file per area (since 2026-10-07; it was one 11.5 MB
`render.json` that every UI change rewrote). A state lives in the file of the area its name starts
with (`impact.area_of`), keyed viewport -> state. A refactor proves "no visual change" with an empty
diff; an intended change regenerates the golden with `pytest --update-golden` (add `--areas x` to
rewrite only that area's file) and the diff is the review. Never with `-n`: an area of over six
states is several slices, and two workers would each rewrite its one file. `tests/test_budgets.py` holds the size ratchets: what is over budget today is listed with
its size and may only shrink.

## How land picks tests

(2026-09-27) `scripts/impact.py` maps the branch's paths to areas through `tests/impact.json`: a
change fenced to one view runs that view's tests, the core and its golden slice (a Ranks change:
~14 s, against ~65 s for everything). A path no area claims, shared CSS, and shared test setup
run everything; `content.json`, the order files, `scope.json` and the golden files are read by what
changed inside them (since 2026-10-05; the docstring of `scripts/impact.py` says how). The
scheduled rebuild runs the whole suite twice a day, the net for whatever the map misses. A new
golden state belongs to the area its name starts with. Fixture files are never claimed by an
area: the build injects all of them into one page.

**E2e only if needed** (David, 2026-10-07; a replay of 71 lands: 60 ran everything, browser tests
were 59% of a land, the rule halves it and still caught 16 of 20 browser-only failures). When impact
says "everything", a gated run still runs every python, node, integration, build and component
test, but a browser test only in a file impact lists (`--e2e-only-in`) and golden only for the
areas a changed path owns (`--areas`, passed with the whole-suite pick too; only `test_render.py`
carries area marks); it prints how many browser tests it left. That count is the browser tests
outside impact's files, not the golden slices `--areas` dropped: pytest's own "deselected" count
holds those. A path or directory after `--` (`-- tests` too) is an explicit request: nothing is
dropped. `tests/test_smoke_views.py` (in `core`)
mounts every view once, so a shared change that breaks a view nobody touched still fails the land.
The rest runs after the land: `land.ps1` starts `scripts/postland.py` detached (from the main
checkout, so the landing worktree can be removed at once), the full suite on the landed commit in
`~/.team-watch-postland`, below normal priority and on at most a quarter of the worker budget.
Each failed test is rerun once; only a test that fails twice goes into the one Discord message,
which says how many failed once and passed (flaky) (`-NoPostland` skips it). `--full`, the 10-run
of new or changed tests and the scheduled runs are unchanged.

`scripts/run_tests.py` runs the same selection `land.ps1` does, on the files on disk, uncommitted
ones included; anything after `--` goes to pytest. `python -m pytest -m "not render"` runs
everything without a browser, ~30 s.

## Test history

(2026-10-05) Every pytest run and land is one JSON line in `.git/test-history/`, shared by all
worktrees; `python scripts/testlog.py` summarizes layers, trend, slowest files, flaky tests and
land phases. Read it before test-speed or flakiness work (it supersedes the hand-timed 2026-10-05
note: browser 830 of 3,122 tests, 725 of 782 worker-s). A weekly job (Wednesday 3:30 am,
`scripts/flake_run.py`) runs the suite 5 times in shuffled order and posts the flaky and broken
tests to Discord; a clean run posts nothing.

(2026-10-07) Each run's line also carries a `profile` block, so slowness can be pinned on the harness
or the test: `python scripts/testlog.py --profile` (the latest full run; `--last` any size; or a commit
prefix or index) prints worker-s split into tests (setup, call, teardown kept apart) and harness (process
startup, collection, session and module fixtures, pytest overhead, idle), the costliest fixtures by scope
and count, the costliest tests and each worker's busy share. The parts must sum to worker-s within 5%;
the rest prints as `unaccounted`. A session fixture's build is charged to the fixture, not to the first
test that asked for it. Written by `Profile` in `tests/runlog.py`; under xdist each worker sends its
block home in `workeroutput`.

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

The bulk migration ended on 2026-10-06 (full page loads 351 -> 22). What is left: `test_render.py`'s 10,
which are the golden and the whole-page checks and stay, and one load each in 12 small files (`FULL_LOADS` in
`test_layer_ratchet.py`). Those move to `mount` when someone next touches them; the ratchet only shrinks.
`BACKLOG` (20) is mostly in page objects (`pages/digest.py` 6, `pages/profile.py` 4): move those checks to
Node when you touch them.

Every other browser file is migrated; copy any of them. The page objects are in `tests/pages/`.
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
| Page objects | `pages/`: `ranks`, `profile` + `profile_head` + `profile_sheet`, `digest` + `digest_live` + `digest_story`, `roster` + `roster_pack` + `roster_motion` + `roster_brief` + `roster_sheet`, `waivers`, `weather`, `hurt`, `live_ball`, `schedule`, `search`, `accuracy`, `connect`, `clip_sheet`, `preview` + `preview_record` + `preview_handoff`, `news` (the old feed) + `news_report` (the injury report, 2026-10-09), `mates`, `parlay` + `parlay_build` + `legsheet`, `strip`, `live` + `live_tabs` + `live_tds` + `live_mine`, `gamesheet`, `teams`, `finder`, `records`, `tradehist`, `league_recap`, `teamswitch` | The only place each view's locators live; `RanksPage` is the smallest model for a new one |
| `clips` | `pages/clips.py` | The Roster's Week plays rail and the "This week" list under it (`ClipsPage`); the clip theater's stubs |
| `recap` | `pages/recap.py` | This week > Recap: banner, tabs, leaders, touchdowns, games, Claude's calls (`RecapPage`), and the nav row it sits in (`RecapNav`) |
| `digest_story` | `pages/digest_story.py` | The Digest's story banner and Monday block with a planted game day (`DigestStoryPage`) |
| `tags` | `pages/tags.py` | Player tags as drawn: the pill on a Roster and a Ranks row, the profile's list (`TagsPage`, 2026-10-08) |
| `league_chip` | `pages/league_chip.py` | The League's one team line on any leaf (`LeagueChip`); class selectors until `surface/league/switch.js` has test ids |
| `open_at`, `open_page` | `test_render.py` | A full page at a size and hash: `(ctx, page, errors)` |
| `pin_network` | `test_render.py` | Refuse every request off the machine, and answer a clip's picture (i.ytimg.com) with a fixed image, so no answer changes the markup (2026-10-06) |
| `watch_errors`, `LOAD_MS` | `test_render.py` | Collect page errors; the 30 s page-load timeout |
| `open_view` | `startsit_page.py` | A touch page already on Start/Sit |
| `VCLOCK` | `pages/roster_pack.py` | A virtual clock so motion tests wait on a condition, not a duration |
| `words` | `wording.py` | The page's text for a content.json key: `words("ranks.head")`. Never type a phrase the page shows; a rewording is then a content.json edit only (2026-10-07) |
| `jsunit` | `jsunit.py` | The Node host behind `node_js`; read its docstring for the file-order rules |
| `req`, `quarantine`, `journey`, `area`, `render` | markers, above | Trace, flake quarantine, full-page journey, impact area, Chromium |
| `integration` | marker, conftest `layer_of` | A test that runs git, a subprocess, a real build or a whole-repo scan: the integration layer and its 1 s limit, not unit's 50 ms |

**Adding a block:** a page object goes in `tests/pages/<view>.py`; a new fixture goes in
`conftest.py` only when 3 or more files need it; list it in this table in the same change.

