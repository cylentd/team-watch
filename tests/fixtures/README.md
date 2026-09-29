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
| `data/startsit_calls.json` | `load_startsit()` — Matchups: a backed and an unbacked start, a sit, two best spots, one without an expert rank |
| `data/pl_startsit.json` | `load_startsit()` — Pitcher List's calls, same week: one agrees with ours (Purdy), one contradicts it (Higgins) |
| `data/grades/2026-w2.json` | `load_startsit()` — the season record, ours behind Pitcher List's |
| `data/history/games/*.jsonl` | `load_schedule()` — week 2 (the pinned clock's week): DET @ SEA, WAS @ LA, MIA @ NE, JAX @ IND; week 3 KC @ SF; a row with no kickoff and a malformed line |
| `data/weather.json` | `load_weather()` — This week > Weather's four cases in week 2: LA a dome, IND retractable with a calm forecast, SEA windy (15 to 22 mph) and wet (70%), NE outdoor with no forecast yet. St. Brown's roster card (next game at SEA) shows the wind chip with his wx |
| `data/player_projections.json` `wx` | Amon-Ra St. Brown carries `wx: {adj: -1.06}` (feed block and file): Weather's "Who it hits" for DET @ SEA and his roster card's "−1.1 in his projection" |
| `data/game_previews.json` | `load_game_preview()` — This week > Preview, one game per kickoff window: PIT @ CLE Thursday (short week), JAX @ LA Sunday morning at Wembley (neutral, wind 17, upset), DET @ CAR 1:00 (rain 56%, Coker out, defense ranks), SF @ NYJ late (3 zones east, line flipped), ATL @ NO Monday (dome, no take, no rest/travel/site) |
| `data/player_projections.json` `weather_adjust` | Weather's "Already counted in our projections": wind QB, WR and TE and precip WR in since 2026-09-26 (feed block and file), the same cells as the live run; kickers "we don't project kickers" |
| `data/weather_backtest.json` | `load_weather_backtest()` — Weather's effects, arm a from the 2026-09-26 run: dome not proven, wind proven for QB, WR, TE and K but not RB, rain for WR and K, cold for K only (so NE reads QBs 1.5 · WRs 1 · TEs 0.5 · kickers 1.5 fewer) |
| `data/props_model.json` `logs` | the leg sheet's bars: Tee Higgins (11 games, the sheet keeps 10) and Chase Brown carry per-game usage `u` (one Higgins target null); St. Brown and Gibbs have none, the path without it (file and feed block) |
| `data/defense_form.json`, `data/sleeper_defense.json` | `load_defense()` — file only, no feed block: NYJ, SEA, GB (no prior season) and LA (the page's LAR); NYJ has two starters out plus a questionable starter and a hurt backup, which are dropped |
| `data/cache/roster_2026.parquet` | `nfl_roster()` — resolves Ja'Marr Chase's TD-only position |
| `heads/*.webp` | inlined headshots; Ja'Marr Chase has none (tests the missing-headshot path) |
| `feed.json` | `TEAM_WATCH_FEED` — feed-first copy of every block above |

The one rule: change any fixture only together with the golden render snapshot regenerated
(`python -m pytest --update-golden`), and read the resulting `tests/golden/render.json` diff as
the review of what the change did to the page.
