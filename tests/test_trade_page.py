"""League > Trades, a player's trade page (surface/finder/tpage.js, ledger #51, 2026-10-08, storyboard trades-pin draft B):
Get lists every package that lands another team's player, your gain first; Send lists each team's best return for your
own, the teams with none folded into one line; Add a player shops two at once; a row opens today's offer card; Make
your own opens Edit with him locked in. The profile's footer is the door. Which rows and in what order is
test_js_tradepage.py, in Node; this file is what the screen draws and does, read through tests/pages/tradepage.py.

The data is the fixture's ESPN league (tests/fixtures/data/trade_offers.json): the reader is Purdy Big in Japan, whose
three offers all go to Run It Back. Two of them land Bijan Robinson (+21.7 for you and 0.0 for them, sending Higgins,
Pollard and Goff and also getting J. Coker; +20.4 and +1.2, also getting K. Concepcion), all three send Tee Higgins, and
two send Higgins and Pollard together."""
import pytest

from component import mount  # noqa: E402,F401  (the fixture)
from pages.finder import finder  # noqa: E402
from pages.tradepage import ProfileFoot, pins, trade_page
from wording import words  # noqa: E402

ME = "espn"                     # Purdy Big in Japan, the fixture's ESPN team
OWNER, PARTNER = "Purdy Big in Japan", "Run It Back"
BIJAN = "trades/get/bijan-robinson"
HIGGINS = "trades/send/tee-higgins"
EXTRA = ("Big Salty", "FAFO!")   # two teams planted in the league with no offer, for the folded line


# ---- Get ----------------------------------------------------------------------------------------------------------

@pytest.mark.req("Trade page", ac="get: every package that lands him, one row each, your gain first")
def test_get_lists_every_package_that_lands_him_your_gain_first(mount):
    tp, errors = trade_page(mount, ME, BIJAN)
    assert tp.title().lower() == words("tradepage.title.get").format(name="B. Robinson").lower()
    assert PARTNER in tp.line() and "RB · ATL" in tp.line()
    assert tp.heads() == [words("tradepage.head.send"), words("tradepage.head.gains")]
    also = words("tradepage.get.also")
    assert tp.rows() == [
        {"main": "Higgins, Pollard, Goff", "sub": also.format(names="J. Coker"), "me": "+21.7", "them": "0.0", "tone": "up", "open": False},
        {"main": "Higgins, Pollard, Goff", "sub": also.format(names="K. Concepcion"), "me": "+20.4", "them": "+1.2", "tone": "up", "open": False},
    ], "the Kyren Williams offer does not land him"
    assert errors == []


@pytest.mark.req("Trade page", ac="a player with nothing shows one plain line why")
def test_get_with_no_package_says_why_in_one_line(mount):
    tp, errors = trade_page(mount, ME, "trades/get/sam-darnold")
    assert tp.rows() == []
    assert tp.why() == words("tradepage.why.getToday")
    assert tp.own_text() == words("tradepage.own.him"), "Make your own stays: the reader can still build one"
    assert errors == []


@pytest.mark.req("Trade page", ac="a row opens today's offer card, with Copy offer and Edit")
def test_a_row_opens_todays_offer_card_and_a_second_tap_closes_it(mount):
    tp, errors = trade_page(mount, ME, BIJAN)
    tp.tap_row(1)
    assert [r["open"] for r in tp.rows()] == [False, True]
    assert tp.cards() == [PARTNER]
    assert set(tp.card_buttons()) >= {words("lboard.offer.copy"), words("lboard.offer.edit")}
    tp.tap_row(0)
    assert [r["open"] for r in tp.rows()] == [True, False], "one card open at a time"
    tp.tap_row(0)
    assert tp.cards() == []
    assert errors == []


