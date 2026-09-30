"""design/highlights.py and Players > Highlights (leaf `highlights`, 2026-09-29): two Claude-written,
number-checked lines per Players view, from ff-jarvis's highlights.json (the fixture is the real week-4
run's packet), and Worth knowing on the Digest reading each view's first line."""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "design"))
import contract  # noqa: E402
from highlights import VIEWS, live_highlights  # noqa: E402
from sources import load_highlights  # noqa: E402
from test_render import browser, SEED  # noqa: E402,F401  (the suite's one Chromium and its pinned clock)


def test_block_keeps_the_tabs_order_and_each_views_leaf():
    b = live_highlights(load_highlights())
    contract.validate("LIVE_HIGHLIGHTS", b)
    assert [(v["view"], v["leaf"]) for v in b["views"]] == list(VIEWS)
    assert all(1 <= len(v["rows"]) <= 2 for v in b["views"])
    row = b["views"][0]["rows"][0]
    assert set(row) == {"slug", "n", "pos", "team", "num", "line"}


def test_a_line_with_no_text_and_a_view_with_no_lines_drop():
    raw = {"season": 2026, "week": 4, "generated": "x",
           "views": {"ranks": [{"slug": "a", "n": "A", "num": "QB1", "line": ""}], "role": [{"slug": "b", "n": "B", "num": "1", "line": "B."}]}}
    b = live_highlights(raw)
    assert [v["view"] for v in b["views"]] == ["role"]


def test_no_file_is_no_block():
    assert live_highlights(None) is None
    assert live_highlights({"views": {}}) is None
    contract.validate("LIVE_HIGHLIGHTS", None)


def _page(browser, page_file, size, hash_):
    ctx = browser.new_context(viewport={"width": size[0], "height": size[1]}, reduced_motion="reduce")
    page = ctx.new_page()
    page.set_default_timeout(5000)
    page.route(re.compile(r"^https?://"), lambda route: route.abort())
    page.add_init_script(SEED)
    page.goto(page_file.as_uri() + "#" + hash_)
    return ctx, page


@pytest.mark.render
def test_highlights_leads_players_and_each_card_opens_its_view(browser, page_file):
    ctx, page = _page(browser, page_file, (360, 800), "highlights")
    try:
        page.wait_for_selector(".hl-v")
        assert page.evaluate("NAV.find(([g]) => g === 'scouting')[1][0]") == "highlights", "Players opens on Highlights"
        heads = [h.strip() for h in page.locator(".hl-go").all_inner_texts()]
        assert heads == ["Ranks", "Leaders", "Role", "Grid"]
        assert page.locator(".hl-ln").count() == 8
        assert page.locator(".hl-ln .hl-hd").count() == 8, "every line leads with a face"
        text = page.locator("#view").inner_text().lower()
        assert not re.search(r"\b(buy|sell|start him|sit him)\b", text), "the tab describes; it does not advise"
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.locator("[data-hlgo='movers']").click()
        assert page.evaluate("SURFACE") == "movers"
    finally:
        ctx.close()


@pytest.mark.render
def test_worth_knowing_is_each_views_first_line_never_the_banners(browser, page_file):
    """David, 2026-09-29: one producer feeds both, so the Digest and the tab never disagree."""
    ctx, page = _page(browser, page_file, (360, 800), "digest")
    try:
        page.wait_for_selector(".dg-facts")
        got = page.evaluate("""() => {
          const d = dgD(), banner = dgLeadSlug(d);
          const want = LIVE_HIGHLIGHTS.views.map(v => (v.rows.find(r => r.slug !== banner) || {}).slug);
          const tiles = [...document.querySelectorAll('.dg-facts .dg-fact')].map(t => [t.dataset.dgfact, t.dataset.dggo]);
          return {banner, want, tiles, leaves: LIVE_HIGHLIGHTS.views.map(v => v.leaf),
                  more: (document.querySelector('.dg-facts [data-dggo="highlights"]') || {}).textContent || ''};
        }""")
        assert [s for s, _ in got["tiles"]] == [s for s in got["want"] if s]
        assert [g for _, g in got["tiles"]] == got["leaves"][:len(got["tiles"])]
        assert got["banner"] not in [s for s, _ in got["tiles"]]
        assert "More in Highlights" in got["more"]
    finally:
        ctx.close()
