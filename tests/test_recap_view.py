"""This week > Recap (leaf `weekrecap`, 2026-10-05, storyboard option C,
https://claude.ai/artifact/HVdkEL4YbiBKUJ3QbLH9gf): the banner, a Players / Scores / Claude bar, one tab's
cards. Browser tests on the week 4 recap fixture (tests/fixtures/data/recap/2026-w04.json): 8 of 16 games
final, Claude 5 of 8 on winners. The data cut is tests/test_recap_data.py's; this proves the page.
The view's tests mount Recap alone (tests/component.py) and read it through tests/pages/recap.py; the two
that cross views (the Digest after Recap's story, the nav's sub-row) are journeys on the full page."""
import json
import re

import pytest

from component import Mounter, mount  # noqa: F401  (the fixture)
from pages.digest import DigestPage
from pages.recap import RecapNav, RecapPage
from test_render import drive, go, open_page
from wording import words

pytestmark = pytest.mark.render

PHONE, DESK = (360, 800), (1100, 900)


def with_recap(fragment, mutate):
    """The built page's data with LIVE_RECAP replaced by mutate(block); mutate returns the new value, None
    for the empty state. LIVE_RECAP is a const, so the data is rewritten, not patched at runtime. No accuracy
    file: its tab (test_accuracy_view.py) is hidden, so these variants test the recap's own tabs."""
    m = re.search(r"const LIVE_RECAP = (.*?);\n", fragment)
    new = json.dumps(mutate(json.loads(m.group(1))))
    fragment = re.sub(r"const LIVE_ACCURACY = .*?;\n", "const LIVE_ACCURACY = null;\n", fragment, count=1)
    m = re.search(r"const LIVE_RECAP = (.*?);\n", fragment)
    return fragment[:m.start()] + f"const LIVE_RECAP = {new};\n" + fragment[m.end():]


@pytest.fixture(scope="module")
def planted(mount, built, tmp_path_factory):
    """`planted(name, mutate)` mounts Recap on data changed by mutate: (page, errors). One page per name.
    It builds on `mount` (same browser, same page), so a test that asks for it is a component test."""
    made = {}

    def mount_with(name, mutate):
        if name not in made:
            made[name] = Mounter(mount.browser, tmp_path_factory.getbasetemp() / f"component-recap-{name}",
                                 with_recap(built.fragment, mutate))
        return made[name]("weekrecap")
    yield mount_with
    for m in made.values():
        m.pages.close()


def on_tab(page, tab):
    rc = RecapPage(page)
    rc.pick_tab(tab)
    assert rc.body_tab() == tab
    return rc


def test_three_tabs_open_on_players_and_the_choice_is_kept(mount):
    page, errors = mount("weekrecap")
    rc = RecapPage(page)
    assert rc.tabs() == ["Players", "Scores", "Claude", "Accuracy"]
    assert rc.pressed_tab() == "players"
    assert rc.sections()["leaders"] == 1 and rc.sections()["games"] == 0
    rc.pick_tab("scores")
    assert rc.sections()["games"] == 1 and rc.sections()["leaders"] == 0
    assert rc.pressed_tab() == "scores"
    # the banner and the bar hold still: a tab repaints the body, not the view
    assert rc.body_tab() == "scores"
    assert rc.stored_tab() == "scores"
    rc.reload()
    assert rc.pressed_tab() == "scores"
    rc.pick_tab("claude")
    assert rc.sections()["claude"] == 1
    assert errors == []


def test_the_banner_calls_the_top_scorer_by_yards_and_touchdowns_never_points(mount):
    page, errors = mount("weekrecap")
    rc = RecapPage(page)
    head = rc.headline()
    assert re.search(r"Allen .*285 yards and 4 TDs", head), head
    assert "point" not in head.lower() and "pts" not in head.lower()
    assert rc.lead_when().upper() == "WEEK 4 · TOP SCORE SO FAR"     # 8 of 16 final: so far
    pills = rc.lead_pills()
    assert len(pills) >= 2                                          # the box line under it: passing, rushing
    assert not any("pts" in p for p in pills)                       # no fantasy points in the pills either
    rc.tap_lead()
    assert errors == []


