"""S15 (David approved 2026-10-31): All lines prints the current build's price. test_s15_prices.py proves the build keeps
the newest pull per book and side; this file reads what the page prints. The oracle is the props fixture itself: of every
pull of a player's Over at DraftKings in a market, the newest `updated` is the price on the screen. Chase Brown's rush
line has two pulls (-130 on 2026-09-09, -110 on 2026-09-10), so a page that printed the older pull would show -130."""
import json
from pathlib import Path

import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.build_prices import BuildPrices

PULLS = json.loads((Path(__file__).parent / "fixtures" / "data" / "bettingpros_props.json").read_text(encoding="utf-8"))["props"]
LINES = [("Chase Brown", "RUSH"), ("Joe Burrow", "PASS"), ("Tee Higgins", "REC"), ("George Kittle", "REC"), ("Brock Purdy", "PASS")]


@pytest.mark.render
@pytest.mark.parametrize("player,market", LINES)
def test_all_lines_prints_the_newest_pull_for_the_book_and_side(mount, player, market):
    pulls = [r for r in PULLS if (r["player"], r["market"], r["book"], r["side"]) == (player, market, "DraftKings", "Over")]
    newest = max(pulls, key=lambda r: r["updated"])["price"]      # American odds print with a sign: "-110", "+160"
    lines, errors = BuildPrices.open_dk(mount)
    assert lines.printed_price(player, market) == f"{newest:+d}", (player, market)
    assert errors == []
