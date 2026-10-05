"""design/recap.py, LIVE_RECAP (2026-10-05): ff-jarvis's weekly recap file cut for This week > Recap. The
fixture (tests/fixtures/data/recap/2026-w04.json) is the real week-4 file with eight of sixteen games final;
its players carry `rostered` and `slot` and it carries `leagues`, which must never reach the page."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "design"))
import contract  # noqa: E402
from recap import live_recap, pick_week  # noqa: E402
from sources import DWR, load_recaps  # noqa: E402

PRIVATE = {"leagues", "rostered", "slot"}


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def raw():
    return json.loads((DWR / "recap" / "2026-w04.json").read_text(encoding="utf-8"))


def block():
    b = live_recap(load_recaps(), slug)
    contract.validate("LIVE_RECAP", b)
    return b


def keys_of(x):
    """Every dict key anywhere inside x."""
    if isinstance(x, dict):
        return set(x) | set().union(*(keys_of(v) for v in x.values()))
    if isinstance(x, list):
        return set().union(*(keys_of(v) for v in x))
    return set()


def old_file():
    """Week 4 as ff-jarvis wrote weeks 1-3: none of the fields added 2026-10-05."""
    r = raw()
    for k in ("games", "preview_record", "k_dst", "left_hurt"):
        del r[k]
    for p in r["players"]:
        for k in ("pass_td", "rush_td", "rec_td", "ret_td", "line"):
            del p[k]
    return r


# --------------------------------------------------------------------------- privacy

def test_the_fixture_holds_the_private_fields_so_the_check_means_something():
    r = raw()
    assert PRIVATE <= keys_of(r)
    assert all("rostered" in p and "slot" in p for p in r["players"])


def test_the_block_holds_no_private_field():
    assert not PRIVATE & keys_of(block())
    assert not PRIVATE & keys_of(live_recap([old_file()], slug))


def test_the_injected_page_holds_no_private_field(built):
    line = next(x for x in built.page.split("\n") if x.startswith("const LIVE_RECAP = "))
    assert not PRIVATE & keys_of(json.loads(line[len("const LIVE_RECAP = "):-1]))
    for word in PRIVATE:
        assert f'"{word}"' not in line


# --------------------------------------------------------------------------- the block

def test_the_week_is_the_files_and_half_its_games_are_final():
    b = block()
    assert (b["season"], b["week"], b["n_final"], b["n_games"]) == (2026, 4, 8, 16)
    assert [g["final"] for g in b["games"]].count(True) == 8
    final = next(g for g in b["games"] if g["game_id"] == "2026_04_PIT_CLE")
    assert (final["away_pts"], final["home_pts"]) == (24.0, 27.0)
    assert final["preview"]["su_hit"] is True and final["preview"]["frozen"] is True
    assert all(g["preview"]["su_hit"] is None for g in b["games"] if not g["final"])
    assert b["preview_record"]["n"] == 8


def test_top_three_per_position_in_the_files_order():
    b = block()
    for pos in ("QB", "RB", "WR", "TE"):
        got = [r["n"] for r in b["stars"] if r["pos"] == pos]
        want = [p["name"] for p in raw()["players"] if p["key"] in raw()["standouts"][pos][:3]]
        assert len(got) == 3 and sorted(got) == sorted(want)
    assert [r["pos"] for r in b["stars"]] == ["QB"] * 3 + ["RB"] * 3 + ["WR"] * 3 + ["TE"] * 3


def test_k_and_dst_top_three_biggest_score_first():
    b = block()
    for rows in (b["k"], b["dst"]):
        assert len(rows) == 3
        assert [r["actual"] for r in rows] == sorted((r["actual"] for r in rows), reverse=True)
    assert b["k"][0]["n"] == "Andre Szmyt" and b["k"][0]["slug"] == "andre-szmyt"
    assert b["dst"][0]["n"] == "BUF" and b["dst"][0]["slug"] is None, "a defense has no face"


def test_smashed_beat_the_projection_and_are_not_already_a_star():
    b = block()
    stars = {r["slug"] for r in b["stars"]}
    assert b["smashed"] and len(b["smashed"]) <= 5
    assert all(r["diff"] >= 8 and r["slug"] not in stars for r in b["smashed"])
    assert [r["diff"] for r in b["smashed"]] == sorted((r["diff"] for r in b["smashed"]), reverse=True)


def test_busts_are_the_files_list_in_its_order():
    names = {p["key"]: p["name"] for p in raw()["players"]}
    assert [r["n"] for r in block()["busts"]] == [names[k] for k in raw()["busts"]]


def test_touchdown_leaders_count_every_kind_and_sort_by_total_then_points():
    b = block()
    rows = b["tds"]
    assert all(r["td"] == sum(r[k] or 0 for k in ("pass_td", "rush_td", "rec_td", "ret_td")) > 0 for r in rows)
    assert [(-r["td"], -r["actual"]) for r in rows] == sorted((-r["td"], -r["actual"]) for r in rows)
    assert rows[0]["n"] == "Josh Allen" and rows[0]["td"] == 4
    assert any(r["ret_td"] for r in rows), "a returner's touchdown counts"
    assert len(rows) == 30 < sum(1 for p in raw()["players"] if p["pass_td"] or p["rush_td"] or p["rec_td"] or p["ret_td"]), \
        "the list is capped, the biggest days kept"


def test_the_top_scorer_carries_his_structured_line():
    top = block()["top"]
    assert top["n"] == "Josh Allen" and top["actual"] == 33.5
    assert top["line"]["pass_yd"] == 285 and top["line"]["pass_td"] == 3


def test_left_hurt_rows_are_the_digests_cut():
    row = next(r for r in block()["left_hurt"] if r["n"] == "Lamar Jackson")
    assert row["injury"] == "ankle" and row["rest"] == "questionable to return" and row["slug"] == "lamar-jackson"
    assert row["later"] == "considered day-to-day"


# --------------------------------------------------------------------------- old files and no file

def test_a_file_from_before_the_new_fields_builds_a_whole_block():
    b = live_recap([old_file()], slug)
    contract.validate("LIVE_RECAP", b)
    assert b["week"] == 4 and (b["n_final"], b["n_games"]) == (8, 16), "the finals come from `slate`, the rest from `pending`"
    assert len(b["games"]) == 8 and all(g["final"] and g["preview"] is None for g in b["games"]), "finals only, no Preview call"
    assert b["preview_record"] is None and b["k"] == [] and b["dst"] == [] and b["left_hurt"] == []
    assert b["tds"] == [] and b["top"]["line"] is None and b["top"]["pass_td"] is None
    assert len(b["stars"]) == 12


def test_no_file_is_no_block():
    assert live_recap([], slug) is None
    contract.validate("LIVE_RECAP", None)


def test_the_newest_week_with_half_its_games_final_wins():
    mk = lambda w, done, total: {"week": w, "games": [{"final": i < done} for i in range(total)]}
    assert pick_week([mk(5, 1, 16), mk(4, 8, 16), mk(3, 16, 16)])["week"] == 4, "one Thursday game is not a week"
    assert pick_week([mk(5, 1, 16), mk(4, 7, 16)])["week"] == 5, "none qualifies: the newest file"
    old = {"week": 3, "slate": [{}] * 9, "pending": [0] * 7}
    assert pick_week([mk(4, 3, 16), old])["week"] == 3, "an old file counts its slate and its pending"
    assert pick_week([]) is None


def test_the_block_stays_small():
    n = len(json.dumps(block()))
    assert n < 30_000, f"LIVE_RECAP is {n} bytes"
