"""What the viewer SEES lands on the music (David, 2026-11-05: "the buildup happened a tick too early";
"I count the reveal as the lit up column"). Rules 16-18: a visible change lands within 2 frames at 30 fps
of its kick. Kicks measured on the played file (film seconds): bar lines 34.077, 38.077 and 40.077, the
loudest of the passage; flux onsets 34.565, 38.048 and 38.931. Checked through the pure motion functions,
frame by frame."""
import pytest

from test_madden_stage_polish import stage_result

FRAME = 1 / 30
LIMIT = 2 * FRAME
REVEAL_KICK = 40.077
BUILD_KICKS = [38.048, 38.931]
COOKED_KICK = 33.300
STAMP_ONSET = 33.581
BASE = .16          # draft.mjs LIGHT.focus, the light a card has going into the build
WINNER, OTHER = 4, 7

SCRIPT = """
const {BUILD, buildCardLight} = await import(base + '/draft-build.mjs');
const {FINALE} = await import(base + '/draft-curse.mjs');
const {filmPlan} = await import(base + '/film.mjs');
const plan = filmPlan(), beat = id => plan.beats.find(entry => entry.id === id);
const injury = beat('injury'), finale = beat('finale');
const frame = 1 / 30, first = Math.ceil((injury.start - .5) * 30), last = Math.floor((finale.start + 1) * 30);
const frames = Array.from({length: last - first + 1}, (_, i) => (first + i) / 30).map(film => {
  const clock = film - injury.start;
  return {film, winner: buildCardLight(clock, WINNER, WINNER, BASE, 1), other: buildCardLight(clock, OTHER, WINNER, BASE, 1)};
});
return {frames, steps: BUILD.steps.map(step => injury.start + step), hit: injury.start + BUILD.hit,
  glow: FINALE.glow.map(time => finale.start + time), finaleStart: finale.start};
""".replace('WINNER', str(WINNER)).replace('OTHER', str(OTHER)).replace('BASE', str(BASE))


@pytest.fixture(scope='module')
def light():
    return stage_result(SCRIPT)


def first_frame(frames, test):
    return next(frame['film'] for frame in frames if test(frame))


def test_romos_column_reads_fully_lit_on_the_loudest_kick(light):
    # The reveal: Romo's column many times the rest, with the flash, on the 40.077 bar line.
    frames = light['frames']
    revealed = first_frame(frames, lambda frame: frame['winner'] > 5 * frame['other'] and frame['winner'] >= 1)
    assert abs(revealed - REVEAL_KICK) <= LIMIT, revealed
    before = [frame for frame in frames if frame['film'] < REVEAL_KICK - LIMIT]
    assert all(frame['winner'] == frame['other'] for frame in before)   # nothing revealed early
    assert abs(light['hit'] - REVEAL_KICK) <= LIMIT, light['hit']
    assert abs(light['glow'][0] - REVEAL_KICK) <= LIMIT, light['glow']   # the column's glow comes with it


def test_each_build_step_is_a_visible_lift_on_its_onset(light):
    # Before the reveal every card pulses alike; each step is a jump in that light on its onset.
    frames = light['frames']
    for kick in BUILD_KICKS:
        step = min(light['steps'], key=lambda time: abs(time - kick))
        assert abs(step - kick) <= LIMIT, (kick, light['steps'])  # honest: allow COND_ASSERT each documented musical kick must produce a visible frame change
        after = next(frame for frame in frames if frame['film'] >= step)
        before = [frame for frame in frames if frame['film'] < step][-1]
        assert after['film'] - step < FRAME  # honest: allow COND_ASSERT each documented musical kick must produce a visible frame change
        assert after['other'] - before['other'] >= .3 * BASE, (kick, before, after)  # honest: allow COND_ASSERT each documented musical kick must produce a visible frame change


CURSE_SCRIPT = """
const {CURSE} = await import(base + '/draft-curse.mjs');
const {ownerState} = await import(base + '/draft-burn.mjs');
const {filmPlan} = await import(base + '/film.mjs');
const curse = filmPlan().beats.find(entry => entry.id === 'curse');
const visit = [{arrive: CURSE.lastLanding, leave: Infinity}];
const first = Math.ceil((curse.start + 5) * 30), last = Math.floor((curse.start + 7) * 30);
const frames = Array.from({length: last - first + 1}, (_, i) => (first + i) / 30).map(film => {
  const seconds = film - curse.start;
  return {film, flash: ownerState(seconds, visit).flash, stamp: seconds >= CURSE.flip[1]};
});
return {frames, end: curse.start + curse.duration};
"""


@pytest.fixture(scope='module')
def curse():
    return stage_result(CURSE_SCRIPT)


def test_cooked_lands_on_the_curse_kick(curse):
    # David, option A (2026-11-05): the switch to COOKed, the card landing and his avatar flashing, on the 34.077 kick.
    landed = first_frame(curse['frames'], lambda frame: frame['flash'] > 0)
    assert abs(landed - COOKED_KICK) <= LIMIT, landed


def test_the_zero_stamp_lands_on_the_next_onset_and_holds_to_the_beats_end(curse):
    # The 0.0 (draft-beats.mjs stampDrop shows it from the flip's end) on the 34.565 onset, after COOKed's landing.
    stamped = first_frame(curse['frames'], lambda frame: frame['stamp'])
    assert abs(stamped - STAMP_ONSET) <= LIMIT, stamped
    assert curse['end'] - stamped == pytest.approx(2.496, abs=LIMIT)
