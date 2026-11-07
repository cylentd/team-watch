import { OPENING, MUSIC_OFFSET } from "./constants.mjs";
import { MUSIC_EDIT, SYNC } from "./constants-music.mjs";

export const SOUND = Object.freeze({impact: .08, ping: OPENING.logoAt - .6, reveal: OPENING.logoAt, volume: .13, decay: .65,
  beat: .5, beatStart: 8, beatEnd: 38, bass: 90, bassEnd: 38, beatLength: .18,
  cut: 260, cutEnd: 110, cutLength: .28, finale: 130, finaleEnd: 45, finaleLength: 1.2,
  stamp: 120, stampEnd: 50, stampLength: .3});
export const MUSIC = Object.freeze({source: MUSIC_EDIT.source, offset: MUSIC_OFFSET, volume: .55, resync: .25,
  hold: SYNC.frames / SYNC.fps, ready: 3});
export const RECEIPT_ENTER = Object.freeze({
  board: Object.freeze({rule: .28, headAt: .08, head: .32, subAt: .2, sub: .3}),
  feature: Object.freeze({rule: .22, headAt: .04, head: .25, subAt: .1, sub: .25}),
  stat: .22,
});

// Preserved app.mjs configuration from the approved film cut.
export const APP_DETAIL = Object.freeze({
  keyboardLeftStep: -0.1,
  keyboardRightStep: 0.1,
});

// Preserved audio.mjs configuration from the approved film cut.
export const AUDIO_DETAIL = Object.freeze({
  gainFloor: 0.001,
  impactFrequency: 105,
  impactEndFrequency: 35,
  pingFrequency: 1400,
  pingEndFrequency: 950,
  pingLength: 0.4,
  revealFrequency: 145,
  revealEndFrequency: 60,
  revealLength: 0.8,
});

// Preserved editorial.mjs configuration from the approved film cut.
export const EDITORIAL_DETAIL = Object.freeze({
  season: 2026,
  through: 8,
  teamCount: 12,
});

// Preserved film-copy.mjs configuration from the approved film cut.
export const FILM_COPY_DETAIL = Object.freeze({
  warrentyTeamId: 3,
  boboTeamId: 4,
  gibbsTeamId: 5,
  auraTeamId: 6,
  honeyTeamId: 7,
  burrowedTeamId: 8,
  chatTeamId: 9,
  jaxonTeamId: 10,
  lamarleyTeamId: 11,
  sausageTeamId: 12,
});

// Preserved film-impacts.mjs configuration from the approved film cut.
export const FILM_IMPACTS_DETAIL = Object.freeze({
  downbeatPadding: 3,
});

// Preserved receipt-entrance.mjs configuration from the approved film cut.
export const RECEIPT_ENTRANCE_DETAIL = Object.freeze({
  cubicExponent: 3,
});

// Preserved timeline.mjs configuration from the approved film cut.
export const TIMELINE_DETAIL = Object.freeze({
  smoothstepCoefficient: 3,
});
