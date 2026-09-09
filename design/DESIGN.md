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
so the numbers are readable, paginated 10 at a time (2026-09-09) once real usage data makes the
list run long — the sample data's 16 fits on two pages.

On mobile (2026-09-09) the chart draws to a taller, narrower geometry sized close to 1:1 with the
actual screen instead of the desktop box scaled down to ~35% (which is what forced a horizontal
swipe to read anything). Per-dot name labels drop at that size — 16 of them collide regardless of
box shape, and the table right below already names every player — dots stay tappable into the
same drawer. Quadrant corner labels shortened to one word each (`CONFIRMED`, `SELL HIGH`, `BUY
LOW`, `FADING`) at both sizes, the explanatory phrase folded into the intro line instead.

## Parlay and DFS

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
and its confidence (that IS the primary info here, not noise the way DK's model%/edge is), a
same set of gallery cards built from Underdog-eligible legs (conf ≥ 58%) instead of DK edge,
ranked by confidence. Switching the toggle clears the cart (a leg's meaning doesn't carry across
books). Either way: load a card into the cart or tap lines by hand; the cart warns when two legs
share a game (correlated legs are one bet, not two).

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
props or DFS's Yahoo salary export are in, the amber sample warning otherwise. My Teams and The
Pool stay sample (trend/rank/news and the whole Pool dataset are still placeholders).

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
