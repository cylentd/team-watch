"""The floor and ceiling in the page (plan U5, 2026-10-05): the profile strip, a Ranks row and the
Start/Sit picker draw the same projection and the same band for one player, each says in words what the
band is once, and a player with no band draws none. The numbers and the rules for who gets one are
Node tests (tests/test_js_range.py); this file is layout and wiring only.

Fixture player: Joe Burrow, 19.4 points, band 8.4 to 28.8 (ff-jarvis's shipped table applied to the fixture)."""
import pytest

from startsit_page import open_view

BURROW = {"n": "Joe Burrow", "pos": "QB", "team": "CIN", "slug": "joe-burrow"}
PURDY = "brock-purdy"


@pytest.fixture(scope="module")
def page(browser, page_file):
    errors = []
    ctx, pg = open_view(browser, page_file, errors=errors)
    yield pg, errors
    ctx.close()


def ranks_row(pg, slug="joe-burrow"):
    pg.evaluate("() => { statsPick('QB'); navGo('ranks'); }")   # Stats' one position (chrome/statspos.js)
    pg.wait_for_selector(f"[data-rkopen='{slug}']")
    return pg.evaluate("""(slug) => { const r = document.querySelector(`[data-rkopen='${slug}']`);
      return {pts: r.querySelector('.rk-pts').childNodes[0].textContent.trim(),
              band: (r.querySelector('.rk-rng') || {}).textContent || null,
              notes: document.querySelectorAll('.rk-headline p').length ? document.querySelector('.rk-headline p').textContent : ''}; }""", slug)


def profile_strip(pg, slug="joe-burrow"):
    pg.evaluate("(p) => openProfile(p, document.body)", {**BURROW, "slug": slug})
    pg.wait_for_selector("#modal.on .pf-lede")
    got = pg.evaluate("""() => ({pts: document.querySelector('.pf-lede-c.proj b').textContent.trim(),
      band: (document.querySelector('.pf-lede-r') || {}).textContent || null,
      notes: document.querySelectorAll('.pf-lede-note').length,
      noteText: (document.querySelector('.pf-lede-note') || {}).textContent || ''})""")
    pg.evaluate("() => modalShut(document.querySelector('.modal.on'))")
    return got


def picker_lane(pg, slugs):
    pg.evaluate("(s) => { SS_PICKS = s; SS_OPEN = false; SS_Q = ''; navGo('matchups'); render(); }", slugs)
    pg.wait_for_selector(".ssv-lanes")
    return pg.evaluate("""() => { const row = [...document.querySelectorAll('.ssv-row')].find(r => r.querySelector('.ssv-lbl span').textContent === 'Projected');
      return {pts: [...row.querySelectorAll('.ssv-v b')].map(b => b.textContent.trim()),
              band: [...row.querySelectorAll('.ssv-rng')].map(b => b.textContent),
              note: (row.querySelector('.ssv-lbl em') || {}).textContent || '',
              notes: row.querySelectorAll('.ssv-lbl em').length}; }""")


@pytest.mark.render
def test_one_player_has_the_same_projection_and_band_in_all_three_views(page):
    pg, errors = page
    r, p, s = ranks_row(pg), profile_strip(pg), picker_lane(pg, ["joe-burrow", PURDY])
    assert (r["pts"], r["band"]) == ("19.4", "8.4–28.8")
    assert (p["pts"], p["band"]) == ("19.4", "8.4–28.8")
    assert (s["pts"][0], s["band"][0]) == ("19.4", "8.4–28.8")
    assert s["band"][1] == "7.3–27.6", "the second lane has his own band"
    assert errors == []


@pytest.mark.render
def test_each_view_says_what_the_band_is_once(page):
    pg, errors = page
    assert ranks_row(pg)["notes"].count("8 in 10 of his games") == 1
    got = profile_strip(pg)
    assert got["notes"] == 1 and "8 in 10" in got["noteText"]
    lane = picker_lane(pg, ["joe-burrow", PURDY])
    assert lane["notes"] == 1 and "8 in 10 of his games" in lane["note"], "one note on the row, not one per player"
    assert errors == []


@pytest.mark.render
def test_nothing_scrolls_sideways_at_360_with_a_band_in_every_view(page):
    pg, errors = page
    for go in (lambda: ranks_row(pg), lambda: picker_lane(pg, ["joe-burrow", PURDY, "chase-brown"])):
        go()
        assert pg.evaluate("document.documentElement.scrollWidth <= innerWidth")
    profile_strip(pg)
    assert errors == []


@pytest.mark.render
def test_a_player_with_no_band_draws_no_range_and_no_note(page):
    pg, errors = page
    pg.evaluate("""() => { for (const r of [...LIVE_RANKS.rows, ...LIVE_RANKS.flex]) { r.floor = null; r.ceil = null; }
      for (const r of Object.values(LIVE_PROJECTIONS.players)) { r.floor = null; r.ceil = null; } }""")
    r = ranks_row(pg)
    assert r["band"] is None and "8 in 10" not in r["notes"]
    p = profile_strip(pg)
    assert p["band"] is None and p["notes"] == 0 and p["pts"] == "19.4"
    s = picker_lane(pg, ["joe-burrow", PURDY])
    assert s["band"] == [] and s["notes"] == 0 and s["pts"][0] == "19.4"
    assert errors == []
