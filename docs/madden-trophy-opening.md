# The Madden Curse midseason show

This is the implementation and asset history, including superseded cuts. For the accepted
Chapter 1 film, start with [the film reference index](madden-film.md), then its active rules.
The current `?film` timing comes from `showcase/madden-curse/timing.json` and
`film.mjs`; historical durations below are not the current cut.

## Earlier promo mode

A 46-second, real-time Three.js league promo, with the approved Lombardi opening,
Blip, twelve team avatars and player-specific headlines. The completed Week 8
Recap embeds this show above the player- and manager-focused league article.

### Earlier promo sequence and shared controls

Use the existing shared server:
`http://localhost:8000/github/team-watch-midseason/showcase/madden-curse/`.
No additional server is needed. Everything the page loads is local, including
Three.js, fonts and the GLB; no fal request runs from a reader's browser.

Play runs once: trophy and Blip (0–12 seconds; the title is whole by 8.2 s and
holds 3.8 s), cold open (12–14), twelve two-second team appearances (14–38),
ensemble (38–44), and the final title (44–46). Behind the stage, a lighting rig
of eleven heads; four moving spots sweep the stage, then converge on the trophy
and Blip as the title forms (`stage-lights.mjs`; only the key light casts shadows).
Pause and Resume retain the camera position; the position slider also pauses.
The final avatars link to their team's article. Equivalent text links below
the standalone show provide keyboard navigation. Inspect trophy allows horizontal
dragging or arrow-key rotation; Escape exits inspection. Audio is opt-in and
uses original synthesized impacts, a pulse and team-cut accents, with no narration
or external music recording.

Reduced motion shows the final composition without the camera sequence, while
retaining user-controlled inspection. Hidden tabs pause and never auto-resume.
Page exit cancels rendering and disposes graphics, observers, listeners and audio.
There is no render loop while the scene is idle. Resize and direct input render
only the next required frame.

## Earlier Chapter 1 cuts (historical)

The following timing descriptions retain the iteration history. They are superseded by the
accepted film linked above, not alternate instructions for rebuilding it.

Open `?film` on the same URL. A 6.08 s opening plays, then Chapter 1, Draft
Receipts, 32 s in seven beats: 38.08 s in all (revision 9, 2026-11-04). The default
page is still the promo; it shares the opening's timing, so its title lands at 4.08 s too.
~~8 s opening, 53.5 s chapter, 61.5 s in all~~ (superseded 2026-11-04, revision 8).
~~57.5 s chapter, 65.5 s cut~~ (superseded 2026-11-04, revision 6).

## Reviewing the current film

Review in the browser, not from an export. Render an MP4 only when David requests it after
chapter approval. The [active rules](madden-film-rules.md) govern this workflow.

1. Open http://localhost:8000/github/team-watch-midseason/showcase/madden-curse/?film
2. Use the beat menu at the top right. On a phone it sits above the film's controls. Click a beat to jump to its start.

   | Key | Does |
   |---|---|
   | J | Back one beat |
   | K | Next beat |
   | L | Loop the beat on screen |
   | Space | Play or pause |

