# Back button walk, 2026-10-08

Walked at 360px on the fixture build (Playwright against the built page, SEED clock). Rule: a view change is in the hash, so Back returns to the previous view; an overlay is one URL-less entry, so Back closes it first. Tabs inside a view (`navModes`) and the team switch's pick are not entries: Back leaves the view. Group clicks open the group's first view (unchanged).

## Wrong landings

| # | from | expected | got | status |
|---|---|---|---|---|
| 1 | Page opened with no hash, tap any group, Back | Digest | stays on the tapped view (blank hash ignored) | fixed |
| 2 | Preview dossier open, tap another pill or group, Back | Preview, then the view before | Preview, then a second Back does nothing (dead entry) | fixed |
| 3 | Start/Sit Compare open, tap another pill, Back | same as 2 | same as 2 | fixed |
| 4 | Search, a result's profile, grid link; Back | Slips, then the view before | Search sheet closed by the hash write, dead entry behind | fixed |
| 5 | Same, via the profile's team pill (roster) | same as 4 | same as 4 | fixed |
| 6 | On Records (Yahoo), pick the ESPN team (lands on Recap), Back | the view before Records | `#records` entry showing Recap | fixed |

Cause of 2 to 5: setting `location.hash` fires `popstate`, which closed the topmost layer and left its entry behind. `layersUnwind` (chrome/layers.js) now closes layers and pops their entries before a view change.

## Walked, correct

Every group and pill in sequence and back (21 views); search sheet, profile, Escape and Back; profile close button; Preview dossier Back; Recap tabs (Back leaves the view, by rule).

## Open (not fixed)

| from | note |
|---|---|
| Connect a league succeeds | `connectSubmit` sets `SURFACE = "roster"` without writing the hash; URL keeps the old view. Needs a connect-flow test with the network stubbed. |
| Reload with an overlay open | The restored entry keeps `history.state.layer`, so one Back does nothing visible. |
| Recap game to Preview dossier, Live game sheet, trade edit page, clip sheet, pack | Not walked this pass; they use the same layer helpers. |
