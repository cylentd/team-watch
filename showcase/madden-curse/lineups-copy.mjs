export const LINEUPS_COPY = Object.freeze({
  label: 'Start/sit regrets, through Week 8',
  defenseManager: 'Gibbs',
  menuDefense: 'Gibbs: the defense experiment',
  menuTightends: 'Lamarley: the tight-end switch',
  // 2026-11-05 (ch4 corrective, David: "you have to have some text to describe what's going on"): the two titles
  // are back as chyrons over each station. ~~Cut, the desk's nameplates carry them~~ (ch4 cinematic, same day).
  defense: 'The defense experiment.',
  defenseCard: {started: 'STARTED · WEEK {week}', points: '{score} PTS',
    logos: {Saints: './assets/saints.webp', Raiders: './assets/raiders.webp'}},
  tightends: 'Lamarley: the tight-end switch.',
  defenseWin: 'Still won.',
  defenseLoss: 'Lost by {margin}.',
  defenseNext: '',
  win: 'WIN',
  // ~~'The points stayed on the bench.'~~, one word fits the 1.6 s bar (rules 38, 39).
  payoff: 'Again.',
  outcomeBoth: 'Won both weeks.',
  outcomeOne: 'Won 1 negative week.',
  outcomeNone: 'No negative-week wins.',
  starter: 'START', bench: 'BENCH', socket: 'DEF',
  week: 'W{week}',
  players: {
    'Harold Fannin Jr.': {name: 'H. Fannin Jr.', portrait: '../../heads/xl/harold-fannin.webp'},
    'Hunter Henry': {name: 'H. Henry', portrait: '../../heads/xl/hunter-henry.webp'},
  },
});
