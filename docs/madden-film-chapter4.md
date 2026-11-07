# Chapter 4: Start/sit regrets

## Current review cut

David approved the two-win defense storyboard after finding the slot/ejection gag
unclear. The current cut reuses the desk, defense props, Gibbs's badge and Blip,
but does not depend on viewers recognizing a shield as a defense symbol.
There is no new shield redesign. This supersedes the older mechanism below.

| Film time | Action | Exact headline |
|---|---|---|
| 62.077-64.077 | Saints defense receipt lands: W4, −3. Gibbs's badge identifies the manager. | Gibbs started Saints DEF. |
| 64.077-66.077 | Receipt stays put; WIN stamps onto it. The margin comes from 82.78 minus 80.28. | Still won by 2.50. |
| 66.077-68.077 | Raiders replaces it as the feature: W5, −1. No negative-score ejection or red slot flash. | Then started Raiders DEF. |
| 68.077-70.077 | Camera gathers both retained receipts; both show WIN. | Two negative starts. Two wins. |

Chiefs' zero-point Week 8 is removed from the visual story, not from the full
receipt archive. Gibbs lost that week; including it weakened the two-win joke.

Lamarley remains at 70.077-78.077. The portrait exchange and scores are unchanged.
November 6 phone review found the added role paragraph too busy over the moving
portraits. That duplicate paragraph is removed. The scene keeps its single title
and the final **Again.**; START, BENCH, week, player name and score stay on the props.
W5 starts Fannin and benches Henry; W8 reverses them. Lime score and WIN stamps
use dark ink rather than white. The exchange and payoff timing are unchanged.

The defense portion remains eight seconds. No earlier chapter timing, music cue,
export, publication or generated HTML changes accompany this revision. Review
whether start, negative score and win read without an explanation.

## Cinematic revision (implemented 2026-11-05)

Chapter 4 becomes one physical lineup desk in the 3D room: 16 s, eight bar lines, a hit on every one.
David reviewed the DOM animatic on November 5, 2026: "Chapter 4 kinda sucks. It's just an infographic.
Not exciting. Not cinematic. No cool animation. Also too slow." He chose a 3D rebuild at 16 s.
The approved rebuild and corrective pass are implemented. The facts, receipts and
no-claims boundaries further down stay true, and every number on screen comes from `lineups-receipts.json`.

| Item | Value |
|---|---|
| Film window | 62.077-78.077 (was 62.077-86.077) |
| Beats | `lineup-defense` 62.077-70.077 (Gibbs), `lineup-tightends` 70.077-78.077 (Lamarley), 8 s each |
| Music | phrase copies 1 and 2 of 4 (asset 50.077-58.077); `repeats` 4, fixed in the Chapter 5 doc |
| Hits | bar lines only: 62.077, 64.077, 66.077, 68.077, 70.077, 72.077, 74.077, 76.077 (rule 18) |
| In | whip right out of Chapter 3 across 61.677-62.477 (rule 20) |
| Between beats | whip right along the same desk across 69.677-70.477, a `travel`, no silver wipe |
| Out | crane up and back over the bench rack to the Chapter 5 riser across 77.677-78.477 |

### Set and props

Reused from Chapter 1: the turf floor and fog (`draft.mjs` ground, `fieldMarkings`); the stage block helper
and its materials (`draft-stage.mjs`) for the desk shell; the card mesh with its portrait texture
(`draft-board.mjs`) for Fannin and Henry, from `heads/xl/harold-fannin.webp` and `heads/xl/hunter-henry.webp`;
the border-light shaft (`draft-path-beams.mjs`, DEF purple and TE teal from `PALETTE`); `stampMesh` for every
week and score; `placard` and `teamName` textures; manager badges from `avatars/yahoo/<id>.webp`; Blip's hop
and face (`blip-hop.mjs`, `blip.mjs`); sparks and dust (`film-impact.mjs`, phone counts); the whip
(`draft-camera.mjs` blend, `expoInOut`).

New pieces, five:

