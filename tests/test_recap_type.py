"""League > Recap's League section reads in one voice per line (STYLE.md "Type", 2026-10-06: "something makes it not
easily readable"; every text passed contrast, but a score line changed face five times). Each test mounts Recap alone
(tests/component.py) and reads it through tests/pages/league_recap.py."""
import pytest

from component import mount  # noqa: E402,F401  (the fixture)
from pages.league_recap import LeagueRecapPage  # noqa: E402


@pytest.mark.parametrize("size", [(360, 800), (1440, 900)], ids=["phone", "desktop"])
def test_recap_names_and_scores_stay_in_one_face_and_stamps_are_big_enough_to_read(mount, size):
    page, errors = mount("recap", size=size)
    r = LeagueRecapPage(page)
    names, body = r.name_faces(), r.body_face()
    assert names and all(f == body for f in names), "every name in the body face, a tagged team's too"
    sides = r.score_sides()
    assert sides and all(sides), "a score takes its name's face, digits fixed-width"
    # The stamps stay stamps (David, 2026-10-06, "I liked the stamps"): caps in the headline's face, at 13.5px or
    # more (12px was the hardest text on the page), the team's name outside them.
    stamps, display = r.stamps(), r.headline_face()
    assert stamps and all(s["case"] == "uppercase" and s["face"] == display and s["px"] >= 13.5 for s in stamps), stamps
    assert errors == []


@pytest.mark.parametrize("game_stamp", [True, False], ids=["with-nail-biter", "without"])
@pytest.mark.parametrize("size", [(360, 800), (1160, 900), (1440, 900)], ids=["phone", "narrow-desktop", "desktop"])
def test_each_card_team_row_holds_its_name_score_and_stamps_on_one_line(mount, size, game_stamp):
    # David, 2026-10-06 at 1160px: "Chanel 146.98 [TOP DOG] beat" ended a line and the loser wrapped under it. The
    # fixture's one card has a Nail-biter, which filled the grid's last column and hid a card without one (the
    # loser's name auto-placed there), so both are laid out.
    page, errors = mount("recap", size=size)
    r = LeagueRecapPage(page)
    if not game_stamp:
        r.drop_game_stamps()
    cards = r.card_rows()
    assert cards and all(len(c) == 2 for c in cards), "two rows a card"
    off_line = [card for card in cards for name, score, *stamps in card
                if not (abs(name - score) <= 4 and all(name - 6 <= s <= name + 30 for s in stamps))]
    assert off_line == []
    assert errors == []


@pytest.mark.parametrize("size", [(360, 800), (1160, 900)], ids=["phone", "narrow-desktop"])
def test_no_two_stamps_on_a_card_overlap(mount, size):
    # 2026-10-06: with the winner's avatar taking a column, Jon's DUMPSTER FIRE ran into the NAIL-BITER on a phone.
    page, errors = mount("recap", size=size)
    # every card as week 4's Phillip-Jon was: a long name, a team stamp on each row, and the game's Nail-biter
    page.evaluate("""() => document.querySelectorAll('.lg-league .lg-row .bp2-sb').forEach(sb => {
        sb.querySelectorAll('.bp2-sr > b').forEach(b => { b.textContent = 'Crystal W.'; });
        sb.querySelectorAll('.bp2-st').forEach(st => st.insertAdjacentHTML('beforeend', '<span class="lg-stamp r">Dumpster fire</span>'));
        if (!sb.querySelector('.bp2-sgame')) sb.insertAdjacentHTML('beforeend', '<span class="bp2-sgame"><span class="lg-stamp x">Nail-biter</span></span>'); })""")
    assert LeagueRecapPage(page).overlapping_stamps() == []
    assert errors == []


def test_the_bottom_row_sections_end_within_150px_of_each_other(mount):
    # STYLE.md "Rows, not columns": Luck so far ran ~200px past the standings (2026-10-06). All 12 teams stay
    # (David: dropping the middle six "might be confusing"); the rows tighten instead. The fixture's league is
    # smaller than twelve and has no grudge, so here this guards; the 12-team page was measured at land.
    page, errors = mount("recap", size=(1440, 900))
    ends = LeagueRecapPage(page).bottom_row_ends()
    assert len(ends) >= 2 and max(ends) - min(ends) <= 150, ends
    assert errors == []


@pytest.mark.parametrize("size", [(360, 800), (1440, 900)], ids=["phone", "desktop"])
def test_every_standings_record_in_a_column_ends_on_one_edge(mount, size):
    # A team with no streak dropped its streak cell on a phone, and its record slid right (2026-10-06).
    page, errors = mount("recap", size=size)
    assert len(LeagueRecapPage(page).record_edges()) == 2, "one edge per column, two columns"
    assert errors == []
