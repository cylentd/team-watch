# Chapter 3: Best pickups

## Current shorter cut

November 6, 2026: David requested faster pacing and no weekly points beside Love's
QB ranks. The infographic now runs 50.077-58.077: the supporting pair lands at
52.077, Love at 54.077, and the rank-only week strip follows at 56.077. The PAR
totals still explain the three pickups' order. This supersedes the longer timing
below; the proposed tunnel treatment remains separate from this pacing correction.

## Approved cinematic revision

David requested a more cinematic scene and QB ranks instead of scores during phone review
on November 5, 2026. David approved this storyboard; the existing pickup
scene has not been rebuilt. Keep its 50.077-62.077 interval and the title **Best pickups.**

Use a broadcast tunnel with three staggered portrait screens on a dark, dimensional
floor. The camera travels past the supporting pickups toward Love rather than watching
three flat cards populate a grid. Stadium light comes from the screen surrounds and
recessed floor fixtures, stays behind the text, and settles after each landing.

| Film time | Camera and subject action | Exact visible copy |
|---|---|---|
| 50.077-52.077 | Carry the trade wipe into a low diagonal dolly along the screens; Schultz rises into the near position and settles on the bar. | Best pickups. / #3 / D. Schultz / COOKed |
| 52.077-54.077 | Pass Schultz; Wilson advances into the focal position, with his manager badge anchored beside him. | #2 / E. Wilson / Aura |
| 54.077-56.077 | Accelerate gently toward the largest screen, then ease out as Love lands on the phrase seam. Supporting screens recede and dim. | #1 / J. Love / Sausage |
| 56.077-58.077 | Hold the hero composition for two seconds with a restrained forward drift. No new text. | #1 / J. Love / Sausage |
| 58.077-59.427 | Remain on the same stage; six rank panels reveal beside Love as a single continuous sweep. | W3 QB16 / W4 QB17 / W5 QB8 / W6 QB6 / W7 QB13 / W8 QB6 |
| 59.427-62.077 | Hold all six ranks, Love and Sausage together; a slow push supplies motion without moving the reading target. | Same copy; no points or method sentence |

Desktop uses the runway's horizontal depth and one row of six weeks. On phones the
supporting screens enter from below and recede behind the hero, without a wide lateral
whip. Love's feature frame remains at least 40% of frame height; ranks settle in two
rows of three next to or beneath his anchored name. All text stays upright and sharp.

Reuse the player portraits, manager badges, fonts, silver wipe, existing bar/phrase
markers, rank receipts and resource lifecycle. Build the layered set, camera-relative
screen movement and rank-first layout. Do not change the chapter duration or music edit.

The ranks above are weekly positional finishes already present in `edition.json`
`pickups.top[0].weeks`; they are not Love's overall season rank. The producer's
`weekly_rank` compares NFL players at the same position that week with the league's
interception scoring adjustment. The top-three pickup order still uses the existing
points-added method; removing the point totals from the screen does not change that
selection or invent a cross-position QB ranking. The proposed scene removes the
visible +20.4/+25.7/+40.5 totals, weekly fantasy points and method subline.

Build the approved camera treatment and rank-only copy, then review the live animatic.
The previously approved implementation follows as the historical baseline.

Three cards rank the league's best pickups through Week 8. David approved this storyboard on
November 5, 2026. It replaces the Love-only chapter below.

## Twelve seconds, three cards

Revised November 5, 2026 (David): one bar added so #1 holds 2 s on his own, and the subline cut to fit the reading rule.

