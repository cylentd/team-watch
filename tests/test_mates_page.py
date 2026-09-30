"""A leaguemate picks their own team (leaguemates phase 1, 2026-09-25): every team in David's two
leagues is in the team switch under its league's name, a pick is remembered in the browser, and a
leaguemate's team has no Waivers (ff-jarvis builds David's only until phase 3)."""
import pytest

from test_render import browser, open_page  # noqa: F401  (browser is a fixture)


def test_a_leaguemate_picks_their_team_and_it_sticks(browser, page_file):
    """My teams asks first (2026-09-27): with no pick in this browser, every My teams view is the
    picker, all 24 teams by league and no "none", never David's roster."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    mates = page.evaluate("MATES.map(m => m.key)")
    if not mates:
        pytest.skip("the fixture's roster files hold no other team")
    mine = page.evaluate("myLeagueKeys().length")   # David's team per league: three since AYO, 2026-09-29
    for leaf in ("roster", "waivers", "myrecap"):
        page.evaluate(f"localStorage.removeItem('tw-team'); SURFACE='{leaf}'; render()")
        assert page.locator("#view[data-view='pick'] .tp-team").count() == len(mates) + mine, f"{leaf} asks first"
        assert page.locator("#view .row").count() == 0, "no roster until a pick"
    assert page.locator(".tp-lg").count() == mine == 3, "one list per league"
    page.locator(f".tp-team[data-pick='{mates[0]}']").click()
    assert page.evaluate("VIEW") == mates[0]
    assert page.evaluate("localStorage.getItem('tw-team')") == mates[0]
    assert page.locator("#view[data-view='pick']").count() == 0, "asked only until a pick"
    assert "Waivers" in page.locator("#subnav").inner_text(), "their league's rail (phase 2)"
    assert page.locator("#subnav .tabcount").count() == 0, "but no claim count: that list is David's"
    page.evaluate("SURFACE='roster'; render()")
    assert page.locator("#view .row").count() > 0, "the leaguemate's roster draws"
    page.reload()
    page.wait_for_function("document.getElementById('view').children.length > 0")
    assert page.evaluate("VIEW") == mates[0], "the pick opens next time"
    assert errors == []
    ctx.close()


def test_a_leaguemates_waivers_is_their_leagues_rail_without_davids_advice(browser, page_file):
    """Phase 2 (2026-09-26): a leaguemate's Waivers tab shows the league's Breaking rail, keyed by
    league, with no status rows (David's players), no verdicts, no cards, no must-claim count."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    mate = page.evaluate("(MATES[0] || {}).key")
    if not mate:
        pytest.skip("the fixture's roster files hold no other team")
    page.evaluate(f"VIEW = '{mate}'; SURFACE = 'waivers'; render(); paintSubnav()")
    assert "Waivers" in page.locator("#subnav").inner_text()
    assert page.locator(".wvc").count() == 0 and page.locator(".wv-mate").count() == 1
    assert page.locator(".wvr-row.k-status").count() == 0
    league = page.evaluate(f"TEAMS['{mate}'].league")
    kept = page.evaluate(f"wireEvents('{league}').filter(e => e.kind !== 'status').length")
    assert page.locator(".wvr-row").count() == kept, "every league-wide row stays"
    text = page.locator("#view").inner_text()
    assert "must-claim" not in text.lower() and "FAAB" not in text
    assert errors == []
    ctx.close()


# Live followed a leaguemate's ESPN board until 2026-09-28; it now shows every matchup in both
# leagues to everyone (tests/test_gameday.py), so there is nothing per-team left to follow.


def test_owner_names_never_reach_the_page(page_file):
    """Team names only (David, 2026-09-25): LIVE_MATES carries a team's name and roster, nothing
    about who owns it."""
    import json, re
    text = page_file.read_text(encoding="utf-8")
    m = re.search(r"const LIVE_MATES = (.*?);\n", text)
    if not m or m.group(1) == "null":
        pytest.skip("no LIVE_MATES block in the fixture page")
    for team in json.loads(m.group(1))["teams"]:
        assert set(team) == {"key", "league", "name", "roster"}
