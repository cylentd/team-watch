"""Stats' position strip (chrome/statspos.js, 2026-10-06, David's "A Slide"): on a phone the positions leave
each Stats view's top row for one pill above the bottom bar, where the thumb is; a tap picks, and a press
that slides along the pill picks the segment under the finger as it moves. The position is one for all of
Stats. Which position a view shows for the shared one is Node's (tests/test_js_statspos.py); these tests
are the strip's layout, its taps and slides, and what the views draw. Mounted views (tests/component.py),
read through tests/pages/statspos.py."""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.ranks import RanksPage
from pages.statspos import StatsPosStrip

# Every phone mount is a touch screen, as a phone is: one kept context per view (tests/component.py).
PHONE, DESKTOP = (360, 740), (1280, 900)
CORE = ["QB", "RB", "WR", "TE"]
# The suite's seed picks the Yahoo team, so Ranks adds D/ST and K (surface/ranks/dst.js).
STRIPS = [("ranks", CORE + ["FLEX", "DST", "K"], ["QB", "RB", "WR", "TE", "FLEX", "D/ST", "K"]),
          ("board", CORE, CORE),
          ("movers", ["ALL", "RB", "WR", "TE"], ["All", "RB", "WR", "TE"]),
          ("usage", CORE, CORE),
          ("schedule", CORE, CORE)]