3. Edit `showcase/madden-curse/timing.json`. Each beat has its length, the headline `hold`, the camera move and its events in beat seconds.
4. Reload. The film re-times with no code edit, and the sheet is shape-checked as it loads.
5. Use [the focused verification lane](madden-film.md#review-evidence). The earlier
   `tests/test_draft_film.py` and broad revision tests remain historical verification
   references; some contain superseded timing expectations. Do not weaken them to obtain a pass.

Exports and stills hide the menu.

## Revision history

### Revision 10 timing and camera (2026-11-04)

Every beat starts on a bar line of the 120 BPM track. Every impact sits within 2 frames
of a measured drum onset or a downbeat; `tests/test_madden_rev8.py` checks each one.

| Film s | What happens |
|---|---|
| 3.78 to 4.08 | THE MADDEN CURSE falls from 2.6 units up as extruded chrome letters and hits the floor in front of the trophy on 4.08: a 1-frame squash, a 3-frame camera shake, a white shock ring out across the floor in 0.7 s, 44 white and amber sparks, a white dust puff gone in 1 s, and the floor haze pushed outward. The HTML title is hidden; the tagline stays (revision 14, `film-title-drop.mjs`, `film-impact.mjs`) |
| 3.58, 4.08 | Blip's two landings; ~~the title lands on the second~~ (superseded, revision 14: the 3D title above) (asset 10.077 s) with a white flare from the trophy's ball, in 0.4 s and gone 0.8 s later, and the beams brighten with it (revision 13) |
| 4.08 to 6.08 | a thin white haze fades in on the floor, under the trophy's base (revision 13) |
| 6.08 | the title hands over to the board in a 1 s light wipe; the spots swing to the floor |
| 6.08 to 8.73 | one straight dolly over the flat board onto the team avatars, then a 0.4 s hold (revision 15, below). ~~6.08 to 9.38: the close fly-by runs past round 1 and slows onto the avatars (revision 13)~~ |
| 9.58 | the board stands, then the whip out ~~about 1 s of the whole wall~~ (revision 9) |
| 23.08 to 27.58 | one fixed wide of WARREN-TY and the wire; Godwin lands on WARREN-TY (23.08), the wire (24.08), WARREN-TY (25.58), the wire (26.58), then leaps off the right edge at 27.18 while Blip turns to watch (revision 14 storyboard) |
| 27.58 to 28.08 | a whip pan right ending in a 0.2 s push-in, landing on the bar line at 28.08 on COOKed's pad, his avatar catching fire; then a slow push |
| 28.59 | the 0.0 flips in on onset 6.509; it reads 1.5 s before the whip (revision 14) |
| ~~23.08, 27.45~~ | ~~Godwin lands on WARREN-TY's, then COOKed's pad; fire runs to the owner's avatar in 0.3 s and the last owner's goes out (revision 12; COOKed was 26.58)~~ (superseded, revision 14) |
| ~~27.45 to 28.05~~ | ~~one push-in, 0.6 s, back to the first stop's close framing on COOKed and the card (revision 13)~~ |
| ~~28.08~~ | ~~the 0.0 lands on that close-up; 2 s to read it before the whip (revision 12; was 27.58)~~ |
| 10.08 + 4n | each later beat, 4 s long (the Godwin trail 8 s); stamps land 1.5 s in |
| 36.08, 36.96 | Romo's +41, then "Next best: −14" on the next onset |

**Revision 15 (2026-11-04).** These supersede the matching rows above.

| Part | Now |
|---|---|
| Export | full 1920x1080, no black bars; the exporter no longer crops or pads |
| Title | ~~the 3D letters land in the lower-third bar, left-aligned, 56% of the frame wide; the tagline sits at the bar's right end~~ (superseded 2026-11-04, chapter 17 below). The ring, sparks and dust hit at the bar |

**Chapter 17 (2026-11-04): the title lands word by word, and the opening runs 7.584 s.** Each word falls and slams into the bar on one hit of the "dun dun dunnn" David hears at 4-5 s. The times live in `timing.json` `opening`.

| Film s | Asset s | What happens |
|---|---|---|
| 4.077 | 10.077 | THE lands with Blip's last hop: small ring, 40% of the sparks, beams flash at 45% |
| 4.461 | 10.461 | MADDEN: 85% ring, 55% of the sparks, beams at 65% (an onset added by hand, 2.4x its median) |
| 4.832 | 10.832 | CURSE, the biggest: 1.3x ring, all 72 sparks, the trophy flare, a 3-frame camera shake |
| 7.084 | 13.084 | the fanfare's last hit; the 1 s hand-over to the board starts |
| 7.584 | 13.584 | the guitar comes in; the board beat starts |

- **Desktop:** one row, 70% of the frame wide, caps about 14% of its height. The tagline wraps to two lines beside it, in the frame's last quarter.
- **Phone:** THE MADDEN over CURSE, 90% of the frame wide, the tagline under them.
- **Scrim:** off for the whole opening. Before, it lifted at 3.83 s.

~~6.077 s opening, the title on 4.077 as one block~~ (revision 8 to 15).
| Fly-by | fixed yaw, 35° pitch, no roll; 40% higher (1.4 above the table, 2.4 on a phone) on a lens 24% narrower. Cosine ease in and out, 2.65 s moving, 0.4 s hold, stand-up 3.05 to 3.5 s |
| Fly-by speed | no point crosses faster than 25% of the frame width a second; the test measures every board point. So the pass covers the top round and a half on a desktop and half a round on a phone |
| Traded | Brown lifts out of Gibbs' column; Aura's badge (avatar and AURA) pops up off the board's left edge; the card arcs out and lands beside it. Its tag fades by 1.25 s and WR111 slams on 1.5. It never enters a column |
| Godwin pads | solid discs with a dark rim: WARREN-TY in a team colour, the wire grey-blue; one white word under each disc; FREE AGENT gone; Blip stands on the floor at the right edge |
| Godwin timing | landings 1, 2, 3.5, 4.5, 5.37; the leap at 4.85; the whip 4.95 to 5.37; the 0.0 at 5.5 (onset 5.499), held 3 s. The beat is 8.5 s |
| Injury | 3.5 s, starting 30.58 on an onset; IR lands on onset 37.581 and the cut on the 38.077 bar line (asset s). Its headline needs 3.67 s at the words rule's pace |

- **Onsets:** `music-onsets.mjs`, from an ffmpeg and numpy spectral-flux pass over the
  asset. Playback starts 6 s into it (`MUSIC_OFFSET`). ~~`MUSIC_MAP`, 2 s offset~~
  (superseded, revision 8: it ran about 80 ms early).
- **Transitions:** every later scene change is a 0.8 s camera whip under a light wipe,
  centred on its bar line (`TRANSITION`).
- **Camera:** each hold pushes in 8% and drifts at most 3° of yaw through square-on, with
  no roll. ~~Orbits of up to 0.2 rad, a roll on the whip, a depth-of-field lens~~
  (superseded, revision 9: the picture looked tilted and soft).
- **Lights:** all eleven heads glow and every beam shows from the first frame.
- **Board light** (revision 10): every card is lit evenly the whole fly-by. ~~Rows lit
  one by one as the camera crossed them~~ (superseded: the rows ahead read dark).
- **Godwin's fire** (revision 10): a front layer burns up both sides of the card and over
  its lower edge, with the portrait and name left clear; the back layer glows behind.
- **The curse leaves with him** (revision 14): when the card hops off WARREN-TY's pad his fire goes out
  in 0.3 s and his avatar is clean again. No char, smoke or fading pad.
- **The curse is passed** (revision 10, char and smoke superseded by revision 14): each time the card lands on a team's pad, a
  ball of the same fire runs to the owner's avatar in 0.3 s and its ring burns, with
  embers. When the card leaves, that fire goes out in 0.3 s. The avatar is left
  charred (dimmed), with a faint wisp of smoke, and its empty pad and ROSTER word fade
  out with the fire (revision 12). One avatar burns at a time. The run
  starts on the landing, which is on an onset. By the 0.0, WARREN-TY is charred and
  COOKed burns. ~~Every owner kept burning~~ (first rev 10 cut, superseded 2026-11-04).
- **Two stations in the wide** (revision 14): WARREN-TY and the wire stand 2.4 units apart (1.4 on a
  phone), centred. COOKed's station is 6 units right of the wire, off frame until the pan. Blip stands
  at the frame's right edge, in front of the wire on a phone, and shakes his head on the second wire
  landing.
- ~~**Two owners in frame**~~ (superseded, revision 14) (revision 10, desktop): the waiver pit stands at the left
  end, then the owners in the order he reaches them. At a stop after the first, the
  floor shot pans sideways in 0.3 s to take in the owner left charred beside this one.
  A 390px phone keeps one stop.
- **Trail camera** (revision 14 storyboard): fixed wide from the first landing to 5.5 s, no orbit
  and no per-stop move. Then one whip pan over 0.5 s into a push-in on COOKed, then a slow push.
- ~~**Trail camera**~~ (superseded, revision 14) (revision 13): from the first landing to COOKed's the camera only widens,
  one slow ease-out. On COOKed's landing it pushes in once, 0.6 s, eased, to the first
  stop's framing on COOKed's burning avatar and the card, and holds there for the 0.0.
  It never moves back out (David: the 0.0 read weak from the wide shot).
  ~~Revision 12: from the first landing to the 0.0 the camera only
  pulls back, one slow ease-out widen, with no push in at any stop or before the 0.0~~ (superseded, revision 13).
  ~~A per-stop pull-back and a push in to the 0.0~~ (revision 10-11: they fought).
- **Smash weeks burn** (revision 14): the earlier flame icon, animated. It ignites on the tile's pop
  (scale from 0 with a flash), then flickers through 4 outline frames at 12 fps with a 1.0 to 1.08
  scale pulse, a glow behind that pulses with it, and 3 embers off the tip. No shader flame.
- ~~**Smash weeks burn**~~ (superseded, revision 14) (revision 13): a top-12 week light gets a live flame in lime and
  orange, with flicker and 6 embers, lit on its pop and burning to the end of the beat
  (`draft-weekfire.mjs`). Bust weeks keep the red X and solid weeks stay silver.
- **Rule line:** every scene keeps 4% of the frame clear above the lower third's rule
  (76% down on a desktop, 66% on a phone).
- **Godwin's trail** (revision 14): five stops, matching `edition.json`: WARREN-TY roster, WAIVER,
  WARREN-TY (the Oct 28 add), WAIVER (the same day's drop), COOKed. Landings at 1, 2, 3.5, 4.5 and 6
  beat seconds; the leap leaves the wire at 5.1.
- ~~**Godwin's trail:**~~ (superseded, revision 14) four stops, 0.4 s moves: WARREN-TY roster, WAIVER, WARREN-TY
  roster again (the Oct 28 add and drop, a 0.35 s bounce, then it settles), COOKed
  roster, 0.0. Holds, revision 12 (David: the third stop left before its fire spread):

  | Stop | Lands | Holds |
  |---|---|---|
  | WARREN-TY | 1.0 | 0.6 s |
  | WAIVER | 2.0 | 1.1 s |
  | WARREN-TY again | 3.5 | 1.47 s |
  | COOKed | 5.37 | 0.63 s to the 0.0 |

  Seconds into the beat. No stop holds under 0.6 s, the fire's 0.42 s run and catch
  plus a beat of burn. COOKed and the 0.0 moved to the next onsets. ~~Stops of about
  0.8 s, COOKed at 4.5~~ (revision 11).
  `yahoo_transactions.json` now starts at Oct 30, so only the COOKed add is in it; the
  Oct 28 moves survive only in `edition.json`.
~~12 s opening, 41.5 s chapter, 46 s promo~~ (superseded 2026-11-03, revision 4).

- **Opening:** a macro shot on the trophy's ball, one slow orbit and dolly out to
  a tighter wide shot, Blip hops in, then the title forms at film 5.52 s and is
  whole by 6.32 s. It holds 1.68 s with a continuing camera push before Chapter 1.
  All eleven moving heads have working spotlights, including dedicated Blip lighting.
- **Blip hops** wherever he crosses the floor (`blip-hop.mjs`): a crouch, a lift,
  a landing squash; the middle hops are longest, so his speed eases in and out.
- **Curse** (~~superseded by revision 9's four stops, above~~): Godwin's card burns in purple flame, then follows seven transaction stops.
  Each stop holds 1 s, with 0.5 s of travel (`TRAIL` in `constants.mjs`; ~~1.6 s and
  0.6 s~~, superseded 2026-11-04). Each stop shows the team avatar (10% of frame
  height or more), the team name under it and the big LINEUP / BENCH / WAIVER word,
  all whole in frame. The 0.0 stamp lands 1 s after the last landing.
- **Card names** are first initial and surname (C. Hubbard); A.J. Brown stays.
- **Board:** rounds 1 to 10. Featured cards use 512px headshots (`heads/xl`),
  the rest 256px (`heads/lg`), 96px where neither exists.
- **Text in sync** (since 2026-11-03, revision 3): a beat's headline appears on
  the frame its motion starts and the previous one leaves at the cut. The stat
  in it (WR7, WR111, 0.0) appears on the frame its stamp or flip lands
  (`FILM.beats[].stat`). Each beat's motion ends 2.5 s or more before the next.
  ~~The headline lands when the motion ends~~ (superseded 2026-11-03).

| Beat | Shows | Headline |
|---|---|---|
| board | the board lies flat as a table; a low pass reads names and faces, then it stands into the wall | Draft spot vs. reality. |
| steal | Golden rises and holds like Hubbard; W1-W8 lights in a 4x2 grid; WR40 → WR7 big at left | An eighth-round bargain. |
| traded | Brown arcs out of Gibbs' column to Aura's badge off the board, stamped WR111 (~~into Aura's column~~, revision 15) | New team. Same disappointment. |
| sleeper | Hubbard rises, 6 smash lights | Eighth-round rock. |
| curse | Godwin follows the roster, waiver and COOKed path in purple fire passed from owner to owner, each one left charred; 0.0 gets a brief flare | The Godwin Curse |
| injury | Achane's portrait and name read whole, then the card is cut cleanly in two and the halves part and fade | Season cut short. |
| finale | Romo's whole column lit and pulsing, the rest dimmed; five rows (headshot, name, gain) and +41, then Next best: −14 | Romo’s value ran deep. |

### NFL broadcast treatment

The approved restyle uses silver, graphite, white and broadcast blue, with red reserved for
the brand marker and negative outcomes. The intro retains the Lombardi macro, orbiting reveal,
Blip and moving stadium lights; football field markings replace the empty studio floor.
Chapter 1 uses photographic player tiles, flat rank bars and a protected headline column.
The board headline is "Draft spot vs. reality." Phone shots keep playback controls below the
subject; the trade camera tracks the move, then pushes in for its readable rank reveal.
Purple flames belong only to Godwin's league joke, not the overall theme. No cracked trophy,
CRT noise, glitch transitions or injured-player destruction.
The existing music, measured outcomes, beat order and explicit controls remain. The intro now ends at eight seconds.
Review stills before export; no video export, commit or publication is implied by this restyle.

The subsequent review cut is explicitly authorized by David. Keep the improved spotlights,
trophy reveal, Blip hops, Brown flight, Godwin route and existing timing/music. Golden no
longer flips away from his portrait. Achane's subline is "Three games from a second-round pick."
Romo's five rows are Wilson +23, Coker +23, Monangai +12, Coleman +10 and Irving +7;
ties select the earlier draft round. The separate +41 is the entire class, not those five rows.
These are positional places gained (draft price minus season-total scoring rank through Week 8),
not fantasy points, PAR, wins or a complete trade verdict. Only Godwin receives animated fire;
his 0.0 is a player score, not evidence that the manager lost the matchup.

November 4 review revision: dark player-card surfaces, larger supporting copy closer to the
action, numbered W1–W8 markers with orange flames for top-12 weeks, and continuous slow
pushes through reading holds. Godwin uses the faded curse portrait. Achane's lower draft-price
strip is cleanly cut away; his photograph and name stay intact, without white frame fragments.
Romo's original column payoff frames all ten displayed rounds with a blue pulse; all photographs
retain their natural colors. The five-return sidebar stays separate. Blip lands on the floor in
front of the plinth and on a board rail after Golden's stamp hop. The trophy stays stationary
unless manually inspected; only the camera moves. Low silver haze obscures the extended floor's
boundary. Larger type and raised board headers improve reading clearance.
~~The new cut is 65.5 seconds, including its eight-second opening.~~ (superseded 2026-11-04)

Revision 6 (2026-11-04, David's notes on revision 5): ~~a desktop frame gives the headline
column and the scene half each; the board sits centred in the right half~~ (superseded by
revision 7, below). Golden keeps only
the headline, one subline and WR40 → WR7. Achane's card is cut in two and fades; no strip is
cut away. Romo's finale drops the labels, arrows and rank pairs, and no card is tinted green
or red. No film text is under 2% of frame height (`--film-floor`), except the print on the
small board cards in the full-board shots. Textures render at twice the pixel ratio.

Revision 7 (2026-11-04, rule 21): every beat, the opening included, uses the full frame width
with its subject centred. The headline and subline sit in a lower-third bar at the foot of the
frame, over a scrim, and the frame's content is lifted above it (`RIG.lift`, and `FILM_INTRO`
in `scene.mjs` for the opening). Golden's WR40 → WR7 sits at the bar's right end. Romo's finale
is the one split frame: his five returns and the headline own the left half, the board the right.
On a phone the bar stays at the bottom, with the subject centred above it. The promo keeps its
title column. The board's small card print stays as texture. It is drawn on a 2x atlas and
rendered at a pixel ratio of 2.

Data: `design/midseason_draft.py` writes `edition.json`'s `draft` block (Rule A
tiers, price minus finish); `draft-data.mjs` checks it where the page reads it.
Reduced motion shows each beat's final frame with its headline.

Music in `?film` only: `assets/ascent-to-the-podium.mp3`, "Ascent to the Podium",
stored as a 70-second local trim beginning 1.98 s into the original track. Playback skips another
2 s (`MUSIC_OFFSET`), so film time is original track time minus 3.98 s
(`MUSIC_START`). The export fades its final 1.5 s. The onset map is
`MUSIC_MAP` in `constants.mjs` (~~superseded by revision 8's onsets, above; the table below is history~~):

| Track time | Film time | What is there | On screen |
|---|---|---|---|
| 4.74 s | 0.76 s | hit | camera reveal; no trophy wobble |
| 9.5 s | 5.52 s | title cue | Blip lands; the title forms; beams converge |
| 11.98 s | 8.0 s | section change, the track's strongest | Chapter 1 opens on the flat board |
| 15.49 s | 11.51 s | section change | the board stands up into the wall |
| 19.5 s to 63.5 s | 15.5 s to 59.5 s | bar downbeats | steal, traded, sleeper, curse, injury, finale |

Godwin's 0.0 now lands at film 49.9 s, after the final route stop, rather than the old
43.49-second track hit. Injury begins at film 53.5 s and the finale at 59.5 s;
they no longer coincide with the previously documented section changes.

~~Cut from 0 s to 55 s; injury on the 45.42 s change~~ (superseded 2026-11-03).

License unconfirmed: David supplied the file on 2026-11-03. Confirm it before
the film is published. ~~Cut to 23 s, offset 0 s, stamp on the 7.04 s hit~~
(superseded 2026-11-03).

## Trophy and dependencies

Verified November 3, 2026:

- Three.js 0.187.0, MIT, pinned from the official npm package. Only the core,
  GLTFLoader and required utilities are vendored. LICENSE is retained.
- Archivo and Big Shoulders Display are hosted locally with their OFL licenses.
- Tripo endpoint `tripo3d/h3.1/image-to-3d`, schema read from fal's official
  OpenAPI endpoint before submission. Standard geometry, no generated textures,
  30,000-face target. The downloaded GLB is 867,096 bytes.
- The image-to-3D request used David's supplied Lombardi-style trophy reference.
  An earlier text-to-3D request had already completed before the reference arrived;
  two generations were submitted in total. The earlier result is not used.
- The reference's unrelated engraving is excluded from the visible model. The
  generated football is retained, and a clean geometric tapered pedestal replaces
  the generated pedestal using a material clipping plane. Silver reflections and
  lighting are generated locally. Blip is built from geometry, not AI-generated.
- The league wordmark is a typographic study, not a recovered official logo asset.

The credential was read from the shared parent `.env` only in the executor. No
key, `.env`, signed service credential or authenticated API route is shipped.
The user-provided reference was transmitted to fal/Tripo for the requested model.

## Files and checks

`showcase/madden-curse/` separates markup, tokens, styles, copy, timeline, scene,
environment, model, character, audio and event/state wiring. Third-party sources
remain unmodified under `vendor/`.

Run the scoped checks:

```
python -m pytest tests/test_trophy_opening.py tests/test_league_show_timeline.py tests/test_trophy_room.py tests/test_midseason_showcase.py -q -p no:randomly
```

The timeline tests are pure Node imports. Browser tests route local files to an
isolated test origin with no live server/API dependency and use Playwright's
controlled clock. They cover explicit start, finite completion, pause/resume,
reduced motion, keyboard inspection, hidden-tab pause, missing models, unavailable
WebGL, context loss, explicit audio opt-in, and title fit at five viewport widths.

## Editorial data

The build exports `edition.json` from `design/midseason_editorial.json` and the
canonical `design/src/content.json`. Player totals come from actual starting
lineups in the local Yahoo Week 1–8 boxes, excluding bench and IR. Each week must
contain all twelve teams exactly once. Featured players need verified starts.
Draft ownership, trade receipts and archived waiver acquisitions inform the
curated paragraphs; they are not inferred from points or current rosters.

The parent page and iframe share no playback state. Same-origin messages pause
the child or request a report jump; the parent verifies both origin and source.
Week 7 previews retain their existing data-driven scenes and do not expose the
frozen Week 8 show or article. No browser calls fal or Yahoo.

This feature remains local and uncommitted. It has not been published.
