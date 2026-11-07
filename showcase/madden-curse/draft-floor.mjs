/* The waiver floor in front of the board: one station per place the cursed card visits, in the order
   he first reaches it. A team's station is its roster; the waiver wire is one pit for everyone. */
// Revision 14 (David's storyboard): the camera holds one wide shot of every station but the last, `gap`
// apart (closer on a phone, so the two stops still read at 390px); the last, COOKed's, stands `reveal`
// further right, off the frame, until the whip pan finds it. ~~One row, one stop per frame~~ (rev 10-13).
export const FLOOR = Object.freeze({z: 1.9, gap: {desk: 2.4, phone: 1.4}, reveal: 6});

export function stationKey(step) {
  if (step.kind === 'drop') return 'pit';
  return `roster-${step.team}`;
}

/* The trail's stops from the player's path (edition.json, design/midseason_draft.py): weeks started and
   benched for one team are one roster stop, and a start after an add is the same roster. Every move
   between rosters and the waiver wire is its own stop, the Oct 28 same-day drop included (revision 14;
   ~~folded into a bounce on the roster~~, revision 8). Each stop keeps the steps it stands for. */
export function trailStops(path) {
  const stops = [];
  path.forEach(step => {
    const key = stationKey(step), open = stops.at(-1);
    if (open?.station === key) { open.steps.push(step); return; }
    stops.push({station: key, kind: key === 'pit' ? 'drop' : 'roster', team: step.team, steps: [step]});
  });
  return stops;
}

/* Each station's place on the floor, in first-arrival order; the last stop's station is the reveal. */
export function stationLayout(steps, mobile = false) {
  const seen = new Map();
  steps.forEach(step => {
    const key = step.station ?? stationKey(step);
    if (!seen.has(key)) seen.set(key, {key, kind: key === 'pit' ? 'pit' : 'roster', team: step.team});
  });
  const entries = [...seen.values()], reveal = steps.at(-1)?.station;
  const shown = entries.filter(entry => entry.key !== reveal), gap = FLOOR.gap[mobile ? 'phone' : 'desk'];
  const middle = (shown.length - 1) / 2, x = index => (index - middle) * gap;
  return entries.map(entry => ({...entry, z: FLOOR.z,
    x: entry.key === reveal ? x(shown.length - 1) + FLOOR.reveal : x(shown.indexOf(entry))}));
}
