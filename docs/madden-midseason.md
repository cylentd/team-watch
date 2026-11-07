# The Madden Curse midseason broadcast

This document covers the Week 8 editorial edition and its original promo integration.
For the accepted Chapter 1 cinematic film, use [the film reference index](madden-film.md).
The promo sequence below is a separate mode, not the current `?film` storyboard or runtime.

Open League > Recap with a Madden Curse team selected, then choose **Watch the special**.
The completed edition combines a 40-second Three.js promo, a league article and the
individual team film room. Nothing posts to the league or an external service.

## The show and the reporting

The Lombardi trophy and Blip open the show. Twelve team avatars then get two seconds
each, with a headline about a player or management decision. All twelve assemble
around the trophy before the final title. The player has pause/resume, replay,
seeking, optional synthesized sound and trophy inspection. It does not loop.

The article follows the same editorial manifest: draft returns, acquisitions,
trades and actual player performances through Week 8. The canonical copy lives in

design/src/content.json. The build exports the standalone edition from those same
paragraphs, so the embedded and standalone reports do not fork.

See [the show implementation notes](madden-trophy-opening.md) for timing, assets,
controls, provenance and lifecycle behavior. The lettering remains a wordmark study;
the original league logo asset is still needed.

## A frozen Week 8 edition

The 2026 special is limited to Yahoo league 75203. It becomes available after seven
complete league-wide rounds and finalizes through Week 8. Later rounds never change
its statistics. Incomplete rounds are excluded for every team.

Week 7 previews retain the earlier data-driven chart player. They do not expose the
Week 8 show or editorial. The finalized edition replaces those charts with the
Three.js show. The November 3 local snapshot contains all six finalized Week 8 games.

Records and individual film-room evidence come from design/midseason.py. Preview
chart frames come from design/midseason_film.py. Player starting-lineup totals and
the show export come from design/midseason_showcase.py. Each weekly player round
must contain all twelve teams exactly once before the exporter accepts it.

## Checks

Run the midseason model, contract, JavaScript, view, playback and showcase tests,
plus the trophy-room and full-show timeline tests. Browser coverage includes
explicit playback, finite completion, pause/resume, seeking, reduced motion,
keyboard inspection, fallback states, responsive titles and navigation cleanup.
Existing frozen goldens are unchanged. No live API is needed for these tests.

The feature is local and uncommitted; it has not been published.
