# Tests: design and conventions

A test lives in the cheapest layer that can catch its defect. Commands are in the repo's
`CLAUDE.md` ("Build, test, land"); this file says how to write a test.

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
per test file; the count only goes down, and a new file's allowance is 0. A test marked `journey`
is not counted: it needs the full page.

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

- **It fails when the behaviour breaks.** `python scripts/mutate.py` mutates the `js/data/` and
  `design/*.py` files the branch changed, one operator at a time, runs the tests `impact.py`
  picks for each, and reports the share of mutants killed. Land prints the score; below 60% it
  warns (`--gate` makes it fail).
- **It passes 10 times in a row.** `python scripts/run_tests.py --repeat-new 10` runs every test
  function the branch added or changed 10 times in parallel. Land runs it; one failure blocks.

## Exemplars and building blocks

Agents copy the patterns they see, bad ones included. Copy these.

| Layer | Exemplar | Why |
|---|---|---|
| python | `test_ranks.py::test_running_backs_are_ordered_and_ranked_by_the_books_number` | Exact lists; each `assert` message says the rule; `req` marker names the behaviour |
| node | `test_js_range.py` | `node_js` loader lists its files; one behaviour a test; missing-data cases beside the happy path |
| component | `test_ranks.py::test_the_back_list_follows_the_books_and_says_why_once_and_flex_does_not` | `mount` + `RanksPage`, no selector in the file, exact values, `errors == []` last |
| browser journey | `test_left_hurt.py`: fixtures `shared_pages`, `shared`; test `test_with_several_hurt_the_best_projection_leads` | `SharedPages` per viewport, errors asserted at teardown, exact order. Copy the fixtures, not its inline selectors |
| error path | `test_weather.py::test_no_backtest_file_means_no_cards_and_no_error` | A missing input still builds and draws the fallback rows; page errors asserted empty |

## Do not copy

| File | Signal (`evaluate`, selector, click, locator calls) | Tracked by |
|---|---|---|
| `test_profile.py` | 1,374 lines, 416 calls | `BACKLOG` 6, `FULL_LOADS` 5 |
| `test_digest.py` | 1,003 lines, 196 calls | `BACKLOG` 16, `FULL_LOADS` 28 |
| `test_roster_cards.py` | 170 calls | `FULL_LOADS` 20 |
| `test_parlay_grid.py` | 155 calls | `FULL_LOADS` 20 |
| `test_live_tdclips.py` | 99 calls; logic run through `page.evaluate` | `BACKLOG` 13, `FULL_LOADS` 18 |
| `test_strip.py` | 83 calls, a full load in nearly every test | `FULL_LOADS` 24 |

These hold inline selectors at scale, pure `data/` logic asserted in a browser, and a page
load per test. `BACKLOG` and `FULL_LOADS` are in `test_layer_ratchet.py` and only shrink.

## Building blocks

| Block | Where | Use it for |
|---|---|---|
| `node_js` | `conftest.py` | Call a `design/src/js` function in Node, ~1 ms |
| `built` | `conftest.py` | One in-process build of `tests/fixtures`, no browser |
| `page_file` | `conftest.py` | Path of the built page, for a browser to open |
| `browser` | `conftest.py` | The worker's one Chromium; never launch your own |
| `keep`, `SharedPages` | `conftest.py` | `keep` hands a context to the module; `SharedPages` opens a page once per key and remembers a failed open |
| `mount` | `component.py` | One surface on a kept context: `page, errors = mount("ranks")` |
| `RanksPage` | `pages/ranks.py` | The only place Ranks locators live; the model for a new page object |
| `open_at`, `open_page` | `test_render.py` | A full page at a size and hash: `(ctx, page, errors)` |
| `watch_errors`, `LOAD_MS` | `test_render.py` | Collect page errors; the 30 s page-load timeout |
| `open_view` | `startsit_page.py` | A touch page already on Start/Sit |
| `VCLOCK` | `test_roster_cards.py` | A virtual clock so motion tests wait on a condition, not a duration |
| `jsunit` | `jsunit.py` | The Node host behind `node_js`; read its docstring for the file-order rules |
| `req`, `quarantine`, `journey`, `area`, `render` | markers, above | Trace, flake quarantine, full-page journey, impact area, Chromium |

**Adding a block:** a page object goes in `tests/pages/<view>.py`; a new fixture goes in
`conftest.py` only when 3 or more files need it; list it in this table in the same change.

