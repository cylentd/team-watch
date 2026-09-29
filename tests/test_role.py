"""design/role.py and Players > Role (leaf `movers`, 2026-09-29): what each RB/WR/TE's work is
worth beside what he scored, from ff-jarvis's role_board.json (the fixture is a slice of the real
week-3 file)."""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "design"))
import contract  # noqa: E402
from role import live_role  # noqa: E402
from sources import load_role_board  # noqa: E402
from test_render import browser, SEED  # noqa: E402,F401  (the suite's one Chromium and its pinned clock)


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def test_block_keeps_rb_wr_te_with_two_games_best_role_first():
    b = live_role(load_role_board(), slug)
    contract.validate("LIVE_ROLE", b)
    pos = {r["pos"] for r in b["rows"]}
    assert pos <= {"RB", "WR", "TE"}, "a QB is not on the board"
    assert all(r["g"] >= 2 for r in b["rows"]), "one game is a box score, not a role"
    assert [r["xfp"] for r in b["rows"]] == sorted((r["xfp"] for r in b["rows"]), reverse=True)
    assert b["rows"][0]["n"] == "Jahmyr Gibbs"


def test_gap_and_last_season_come_through_as_written():
    rows = {r["n"]: r for r in live_role(load_role_board(), slug)["rows"]}
    jsn = rows["Jaxon Smith-Njigba"]
    assert round(jsn["pts"] - jsn["xfp"], 1) == jsn["gap"]
    assert jsn["prev"]["season"] == 2025 and jsn["prev"]["gap"] > 0, "beat his workload last season too"
    assert any(r["prev"] is None for r in rows.values()), "the fixture carries a player with no last season"


def test_no_file_is_no_block():
    assert live_role(None, slug) is None
    contract.validate("LIVE_ROLE", None)


@pytest.mark.render
def test_role_draws_the_work_and_never_advises(browser, page_file):
    ctx = browser.new_context(viewport={"width": 360, "height": 800}, reduced_motion="reduce")
    page = ctx.new_page()
    page.set_default_timeout(5000)
    page.route(re.compile(r"^https?://"), lambda route: route.abort())
    page.add_init_script(SEED)
    try:
        page.goto(page_file.as_uri() + "#movers")
        page.wait_for_selector(".rv-row")
        first = page.locator(".rv-row").first
        assert "Gibbs" in first.inner_text()
        assert "in the 5" in first.locator(".rv-work").inner_text(), "his touchdowns sit beside his scoring chances"
        lines = page.evaluate("""Math.max(...[...document.querySelectorAll('.rv-work')].map(e =>
          Math.round(e.offsetHeight / parseFloat(getComputedStyle(e).lineHeight || 16))))""")
        assert lines == 1, f"the work line wraps to {lines} lines at 360px (it did in mono)"
        text = page.locator("#view").inner_text().lower()
        assert not re.search(r"\b(buy|sell|luck|lucky)\b", text), "the page describes; it does not advise"
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.locator("[data-rvpos='TE']").click()
        assert all(p == "TE" for p in page.locator(".rv-pos").all_inner_texts())
    finally:
        ctx.close()