| Film time | On screen | Copy |
|---|---|---|
| 50.077 | Whip in off the trade tracker; the title rises. | Best pickups. / Points over who he replaced |
| 52.077 | #3 card lands (bar line). | #3 · D. Schultz · COOKed · +20.4 · 3 starts |
| 54.077 | #2 card lands (bar line). | #2 · E. Wilson · Aura · +25.7 · 6 starts |
| 56.077 | #1 lands largest on the phrase seam. | #1 · J. Love · Sausage · +40.5 |
| 56.077–58.077 | #1 holds 2 s; the stage drifts in slowly. | |
| 58.077 | Cut to waiver-starts (bar line); #3 and #2 dim; his six weeks fill. | W3 19.5 QB16 · W4 14.1 QB17 · W5 25.3 QB8 · W6 21.2 QB6 · W7 18.0 QB13 · W8 22.5 QB6 |
| 58.5–62.077 | Reading hold with a slow push. | |

The film now ends at 62.077. ~~60.077~~. Wins swung stay off screen.

| Beat | Length | Hold | Words counted |
|---|---|---|---|
| waiver-claim | 8 s | 2 s | 21 (title, subline, #3 and #2 cards) |
| waiver-starts | 4 s | 3.5 s | 5 (#1's card; the weekly numbers are scanned, not read) |

The reading rule is about 3 words a second plus 1 s, so 21 words need 8 s.

| Layout | Cards |
|---|---|
| Desktop | Left to right #3, #2, #1, one floor; #1 is the largest, its weeks in one row of six |
| Phone (390x844, 360x800) | #1 on top at 40% or more of frame height, weeks in two rows of three; #2 and #3 side by side under it |

- **Data:** every number comes from `edition.json` `pickups`, read by `waivers-data.mjs`. A week with no rank prints "out" (Wilson, W8).
- **Copy:** `waivers-copy.mjs`; team names are the short names from the film copy.
- **Timing:** two `chapter: 3` beats in `timing.json`, 8 s and 4 s (~~6 s and 4 s~~). The beat ids stay `waiver-claim` and `waiver-starts`, so `film.mjs`, `film-copy.mjs` and `trades-view.mjs` are unchanged.
- **Stills:** `.claude/review/ch3-pickups/`, six moments at three sizes. The 12 s version: files ending `-v2`, five moments at 1440x900, 390x844 and 360x780.

## Superseded: the waiver claim that stayed (November 5, 2026)

Superseded the same day by Best pickups above. Kept as the record of the Love-only version.

For Madden Curse league viewers who know the managers, this follows the draft receipts and
Aura trade tracker. David authorized posting the storyboard and building it overnight on
November 5, 2026. This is an animatic, not final visual acceptance.

## Eight seconds on one roster stage

| Film time | Camera and subject | Exact copy | Reading and music |
|---|---|---|---|
| 50.077–52.077 | Carry Sausage out of the fan under a broadcast wipe. Love rises into a QB roster slot; the view settles. | A quarterback off waivers. / J. Love / SAUSAGE | Bar-line entrance, no invented percussion hit. |
| 52.077–54.077 | Claim receipt lands beside Love. Backlight moves behind the portrait. | CLAIMED SEP 23 | Bar-line landing, two-second hold. |
| 54.077–56.077 | Push closer. Six weekly lineup slots fill in one continuous reveal beside the subject. | Six straight starts. / W3 W4 W5 W6 W7 W8 | Same-stage continuation, no second wipe. |
| 56.077–58.077 | Contribution total lands; complete composition holds with a gentle push. | 120.56 lineup points. | Phrase seam at 56.077; two-second payoff. |

Desktop groups portrait and headline with six slots alongside. Phones put the portrait above
two rows of three slots, with headline and total adjacent. Effects stay clear of text. Reuse
the local Love portrait, Sausage badge, fonts, music, wipes and controls. Build the roster slot,
week reveal, data boundary and responsive pose. Existing Blip movement remains untouched.

## Evidence through Week 8

Production root: `C:/Users/David/.ff-jarvis-history/data`, checked November 5, 2026.

- `history/transactions/2026-09-23.jsonl`, Jordan Love add record at 01:14 PDT: Sausage
  claimed him via waiver on September 23, 2026. Not a free-agent pickup.
- `yahoo_league_box.json`, weeks 3–8, team 12 away QB starter: 19.48, 14.08, 25.28,
  21.24, 17.96, 22.52. Six starts total 120.56 lineup points.
- `yahoo_league.json`, team 12 in those weeks: W, L, L, W, W, L. This is contribution,
  not value, PAR, a season-saving claim or proof that the claim caused wins.
- Article agreement: `design/src/content.json`, `midseason.team.12.report`.
- The November 4 roster still holds Love, a post-cutoff cross-check only.

Unused gaps: waiver bid, claim priority, manager intent and counterfactual wins. No invented
claims, past-season history or new PAR calculation.

## Review boundaries

Preserve Chapter 1 and six-second Chapter 2, which ends at 50.077. No generated-HTML rebuild,
export, commit or publication. Chapter 3 awaits the morning review. Validate data rejection,
music alignment, seeking, reduced motion, asset readiness, lifecycle and desktop/phone fit.

Morning review: approve or revise the animatic pacing, readability and continuity before
further production polish.

## Working animatic built

Chapter 3 now runs from 50.077 to 58.077 seconds. The test-contract correction received
an independent PASS before implementation. Review the working film using the existing
shared URL, or choose “The waiver claim” and “Six starts” in the beat menu.

Validation recorded November 5, 2026:

- Chapter 3 suite: 32 passed, including receipt validation, timing, phone layout, reverse
  seeking, reduced motion, delayed assets and failure cleanup.
- Earlier-chapter focused lane: 78 passed and seven failed. The failures retain older
  whole-film duration or fixed beat-list expectations; those assertions remain unchanged.
- Stills at 1440x900, 390x844 and 360x800 are in `.claude/review/ch3-animatic/`.
- Two headless Chromium phone handoffs with opt-in sound each sampled 104 frames:
  p95 gap 16.8 ms, maximum 33.4 ms, no gap above 50 ms. This covers the handoff only,
  not full-film or real-device performance. Browsers were closed.

Independent still review found one material issue: the phone feature card occupied about
24% of the frame rather than rule 22’s 40%. Other inspected still criteria passed for an
animatic. The phone card is now 40% before the gentle push; the portrait retains its native
256px limit rather than stretching the source. The six slots remain in two rows of three.

Four new regression cases failed on the original 24% framing, then passed after the layout
correction. The combined Chapter 3 and feature-framing suites now pass 36 tests. Refreshed
stills are in `.claude/review/ch3-phone-framing/`; the payoff card measures 343px at 390x844
and 325px at 360x800. Main-thread inspection found no clipped or overlapping required copy.
Desktop styling and chapter timings are unchanged.

The six-call delegate budget is exhausted, so the correction has no independent recheck.
The earlier independent FAIL is not relabeled as a PASS. David’s pacing, readability and
continuity approval remains pending. Earlier handoff performance measurements predate this
phone correction. No generated HTML rebuild, export, commit or publication accompanied it.

## Earlier test-validation stop

The notes below record the earlier stop, not the current implementation state.

November 5, 2026: the storyboard and draft tests exist, but no Chapter 3 production code or
timing changes have been made. The film still ends at 50.077 seconds. Two intended red tests
failed at the correct boundaries: expected total 58.077, and expected new chapter state.

Independent test validation failed, then the single corrective recheck failed. Remaining
blockers: measure explicit required text with effective ancestor visibility rather than
filtering tagged elements; isolate delayed portrait and required-font readiness after other
initialization has settled. The rules stop implementation after that second failed verdict.
David must authorize further correction/validation before the build can proceed. The new
tests intentionally remain red and are not a claim that Chapter 3 works. Chapter 2 end-state
assertions were restored because the extension has not been implemented.

David approved an additional correction/validation round. That review accepted isolated
asset gating but found that geometry still trusted the production beat label. The helper now
takes the expected beat from the test, so stale or absent production metadata cannot omit the
payoff. This last correction has not received a passing independent verdict. No additional
delegate was started and no Chapter 3 production implementation has begun.
