"""S15 (David approved 2026-10-31): a reader opens Slips, All lines or DFS and the lines and prices shown are the current
build's, and a slip builds from them.

Two places a stale number could get in. Build: the props file keeps every pull, an old line next to this week's, and the
page must carry the newest `updated` per book and side (design/build.py `live_props`). DFS: the pool's salary is the price
the pool row prints, and the lineup a tap builds spends exactly those salaries. Both oracles are written here from the
inputs: the first from rows planted in the test, the second from tests/fixtures/data/dfs_pool.json."""
import json
import sys
from pathlib import Path

import pytest

from component import mount  # noqa: F401  (the fixture)
from wording import words

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "design"))
import build  # noqa: E402

POOL = json.loads((Path(__file__).parent / "fixtures" / "data" / "dfs_pool.json").read_text(encoding="utf-8"))


def pull(price, line, updated, side="Over"):
    return {"market": "RUSH", "player": "Chase Brown", "position": "RB", "team": "CIN", "side": side, "line": line,
            "price": price, "game": "CIN @ NYJ", "commence": "2026-09-13 17:00:00", "updated": updated, "book": "DraftKings"}


@pytest.fixture
def chase_brown(monkeypatch):
    """live_props over three pulls of one line, the newest first in the file: (-110 at 65.5 now), (-130 at 60.5 a day
    earlier), and the Under at 65.5 now. Returns Chase Brown's row."""
    rows = [pull(-110, 65.5, "2026-09-10 07:35:00"), pull(-130, 60.5, "2026-09-09 10:00:00"),
            pull(-112, 65.5, "2026-09-10 07:35:00", side="Under")]
    raw = {"props": rows, "source": "test", "fetched": "2026-09-10", "events": 1, "failed": []}
    for name, value in (("load_props_raw", (raw, "test")), ("load_model_raw", None), ("load_wrcb", None)):
        monkeypatch.setattr(build, name, lambda value=value: value)
    monkeypatch.setattr(build, "nfl_roster", lambda: {})
    return build.live_props(set(), {})["props"][0]


def test_s15_a_line_carries_the_newest_pull_per_book_and_side(chase_brown):
    assert chase_brown["books"]["DraftKings"] == {"over": -110, "line": 65.5, "under": -112}
    assert chase_brown["line"] == 65.5


@pytest.mark.render
def test_s15_the_dfs_pool_prints_its_salaries_and_a_tap_builds_the_lineup_from_them(mount):
    page, errors = mount("dfs", size=(1280, 900))
    burrow = next(p for p in POOL["players"] if p["name"] == "Joe Burrow")
    row = page.locator(".dfsrow", has_text=burrow["name"])
    assert row.locator(".pnum").first.inner_text() == f"${burrow['salary']}"
    row.click()
    slot = page.locator(".lslot:not(.vacant)", has_text=burrow["name"])
    assert slot.locator(".lsal").inner_text() == f"${burrow['salary']}"
    assert page.locator(".payrow", has_text=words("dfs.lineup.spent")).locator("b").inner_text() == f"${burrow['salary']}"
    assert errors == []
