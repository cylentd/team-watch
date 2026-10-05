# Fixtures

Tiny, deterministic inputs for `design/build.py`, standing in for `ff-jarvis`'s `data/`. 7
players (Joe Burrow, Chase Brown, Tee Higgins, Brock Purdy, George Kittle, Amon-Ra St. Brown,
Jahmyr Gibbs) across CIN/SF/DET, plus Ja'Marr Chase as a TD-only, headshot-less, no-role case.

| File | Feeds |
|---|---|
| `data/espn_rosters.json` | `live_espn()` — read directly, no feed fallback |
| `data/league_rosters.json` | `live_yahoo()` — read directly, no feed fallback |
| `data/ayo_*.json` | the third league, AYO (2026-09-29), the first Yahoo league's shapes: `ayo_rosters` (Taylor Made for Sundays: Chase Brown on all three of David's teams, Gibbs Yahoo too, Purdy and Higgins ESPN too, Jefferson AYO only; one leaguemate, Don Wick), `ayo_settings` (the real AYO scoring: kicking 3/3/3/4/5, no misses), `ayo_league` (4 teams, weeks 1-2 decided), `ayo_league_box`, `ayo_league_recap` (week 2). No history, owners, managers, trades or case rosters: Records and Trades draw their empty state. `waiver_packet.json` carries an AYO league with Jaylen Warren on its wire alone |
| `data/sleeper_status.json` | `load_status()` — injury/depth badges |
| `data/bettingpros_props.json` | `load_props_raw()` — prop lines, 3 games/2 books |
| `data/props_model.json` | `load_model_raw()` — P(over), edge, stale/moved/norole |
| `data/slip_reasons.json` | `load_slip_reasons()` — the Slips board's why (2026-10-03), file only: Higgins, St. Brown, Kittle and Gibbs have a line, Lamar Jackson has none and is cut from LIVE_REASONS |
| `data/bettingpros_props.json`, `props_model.json`, `feed.json` LONG | Longest reception (2026-10-03): Higgins (DK 22.5, Underdog 23.5), St. Brown (27.5 / 28.5) and Kittle (DK 19.5 only) with `p_over: null`; `v.LONG` in all four logs (Kittle has no log) |
| `data/player_projections.json` | `load_player_proj()` / `model_points()` — DFS projections |
| `data/dfs_pool.json` | `load_dfs_pool()` — Yahoo DFS pool, incl. an FPPG-fallback row |
| `data/wrcb.json` | `load_wrcb()` — WR/CB upgrade/downgrade tags |
| `data/breaking_news.json` | `load_news()` — 5 items, one with an unparseable date |
| `data/startsit_calls.json` | `load_startsit()` — the two best spots the Start/Sit board leads with (Gibbs RB, Kittle TE); the v2 takes in it are no longer read (2026-10-04) |
| `data/startsit_v3.json` | `load_startsit_v3()` — Start/Sit v3 (2026-10-04, shaped by CONTRACT.md): week 6 with ten SMASH players across positions (Kittle with no line or price), four bold STARTs and five bold SITs (some with reasons, some without), and a record with week 5 graded (a START void, a for-fun line) and six last-week rows (hit, miss, void). The producer's own file may replace it |
| `data/trade_offers.json` | `load_trade_offers()` — League > Teams > Find trades (2026-10-05), file only (no feed block): ESPN's Purdy Big in Japan to Run It Back with two bold offers (one with a Questionable and an IR player) and one fair, Run It Back to Purdy bold only, AYO's Taylor Made for Sundays to Don Wick (an Out player), Don Wick back to Taylor Made absent, Yahoo empty |
| `data/history/games/*.jsonl` | `load_schedule()` — week 2 (the pinned clock's week): DET @ SEA, WAS @ LA, MIA @ NE, JAX @ IND; week 3 KC @ SF; a row with no kickoff and a malformed line |
| `data/weather.json` | `load_weather()` — This week > Weather's four cases in week 2: LA a dome, IND retractable with a calm forecast, SEA windy (15 to 22 mph) and wet (70%), NE outdoor with no forecast yet. St. Brown's roster card (next game at SEA) shows the wind chip with his wx |
| `data/player_projections.json` `wx` | Amon-Ra St. Brown carries `wx: {adj: -1.06}` (feed block and file): Weather's "Who it hits" for DET @ SEA and his roster card's "−1.1 in his projection" |
| `data/game_previews.json` | `load_game_preview()` — This week > Preview, one game per kickoff window: PIT @ CLE Thursday (short week), JAX @ LA Sunday morning at Wembley (neutral, wind 17, upset), DET @ CAR 1:00 (rain 56%, Coker out, defense ranks), SF @ NYJ late (3 zones east, line flipped), ATL @ NO Monday (dome, no take, no rest/travel/site). Confidence (2026-09-29): PIT @ CLE no edge, JAX getting 3 STRONG, DET giving 3.5 SOLID, SF getting 1.5 LEAN with no moneyline (`market_win` null, so no bar) |
| `data/preview_record.json` | `load_preview_record()` — Claude's graded weeks 1 and 2 (4 games each): 4-2-1 vs spread, one no-edge pass, a push, a game with no market win %, so closer on 4 of 7 |
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
