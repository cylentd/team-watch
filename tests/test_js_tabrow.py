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
    """Weather and Schedule are out of the row (NAV_HIDDEN): open, no pill is pressed and nothing expands."""
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


def test_a_view_declares_its_tabs_once(row):
    """One mechanism: a view registers its tabs; the row reads them. No view-specific code in nav.js."""
    assert row("navModesOf('nothing')") is None
    got = row("""(() => { navModes("demo", () => ({ids: ["a", "b"], cur: "b", attr: "demotab",
      label: k => k.toUpperCase(), select: () => {}})); const m = navModesOf("demo");
      return {ids: m.ids, cur: m.cur, attr: m.attr, label: m.label("a")}; })()""")
    assert got == {"ids": ["a", "b"], "cur": "b", "attr": "demotab", "label": "A"}