| Piece | Source and shape | Travel | Trigger | Fade |
|---|---|---|---|---|
| Lineup desk | One long slab, two stations: Gibbs's left, Lamarley's right. Each has a nameplate (badge disc and name) on the front face and a ledge on its left end. A broadcast-blue recess strip runs along the lip | Fixed | Strip lights on 62.077 | Settles to 40% over 0.5 s |
| Socket | A recessed slot one card wide, with a rim band like the fly-by border. Gibbs's carries a DEF placard, Lamarley's a START placard | Fixed | Rim flares on each landing; its shaft rises 0.6 card heights | Shaft gone 0.5 s after the hit, rim back to 50% |
| Defense shields | An extruded shield slab, one per start: SAINTS, RAIDERS, CHIEFS in big words (text only; no logo art) and a `stampMesh` week and score at its foot | Drops straight down from above frame into the socket in 0.35 s (`outExpo`), 8% squash on landing. The next shield knocks it out: it pops up 0.4 units and arcs left onto the ledge in 0.5 s (`outCubic`), landing upright | Lands on its bar | Rests on the ledge until the whip out |
| Point tokens and chute | Six lime discs (`PALETTE.brandLime`) on a rail right of the socket; a hinged flap on the socket's front | A deduction slides tokens left into the chute, one every 4 frames, and drops them through the desk | 6 frames after a negative landing; Chiefs opens the flap with nothing behind it | Gone 0.6 s after the hit; the flap stays open |
| Bench rack | A lit shelf behind and above Lamarley's socket with one card slot and a BENCH placard | Fixed; cards drop or lift into its slot | Rack light 40% until its card scores, full on that hit | Back to 40% on the next swap |

The six tokens on the rail are a picture of "points", not a count; only the tokens that leave carry a number.

### Beat table: Gibbs, `lineup-defense`

| Film time | Shot and its one move | What happens in the set | Hit | Visible copy |
|---|---|---|---|---|
| 61.677-62.477 | Whip right (`expoInOut`, 0.8 s) into a low medium on Gibbs's station, camera just above the desk top | The SAINTS shield falls through the whip's back half and slams the socket on the bar. Rim flares DEF purple, the shaft rises, sparks at the socket foot. Three tokens slide into the chute | 62.077 Saints slam (also the cut) | Start/sit regrets. Set: GIBBS, DEF, SAINTS, W4, −3 |
| 62.477-67.6 | Slow push-in toward the socket, 10% of the distance (`inOutCubic`), one move through three landings | RAIDERS drops and knocks SAINTS onto the ledge. One token slides into the chute | 64.077 Raiders slam | RAIDERS, W5, −1 |
| (same shot) | (same push) | CHIEFS drops and knocks RAIDERS onto the ledge. The flap opens 6 frames later and nothing comes out. Blip hops twice from the nameplate to the chute (66.4-67.2) and leans in to look. His pause holds to 67.6 | 66.077 Chiefs slam | CHIEFS, W8, 0 |
| 67.6-68.077 | Track left along the desk (`outCubic`), arriving on the bar with the ledge pair centred and the socket at frame right | The ledge's under-light flashes; SAINTS and RAIDERS stand lit side by side. Blip turns from the chute to the ledge | 68.077 Negative-week wins | Won both negative weeks. |
| 68.077-69.677 | Held composition, 3% drift push | Nothing new enters; the headline holds | none | Same |
| 69.677-70.477 | Whip right along the desk to Lamarley's station | The headline leaves at 70.0, out in 4 frames | 70.077 (next beat) | none |

### Beat table: Lamarley, `lineup-tightends`

