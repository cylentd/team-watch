# Madden Curse film: Chapter 2 storyboard (approved 2026-11-05)

David approved this storyboard on 2026-11-05. Chapter 2 is a short trade tracker, not a story
chapter: where Aura's three September trades stand through Week 8, and his record without them.
Rules: [film rules](madden-film-rules.md). Index: [start here](madden-film.md).

## Shot (6 s, film 44.077 to 50.077)

Approved at 4 s; David then said to lengthen it if it feels rushed (2026-11-05). The 4 s cut left
1.9 s to read a 6-word headline after glancing at three leads, under the craft reference's
2.5 s planning figure, so it starts at 6 s: the same shot with one more bar of reading hold.
Timing lives in `timing.json`; the animatic decides whether 6 s is right.

| Film time | Camera | Action | Copy |
|---|---|---|---|
| 44.077 to 45.3 | Whip off Romo's board, then a slow push | Aura's avatar sits large on the left; three rails fan out to the three partners; each light runs to its Week 8 spot | none |
| 45.3 | Push continues | The leads appear where the lights stop | +17.9, +63.7, +4.5 |
| 46.077 | Push eases to a stop | Hit: 3-5 stamps under Aura's avatar | **No trades? Aura goes 5-3.** beside the avatar |
| 46.3 to 50.0 | Held, light drifting along the rails | Reading hold | same |
| 50.077 | Whip out to Chapter 3 (added when Chapter 3 exists) | | |

- Desktop: Aura left, partners right, headline beside Aura's avatar.
- Phone: Aura at the bottom, rails fanning upward, headline directly above the avatar.
- Partners' records are not shown (David agreed 2026-11-05: two do not change, team 3's rests on a 0.1-point game).
- The TEAM WATCH tag leaves Chapter 1's finale and returns on the last chapter's final frame (David, 2026-11-05). The opening tag is unchanged.
- Lengths change on bar lines (2 s). 50.077 is a bar line but mid-phrase; the phrase seams are 48.077 and 56.077.

## Music

From film 41 to 54 the track is a steady light 120 BPM groove: soft kicks on the bar lines, no big hits.
Film 54 to 56 lifts, likely the end of a 4-bar phrase (40.077, 48.077, 56.077). 48.077 is the seam where
Chapter 3 starts. The track stops at full level at film 66 with no fade, so later chapters need more music.
Source: an energy and flux profile of `ascent-to-the-podium.mp3`, 2026-11-05; phrase length is a judgment.

## Facts

| Trade (date) | Aura sent | Aura got | Partner | Lead through W8 |
|---|---|---|---|---|
| Sep 15 | J. Chase | S. Diggs, P. Washington | team 3 | team 3 +17.9 |
| Sep 16 | G. Kittle, M. Nabers | D. Samuel, L. McConkey | Sausage | Sausage +63.7 |
| Sep 18 | B. Bowers, T. Lawrence, P. Washington | D. Maye, A.J. Brown, I. Likely, Rams D/ST | Gibbs | Gibbs +4.5 |

- Leads: ff-jarvis `model/season/trade_verdicts.py` `verdicts()` (the Trade history page's PAR), recomputed at the Week 8 cutoff. The saved `yahoo_trade_verdicts.json` (2026-09-28) is stale.
- No-trade record, 3-5 actual, 5-3 without trades: every trade undone from Week 2. Each team keeps its other real starters, bench and waiver moves. A traded-in starter's slot goes to the best eligible player left by Yahoo's own projection that week. A player the team traded away replaces a starter when Yahoo projected him higher. A defense slot with no defense left gets the team's Week 1 defense, scored from `gamelog_kdst.json` `dst_yahoo`. Opponents are rebuilt the same way. Every recomputed actual score matches `yahoo_league.json`.
- Aura's flips: Week 2 vs Jaxon (131.7 to 114.2) and Week 7 vs Something Burrowed (104.8 to 94.3). Without the Patriots stand-in, Week 2 stays a loss (4-4).
