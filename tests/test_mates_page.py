"""A leaguemate picks their own team (leaguemates phase 1, 2026-09-25): every team in David's two
leagues is in the team switch under its league's name, a pick is remembered in the browser, and a
leaguemate's team has no Waivers (ff-jarvis builds David's only until phase 3)."""
import pytest

from test_render import browser, open_page  # noqa: F401  (browser is a fixture)


def test_a_leaguemate_picks_their_team_and_it_sticks(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.evaluate("SURFACE='roster'; render()")
    mates = page.evaluate("MATES.map(m => m.key)")
    if not mates:
        pytest.skip("the fixture's roster files hold no other team")
    assert page.locator("[data-tsask]").count() == 1, "a reader who has not picked is asked once"
    page.click("[data-tsask]")
    heads = page.locator(".ts-head").all_inner_texts()
    assert len(heads) >= 1 and page.locator(".ts-item[data-k]").count() == len(mates) + 2
    page.locator(f".ts-item[data-k='{mates[0]}']").click()
    assert page.evaluate("VIEW") == mates[0]
    assert page.evaluate("localStorage.getItem('tw-team')") == mates[0]
    assert page.locator("[data-tsask]").count() == 0, "asked only until a pick"
    assert "Waivers" not in page.locator("#subnav").inner_text(), "no Waivers for a leaguemate yet"
    assert page.locator("#view .row").count() > 0, "the leaguemate's roster draws"
    page.reload()
    page.wait_for_function("document.getElementById('view').children.length > 0")
    assert page.evaluate("VIEW") == mates[0], "the pick opens next time"
    assert errors == []
    ctx.close()


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
