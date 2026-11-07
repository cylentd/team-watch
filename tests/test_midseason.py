"""The special uses one complete cutoff, never live scores or current standings."""
import copy

import pytest

from midseason import midseason_special


def round_games(week):
    return [{"week": week, "home": home, "away": away, "hp": hp, "ap": ap,
             "winner": "home", "tier": None}
            for home, away, hp, ap in [(1, 2, 100.0, 90.0), (3, 4, 120.0, 80.0)]]


@pytest.fixture
def season():
    return {"league_id": "75203", "league": "The Madden Curse", "season": 2026,
            "generated": "2026-11-02T05:51", "week": 8,
            "teams": {str(team): {"name": f"Team {team}", "w": 99, "l": 99} for team in range(1, 5)},
            "games": [game for week in range(1, 8) for game in round_games(week)]}


def test_complete_weeks_drive_records_not_live_standings(season):
    result = midseason_special(season)
    assert result is not None
    assert (result["through"], result["final"]) == (7, False)
    team = next(team for team in result["teams"] if team["id"] == 1)
    assert (team["w"], team["l"], team["t"], team["pf"], team["pa"]) == (7, 0, 0, 700.0, 630.0)
    assert (team["standing"], team["scoring_rank"], team["allplay"]) == (2, 2, [14, 7, 0])


def test_news_desk_headlines_use_the_same_finalized_window(season):
    season["games"] += round_games(8)[:1]
    overview = midseason_special(season)["overview"]
    assert overview == {"leader": 3, "scorer": 3, "points": 2730.0, "games": 14,
                        "peak": {"id": 3, "week": 1, "points": 120.0}}


def test_film_frames_keep_one_score_scale_and_actual_week_order(season):
    film = midseason_special(season)["film"]
    assert film["leaders"] == [3, 1] and film["crowd"] == 2
    assert film["max_total"] == 840.0
    assert [frame["week"] for frame in film["frames"]] == list(range(1, 8))
    assert film["frames"][0]["teams"][0] == {"id": 3, "total": 120.0, "place": 0, "share": 120.0 / 840.0}
    assert film["frames"][-1]["teams"][0] == {"id": 3, "total": 840.0, "place": 0, "share": 1.0}


def test_the_form_story_compares_the_last_two_completed_weeks(season):
    season["games"][-4]["hp"] = 150.0
    season["games"][-2]["hp"] = 150.0
    season["games"] += round_games(8)[:1]
    surge = midseason_special(season)["film"]["surge"]
    assert surge == {"id": 1, "baseline": 100.0, "recent": 150.0, "change": 50.0,
                     "baseline_weeks": 5, "recent_weeks": 2, "wins": 2, "losses": 0, "ties": 0}


def test_partial_week_is_excluded_for_every_team(season):
    season["games"] += round_games(8)[:1]
    result = midseason_special(season)
    assert result is not None
    assert result["through"] == 7
    assert all(len(team["weeks"]) == 7 for team in result["teams"])


def test_final_edition_freezes_at_week_eight(season):
    season["games"] += round_games(8) + round_games(9)
    result = midseason_special(season)
    assert result is not None
    assert (result["through"], result["final"]) == (8, True)
    assert next(team for team in result["teams"] if team["id"] == 3)["pf"] == 960.0


def test_a_gap_does_not_mix_different_week_windows(season):
    season["games"] += round_games(8)[:1] + round_games(9)
    assert midseason_special(season)["through"] == 7


def test_ties_count_in_matchup_and_all_play_records(season):
    season["games"][0].update(ap=100.0, winner="tie")
    result = midseason_special(season)
    assert result is not None
    team = next(team for team in result["teams"] if team["id"] == 1)
    assert (team["w"], team["l"], team["t"]) == (6, 0, 1)
    assert team["allplay"] == [13, 7, 1]


@pytest.mark.parametrize("score", [None, True, float("nan"), float("inf"), -1])
def test_missing_or_invalid_final_scores_do_not_become_zero(season, score):
    season["games"][0]["hp"] = score
    assert midseason_special(season) is None


def test_only_the_madden_curse_gets_the_special(season):
    season["league_id"] = "other"
    assert midseason_special(season) is None


def test_the_early_season_has_no_midseason_entry(season):
    season["games"] = round_games(1)
    assert midseason_special(season) is None


def test_next_season_does_not_reuse_this_years_team_scripts(season):
    season["season"] = 2027
    assert midseason_special(season) is None


def test_duplicate_games_do_not_pass_as_a_complete_round(season):
    season["games"].append(copy.deepcopy(season["games"][0]))
    assert midseason_special(season) is None


def test_the_story_carries_the_original_matchup_receipt(season):
    result = midseason_special(season)
    assert result is not None
    team = next(team for team in result["teams"] if team["id"] == 1)
    assert team["best"] == {"week": 1, "points": 100.0, "opponent": 2, "against": 90.0, "result": "W"}
    assert team["closest_win"] == team["best"]


def test_building_the_edition_leaves_its_input_alone(season):
    before = copy.deepcopy(season)
    midseason_special(season)
    assert season == before
