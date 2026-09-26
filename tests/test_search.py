"""Player search: the joined index, the matcher, and the sheet on a phone.

The fixture carries Amon-Ra St. Brown (WR, DET), Chase Brown (RB, CIN) and Tee Higgins (WR, CIN)
on the rosters, which is enough to prove prefix, hyphen halves, a typo, and a position/team filter.
"""
import pytest

from test_render import browser, open_page  # noqa: F401  (browser is a fixture)

pytestmark = pytest.mark.render

PHONE = (360, 780)
DESK = (1280, 900)


@pytest.fixture(scope="module")
def page(browser, page_file):
    ctx, pg, errors = open_page(browser, page_file, DESK)
    yield pg
    assert errors == []
    ctx.close()


def slugs(page, q):
    return page.evaluate(f"searchFind({q!r}, 8).map(r => r.e.slug)")


def test_the_index_holds_each_player_once_and_every_rostered_one(page):
    dupes = page.evaluate("(() => { const s = searchIndex().map(e => e.slug); return s.length - new Set(s).size; })()")
    assert dupes == 0
    # A leaguemate's team is rostered only while it is on screen (data/search.js); a player with no
    # headshot is indexed by his name's slug.
    missing = page.evaluate("""Object.values(TEAMS).filter(tm => !tm.mate || tm.key === VIEW)
        .flatMap(tm => tm.roster.map(p => [p.slug || slugOf(p.n), tm.key]))
        .filter(([s, k]) => !searchIndex().some(e => e.slug === s && e.tier === 3 && e.leagues.includes(k)))""")
    assert missing == []


def test_a_leaguemates_players_are_yours_only_on_their_team(page):
    mate = page.evaluate("(MATES[0] || {}).key")
    if not mate:
        pytest.skip("no leaguemate in the fixture")
    tagged = lambda: page.evaluate(f"searchIndex().filter(e => e.leagues.includes('{mate}')).length")
    assert tagged() == 0, "another team's players are not the reader's"
    page.evaluate(f"VIEW = '{mate}'; SEARCH_INDEX = null")
    try:
        assert tagged() > 0, "the reader's own pick is"
    finally:
        page.evaluate("VIEW = 'yahoo'; SEARCH_INDEX = null")   # the page is shared with the tests after


@pytest.mark.parametrize("q,first", [
    ("amonra", "amonra-st-brown"),     # a hyphenated name typed without its hyphen
    ("Amon-Ra", "amonra-st-brown"),    # and with it
    ("st. brown", "amonra-st-brown"),  # punctuation dropped, two words both required
    ("higg", "tee-higgins"),           # the start of a surname
    ("higins", "tee-higgins"),         # one letter missing, 4+ letters typed
])
def test_the_best_match_comes_first(page, q, first):
    assert slugs(page, q)[0] == first


def test_a_hyphenated_name_answers_to_its_second_half(page):
    assert "amonra-st-brown" in slugs(page, "ra")


def test_position_and_team_words_filter(page):
    got = page.evaluate("searchFind('wr det', 50).map(r => [r.e.pos, r.e.team])")
    assert got and all(pos == "WR" and team == "DET" for pos, team in got)


def test_no_typo_allowance_under_four_letters(page):
    # "brw" is one edit from "bro", but at three letters that would match half the league.
    assert "chase-brown" not in slugs(page, "brw")


def test_ties_break_toward_the_players_you_roster(page):
    ranked = page.evaluate("searchFind('a', 400).map(r => [r.score, r.e.tier])")
    assert ranked == sorted(ranked, key=lambda r: (-r[0], -r[1]))


def test_the_matched_letters_are_bold(page):
    html = page.evaluate("searchNameHTML('Amon-Ra St. Brown', searchFind('ra', 8).find(r => r.e.slug === 'amonra-st-brown').marks)")
    assert html == "Amon-<b>Ra</b> St. Brown"


def test_slash_opens_and_escape_closes_on_a_desktop(browser, page_file):
    ctx, pg, errors = open_page(browser, page_file, DESK)
    try:
        pg.keyboard.press("/")
        assert pg.is_visible("#search")
        assert pg.evaluate("document.activeElement.id") == "search-q"
        assert pg.input_value("#search-q") == ""   # the slash opened it; it was not typed
        pg.keyboard.press("Escape")
        assert pg.is_hidden("#search")
        pg.wait_for_timeout(50)
        assert pg.evaluate("history.state") is None   # its history entry went with it
        assert errors == []
    finally:
        ctx.close()


def test_the_phone_flow(browser, page_file):
    """Open from the nav bar, type, tap the best match, then Back twice: profile, then search."""
    ctx, pg, errors = open_page(browser, page_file, PHONE)
    try:
        hash_before = pg.evaluate("location.hash")
        pg.click("#navsearch")
        assert pg.evaluate("document.activeElement.id") == "search-q"
        assert pg.inner_text("#search-list .sr-cap").strip().upper() == "YOUR ROSTER"

        pg.fill("#search-q", "higg")
        best = pg.locator("#sr-0")
        assert "Higgins" in best.inner_text()
        # Best match sits right on top of the input, nearest the thumb; the rest stack upward.
        bar = pg.locator(".search-bar").bounding_box()
        rows = [pg.locator(f"#sr-{i}").bounding_box() for i in range(pg.locator(".sr-row").count())]
        assert abs(rows[0]["y"] + rows[0]["height"] - bar["y"]) < 12
        assert all(r["y"] <= rows[0]["y"] for r in rows)
        assert pg.evaluate("document.documentElement.scrollWidth <= innerWidth")

        best.click()
        pg.wait_for_selector("#modal.on")
        assert "HIGGINS" in pg.inner_text("#pf-title").upper()

        pg.go_back()
        pg.wait_for_function("!document.getElementById('modal').classList.contains('on')")
        assert pg.is_visible("#search")
        assert pg.input_value("#search-q") == "higg"   # the query survives the profile

        pg.go_back()
        pg.wait_for_function("document.getElementById('search').hidden")
        assert pg.evaluate("location.hash") == hash_before   # Back closed layers, not the view

        pg.click("#navsearch")   # and he is now the first recent
        assert pg.inner_text("#search-list .sr-cap").strip().upper() == "RECENT"
        assert "Higgins" in pg.inner_text("#sr-0")
        assert errors == []
    finally:
        ctx.close()


def test_nothing_found_says_why(browser, page_file):
    ctx, pg, errors = open_page(browser, page_file, PHONE)
    try:
        pg.click("#navsearch")
        pg.fill("#search-q", "zzqx")
        assert pg.inner_text(".sr-none") == "No “zzqx” in this week’s data"
        assert errors == []
    finally:
        ctx.close()
