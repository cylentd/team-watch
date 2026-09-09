# Status

One line per active thread. Update the moment you stop working on something — captured now beats remembered later. Git already answers "what changed and why" (commit messages); this answers "why does it matter" and "what's next", the two things memory drops first.

| Thread | Branch | Status | Next action | Touched |
|---|---|---|---|---|
| Grade the prop model | not started | Week-1 lines are priced in ff-jarvis `data/props_model.json` (776 lines, model through 2025 wk18, METHODOLOGY §12.29). No test against outcomes yet; the model leans under at the book's lines and its largest edges are news it cannot see | After week-1 box scores post (Tue 2026-09-15): add a `grade` subcommand to `props_model.py` that joins the priced lines to the weekly file and reports hit rate by model bucket. Then, in order: injury report, opponent, role changes. Fix `props_client.py` TD rows (`player` is the offer's first participant, the real player is `side`; build.py works around it). DFS lineup separately needs a Yahoo contest CSV export | 2026-09-09 |
| Game-day live view | not started | Scoped only, no branch yet: a 4th surface showing both rosters live during games — score, clock, live fantasy points per starter. Data: ESPN fantasy league API (already wired, gives live points) + ESPN scoreboard API (clock/score, no auth). Reuses the existing roster-row layout with a live-pts column instead of trend/rank; no new drawer needed. Rough effort: half a day, mostly the ~30s poll loop during live windows | Build a new `#live` view + nav entry when David wants to start it, or wait until week 1 kicks off to test against real live games | 2026-09-09 |

## Closed (last 5)

Move a row here when a thread lands. Trim past 5 — git log is the permanent record, this is a working memory aid, not an archive.

| Thread | Landed | Outcome |
|---|---|---|
| Wire real props into builder | 2026-09-09, team-watch c72adb9 + ff-jarvis 97def07 | Builder runs on the live BettingPros market (DraftKings + Underdog) with a calibrated per-stat model behind model % and edge, market and kickoff filters, slip presets per window plus Underdog picks. Display only: no test against outcomes yet, see "Grade the prop model" |
