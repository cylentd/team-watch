# Madden Curse film: rules for video and copy

These rules collect David's direction through Chapter 1 acceptance. Apply them before a review
build. Check framing in stills and choreography in playback; code inspection alone proves neither.
Start with [the reference index](madden-film.md) for acceptance, implementation and evidence.
The [craft reference](madden-film-craft.md) explains the decisions; it is not a second rulebook.
Rule IDs stay stable because source and tests cite them. Defaults below yield to an explicitly
approved, sequence-specific treatment, not to an agent's preference.

## Process

1. **Storyboard first.** Each chapter gets a beat table (time, what moves, what lands) that David
   approves before any code is written.
2. **Review in the browser, not an MP4.** Review the live film page (`?film`, with its beat menu:
   jump, loop, scrub). Approval of a visual revision does not authorize a commit, push or export.
   Export an MP4 when requested after the chapter is approved.
3. **Animatic first.** A chapter starts as a rough with flat cards, real timing, real music and
   real copy. David approves pacing and story on the animatic; polish (flames, lighting, camera)
   starts only on approved timing.
4. **Timing is a sheet.** Every beat's duration, hold and camera move lives in one timing file
   (`timing.json`), never in code. A timing note is a one-number edit; the onset test still guards
   the music.
5. **Batch the notes.** Collect every edit in a round, then build once.
6. **One chapter at a time.** Never build the next chapter until the current one is approved.
7. **An independent reviewer judges the stills before David sees them.** A fresh agent gets only
   this file, the storyboard and the screenshots, never the builder's report. It grades every rule
   pass or fail with the frame that shows it. The builder fixes the failures, and the review runs
   once more at most.

## Facts

8. **Verify every claim against lineups and transactions.** For each claim, check whether the
   player was started or only rostered, who held him in which week, and which team he is on now.
9. **No causal claim without the results.** Check the team's W/L record in the weeks it held the
   player before asserting that ownership caused losses. Godwin's curse is a league running joke;
   preserve the joke without presenting it as a verified causal finding.
10. **Measure with David's definitions.** Rule A: weekly position rank. A smash is a top 6 QB/TE or
   a top 12 RB/WR. A bust is outside QB/TE 18 or RB/WR 36. Value is drafted position rank minus
   finish rank. Missed games count as zero points. Never use raw points or hindsight PAR as value.
11. **Injuries are bad luck, never a joke.** Show an injury beat straight, and never imply the
   manager is still waiting on the player.

## Pacing and motion

12. **Default to 4 to 5 s for a feature beat.** Budget a readable payoff within it. The approved
    board establishment and multi-stop Godwin trail are longer sequences; their timing lives in
    the sheet. A words-per-second estimate is a planning aid, not evidence that a moving shot reads.
13. **Stage attention before text.** Feature headlines enter with their action; a stat (WR7, 0.0)
    lands with its graphic. The board fly-by has no lower third, border or bottom scrim. Once the
    full board settles, draw the rule, ease in the headline, then bring in the subline.
14. **Establish a new environment before its details.** Allow 3 s or more for a sequence such as
    the low pass over the flat draft board. The close fly-by is the long part (3 s or more, faces
    readable). The full-board title gets its entrance, then 2 s fully readable before travel resumes.
    An establishing shot ends on the thing that names the place: the fly-by ends on the team
    avatars and names, because that row is what tells a viewer it is a draft board.
15. **The intro runs 8 s at most, and no second is dead.** The camera or a subject is always
    moving. A hold is a held composition with motion inside it (light sweeping, embers, a slow
    push), never a frozen frame.
16. **Hold the payoff.** A title or rank reveal holds about 2 s before the next move.
17. **Map the music before timing anything.** Find the tempo, bar lines and section changes. Every
    beat starts on a bar line, and every section change lands on a scene change.
18. **Hits land on hits.** Every impact (a stamp, a flip, a card cut, a title landing, a cut between
    scenes) sits on a drum onset or a downbeat, within 2 frames. Test it from the onset list, not
    by ear. A beat with no onset near its impact moves to the nearest one. The November 6 Gibbs
    entrance experiment permits Saints at film 59.077 on the established 120 BPM half-bar beat,
    after the incoming wipe; this is a metrical beat, not a detected onset. Other impacts retain
    the onset/downbeat requirement.
19. **Nothing is visible before its moment.** An element enters on its beat (pop, fade or slide),
    never sits pre-drawn in the frame. Week lights, stamps and badges start at zero opacity.
20. **Every scene change is a transition.** A cut is a designed move: a wipe, a camera whip, a
    light sweep or a card flying through. Never a hard cut to black, and never a light turning off
    with nothing taking over. A transition runs 0.7 to 1.0 s, long enough to see what moved.
21. **Cinematic camera, sharp picture.** Use motivated movement, parallax and glints. An explicit
    reading hold may lock the camera; do not introduce drift that defeats that hold. Never a
    visible tilt: the subject stays upright and square to the viewer. Depth of field only on the
    far background, and only if the subject stays pixel-sharp at 1080p; any post-process that
    softens the subject is turned off. Outside an approved reading hold, avoid an unmotivated
    static frame. The board's deliberate tilt is not camera roll.

## Readability

22. **Frame less, bigger.** Feature shots give the selected subject at least 40% of a 390px phone's
    frame height. Ensemble reveals show the required overview: Chapter 1 fits all twelve columns
    and its first ten rounds. Do not apply the feature close-up requirement to that wide shot.
23. **Label locations in words, with a picture.** A place in the story gets the team's avatar plus a
    big word (LINEUP, BENCH, WAIVER), never small print.
