"""While the film's music plays, the picture follows the music (rules 16-18: hits within 2 frames at 30 fps).

The sound object is driven in Node with a fake Audio that starts late and reports its time in coarse steps,
the way a real element does; the loop is the same one app.mjs ticks: clock(time, delta) ?? time + delta."""
from test_madden_stage_polish import stage_result

HARNESS = '''
const {SYNC, MUSIC_OFFSET} = await import(base + '/music-onsets.mjs');
const tolerance = SYNC.frames / SYNC.fps;
class FakeAudio {
  constructor() { this.currentTime = 0; this.paused = true; this.seeking = false; this.readyState = 4; this.ended = false; this.volume = 1; this.src = ''; this.startAfter = 0; this.step = 0; }
  play() { this.paused = false; this.waited = 0; return Promise.resolve(); }
  pause() { this.paused = true; }
}
let wall = 0, fake;
globalThis.Audio = class extends FakeAudio { constructor() { super(); fake = this; } };
const node = () => ({connect() {}, disconnect() {}, start() {}, stop() {}, frequency: param(), gain: param()});
function param() { return {setValueAtTime() {}, exponentialRampToValueAtTime() {}}; }
globalThis.AudioContext = class { currentTime = 0; destination = {};
  createOscillator() { return node(); } createGain() { return node(); }
  resume() { return Promise.resolve(); } suspend() { return Promise.resolve(); } close() {} };
globalThis.fetch = async () => ({blob: async () => ({})});
URL.createObjectURL = () => 'blob:music';
URL.revokeObjectURL = () => {};
const {createSound} = await import(base + '/audio.mjs');
// One 60 Hz frame: the audio element advances once it has started, in `step`-second readings.
function run(sound, {startAfter, step, seconds, follow = true}) {
  const dt = 1 / 60, lags = []; let film = 5, trueAudio = null, waited = 0;
  sound.play(film);
  trueAudio = fake.currentTime;
  for (let frame = 0; frame < seconds * 60; frame++) {
    waited += dt;
    if (waited > startAfter) { trueAudio += dt; fake.currentTime = step ? Math.floor(trueAudio / step) * step : trueAudio; }
    const heard = follow ? sound.clock?.(film, dt) : null;
    film = heard ?? film + dt;
    sound.update(film);
    if (waited > startAfter + .5) lags.push(film - (trueAudio - MUSIC_OFFSET));
  }
  return {worst: Math.max(...lags.map(Math.abs)), tolerance};
}
'''


LATE_STARTING_TRACK_DOES_NOT_LEAVE_THE_PICTURE_AHEAD_OF_IT_SCRIPT = ('''
const sound = createSound(true); await sound.toggle();
return run(sound, {startAfter: .3, step: 0, seconds: 6});
''')

COARSE_AUDIO_CLOCK_READINGS_ARE_SMOOTHED_INSIDE_TWO_FRAMES_SCRIPT = ('''
const sound = createSound(true); await sound.toggle();
return run(sound, {startAfter: .1, step: .05, seconds: 6});
''')

FILM_TIME_IS_THE_MUSIC_TIME_MINUS_THE_OFFSET_SCRIPT = ('''
const sound = createSound(true); await sound.toggle(); sound.play(10);
fake.currentTime = 10 + MUSIC_OFFSET + .4;
return {film: sound.clock?.(10, 1 / 60) ?? null, offset: MUSIC_OFFSET};
''')

WITHOUT_PLAYING_MUSIC_THE_CLOCK_IS_NOT_USED_SCRIPT = ('''
const off = createSound(true); off.play(3);           // sound never turned on
const still = createSound(false); await still.toggle(); still.play(3);   // not a film: no music element
const paused = createSound(true); await paused.toggle(); paused.play(3); fake.paused = true;
const scrubbing = createSound(true); await scrubbing.toggle(); scrubbing.play(3); fake.seeking = true;
const loading = createSound(true); await loading.toggle(); loading.play(3); fake.readyState = 1;
const stopped = createSound(true); await stopped.toggle(); stopped.play(3); stopped.stop();
return [typeof off.clock, ...[off, still, paused, scrubbing, loading, stopped].map(sound => sound.clock?.(3, 1 / 60) ?? null)];
''')


def run(body):
    return stage_result(HARNESS + body)


def test_a_late_starting_track_does_not_leave_the_picture_ahead_of_it():
    result = run(LATE_STARTING_TRACK_DOES_NOT_LEAVE_THE_PICTURE_AHEAD_OF_IT_SCRIPT)
    assert result['worst'] <= result['tolerance'] + 1e-9


def test_coarse_audio_clock_readings_are_smoothed_inside_two_frames():
    result = run(COARSE_AUDIO_CLOCK_READINGS_ARE_SMOOTHED_INSIDE_TWO_FRAMES_SCRIPT)
    assert result['worst'] <= result['tolerance'] + 1e-9


def test_film_time_is_the_music_time_minus_the_offset():
    answer = run(FILM_TIME_IS_THE_MUSIC_TIME_MINUS_THE_OFFSET_SCRIPT)
    assert abs(answer['film'] - 10.4) < 1e-9


def test_without_playing_music_the_clock_is_not_used():
    answer = run(WITHOUT_PLAYING_MUSIC_THE_CLOCK_IS_NOT_USED_SCRIPT)
    assert answer == ['function'] + [None] * 6
