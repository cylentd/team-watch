"""api/league.py `read_league`: the 60 s memo must never hand one visitor another's private league.

Nothing here touches the network; `fetch` is replaced.
"""

import importlib.util
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "api"))


def _load():
    spec = importlib.util.spec_from_file_location("league_memo_fn", REPO / "api" / "league.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lg = _load()


def _count_fetches(monkeypatch):
    calls = []

    def fake(lid, views, swid, s2, agent=None):
        calls.append((lid, swid, s2))
        return {"served_to": s2}

    monkeypatch.setattr(lg, "fetch", fake)
    lg._memo.clear()
    return calls


def test_a_different_cookie_for_the_same_private_league_reaches_espn(monkeypatch):
    calls = _count_fetches(monkeypatch)
    owner = lg.read_league({"lid": "1534545", "swid": "{A}", "s2": "owner-secret"})
    other = lg.read_league({"lid": "1534545", "swid": "{B}", "s2": "guess"})
    assert len(calls) == 2
    assert owner == {"served_to": "owner-secret"}
    assert other == {"served_to": "guess"}


def test_the_same_cookie_is_still_served_from_the_memo(monkeypatch):
    calls = _count_fetches(monkeypatch)
    e = {"lid": "1534545", "swid": "{A}", "s2": "owner-secret"}
    lg.read_league(e)
    lg.read_league(dict(e))
    assert len(calls) == 1


def test_a_public_league_is_still_shared_between_visitors(monkeypatch):
    calls = _count_fetches(monkeypatch)
    lg.read_league({"lid": "99", "swid": None, "s2": None})
    lg.read_league({"lid": "99", "swid": None, "s2": None})
    assert len(calls) == 1


def test_the_memo_key_never_holds_the_cookie_itself(monkeypatch):
    _count_fetches(monkeypatch)
    lg.read_league({"lid": "1", "swid": "{A}", "s2": "owner-secret"})
    assert "owner-secret" not in repr(list(lg._memo))