| Film time | Shot and its one move | What happens in the set | Hit | Visible copy |
|---|---|---|---|---|
| 70.077 | Whip lands in a medium: START socket low left, BENCH rack high right | Fannin's card slams START (TE teal shaft, sparks); Henry's card drops onto the rack on the same bar at 40% light. Stamps pop in order, 4 frames apart: W5, then 0.90 last and largest | 70.077 Week 5 starters settle | Set: LAMARLEY, START, BENCH, W5, H. Fannin Jr., H. Henry, 0.90 |
| 71.5-72.077 | Crane up to the rack (`inOutCubic`), arriving on the bar | Rack light goes full; Henry's border shaft fires; 11.90 slams, larger than 0.90 | 72.077 Week 5 bench result | 11.90 |
| 72.077-73.5 | Held, 3% drift | Both pairs readable | none | Same |
| 73.5-74.077 | Crane down to the socket (`inOutCubic`) | Stamps clear in 4 frames. The W5 stamp flips once to W8. Fannin lifts and arcs up-left to the rack while Henry drops and arcs right into the socket; their faces never overlap (180° rule). Both land on the bar | 74.077 Week 8 swap lands | W8, H. Henry, START, H. Fannin Jr., BENCH; 4.50 pops 6 frames later |
| 75.5-76.077 | Crane up to the rack (`inOutCubic`) | 18.40 slams, the biggest stamp of the chapter; the TE shaft at full height; sparks at the rack foot, below the text. Blip snaps his head up to the rack twice | 76.077 Week 8 bench result | 18.40. Headline: Again. |
| 76.077-77.677 | Held, 3% drift | The picture and the headline hold | none | Same |
| 77.677-78.477 | Crane up and back over the rack onto the riser behind (Chapter 5) | The headline leaves at 77.95, out in 4 frames | 78.077 (Chapter 5) | none |

Copy changes for David to approve:

- **Dropped:** "Gibbs / The defense experiment." and "Lamarley / The tight-end switch.". The desk nameplates and socket placards show both (rules 26, 40).
- **Changed:** "The points stayed on the bench." becomes "Again.". Six words need about 2.5 s and the bar gives 1.6 s; BENCH already reads on the rack (rules 38, 39). The bigger score benched a second time is the one thing the picture cannot say.

### Desktop and phone composition

| Shot | Desktop (1440x900) | Phone (390x844) |
|---|---|---|
| Gibbs socket | Socket and shield in the centre-right third, at 45% of frame height. Nameplate at left on the desk face. Headline in the upper right beside the socket | Socket and shield at 40-45% of frame height, centred. Headline directly above it. Controls stay at the bottom, below the desk |
| Ledge pair | Both shields whole at left, socket at frame right | Both shields whole and centred, socket cropped at the right edge |
| Lamarley pair | START low left, rack high right, both whole in one medium. The cranes are small re-centres | Rack straight above the socket. The featured card is at least 40% of frame height; the other card shows its name and stamp whole at the top or bottom edge |

Text stays upright and sharp in both layouts: DOM headlines, with stamps as Chapter 1's textures. Tokens move
only sideways and down, away from the headline. Sparks, shafts and Blip stay below the type (rule 36).
Portraits render below their 512 px native size (rules 24, 31). START and BENCH are words, never colour alone.

**Reduced motion.** Each hit's end state appears on its bar line. Nothing flies, no token travels,
and there are no shafts, sparks or shake. The camera cuts to each shot's settled framing with a 0.3 s
cross-fade instead of the whips and cranes. The flap is shown open for Chiefs. Blip appears at the chute
without hopping. Every result and headline shows for its full window.

**Seek and reverse.** Every pose is a pure function of film time, as in Chapter 1. Shields, cards,
stamps, tokens and the flap are rebuilt from the receipts each frame. Seeking before a landing hides that
object (rule 19). Seeking back across 74.077 restores the W5 assignment and hides W8's scores. Seeking back
across 66.077 closes the flap and refills the rail. Impacts are pure functions of their age (`film-impact.mjs`).

**Warm-up.** Before Play enables, the room decodes the two 512 px portraits, the three shield and placard
textures and both badges. It then adds warm moments to `scene.mjs` `warmPlayback`: each beat's middle and
0.1 s after each of the eight hits, so the additive shaft, spark and stamp variants compile before the
first cold play (rule 49). Pagehide disposes the desk's geometry, materials and textures with the room.

### Why this is cinematic