@pytest.mark.req("Trade page", ac="make your own opens Edit with him locked in YOU GET")
def test_make_your_own_opens_edit_with_him_locked_in_you_get(mount):
    tp, errors = trade_page(mount, ME, BIJAN)
    tp.own()
    locked = tp.locked()
    assert locked["package"] == ["RB B. Robinson"]
    assert locked["disabled"] == ["Bijan Robinson"], "his roster row cannot take him out"
    assert errors == []


# ---- Send ---------------------------------------------------------------------------------------------------------

@pytest.mark.req("Trade page", ac="send: one row per team, its best return; the teams with no offer as one folded line")
def test_send_lists_each_teams_best_return_and_folds_the_rest(mount):
    tp, errors = trade_page(mount, ME, HIGGINS, teams=EXTRA)
    assert tp.title().lower() == words("tradepage.title.send").format(names="T. Higgins").lower()
    assert words("tradepage.line.yours") in tp.line()
    assert tp.heads() == [words("tradepage.head.team"), words("tradepage.head.gains")]
    add = words("tradepage.send.add").format(names="Pollard, Goff")
    assert tp.rows() == [{"main": PARTNER, "sub": f"B. Robinson, J. Coker · {add}", "me": "+21.7", "them": "0.0", "tone": "up", "open": False}], \
        "three offers with Run It Back, one row: its best"
    assert tp.none() == f"{', '.join(EXTRA)} | {words('tradepage.none.one')}", "the teams with no offer, one line"
    assert errors == []


@pytest.mark.req("Trade page", ac="add a player shops two at once")
def test_add_a_player_shops_two_at_once_and_a_cross_takes_one_back_out(mount):
    tp, errors = trade_page(mount, ME, HIGGINS, teams=EXTRA)
    assert "tony-pollard" in tp.add_options() and "tee-higgins" not in tp.add_options() and "dk-metcalf" in tp.add_options()
    tp.add("tony-pollard")
    assert tp.hash() == "#trades/send/tee-higgins+tony-pollard"
    assert tp.shopped() == ["T. Higgins", "T. Pollard"] and not tp.has_add(), "two shopped: each with its cross, no third"
    assert [(r["main"], r["me"]) for r in tp.rows()] == [(PARTNER, "+21.7")]
    assert tp.none() == f"{', '.join(EXTRA)} | {words('tradepage.none.two')}"
    assert tp.own_text() == words("tradepage.own.them")
    tp.drop(0)
    tp.page.wait_for_selector("[data-testid=tpg-add]")
    assert tp.hash() == "#trades/send/tony-pollard"
    assert tp.shopped() == [] and tp.has_add()
    assert errors == []


@pytest.mark.req("Trade page", ac="the side follows who owns him, whatever the link said")
def test_a_get_link_for_your_own_player_shows_shop_and_says_so_in_the_hash(mount):
    tp, errors = trade_page(mount, ME, "trades/get/tee-higgins", linked=True)
    assert tp.title().lower() == words("tradepage.title.send").format(names="T. Higgins").lower()
    assert tp.hash() == f"#{HIGGINS}"
    assert errors == []


def test_a_player_on_no_roster_in_your_league_says_so(mount):
    tp, errors = trade_page(mount, ME, "trades/get/patrick-mahomes")
    assert tp.rows() == []
    assert tp.why().endswith(words("tradepage.why.free").split("{name}")[1]), "one line: he is on no roster here"
    assert errors == []


# ---- the pinned search, when ff-jarvis has written one ------------------------------------------------------------

def _pins(get, send=None, offers=()):
    return {"trade_pins/index.json": {"leagues": {"espn": {OWNER: "espn/pp.json"}}},
            "trade_pins/espn/pp.json": {"updated": "2026-10-08T05:50", "league": "espn", "owner": OWNER,
            "players": {}, "offers": list(offers), "get": get, "send": send or {}, "pairs": []}}


