import { FILM_COPY_DETAIL as TUNING } from './constants-playback.mjs';
/* Every word the film shows. {tokens} are filled from edition.json: Chapter 1's from the draft block by
   receipts.mjs, Chapter 2's from the trades block by trades-data.mjs. */
import { WAIVERS_COPY } from './waivers-copy.mjs';
import { LINEUPS_COPY } from './lineups-copy.mjs';
import { POWER_COPY } from './power-copy.mjs';

export const FILM_COPY = Object.freeze({
  ui: {
    play: 'Play the film', replay: 'Replay film',
    ready: 'Ready. Sound is optional.',
    playing: 'Playing.',
    complete: 'Read the stories behind the teams.',
    reduced: 'Reduced motion is on. Each beat is shown as a still. Drag the slider to step through them.',
    seek: 'Film position',
    canvas: 'The league’s draft board, rounds 1 to 10 on cards, with the picks that made the season pulled out one at a time.',
  },
  // The review menu on ?film (film-review.mjs); never in a cut.
  review: {
    label: 'Film beats', scrub: 'Film time', loop: 'Loop this beat',
    keys: 'J back · K next · L loop · Space pause',
    beats: {intro: 'Opening', board: 'Draft board', steal: 'The steal', traded: 'Traded', sleeper: 'The sleeper',
      curse: 'The curse', injury: 'The injury', finale: 'The verdict', trades: 'The trades',
      'waiver-claim': WAIVERS_COPY.menuClaim, 'waiver-starts': WAIVERS_COPY.menuStarts,
      'lineup-defense': LINEUPS_COPY.menuDefense, 'lineup-tightends': LINEUPS_COPY.menuTightends,
      'power-board': POWER_COPY.menuBoard, 'power-close': POWER_COPY.menuClose},
  },
  // Chapter 2 (docs/madden-film-chapter2.md, approved 2026-11-05): the rails and leads carry the trades, so the
  // one headline says what the picture cannot. The partners' records are not shown.
  trades: {
    headline: 'No trades? {team} goes {noTrades}.',
    lead: '+{lead}',
    // The card's screen-reader name; never drawn.
    label: '{team}’s trades, each a rail to the team that leads it through Week {through}, and his record with and without them.',
  },
  chapter: 'CHAPTER 1',
  drafted: 'DRAFTED',
  injuryStatus: 'IR',
  week: {smash: 'Boom', solid: 'Solid', bust: 'Bust', out: 'Out'},
  headline: {
    board: 'Draft spot vs. reality.',
    steal: 'An eighth-round bargain.',
    traded: 'New team. Same disappointment.',
    sleeper: 'Eighth-round rock.',
    curse: 'The Godwin Curse',
    injury: 'Season cut short.',
    finale: 'Romo’s value ran deep.',
  },
  // The card already names the player (docs/madden-film-rules.md), so no subline repeats him.
  // A smash is a top-12 RB or WR week (Rule A).
  sub: {
    board: 'Bargains, misses, bad luck.',
    steal: '{smashWord} top-12 weeks. No busts.',
    traded: '{startsWord} starts. No top-36 finishes.',
    sleeper: 'Top-12 back in {smash} of {games}.',
    curse: 'COOKed tempted fate.',
    injury: '{games} games from a second-rounder.',   // ch17 (coordinator): numerals, rule 25; ~~{gamesWord} games, a second-rounder.~~ (rev 16)
    // The five rows and the class total carry the finale, so it has no subline (David, 2026-11-04).
    finale: '',
  },
  // The part of a headline or subtitle that waits for its beat's stamp or flip (constants.mjs `stat`).
  stat: {sleeper: 'Top-12 back in {smash} of {games}.'},
  // Beside the scene only the numbers the picture cannot show: Golden's two ranks, Romo's rows and
  // total (rules 19 and 20). Captions, keys and method lines are cut.
  detail: {arrow: '→', total: 'Draft class', next: 'Next best:'},
  // A stop on the waiver floor: the team's avatar and name beside one big word.
  waiverOwner: 'FREE AGENT',
  station: {roster: 'ROSTER', pit: 'WAIVER'},
  team: {1: 'Romo', 2: 'COOKed', [TUNING.warrentyTeamId]: 'WARREN-TY', [TUNING.boboTeamId]: 'Bo-Bo', [TUNING.gibbsTeamId]: 'Gibbs', [TUNING.auraTeamId]: 'Aura',
    [TUNING.honeyTeamId]: 'Honey', [TUNING.burrowedTeamId]: 'Burrowed', [TUNING.chatTeamId]: 'Chat', [TUNING.jaxonTeamId]: 'Jaxon', [TUNING.lamarleyTeamId]: 'Lamarley', [TUNING.sausageTeamId]: 'Sausage'},
  numbers: ['Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine'],
  suffixes: ['Jr.', 'Sr.', 'II', 'III', 'IV'],
});
