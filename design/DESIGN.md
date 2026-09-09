# Team Watch — design mock

Four surfaces, one console:

| # | Surface | Question it answers |
|---|---|---|
| 01 | My teams | What moved on my two rosters, and what do I do about it |
| 02 | The pool | Which player anywhere in the league is taking over a role |
| 03 | Parlay | Which of the model's best slips do I take, or what do I build myself |
| 04 | DFS | Which precomputed lineup do I load, or what do I build myself |

Build after editing `template.html`:

```
python design/build.py
```

## Live data in, sample signals on top

`build.py` reads the real roster files from `ff-jarvis` and injects them:

| Source | Injected as | Carries |
|---|---|---|
| `data/espn_rosters.json` | `LIVE_ESPN` | name, pos, team, **lineup slot**, injury status |
| `data/league_rosters.json` | `LIVE_YAHOO` | name, pos, team — **no slot, no status** |

The Yahoo file comes from a website scrape, so lineup slots are inferred by filling the league
lineup in roster order. The board says so in a caption rather than passing the guess off as fact.

Everything else — `trend`, `d`, `rank`, `news` — lives in the `SIGNALS` map in `template.html`,
keyed by player name. That is the seam: when `model.watch` produces real output, `SIGNALS` gets
replaced by its JSON and nothing else changes.

## The pool

Ranked on usage, never points. The anchor is a quadrant scatter: **x = change in snap/target
share, y = touchdown luck.** The four corners are the whole product.

| Quadrant | Meaning | Action |
|---|---|---|
| upper right | role and box score agree | confirmed, hold |
| upper left | points without the role | sell high |
| lower right | role without the points | **buy low** |
| lower left | both gone | fade |

Dot size is snaps. A lime ring means he is on one of my rosters. Table below repeats it as rows
so the numbers are readable.

## Parlay and DFS

Split into their own top-level tabs (2026-09-09) so the cart, not the 900-row props pool, is the
first thing a mobile reader reaches. Each tab: a collapsed-by-default "how this works" banner,
a gallery of the model's precomputed picks, then the cart-style custom builder, then the pool.

**Parlay**: the gallery is one card per kickoff window (never two calendar dates in one card —
`design/build.py`'s `assign_windows` splits a time-of-day bucket like "evening" into per-weekday
windows, e.g. "Thursday Night" / "Monday Night", when the week's games land on more than one
date) crossed with yards / TDs / mix scope, ranked by model edge, the best one badged. Load a
card into the cart or tap lines by hand; the cart warns when two legs share a game (correlated
legs are one bet, not two). Model %/edge and every book's price live behind each line's chevron,
not on the row.

**DFS**: a swipeable rail of precomputed lineups per strategy (greedy = max points, non-chalk =
for GPPs) each with a "Load into my lineup" button, then nine cart slots against a cap, salary
bar, summed ownership, and a styled empty slot — a second toggle picks Yahoo ($200 cap, live from
ff-jarvis's `data/dfs_pool.json`) or DraftKings ($50,000 cap, sample).

## Direction

Signal Desk — a dark trading-terminal console.

| Token | Meaning |
|---|---|
| lime `#c8ff2e` | active, starter, buy-low, brand |
| green `#37e08b` | trending up, confirmed |
| red `#ff5a52` | trending down, sell |
| amber `#ffb020` | caution, stale, correlated legs |
| violet / red marks | Yahoo / ESPN league identity only |

Positions are typographic, never coloured. Type: Bricolage Grotesque (display), Archivo (UI),
JetBrains Mono (all numerals).

## States already styled

Empty, loading skeletons, error (401 / token expired), stale cache. Plus in-place variants: the
scatter's no-data axes, `No data` trend chips, unranked players, and an empty DFS slot.

## Verified 2026-09-09

Desktop 1400px and phone 390px, no horizontal overflow on any of the four surfaces, no console
errors. Gallery/rail interactions checked headless: loading a gallery card or a strategy lineup
into the cart, expanding a leg's chevron without toggling it into the slip, tapping inside the
expanded detail without toggling it, the explainer's open state surviving a pagination re-render.
Rosters and team names are live. Trend, rank, news, pool, props and DFS content are sample.
