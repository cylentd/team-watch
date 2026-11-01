"""S4: a public view shows no roster or personal advice, to anyone (VISION.md, Not doing; Decisions 2026-10-04).

Oracles, both from the scenario and not from the code:
- a stranger's public view names no fantasy team;
- the league-wide views draw the same words for a stranger and for the reader holding the most personal state.
"""
import pytest

from component import mount  # noqa: F401  (mount is the fixture)
from pages.public_views import STRANGER, PublicView
from test_smoke_views import one_context_at_a_time  # noqa: F401  (a fixture)

# Views of the five groups that hold no team of the reader's: Team, Live and League's team pages are the
# reader's own, by design (DESIGN.md "What David has ruled on").
PUBLIC = ("digest", "weather", "preview", "weekrecap", "news", "ranks", "board", "movers", "usage", "schedule")
# DESIGN.md calls these "league-wide and public: reads no roster". Ranks and the bets tag the reader's own
# players, which is allowed once a reader has picked a team.
LEAGUE_WIDE = ("digest", "weather", "preview", "weekrecap")


@pytest.mark.parametrize("surface", PUBLIC)
def test_a_strangers_public_view_names_no_fantasy_team(mount, one_context_at_a_time, surface):
    page, errors = mount(surface, init=(STRANGER,))
    view = PublicView(page)
    assert view.reader_state() == [None, [], False], "the stranger holds no team, no follow, no owner mark"
    names, text = view.fantasy_team_names(), view.text().casefold()
    assert len(names) > 1, "the fixture has David's team and leaguemates to look for"
    assert [n for n in names if n.casefold() in text] == []
    assert errors == []


@pytest.mark.parametrize("surface", LEAGUE_WIDE)
def test_a_league_wide_view_reads_the_same_with_a_team_picked(mount, one_context_at_a_time, surface):
    page, errors = mount(surface, init=(STRANGER,))
    view = PublicView(page)
    stranger = view.text()
    view.as_signed_in_reader()
    assert view.reader_state()[2] is True, "the second reader carries the owner mark"
    assert view.text() == stranger
    assert errors == []
