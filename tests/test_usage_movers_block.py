"""The Digest-by-day blocks (2026-10-06), data side only: LIVE_USAGE_MOVERS (design/usage_movers.py), LIVE_DIGEST.gains
and hurt[].practice (design/digest.py), and K in LIVE_SOS (design/sos.py). ff-jarvis writes the files on its own
schedule; until it does every block is absent, and the build must still pass."""
import copy
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "design"))
import audit_blocks  # noqa: E402
import contract  # noqa: E402
import sources  # noqa: E402
from _espn import slugify  # noqa: E402
from digest import live_digest  # noqa: E402
from sos import live_sos  # noqa: E402
from usage_movers import live_usage_movers, load_usage_movers  # noqa: E402

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "data" / "usage_movers.json").read_text(encoding="utf-8"))


def _block():
    return live_usage_movers(load_usage_movers())


# ---- LIVE_USAGE_MOVERS ----

@pytest.mark.req("Digest", ac="usage movers come from the fixture file")
def test_usage_movers_are_cut_from_the_fixture_and_pass_the_contract():
    b = _block()
    assert contract.problems("LIVE_USAGE_MOVERS", b) == []
    assert (b["season"], b["week"], b["from_week"], b["to_week"], b["llm"]) == (2026, 4, 3, 4, "ok")
    assert [r["slug"] for r in b["rows"]] == ["bijan-robinson", "harold-fannin-jr"], "the file's order, biggest change first"
    bijan = b["rows"][0]
    assert (bijan["metric"], bijan["was"], bijan["now"], bijan["change"], bijan["spark"]) == ("snap", 55.0, 78.0, 23.0, [55.0, 55.0, 78.0])
    assert bijan["carries"] == 15 and bijan["teammate"] is None
    assert b["rows"][1]["teammate"] == {"name": "David Njoku", "was": 24.0, "now": 12.0}


@pytest.mark.req("Digest", ac="usage movers show Claude's line, else the template fact")
def test_a_row_shows_claudes_line_and_falls_back_to_the_fact():
    raw = copy.deepcopy(FIXTURE)
    raw["rows"][0]["line"] = ""
    b = live_usage_movers(raw)
    assert b["rows"][0]["line"] == FIXTURE["rows"][0]["fact"], "no line: the template fact"
    assert b["rows"][1]["line"] == FIXTURE["rows"][1]["line"], "Claude's line wins over the fact"


@pytest.mark.req("Digest", ac="the page only gets the fields it reads")
def test_a_row_drops_the_checked_numbers():
    row = _block()["rows"][0]
    assert "nums" not in row, "nums are the producer's check of its own line, not the page's"


def test_the_build_injects_the_block_from_the_fixture(built):
    m = re.search(r"^const LIVE_USAGE_MOVERS = (.*);$", built.fragment, re.M)
    assert m, "LIVE_USAGE_MOVERS is not injected"
    assert json.loads(m.group(1).replace("<\\/", "</")) == _block()


@pytest.mark.req("Digest", ac="no usage movers file builds and says none")
def test_no_file_is_null_and_the_build_step_says_so(tmp_path, monkeypatch):
    monkeypatch.setattr(sources, "DWR", tmp_path)
    monkeypatch.setattr(sources, "FEED", tmp_path / "no_feed.json")
    assert load_usage_movers() is None
    blocks, report = {}, []
    audit_blocks.add_audit_blocks(blocks, report)
    assert blocks["LIVE_USAGE_MOVERS"] is None
    line = next(l for l in report if l.startswith("Usage movers"))
    assert "falls back" not in line and "no live file" not in line, "an absent file is not a stale-source warning"
    contract.validate("LIVE_USAGE_MOVERS", None)


def test_the_build_report_names_the_week_and_the_rows():
    from usage_movers import report
    assert report(_block()) == "Usage movers: week 4, 2 rows"


def test_the_feed_block_is_read_before_the_file(tmp_path, monkeypatch):
    feed = tmp_path / "feed.json"
    from_feed = {**FIXTURE, "week": 9}
    feed.write_text(json.dumps({"usage_movers": {"data": from_feed, "fetched": "x"}}), encoding="utf-8")
    monkeypatch.setattr(sources, "FEED", feed)
    assert load_usage_movers()["week"] == 9


def test_a_file_with_no_rows_is_a_block_with_no_rows():
    b = live_usage_movers({**FIXTURE, "rows": []})
    assert b["rows"] == [] and contract.problems("LIVE_USAGE_MOVERS", b) == []


@pytest.mark.parametrize("field", ["slug", "name", "now", "change", "spark", "was", "metric", "pos", "team"])
def test_the_contract_names_a_row_field_the_page_reads(field):
    b = _block()
    del b["rows"][1][field]
    assert contract.problems("LIVE_USAGE_MOVERS", b) == [f"LIVE_USAGE_MOVERS.rows[1].{field}"]


