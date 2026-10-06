"""League > Teams > Find trades (2026-10-05): ff-jarvis's trade_offers.json is checked and written beside the page
by design/trade_offers.py, and the roster sheet's lime button opens a builder sheet that fetches it on first open.
The file is tested against tests/fixtures/data/trade_offers.json (a bold+fair pair, a bold-only pair, injured
players, an AYO pair whose reverse has no entry); the sheet in Chromium with the fetch replaced, because from
file:// the browser refuses it."""
import copy
import json
import pathlib
import re
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "design"))
import contract  # noqa: E402
import sources  # noqa: E402
import trade_offers  # noqa: E402
from conftest import FIXTURES, REPO  # noqa: E402
from test_render import SEED  # noqa: E402

FIXTURE = json.loads((FIXTURES / "data" / "trade_offers.json").read_text(encoding="utf-8"))


# ---- the file: read, checked, written ---------------------------------------------------------------

def test_the_offers_are_read_from_the_file_and_the_feed_block_wins(tmp_path, monkeypatch):
    assert sources.load_trade_offers() == FIXTURE, "the fixture feed has no block, so the file is read"
    block = {"updated": "2026-10-06T01:00", "season": 2026, "leagues": {"espn": {"week": 5, "teams": {}}}}
    feed = tmp_path / "feed.json"
    feed.write_text(json.dumps({"trade_offers": {"data": block, "fetched": block["updated"]}}), encoding="utf-8")
    monkeypatch.setattr(sources, "FEED", feed)
    assert sources.load_trade_offers() == block


def test_no_feed_block_and_no_file_is_none(tmp_path, monkeypatch):
    monkeypatch.setattr(sources, "FEED", tmp_path / "none.json")
    monkeypatch.setattr(sources, "DWR", tmp_path)
    assert sources.load_trade_offers() is None


def test_the_contract_passes_the_fixture_and_names_every_missing_field():
    contract.validate("TRADE_OFFERS", FIXTURE)
    bad = copy.deepcopy(FIXTURE)
    pair = bad["leagues"]["espn"]["teams"]["Purdy Big in Japan"]["Run It Back"]
    del pair["bold"][0]["gain"]
    del pair["bold"][0]["send"][1]["injury"]
    del pair["fair"]
    del bad["leagues"]["ayo"]["week"]
    with pytest.raises(SystemExit) as e:
        contract.validate("TRADE_OFFERS", bad)
    msg = str(e.value)
    for at in (".bold[0].gain", ".bold[0].send[1].injury", "['Run It Back'].fair", "leagues['ayo'].week"):
        assert at in msg, at
    assert contract.problems("TRADE_OFFERS", None) == []


def without_drop_rule(doc):
    """The file as it was before the drop rule: no IR slots, no keep / ir_ok / protect, no ir_moves."""
    old = copy.deepcopy(doc)
    for lg in old["leagues"].values():
        lg["lineup"].pop("ir")
        for rows in lg["values"].values():
            for p in rows:
                for k in trade_offers.DROP_VALUE:
                    p.pop(k)
        for ps in lg["teams"].values():
            for kinds in ps.values():
                for offers in kinds.values():
                    for o in offers:
                        o.pop("ir_moves")
    return old


def test_the_drop_rules_fields_are_required(monkeypatch):
    """Required since 2026-10-05 (ff-jarvis 4e69378): a file from before the drop rule fails the build."""
    old = without_drop_rule(FIXTURE)
    assert trade_offers.DROP_RULE_REQUIRED is True
    miss = trade_offers.problems(old)
    assert any(m.endswith(".lineup.ir") for m in miss), miss
    monkeypatch.setattr(trade_offers, "DROP_RULE_REQUIRED", False)
    assert trade_offers.problems(old) == [], "with the flag off the old shape passes, so the flag is what enforces it"
    monkeypatch.undo()
    assert trade_offers.problems(FIXTURE) == [], "the fixture follows the spec exactly"
    no_moves = copy.deepcopy(FIXTURE)
    del no_moves["leagues"]["espn"]["teams"]["Purdy Big in Japan"]["Run It Back"]["bold"][0]["ir_moves"]
    assert any(m.endswith("bold[0].ir_moves") for m in trade_offers.problems(no_moves))
    no_ir = copy.deepcopy(FIXTURE)
    del no_ir["leagues"]["espn"]["values"]["Run It Back"][0]["keep"]
    assert any(m.endswith("['Run It Back'][0].keep") for m in trade_offers.problems(no_ir))


