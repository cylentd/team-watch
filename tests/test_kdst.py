"""design/kdst.py: LIVE_KDST, each club's D/ST and K points per played game (2026-10-07), from ff-jarvis's
gamelog_kdst.json in the jobs data dir (file only, not in the feed). Without the file the K and D/ST backs
keep the facts they had."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "design"))
import contract  # noqa: E402
import kdst  # noqa: E402
import sources  # noqa: E402

ROW = {"week": 1, "opp": "LAC", "home": False, "dst_espn": 13.0, "dst_yahoo": 10.0, "k_yahoo": 16.4, "k_ayo": 16.0, "kickers": ["C.Ryland"]}
RAW = {"generated": "2026-10-07T13:38", "season": 2026, "through_week": 4, "teams": {"ARI": [ROW]}}


def test_the_block_passes_the_file_through():
    assert kdst.live_kdst(RAW) == RAW


@pytest.mark.parametrize("raw", [None, {}, {"teams": {}}])
def test_no_file_or_no_teams_is_no_block(raw):
    assert kdst.live_kdst(raw) is None


def test_the_loader_reads_the_jobs_data_file_and_a_missing_one_is_none(tmp_path, monkeypatch):
    monkeypatch.setattr(sources, "DWR", tmp_path)
    assert kdst.load_kdst() is None
    (tmp_path / "gamelog_kdst.json").write_text('{"teams": {"ARI": []}}', encoding="utf-8")
    assert kdst.load_kdst() == {"teams": {"ARI": []}}


def test_a_row_missing_a_field_the_page_reads_fails_the_contract():
    bad = {**RAW, "teams": {"ARI": [{k: v for k, v in ROW.items() if k != "k_ayo"}]}}
    assert contract.problems("LIVE_KDST", bad) == ["LIVE_KDST['ARI'][0].k_ayo"]


def test_a_whole_row_passes_the_contract():
    assert contract.problems("LIVE_KDST", RAW) == []
