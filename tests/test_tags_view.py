"""Player tags, drawn (2026-10-08, ledger #41): one pill on a Roster row and a Ranks row, every tag with its plain line
in the profile. What each tag says, and in what order, is Node's (tests/test_js_tags.py); this file proves the screen
draws it at 360px without growing a row, and that no block draws nothing.

The fixture (tests/fixtures/data/player_tags.json): Joe Burrow Lucky only (hidden, so no tag), Jahmyr Gibbs Rising and
Trending, Chase Brown two Sleeper signals, Breece Hall Lucky, Rising and Trending (Rising shows), Brock Purdy none, the
SF George Kittle Rising, Amon-Ra St. Brown none (test_profile_panes.py holds his profile free of a Rising word). The
Roster mounts the Yahoo team (Burrow, St. Brown, Chase Brown, Gibbs).
"""
import re

import pytest

from component import Mounter, mount  # noqa: F401  (the fixture)
from pages.ranks import RanksPage
from pages.roster import on_roster
from pages.tags import TagsPage
from wording import words

REQ = "Player tags"
PHONE = (360, 740)
THREE_LINES = 66      # a starter row with name, game and kickoff at 360px (measured 2026-10-08): room for pill and bars


@pytest.fixture(scope="module")
def no_block(mount, built, tmp_path_factory):
    """The page as a build without ff-jarvis's file writes it: LIVE_PLAYER_TAGS is null."""
    fragment = re.sub(r"^const LIVE_PLAYER_TAGS = .*;$", "const LIVE_PLAYER_TAGS = null;", built.fragment, flags=re.M)
    assert fragment != built.fragment, "the fixture build injects no LIVE_PLAYER_TAGS to remove"
    m = Mounter(mount.browser, tmp_path_factory.getbasetemp() / "component-no-tags", fragment)
    yield m
    m.pages.close()


@pytest.mark.req(REQ, ac="a Roster row shows its first tag; a player with none, or only the hidden Lucky, shows none")
def test_each_roster_row_shows_its_first_tag(mount):
    profile, errors = on_roster(mount, size=PHONE)
    assert TagsPage(profile.page).roster_tags() == {
        "Joe Burrow": None, "Amon-Ra St. Brown": None, "Chase Brown": "POTENTIAL", "Jahmyr Gibbs": "RISING"}
    assert errors == []


@pytest.mark.req(REQ, ac="POTENTIAL is named Sleeper on the row, and its hover text is its plain lines")
def test_the_potential_pill_says_sleeper_with_its_lines_as_the_hover_text(mount):
    profile, errors = on_roster(mount, size=PHONE)
    pill = TagsPage(profile.page).roster_pill("Chase Brown")
    assert pill["text"] == words("tags.label.sleeper")
    assert words("tags.sleeper.routesFirst") in pill["title"] and words("tags.sleeper.vacated") in pill["title"]
    assert errors == []


@pytest.mark.req(REQ, ac="at 360px the pill sits above the bars inside the row, never over them, and a row grows by no more than the pill")
def test_at_360px_the_pill_sits_over_the_bars_and_never_covers_them(mount):
    """The fixture's rows are two text lines (53px); a live three-line row (66px) has the room and keeps its height
    (checked by hand on 2026-10-08's data: every row 66px with and without its pill)."""
    profile, errors = on_roster(mount, size=PHONE)
    tags = TagsPage(profile.page)
    rows, bare = tags.roster_layout(), tags.roster_heights_without_pills()
    tagged = [(r, h) for r, h in zip(rows, bare) if r["tagged"]]
    assert tagged and any(not r["tagged"] for r in rows)
    assert all(r["above"] and r["inside"] for r, _ in tagged), tagged
    assert all(h <= r["h"] <= h + r["pill"] + 2 for r, h in tagged), tagged
    assert all(r["h"] == h for r, h in tagged if h >= THREE_LINES), tagged
    assert errors == []


@pytest.mark.req(REQ, ac="a Ranks row carries its first tag on the name line, and the line stays one line at 360px")
def test_a_ranks_row_carries_its_first_tag_on_one_name_line(mount):
    page, errors = mount("ranks", size=PHONE)
    ranks, tags = RanksPage(page), TagsPage(page)
    ranks.pick("RB")
    got = tags.ranks_tags()
    assert (got["breece-hall"], got["chase-brown"], got["kendre-miller"]) == ("RISING", "POTENTIAL", None)
    assert tags.ranks_name_line_fits("breece-hall") and tags.ranks_name_line_fits("chase-brown")
    ranks.pick("QB")
    assert tags.ranks_tags() == {"joe-burrow": None, "brock-purdy": None}
    assert errors == []


@pytest.mark.req(REQ, ac="the profile lists every tag in order with its plain line and no other word, no Fact or Tested")
def test_the_profile_lists_every_tag_with_its_line_and_nothing_else(mount):
    profile, errors = on_roster(mount, size=PHONE)
    tags = TagsPage(profile.page)
    profile.open_from_roster("Jahmyr Gibbs")
    assert tags.profile_list() == [
        (words("tags.label.rising"), words("tags.rising.fact").replace("{n}", "3").replace("{last}", "21.4").replace("{earlier}", "17.2"), 0),
        (words("tags.label.trending"), words("tags.trending.fact").replace("{rank}", "4").replace("{hours}", "24").replace("{adds}", "412,305"), 0)]
    profile.close()
    profile.open_from_roster("Joe Burrow")
    assert not tags.profile_has_list()                    # Lucky is hidden: no list at all
    assert errors == []


@pytest.mark.req(REQ, ac="no METHODOLOGY id or ff-jarvis tag name reaches the profile's words")
def test_the_profiles_words_name_no_trial_and_no_raw_tag(mount):
    profile, errors = on_roster(mount, size=PHONE)
    profile.open_from_roster("Chase Brown")
    text = " ".join(f"{word} {line}" for word, line, _ in TagsPage(profile.page).profile_list())
    assert not re.search(r"\b12\.\d+|POTENTIAL|VACATED|ROUTES_FIRST|\bSLEEPER\b", text)
    assert errors == []


@pytest.mark.req(REQ, ac="watch's RISING verdict gives way when the Rising tag fires, and stays for a player without it")
def test_watchs_rising_verdict_gives_way_to_the_rising_tag(mount):
    profile, errors = on_roster(mount, size=PHONE)
    tags = TagsPage(profile.page)
    tags.plant_verdict("RISING")
    profile.open_from_roster("Jahmyr Gibbs")
    assert not tags.verdict_shown() and tags.profile_has_list()
    profile.close()
    profile.open_from_roster("Amon-Ra St. Brown")
    assert tags.verdict_shown() and not tags.profile_has_list()
    assert errors == []


@pytest.mark.req(REQ, ac="no block draws no pill on any row and no list in the profile")
def test_with_no_block_nothing_is_drawn(no_block):
    profile, errors = on_roster(no_block, size=PHONE)
    tags = TagsPage(profile.page)
    assert set(tags.roster_tags().values()) == {None}
    profile.open_from_roster("Joe Burrow")
    assert not tags.profile_has_list()
    assert errors == []
