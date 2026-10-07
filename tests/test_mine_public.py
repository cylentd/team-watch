"""The page carries no David-only "mine" flag (2026-10-06). No browser.

The build used to write `mine` on every prop and every usage-pool row from David's rosters, so the public page
told every reader that David's players were theirs (Build's Mine only, the "My players" slip, the DFS lime edge,
the chat's `rostered_by_me`). Those read the teams the reader follows now (data/mates.js `mineSlugs`,
tests/test_js_bets_mine.py, test_js_mine_rows.py), so nothing reads the flag and the page no longer carries it.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "design"))
import build  # noqa: E402
import contract  # noqa: E402
from test_build import injected  # noqa: E402


def block(built, name):
    return injected(built.fragment)[name]


def test_no_prop_row_carries_a_mine_flag(built):
    rows = block(built, "LIVE_PROPS")["props"]
    assert rows, "the fixture has lines"
    assert [p["n"] for p in rows if "mine" in p] == []


def test_no_prop_row_says_which_of_his_leagues_hold_the_player(built):
    """`leagues` on a prop was the keys of David's leagues that roster the player: his roster, per line, on a
    public page, and nothing read it."""
    rows = block(built, "LIVE_PROPS")["props"]
    assert rows, "the fixture has lines"
    assert [p["n"] for p in rows if "leagues" in p] == []


def test_no_usage_pool_row_carries_a_mine_flag(built):
    rows = block(built, "LIVE_POOL")["players"]
    assert rows, "the fixture has a pool"
    assert [p["n"] for p in rows if "mine" in p] == []


def test_the_contract_no_longer_asks_for_the_flag():
    assert "mine" not in contract.CONTRACT["LIVE_PROPS"]["rows"][1]
    assert "mine" not in contract.CONTRACT["LIVE_POOL"]["rows"][1]


def test_the_build_report_still_counts_the_lines_on_my_rosters(built):
    """The report is David's log, not the page: it counts from his roster blocks, now that no row holds a flag."""
    held = {build.slugify(r["n"]) for name in ("LIVE_ESPN", "LIVE_YAHOO") for r in block(built, name)["roster"]}
    on_mine = sum(1 for p in block(built, "LIVE_PROPS")["props"] if build.slugify(p["n"]) in held)
    assert on_mine, "the fixture's lines include players on his rosters"
    assert f", {on_mine} on my rosters" in "\n".join(built.report)