def test_a_producer_row_missing_a_field_fails_in_the_cut_not_as_null():
    """The cut keeps only what the file has, so a dropped `now` fails the contract by name instead of drawing a blank."""
    raw = copy.deepcopy(FIXTURE)
    del raw["rows"][0]["now"]
    assert contract.problems("LIVE_USAGE_MOVERS", live_usage_movers(raw)) == ["LIVE_USAGE_MOVERS.rows[0].now"]


def test_a_row_with_neither_line_nor_fact_fails_the_contract():
    raw = copy.deepcopy(FIXTURE)
    raw["rows"][0]["line"] = ""
    raw["rows"][0]["fact"] = ""
    assert contract.problems("LIVE_USAGE_MOVERS", live_usage_movers(raw)) == ["LIVE_USAGE_MOVERS.rows[0].line"]


def test_a_spark_that_is_not_three_weeks_fails_the_contract():
    b = _block()
    b["rows"][0]["spark"] = [55.0, 78.0]
    assert contract.problems("LIVE_USAGE_MOVERS", b) == ["LIVE_USAGE_MOVERS.rows[0].spark"]


def test_a_teammate_missing_a_number_fails_the_contract():
    b = _block()
    del b["rows"][1]["teammate"]["now"]
    assert contract.problems("LIVE_USAGE_MOVERS", b) == ["LIVE_USAGE_MOVERS.rows[1].teammate.now"]


def test_the_block_missing_its_rows_fails_the_contract():
    b = _block()
    del b["rows"]
    assert "LIVE_USAGE_MOVERS.rows" in contract.problems("LIVE_USAGE_MOVERS", b)


# ---- LIVE_DIGEST.gains and hurt[].practice ----

GAIN = {"out": {"key": "puka nacua", "slug": "puka-nacua", "name": "Puka Nacua", "pos": "WR", "team": "LA", "status": "Out", "injury": "Hip"},
        "next": {"key": "xavier smith", "slug": "xavier-smith", "name": "Xavier Smith", "pos": "WR", "team": "LA", "depth": 2,
                 "snap_last": 61.0, "tgt_pct_last": 14.5, "carries_last": None, "targets_last": 5}}
PRACTICE = [{"day": "Wed", "mark": "DNP"}, {"day": "Thu", "mark": "LP"}, {"day": "Fri", "mark": None}]


def _packet():
    return json.loads((Path(__file__).parent / "fixtures" / "data" / "weekly_digest.json").read_text(encoding="utf-8"))


def _old_packet():
    """The fixture as ff-jarvis wrote it before gains and practice marks (2026-10-06)."""
    raw = _packet()
    raw.pop("gains", None)
    for r in raw["hurt"]:
        r.pop("practice", None)
    return raw


def _digest(raw):
    return live_digest(raw, slugify, None)


@pytest.mark.req("Digest", ac="gains pass through from the packet")
def test_gains_pass_through_with_their_next_man():
    raw = _packet()
    raw["gains"] = [GAIN, {"out": GAIN["out"], "next": None}]
    b = _digest(raw)
    assert b["gains"] == [GAIN, {"out": GAIN["out"], "next": None}]
    assert contract.problems("LIVE_DIGEST", b) == []


def test_a_packet_from_before_gains_has_none():
    b = _digest(_old_packet())
    assert b["gains"] == [] and contract.problems("LIVE_DIGEST", b) == []


def test_the_cut_keeps_only_the_gain_fields_the_page_reads():
    raw = _packet()
    raw["gains"] = [{"out": {**GAIN["out"], "extra": 1}, "next": {**GAIN["next"], "extra": 1}, "why": "x"}]
    g = _digest(raw)["gains"][0]
    assert set(g) == {"out", "next"} and "extra" not in g["out"] and "extra" not in g["next"]


@pytest.mark.req("Digest", ac="practice marks pass through on each hurt row")
def test_practice_passes_through_on_a_hurt_row_and_is_empty_without():
    raw = _old_packet()
    raw["hurt"][0]["practice"] = PRACTICE
    b = _digest(raw)
    assert b["hurt"][0]["practice"] == PRACTICE, "the null mark stays: no report logged that day"
    assert b["hurt"][1]["practice"] == [], "a packet from before practice has no marks, and the page draws none"
    assert contract.problems("LIVE_DIGEST", b) == []


@pytest.mark.parametrize("path,drop", [
    (("gains", 0, "out"), "slug"), (("gains", 0, "out"), "name"), (("gains", 0, "out"), "status"),
    (("gains", 0, "next"), "slug"), (("gains", 0, "next"), "depth"),
])
def test_the_contract_names_a_gain_field_the_page_reads(path, drop):
    raw = _packet()
    raw["gains"] = [copy.deepcopy(GAIN)]
    b = _digest(raw)
    del b[path[0]][path[1]][path[2]][drop]
    assert contract.problems("LIVE_DIGEST", b) == [f"LIVE_DIGEST.gains[0].{path[2]}.{drop}"]


