import { AUDIO_DETAIL as TUNING } from './constants-playback.mjs';
import { SOUND, MUSIC } from "./constants-playback.mjs";
import { SHOW } from "./constants.mjs";
import { filmPlan, statAt } from './film.mjs';   // a stamp's sound plays on the frame its stat lands

/* The film's track: Ascent to the Podium, the asset cut from 1.98 s into the track, played from
   `MUSIC_OFFSET` (6 s, music-onsets.mjs) so its 10.077 s hit lands the title at film 4.077 s
   (docs/madden-trophy-opening.md). A drift past `resync` seconds snaps it back to the clock. */
/* While the music plays it is the film's clock (`clock` below): the picture follows what the audio element
   reports, so a late-starting track can no longer sit behind the picture inside the `resync` window.
   `hold` is how far past its last reading the picture may run when the element reports in coarse steps:
   the 2-frame sync tolerance (music-onsets.mjs, film rules 16-18). `ready` is HAVE_FUTURE_DATA. */

export function createSound(film = false) {
  let context, enabled = false, playing = false, lastTime = -1, reading = NaN, held = 0;
  const active = new Set();
  const music = film ? new Audio() : null;
  if (music) music.volume = MUSIC.volume;
  // Fetched whole on the first Sound on (370 KB) and played from a blob, so a seek works on any server,
  // with or without range requests, and nothing loads for a reader who never turns sound on.
  async function loadMusic() {
    if (!music || music.src) return;
    music.src = URL.createObjectURL(await (await fetch(MUSIC.source)).blob());
  }
  const stamps = film ? filmPlan().beats.map(beat => statAt(beat) ?? beat.start) : [];
  const place = time => { if (music) music.currentTime = Math.max(0, time + MUSIC.offset); };
  const listen = () => { if (music && enabled && playing) music.play().catch(() => {}); };
  function tone(frequency, end, length, type = 'sine') {
    if (!enabled || !context) return;
    const oscillator = context.createOscillator(), gain = context.createGain();
    oscillator.type = type;
    oscillator.frequency.setValueAtTime(frequency, context.currentTime);
    oscillator.frequency.exponentialRampToValueAtTime(end, context.currentTime + length);
    gain.gain.setValueAtTime(SOUND.volume, context.currentTime);
    gain.gain.exponentialRampToValueAtTime(TUNING.gainFloor, context.currentTime + length);
    oscillator.connect(gain); gain.connect(context.destination); active.add(oscillator);
    oscillator.onended = () => { oscillator.disconnect(); gain.disconnect(); active.delete(oscillator); };
    oscillator.start(); oscillator.stop(context.currentTime + length);
  }
  return {
    async toggle() {
      if (!context) context = new AudioContext();
      enabled = !enabled;
      if (enabled) { await context.resume(); await loadMusic(); listen(); }
      else { await context.suspend(); music?.pause(); }
      return enabled;
    },
    start() { lastTime = -1; place(0); if (enabled) context.resume(); },
    play(time) { playing = true; place(time); listen(); },
    seek(time) { lastTime = time; place(time); },
    /* The film time the music says it is at, or null when the picture keeps its own clock (sound off, not a
       film, paused, scrubbing, not loaded, ended). `delta` is the seconds since the last tick; between two
       element readings the picture advances by it, for at most `hold`. The device's output latency is
       subtracted when the browser reports one, since currentTime is what was decoded, not what is heard. */
    clock(time, delta) {
      const usable = music && enabled && playing && !music.paused && !music.seeking && !music.ended &&
        music.readyState >= MUSIC.ready;
      if (!usable) { reading = NaN; return null; }
      const latency = Number.isFinite(context?.outputLatency) ? context.outputLatency : 0;
      const heard = music.currentTime - MUSIC.offset - latency;
      if (heard !== reading) { reading = heard; held = 0; return heard; }
      held = Math.min(MUSIC.hold, held + delta);
      return heard + held;
    },
    update(time) {
      if (lastTime < SOUND.impact && time >= SOUND.impact) tone(TUNING.impactFrequency, TUNING.impactEndFrequency, SOUND.decay);
      if (lastTime < SOUND.ping && time >= SOUND.ping) tone(TUNING.pingFrequency, TUNING.pingEndFrequency, TUNING.pingLength);
      if (lastTime < SOUND.reveal && time >= SOUND.reveal) tone(TUNING.revealFrequency, TUNING.revealEndFrequency, TUNING.revealLength, 'triangle');
      if (film) {
        stamps.forEach(at => { if (lastTime < at && time >= at) tone(SOUND.stamp, SOUND.stampEnd, SOUND.stampLength, 'triangle'); });
        if (music && enabled && Math.abs(music.currentTime - (time + MUSIC.offset)) > MUSIC.resync) place(time);
        lastTime = time;
        return;
      }
      if (time >= SOUND.beatStart && time < SOUND.beatEnd &&
          Math.floor(lastTime / SOUND.beat) !== Math.floor(time / SOUND.beat))
        tone(SOUND.bass, SOUND.bassEnd, SOUND.beatLength);
      if (time >= SHOW.teamsAt && time < SHOW.castAt &&
          Math.floor((lastTime - SHOW.teamsAt) / SHOW.teamDuration) !== Math.floor((time - SHOW.teamsAt) / SHOW.teamDuration))
        tone(SOUND.cut, SOUND.cutEnd, SOUND.cutLength, 'triangle');
      if (lastTime < SHOW.finaleAt && time >= SHOW.finaleAt)
        tone(SOUND.finale, SOUND.finaleEnd, SOUND.finaleLength, 'triangle');
      lastTime = time;
    },
    stop() { playing = false; music?.pause(); active.forEach(node => { try { node.stop(); } catch {} }); },
    dispose() { playing = false; music?.pause(); if (music?.src) URL.revokeObjectURL(music.src); active.forEach(node => { try { node.stop(); } catch {} }); context?.close(); },
  };
}