@pytest.mark.journey
def test_claudes_story_about_the_top_scorer_is_the_banner_and_the_digest_leaves_it(browser, page_file):
    """David, 2026-10-05: the Digest and Recap banners never carry the same content. A result story about the
    Recap's top scorer is Recap's (escaped, in place of the template); the Digest leads with something else."""
    ctx, page, errors = open_page(browser, page_file, PHONE)
    rc = RecapPage(page)
    rc.plant_story()
    drive(page, go("weekrecap"))
    assert rc.headline() == "Allen torches the Bills for 285 yards <3"
    assert rc.lead_fact() == "Josh Allen threw four scores."
    assert rc.lead_pills() == []
    drive(page, go("digest"))
    dg = DigestPage(page)
    assert "torches" not in dg.headline()
    assert dg.headline().strip() != ""
    ctx.close()
    assert errors == []


def test_players_leaders_lists_and_touchdowns(mount):
    page, errors = mount("weekrecap")
    rc = RecapPage(page)
    assert rc.pos_heads() == ["QB", "RB", "WR", "TE", "K", "DST"]
    assert all(n == 3 for n in rc.leader_counts())
    # a kicker's day is his box line; a defense has no page to open
    assert "FG" in rc.first_day("K")
    assert rc.openable("DST") == 0
    # the three lists, one open on a phone
    assert [re.sub(r"\s+\d+$", "", s) for s in rc.list_tab_labels()] == ["Smashed", "Busts", "Left hurt"]
    assert len(rc.open_panels()) == 1
    assert rc.open_panels() == ["smashed"]
    rc.pick_list("left")
    assert rc.open_panels() == ["left"]
    assert "Concussion" in rc.panel_text("left")
    # touchdowns: top five, then Show all; a dot per rushing, receiving or return score
    assert rc.touchdown_rows() == 5
    rc.toggle_touchdowns()
    assert rc.touchdown_rows() == 19 and rc.touchdown_more() == "Show fewer"
    dots = rc.touchdown_dots()
    assert dots == sorted(dots, reverse=True) and min(dots) >= 1
    assert rc.touchdown_note().startswith("Most passing TDs: J. Allen, D. Prescott, A. Rodgers, 3 each")
    assert rc.sideways() <= 0
    rc.open_first_touchdown()
    assert errors == []


def test_desktop_lays_the_three_lists_open_side_by_side(mount):
    page, errors = mount("weekrecap", size=DESK)
    rc = RecapPage(page)
    assert rc.list_tabs_hidden()
    panels = rc.panels()
    assert panels["count"] == 3 and panels["shown"]
    assert len(set(panels["tops"])) == 1, panels["tops"]
    xs = panels["lefts"]
    assert xs == sorted(xs) and len(set(xs)) == 3
    assert rc.list_head_visible()
    # the leaders sit three across, and nothing's label sits more than 560px from its value
    assert rc.leader_columns() == 3
    assert rc.labels_far_from_values(560) == 0
    assert rc.sideways() <= 0
    assert errors == []


def test_scores_group_by_window_with_the_pick_and_its_grade(mount):
    page, errors = mount("weekrecap")
    rc = on_tab(page, "scores")
    heads = rc.window_names()
    assert [h.upper() for h in heads] == ["THURSDAY NIGHT", "SUNDAY MORNING", "SUNDAY EARLY", "SUNDAY LATE", "SUNDAY NIGHT", "MONDAY NIGHT"]
    assert rc.first_window_times() == "5:15 PM"
    assert rc.game_count() == 16
    assert rc.marks()["hit"] == 5 and rc.marks()["miss"] == 3     # Claude 5 of 8 on winners
    assert re.fullmatch(r"Claude picked 5 of 8 winners · 5–3 vs spread", rc.strip())
    # a final's winner is bold; a game still to play shows its kickoff in the reader's clock and the pick
    assert rc.winner_of("PIT 24") == "CLE 27"
    assert rc.pick_of("ATL") == "5:15 PM · Picked ATL"
    assert rc.marks_in("ATL") == 0
    assert rc.sideways() <= 0
    assert errors == []


