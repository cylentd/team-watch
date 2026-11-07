import { MUSIC_OFFSET, bar, filmTime } from './music-onsets.mjs';
import { TIMING, at, ats, param, span } from './timing.mjs';
/* The music ("Ascent to the Podium", 120 BPM) is mapped in music-onsets.mjs: its drum onsets in asset
   seconds, and the bar lines from its 10.077 s hit. Film time = asset time - MUSIC_OFFSET.
   ~~Hits at track 1.49, 3.99 ... 43.49 s from a mean-normalised flux pass, and Chapter 1 on the 11.98 s
   section change at film 8.0 s~~ (superseded 2026-11-04, revision 8: that pass ran about 80 ms early
   against the asset, and the title was too slow). */
export { MUSIC_OFFSET };

// Revision 8 (David, 2026-11-04: "title too slow"): Blip hops in on two hits (asset 9.578 and 10.077 s; no onset at 9.08 s), his last landing and the
// title land together on the 10.077 s hit (film 4.077 s), the title holds 2 s while the camera pushes,
// and the spots sweep down into the board on the next bar line. The title forms in `logoDuration`
// before its hit. ~~Formed at 5.52 s over 0.8 s and held until 8 s~~ (revision 7).
// Chapter 17 (David's music cues, 2026-11-04): the title's words land on the three-hit at film 4-5 s, the
// fanfare ends at 7.08 and the board starts on the guitar's entry, so the opening runs timing.json's
// `opening.duration` (7.584 s). `logoAt` stays the stage's moment: the pull-back done, Blip's last landing and
// THE. ~~duration bar(1), 6.077 s~~ (revision 8).
export const OPENING = Object.freeze({
  duration: TIMING.opening.duration, logoAt: bar(0), logoDuration: .25, blipAt: bar(0) - 1.5,
  revealDuration: 1, hops: 2, milliseconds: 1000, maxDelta: 0.05,
  maxPixelRatio: 2, mobileWidth: 640, cameraFov: 36, phoneFov: 44,   // vertical degrees; a phone's portrait frame needs the wider lens
  trophyHeight: 3.7, modelUrl: './assets/lombardi.glb',
  inspectionLimit: 0.75, dragSensitivity: 0.006,
  nudgeAt: filmTime(6.838), nudgeDuration: .6, nudgeAngle: .012,   // the first onset after playback starts
});
/* Every scene change is a designed move (rule 18): `window` seconds centred on the bar line, half before
   it and half after: a camera whip and a light sweep across the frame (draft-camera.mjs, film.css). */
// Rule 18 (David rev 9: transitions still fast): a scene change runs 0.8 s centred on its bar line, the title's
// hand-over to the board 1 s. ~~0.6 s for every change~~ (revision 8).
export const TRANSITION = Object.freeze({window: .8, intro: 1});

export const PALETTE = Object.freeze({
  background: 0x090b0e, silver: 0xcbd0d6, floor: 0x12161b,
  lime: 0xc4f36b, blue: 0x5e7f9c, white: 0xf4f5f6,
  broadcast: 0x377ce8, alert: 0xc62e38, paper: 0xe9edf1, print: 0x111923,
  cardSurface: 0x18232f, boom: 0xffad55,
  field: 0x14251f, fieldLine: 0xf4f5f6,   // faint white yard lines (rev 17; ~~0x8b9d97~~)
  turf: 0x10241a,   // both floors, a muted broadcast turf (David rev 17); set it to 0x12161b to revert
  blipCase: 0x39414a, blipScreen: 0x101a1d,
  // The page's own tokens (design/src/css/base/tokens.css): --up, --down, the position colours, and
  // the curse's black fire (--hex-*, League > Trades), so the film and the site mean the same thing.
  up: 0x37e08b, down: 0xff5a52,
  QB: 0x5ab4ff, RB: 0xff9d5c, WR: 0xff6fd8, TE: 0x3fd8c2, K: 0xd8c38a, DEF: 0xa58bff,
  hexRim: 0xc3a0ff, hex1: 0x5a2a98, hex2: 0x241240, hex3: 0x0c0714, hexMid: 0x1a0d2e, hexCore: 0x030206,
  muted: 0x9ca6b1, slab: 0x161b22, slabEdge: 0x343c47, room: 0x0b0e12, unlit: 0x080a0d,
  // The film's title in Team Watch's palette (ch17, David): the site's warm ink and brand lime (tokens.css --ink,
  // --lime) and the logo's red mark (tokens.css here, --broadcast-red); `inkShade` the ink's bevel shadow,
  // `limeShade` the lime's, `sideFace` the letters' dark extruded sides.
  ink: 0xf3f1ea, inkShade: 0x8f8a7e, brandLime: 0xc8ff2e, limeShade: 0x5f7a12, mark: 0xc62e38, sideFace: 0x1a1d22,
  // The stadium behind the rig: the stand's dark tiers and its far crowd lights (stage-stands.mjs).
  stand: 0x14181e, crowd: 0xd9cfb8,
});