| David's word | What changes |
|---|---|
| Infographic | The DOM card page is gone. Numbers are stamps on physical shields and cards in a lit 3D set, and the camera moves through it |
| Not exciting | Every bar lands a physical impact: a slam, a knock-out, a swap, a score. Each beat climbs to its punchline: the empty chute, then the bigger bench score |
| Not cinematic | Whip in, push, track, whip, cranes: one motivated move per shot, cut on bar lines, held 6-12 frames after each impact |
| No cool animation | Shields drop and knock each other out, tokens drain into a chute, cards cross mid-air, border shafts fire, and Blip peeks and double-takes |
| Too slow | 24 s becomes 16 s, with four hits per beat instead of five over 12 s. Two titles are cut and the closing headline is one word |

### Retime list (tests are not edited here)

| Where | Old | New |
|---|---|---|
| `timing.json` `lineup-defense` | duration 12, stat 4; saints 3.5-4, raiders 5.5-6, chiefs 7.5-8, peek 8.4-9.2, outcome at 10 | duration 8, stat 0; saints lands at 0 (its fall leads the beat by 0.35 s), raiders at 2, chiefs at 4, peek 4.3-5.5, track 5.5-6, outcome at 6 |
| `timing.json` `lineup-tightends` | duration 12; players5 1.5-2, bench5 at 4, switch 6-8, switchHit at 6, starter8 at 8, bench8 at 10 | duration 8; players5 at 0, crane 1.4-2, bench5 at 2, switch 3.4-4, swap hit at 4 ("Week 8 swap lands"), starter8 stamp at 4.2 (no hit), crane 5.4-6, bench8 at 6 |
| `test_lineup_chapter_appends_twenty_four_seconds...` | durations 12, 12; starts 62.077, 74.077; plan 106.077 | durations 8, 8; starts 62.077, 70.077; plan 98.077 |
| `test_lineup_impacts_use_exact_bar_lines...` | hits filtered below 86; Saints 66.077, Raiders 68.077, Chiefs 70.077, wins 72.077, cut 74.077, W5 settle 76.077, W5 bench 78.077, W8 switch 80.077, W8 starter 82.077, W8 bench 84.077 | filtered below 78; Saints 62.077, Raiders 64.077, Chiefs 66.077, wins 68.077, cut 70.077, W5 settle 70.077, W5 bench 72.077, W8 swap 74.077 (replaces both W8 switch and W8 starter), W8 bench 76.077 |
| `test_pose_hides_future_weeks...` (chapter seconds) | pose 5, 9, 19, 23; reduced 15 | pose 1, 4.6, 11.8, 15.5; reduced 10.5 |
| `test_music_extension_covers_the_chapter...` | repeats 5; 111.59 | repeats 4; 103.59 |
| `test_settled_shots...` seeks | 67, 69, 71, 73, 79, 85.8 | 63.6, 65.6, 67.5, 69.4, 73.6, 77.5 |
| `test_real_text_and_reverse_seek...` | 85.8, 79, 65 | 77.5, 73.6, 61.5 |
| `test_defense_weeks_and_the_wins_punchline...` | 67, 69, 71, then 73 | 63.6, 65.6, 67.5, then 69.4 |
| `test_deduction_tokens_and_blip_never_cross...` | 66.09, 66.3, 68.09, 68.3, 70.8, 73 | 62.09, 62.3, 64.09, 64.3, 66.8, 69.4 |
| `test_reduced_motion_renders_current_story...` | 85, 75 | 77.5, 72.5 |
| `test_pagehide_removes_the_new_chapter...` | 85 | 77.5 |

The journey tests read DOM selectors (`[data-lineup-defense-card]`, `[data-lineup-history]`, `featureHeight`).
In 3D they need the shot's projected bounds instead, through a new page object (tests/README.md). The ledge
pair replaces `[data-lineup-history]`. Each edit to a frozen test needs `Test-Reapproved` after David's yes.

## Original treatment

Lead with Gibbs's defense experiment, then Lamarley's tight-end switch.
The humor comes from absurd fantasy outcomes across eight weeks, not a claim that
managers should have predicted every result. Keep injury situations out of the joke.

David approved the combined storyboard with "ok go." A Chapter 4 animatic is now
implemented for desktop and phone review. The prior
Burrow/Purdy rotation and Chat/Pollard roast are superseded. David pointed out that
Chat could reasonably have waited for Pollard to establish himself; the available
records do not establish a foolish process or the manager's intent.

