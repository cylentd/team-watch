# Team Watch

A console for two fantasy football teams — one on Yahoo, one on ESPN. It answers one question per
player: **what moved, and what do I do about it.**

Live: deployed on Vercel from `index.html`.

| # | Surface | What it shows |
|---|---|---|
| 01 | My teams | roster board with trend sparkline, position rank, news badge; player drawer; waiver swap cards; the players who start for **both** teams |
| 02 | The pool | every player who logged a snap, on a usage-against-luck scatter — role growing, points lagging, and the four quadrants that follow |
| 03 | Parlay | a gallery of the model's best precomputed slips, one card per kickoff window (never two calendar days in one card) crossed with yards/TDs/mix, plus a cart-style custom builder |
| 04 | DFS | precomputed lineups per strategy (greedy vs. non-chalk) in a swipeable rail, plus a cart-style custom lineup against a salary cap — Yahoo (live) or DraftKings (sample) |

Rosters and team names are pulled live from the `ff-jarvis` repo. Trend, rank, news, pool and
builder content are sample data, replaced later by the `team-watch` skill. See
[design/DESIGN.md](design/DESIGN.md) for the data contract and the design system.

## Build

```
python design/build.py
```

Edit `design/template.html`, never the generated files. The build writes two copies of the same
page: `index.html` at the root (full HTML document, what Vercel serves) and `design/index.html`
(fragment, what the Artifact publisher takes). Player headshots are inlined as data URIs, so
both files work offline.

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
design/template.html   source — all markup, CSS and sample data
design/build.py        inlines headshots, writes both outputs
design/DESIGN.md       design system + the field contract the skill must supply
index.html             generated — do not edit
```
