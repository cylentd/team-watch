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

## Second walk, 2026-10-09 (after the Home / Team / Matchup regroup)

| # | from | expected | got | status |
|---|---|---|---|---|
| 7 | DFS or Slips, "How this works" drawer open, Back | drawer closes, view stays | view changed, drawer left open over it (`showDrawer` pushed no entry) | fixed |
| 8 | A league connected through the sheet | URL `#roster`, Back returns to the view before | URL kept the old view (`SURFACE` set without the hash) | fixed |

Walked, correct: every group and pill in the new row (Home, Team, Matchup, Players, League; 19 steps) and back, with the active group and pressed pill matching each entry; Live game sheet, clip sheet, leg sheet, search, Connect, profile, Preview dossier (opened by a Digest card, a Recap game or Ranks), each closed by Back and by its own close; trade finder Edit and a trade page's Make your own offer (Back closes, a pill tap unwinds first); the trade page's Trades link (a step forward by its label; Back returns to the page); the team switch on a trade page (replaces the entry).

## Open (not fixed)

| from | note |
|---|---|
| Reload with an overlay open | The restored entry keeps `history.state.layer`, so one Back does nothing visible. Clearing the marker still leaves one duplicate step. |
| Ask chat panel | Deliberately not a layer (chat.js header): it stays open across views. Back leaves the view with it open. |
| Tabs inside a view (Live, Recap, Ranks' Rest of season) | Not entries, by the rule above. Making each a step is a decision for David. |
