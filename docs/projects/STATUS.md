# Status

One line per active thread. Update the moment you stop working on something — captured now beats remembered later. Git already answers "what changed and why" (commit messages); this answers "why does it matter" and "what's next", the two things memory drops first.

| Thread | Branch | Status | Next action | Touched |
|---|---|---|---|---|
| Wire real props into builder | props-wiring (team-watch); ff-jarvis side landed on main 2026-09-09 | builder shows the live BettingPros market with model % and edge on 776 of 918 lines, market and kickoff filters, slip presets (best / morning / afternoon / evening / Underdog picks / mine): ff-jarvis `model.market.props_model` (v1, METHODOLOGY §12.29) runs as the `model` refresh step, `build.py` joins `market.props_model` per book line; rookies and novelty lines stay "pending" | Land `props-wiring` once the other session's teams-view commit is in (squash first, several commits). Grade the week-1 lines when box scores post (Tue 2026-09-15). Model gaps in order: injury report, opponent, role changes. Fix `props_client.py` TD rows (`player` is the offer's first participant, the real player is `side`; build.py works around it). DFS lineup separately needs a Yahoo contest CSV export | 2026-09-09 |
| Game-day live view | not started | Scoped only, no branch yet: a 4th surface showing both rosters live during games — score, clock, live fantasy points per starter. Data: ESPN fantasy league API (already wired, gives live points) + ESPN scoreboard API (clock/score, no auth). Reuses the existing roster-row layout with a live-pts column instead of trend/rank; no new drawer needed. Rough effort: half a day, mostly the ~30s poll loop during live windows | Build a new `#live` view + nav entry when David wants to start it, or wait until week 1 kicks off to test against real live games | 2026-09-09 |

## Closed (last 5)

Move a row here when a thread lands. Trim past 5 — git log is the permanent record, this is a working memory aid, not an archive.