def test_present_drop_rule_fields_are_checked_even_while_optional():
    bad = copy.deepcopy(FIXTURE)
    del bad["leagues"]["espn"]["values"]["Run It Back"][0]["protect"]      # keep and ir_ok are there, protect is not
    del bad["leagues"]["espn"]["teams"]["Run It Back"]["Purdy Big in Japan"]["bold"][1]["ir_moves"][0]["slug"]
    miss = trade_offers.problems(bad)
    assert any(m.endswith("['Run It Back'][0].protect") for m in miss), miss
    assert any(m.endswith("bold[1].ir_moves[0].slug") for m in miss), miss


def without_option_b(doc, their=True, players=True):
    """The file as it was before option B: no `last2` or `chips` on any player, no `their` on any offer."""
    old = copy.deepcopy(doc)
    for lg in old["leagues"].values():
        for rows in lg["values"].values():
            for p in rows:
                if players:
                    del p["last2"], p["chips"]
        for ps in lg["teams"].values():
            for kinds in ps.values():
                for offers in kinds.values():
                    for o in offers:
                        if players:
                            for side in ("send", "get", "drop", "ir_moves"):
                                for p in o[side]:
                                    del p["last2"], p["chips"]
                            for side in ("ir_moves", "drop"):
                                for p in o["their"][side]:
                                    del p["last2"], p["chips"]
                        if their:
                            del o["their"]
    return old


def test_option_bs_fields_are_required(monkeypatch):
    """Required since 2026-10-05 (ff-jarvis 79b2b0b): a file without last2, chips and their fails the build."""
    assert trade_offers.OPTION_B_REQUIRED is True
    assert any(m.endswith(".last2") for m in trade_offers.problems(without_option_b(FIXTURE, their=False)))
    assert any(m.endswith(".their") for m in trade_offers.problems(without_option_b(FIXTURE, players=False)))
    monkeypatch.setattr(trade_offers, "OPTION_B_REQUIRED", False)
    assert trade_offers.problems(without_option_b(FIXTURE)) == [], "with the flag off the old shape passes"
    monkeypatch.undo()
    assert trade_offers.problems(FIXTURE) == [], "the fixture follows the spec exactly"
    bad = copy.deepcopy(FIXTURE)
    del bad["leagues"]["espn"]["values"]["Run It Back"][0]["chips"]                  # last2 is there, chips is not
    pair = bad["leagues"]["espn"]["teams"]["Purdy Big in Japan"]["Run It Back"]
    del pair["bold"][1]["their"]["drop"]
    pair["bold"][0]["send"][1]["chips"] = "Hot"                                     # a string, not a list
    del pair["bold"][0]["their"]["ir_moves"][0]["last2"]
    miss = trade_offers.problems(bad)
    for at in ("['Run It Back'][0].chips", "bold[1].their.drop", "bold[0].send[1].chips", "bold[0].their.ir_moves[0].last2"):
        assert any(m.endswith(at) for m in miss), (at, miss)


def test_a_null_last2_is_a_value_and_a_missing_one_is_not():
    ok = copy.deepcopy(FIXTURE)
    ok["leagues"]["espn"]["values"]["Run It Back"][0]["last2"] = None             # a rookie with one game
    assert trade_offers.problems(ok) == []
    del ok["leagues"]["espn"]["values"]["Run It Back"][0]["last2"]
    assert any(m.endswith("['Run It Back'][0].last2") for m in trade_offers.problems(ok))


def test_a_null_injury_is_a_value_and_a_missing_one_is_not():
    ok = copy.deepcopy(FIXTURE)
    assert ok["leagues"]["espn"]["teams"]["Purdy Big in Japan"]["Run It Back"]["bold"][0]["send"][1]["injury"] is None
    assert trade_offers.problems(ok) == []


