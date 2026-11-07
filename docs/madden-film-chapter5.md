# Chapter 5: Midseason power rankings

## Current music edit

November 6, 2026: the shorter pickups shift this chapter to 74.077. The rankings
run to 84.077; the finale holds to 98.077. The original song's closing passage
now begins with the rankings, replacing the repeated middle and the old mid-song
tail. TEAM WATCH enters at 91.577 and settles on the closing chord at 92.077.
The remaining six seconds retain the chord's sustain and decay, with a short
safety fade at the quiet end. These times supersede the previous music table.

## Current review cut

Review 78.077-98.077. The riser, standings-to-power shuffle and trophy ending are
implemented for David's playback review; the film's earlier chapters and total
duration are unchanged by this corrective pass.

- All twelve plates land in actual standings order at 80.077 under **Standings.**
  They hold, then move through separate depth lanes from 81.077 to 82.077.
- **Power rankings.** and **All-play, Weeks 1-8** accompany the new order. Plates
  replace their large actual records with all-play records and show actual league
  placement underneath, not W-L. Sausage compares **#6 actual** with **#3 power**.
  Lime power stamps use dark ink. The numbers come from the checked Week 8 receipts,
  not a new ranking formula.
- The Sausage feature and top-four lift remain. The wide has lit stage wings, a
  broadcast-blue back wall, floor haze and feathered stadium beams rather than an
  empty black background. Card names are enlarged for the closing phone view.
- The opening's actual Lombardi lowers onto the summit at 90.077-92.077. Blip hops
  beside it, **Still anyone's game.** supplies the second-half invitation, and the
  TEAM WATCH ident returns for the final musical hit. Reverse seeking restores the
  trophy to its opening position; page cleanup releases its reference.

Next: confirm the standings-to-power comparison, phone readability and trophy
bookend in live playback. The earlier cube and folder storyboard below is history;
neither prop remains in the current cut.

## Cinematic revision (implemented 2026-11-05)

Chapter 5 becomes a lit two-tier riser in the 3D room. Twelve manager plates slam onto it, and the camera
travels through its depth to the top six, then eases into Sausage. The film ends at **98.077** with
**`repeats` 4**. David gave Chapter 4's 3D rebuild "the same direction" for this chapter on November 5, 2026.
The approved rebuild and corrective pass are implemented. The ranking definition, the
receipts and the no-claims boundaries further down stay true. Every plate reads from `power-receipts.json`.

### Placement and music

| Item | Value |
|---|---|
| Film window | 78.077-98.077, 20 s (was 86.077-106.077) |
| Beats | `power-board` 78.077-88.077 and `power-close` 88.077-98.077, 10 s each |
| Phrase copies | film 62.077, 70.077, 78.077, 86.077 (Chapter 4 takes the first two) |
| Song's tail | starts at 62.077 + 8 × 4 = 94.077; its last hit lands 3.513 s in, at 97.59 (asset 103.59) |
| Played asset | 104 s (was 112). The film ends 0.077 s past it, as 106.077 ends past 106 today |
| Ident | TEAM WATCH fades in 96.077-96.577, then holds to 98.077 |
| Why 4 | `repeats` 3 puts the tail at 86.077, ending the film near 90, before the 94.077 floor. `repeats` 5 ends it at 106.077, past the 98.077 ceiling |

Hits sit on bar lines 78.077-96.077. The one exception is the song's last hit at 97.59, which lands the ident.
There are no other onsets in the phrase copies (rule 18).

### Set and props

Reused from Chapter 1: the turf floor and fog; the stage block helper, wings and materials (`draft-stage.mjs`)
for the riser's shell; the rail strips' light for each tier's front edge; the blue backlight wave
(`draft-reveal-glow.mjs`) for the 94.077 release; manager badges (`avatars/yahoo/<id>.webp`); `placard`,
`teamName` and `stampMesh` textures; the flip of the curse's 0.0 for the rank cube; Blip's hop and face;
dust, chips and sparks (`film-impact.mjs`, phone counts); the ident (`film-ident.mjs`).

New pieces, four:

