"""League > Trade history's Best and Worst trader cards are about the person (2026-11-01, David chose "People vs
trades"): on ESPN the best trader's biggest win, the worst trader's biggest loss and Heist #1 were one trade, drawn
three times in a row of five. Only heists show a trade now; a lead card shows its manager's closed trades as a strip.

The block is planted through `league_trades.live_trades`, as in tests/test_espn_tradehist.py. Worked by hand:

    id  when       sides, held PAR   held result     tree
    0   2022 wk 9  ace 80, zed 10    ace +70         the biggest trade, so Heist #1, and both leads' old proof
    1   2021 wk 3  ace 5, bo 9       bo +4
    2   2023 wk 4  ace 7, cy 7       tie
    3   2023 wk 2  ace 30, di 5      ace +25
    4   2024 wk 5  ace 1, zed 2      open, no mark
    5   2021 wk 5  zed 2, bo 8       bo +6
    6   2022 wk 2  zed 6, cy 3       zed +3
    7   2023 wk 7  zed 1, di 9       di +8

    ace, oldest first: L W W T, 2-1-1; zed: L W L L, 1-3. bo, cy and di have too few trades to rank.
"""
import pytest

import league_trades as T
from component import mount  # noqa: E402,F401  (the fixture)
from pages.league_chip import pick_script  # noqa: E402
from pages.tradehist import TradeHistoryPage  # noqa: E402
from pages.tradehist_lead import TradeHistoryLead  # noqa: E402
from pages.tradehist_text import TradeHistoryText  # noqa: E402
from wording import words  # noqa: E402

PHONE, DESKTOP = (360, 740), (1280, 900)
LINE_GAP = 4     # px: the strip's 3px gap, plus the 1 that rounding two tops can add
NAMES = {"ace": "Ace", "zed": "Zed", "bo": "Bo", "cy": "Cy", "di": "Di"}
W, L, TIE = words("trades.res.w"), words("trades.res.l"), words("trades.res.t")


def filled(key, **values):
    """A content.json line as the page prints it, its {slots} filled."""
    return words(key).format(**values)


def side(m, par, tree, player):
    return {"manager": m, "players": [{"name": player}], "par": par, "tree": tree, "after": "8-6"}


def trade(season, week, a, b, margin, open_=False):
    return {"season": season, "week": week, "open": open_, "margin": margin, "sides": [side(*a), side(*b)]}


def manager(trades, won, lost, per_trade):
    return {"trades": trades, "won": won, "lost": lost, "per_trade": per_trade, "lo": per_trade - 5, "hi": per_trade + 5, "shrunk": per_trade}


TRADES = [trade(2022, 9, ("ace", 80, 90, "Alan Shared"), ("zed", 10, 5, "Zack Shared"), 85.0),
          trade(2021, 3, ("ace", 5, 6, "Abe Two"), ("bo", 9, 9, "Bob Two"), 3.0),
          trade(2023, 4, ("ace", 7, 10, "Ann Tied"), ("cy", 7, 8, "Cal Tied"), 2.0),
          trade(2023, 2, ("ace", 30, 30, "Art Three"), ("di", 5, 5, "Dan Three"), 25.0),
          trade(2024, 5, ("ace", 1, 1, "Amy Open"), ("zed", 2, 2, "Zoe Open"), 1.0, open_=True),
          trade(2021, 5, ("zed", 2, 2, "Zip Five"), ("bo", 8, 8, "Ben Five"), 6.0),
          trade(2022, 2, ("zed", 6, 6, "Zev Six"), ("cy", 3, 3, "Cam Six"), 3.0),
          trade(2023, 7, ("zed", 1, 1, "Zac Seven"), ("di", 9, 9, "Don Seven"), 8.0)]
MANAGERS = {"ace": manager(4, 2, 1, 22.5), "zed": manager(4, 1, 3, -21.3), "bo": manager(2, 2, 0, 5.0),
            "cy": manager(2, 0, 1, -1.5), "di": manager(2, 1, 1, 8.5)}


