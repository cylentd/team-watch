"""The phone's one tab row, in Node (data/tabrow.js; 2026-10-05, game-day flow wave 2, unit U6).

On a phone the group's views are pills in one row under the header, and the open view's pill opens in
place into that view's own tabs (Live: My league, NFL, TDs). What the row holds, which pill and segment
are pressed, and where the row scrolls to are data: no DOM. How it looks at 360 px is test_render.py."""
import pytest

WEEK = ["digest", "weekrecap", "news", "matchups", "preview", "live"]
LIVE = {"ids": ["league", "games", "tds"], "cur": "games"}


@pytest.fixture(scope="module")
def row(node_js):
    return node_js("data/tabrow.js")


def test_a_view_with_no_tabs_draws_plain_pills(row):
    plan = row("tabRowPlan", WEEK, "news", None, True)
    assert plan["shown"] is True
    assert [p["leaf"] for p in plan["pills"]] == WEEK
    assert [p["leaf"] for p in plan["pills"] if p["on"]] == ["news"]
    assert all(p["segs"] is None for p in plan["pills"])


def test_the_open_view_opens_into_its_own_tabs_in_place(row):
    plan = row("tabRowPlan", WEEK, "live", LIVE, True)
    live = plan["pills"][-1]
    assert live["leaf"] == "live" and live["on"] is True
    assert live["segs"] == [{"id": "league", "on": False}, {"id": "games", "on": True}, {"id": "tds", "on": False}]
    assert all(p["segs"] is None for p in plan["pills"][:-1]), "only the open view expands"


def test_a_desktop_keeps_the_views_own_bar(row):
    """Over 760 px the row is today's words, and the view draws its own tabs."""
    plan = row("tabRowPlan", WEEK, "live", LIVE, False)
    assert all(p["segs"] is None for p in plan["pills"])


def test_an_unknown_current_tab_presses_the_first(row):
    plan = row("tabRowPlan", WEEK, "live", {"ids": ["league", "games", "tds"], "cur": "matchup"}, True)
    assert [s["on"] for s in plan["pills"][-1]["segs"]] == [True, False, False]


def test_one_tab_is_not_a_choice(row):
    """Recap with only Scores left draws no segments, as its own bar hides with one tab."""
    plan = row("tabRowPlan", WEEK, "weekrecap", {"ids": ["scores"], "cur": "scores"}, True)
    assert plan["pills"][1]["segs"] is None


def test_a_view_opened_off_the_row_presses_nothing(row):
    """Weather is out of the row (NAV_HIDDEN; Schedule was too until 2026-10-06): open, no pill is pressed and nothing expands."""
    plan = row("tabRowPlan", WEEK, "weather", {"ids": ["a", "b"], "cur": "a"}, True)
    assert not any(p["on"] for p in plan["pills"]) and all(p["segs"] is None for p in plan["pills"])


def test_a_group_of_one_shows_a_row_only_for_its_views_tabs(row):
    assert row("tabRowPlan", ["parlay"], "parlay", None, True)["shown"] is False
    assert row("tabRowPlan", ["parlay"], "parlay", {"ids": ["thu", "sun"], "cur": "sun"}, True)["shown"] is True
    assert row("tabRowPlan", ["parlay"], "parlay", {"ids": ["thu", "sun"], "cur": "sun"}, False)["shown"] is False


@pytest.mark.parametrize("left,width,scroll,view,want", [
    (20, 60, 0, 360, 0),          # already in view: the row stays where the reader left it
    (400, 60, 0, 360, 116),       # off the right edge: just far enough to show it, with 16 px to spare
    (40, 60, 200, 360, 24),       # off the left edge: back to it
    (300, 420, 0, 360, 284),      # wider than the row (a pill opened into its tabs): its start shows
])
def test_the_pressed_pill_is_scrolled_into_view(row, left, width, scroll, view, want):
    assert row("tabRowScroll", left, width, scroll, view, 16) == want


PILL = {"left": 92, "width": 367}     # Recap opened into four tabs: wider than a 360 px row


@pytest.mark.req("Swipe between tabs", ac="a swipe into a view lands on its nearest tab")
@pytest.mark.parametrize("seg,want", [
    (None, 76),                                   # no tab to aim at: the pill's start, as before
    ({"left": 162, "width": 72}, 76),             # its first tab shows at the pill's start: the same place
    ({"left": 351, "width": 85}, 76),             # a tab ending right at the row's edge shows whole already
    ({"left": 377, "width": 85}, 118),            # its last tab is past the edge there: just far enough to show it
])
def test_a_swipe_aims_the_row_at_the_tab_it_landed_on(row, seg, want):
    assert row("tabRowAim", PILL, seg, 0, 360, 16) == want


