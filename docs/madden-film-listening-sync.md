# Phone listening corrections

The phone and desktop should share musical cue times. Responsive framing is allowed;
a phone camera finishing a story move a second after the music is not.

## Visible arrivals

David identified the COOKed sound at approximately 33.3 seconds and the Romo reveal
around 40 seconds during Tailscale phone review on November 5, 2026.

| Event | Previous working behavior | Revised working behavior |
|---|---|---|
| COOKed arrival | 34.077 | 33.300, using David's listening marker |
| Godwin 0.0 | 34.577 | 33.581, the following existing onset |
| Board anticipation begins | 38.048 | 37.587, an existing onset |
| Romo column light | 40.077 | 40.077, unchanged |
| Phone framing reaches Romo | About 41.221 | 40.077, with the light |
| Desktop pull reaches its verdict frame | About 42.077 | 40.077, with the light |

The first four Godwin stops now land at 28.577, 29.577, 30.577 and 31.577. Roster
stops retain their fire-travel hold; the wire has a shorter hold. The final leap and
pan settle on 33.300. Chapter boundaries and the film's 62.077 duration are unchanged.

The 33.300 marker is listener-supplied, not an independently detected waveform
transient. `LISTENING_CUES` identifies it separately before it enters the combined
musical cue list. No audio asset was recut or offset changed for this correction.

## Fly-by accents

The camera chase remains the base light sequence. For each detected hit in the skim,
one nearby card can become an accent when its natural flash is within 0.18 seconds
of that hit. Its peak is aligned to the hit and its shaft and face are stronger;
other cards retain their camera-triggered pulses. Selection is deterministic per
viewport. The camera path does not change, and a cue never accents several cards.

## Playback limits

Both layouts use `createSound.clock` in the same `app.mjs` tick. This correction does
not establish a Tailscale transport delay or measure the user's handset, speakers
or headphones. Local Chromium at phone widths is not an actual phone playback test.

Focused evidence and remaining protected-test disagreements are recorded in the
conversation. New tests live in `tests/test_madden_listening_sync.py`; old timing
assertions remain unchanged pending scoped reapproval. Capture scripts and stills
are under `.claude/review/listening-sync/`. No independent review, full-film
regression, generated HTML rebuild, export, commit or publication accompanies this work.

The final focused run collected 75 tests: 71 passed and four retained expectations
failed. Those four still require the old roster-arrival times, no phone frame shift
before the light hit, COOKed at 34.077 and the 0.0 at 34.565. They were not weakened.
All five new synchronization tests passed. Four original cases were observed red
before implementation; the fifth adds actual camera-composition coverage. The
general impact-alignment and fire-hold tests pass without expectation changes.
