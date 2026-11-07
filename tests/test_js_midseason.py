"""The broadcast is a pure view over one edition, with names escaped and bounded navigation."""
import pytest


@pytest.fixture(scope="module")
def desk(node_js):
    return node_js("data/constants-midseason.js", "data/midseason.js", "data/midseason-film.js", "surface/midseason/view.js", "surface/midseason/news.js")


@pytest.fixture
def league():
    week = {"week": 1, "points": 100, "against": 90, "opponent": 2, "result": "W"}
    team = {"id": 1, "w": 7, "l": 0, "t": 0, "pf": 700, "pa": 630, "average": 100,
            "standing": 2, "scoring_rank": 2, "against_rank": 2, "allplay": [14, 7, 0],
            "angle": "contender", "best": week, "closest_win": week, "weeks": [week]}
    return {"league": "The Madden Curse", "teams": [{"id": 1, "name": "<script>Romo</script>", "avatar": ""},
            {"id": 2, "name": "Opponent & Co", "avatar": ""}],
            "midseason": {"season": 2026, "through": 7, "target": 8, "final": False,
                          "generated": "2026-11-02T05:51", "max_score": 120,
                          "teams": [team, {**team, "id": 2}]}}


def test_the_recap_entry_is_only_present_with_an_edition(desk, league):
    assert "data-msopen" in desk("msEntryHTML", league)
    assert desk("msEntryHTML", {"league": "AYO", "teams": []}) == ""


def test_each_team_gets_roast_hype_and_matchup_receipts(desk, league):
    html = desk("msPageHTML", league, league["midseason"], 1)
    assert "data-msstage" in html and "data-msreceipts" in html
    assert "data-msroast" in html and "data-mshype" in html
    assert "100.00" in html and "Opponent &amp; Co" in html


def test_team_names_are_escaped_in_every_rendered_context(desk, league):
    html = desk("msPageHTML", league, league["midseason"], 1)
    assert "<script>Romo</script>" not in html
    assert "&lt;script&gt;Romo&lt;/script&gt;" in html


def test_preview_and_final_cutoffs_are_visible(desk, league):
    html = desk("msPageHTML", league, league["midseason"], 1)
    assert "Through Week 7" in html and "Week 8" in html
    league["midseason"].update(through=8, final=True)
    assert "finalizing" not in desk("msPageHTML", league, league["midseason"], 1).lower()


def test_next_previous_never_leave_the_team_list(desk, league):
    edition = league["midseason"]
    assert desk("msStep", edition, 1, -1) == 1
    assert desk("msStep", edition, 1, 1) == 2
    assert desk("msStep", edition, 2, 1) == 2


def test_a_missing_team_falls_back_to_a_real_spotlight(desk, league):
    html = desk("msPageHTML", league, league["midseason"], 999)
    assert "data-msstage" in html and "&lt;script&gt;Romo&lt;/script&gt;" in html


def test_the_score_chart_has_a_text_alternative(desk, league):
    html = desk("msPageHTML", league, league["midseason"], 1)
    assert 'role="img"' in html and "aria-label=" in html
    assert "Week 1" in html and "100.00" in html


def test_the_hype_uses_real_numbers_instead_of_unfilled_placeholders(desk, league):
    words = desk("msWords", league["midseason"]["teams"][0])
    assert "100.00-point" in words[2] and "Week 1" in words[2]
    assert "{" not in " ".join(words)
