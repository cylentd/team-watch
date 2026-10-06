# TODO

Tick an item in the commit that finishes it. Newest at the top of each section. Started 2026-10-06; supersedes `~/.claude/plans/team-watch-next.md` (units 1-7, kept there as history).

## Now

- [ ] **Back button assessment.** Back in some places lands somewhere unexpected; the breadcrumb is probably broken. Walk every view, tab, drill-in and overlay at 360px, press Back after each, and log each wrong landing as from / expected / got. History code: `js/chrome/layers.js`, `js/chrome/nav.js`, `js/surface/recap/state.js`, `js/surface/profile/gridlink.js`, `js/data/owner.js`. Done when each wrong landing is fixed and pinned by a test like `test_a_hash_opens_its_view`. (2026-10-06)
- [ ] **Team logo assessment.** Find where a team logo makes a view easier to read; League > Teams is the first candidate. Open question: fantasy team logos (Yahoo/ESPN avatars), NFL club logos, or both. Rank the views yes/no, storyboard the yes ones (STYLE.md), check what ff-jarvis already fetches before adding a source. (2026-10-06)

## Checks on a date

- [ ] Tue 2026-10-06, after the week turn: Preview > Past games shows week 4.
- [ ] Sun 2026-10-11: the Live TD reel matches the day's real touchdowns.
- [ ] Mon 2026-10-12, ~9:15 PM PT: the whole page turns to week 6 after the last final (One page week).
- [ ] On/after 2026-10-21: run the season scorecard trials once (`python -m model.season.season_scorecard --trials` in ff-jarvis) and record them in METHODOLOGY 12.60. Rerun the week-3 recap first: it lacks PHI @ CHI.
- [ ] 2026-11-11: review Start/Sit v3's record.

## Needs an iPhone

- [ ] Recap's Share PNG.
- [ ] Sound on the Roster clips player.
- [ ] Live clock and ESPN play wording, last planned for Mon ATL @ NO (2026-10-05); not confirmed.

## Waiting

- [ ] **Yahoo sign-in.** Blocked on Yahoo approving app `UuR5CedM` (last checked 2026-09-24). Spec: unit 2 in `~/.claude/plans/team-watch-next.md`.
- [ ] **ROS value.** ff-jarvis 12.97 passed its backtest on branch `ros-value`, unlanded; Ranks > Rest of season is storyboarded (2026-10-06).
- [ ] **Chain trades.** Storyboard started 2026-10-05.
- [ ] **Follow a game, part 2.** Part 1 landed 2026-09-28.
- [ ] **Third league.** Menu drill-in landed; the league-ID data work is open.

## Parked

- [ ] **ESPN QR fallback.** Only when a friend cannot use the league-manager setting or the phone bookmark.
