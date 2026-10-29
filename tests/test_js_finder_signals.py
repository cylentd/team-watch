"""An offer card's "what changed since the price" lines (surface/finder/signals.js, 2026-10-29), in Node: ff-jarvis's
`trade_signals` writes a league's signals by slug into the offers file, and a card lists those on its players, the
facts the price lags first. The cases are the 2026-10-29 Yahoo trade talk: Rashee Rice back at practice while his price
still counted missed games, Braelon Allen filling in for Breece Hall, Garrett Wilson's falling target share."""
import pytest


@pytest.fixture(scope="module")
def sig(node_js):
    return node_js("surface/finder/signals.js")


def p(name, slug):
    return {"name": name, "slug": slug, "pos": "WR"}


def s(kind, text, stale):
    return {"kind": kind, "text": text, "stale": stale, "date": None, "nums": {}}


OFFER = {"send": [p("Jameson Williams", "jameson-williams"), p("Rashee Rice", "rashee-rice")],
         "get": [p("Garrett Wilson", "garrett-wilson"), p("Braelon Allen", "braelon-allen")]}
SIGS = {"jameson-williams": [s("role_news", "10-26: two TDs again", False)],
        "rashee-rice": [s("returning", "practiced (Wed LP)", True)],
        "garrett-wilson": [s("usage_down", "Target share 13% over his last 2", True), s("rumor", "10-28: Jets open to deals", False)],
        "braelon-allen": [s("starter_back", "Breece Hall is back at practice", True)]}


def test_the_lagging_facts_come_first_in_kind_order_and_a_card_shows_three(sig):
    got = sig("tfSignals", OFFER, SIGS)
    assert [(r["name"], r["kind"]) for r in got] == [
        ("Rashee Rice", "returning"), ("Braelon Allen", "starter_back"), ("Garrett Wilson", "usage_down")]
    assert all(r["stale"] for r in got)


def test_a_player_without_signals_or_an_unknown_kind_adds_nothing(sig):
    assert sig("tfSignals", OFFER, {}) == [] and sig("tfSignals", OFFER, None) == []
    assert sig("tfSignals", OFFER, {"rashee-rice": [s("vibes", "x", True)]}) == []


def test_facts_the_price_does_not_lag_still_show_when_there_is_room(sig):
    got = sig("tfSignals", OFFER, {"jameson-williams": SIGS["jameson-williams"], "garrett-wilson": SIGS["garrett-wilson"]})
    assert [r["kind"] for r in got] == ["usage_down", "rumor", "role_news"]


def test_the_lines_name_the_kind_and_the_player_and_mark_the_lagging_ones(sig):
    html = sig("tfSignalsHTML", OFFER, {"signals": SIGS})
    assert html.count('data-testid="finder-signal"') == 3 and html.count('class="tf-sig lag"') == 3
    assert "<b>Returning</b> R. Rice: practiced (Wed LP)" in html
    assert "<b>Starter back</b> B. Allen: Breece Hall is back at practice" in html


def test_a_file_from_before_the_signals_draws_no_line(sig):
    assert sig("tfSignalsHTML", OFFER, {}) == "" and sig("tfSignalsHTML", OFFER, None) == ""


def test_the_text_is_escaped(sig):
    html = sig("tfSignalsHTML", OFFER, {"signals": {"rashee-rice": [s("rumor", "<b>x</b>", False)]}})
    assert "&lt;b&gt;x&lt;/b&gt;" in html