## Gibbs's defense department

Gibbs started three defenses at zero or worse: Saints -3 in Week 4, Raiders -1 in
Week 5, Chiefs 0 in Week 8. They contributed -4 combined, and both negative starts
came in wins. Blip confidently installs each DEF plate; a negative result withdraws
point tokens from his lineup. The zero-point dispenser opens and nothing comes out.
His expectant pause is the gag, not a pretend NFL sack or tackle.

These are selected weeks, not three consecutive starts. The full defense sequence
was 2, 1, 8, -3, -1, 15, 3, 0: **25 points from eight actual DEF starts**. Show or
account for the good weeks when revealing the season total. Positive recorded
projections do not establish that the manager knew a deduction was coming.

## Lamarley's tight-end switch

Week 5: H. Fannin Jr. starts for **0.90**, while H. Henry scores **11.90 on the
bench**. Week 8: Henry starts for **4.50**, while Fannin scores **18.40 on the
bench**. Follow the player swap, then find the bigger score on the bench again.
Blip turns back toward the bench; no invented manager quote is needed.

Keep W5 and W8 explicit: these were not consecutive weeks. Do not say Lamarley
always chose wrong. In Week 7, starting Henry's 10.60 narrowly beat Fannin's benched
10.10. Both featured starters had higher recorded projections. The joke is the
frustrating outcome of a plausible choice, not incompetence. Neither featured
bench swap alone changes that week's actual winner.

## Shot and reading budget

**Superseded, DOM animatic.** The cinematic revision at the top replaces this table and its
62.077-86.077 placement (2026-11-05). Kept as the record of what David reviewed.

The twenty-four seconds below are chapter-local. The timing sheet places Chapter 4
at 62.077-86.077, preserving the existing opening and Chapters 1-3 placements.
The animatic uses the music map recorded below; the table remains the review target.

| Chapter time | Camera and subject action | Exact proposed visible copy |
|---|---|---|
| 0-4 s | Establish Gibbs's badge and physical DEF socket in a low diagonal camera move. Settle before the first score. | Gibbs / The defense experiment. |
| 4-6 s | Saints plate seats in the socket. Three point tokens leave the lineup; the deduction settles for reading. | W4 / Saints / -3 |
| 6-8 s | Track the replacement Raiders plate into the same socket. Another token leaves. | W5 / Raiders / -1 |
| 8-10 s | Advance explicitly to Week 8 Chiefs. The dispenser opens, nothing drops, and Blip looks inside. | W8 / Chiefs / 0 |
| 10-12 s | Keep the three selected receipts together and reveal the result twist. | Won both negative weeks. |
| 12-14 s | Track along the desk to Lamarley's badge. Establish the TE socket and a visibly separate bench behind it; Gibbs's receipts leave frame. | Lamarley / The tight-end switch. |
| 14-18 s | W5 Fannin locks into START. Arc toward Henry on the BENCH as his larger result rises; settle both results together for the final two seconds. | W5 / H. Fannin Jr. / START / 0.90 / H. Henry / BENCH / 11.90 |
| 18-20 s | Advance to W8. The two portraits exchange places; scores clear before the swap and new scores attach only once the players settle. | W8 / H. Henry / START / H. Fannin Jr. / BENCH |
| 20-24 s | Henry's 4.50 appears, then the camera finds Fannin's 18.40 on the bench. Blip looks back; all movement settles for a two-second read. | H. Henry / START / 4.50 / H. Fannin Jr. / BENCH / 18.40; headline: The points stayed on the bench. |

The chapter title can be **Start/sit regrets.** No manufactured manager quote or
claim that the two managers should have known these results belongs in the scene.

## Desktop and phone composition

**Superseded, DOM animatic** (2026-11-05): see the cinematic revision's composition table.

Desktop uses the desk's front/back depth: active socket near the camera, bench
behind a clear boundary. One selected object controls attention. Deduction tokens
never cross the score, name or headline. The two tight ends share one focal
cluster; distinguish START from BENCH with words, never color alone. Keep the
headline near the featured players, with the week and each result nearby.

