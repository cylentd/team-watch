# Madden Curse film: start here

Chapter 1's desktop and mobile revisions are accepted. Preserve the finished broadcast
package; future chapters start with a storyboard, not another redesign of the opening.
Visual approval does not authorize Chapter 2, an export, a commit or publication.

## Fly-by lighting and first defense entrance experiment

November 6: each fly-by ignition leaves its card face and border softly lit, while
its tall shaft still fades quickly. All twelve team avatars brighten together as
the camera reaches their row, then settle with restrained blue rims through the
full-board hold. They reset when seeking back or leaving the board; no new image
assets or audio downloads are required.

The Gibbs wipe now reveals an empty desk. Saints drops from 58.727 to 59.077,
using the same 0.35-second fall as Raiders, instead of landing behind the incoming
wipe. The landing uses the established half-bar beat, not a claimed audio onset
(rule 18's scoped experiment). “Still won.” at 60.077, Raiders at 62.077 and
“Won both weeks.” at 64.077 remain unchanged. Total runtime stays 98.077 seconds.

## Mobile Gibbs composition

November 6 phone review: Gibbs’s avatar is 50% larger, with a larger manager name
and defense title. The defense-only phone camera moves closer and places the
card lower to use the empty bottom space. Desktop framing and the tight-end
sequence are unchanged.

## Shorter pickups and musical ending

Best pickups now takes eight seconds, from 50.077 to 58.077. The two supporting
cards land together at 52.077, Love lands at 54.077, and his six-week strip fills
from 55.227 to 56.077. The one-second earlier sweep removes the wait after Love
lands without shifting the later music cues. Each week shows its QB rank without a duplicate points
score. The three cards retain their PAR totals, which determine pickup order.

Chapter 4 starts at 58.077; Chapter 5 starts at 74.077. Its music jumps to the
original song's closing passage rather than repeating the middle through the
rankings. The closing chord and TEAM WATCH landing align at 92.077. The held
ident gives the sustained chord and reverb room to decay until 98.077. Total
runtime remains unchanged; the time saved on pickups moves to the ending.

Source receipt, November 6, 2026: the supplied Downloads/Ascent_to_the_Podium.mp3
is 175.987 seconds, whereas the earlier film source was a mid-song trim. The new
lossless source asset retains original seconds 150.057-174.057. Playback uses
the existing single MP3, with a 40 ms splice and a 350 ms safety fade confined
to the quiet end of the decay. The FLAC is a rebuild source, not a browser fetch.
The opening, Godwin, Achane and Romo cue times remain unchanged.

Review the shorter pickups and the final musical transition on the live film.
Audio-envelope and timing checks do not substitute for listening approval.

## Cut and TE clarity

November 6, 2026: Achane's split animation was still running, but the build began
pulling the camera away at injury second 1.510, just before the cut at 1.513.
The camera now keeps the close-up until the halves finish fading at 2.012.
Board-light build cues, the 40.077 reveal, chapter lengths and total runtime are
unchanged. Matching phone stills confirm the split is readable rather than tiny
on the full board.

The TE scene now has one headline, then **Again.** at the payoff. The duplicate
paragraph listing the week, starter and bench player is removed; START, BENCH,
names, weeks and scores remain on the physical props. This supersedes the added
role-caption treatment described in the earlier clarity record below.

All 14 new cut/caption regressions pass, alongside the preceding focused checks.
One existing mobile suspense test also fails with the pre-fix camera behavior:
it expects zero horizontal offset even after the accepted winner reveal. Its
offsets are identical before and after this correction; the test is left unchanged.
No full regression, export, publication or generated HTML rebuild was performed.

## Loading screen

The pre-play screen now uses the existing film wordmark, a small animated lime broadcast
signal and “Getting the film ready.” Playback and review controls are hidden until the
existing asset and scene warm-up gates finish. Loading failure exits the animation into
the existing error explanation; reduced motion keeps the signal static. The stylesheet
is 1,616 bytes, with no new images, video, animation library or artificial minimum wait.

Focused loading checks passed in eight cases at phone, Fold-shaped and desktop sizes,
including reduced motion and failed edition loading. This is not a full-film performance
benchmark or real-device approval. No generated HTML rebuild, export or publication.

## Current polish decision

David selected stage depth for the 14-second board shot and retained **Best pickups**
for Chapter 3. The board now has angled side wings, stepped metal supports, a raised
deck and an overhead recess. Its desktop overview sits slightly farther back and higher
so Round 10 clears the lower-third caption. Phone board framing and musical cue times
are unchanged. The stage fades with the board light and is hidden in other scenes.

Evidence recorded November 5, 2026: three new regressions failed before their respective
fixes; the final focused lane passed 55 tests across stage depth, fly-by polish, revision 8
camera behavior and phone framing. Stills at 360x800, 390x844 and 1440x900 are under
`.claude/review/stage-depth/`. Main-thread still inspection is complete; no independent
recheck or new visual approval is recorded. No full-film regression, export, generated
HTML rebuild or publication was performed for this correction. Earlier acceptance and
working-cut records below are historical; use the timing sheet for the current runtime.

## Choose the reference for the job

The latest phone listening correction is in [Phone listening corrections](madden-film-listening-sync.md).
It aligns COOKed to David's 33.3-second marker and completes the Romo camera move on
40.077. The new rank-led cinematic pickup treatment is approved at the top of
[Chapter 3](madden-film-chapter3.md); its rebuild is pending.

David selected both Chapter 4 stories: Gibbs's defense experiment and Lamarley's
Henry/Fannin tight-end switch. COOKed's bench defense is a researched backup.
Chapter 5 proposes a performance-based power ranking with actual records
and an open second-half finish. The Burrowed QB rotation and generic schedule ending
are superseded. The Pollard roast is also rejected: the box scores do not establish
a foolish process or the manager's intent. The detailed
[Chapter 4 storyboard](madden-film-chapter4.md) is approved and its 3D correction cut is
integrated at 62.077-78.077. Review the explicit experiment titles, readable defense
score holds and TE swap. [Chapter 5](madden-film-chapter5.md) is implemented at
78.077-98.077: actual standings shuffle into all-play power order, then the opening
trophy returns for the close. Both chapters await David's playback approval; no
independent corrective still review has run. Chapter 3's cinematic rebuild remains
pending. The timing sheet and mapped music extension remain the runtime authority.

| Need | Read | Authority |
|---|---|---|
| Constraints for a storyboard, build or review | [Film rules](madden-film-rules.md) | Active requirements; numbered IDs stay stable because source and tests cite them |
| Why a treatment worked or failed | [Craft reference](madden-film-craft.md) | Chapter 1 lessons, review evidence and a technique toolbox; general conventions are not requirements |
| Asset provenance, controls and earlier cuts | [Opening implementation history](madden-trophy-opening.md) | Historical reference; old runtimes and shot lists do not override the current timing sheet |
| Week 8 article, edition scope and original integration | [Midseason edition](madden-midseason.md) | Editorial/integration context; its original promo is distinct from the Chapter 1 film |
| Original product intent | [Project vision](../VISION.md) | League-specific reporting and broadcast direction |

## Find the current implementation

- Review the accepted film at
  `http://localhost:8000/github/team-watch-midseason/showcase/madden-curse/?film`.
  Use the existing shared server. The URL without `?film` is a separate promo mode.
- [Timing sheet](../showcase/madden-curse/timing.json) owns beat durations and events;
  [film model](../showcase/madden-curse/film.mjs) derives the sequence. Old prose is not a timing source.
- [Camera](../showcase/madden-curse/draft-camera.mjs) and
  [phone framing](../showcase/madden-curse/draft-mobile-framing.mjs) own composition.
  [Border beams](../showcase/madden-curse/draft-path-beams.mjs),
  [reveal wave](../showcase/madden-curse/draft-reveal-glow.mjs) and
  [suspense](../showcase/madden-curse/draft-build.mjs) carry the lighting sequence.
- [Film copy](../showcase/madden-curse/film-copy.mjs) and
  [receipt layout](../showcase/madden-curse/film.css) are separate from camera motion.
- [Audio edit](../showcase/madden-curse/music-edit.mjs),
  [onsets](../showcase/madden-curse/music-onsets.mjs) and the timing sheet must remain synchronized.
- [Scene preparation](../showcase/madden-curse/scene-warmup.mjs) prepares textures and render states
  before Play. Preserve controls, opt-in audio, reduced motion and resource cleanup.

## What is approved and what is only proposed

The accepted package includes the Lombardi/Blip opening, brand typography, sequential
card-border beams, a full-board reveal and reading hold, Godwin's purple fire, Achane's
clean cut/fade, neutral pre-hit suspense and Romo's pulsing column. On phones, the reveal
and buildup fit the whole board. Romo's headline precedes his returns on both layouts.

A later discussion identified competition between the bottom caption and the main action.
The proposed next-storyboard treatment groups the short headline, player and key stat into
one focal area, with a reading moment after the main move. This broader caption recomposition
has not been implemented; do not describe it as part of the accepted build or silently retime
Chapter 1. See [the attention lesson](madden-film-craft.md#reading-and-watching-compete).

## Review evidence

### Chapters 4 and 5 corrective pass

Recorded November 5, 2026. The combined Chapter 4, Chapter 5, power-timing,
film-set and live-finale integration lane passed **116 checks**: 75 pure checks
(4.9 seconds worker time) and 41 browser checks (196.8 seconds). A subsequent
material-only correction made stadium beams use their texture's alpha channel;
the five affected live trophy/headline checks passed afterward (25.9 seconds).
This is focused evidence, not a fresh full-film or full-repository regression.

The new live integration test failed first because the finale had no trophy
reference, then passed after scene-to-set wiring was completed. The existing
reduced-motion phone case caught an early transition blend and passes after the
set camera was changed to use elapsed time. Test-contract repairs preserve all
coordinates when flattening unsupported nested approximate comparisons, and
sample Blip during flight rather than during a scheduled landing. Defense tests
now pin the longer readable hold and completed ejection before the next shield.
No frozen golden or earlier-chapter acceptance test was changed in this pass.

Captured 33 review frames at 360x800, 390x844 and 1440x900 with no page errors;
the four final trophy/ident frames were refreshed after the material correction.
Evidence is in the local temporary folders:

- `C:/Users/David/AppData/Local/Temp/madden-corrections`
- `C:/Users/David/AppData/Local/Temp/madden-corrections-final`

Main-thread inspection covered representative defense, TE, power-order, trophy
and ident frames. Independent review did not run; no additional delegates were
started after the prior provider limit. The new test's static quality check and
the copy scanner passed. Browser contexts closed after each check and capture;
no server was started. No commit, publication, video export or generated HTML
rebuild was performed. Real-phone playback, audio continuity and visual approval
remain David's review steps.

### Latest clarity corrections

David's Fold screenshot exposed a clipped Jordan Love card in Chapter 3. Pickup
layout now considers frame aspect ratio as well as width, and the desktop frame
unit is bounded by width. The method line is **Ranked by points over replacement
(PAR).** This names the existing lineup-replacement calculation; no scoring or
ranking formula changed.

Chapter 4's approved two-win story replaces the defense ejection metaphor; see
[madden-film-chapter4.md](madden-film-chapter4.md). The existing props remain, with
literal started-defense headlines and WIN stamps. Lamarley's start/bench roles
are explicit. Lime stamps in Chapters 4 and 5 use dark ink.

Chapter 5 compares actual leaderboard placement with power placement, not W-L
record with power placement. Each card's small actual line is its league place;
Sausage's feature compares **#6 actual** with **#3 power**. All-play calculations,
standings order and the finale remain unchanged. Real Fold approval is pending.

### Chapter 1 acceptance

Recorded for this acceptance on 2026-11-04:

- The film model returns a 7.584-second opening and 44.077-second total.
- David approved desktop, reopened mobile, then accepted the mobile corrections with
  "everyhing looks good now."
- The latest focused run passed 40 tests: mobile framing, border/sky/path lighting,
  headline entrances, identity, opening and the existing desktop/phone straight-dolly motion cap.
- Playback and stills were captured at 360x800, 390x844 and 1440x900. Browser contexts closed
  after review. Headless checks are not a real-device performance guarantee.
- This was not a full regression, a new independent still-review verdict or an MP4 review.
  Existing defense-headshot 404 fallbacks and earlier broad-test conflicts remain documented
  in the craft reference. No export or deployment accompanied acceptance.

Reproduce the focused lane from the feature worktree:

```sh
python -m pytest tests/test_madden_mobile_framing.py tests/test_madden_border_lights.py tests/test_madden_sky_lights.py tests/test_madden_headline_entrance.py tests/test_madden_colored_path.py tests/test_madden_ident.py tests/test_trophy_opening.py tests/test_madden_rev8.py::test_the_fly_by_is_one_straight_dolly_nothing_crossing_faster_than_a_quarter_frame_a_second -q
```

The command is a focused lane, not a substitute for the repo's land gates. Rerun only when
its inputs change; do not relabel the historical pass as a fresh run.

## Chapter 3 working cut

The working film now ends at 58.077 seconds. Chapter 1 retains its accepted timing;
Chapter 2 occupies 44.077–50.077. [Chapter 3’s storyboard and evidence](madden-film-chapter3.md)
cover Sausage’s September 23 waiver claim of Jordan Love and six actual QB starts.
Use “The waiver claim” or “Six starts” in the beat menu to review the new sequence.

The November 5 Chapter 3 and phone-feature suites passed 36 tests. The earlier-chapter
focused run passed 78 and failed seven older whole-film duration/beat-list expectations,
left unchanged. Independent still review found the phone feature too small; the card
was enlarged from 24% to 40% of frame height with four red-to-green regression cases.
The correction has main-thread still inspection but no independent recheck. David’s
visual approval remains pending; this does not extend Chapter 1’s acceptance. No export,
publication or generated HTML rebuild accompanied it.

## November 6 defense-card polish

The current Chapter 4 defense treatment is recorded in [the defense-card revision](madden-film-chapter4.md#november-6-defense-card-revision). It replaces the shield/ledge pair with one started-lineup card at a time, local NFL logos, explicit PTS labels, one Gibbs identity, and staged win outcomes. Chapter 4 remains 58.077–74.077; total runtime remains 98.077. Chapter 5's thin outlines and transparent decal layering are simplified to reduce shimmer. Phone/Fold-shaped/desktop verification is not real-Fold playback approval.

## Trophy fly-in review cut

The ending approaches the trophy and perched Blip from 90.077 to 91.577 seconds,
then continues forward into black. A large, centered TEAM WATCH identity replaces
the small corner tag and lands on the final chord at 92.077. It holds on black
until the film ends at 98.077. Earlier chapters and their music cues are unchanged.
See [the full-screen ending record](madden-film-chapter5.md#full-screen-closing-identity)
for checks and device-review limits. Review the live ending from 90 seconds;
no export or deployment accompanies this cut.
