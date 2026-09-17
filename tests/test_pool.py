"""design/pool.py: the Pool page's rows from watch.json's league-wide pool (fixture)."""
import json
import re

from build import slugify
import pool


def _pool(built):
    m = re.search(r"^const LIVE_POOL = (.*);$", built.fragment, re.M)
    return json.loads(m.group(1).replace("<\\/", "</"))


def test_ranked_by_role_share_with_the_verdicts_own_share_move(built):
    p = _pool(built)
    assert [r["n"] for r in p["players"]] == ["Chase Brown", "Kalif Raymond", "George Kittle", "Dontayvion Wicks"]
    brown = p["players"][0]
    assert (brown["share"], brown["dShare"]) == (62.0, 15.2), "a back's role is his carry share"
    assert brown["luck"] == -18, "watch's ratio, as percent"
    assert p["trended"] == 3, "Kittle has one week, so no move to plot"


def test_availability_comes_from_rostered_by(built):
    rows = {r["n"]: r for r in _pool(built)["players"]}
    assert rows["Chase Brown"]["mine"] is True
    assert rows["Kalif Raymond"]["leagues"] == {"espn": None, "yahoo": None}
    assert rows["Dontayvion Wicks"]["leagues"] == {"espn": "Team 3", "yahoo": None}
    assert rows["Dontayvion Wicks"]["mine"] is False


def test_a_quarterbacks_role_is_his_snaps_and_he_ranks_after_skill_players():
    usage = {"through_week": 1, "leagues": [], "pool": [
        {"name": "Drew Lock", "pos": "QB", "team": "SEA", "snap": 90.0, "d_snap": 5.0, "tgt": 0.0, "car": 9.1,
         "d_tgt": 0.0, "d_car": 2.0, "opp": 30, "luck": 0.1, "verdict": "hold", "rostered_by": []},
        {"name": "Back Up", "pos": "RB", "team": "SEA", "snap": 30.0, "car": 20.0, "opp": 8, "rostered_by": []}]}
    rows = pool.live_pool(usage, slugify)["players"]
    assert [r["n"] for r in rows] == ["Back Up", "Drew Lock"]
    assert (rows[1]["share"], rows[1]["dShare"]) == (90.0, 5.0)


def test_no_pool_is_none_so_the_page_keeps_its_sample():
    assert pool.live_pool({"pool": []}, slugify) is None
    assert pool.live_pool(None, slugify) is None
