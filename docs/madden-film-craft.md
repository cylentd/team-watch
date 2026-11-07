# Madden Curse film: craft reference

Techniques for the chapters still to build. [Start here](madden-film.md) for current acceptance,
implementation and evidence. [Film rules](madden-film-rules.md) is the spec a build must pass;
this file explains the decisions. Part 1 preserves Chapter 1 lessons and historical measurements.
Part 2 is general film and motion-design practice; the
numbers in it are working conventions, not measured from a source, so treat them as starting
points.

## Part 1. Chapter 1 retrospective

### Preserve the accepted broadcast package

David accepted Chapter 1: "finally we finished chapter 1. Perfect." Carry this finish forward;
new chapters should not restart the visual exploration or redesign the approved opening.

That first approval covered David's desktop review. He then reopened mobile review, explicitly
saying he had not tested it, and later accepted the corrections with "everyhing looks good now."
Desktop and mobile are now accepted; that does not turn unimplemented ideas into finished work.

- Keep the silver Lombardi trophy, Blip's hopping entrance and the current camera choreography.
  The zoom enters the football, followed by a brief cut flash at the handoff rather than an
  early flash that masks the approach.
- Use the real Team Watch title face, Bricolage Grotesque 800. THE MADDEN stays white and CURSE
  lime. Keep the subtitle clear of the title. The brand ident appears only in the opening and close.
- Fly-by lights rise from the rectangular card borders. Each position-colored shaft fires just
  ahead of the camera and fades behind it. Preserve the player's face under the light.
- The fly-by has no lower-third text, rule or bottom scrim. At the full-board reveal, the rule
  draws across, the headline eases in and the subline follows. Allow the entrance, then two
  seconds of fully readable hold. One blue backlight wave supports this reveal and settles.
- Lower thirds carry the story headline and useful supporting copy, without repeated "Chapter 1"
  labels. Leave enough mask bleed for descenders; do not reduce the type to solve clipping.
- Godwin retains the purple moving-flame gag. Achane's card cuts cleanly and fades; do not use
  a bone-breaking effect. Romo's finale highlights the entire column, with no red/green card grading.
- Keep Romo's column concealed during the buildup. Accelerating rail lights provide anticipation;
  his column lights on the hit. A fully lit winner before that moment spoils the reveal.

### What the final review taught

| Finding | Cause or mismatch | Lesson for the next chapter |
|---|---|---|
| The bottoms of letters were clipped in every lower third | The entrance clip-path stopped at the line box, cutting off ink such as the tail of "g" even after entry completed | Give masks ink clearance on every edge; check actual descenders, not just element bounds |
| The first football-to-board transition stalled, while replay was smoother | Preparing the assets had not prepared all GPU resources and screen-output shader variants | Warm textures and representative render states before enabling Play; include newly added effects |
| White arcs swept upward across the trophy | The title-impact ring included its rear half, which projected over the subject | Check effects in camera space and in motion; retain the foreground spread from the title's foot |
| A glow around every card did not read as stadium introductions | Simultaneous halos had neither the requested direction nor a timed introduction | Specify source, shape, travel direction, trigger and fade before implementing an effect |
| Circular beams still missed the brief | Light came from a point above the card rather than its border | Attach the emitter to the actual card perimeter; shape matters as much as color |
| Full rectangular shafts obscured the players | Overlapping translucent walls accumulated too much light | Separate the light's activation from its volume density; feather edges and fade along the shaft |
| The board revealed Romo too early | His column brightened during anticipation instead of at the payoff | Build energy with neutral scenery; withhold the answer until the musical hit |
| An added reading hold moved later impacts off the music | Visual timing changed without the equivalent soundtrack and onset adjustment | Update the timing sheet, audio edit and derived onset map together; test downstream hits |
| Mobile showed only a few columns while a full-board wave played | Its overview still used a cropped, close wall shot | Fit every column and round to the actual aspect ratio during ensemble effects; keep close-ups for individual stories |
| Mobile anticipation happened outside the frame | The camera approached the winning column before the neutral rail chase finished | Show the board through the buildup, then move to the winning column after the hit; animate view offsets with the same reveal clock |
| Phone beams missed the visible cards and looked short | Triggers followed the distant look point, with desktop beam height and density | Align activation with the visible ground corridor and tune mobile shaft height and density separately |
| The verdict's headline sat below its evidence | A negative CSS order put the returns first | Lead with the verdict, then the player returns, on both phone and desktop |
| A faster phone pass exceeded the existing edge-speed limit | Changing travel distance without checking projected movement exposed fast foreground crossings | Check motion in screen space; framing can preserve a longer path without weakening the speed cap |

### Reading and watching compete