def planted(trades=TRADES, managers=MANAGERS):
    return T.live_trades({"trades": trades, "managers": managers, "curses": []}, {"managers": NAMES}, skip=frozenset(), key="espn")


def busy():
    """Ace with 25 closed trades, the most the strip is built for; Zed as before."""
    many = [trade(2000 + i, 1, ("ace", 9, 9, f"Al Many{i}"), ("bo", 1, 1, f"Bea Many{i}"), 8.0) for i in range(24)]
    return planted(TRADES[5:] + [TRADES[0]] + many, {**MANAGERS, "ace": manager(25, 25, 0, 30.0)})


def open_lead(mount, block, size=PHONE):
    page, errors = mount("tradehist", size=size, init=(pick_script("espn"),))
    TradeHistoryText(page).plant_and_open(block)
    return page, errors, TradeHistoryLead(page)


@pytest.mark.req("Trade history", ac="a lead card is about the person: no trade rows, no players, no foot")
@pytest.mark.parametrize("kind", ["best", "worst"])
def test_a_lead_card_draws_no_trade(mount, kind):
    _, errors, lead = open_lead(mount, planted())
    card = lead.card(kind)
    assert (card["tradeRows"], card["faces"], card["foot"]) == (0, 0, 0), "the person, not a trade"
    assert errors == []


@pytest.mark.req("Trade history", ac="the name headline and the deck stay")
def test_a_lead_card_keeps_its_headline_and_its_deck(mount):
    _, errors, lead = open_lead(mount, planted())
    best, worst = lead.card("best"), lead.card("worst")
    assert best["head"] == filled("trades.lead.wins", m="Ace")
    assert best["deck"] == filled("trades.lead.deck", n="+22.5", wl="2–1–1")
    assert best["n"] == filled("trades.lead.n", n=4)
    assert worst["head"] == filled("trades.lead.due", m="Zed")
    assert worst["deck"] == filled("trades.lead.deck", n="−21.3", wl="1–3")
    assert errors == []


@pytest.mark.req("Trade history", ac="one mark per closed trade, oldest to newest, open trades left out")
def test_the_strip_is_the_managers_closed_trades_oldest_first(mount):
    _, errors, lead = open_lead(mount, planted())
    assert lead.card("best")["marks"] == [L, W, W, TIE], "2021 lost, 2022 won, 2023 week 2 won, 2023 week 4 tied; 2024 open"
    assert lead.card("worst")["marks"] == [L, W, L, L], "2021 lost, 2022 week 2 won, 2022 week 9 lost, 2023 lost; 2024 open"
    assert errors == []


@pytest.mark.req("Trade history", ac="not colour alone: a letter, a colour and a label for a screen reader")
def test_each_mark_carries_a_letter_and_the_strip_says_its_count(mount):
    _, errors, lead = open_lead(mount, planted())
    assert lead.mark_kinds("best") == [["dn", L], ["up", W], ["up", W], ["open", TIE]]
    best, worst = lead.card("best"), lead.card("worst")
    assert best["role"] == "img"
    assert best["aria"] == filled("trades.lead.formAriaTied", w=2, l=1, t=1)
    assert worst["aria"] == filled("trades.lead.formAria", w=1, l=3)
    assert errors == []


@pytest.mark.req("Trade history", ac="no trade repeats in the row when best, worst and Heist #1 share one")
@pytest.mark.parametrize("size", [PHONE, DESKTOP], ids=["phone", "desktop"])
def test_the_trade_best_worst_and_heist_one_share_is_drawn_once(mount, size):
    _, errors, lead = open_lead(mount, planted(), size)
    cards = lead.top_row()
    assert [c["lead"] for c in cards] == [True, True, False, False, False]
    assert [c["players"] for c in cards[:2]] == [[], []]
    players = [p for c in cards for p in c["players"]]
    assert "A. Shared" in cards[2]["players"], "the shared trade is Heist #1"
    assert len(players) == len(set(players)), players
    assert errors == []


