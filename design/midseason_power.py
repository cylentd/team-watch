"""Chapter 5 of the midseason film, Midseason power rankings: every team's weekly score against the other
eleven (all-play), ranked beside the real standings (docs/madden-film-chapter5.md).

Method (David, 2026-11-05), Yahoo league 75203, Weeks 1-8:
- Each week every team's score faces the other 11 scores: a win is 1, a tie 0.5, a loss 0. All-play w/l/t are
  integers (a tie is a `t`, never half a win), so w + l + t is 11 a week and 88 over eight weeks.
- Power place = all-play wins plus half the ties, then points scored. The points tie-break is named in the
  block (`order`, `tieBreak`), because three teams share 55-33 and points decide their order.
- Standing place = the real record (wins plus half the ties), then points.
- Luck = real wins (ties half) minus the share the points earned, per week the beaten scores over 11, the
  method of league_back.add_standings, rounded to one decimal.
Points are summed from the games; a team's season total in the file can differ, and the games are the oracle.
"""
from constants_midseason import ALL_PLAY_TIE_CREDIT

import json
from pathlib import Path

from midseason_trades import LEAGUE_ID, THROUGH

TEAMS = 12                  # the league's size; a week with fewer scoring teams is refused
TENTHS = 1
CENTS = 2
ORDER = 'all-play wins, then points scored'
TIE_BREAK = 'points'
OUT = Path(__file__).resolve().parents[1] / 'showcase' / 'madden-curse' / 'power-receipts.json'
WIN, TIE, LOSS = 'w', 't', 'l'


def check_league(season):
    if str(season.get('league_id')) != str(LEAGUE_ID):     # the file keeps it as text
        raise ValueError(f'Power rankings are for league {LEAGUE_ID}, not {season.get("league_id")}')


def _week_scores(games, week, teams):
    """{team id: score} for one week, refusing a gap, a repeat or a score that is not a number."""
    scores = {}
    for g in games:
        if g['week'] != week:
            continue
        for team, score in ((int(g['home']), g['hp']), (int(g['away']), g['ap'])):
            if isinstance(score, bool) or not isinstance(score, (int, float)):
                raise ValueError(f'Week {week} team {team}: score {score!r} is not a number')
            if team in scores:
                raise ValueError(f'Week {week}: team {team} appears twice')
            scores[team] = score
    if not scores:
        raise ValueError(f'Week {week} has no games')
    if len(scores) != teams:
        raise ValueError(f'Week {week} has {len(scores)} teams scoring, not {teams} teams')
    return scores


def _all_play(scores, tally):
    for team, score in scores.items():
        for other, theirs in scores.items():
            if other != team:
                tally[team][WIN if score > theirs else TIE if score == theirs else LOSS] += 1


def _week_earned(scores):
    return {team: sum(1 if score > o else ALL_PLAY_TIE_CREDIT if score == o else 0 for t, o in scores.items() if t != team)
            / (len(scores) - 1) for team, score in scores.items()}


def _record(games, through):
    out = {}
    for g in games:
        if g['week'] > through:
            continue
        outcome = {'home': (WIN, LOSS), 'away': (LOSS, WIN)}.get(g['winner'], (TIE, TIE))
        for team, kind in ((int(g['home']), outcome[0]), (int(g['away']), outcome[1])):
            out.setdefault(team, {WIN: 0, LOSS: 0, TIE: 0})[kind] += 1
    return out


def _share(counts):
    return counts[WIN] + counts[TIE] / 2


def power_block(season, through=THROUGH, teams=TEAMS):
    check_league(season)
    games = [g for g in season['games'] if g['week'] <= through]
    allplay = {int(i): {WIN: 0, LOSS: 0, TIE: 0} for i in season['teams']}
    earned = {team: 0.0 for team in allplay}
    points = {team: 0.0 for team in allplay}
    for week in range(1, through + 1):
        scores = _week_scores(games, week, teams)
        _all_play(scores, allplay)
        for team, share in _week_earned(scores).items():
            earned[team] += share
            points[team] += scores[team]
    record = _record(games, through)
    points = {team: round(total, CENTS) for team, total in points.items()}
    standing = sorted(allplay, key=lambda t: (-_share(record[t]), -points[t]))
    power = sorted(allplay, key=lambda t: (-_share(allplay[t]), -points[t]))
    rows = [{'id': team, 'name': season['teams'][str(team)]['name'], 'power': place,
             'standing': standing.index(team) + 1, 'record': record[team], 'allPlay': allplay[team],
             'points': points[team], 'luck': round(_share(record[team]) - earned[team], TENTHS) + 0.0}
            for place, team in enumerate(power, 1)]
    return {'season': int(season['season']), 'league': LEAGUE_ID, 'through': through,
            'comparisons': through * (teams - 1), 'order': ORDER, 'tieBreak': TIE_BREAK, 'teams': rows}


def load_power(data):
    """The chapter's block from ff-jarvis's league file, or None when it is missing."""
    path = Path(data) / 'yahoo_league.json'
    if not path.exists():
        return None
    return power_block(json.loads(path.read_text(encoding='utf-8')))


def main():
    block = load_power(Path.home() / '.ff-jarvis-history' / 'data')
    if block is None:
        raise SystemExit('no yahoo_league.json')
    OUT.write_text(json.dumps(block, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'wrote {OUT.name}: {len(block["teams"])} teams, {block["comparisons"]} comparisons each')


if __name__ == '__main__':
    main()