Phone features use at least 40% of frame height for the selected socket/emblem
cluster. Manager badge, week and score sit beside or directly below it. The three
non-positive defense plates replace each other in the same large composition.
For Lamarley, place the featured starter above the bench player and move the camera
between them; settle with both name/result pairs visible rather than shrinking two
full desks onto one screen. Keep the featured portrait/socket cluster at least 40%
of frame height without enlarging portrait pixels beyond their native resolution.
Text stays upright and sharp;
lighting and Blip stay clear of it. Reduced motion presents each real result without
token travel. Preserve readiness, seek/reverse behavior and resource cleanup.

## Other researched stories, not selected yet

- **COOKed's unused defense:** Week 2 Panthers scored 25 on his bench, matching
  Gibbs's entire eight-start DEF total. Starting Eagles scored 3; COOKed still won
  101.12-83.36. Eagles had the higher recorded projection, 8.05 versus 7.04. Retain
  as a researched backup, not a third story in the selected chapter.
- **Gibbs's bench during the skid:** Week 6 Bernard had 20.20 on the bench versus
  starting WR Washington's 8.40. Week 8 Emmett Johnson had 22.80 on the bench versus
  starting RB McGowan's 2.90. Each same-position replacement would mathematically
  overturn that week's losing score with the opponent held fixed: 130.34-126.60
  and 124.40-119.16 respectively. These are hindsight counterfactuals, not real wins
  or proof that the manager could foresee them. Bernard's FA add was October 14,
  03:09 PDT, before Week 6. Further availability/lock context is needed before a
  blame-oriented story; the defense gag does not require such a claim.

Pollard is excluded as a roast. His first five benched scores were 3.90, 7.00,
11.60, 12.00 and 5.20. The bench 35 alone does not establish a failed process; his
next actual start produced 27.20. Week 6 availability constraints and Chat's intent
were not established. Do not infer either from the box score.

## Receipts and build boundary

Verified locally November 5, 2026, through Week 8 only. Data root:
`C:/Users/David/.ff-jarvis-history/data`.

| Week | Gibbs DEF starter | Points | Actual Gibbs result |
|---|---|---:|---|
| 1 | Rams | 2 | W 128.12-70.66 |
| 2 | Chiefs | 1 | L 83.36-101.12 |
| 3 | Chiefs | 8 | W 141.28-86.60 |
| 4 | Saints | -3 | W 82.78-80.28 |
| 5 | Raiders | -1 | W 133.94-70.64 |
| 6 | Chiefs | 15 | L 118.54-126.60 |
| 7 | Chiefs | 3 | L 79.48-138.66 |
| 8 | Chiefs | 0 | L 104.50-119.16 |

| Week | Lamarley TE starter | Points | Bench TE | Bench points | Actual result |
|---|---|---:|---|---:|---|
| 5 | H. Fannin Jr. | 0.90 | H. Henry | 11.90 | W 126.04-108.40 |
| 7 | H. Henry | 10.60 | H. Fannin Jr. | 10.10 | Context: starter outscored bench |
| 8 | H. Henry | 4.50 | H. Fannin Jr. | 18.40 | L 87.90-111.38 |

Recorded projections: W5 Fannin 8.41, Henry 8.31; W8 Henry 8.89, Fannin 8.03.

- `yahoo_league_box.json`, `weeks[1..8]`: historical starting slots and benches
  for every claim. Week 2 team 2 has Eagles 3 in DEF and Panthers 25 on the bench.
- `yahoo_league.json`: actual outcomes and margins; bench points are not added to
  the team's recorded score.
- Transaction archive: `2026-09-30.jsonl` records Gibbs's Saints waiver add on
  September 30, 00:44 PDT, and Chiefs drop. `2026-10-07.jsonl` records Saints
  drop; `2026-10-10.jsonl` records Raiders waiver add October 10, 00:34 PDT.
  `2026-10-12.jsonl` records Chiefs FA add October 11, 17:42 PDT;
  `2026-10-14.jsonl` records Raiders drop October 14, 00:41 PDT.