export const css = color => `#${color.toString(16).padStart(6, '0')}`;

/* Seven draft stories after the six-second opening, each starting on a bar line (rule 15). Revision 8
   (David, 2026-11-04: every scene ran about 1 s long): a beat is two bars, 4 s; its motion is done by
   about 2 s and its headline holds 2 s (rule 10). Its stamp lands 1.5 s in, on the bar's fourth beat,
   which the onsets carry in every bar the beats use (music-onsets.mjs). Times are seconds into the beat;
   `pace` 1 everywhere, so a beat's motion clock is the film's. ~~Beats of 6-7.5 s, slowed by a pace of
   1.3-2.4~~ (revision 7).
   Godwin's trail, revision 14 (David's storyboard): five stops in edition.json's order, his WARREN-TY
   roster, the waiver wire, WARREN-TY again (the Oct 28 add), the waiver wire again (the same day's drop),
   and COOKed's roster, where the 0.0 lands. The camera holds one wide shot of WARREN-TY and the wire for
   the first four; the card leaps off the wire's right at `leap`, the camera whips right over `pan`, pushes
   in for `push` s and holds. Every landing and the flip sit on an onset or a bar line, in beat seconds:
   1 (onset 0.994), 2 (bar), 3.5 (3.502), 4.5 (4.501), COOKed 5.37 (5.371), flip 5.5 (5.499).
   Revision 15 (David: hold the 0.0 2.5-3 s): the 0.0 holds 2.5 s to the beat's end. The time came off the
   second wire stop (0.35 s; the wire has no owner to burn) and the leap and pan; the first stops cannot
   move, since no other onset falls between them. ~~COOKed 6, flip 6.5, a 1.5 s hold~~ (revision 14).
   2026-11-05, David option A: COOKed lands on 6 (the 34.077 kick, the loudest of the trail), the 0.0 on 6.5
   (film 34.577, onset 34.565) and holds 1.5 s; the leap, pan and push move 0.5 s later with it. ~~COOKed 5.5, flip 6~~ (rev 17).
   A move takes `move`. `minHold`, a roster stop's least: the 0.42 s run and catch to the avatar
   (draft-burn.mjs BURN) and a beat of burn after it. ~~Four stops, the Oct 28 drop folded into a bounce,
   a camera that widened then pushed in~~ (revisions 12-13).
   Since the film review tooling (2026-11-04) every one of these numbers lives in timing.json, read here.
   Revision 15 (David: Achane ran long): the injury gives 0.5 s of its hold after the fade to the 0.0's hold,
   so the finale stays on its bar line; the injury starts half a bar late, on onset 36.583, its IR on 37.581
   and its cut on the 38.077 bar line (asset s). ~~Curse 8 s, injury 4 s~~ (revision 14). */
const [panFrom, panTo] = span('curse', 'pan'), [pushFrom, pushTo] = span('curse', 'push');
export const TRAIL = Object.freeze({leave: at('curse', 'leave'), landings: ats('curse', 'stop'), move: param('curse', 'move'),
  leap: at('curse', 'leap'), pan: Object.freeze([panFrom, panTo]), push: pushTo - pushFrom, flip: at('curse', 'flip'),
  minHold: param('curse', 'minHold')});
/* A beat settles when its headline hold starts: its length less the hold. `chapter` is the film chapter it
   belongs to (timing.json, 1 unless the sheet says otherwise): Chapter 1 is the draft board, Chapter 2 the trades. */
export const FILM = Object.freeze({
  chapterAt: OPENING.duration, handoff: TRANSITION.intro,
  beats: Object.freeze(TIMING.beats.map(beat => Object.freeze({id: beat.id, duration: beat.duration, pace: beat.pace,
    settle: beat.duration - beat.hold, stat: beat.stat, chapter: beat.chapter ?? 1}))),
});
export const STAT_AT = Object.freeze(Object.fromEntries(FILM.beats.map(beat => [beat.id, beat.stat])));

// The promo keeps its 2 s cold open and 2 s per team, after the 10 s opening.
export const SHOW = Object.freeze({
  duration: 44, coldAt: 10, teamsAt: 12, teamDuration: 2, teamCount: 12,
  castAt: 36, castDuration: 4, finaleAt: 42, titleDuration: 1.2,
  entranceFraction: .22, exitFraction: .82, cutAngle: .3,
});
