"""Malformed broadcast data must fail at injection, rather than in a reader's browser."""
from midseason_contract import problems_league


def test_an_absent_edition_is_allowed():
    assert problems_league({"league": "AYO"}) == []


def test_a_present_edition_cannot_omit_its_cutoff():
    problems = problems_league({"midseason": {"teams": []}})
    assert "midseason.through" in problems


def test_a_team_requires_the_original_best_week_score():
    problems = problems_league({"midseason": {"teams": [{"best": {"week": 1}}]}})
    assert "midseason.teams[0].best.points" in problems