def test_build_writes_the_same_data_compact_beside_the_page(tmp_path):
    line = trade_offers.build(tmp_path)
    assert line.startswith("Offers: espn 2, yahoo 0, ayo 1 pairs with an offer, updated 2026-10-05T14:07")
    text = (tmp_path / trade_offers.NAME).read_text(encoding="utf-8")
    assert json.loads(text) == FIXTURE
    assert text == json.dumps(FIXTURE, ensure_ascii=False, separators=(",", ":")), "compact: the file is fetched by every reader"


def test_build_with_no_offers_writes_nothing_and_says_so(tmp_path, monkeypatch):
    monkeypatch.setattr(sources, "FEED", tmp_path / "none.json")
    monkeypatch.setattr(sources, "DWR", tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    assert trade_offers.build(out).startswith("Offers: none")
    assert list(out.iterdir()) == []


def test_build_refuses_a_file_missing_a_field(tmp_path, monkeypatch):
    bad = copy.deepcopy(FIXTURE)
    del bad["leagues"]["ayo"]["teams"]["Taylor Made for Sundays"]["Don Wick"]["fair"][0]["get"][0]["slug"]
    (tmp_path / "trade_offers.json").write_text(json.dumps(bad), encoding="utf-8")
    monkeypatch.setattr(sources, "FEED", tmp_path / "none.json")
    monkeypatch.setattr(sources, "DWR", tmp_path)
    with pytest.raises(SystemExit, match=r"fair\[0\]\.get\[0\]\.slug"):
        trade_offers.build(tmp_path)


def test_the_offers_are_not_in_the_page_and_the_page_names_the_file_the_build_writes(built):
    assert '"gain":8.5' not in built.fragment and '"gain": 8.5' not in built.fragment, "fetched, never injected"
    assert f'const TB_URL = "{trade_offers.NAME}"' in built.fragment


def test_vercel_serves_the_file_git_marks_it_generated_and_land_folds_it_in():
    assert f"!{trade_offers.NAME}" in (REPO / ".vercelignore").read_text(encoding="utf-8").split(), ".vercelignore is an allowlist"
    attrs = (REPO / ".gitattributes").read_text(encoding="utf-8")
    assert re.search(rf"^{re.escape(trade_offers.NAME)}\s+-diff merge=ours", attrs, re.M)
    assert f'"{trade_offers.NAME}"' in (REPO / "scripts" / "land.ps1").read_text(encoding="utf-8")


# ---- the sheet ---------------------------------------------------------------------------------------

# Replaces the page's fetch of the offers: from file:// the browser refuses it. window.__tb is the mode ("ok",
# "fail", "hold" until __tbRelease()), __tbFetches how many times the page asked.
PLANT = """(() => {
  window.__tb = "ok"; window.__tbFetches = 0;
  const real = window.fetch.bind(window), body = %s;
  window.fetch = (url, ...rest) => {
    if (!String(url).includes("trade_offers.json")) return real(url, ...rest);
    window.__tbFetches++;
    const reply = () => window.__tb === "ok" ? new Response(JSON.stringify(body), {status: 200}) : Promise.reject(new TypeError("Failed to fetch"));
    if (window.__tb !== "hold") return Promise.resolve(reply());
    return new Promise(res => { window.__tbRelease = () => { window.__tb = "ok"; res(reply()); }; });
  };
})();""" % json.dumps(FIXTURE)
COPY_REFUSED = "navigator.clipboard.writeText = () => Promise.reject(new DOMException('no', 'NotAllowedError'));"


def reader(browser, page_file, pick, w=360, h=800, init=""):
    """The fixture page at `w` x `h` as a reader whose team is `pick` (a TEAMS key, or None), on League > Teams."""
    ctx = browser.new_context(viewport={"width": w, "height": h}, reduced_motion="reduce")
    ctx.grant_permissions(["clipboard-read", "clipboard-write"])
    page = ctx.new_page()
    page.set_default_timeout(5000)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.route(re.compile(r"^https?://"), lambda route: route.abort())
    page.add_init_script(SEED + (f'try {{ localStorage.setItem("tw-team", "{pick}"); }} catch (e) {{}}' if pick else
                                 'try { localStorage.removeItem("tw-team"); } catch (e) {}') + PLANT + init)
    page.goto(page_file.as_uri() + "#teams")
    page.wait_for_selector("#view[data-view='teams'] > *")
    return ctx, page, errors


def roster(page, key):
    """A team's page, opened from the board."""
    page.locator(f"[data-lbopen='{key}']").click()
    page.wait_for_selector(".lbp-title")


def builder(page, key):
    """The trade builder page, one page further in."""
    roster(page, key)
    page.locator("[data-tbfind]").click()
    page.wait_for_selector("#tb-title")


def on_board(page):
    page.wait_for_selector(".lb-grid")


@pytest.mark.render
def test_the_button_is_for_a_team_that_is_not_the_readers_own_in_the_readers_league(browser, page_file):
    ctx, page, errors = reader(browser, page_file, "espn")
    roster(page, "espn-run-it-back")
    assert page.locator("[data-tbfind]").inner_text() == "Find trades with Run It Back"
    assert page.locator("[data-lbmine]").count() == 0, "a reader with a team in this league switches with the team switch"
    page.locator(".lbp-back").click()
    on_board(page)
    roster(page, "espn")
    assert page.locator("[data-tbfind]").count() == 0 and page.locator("[data-lbmine]").count() == 0, "your own team has nobody to trade with"
    assert page.locator(".lbp-yours").inner_text() == "Your team"
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_a_reader_with_no_team_in_the_league_gets_this_is_my_team_and_no_trade_button(browser, page_file):
    ctx, page, _ = reader(browser, page_file, "ayo")                      # the reader's team is in AYO
    page.locator("[data-lgpick='espn']").click()                           # the board on ESPN's league
    roster(page, "espn-run-it-back")
    assert page.locator("[data-tbfind]").count() == 0
    assert page.locator("[data-lbmine]").inner_text() == "This is my team"
    ctx.close()
    ctx, page, _ = reader(browser, page_file, None)                        # no team picked at all
    page.locator("[data-lgpick='espn']").click()
    roster(page, "espn")
    assert page.locator("[data-tbfind]").count() == 0 and page.locator("[data-lbmine]").count() == 1
    ctx.close()


@pytest.mark.render
def test_this_is_my_team_picks_it_the_way_the_team_switch_does_and_the_other_teams_then_offer_trades(browser, page_file):
    ctx, page, errors = reader(browser, page_file, None)
    page.locator("[data-lgpick='espn']").click()
    assert page.locator(".lb-pick").inner_text() == "Tap your team to set it" and page.locator(".lb-row.mine").count() == 0
    roster(page, "espn-run-it-back")
    slot = page.evaluate("document.querySelector('.lbp-slot').getBoundingClientRect().height")
    page.locator("[data-lbmine]").click()
    assert page.evaluate("[localStorage.getItem('tw-team'), VIEW, myTeamLoad()]") == ["espn-run-it-back"] * 3, "pickTeam's own storage and state"
    assert page.locator(".lbp-yours").inner_text() == "Your team"
    assert page.locator("[data-lbmine]").count() == 0 and page.locator("[data-tbfind]").count() == 0
    assert page.evaluate("document.querySelector('.lbp-slot').getBoundingClientRect().height") == slot, "the action row keeps its height"
    assert page.evaluate("document.activeElement.className") == "lbp-yours"
    page.locator(".lbp-back").click()
    on_board(page)
    assert page.locator(".lb-pick").count() == 0, "the line is gone once the reader has a team here"
    assert names(page)[0] == "Run It Back" and page.locator(".lb-row.mine").count() == 1, "pinned"
    roster(page, "espn")
    assert page.locator("[data-tbfind]").inner_text() == "Find trades with Purdy Big in Japan"
    assert page.locator("[data-lbmine]").count() == 0, "a reader who has a team here never sees This is my team on another"
    ctx.close()
    assert errors == []


def names(page):
    return page.locator(".lb-row .lb-team b").all_inner_texts()


@pytest.mark.render
def test_the_builder_opens_on_bold_with_each_offer_as_two_columns_and_one_number(browser, page_file):
    ctx, page, errors = reader(browser, page_file, "espn")
    assert page.evaluate("__tbFetches") == 0, "nothing is fetched until a reader opens the builder"
    builder(page, "espn-run-it-back")
    page.wait_for_selector(".tb-card .tb-gain")
    assert page.locator("#tb-title").get_attribute("aria-label") == "You and Run It Back"
    assert page.locator("#tb-title .tb-swap").count() == 1, "the swap is a drawn icon, not a glyph"
    assert page.locator("[data-tbtab='bold']").get_attribute("aria-pressed") == "true"
    assert page.locator("[data-tbtab='fair']").get_attribute("aria-pressed") == "false"
    assert page.locator(".tb-line").inner_text() == "Biggest gain for you"
    assert page.locator(".tb-card").count() == 3
    first = page.locator(".tb-card").first
    assert first.locator(".tb-h").all_inner_texts() == ["YOU SEND", "YOU GET"]
    cols = first.locator(".tb-col")
    assert [r.replace("\n", " ") for r in cols.nth(0).locator(".tb-p").all_inner_texts()] == ["WR T. Higgins Q", "QB B. Purdy", "RB O. Gordon II"]
    assert cols.nth(1).locator(".tb-p").count() == 2
    assert first.locator(".tb-inj").all_inner_texts() == ["Q"], "an amber pill where a status is set"
    assert first.locator(".tb-gain").inner_text() == "+8.5 pts a week for you"
    assert first.locator(".tb-gain b").evaluate("e => getComputedStyle(e).color") == "rgb(55, 224, 139)", "green"
    assert page.locator(".tb-upd").inner_text() == "Offers updated Oct 5"
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert page.evaluate("__tbFetches") == 1
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_fair_is_the_other_tab_and_the_last_tab_is_kept_for_the_visit_and_the_file_is_fetched_once(browser, page_file):
    ctx, page, _ = reader(browser, page_file, "espn-run-it-back")     # Run It Back's offers to Purdy have both kinds
    builder(page, "espn")
    page.wait_for_selector(".tb-card .tb-gain")
    top = page.evaluate("document.querySelector('[data-tbtab]').getBoundingClientRect().top")
    page.locator("[data-tbtab='fair']").click()
    assert page.locator("[data-tbtab='fair']").get_attribute("aria-pressed") == "true"
    assert page.locator(".tb-line").inner_text() == "Both lineups gain"
    assert page.locator(".tb-card").count() == 3 and page.locator(".tb-gain").first.inner_text() == "+1.1 pts a week for you"
    assert page.evaluate("document.querySelector('[data-tbtab]').getBoundingClientRect().top") == top, "the tabs do not move between tabs"
    page.locator(".lbp-back").click()
    page.wait_for_selector("[data-tbfind]")
    page.locator(".lbp-back").click()
    on_board(page)
    builder(page, "espn")
    assert page.locator("[data-tbtab='fair']").get_attribute("aria-pressed") == "true", "kept in memory for the visit"
    assert page.evaluate("__tbFetches") == 1, "the file is cached for the session"
    ctx.close()


@pytest.mark.render
def test_an_empty_tab_and_a_pair_with_no_entry_say_so_in_one_line(browser, page_file):
    ctx, page, _ = reader(browser, page_file, "espn")                  # Purdy's offers to Run It Back: bold only
    builder(page, "espn-run-it-back")
    page.wait_for_selector(".tb-card .tb-gain")
    assert page.locator(".tb-card").count() == 3
    page.locator("[data-tbtab='fair']").click()
    assert page.locator(".tb-card").count() == 0
    assert page.locator(".tb-empty").inner_text() == "No fair offer this week"
    ctx.close()
    ctx, page, _ = reader(browser, page_file, "ayo-don-wick")          # Don Wick to Taylor Made: nothing in the file
    page.locator("[data-lgpick='ayo']").click()
    builder(page, "ayo")
    page.wait_for_selector(".tb-empty")
    assert page.locator(".tb-empty").inner_text() == "No offers this week"
    assert page.locator("[data-tbtab]").count() == 0, "nothing to switch between"
    ctx.close()
    ctx, page, _ = reader(browser, page_file, "ayo")                   # Taylor Made to Don Wick: bold has one, fair has one
    page.locator("[data-lgpick='ayo']").click()
    builder(page, "ayo-don-wick")
    page.wait_for_selector(".tb-card .tb-gain")
    assert page.locator(".tb-inj").all_inner_texts() == ["O"], "Out is an O"
    ctx.close()


@pytest.mark.render
def test_copy_offer_puts_a_message_of_true_season_averages_on_the_clipboard(browser, page_file):
    ctx, page, errors = reader(browser, page_file, "espn")
    builder(page, "espn-run-it-back")
    page.wait_for_selector(".tb-card .tb-gain")
    page.locator("[data-tbcopy='0']").click()
    page.wait_for_function("document.querySelector(\"[data-tbcopy='0']\").textContent === 'Copied'")
    assert page.evaluate("navigator.clipboard.readText()") == (
        "Trade? I send Higgins (14.4 a game), Purdy (28.8), Gordon II (10.2) for Smith-Njigba (25.3) and Brown (11.4)."
        " M. Mariota can go to your IR slot, so you don't cut anyone.")
    page.locator("[data-tbcopy='1']").click()
    page.wait_for_function("document.querySelector(\"[data-tbcopy='1']\").textContent === 'Copied'")
    assert page.evaluate("navigator.clipboard.readText()") == (
        "Trade? I send Purdy (28.8 a game), Raymond (9.4), Gordon II (10.2) for Smith-Njigba (25.3)."
        " M. Mariota can go to your IR slot. You'd only need to cut J. Hill.")
    page.locator("[data-tbcopy='2']").click()
    page.wait_for_function("document.querySelector(\"[data-tbcopy='2']\").textContent === 'Copied'")
    assert page.evaluate("navigator.clipboard.readText()") == (
        "Trade? I send Purdy (28.8 a game) for Brown (11.4) and Watson (16.5)."), "Watson is Hot, but the reader gets him: season average, never his last 2; his room is fine, so no sentence"
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_a_refused_clipboard_shows_the_text_selected_in_a_box(browser, page_file):
    ctx, page, _ = reader(browser, page_file, "espn", init=COPY_REFUSED)
    builder(page, "espn-run-it-back")
    page.wait_for_selector(".tb-card .tb-gain")
    page.locator("[data-tbcopy='1']").click()
    page.wait_for_selector(".tb-box")
    box = page.locator(".tb-box")
    assert box.input_value() == ("Trade? I send Purdy (28.8 a game), Raymond (9.4), Gordon II (10.2) for Smith-Njigba (25.3)."
                                 " M. Mariota can go to your IR slot. You'd only need to cut J. Hill.")
    assert page.evaluate("(() => { const b = document.querySelector('.tb-box'); return document.activeElement === b && b.selectionEnd - b.selectionStart === b.value.length; })()")
    assert page.locator("[data-tbcopy='1']").inner_text() == "Copy offer", "no false Copied"
    ctx.close()


@pytest.mark.render
def test_the_builder_shows_shapes_while_loading_and_an_error_with_a_retry(browser, page_file):
    ctx, page, errors = reader(browser, page_file, "espn", init="window.__tb = 'hold';")
    builder(page, "espn-run-it-back")
    assert page.locator(".tb-skel").count() == 3 and page.locator(".tb-line").inner_text() == "Finding offers"
    page.evaluate("__tbRelease()")
    page.wait_for_selector(".tb-card .tb-gain")
    assert page.locator(".tb-skel").count() == 0
    ctx.close()
    ctx, page, errors = reader(browser, page_file, "espn", init="window.__tb = 'fail';")
    builder(page, "espn-run-it-back")
    page.wait_for_selector(".tb-empty")
    assert "Offers did not load" in page.locator(".tb-empty").inner_text()
    assert page.locator("[data-tbtab]").count() == 0 and page.locator(".tb-card").count() == 0
    page.evaluate("window.__tb = 'ok'")
    page.locator("[data-tbretry]").click()
    page.wait_for_selector(".tb-card .tb-gain")
    assert page.evaluate("__tbFetches") == 2
    ctx.close()
    assert errors == [], "a failed fetch is a state, not an exception"


@pytest.mark.render
def test_from_file_the_real_fetch_is_refused_and_the_page_says_so(browser, page_file):
    ctx = browser.new_context(viewport={"width": 360, "height": 800}, reduced_motion="reduce")
    page = ctx.new_page()
    page.set_default_timeout(5000)
    page.route(re.compile(r"^https?://"), lambda route: route.abort())
    page.add_init_script(SEED + 'try { localStorage.setItem("tw-team", "espn"); } catch (e) {}')
    page.goto(page_file.as_uri() + "#teams")
    page.wait_for_selector("#view[data-view='teams'] > *")
    builder(page, "espn-run-it-back")
    page.wait_for_selector(".tb-empty")
    assert "Offers did not load" in page.locator(".tb-empty").inner_text()
    ctx.close()


@pytest.mark.render
def test_back_and_the_link_step_back_one_page_at_a_time_from_the_builder_to_the_team_to_the_board(browser, page_file):
    ctx, page, errors = reader(browser, page_file, "espn")
    builder(page, "espn-run-it-back")
    assert page.locator(".lbp-back").inner_text() == "Run It Back", "the link names the page it goes back to"
    assert page.locator("#lbsheet, #tbsheet, .lbs-scrim").count() == 0, "pages all the way: no sheet, no scrim"
    page.go_back()
    page.wait_for_selector("[data-tbfind]")
    assert page.locator(".lbp-title").inner_text() == "Run It Back", "Back closed the builder, not the team"
    assert page.evaluate("document.activeElement.hasAttribute('data-tbfind')"), "focus returns to the button"
    page.locator("[data-tbfind]").click()
    page.wait_for_selector("#tb-title")
    page.locator(".lbp-back").click()
    page.wait_for_selector("[data-tbfind]")
    page.go_back()
    on_board(page)
    assert page.evaluate("location.hash") == "#teams"
    assert page.evaluate("localStorage.getItem('tw-team')") == "espn", "trading with a team never picks it"
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_leaving_teams_with_a_page_open_forgets_it(browser, page_file):
    ctx, page, errors = reader(browser, page_file, "espn")
    builder(page, "espn-run-it-back")
    page.locator(".navitem[data-s='scouting']").click()
    page.wait_for_selector("#view[data-view='highlights'] > *")
    page.locator(".navitem[data-s='league']").click()
    page.locator(".mode-sub[data-leaf='teams']").click()
    on_board(page)
    assert page.locator(".lbp").count() == 0, "Teams opens on its board, not on the page left behind"
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_the_builder_fits_a_phone_and_a_desktop_with_no_sideways_scroll(browser, page_file):
    for w, h in ((360, 800), (1280, 900)):
        ctx, page, _ = reader(browser, page_file, "espn", w=w, h=h)
        builder(page, "espn-run-it-back")
        page.wait_for_selector(".tb-card .tb-gain")
        box = page.evaluate("(() => { const r = document.querySelector('.lbp').getBoundingClientRect(); return [r.left, r.right]; })()")
        assert box[0] >= 0 and box[1] <= w
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        assert page.evaluate("(() => { const b = document.querySelector('.tb-body'); return b.scrollWidth <= b.clientWidth; })()")
        assert page.evaluate("[...document.querySelectorAll('.tb-copy, .lbp-act, .lbp-back, [data-tbtab]')].every(b => b.getBoundingClientRect().height >= 44)")
        left = page.evaluate("document.querySelector('.tb-card').getBoundingClientRect().left - document.querySelector('.lbp-back').getBoundingClientRect().left")
        assert abs(left) <= 12, f"left-aligned on the frame's edge, {left}px off the link"
        assert page.evaluate("document.querySelector('.tb-card').getBoundingClientRect().width") <= 561, "a card keeps to one column"
        ctx.close()
