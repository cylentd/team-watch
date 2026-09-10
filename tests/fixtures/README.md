# Fixtures

Tiny, deterministic inputs for `design/build.py`, standing in for `ff-jarvis`'s `data/`. 7
players (Joe Burrow, Chase Brown, Tee Higgins, Brock Purdy, George Kittle, Amon-Ra St. Brown,
Jahmyr Gibbs) across CIN/SF/DET, plus Ja'Marr Chase as a TD-only, headshot-less, no-role case.

| File | Feeds |
|---|---|
| `data/espn_rosters.json` | `live_espn()` — read directly, no feed fallback |
| `data/league_rosters.json` | `live_yahoo()` — read directly, no feed fallback |
| `data/sleeper_status.json` | `load_status()` — injury/depth badges |
| `data/bettingpros_props.json` | `load_props_raw()` — prop lines, 3 games/2 books |
| `data/props_model.json` | `load_model_raw()` — P(over), edge, stale/moved/norole |
| `data/player_projections.json` | `load_player_proj()` / `model_points()` — DFS projections |
| `data/dfs_pool.json` | `load_dfs_pool()` — Yahoo DFS pool, incl. an FPPG-fallback row |
| `data/wrcb.json` | `load_wrcb()` — WR/CB upgrade/downgrade tags |
| `data/breaking_news.json` | `load_news()` — 5 items, one with an unparseable date |
| `data/cache/roster_2026.parquet` | `nfl_roster()` — resolves Ja'Marr Chase's TD-only position |
| `heads/*.webp` | inlined headshots; Ja'Marr Chase has none (tests the missing-headshot path) |
| `feed.json` | `TEAM_WATCH_FEED` — feed-first copy of every block above |

The one rule: change any fixture only together with the golden render snapshot regenerated
(`python -m pytest --update-golden`), and read the resulting `tests/golden/render.json` diff as
the review of what the change did to the page.