def _step(row, leaf, modes, d):
    return row("tabRowStep", row("tabRowPlan", WEEK, leaf, modes, True), d)


@pytest.mark.req("Swipe between tabs", ac="a swipe is a tap on the next thing in the row")
@pytest.mark.parametrize("leaf,modes,d,want", [
    ("news", None, 1, {"leaf": "matchups"}),                  # swipe left: the pill to the right
    ("news", None, -1, {"leaf": "weekrecap"}),                # swipe right: the pill to the left
    ("live", LIVE, 1, {"seg": "tds"}),                        # an opened pill: its tabs are stops too
    ("live", LIVE, -1, {"seg": "league"}),
    ("live", {"ids": ["league", "games", "tds"], "cur": "league"}, -1, {"leaf": "preview"}),  # off its first tab
    ("preview", None, 1, {"leaf": "live"}),                   # into a view with tabs: the view (its tab is tabRowEnter's)
    ("digest", None, 1, {"leaf": "weekrecap"}),               # from the first pill: its end stops only the way back
])
def test_a_swipe_goes_to_the_next_stop_in_the_row(row, leaf, modes, d, want):
    assert _step(row, leaf, modes, d) == want


@pytest.mark.req("Swipe between tabs", ac="the row's ends stop the swipe")
@pytest.mark.parametrize("leaf,modes,d", [
    ("digest", None, -1),                                     # first pill: nothing to the left
    ("live", {"ids": ["league", "games", "tds"], "cur": "tds"}, 1),  # last tab of the last pill
    ("weather", None, 1),                                     # a view off the row has no place in it
])
def test_a_swipe_past_the_row_goes_nowhere(row, leaf, modes, d):
    assert _step(row, leaf, modes, d) is None


RECAP = {"ids": ["players", "scores", "claude", "accuracy"], "cur": "accuracy"}


@pytest.mark.req("Swipe between tabs", ac="a swipe into a view lands on its nearest tab")
@pytest.mark.parametrize("modes,d,want", [
    (LIVE, 1, "league"),                                              # Preview -> Live: its first tab, not the one it remembers
    (RECAP, 1, "players"),                                            # Digest -> Recap left on Accuracy: Players
    ({**RECAP, "cur": "players"}, -1, "accuracy"),                    # News -> Recap: its last tab
    ({**LIVE, "cur": "nothing"}, -1, "tds"),                          # a current tab it no longer has
    ({"ids": ["thu", "sun"], "cur": "thu"}, -1, "sun"),               # Slips with two kickoffs, from All lines
])
def test_a_swipe_into_a_view_with_tabs_lands_on_the_tab_nearest_where_it_came_from(row, modes, d, want):
    assert row("tabRowEnter", modes, d, True) == want


@pytest.mark.parametrize("modes,d,phone", [
    ({**LIVE, "cur": "league"}, 1, True),                             # already on its first tab: nothing to select
    ({**RECAP, "cur": "nothing"}, 1, True),                           # an unknown tab draws as the first already
    ({"ids": ["scores"], "cur": "scores"}, -1, True),                 # one tab is not a choice
    (None, 1, True),                                                  # a view with no tabs
    (LIVE, 1, False),                                                 # a desktop: the tabs are the view's own bar, not stops
])
def test_a_swipe_into_a_view_selects_nothing_when_there_is_nothing_to_move(row, modes, d, phone):
    assert row("tabRowEnter", modes, d, phone) is None


def test_a_hidden_row_takes_no_swipe(row):
    """A group of one (Bets > Slips with no kickoffs) shows no row, so there is nothing to swipe to."""
    assert row("tabRowStep", row("tabRowPlan", ["parlay"], "parlay", None, True), 1) is None


def test_a_view_declares_its_tabs_once(row):
    """One mechanism: a view registers its tabs; the row reads them. No view-specific code in nav.js."""
    assert row("navModesOf('nothing')") is None
    got = row("""(() => { navModes("demo", () => ({ids: ["a", "b"], cur: "b", attr: "demotab",
      label: k => k.toUpperCase(), select: () => {}})); const m = navModesOf("demo");
      return {ids: m.ids, cur: m.cur, attr: m.attr, label: m.label("a")}; })()""")
    assert got == {"ids": ["a", "b"], "cur": "b", "attr": "demotab", "label": "A"}
