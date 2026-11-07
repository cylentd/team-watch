/* Every word Chapter 3 shows (docs/madden-film-chapter3.md, Best pickups, approved 2026-11-05). {tokens} are filled
   from edition.json's pickups block by waivers-data.mjs; team names are the film's short ones (film-copy.mjs team). */
export const WAIVERS_COPY = Object.freeze({
  head: 'Best pickups.',
  // 2026-11-05 (David): 21 words or fewer on waiver-claim. ~~Points over who he’d have started instead~~.
  sub: 'Ranked by points over replacement (PAR).',
  rank: '#{rank}', added: '+{added}', starts: '{starts} starts',
  week: 'W{week}', weekRank: '{pos}{rank}', out: 'out',
  // The card's screen-reader name; never drawn.
  label: 'The league’s three best pickups through Week {through}, by points over the player each team would have started instead.',
  menuClaim: 'Best pickups', menuStarts: 'The top pickup',
});