def test_a_gain_with_no_out_or_next_key_fails_the_contract():
    raw = _packet()
    raw["gains"] = [copy.deepcopy(GAIN)]
    b = _digest(raw)
    del b["gains"][0]["next"]
    b["gains"][0]["out"] = None
    assert contract.problems("LIVE_DIGEST", b) == ["LIVE_DIGEST.gains[0].next", "LIVE_DIGEST.gains[0].out"]


@pytest.mark.parametrize("drop", ["day", "mark"])
def test_the_contract_names_a_practice_entry_missing_day_or_mark(drop):
    raw = _packet()
    raw["hurt"][0]["practice"] = copy.deepcopy(PRACTICE)
    b = _digest(raw)
    del b["hurt"][0]["practice"][1][drop]
    assert contract.problems("LIVE_DIGEST", b) == [f"LIVE_DIGEST.hurt[0].practice[1].{drop}"]


def test_a_hurt_row_with_no_practice_key_fails_the_contract():
    b = _digest(_packet())
    del b["hurt"][2]["practice"]
    assert contract.problems("LIVE_DIGEST", b) == ["LIVE_DIGEST.hurt[2].practice"]


def test_a_missing_gains_key_fails_the_contract():
    b = _digest(_packet())
    del b["gains"]
    assert contract.problems("LIVE_DIGEST", b) == ["LIVE_DIGEST.gains"]


# ---- LIVE_SOS gains K ----

K_WIN = {"games": 4, "pts_pg": 8.1, "current": 8.4, "prior": 7.9, "avg_def_rank": 15.0, "rank": 9}
K_BLOCK = {"scoring": "Yahoo kicker points", "prior_season": 2025, "prior_used": True, "note": "from play-by-play"}


def _sos():
    return json.loads((Path(__file__).parent / "fixtures" / "data" / "sos.json").read_text(encoding="utf-8"))


@pytest.mark.req("Schedule", ac="K passes through with the file")
def test_k_rows_and_the_k_note_pass_through_in_live_sos():
    raw = _sos()
    for t in raw["teams"].values():
        t["K"] = {w: dict(K_WIN) for w in ("next4", "ros", "playoffs")}
    raw["k"] = K_BLOCK
    raw["source"] = {**raw["source"], "k_play_by_play": ["pbp_2026.parquet", "pbp_2025.parquet"]}
    b = live_sos(raw)
    assert all(t["K"]["next4"] == K_WIN for t in b["teams"].values())
    assert b["k"] == K_BLOCK
    assert b["source"] == {"k_play_by_play": ["pbp_2026.parquet", "pbp_2025.parquet"]}, "the page keeps the K source, not the file paths"
    assert contract.problems("LIVE_SOS", b) == []


def test_a_k_row_may_have_null_numbers():
    raw = _sos()
    nulls = {k: None for k in K_WIN}
    for t in raw["teams"].values():
        t["K"] = {w: {**nulls, "games": 3} for w in ("next4", "ros", "playoffs")}
    assert contract.problems("LIVE_SOS", live_sos(raw)) == []


def _old_sos():
    """The fixture as ff-jarvis wrote it before kickers (2026-10-06)."""
    raw = _sos()
    raw.pop("k", None)
    raw.pop("source", None)
    raw.pop("k_allowed", None)
    for t in raw["teams"].values():
        t.pop("K", None)
    return raw


def test_a_file_with_no_k_has_no_k_rows():
    b = live_sos(_old_sos())
    assert b["k"] is None and b["source"] is None and b["k_allowed"] is None
    assert all("K" not in t for t in b["teams"].values())
    assert contract.problems("LIVE_SOS", b) == []


def test_the_contract_names_a_k_window_missing_a_field():
    raw = _sos()
    team = sorted(raw["teams"])[0]
    for t in raw["teams"].values():
        t["K"] = {w: dict(K_WIN) for w in ("next4", "ros", "playoffs")}
    del raw["teams"][team]["K"]["ros"]["rank"]
    assert contract.problems("LIVE_SOS", live_sos(raw)) == [f"LIVE_SOS.teams[{team!r}].K.ros.rank"]


@pytest.mark.req("Schedule", ac="k_allowed passes through with the file")
def test_k_allowed_passes_through_for_all_32_defenses_and_passes_the_contract():
    raw = _sos()
    b = live_sos(raw)
    assert b["k_allowed"] == raw["k_allowed"]
    assert sorted(b["k_allowed"]) == sorted(raw["teams"]) and len(b["k_allowed"]) == 32
    assert sorted(e["rank"] for e in b["k_allowed"].values()) == list(range(1, 33))
    assert contract.problems("LIVE_SOS", b) == []


def test_the_contract_names_a_k_allowed_entry_missing_a_field():
    raw = _sos()
    team = sorted(raw["k_allowed"])[0]
    del raw["k_allowed"][team]["rank"]
    assert contract.problems("LIVE_SOS", live_sos(raw)) == [f"LIVE_SOS.k_allowed[{team!r}].rank"]