A desktop watcher reported missing bottom copy while watching the animation. David agreed
that reading below and looking back up felt unnatural. Treat that as an attention/composition
finding; a numerical reading-time budget alone does not settle it.

For the next storyboard, test one focal cluster: the short headline beside the featured player
on desktop and immediately above the card on mobile, with the key stat in the same area.
Let the major move land before asking for reading, while keeping gentle motion in the held
composition. Remove words already communicated by the picture before adding runtime.

This is the proposed treatment, not an implemented Chapter 1 caption redesign. Romo's
headline-above-returns change is implemented. Preserve the approved animations; do not add
blank pauses or extend every beat as a blanket fix.

### Review evidence and boundaries

- [The current acceptance and focused test receipt](madden-film.md#review-evidence) records
  desktop approval, the reopened phone review and David's subsequent acceptance of mobile.
  Agent screenshots alone were not user acceptance. No approval authorizes Chapter 2, export,
  commit or publication without a request.
- The accepted opening plus Chapter 1 runs 44.077 seconds. Its two-second reading extension
  uses `ascent-to-the-podium-read-hold.mp3`; the original soundtrack remains available.
- Before the mobile correction, a focused run passed 30 tests across `test_madden_border_lights.py`,
  `test_madden_sky_lights.py`, `test_madden_headline_entrance.py`,
  `test_madden_colored_path.py`, `test_madden_ident.py` and `test_trophy_opening.py`
  under `tests/`. The later mobile lane passed 40 tests, including the existing motion cap;
  its command is in the reference index. Neither run was a full regression or an MP4 review.
- Earlier browser stills were checked at 360x800, 1440x900 and 817x760; the mobile correction
  also captured playback and stills at 360x800, 390x844 and 1440x900. Playback profiling and
  still review answer different questions; neither substitutes for the other.
- In headless measurements, the cold handoff delay fell from approximately 567 ms to 117 ms
  after preparation. These are diagnostic observations, not a frame-rate guarantee on David's
  desktop or phone. Existing defense-headshot 404s continue to use their fallback treatment.
- Earlier broad tests contain old timing and choreography expectations. The focused acceptance
  run does not resolve those conflicts. Reconcile each against the approved behavior before a
  future land; do not loosen tests just to obtain a pass.
- The final browser checks used the shared server. No additional server, export or deployment
  was created. The feature worktree still contains uncommitted work from multiple iterations.

Review page: `http://localhost:8000/github/team-watch-midseason/showcase/madden-curse/?film`.
Implementation starts in `showcase/madden-curse/`; the timing sheet is `timing.json`.

### What cost the most revisions

| Problem | Revisions | Lesson |
|---|---|---|
| Camera: dizzy fly-by, awkward zooms, tilt | 6 | Earlier revisions implicated competing path moves, orbit and roll. Use one motivated move per shot and check projected speed too; do not infer that speed can never be the problem. |
| Text over the scene, side column, text too small | 5 | Lower thirds improved that iteration, but later feedback exposed the cost of looking between text and action. Decide the focal composition in the storyboard rather than mandating one placement for every scene. |
| The one-note round | ~15 | A revision per note doubled the count. Batch a full watch into one list. |
| Effects that read as cheap (bars, cones, blob flames, a fire ball) | 4 | A placeholder in a review build always gets a note. Build the effect or leave it out. |
| Copy that explained the graphic | 4 | The viewer sees the card; the headline says the one thing the card cannot. |
| The curse mechanic (char, sink, ball, bench stop) | 5 | A gag needs one clear read. The simplest version (ignite, go out, pass on) won. |
| Music | 3 | Map the onsets first and lock every impact to them; "it feels off" is always a hit that is not on a hit. David hears structure (the dun-dun-dunnn, the fanfare's end, the groove's entry); ask for his cue sheet before timing a scene. |

### What worked first time

- The independent still review: it caught text collisions, blur and empty frames before David did.
- The timing sheet: a half-second note is now a number edit, not a rebuild.
- The parallel exporter (15 min to 100 s), and then the live review page, which made exports rare.
- Storyboarding the Godwin beat as a table before building it.

### Process for Chapter 2

1. Ask David for the music cue sheet for the chapter's window (what he hears, at what second).
2. Storyboard as a beat table on those cues. He approves the table.
3. Animatic: flat cards, real timing, real copy, real music. He approves pacing on the review page.
4. Polish per beat, reviewer pass, one batch of notes, one revision, export.

## Part 2. Technique reference

### Camera

| Move | Use it for | Rule |
|---|---|---|
| Push-in | Rising attention, a reveal | Only on a beat that earns it; ease out and stop |
| Pull-back | Context, isolation, a finale | End on the new information, never on an empty wide |
| Orbit | A hero object's form (the trophy) | 45-90° at most, constant radius, slow |
| Whip pan | A chapter or scene change | Hide the cut in the blur; same direction in and out |
| Crane | Scale reveal | Start on a detail, end on the establishing wide |
| Rack focus | Shift attention without a cut | Only when the story shifts; the subject stays sharp |
| Skim / drone | Energy and scale over a surface | Straight path, constant speed, land on a subject |
| Dutch angle | Unease | Avoid in sports; reads as an error |

- **Motivated camera.** Every move has a nameable reason (a reveal, a follow). No reason, lock it off.
- **One move per shot.** A push, an orbit and a tilt together is what made rev 8 tilt.
- **180° rule.** Two rivals (a trade's two sides) keep their screen sides; cross the line only with a neutral shot or a visible move.

### Shot grammar

- **Sizes:** establishing (where we are), medium (the subject), close-up (the emotion), insert (the stat). One idea per shot; step sizes by a clear jump.
- **Shot / reverse** for a matchup: mirrored framing, same lens.
- **Centre** for a hero or trophy, **thirds** for a dynamic scene. Centre is a choice, not a default.
- **Lead room:** more space in the direction the subject faces or moves.
- **Safe areas:** nothing essential outside the inner ~80% (title-safe); the lower third sits in the bottom third.

### Editing and rhythm

- **Cut on action:** cut mid-movement, matching speed and direction across the cut.
- **Cut to the beat:** cuts on downbeats, moves on the off-beats.
- **J / L cuts:** let the music's swell lead the next shot by a few frames.
- **Match cut:** a shape or motion carries across (a card's edge becomes a board slot), in the same screen position.
- **Hold after impact:** 6-12 frames frozen on the hit, then move.
- **Reading time:** about 1 s per 3 words plus 0.5 s. A long headline is shortened, never sped up.
- **Kill your darlings:** the last pass removes 10-15% of the runtime.
- **Pacing curve:** build, hit, release; each chapter ends on a release.

### Motion design

| Principle | Applied to cards and the mascot |
|---|---|
| Anticipation | 3-6 frames of the opposite move before the main one (a card dips before it flies) |
| Squash and stretch | Under 10% on cards; larger on Blip |
| Ease in/out | Never ship linear except loops and scrolling |
| Follow-through | Children (antenna, card tilt) settle 2-4 frames after the body stops |
| Secondary action | Sparks and glints support the hit and never compete with it |
| Staging | One focal point; dim or soften everything else at the hit |
| Appeal | Check every shot as a thumbnail: clear silhouette |
| Impact frame | 1-2 frames of white or an extreme pose, only on the biggest hit |

**Named eases:** `outCubic` / `outExpo` for entrances, `inCubic` for exits, `inOutCubic` / `inOutQuart` for camera moves, `outBack` for a pop with overshoot, `outElastic` rarely, `linear` only for loops.

### Lighting

- **Three-point:** key 45° off axis and high, fill to lift shadows, rim for separation.
- **Ratio:** about 4:1 key-to-fill for a hero shot, about 2:1 for cards and UI.
- **Rim:** thin, cooler or brighter than the key.
- **Volumetrics and haze:** low density, so blacks stay black.
- **Practicals:** a visible lamp casts matching light.
- **Temperature:** one warm, one cool, no more.
- **No flat light:** every subject shows a light-to-shadow gradient.

### Broadcast package conventions

- **Chyron slam:** in over 8-12 frames, hold 2-3 s, out faster than in.
- **Card reveal:** fly in, settle, then stats pop in order of importance, 3-5 frames apart; the number the viewer needs most lands last and largest.
- **Hero pose:** low angle, rim light, slow push, silhouette to detail.
- **Speed ramp:** ramp on the beat, back to normal on the next bar.
- **Flare:** one per sequence, from a light in frame.
- **Particles:** secondary; never over text.
- **NFL Films look:** low angles, shallow depth, slow motion, dark contrasty grade. Epic for stakes, warm for nostalgia.

### Music

- **Onset-locked hits:** analyse the transients once, drive every impact from that list.
- **Let the build carry a reveal:** a riser covers a slow push; reveal on the drop, not before.
- **Silence before the punchline:** once per film.
- **Hit the downbeat, breathe on the bar:** one major hit per bar at most.

### Sources (accessed 2026-11-04)

- https://artlist.io/blog/camera-movements/
- https://www.comp.nus.edu.sg/~cs5245/lecture/camera.pdf (the 180° rule)
- https://uxcel.com/blog/12-principles-of-animation-a-guide-to-motion-design-133
- https://madegooddesigns.com/motion-design-principles/
- StudioBinder and School of Motion pages did not load in the search; their entries above are unverified.
