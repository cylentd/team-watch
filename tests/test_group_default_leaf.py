"""A group click opens the group's first view (2026-10-07, TODO "group-default-leaf").

League -> Roster and This week -> Digest on every click, however far into the group the reader went last
time; it used to return to the last leaf seen there (LAST_LEAF). A hash is still the place a reload or a
bookmark lands, and Back still walks the views. The phone's bottom tab bar and the desktop bar are the
same `#nav` buttons, so each size is proven here. The page's clock is pinned to a Saturday (SEED), so the
Tuesday rule (Waivers leads League on a claims day, chrome/nav.js navDefaultLeaf) does not enter."""
import pytest

from component import mount  # noqa: F401

pytestmark = pytest.mark.render

SIZES = {"phone bottom bar": (360, 740), "desktop bar": (1280, 800)}
GROUP_BUTTON = "#nav .navitem[data-s='{}']"


def leaf(page):
    return page.evaluate("SURFACE")


def tap_group(page, group):
    page.locator(GROUP_BUTTON.format(group)).click()
    page.wait_for_function("g => navGroupOf(SURFACE) === g", arg=group)


@pytest.fixture(params=sorted(SIZES))
def home(request, mount):
    """The Digest at the size under test: (page, errors), asserted free of page errors after the test."""
    page, errors = mount("digest", size=SIZES[request.param])
    yield page
    assert errors == []


@pytest.mark.req("Navigation: one League group, Stats", ac="a group click opens the group's first view")
def test_league_opens_roster_after_the_reader_left_it_on_teams(home):
    home.evaluate("navGo('teams')")
    tap_group(home, "week")
    tap_group(home, "team")
    assert leaf(home) == "roster"


@pytest.mark.req("Navigation: one League group, Stats", ac="a group click opens the group's first view")
def test_this_week_opens_the_digest_after_the_reader_left_it_on_news(home):
    home.evaluate("navGo('news')")
    tap_group(home, "league")
    tap_group(home, "home")   # Today is Home, its own tab (Home draft B, 2026-10-08)
    assert leaf(home) == "digest"


@pytest.mark.req("Navigation: one League group, Stats", ac="a group click opens the group's first view")
def test_the_open_group_taps_back_to_its_first_view(home):
    home.evaluate("navGo('dfs')")
    tap_group(home, "week")
    assert leaf(home) == "preview"   # Matchup's landing view outside a game window (David, 2026-10-09)


@pytest.mark.req("Navigation: one League group, Stats", ac="a group click opens the group's first view")
@pytest.mark.parametrize("group,deep,first", [("scouting", "usage", "ranks"), ("week", "dfs", "preview")])
def test_stats_and_bets_open_their_first_view_too(home, group, deep, first):
    home.evaluate("leaf => navGo(leaf)", deep)
    tap_group(home, "home")
    tap_group(home, group)
    assert leaf(home) == first


@pytest.mark.req("Navigation: one League group, Stats", ac="the hash still restores a leaf")
def test_a_hash_still_opens_its_own_leaf_after_a_group_click(home):
    home.evaluate("navGo('teams')")
    tap_group(home, "week")
    home.evaluate("location.hash = '#usage'")
    home.wait_for_function("SURFACE === 'usage'")
    assert leaf(home) == "usage"


@pytest.mark.req("Navigation: one League group, Stats", ac="the hash still restores a leaf")
def test_a_bookmark_opens_its_leaf_not_the_group_default(mount):
    page, errors = mount("usage")
    assert (leaf(page), page.evaluate("location.hash")) == ("usage", "#usage")
    assert errors == []


@pytest.mark.req("Navigation: one League group, Stats", ac="Back is unchanged")
def test_back_after_a_group_click_returns_to_the_view_it_left(home):
    home.evaluate("navGo('news')")
    tap_group(home, "team")
    assert leaf(home) == "roster"
    home.go_back()
    home.wait_for_function("SURFACE === 'news'")
    assert leaf(home) == "news"