- `history/transactions/2026-10-08.jsonl` records Lamarley's Henry FA add on
  October 7; `2026-10-14.jsonl` records Gibbs's Bernard FA add on October 14.

Reuse badges, team emblems, broadcast fonts, Blip and deterministic film state.
Build the DEF/TE sockets, token mechanism, bench boundary, two-player swap and
checked historical lineup contract. Tests must pin all eight Gibbs defense starts
and the 25 total, three non-positive starts, both negative-week wins, Lamarley's
W5/W8 start/bench assignments and scores, and the W7 counterexample. Reject
null-as-zero, bench-as-start and duplicate weeks. Include phone
composition, reverse seeking, reduced motion, readiness and cleanup.

## Music map and implementation

**Superseded in part** (2026-11-05): the cinematic revision uses four phrase copies and bar lines
62.077-76.077; the cue times below describe the DOM animatic.

The played file is now `ascent-to-the-podium-lineups.mp3`, 96 seconds including the
unchanged six-second playback offset. At asset 68.077 (film 62.077), insert three
copies of asset 50.077-58.077: an eight-second, four-bar phrase from the existing
read-hold track. Each boundary has a five-millisecond edge fade without shortening
the phrase. The original read-hold asset remains untouched. The edit is reproducible
with `python scripts/build_lineup_music.py` and configured in `music-edit.mjs`.

At 120 BPM, the new landings are film 66.077, 68.077, 70.077 and 72.077 for Gibbs;
76.077, 78.077, 80.077, 82.077 and 84.077 for Lamarley. All sit on the established
two-second bar grid. The onsets module maps the repeated phrase and shifts only
the old post-insertion tail. No newly detected drum transient is claimed.

The DEF plates use large NFL abbreviations in a dimensional shield, rather than
newly fetched official logo art. The two TE portraits use existing 512px local
assets; rendered portraits stay below native size. Blip reuses the Team Watch mark
and the existing anticipation/lift/landing/squash model. The same desk tracks into
the TE sockets without a second wipe. A silver wipe overlaps the outgoing pickups
plate, and the 3D room rests during the new DOM chapter.

The checked receipt file is `lineups-receipts.json`; no bench contribution enters
an actual team score. Seeking reconstructs the shot, including reverse swaps and
future-score hiding. New images and shared fonts decode before Play, and pagehide
disposes the overlay. Chapter 3's separately approved cinematic rebuild is still
pending; this work does not claim to have completed it. Chapter 5 is not built.

Next: review the live animatic's pacing, reading holds, swap continuity and music
on desktop and phone before approving further polish. Independent storyboard/still
review has not run because the prior delegation budget is exhausted. Cold-play
latency and subjective audio continuity still require playback review.

## November 6 defense-card revision

This treatment supersedes the defense shield/ledge composition above. The eight-second beat remains 58.077–66.077; the tight-end sequence and music cues are unchanged.

- Gibbs's avatar and name appear once above the action, with “The defense experiment.”
- Saints logo and name, “STARTED · WEEK 4”, and “−3 PTS” form one lineup card. The incoming wipe clears to an empty desk; Saints drops 58.727–59.077 on the half-bar beat, matching Raiders’ fall. “Still won.” lands at 60.077.
- Raiders replaces Saints at 62.077: its logo, “STARTED · WEEK 5”, and “−1 PTS”. The retired card never returns.
- “Won both weeks.” lands at 64.077. No extra DEF placard, manager nameplate, WIN stamp or ledge pair.

The logos are local 256px WebPs sourced from ESPN's NFL team-logo assets; both must load before Play. No runtime third-party logo requests. Fine brushed stripes and inner keylines are removed, printed layers have depth bias, TE portrait/stamp layers have more separation, and Chapter 5 card decals no longer write transparent depth. Thin silver outlines on power cards are removed. These reduce identified shimmer risks; stills and material checks alone cannot certify flicker-free playback on David's Fold.

Review the defense beat and power shuffle on the phone before accepting this polish. No publication, video export, music re-encode or generated-HTML rebuild accompanies this revision.