@pytest.mark.render
@pytest.mark.req("Stats position strip", ac="a phone's Stats view draws the strip above the bar, not its top chips")
@pytest.mark.parametrize("surface,positions,labels", STRIPS, ids=[s[0] for s in STRIPS])
def test_a_phone_draws_the_strip_above_the_bar_instead_of_the_top_chips(mount, surface, positions, labels):
    page, errors = mount(surface, size=PHONE, touch=True)
    strip = StatsPosStrip(page)
    assert strip.shown()
    assert strip.positions() == positions and strip.labels() == labels
    assert strip.view_chip_count() == 0, "the view's own top chips are not drawn on a phone"
    g = strip.geometry()
    assert round(g["bar_top"] - g["bottom"]) == 12, "12px above the bottom bar"
    assert (round(g["left"]), round(g["width"] - g["right"])) == (16, 16), "16px gutters"
    assert round(g["height"]) == 48
    assert min(g["segs"]) >= 44, f"every segment a thumb's width: {g['segs']}"
    assert not strip.scrolls_sideways()
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Stats position strip", ac="a desktop keeps the top chips and draws no strip")
def test_a_desktop_keeps_the_top_chips_and_draws_no_strip(mount):
    page, errors = mount("ranks", size=DESKTOP)
    strip = StatsPosStrip(page)
    assert not strip.shown()
    assert strip.view_chip_count() == 7
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Stats position strip", ac="a Stats view with no position draws no strip")
def test_news_draws_no_strip(mount):
    """Highlights, the first such view, was dropped 2026-10-08; News holds no position either."""
    page, errors = mount("ranks", size=PHONE, touch=True)
    strip = StatsPosStrip(page)
    strip.open_view("news")
    assert strip.surface() == "news" and not strip.shown()
    strip.open_view("ranks")
    assert strip.shown(), "back on Ranks it returns"
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Stats position strip", ac="a tap picks the segment and the view's list follows")
def test_a_tap_on_a_segment_redraws_the_list(mount):
    page, errors = mount("ranks", size=PHONE, touch=True)
    strip, ranks = StatsPosStrip(page), RanksPage(page)
    assert strip.pressed() == ["RB"] and strip.highlight_on() == "RB"
    strip.tap("WR")
    assert strip.pressed() == ["WR"] and strip.highlight_on() == "WR"
    assert "WR ranks" in strip.drawn()
    assert [r["slug"] for r in ranks.rows()][:1] == ["amonra-st-brown"]
    assert strip.highlight_count() == 1, "one highlight slides; the segments carry none of their own"
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Stats position strip", ac="a press that slides picks the segment under the finger as it moves")
def test_a_slide_picks_the_segment_under_the_finger_as_it_moves(mount):
    page, errors = mount("ranks", size=PHONE, touch=True)
    strip = StatsPosStrip(page)
    seen = strip.slide("QB", ["RB", "WR", "TE"], lambda: (strip.pressed(), strip.drawn()))
    assert [p for p, _ in seen] == [["QB"], ["RB"], ["WR"], ["TE"], ["TE"]], "the list follows the finger, then stays"
    assert [d.split()[2] for _, d in seen] == ["QB", "RB", "WR", "TE", "TE"]
    assert strip.highlight_on() == "TE"
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Stats position strip", ac="the strip takes its own touches")
def test_the_strip_takes_its_own_touches_and_reads_as_a_group_of_buttons(mount):
    page, errors = mount("ranks", size=PHONE, touch=True)
    strip = StatsPosStrip(page)
    assert strip.gesture() == {"touch": "none", "own": True}, "a slide never scrolls the page or swipes the tab"
    assert strip.group() == {"role": "group", "label": "Position", "buttons": True}
    strip.focus("WR")
    ring = strip.focus_ring("WR")
    assert ring["focused"] and ring["style"] == "solid" and ring["width"] == "2px"
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Stats position strip", ac="a sideways drag on the strip moves the position, never the tab")
def test_a_finger_dragged_along_the_strip_picks_a_position_and_never_turns_the_tab(mount):
    """The tab swipe listens on the whole document (chrome/tabswipe.js, 2026-10-06); a drag from QB to TE is a
    sideways swipe by its shape, so only the strip owning its touches keeps Ranks open."""
    page, errors = mount("ranks", size=PHONE, touch=True)
    strip = StatsPosStrip(page)
    assert strip.tab() == ["ranks", "ranks"]
    strip.finger_drag("QB", "TE")
    assert strip.pressed() == ["TE"] and "TE ranks" in strip.drawn()
    assert strip.tab() == ["ranks", "ranks"], "the tab row did not move"
    strip.finger_drag("TE", "RB")
    assert strip.pressed() == ["RB"] and strip.tab() == ["ranks", "ranks"]
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Stats position strip", ac="one position for all of Stats")
def test_the_position_carries_across_stats(mount):
    page, errors = mount("ranks", size=PHONE, touch=True)
    strip = StatsPosStrip(page)
    strip.tap("WR")
    not_pressed, not_drawn = [], []
    for leaf in ("board", "usage", "movers", "schedule"):
        strip.open_view(leaf)
        if strip.pressed() != ["WR"]:
            not_pressed.append(leaf)
        if "WR" not in strip.drawn():
            not_drawn.append(leaf)
    assert not_pressed == [], "WR is not the pressed position on these views"
    assert not_drawn == [], "WR is not drawn on these views"
    strip.open_view("ranks")
    strip.tap("FLEX")
    strip.open_view("movers")
    assert strip.pressed() == ["ALL"] and strip.drawn() == "RB TE WR", "FLEX is All on Work vs points"
    strip.open_view("board")
    assert strip.pressed() == ["WR"] and strip.drawn() == "WR", "Leaders keeps the last of QB to TE"
    strip.open_view("ranks")
    assert strip.pressed() == ["FLEX"], "and the shared choice is still FLEX"
    strip.tap("QB")
    strip.open_view("movers")
    assert strip.pressed() == ["ALL"], "no QB on Work vs points"
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Stats position strip", ac="the last row clears the strip")
@pytest.mark.parametrize("surface", [s[0] for s in STRIPS])
def test_the_last_row_clears_the_strip(mount, surface):
    page, errors = mount(surface, size=PHONE, touch=True)
    strip = StatsPosStrip(page)
    strip.scroll_to_end()
    assert strip.lowest_content_bottom() <= strip.strip_top(), "nothing hides behind the strip at the page's end"
    assert errors == []