24. **Use 512px headshots** where a source exists. Never upscale a 96px one.
25. **No small story-bearing text in a video.** Budget one headline and one number. Required copy
    is at least 2% of the frame height (22px at 1080p); cut footnotes and method lines rather than
    shrinking them. The overview's background card atlas establishes a board, not 120 reading tasks.
26. **Visuals over words.** When a picture carries the point (a headshot, a column lit up, a card
    cut in half), no sentence repeats it. A finale lists at most 5 rows: headshot, name, one number.
27. **Preserve the accepted composition.** Chapter 1's features use the full-width scene and
    broadcast lower thirds; Romo's verdict is a deliberate split with its headline above the list.
    Avoid large unused regions. Do not turn this placement into a universal rule for new storyboards:
    adjacent headline/subject layouts remain a proposal documented in the craft reference.
28. **Even spacing.** Columns, rows and margins are distributed evenly across the frame, and the
    lower-third bar and the scene above it get their own clear space. Feature shots do not waste half
    the frame; the verdict's purposeful split is an exception.
    The scene keeps a gap of at least 4% of the frame height above the bar's rule line; nothing
    touches or crosses the line.
29. **Nothing is cut off.** Every avatar, label and card the story needs sits whole inside the
    frame at 1080p and at 390px.
30. **Indicators are big.** A week light, a stamp or a value badge is at least 4% of the frame
    height, and its label reads at a glance.
31. **Render at 1080p, sharp.** Textures load at their largest size, and nothing in frame looks
    blurry or upscaled.
32. **A hold is as short as it can be read.** A stop in a trail holds about 1 s; a move between
    stops takes about 0.5 s. A stop that cannot be read in 1 s needs bigger graphics, not more time.

## Visual finish

33. **No placeholder geometry in a review build.** Unlit bars read as stray white lines, and
    faceted cones read as cheap. A light has a glow, and a beam fades along its length and edges.
34. **Characters move like characters.** Blip walks or hops: each step has a lift, a landing and a
    squash. He never glides across the floor at a constant speed.
35. **Modern NFL broadcast, not Halloween.** Use polished silver, stadium lighting, physical
    draft-board graphics and clean broadcast wipes. Purple moving fire is reserved for the
    Godwin Curse running joke, explicitly restored by David. No haunted or cracked trophy,
    CRT noise or glitch transitions. Treat the player's portrait respectfully and injuries plainly.
    An injury is the card cut cleanly in half and fading, never broken bones or shards.
    A highlighted column is the whole column lit and pulsing, never green or red tints per card.
36. **Nothing crosses the text.** No beam, glow or object passes over a headline.

## Copy

37. **On-screen copy is headlines, not voiceover.** The film has no announcer. Lines are for a
    viewer reading, not a narrator speaking.
38. **6 words or fewer** for a headline, and 6 or fewer for its subline.
39. **Say each thing once.** A word or idea appears once per screen and never repeats on the next
    screen. The title screen says "The Madden Curse" once.
40. **Never repeat what the graphic already shows.** If the card says C. Hubbard, the headline does
    not name him.
41. **Names are first initial plus surname:** C. Hubbard, M. Golden. A.J. Brown stays as it is.
42. **Plain sports-desk words.** No slogans ("Twelve teams. One obsession."), no corny puns, no
    stat fragments that read oddly ("Round 8. Zero busts.").
43. **A subline supports its headline.** Add a missing, verified fact rather than a second slogan
    or a restatement of the graphic. Omit the subline when the visual already supplies that fact.
44. **Run the writing-hygiene scanner** on every copy file and fix its hits before the build.

## Chapter 1 finish to preserve

45. **Use the actual Team Watch identity.** The Madden Curse title uses local Bricolage Grotesque
    800. Keep THE MADDEN white and CURSE lime. The Team Watch ident belongs in the opening and
    closing, not throughout the film. Do not repeat "Chapter 1" on the lower thirds.
46. **Lights have a source and a sequence.** Fly-by light rises from each card's rectangular border,
    tinted to its position. Fire it as the camera approaches, then fade it behind the camera.
    A circular emitter above a card and an all-board backglow do not satisfy this. Keep the light
    translucent enough to see the portrait. The full-board reveal gets one blue backlight wave,
    then settles for reading.
47. **Do not show the winner during the buildup.** Keep column brightness equal before the finale
    hit. Accelerating rail lights supply anticipation; Romo's whole-column highlight lands on
    the hit. No early glow that gives away the payoff, and no per-card red/green grading.
48. **Animation masks must include the ink.** Leave room for descenders and accents outside the
    line box, including at the fully entered state. Check every lower third, not just its first
    headline. Never fix clipping by shrinking otherwise readable type.
49. **Test a cold first play.** Upload textures and warm the visible scene and screen-output shader
    variants before enabling Play. Warm new effects too. Compare the first handoff with replay;
    smooth seeking or a warm replay alone does not establish smooth first playback.
50. **Keep review controls and lifecycle behavior.** Pause/resume, precise seeking, opt-in audio,
    reduced motion, hidden-tab handling and GPU resource disposal survive visual revisions.

51. **Review mobile choreography independently.** Ensemble effects must fit within the phone
    frame. Light triggers must follow visible cards, not an offscreen look point. Keep the
    suspense visible until the hit; move to the winning column afterward. Put the verdict
    headline above its player returns on both layouts.

Chapter 1 is accepted on desktop and mobile. See [the acceptance record](madden-film.md#review-evidence)
for the review sequence, measured evidence and action boundaries.
