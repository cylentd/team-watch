# Team Watch

A console for two fantasy football teams — one on Yahoo, one on ESPN. It answers one question per
player: **what moved, and what do I do about it.**

Live: deployed on Vercel from `index.html`.

| # | Surface | What it shows |
|---|---|---|
| 01 | My teams | roster board with trend sparkline, position rank, news badge; player drawer; waiver swap cards; the players who start for **both** teams |
| 02 | The pool | every player who logged a snap, on a usage-against-luck scatter — role growing, points lagging, and the four quadrants that follow |
| 03 | Parlay | a gallery of the model's best precomputed slips, one card per kickoff window (never two calendar days in one card) crossed with yards/TDs/mix, plus a cart-style custom builder |
| 04 | DFS | precomputed lineups per strategy (greedy vs. non-chalk) in a swipeable rail, plus a cart-style custom lineup against a salary cap — Yahoo (live) or DraftKings (sample). Projections come from ff-jarvis's `model.market.projections` — half-PPR points for every player it has a rate for. A rookie with no game log is priced off his own line this week (tagged LINE); Yahoo's FPPG, rescaled per position, fills in whoever is left (tagged Y) |

Rosters and team names are pulled live from the `ff-jarvis` repo. Trend, rank, news, pool and
builder content are sample data, replaced later by the `team-watch` skill. See
[design/DESIGN.md](design/DESIGN.md) for the data contract and the design system.

## Build

```
python design/build.py
```

Edit the parts under `design/src/`, never the generated files. `design/assemble.py` joins the
parts in the order the two manifests give (`python design/assemble.py --map` says which part
owns which output line). The build writes two copies of the same page: `index.html` at the root (full HTML document, what Vercel serves) and `design/index.html`
(fragment, what the Artifact publisher takes). Player headshots are inlined as data URIs, so
both files work offline.

Both outputs are ~1.4 MB and are rewritten in full on every build, so a feature branch that
commits them conflicts with any other branch on a blob nobody can merge. **Feature branches do
not commit them; the build runs once, at land time:**

```
.\scripts\land.ps1        # rebase onto main, rebuild, fold into the commit, land
```

`.gitattributes` marks both `-diff merge=ours`, which needs a driver defined once per clone —
`git config --local merge.ours.driver true`. `land.ps1` sets it if it is missing. If the two
files ever do conflict, never merge them: `git checkout --ours index.html design/index.html`,
finish the rebase, then rebuild.

## Test

```
python -m pytest                   # everything, about 7 s
python -m pytest -m "not render"   # no browser, under a second
python -m pytest --update-golden   # after an intended visual change
```

The suite builds the page against `tests/fixtures/` (7 players, 3 games, every live path) and
checks: the parts assemble and the manifests agree; every injected block parses and meets the
field contract the JS reads; the theme lint has no errors; every part and function is within its
size budget; the assembled script parses; and the page, rendered in Chromium across every
surface and toggle at a desktop and a phone width, matches `tests/golden/render.json` (markup
plus the computed style of every styled class). `scripts/land.ps1` runs it before building.

The build also reads `ff-jarvis/data/{espn_rosters,league_rosters}.json` and injects the live
rosters. If those files are missing it falls back to the copies inside the template, so the page
always renders.

Yahoo's DFS pool in the Builder reads ff-jarvis's `data/dfs_pool.json` (via `feed.json`'s
`market.dfs` block, or that file directly) — a contest's own "Export Player List" CSV, imported by
hand with `python -m model.clients.dfs import <csv>` (Yahoo has no public API for this, and an
automated scrape is deliberately not built — see that module's docstring). Re-import before a build
to refresh salaries; without it the Yahoo mode falls back to sample data. Injury status prefers
ff-jarvis's Sleeper read (`data/sleeper_status.json`) over the pool's own Yahoo status column —
see `design/build.py`'s `load_status()`.

## Layout

```
design/src/shell.html  source — the document and its static markup
design/src/css/        source — style, one part per surface or component
design/src/js/         source — behaviour, data/ lib/ ui/ builder/ surface/ chrome/ main.js
design/src/order.*.txt the concatenation order, with the reasons it is load-bearing
design/assemble.py     joins the parts; --check, --map, --verify
design/contract.py     the fields each injected block must carry; a miss fails the build
design/lint_css.py     theme rules; an error fails the build
design/build.py        inlines headshots and live data, writes both outputs
tests/                 pytest suite; fixtures/ are the pinned inputs, golden/ the rendered snapshot
design/DESIGN.md       design system + the field contract the skill must supply
index.html             generated — do not edit
```
