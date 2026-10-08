"""design/highlights.py and Players > Highlights (leaf `highlights`, 2026-09-29): two Claude-written,
number-checked lines per Players view, from ff-jarvis's highlights.json (the fixture is the real week-4
run's packet). (The Digest's Highlights section left on 2026-10-04.)"""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "design"))
import contract  # noqa: E402
from highlights import VIEWS, live_highlights  # noqa: E402
from sources import load_highlights  # noqa: E402
from test_render import open_at  # noqa: E402
from wording import words  # noqa: E402


def test_block_keeps_the_tabs_order_and_each_views_leaf():
    b = live_highlights(load_highlights())
    contract.validate("LIVE_HIGHLIGHTS", b)
    assert [(v["view"], v["leaf"]) for v in b["views"]] == list(VIEWS)
    assert all(1 <= len(v["rows"]) <= 2 for v in b["views"])
    row = b["views"][0]["rows"][0]
    assert set(row) == {"slug", "n", "pos", "team", "num", "line", "kind"}
    assert row["kind"] == "ranks.jump", "the kind is the candidate id's view and kind, ff-jarvis's contract"


def test_a_line_with_no_text_and_a_view_with_no_lines_drop():
    raw = {"season": 2026, "week": 4, "generated": "x",
           "views": {"ranks": [{"slug": "a", "n": "A", "num": "QB1", "line": ""}], "role": [{"slug": "b", "n": "B", "num": "1", "line": "B."}]}}
    b = live_highlights(raw)
    assert [v["view"] for v in b["views"]] == ["role"]


def test_no_file_is_no_block():
    assert live_highlights(None) is None
    assert live_highlights({"views": {}}) is None
    contract.validate("LIVE_HIGHLIGHTS", None)


@pytest.mark.render
def test_highlights_leads_players_and_each_card_opens_its_view(browser, page_file):
    ctx, page, errors = open_at(browser, page_file, (360, 800), "#highlights")
    try:
        page.wait_for_selector(".hl-v")
        assert page.evaluate("NAV.find(([g]) => g === 'scouting')[1][0]") == "highlights", "Players opens on Highlights"
        heads = [h.strip() for h in page.locator(".hl-go").all_inner_texts()]
        assert heads == [words(f"highlights.view.{k}") for k in ("ranks", "leaders", "role", "grid")]
        assert page.locator(".hl-ln").count() == 8
        assert page.locator(".hl-ln .hl-art :is(img, .fallback)").count() == 8, "every card shows the player"
        # The Reel (2026-09-30): every number has its unit, and a sign says up or down in colour.
        cards = page.evaluate("""() => [...document.querySelectorAll('.hl-ln')].map(c => ({
          num: c.querySelector('.hl-n').textContent, cls: c.querySelector('.hl-n').className,
          unit: (c.querySelector('.hl-txt > .hl-u') || {}).textContent || ''}))""")
        assert all(c["unit"] for c in cards), cards
        def tone(c):
            return " up" if c["num"].startswith("+") else " down" if c["num"].startswith("-") else ""
        assert [c for c in cards if c["cls"] != "hl-n" + tone(c)] == []
        text = page.locator("#view").inner_text().lower()
        assert not re.search(r"\b(buy|sell|start him|sit him)\b", text), "the tab describes; it does not advise"
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        # A packet for another week than the page's (after the turn, 2026-10-05) says nothing is posted.
        page.evaluate("LIVE_SCHEDULE.week = LIVE_HIGHLIGHTS.week + 1; render()")
        page.wait_for_selector(".hl .state-empty")
        assert page.locator(".hl-v").count() == 0 and page.locator(".hl-ln").count() == 0
        page.evaluate("LIVE_SCHEDULE.week = LIVE_HIGHLIGHTS.week; render()")
        page.wait_for_selector(".hl-v")
        page.locator("[data-hlgo='movers']").click()
        assert page.evaluate("SURFACE") == "movers"
        assert errors == []
    finally:
        ctx.close()
