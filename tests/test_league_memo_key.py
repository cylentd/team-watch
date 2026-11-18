"""api/league.py's 60 s memo must never hand one visitor's private league to another."""
import importlib.util
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[1]


def _load():
    import sys
    sys.path.insert(0, str(REPO / "api"))
    spec = importlib.util.spec_from_file_location("league_memo_fn", REPO / "api" / "league.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lg = _load()


def _count_fetches(monkeypatch):
    calls = []
    monkeypatch.setattr(lg, "fetch", lambda lid, views, swid, s2, agent=None: calls.append((swid, s2)) or {"s2": s2})
    lg._memo.clear()
    return calls


def test_a_different_s2_never_reads_anothers_cached_league(monkeypatch):
    calls = _count_fetches(monkeypatch)
    owner = lg.read_league({"lid": "1", "swid": "{A}", "s2": "owner-secret"})
    other = lg.read_league({"lid": "1", "swid": "{B}", "s2": "guess"})
    assert len(calls) == 2
    assert other == {"s2": "guess"} and owner == {"s2": "owner-secret"}


def test_the_same_credentials_still_share_the_memo(monkeypatch):
    calls = _count_fetches(monkeypatch)
    e = {"lid": "1", "swid": "{A}", "s2": "owner-secret"}
    lg.read_league(e)
    lg.read_league(dict(e))
    assert len(calls) == 1


def test_a_different_swid_with_the_same_s2_is_a_separate_entry(monkeypatch):
    calls = _count_fetches(monkeypatch)
    lg.read_league({"lid": "1", "swid": "{A}", "s2": "x"})
    lg.read_league({"lid": "1", "swid": "{B}", "s2": "x"})
    assert len(calls) == 2


def test_public_leagues_share_one_entry(monkeypatch):
    calls = _count_fetches(monkeypatch)
    lg.read_league({"lid": "1"})
    lg.read_league({"lid": "1", "swid": None, "s2": None})
    assert len(calls) == 1