@pytest.mark.req("Trade history", ac="Yahoo's cards are the same cards")
def test_a_yahoo_reader_gets_the_strip_too(mount):
    page, errors = mount("tradehist", size=PHONE, init=(pick_script("yahoo"),))
    TradeHistoryText(page).plant_and_open(planted())
    lead = TradeHistoryLead(page)
    assert lead.has_strip("best") and lead.has_strip("worst")
    assert [p for c in lead.top_row()[:2] for p in c["players"]] == []
    assert errors == []


@pytest.mark.req("Trade history", ac="25 trades fit one or two lines at 360px")
@pytest.mark.parametrize("size", [PHONE, DESKTOP], ids=["phone", "desktop"])
def test_a_busy_managers_strip_fits_two_lines(mount, size):
    _, errors, lead = open_lead(mount, busy(), size)
    fit = lead.strip_lines("best")
    assert len(lead.card("best")["marks"]) == 25
    assert fit["lines"] == 2 and fit["over"] <= 0.5, fit
    assert errors == []


@pytest.mark.req("Trade history", ac="a busy strip's marks stay square and its two lines read as one strip")
@pytest.mark.parametrize("size", [PHONE, DESKTOP], ids=["phone", "desktop"])
def test_a_busy_managers_marks_stay_square_and_close(mount, size):
    _, errors, lead = open_lead(mount, busy(), size)
    fit = lead.strip_lines("best")
    assert abs(fit["width"] - fit["height"]) <= 1, f"a mark stays square: {fit}"
    assert fit["between"] <= LINE_GAP, f"the two lines read as one strip: {fit}"
    assert errors == []


@pytest.mark.req("Trade history", ac="a busy strip clips nothing and the page keeps its width")
@pytest.mark.parametrize("size", [PHONE, DESKTOP], ids=["phone", "desktop"])
def test_a_busy_managers_strip_clips_nothing(mount, size):
    page, errors, lead = open_lead(mount, busy(), size)
    assert lead.card_clips() == 0
    assert TradeHistoryPage(page).fits()
    assert errors == []


@pytest.mark.req("Trade history", ac="a matched set on a phone: every card in the swipe row one height")
def test_the_swipe_row_is_one_height_on_a_phone(mount):
    _, errors, lead = open_lead(mount, planted())
    cards = lead.top_row()
    assert len({c["height"] for c in cards}) == 1, [c["height"] for c in cards]
    assert errors == []


@pytest.mark.req("Trade history", ac="the strip holds the card's foot and the name centres in the height a heist leaves")
@pytest.mark.parametrize("size", [PHONE, DESKTOP], ids=["phone", "desktop"])
def test_the_name_centres_in_the_height_a_heist_leaves(mount, size):
    _, errors, lead = open_lead(mount, planted(), size)
    room = lead.strip_room("best")
    assert abs(room["toCardFoot"]) <= 2, f"the strip holds the card's foot: {room}"
    assert room["aboveName"] > 0, f"a heist's rows leave height to share out: {room}"
    assert abs(room["aboveName"] - room["underName"]) <= 2, f"the name centres: {room}"
    assert errors == []


@pytest.mark.req("Trade history", ac="side by side, the two strips share one line whatever size their marks are")
def test_the_strips_share_a_line_across_a_desktop(mount):
    _, errors, lead = open_lead(mount, busy(), DESKTOP)     # 25 small marks beside 4 big ones
    best, worst = lead.strip_room("best"), lead.strip_room("worst")
    assert abs(best["marksBottom"] - worst["marksBottom"]) <= 1 and abs(best["keyTop"] - worst["keyTop"]) <= 1, (best, worst)
    assert errors == []


@pytest.mark.req("Trade history", ac="five cards across a desktop, sharing a top and a bottom edge")
def test_five_cards_read_across_a_desktop(mount):
    page, errors, lead = open_lead(mount, planted(), (1440, 900))
    cards = lead.top_row()
    assert len(cards) == 5 and len({c["top"] for c in cards}) == 1
    assert len({c["height"] for c in cards}) == 1
    assert errors == []