def test_a_game_opens_previews_dossier_only_when_preview_holds_the_same_week(mount):
    page, errors = mount("weekrecap")
    rc = on_tab(page, "scores")
    assert rc.game_buttons() == 0           # the fixture's Preview is week 2
    # Preview holds the recap's week, but the page week is still 2: Preview shows nothing, so no button.
    rc.plant_preview_week()
    assert rc.game_buttons() == 0
    # Both on the recap's week (the page has not turned past it): the games open their dossiers.
    rc.plant_page_week()
    assert rc.game_buttons() >= 1
    rc.open_game("PIT 24")
    assert rc.surface() == "preview" and rc.opened_preview_game() == "PITCLE"
    assert errors == []


def test_claude_tab_tiles_calls_and_the_every_week_link(mount):
    page, errors = mount("weekrecap")
    rc = on_tab(page, "claude")
    assert rc.tile_values() == ["5–3", "5–3", "6–2"]
    assert rc.tile_labels() == ["Winners", "Vs spread", "Over/under"]
    # best: a winner picked against the market (CLE at home getting 2.5); worst: the surest miss
    best, worst = rc.call(0), rc.call(1)
    assert "BEST CALL" in best.upper() and "CLE over PIT, 27–24" in best
    assert words("weekrecap.claude.bestDog") in best
    assert "WORST CALL" in worst.upper() and "JAX at 57% to win" in worst and "CIN won 27–14" in worst
    rc.open_every_week()
    assert rc.surface() == "preview" and rc.preview_record_open() is True
    assert errors == []


def test_no_recap_file_says_so_in_one_line(planted):
    page, errors = planted("none", lambda d: None)
    rc = RecapPage(page)
    assert rc.empty_title() == words("weekrecap.empty.title")
    assert rc.tab_count() == 0 and rc.cards() == 0
    assert rc.sideways() <= 0
    assert errors == []


def test_a_section_without_data_hides_and_one_tab_left_hides_the_bar(planted):
    def bare(d):       # games only: no players, no record, nothing graded
        d.update(stars=[], k=[], dst=[], smashed=[], busts=[], tds=[], left_hurt=[], preview_record=None, top=None)
        for g in d["games"]:
            g["preview"] = None
        return d
    page, errors = planted("bare", bare)
    rc = RecapPage(page)
    assert rc.tab_count() == 0                      # Scores is the only tab left
    assert rc.sections()["games"] == 1 and rc.lead_count() == 0
    assert rc.strip_count() == 0 and rc.marks()["all"] == 0

    def sparse(d):     # no touchdowns, one list: the other lists and cards are not drawn, no zeros
        d.update(tds=[], busts=[], left_hurt=[], k=[], dst=[], preview_record=None)
        return d
    page, errors2 = planted("sparse", sparse)
    rc = RecapPage(page)
    assert rc.sections()["tds"] == 0 and rc.list_tab_count() == 1
    assert rc.pos_heads() == ["QB", "RB", "WR", "TE"]
    assert "0" not in rc.list_counts()
    assert errors == [] and errors2 == []


@pytest.mark.journey
def test_weather_is_out_of_the_sub_row_but_the_hash_and_navgo_still_open_it(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, PHONE)
    nav = RecapNav(page)
    assert nav.sub_row() == ["Today", "Live", "Start/Sit", "Preview", "Results", "Highlights"]
    assert nav.sub_row_fits()
    nav.open_by_hash("weather")
    assert nav.group() == "week"
    assert nav.pressed_subs() == 0
    nav.go("weekrecap")
    assert nav.pressed_sub() == "Results"
    ctx.close()
    assert errors == []


@pytest.mark.parametrize("tab", ["players", "scores", "claude"])
def test_nothing_scrolls_sideways_at_360(mount, tab):
    page, errors = mount("weekrecap")
    rc = on_tab(page, tab)
    assert rc.sideways() <= 0
    assert rc.clipped_scrollers() == []
    assert errors == []