| Piece | Source and shape | Travel | Trigger | Fade |
|---|---|---|---|---|
| Riser | Two stepped tiers: front low for places 7-12, back high for 1-6. Desktop sets a row of six per tier; a phone sets each tier as a 2x3 block of three steps. Each slot's front carries its place numeral, 1-12, and sits on a short piston | Pistons move plates up and down only | Tier strips light on 78.077; pistons lift the top four on 88.077 | Strips settle to 50% over 0.5 s |
| Manager plates | Twelve portrait-shaped slabs (3:4), each with badge, manager name and actual W-L. Same face layout as the Chapter 1 cards | Drop straight down from above frame into their slots in 0.35 s (`outExpo`), 6% squash. A tier lands all six together | Front tier 80.077, back tier 82.077 | No fade; places 5-12 dim to 40% on 88.077 and sink 0.1 units |
| Rank cube | A two-faced block on Sausage's plate: "#6 standings", then "#3 power" | Rises from the plate top in 0.3 s; flips 180° about X in 0.28 s (`outBack`), like the curse's 0.0 | Rises 84.077, flips 86.077 | Stays; sinks into the plate on 88.077 |
| First-half file | A folder of two thin hinged boards on the riser apron, tab reading "First half", lying open | Blip lands on the cover, which swings shut in 6 frames (`inCubic`) | Shuts 92.077 | Dust puff and chips clear in 1 s |

### Beat table: `power-board`

| Film time | Shot and its one move | What happens in the set | Hit | Visible copy |
|---|---|---|---|---|
| 77.677-78.477 | Crane up and back from Chapter 4's bench rack over the desk onto the riser (`inOutCubic`, 0.8 s), ending on an establishing wide | The empty riser's tier strips light; slot numerals glow | 78.077 cut to power-board | Power rankings. / All-play, Weeks 1-8 |
| 78.477-80.077 | Held wide, 3% drift push | Plates 7-12 fall from above frame and land together on the bar; a line of dust runs along the tier edge. Stats pop on each plate 3-5 frames apart: badge, name, record last | 80.077 places 7-12 land | Six plates: badge, name, W-L |
| 81.4-82.077 | Depth move: a crane up and over the front tier toward the back tier (`inOutCubic`), arriving on the bar | Plates 1-6 land together on the back tier; the front tier passes under the lens and drops out of frame bottom | 82.077 top six land | Six plates |
| 83.5-84.077 | Push-in onto Sausage's plate in slot 3 (`inOutCubic`), ending in a feature close | His plate slides 0.3 units forward out of the slot; the rank cube rises reading "#6 standings"; his record stamp grows to the feature size. The other plates soften to 40% | 84.077 Sausage plate lifts | #6 standings / 4-4 actual |
| 84.077-86.077 | Held feature, 3% drift | The cube flips to "#3 power" and the plate seats back into slot 3 on the same bar; the 4-4 never changes | 86.077 Sausage #3 power | #3 power / 4-4 actual / Better than the record. |
| 86.077-87.677 | Held, 3% drift | Nothing new; the headline holds | none | Same |

### Beat table: `power-close`

