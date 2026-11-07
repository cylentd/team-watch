
export const MUSIC_EDIT = Object.freeze({
  source: './assets/ascent-to-the-podium-lineups.mp3',
  baseSource: './assets/ascent-to-the-podium-read-hold.mp3',
  insert: 20.077, repeat: 2, crossfade: .01,
  extension: Object.freeze({
    at: 68.077, from: 50.077, length: 8, repeats: 4, fade: .005
  }),
  finale: Object.freeze({
    source: './assets/ascent-to-the-podium-finale.flac',
    at: 80.077, length: 24, crossfade: .04, fadeOut: .35,
    onsets: Object.freeze([3.98, 5.992, 6.352, 9.997, 11.492, 17.997])
  })
});
export const SYNC = Object.freeze({fps: 30, frames: 2});
export const SOURCE_ONSETS = Object.freeze([2.461, 2.833, 3.587, 4.087, 5.074, 6.838, 9.578, 10.077, 10.461, 10.832, 13.084,
  13.584, 15.592, 16.091, 16.579, 17.578, 18.576, 19.075, 19.215, 19.586, 20.584, 21.583, 23.591, 24.59, 25.449,
  25.588, 26.587, 27.585, 29.071, 31.579, 32.078, 32.578, 33.448, 33.576, 33.831, 34.075, 34.586, 34.83, 35.585,
  36.084, 36.583, 36.838, 36.966, 37.082, 37.581, 38.565, 38.835, 39.59, 40.078, 40.588, 40.832, 41.587, 41.831, 42.075,
  42.957, 44.571, 69.59]);
