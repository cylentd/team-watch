import { SOURCE_ONSETS, SYNC } from "./constants-music.mjs";
export { SYNC };
/* The drum onsets of assets/ascent-to-the-podium.mp3, in seconds into the asset (the track from 1.98 s).
   Source: a spectral-flux pass, 2026-11-04 (T3 artifacts madden-midseason/ch8/onsets.py): ffmpeg decodes
   the asset to 22.05 kHz mono; 1024-sample Hann frames every 256 samples; log magnitude below 4 kHz, where
   the kick and snare sit; an onset is a flux peak over 2.5 times its rolling 1 s median, 0.1 s from the
   next. A finer pass (512-sample frames, 64 hop) moves none of them by more than 6 ms.
   The track is 120 BPM: its strongest early hit, 10.077 s, is a downbeat, and a bar follows every 2 s
   (34.075 and 40.078 sit on the same grid). Rule 16: every impact in the film lands within 2 frames of
   one of these onsets or of a downbeat.
   10.461 s is added by hand (chapter 17, 2026-11-04): the middle hit of the "dun dun dunnn" David hears under
   the title (10.077, 10.461, 10.832). The same pass finds it at 2.4 times its median, just under the 2.5 cut
   (T3 artifacts madden-midseason/ch17/title/window.py).
   38.565 s is added by hand (2026-11-05): the hit the curse's 0.0 stamp lands on (film 34.565, David's option A).
   The same flux pass run on the played read-hold file finds it at 3.0 times its median; the original pass on
   the source asset did not list it, cause unknown (scratch mc_readhold_sync.py, 2026-11-05). */
import { MUSIC_EDIT } from './music-edit.mjs';
export const MUSIC_OFFSET = 6;
export const LISTENING_CUES = Object.freeze({cooked: 33.3});

const READ_HOLD_ONSETS = [
  ...Object.values(LISTENING_CUES).map(time => time + MUSIC_OFFSET),
  ...SOURCE_ONSETS.map(time => time >= MUSIC_EDIT.insert ? time + MUSIC_EDIT.repeat : time),
  ...SOURCE_ONSETS.filter(time => time >= MUSIC_EDIT.insert - MUSIC_EDIT.repeat && time < MUSIC_EDIT.insert)
    .map(time => time + MUSIC_EDIT.repeat),
];
const EXTENSION = MUSIC_EDIT.extension;
const extendOnset = time => time >= EXTENSION.at ? time + EXTENSION.length * EXTENSION.repeats : time;
const repeatedOnsets = Array.from({length: EXTENSION.repeats}, (_, index) =>
  READ_HOLD_ONSETS.filter(time => time >= EXTENSION.from && time < EXTENSION.from + EXTENSION.length)
    .map(time => EXTENSION.at + index * EXTENSION.length + time - EXTENSION.from)).flat();
const finale = MUSIC_EDIT.finale;
export const ONSETS = Object.freeze([
  ...[...READ_HOLD_ONSETS.map(extendOnset), ...repeatedOnsets].filter(time => time < finale.at - finale.crossfade),
  ...finale.onsets.map(time => finale.at + time),
].sort((first, second) => first - second));
export const DOWNBEAT = 10.077, BAR = 2, BEAT = BAR / 4;
/* Playback starts this far into the asset, so its 10.077 s hit lands the title at film 4.077 s
   (revision 8, 2026-11-04: the title was too slow; 2 s before). */
/* Rule 16's tolerance: 2 frames of the 30 fps export. */

export const filmTime = asset => +(asset - MUSIC_OFFSET).toFixed(3);
/* The film second of the `count`th bar line after the title's hit (0 is the hit itself). */
export const bar = count => filmTime(DOWNBEAT) + count * BAR;