| Film time | Shot and its one move | What happens in the set | Hit | Visible copy |
|---|---|---|---|---|
| 87.677-88.077 | Pull back to the top four (`outCubic`), a `travel`, arriving on the bar | Pistons lift places 1-4 by 0.25 plate heights; Jaxon's goes one notch (0.08) higher than the three tied plates; places 5-12 dim and sink. The notch is the gap | 88.077 top four settle | One all-play win apart. |
| 89.4-90.077 | Pull back to the whole riser and its apron (`outCubic`), ending on the new information: Blip and the open file | Blip hops in from frame left in three hops, the last landing beside the file on the bar; every plate comes back to full light | 90.077 Blip lands | none (the file's tab: First half) |
| 90.077-92.077 | Held wide, 3% drift push | Blip crouches and jumps onto the cover; it slams shut on the bar with a dust puff and chips | 92.077 file shuts | Still anyone's game. |
| 92.077-96.077 | Same held wide, push continuing | On 94.077, as the song's tail begins, one blue backlight wave sweeps the riser left to right in 1.5 s. The headline leaves at 95.9 | 94.077 tail begins | Same, until 95.9 |
| 96.077-98.077 | Same held wide | The scene dims to 40% over 0.5 s under the returning ident. On the song's last hit the tag settles from 104% scale (`outBack`) and one glint crosses it | 96.077 ident returns; 97.59 ident lands | TEAM WATCH |

Copy changes for David to approve:

- **Dropped:** "Top four.". The lifted four are the picture (rule 26).
- **Changed:** "Sausage" is no longer a headline, because his plate names him (rule 40).
- **New:** the cube's "#6 standings". It is the only new string, and it states the actual standings place from the receipts.

"Still anyone's game." stays an editorial invitation to the second half. The plates are never lit equally,
because that would read as equal odds (the boundary under "Shot and reading budget" below).

### Desktop and phone composition

| Shot | Desktop (1440x900) | Phone (390x844) |
|---|---|---|
| Wide (78-80) | The whole riser and both tiers fit, headline at upper left above the back tier | The front 2x3 block fits whole, with the back block's top step visible; the headline sits above it |
| Top six (82) | Back row of six whole, front row cut by frame bottom | Back 2x3 block whole |
| Sausage (84-87) | His plate at 45% of frame height, centre-right; headline beside it at left | His plate at 40-45% of frame height (about 340 px), headline directly above. Controls stay at the bottom |
| Top four (88) | Four plates whole in one row, evenly spaced | The 2x2 group whole |
| Close (90-98) | All twelve whole, Blip and the file on the apron in the lower third | All twelve as two 2x3 blocks stacked, plates about 100 px tall; Blip and the file below them, clear of the controls |

Badges, names and records stay upright and sharp. Record and rank text is at least 2% of frame height
(rule 25). The wave runs behind the plates and never crosses a headline (rule 36). The dust and chips stay below the type.

**Reduced motion.** Each hit's end state appears on its bar line. Plates sit in their slots, the cube shows
"#6 standings" until 86.077 and "#3 power" after, and the pistons stand at their settled heights. There are no
falls, flips, hops, dust or wave. The camera cuts to each shot's settled framing with a 0.3 s cross-fade.
The headlines and the ident keep their windows.

**Seek and reverse.** Every pose is a pure function of film time. Plates before their bar are hidden
(rule 19). The cube's face follows the clock, so seeking back across 86.077 shows "#6 standings" again. Pistons,
Blip's place and the file's lid are recomputed each frame, so seeking back across 92.077 reopens the file.
The ident's opacity stays `identAt(time)`.

**Warm-up.** Before Play enables, the room decodes all twelve badges and builds the plate, numeral, cube
and file textures. It then warms each beat's middle and 0.1 s after each hit in `scene.mjs` `warmPlayback`,
the wave's additive shader and the impact points included (rule 49). Pagehide disposes the riser with the room.

### Why this is cinematic

| David's word | What changes |
|---|---|
| Infographic | The ranking is a physical riser of plates, so order is height and depth, not a list. Two of the three numbers on screen are objects: the cube flip and Jaxon's one-notch piston |
| Not exciting | Each of ten bars lands a slam, a lift, a flip or a shut file. The close builds to Blip shutting the first half on the beat |
| Not cinematic | Crane in from Chapter 4's rack, a held wide, a depth move over the front tier, a push to the feature, then two pull-backs ending on new information. One move per shot |
| No cool animation | Tiers of plates drop together, the rank cube flips, pistons lift the leaders, Blip hops and slams the file, and a blue wave rides the song's tail |
| Too slow | The song's tail fixes the length at 20 s, so the speed comes from density. The DOM version had 7 hits in 20 s; this one has 11. Every 2 s bar brings a new object, and one heading is cut |

### Retime list (tests are not edited here)

| Where | Old | New |
|---|---|---|
| `music-edit.mjs` `extension.repeats` | 5 | 4; rebuild the asset with `python scripts/build_lineup_music.py` |
| `timing.json` `about` | "ends the film at 106.077" | "ends the film at 98.077" |
| `timing.json` `power-board` | duration 12; plates 0-2, topsix 4-6, feature 8-10 | duration 10; lower at 2, upper at 4, feature at 6 ("Sausage plate lifts"), flip at 8 ("Sausage #3 power") |
| `timing.json` `power-close` | duration 8; four 0-2, marker 2-2.4, close 3.6-4, file 4.5-6, ident 6-6.5 | duration 10; four at 0, hops 0.6-2 (blip at 2), close at 4, wave at 6, ident 8-8.5, last at 9.513 ("Ident lands", 97.59) |
| `film.mjs` `TRAVEL` | power-board absent | add `power-board` (the crane in) |
| `test_power_beats_extend_the_film...` | durations 12, 8; starts 86.077, 98.077; plan 106.077; first 12 starts end 62.077, 74.077 | durations 10, 10; starts 78.077, 88.077; plan 98.077; first 12 starts end 62.077, 70.077 |
| `test_power_close_travels_on_the_same_set...` | power-board `across` | power-board `travel` |
| `test_power_impacts_land_on_bar_lines` | filter from 86; cut 86.077, plates 88.077, top six 92.077, Sausage 96.077, cut 98.077, four 100.077, close 102.077 | filter from 78; cut 78.077, places 7-12 80.077, top six 82.077, Sausage lifts 84.077, Sausage #3 86.077, cut 88.077, four 88.077, Blip 90.077, close 92.077, tail 94.077, ident 96.077, ident lands 97.59 (an onset, not a downbeat) |
| `test_music_tail_plays_the_songs_own_ending...` | repeats 5; 111.59 in, 95.59 and 109.59 out; cues 66.077-84.077 | repeats 4; 103.59 in, 111.59 and 95.59 out; cues 64.077-76.077 |
| `test_ident_returns_across_the_close_ident_event...` | before 86.1, 98.1, 103.9; rising 104.2, 104.4; held 105 | before 78.1, 88.1, 95.9; rising 96.2, 96.4; held 97 |
| `test_played_asset_really_covers...` (lineup music) | asset 112; 112 − 6 > 106.077 − .1 | asset 104; 104 − 6 > 98.077 − .1 |
| `test_madden_ident.py`, `test_madden_chapter2.py` `test_the_tag_shows_in_the_opening_only` | samples by beat; end reads 1 | no number changes; re-run, since the ident still starts 2 s before the end |

Build notes the renderer does not cover yet:

- `scene.mjs` `drawRoom` skips the 3D room for the `lineups` chapter, and `draft-camera.mjs` holds the finale's frame for any later chapter. Both need Chapter 4 and 5 shots.
- `draft-camera.mjs` `arrival` times a travel to the next onset. No onset falls between 62.077 and 97.59, so travels there need a bar-line fallback.
- A shield or card that lands on a beat's first frame falls during the incoming whip. The sheet needs a lead (a negative `from`), or the pose reads the outgoing clock.
- The 97.59 ident landing is new. `film-ident.mjs` only fades today.

## Original treatment

Close on a performance-based power ranking, with actual records beside it. Show where
the first eight weeks' scoring supports a team more than its record does, then reopen
the second half. The prior generic schedule-mechanism ending is superseded.

David requested power rankings and an open-race finish on November 5, 2026. This
storyboard and ranking presentation are proposals for approval before implementation.
They are not a new canonical model or rest-of-season forecast.

## Rank the performance, keep the record visible

No existing named power-ranking formula was found in the inspected midseason and
league modules or production data. There is an existing all-play basis in
`design/league_back.py::add_standings`, already used for the league's luck figures.
Reuse that comparison: each weekly score faces all eleven other teams' scores from
the same week; score ties count half. Across eight weeks that is 88 comparisons.

Proposed power order: descending all-play performance, total actual points breaking
ties. The total-points tie-break is an explicit presentation proposal, not a hidden
new weighted formula. Three teams tie at 55-33; their scoring totals put Lamarley,
Sausage and WARREN-TY in that order. Do not exaggerate the gap between them.

The entry label is **Power rankings.** Keep **All-play / Weeks 1-8** nearby and an
actual W-L label on each record. The full order is an ensemble view; focus time goes
to the meaningful mismatch and the tight leading group, not twelve equal profiles.

## The story the ranking actually supports

Sausage is the clearest record/performance mismatch: 4-4 in the standings, 55-33 in
all-play, third in this proposed power order after the points tie-break. The existing
luck method gives him -1.0 wins relative to a 5.0-win all-play benchmark. That is a
season-wide schedule comparison, not a claim that a particular loss was stolen.

Jaxon leads the all-play comparison at 56-32. Lamarley, Sausage and WARREN-TY are each
55-33. Only one of 88 comparisons separates the leader from those three; Jaxon's
6-2 actual record is stronger than that narrow scoring-performance gap alone.
This supports a close-leading-group finish without staging an on-field rivalry.

COOKed is 5-3 but eighth in this proposed order, with 41-47 all-play and +1.3 wins
of schedule luck by the existing method. The record is real; do not remove wins or
call the roster a fraud. Honey is 2-6 with -0.7 wins of schedule luck, but still
11th in this order. Bad records can include bad luck without every struggling
roster secretly being elite. Do not promote a low-scoring team merely to manufacture
a redemption story.

## Shot and reading budget

**Superseded, DOM animatic.** The cinematic revision at the top replaces this table, its
86.077-106.077 placement and its music note (2026-11-05). The closing-line boundary below still holds.

These twenty seconds are chapter-local editorial allowances, not locked cues. The
current film ends at 62.077 seconds and its audio asset is 72 seconds with a six-second
playback offset. Chapters 4-5 need a deliberate music extension and fresh phrase map;
there are no verified new hits at these provisional times. Preserve Chapters 1-3.

| Chapter time | Camera and subject action | Exact proposed visible copy |
|---|---|---|
| 0-4 s | Carry the Chapter 4 bench/start boundary into a deep broadcast ranking set. Manager plates rotate into their proposed all-play positions, then settle. Desktop reveals the full board; phone first establishes places 7-12 as a readable six-row group. | Power rankings. / All-play / Weeks 1-8 / ranks, manager names, actual W-L records |
| 4-8 s | Move through the board's depth to the top six, not a whip past twelve tiny cards. Desktop keeps the complete order; phone replaces the lower half with places 1-6 and holds. All ranking movement is complete before the reading hold. | Same heading and method; ranks 1-6 with actual records |
| 8-12 s | Ease into Sausage's plate. His actual 4-4 record remains fixed while his plate's sixth-place standings position resolves into third in the proposed power order. Pause on the difference; no fantasy points are added or results rewritten. | Sausage / #3 power / 4-4 actual / Better than the record. |
| 12-16 s | Pull back to the leading four in one focal group. The set shows one scoring-comparison marker between Jaxon and the three tied all-play totals. Keep any exact count clearly labeled all-play, never real wins. | Top four. One all-play win apart. |
| 16-20 s | Broaden to the league's badges with the midseason identity. The ranking stays background context; Blip closes the first-half file and turns toward the next empty lineup sheet. Hold the closing headline at least two seconds. | Still anyone's game. |

The last line is an editorial invitation to the second half. It does not assert equal
championship odds, certify that nobody is mathematically eliminated, guarantee a
playoff berth or predict the rest of the schedule. Playoff-team count and regular-season
length are null in the inspected snapshot; resolve those before making specific
qualification claims. Do not invent percentages to strengthen the ending.

## Desktop and phone composition

**Superseded, DOM animatic** (2026-11-05): see the cinematic revision's composition table.

Desktop uses twelve manager plates in two readable columns of six with physical
depth, manager badges and anchored rank/actual-record labels. The camera move reveals
how the order differs from standings; it is not a static leaderboard screenshot.
For Sausage, the selected plate occupies the feature frame and the rest recede.

Phone shows two six-row groups sequentially, lower half first and top half second,
with a stable heading/method location. Only the selected feature needs the 40%-height
composition; the full order is an ensemble. No tiny twelve-row list squeezed into
one phone frame. The leading four settle in an evenly spaced 2x2 group. Foreground
copy and badges remain sharp, upright and clear of lighting effects.

The all-play order and actual record are separate fields. Never animate an actual
4-4 record into 5-3 as if the season changed. Reduced motion presents each settled
ranking group and feature directly, with no reordering flight.

## Proposed order and verification receipts

| Power place | Team | Actual record | All-play comparisons | Points scored | Existing luck, wins |
|---|---|---|---|---:|---:|
| 1 | Jaxon | 6-2 | 56-32 | 954.28 | +0.9 |
| 2 | Lamarley | 5-3 | 55-33 | 946.70 | 0.0 |
| 3 | Sausage | 4-4 | 55-33 | 935.86 | -1.0 |
| 4 | WARREN-TY | 5-3 | 55-33 | 905.02 | 0.0 |
| 5 | Chat | 4-4 | 47-41 | 850.04 | -0.3 |
| 6 | Gibbs | 4-4 | 46-42 | 872.00 | -0.2 |
| 7 | Romo | 5-3 | 45-43 | 864.32 | +0.9 |
| 8 | COOKed | 5-3 | 41-47 | 836.42 | +1.3 |
| 9 | Burrowed | 3-5 | 38-50 | 807.70 | -0.5 |
| 10 | Aura | 3-5 | 36-52 | 786.38 | -0.3 |
| 11 | Honey | 2-6 | 30-58 | 784.98 | -0.7 |
| 12 | Bo-Bo | 2-6 | 24-64 | 726.14 | -0.2 |

The points and luck columns are evidence, not extra on-screen numbers. Existing luck
is actual wins minus accumulated weekly all-play win shares, rounded to one decimal
by the existing method. This descriptive comparison is not a predictive model.

## Reuse and build boundary

Reuse manager badges, broadcast typography, silver transitions, Blip's character
movement and deterministic film/readiness/lifecycle contracts. Build the ranking
set, grouped phone framing and a checked through-Week-8 power-ranking contract.
Production should reuse the existing all-play calculation, with explicit order and
tie-break metadata; never recompute a competing metric in a view.

Tests must cover all 48 actual games, 96 team-week scores, twelve teams each week,
88 comparisons per team, the tied 55-33 group and points tie-break, actual-record
immutability and the existing luck values. Add tie, missing-week and duplicate-team
cases before implementation. Also test reverse seeking, both phone groups, the
feature/ensemble framing distinction, reduced motion, readiness and cleanup.

## Sources and open work

Verified locally November 5, 2026, through Week 8 only. Data root:
`C:/Users/David/.ff-jarvis-history/data`.

- `yahoo_league.json`, `games[week<=8]`: all 48 games, 96 actual team-week
  scores and actual records. Week 9 data is excluded.
- `yahoo_league_box.json`: all 96 starter sums match the game totals within 0.01;
  bench points never enter team totals.
- `design/league_back.py::add_standings` was executed read-only on Weeks 1-8 to
  reproduce the existing luck figures. An independent local tally of same-week
  score comparisons supplies the proposed order and is checked against those figures.
- No weekly total-score ties exist in this cutoff. Tie behavior still belongs in the
  eventual contract/tests; do not silently omit it from the implementation.

Open work: approve the proposed ranking definition and storyboard, map the extended
music, set absolute cue times, implement checked data/test contracts, then review
live desktop and phone animatics. No production scene, music or timing changed for
this proposal. No independent storyboard review ran; the prior delegation budget is
exhausted. Chapter integration remains sequential after Chapter 3 review.

## Approved trophy fly-in

The closing wide now becomes a physical camera approach toward the trophy and
perched Blip. It starts after Blip lands at 90.077 seconds, eases to its final
frame at 91.577, and holds there through 98.077. The lens stays unchanged. TEAM
WATCH enters after the approach and lands with the existing chord at 92.077.
The ranking overview remains wide until the approach begins; the closing feature
frames the trophy and Blip rather than all twelve teams.

Reduced motion selects settled shots from the actual film clock, without the
approach. Seeking backward restores the earlier shot. Existing assets are reused;
there is no new image, model, audio asset or render pass.

Verification, November 6, 2026: six new camera cases failed before implementation
and pass with the move; the application reduced-motion seek case also passes.
The affected Chapter 5 lane passes 30 tests, including its existing browser checks.
Timing, audio-splice and trophy integration checks passed in the preceding scoped
run. Stills were inspected at 360x800, 390x844, 690x829 and 1440x900. These are
headless framing checks, not physical-Fold or slow-connection playback approval.
No export, publication, generated HTML rebuild or independent review ran.

David should review the live ending from 90 seconds and approve or revise the
approach speed, trophy framing and settled tag before export.

## Full-screen closing identity

This replaces the preceding held trophy shot and small closing tag. The trophy
approach remains 90.077–91.577. The camera then continues forward until 92.077;
black covers the frame by 91.927. The centered Team Watch identity enters over
the next 0.15 seconds and lands on the existing final chord at 92.077. It holds
on black through 98.077. The opening identity and earlier chapters are unchanged.

The existing SVG Blip mark sits above the wordmark. The complete identity fills
at least 65% of frame width and 25% of frame height at the review sizes. No new
image, font, audio file or WebGL render pass is added. Reduced motion uses settled
camera shots and direct black/logo changes; reverse seeking restores the film.

Verification, November 6, 2026: seven initial acceptance cases failed before the
change. The expanded end-card suite passes 13 cases, including phone, Fold-shaped,
desktop and reduced-motion browser checks. The scoped timing, camera continuity,
existing ident and audio-splice checks pass. New-test static checks are clean.
Headless captures support framing review, not physical-device playback approval.
No export, publication or generated HTML rebuild ran.

Review the live ending from 90 seconds, especially the speed into black and the
logo landing. Independent review was not run.

The closing mark now gives one wink from 92.577 to 92.877 seconds, half a second
after the logo lands. Only one eye closes; the wordmark, brow and smirk stay still.
The usual smug face returns for the remaining hold. Reduced motion omits the wink.
Four focused timing/rendered-eye cases pass, including exact reverse seeking;
phone and desktop frame strips were inspected. No additional media is loaded.
