# Status

One line per active thread. Update the moment you stop working on something — captured now beats remembered later. Git already answers "what changed and why" (commit messages); this answers "why does it matter" and "what's next", the two things memory drops first.

| Thread | Branch | Status | Next action | Touched |
|---|---|---|---|---|
| Wire real props into builder | main | props client live in ff-jarvis (DraftKings + Underdog, `data/bettingpros_props.json`); builder UI (`template.html` PROPS/SLIP) still hardcoded sample data; no per-stat prediction model exists to fill the "model %" / "edge" columns the card design assumes | Decide the model/edge question first (see options in session), then wire `feed.json market.props_bp` into `build.py`; DFS lineup separately needs a Yahoo contest CSV export, nothing pulls it yet | 2026-09-09 |

## Closed (last 5)

Move a row here when a thread lands. Trim past 5 — git log is the permanent record, this is a working memory aid, not an archive.