@pytest.mark.req("Trade page", ac="the pinned search's reason when a player has no package")
def test_with_a_pinned_file_a_player_with_nothing_says_its_reason(mount):
    tp, errors = trade_page(mount, ME, BIJAN, files=_pins({"bijan-robinson": {"reason": "no_gain_for_him"}}))
    assert tp.pin_fetches() == ["trade_pins/index.json", "trade_pins/espn/pp.json"]
    assert tp.rows() == [] and tp.why() == words("tradepage.why.heLoses").format(owner=PARTNER)
    assert errors == []


def test_without_a_pinned_file_the_page_fills_from_todays_offers(mount):
    tp, errors = trade_page(mount, ME, BIJAN, files={})
    assert tp.pin_fetches() == ["trade_pins/index.json"], "asked for the index once, got a 404"
    assert len(tp.rows()) == 2
    assert errors == []


# ---- states and layout --------------------------------------------------------------------------------------------

def test_with_no_team_picked_the_page_asks_for_one(mount):
    tp, errors = trade_page(mount, None, BIJAN)
    assert tp.need() == words("finder.need")
    assert errors == []


def test_back_returns_to_the_finder(mount):
    tp, errors = trade_page(mount, ME, BIJAN)
    tp.back()
    tp.page.wait_for_selector("[data-testid=finder-chip]")
    assert errors == []


@pytest.mark.parametrize("size", [(360, 740), (1280, 800)])
def test_the_page_fits_a_phone_and_keeps_one_column_on_a_desktop(mount, size):
    tp, errors = trade_page(mount, ME, HIGGINS, size=size)
    assert tp.fits()
    assert tp.column_box()["w"] <= 560, "a row's name and its number stay within 560px (STYLE.md)"
    assert errors == []


# ---- the profile's footer -----------------------------------------------------------------------------------------

BIJAN_P = {"n": "Bijan Robinson", "pos": "RB", "team": "ATL", "slug": "bijan-robinson"}
HIGGINS_P = {"n": "Tee Higgins", "pos": "WR", "team": "CIN", "slug": "tee-higgins"}


def profile(mount, pick, player, size=(360, 740)):
    """(page, ProfileFoot, errors): the Trades view for `pick` with `player`'s profile open over it."""
    page, errors = finder(mount, pick, size=size, init=(pins(),))
    foot = ProfileFoot(page)
    foot.open(player)
    return page, foot, errors


@pytest.mark.req("Trade page", ac="the profile footer: Close and Trade for him, or Shop him for your own")
@pytest.mark.parametrize("player,label", [(BIJAN_P, "profile.foot.get"), (HIGGINS_P, "profile.foot.send")])
def test_the_profile_footer_offers_close_and_the_trade_by_who_owns_him(mount, player, label):
    page, foot, errors = profile(mount, ME, player)
    assert foot.buttons() == [words("common.action.close"), words(label)]
    box = foot.foot_box()
    assert abs(box["foot_bottom"] - box["modal_bottom"]) <= 1, "the footer sits on the modal's bottom edge, in thumb reach"
    assert errors == []


def test_the_footer_has_only_close_with_no_team_picked(mount):
    page, foot, errors = profile(mount, None, BIJAN_P)
    assert foot.buttons() == [words("common.action.close")]
    foot.close()
    page.wait_for_function("!document.getElementById('modal').classList.contains('on')")
    assert errors == []


def test_trade_for_him_closes_the_profile_and_opens_his_page(mount):
    page, foot, errors = profile(mount, ME, BIJAN_P)
    foot.trade()
    page.wait_for_function(f"location.hash === '#{BIJAN}'")
    page.wait_for_selector("[data-testid=tpg-title]")
    assert not foot.is_open()
    assert errors == []


def test_on_a_desktop_the_footer_keeps_only_the_trade_button(mount):
    page, foot, errors = profile(mount, ME, BIJAN_P, size=(1280, 800))
    assert foot.buttons() == [words("profile.foot.get")], "the ✕ is in reach on a desktop"
    assert errors == []
