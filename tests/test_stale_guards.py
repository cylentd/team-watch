"""Stale-news guards (2026-10-04): Preview re-reads Sleeper's status, the News lead pin skips a story a
later one undoes, and Waivers flag a must/worth card whose player is now out. No browser."""
import json
import pathlib
import re

import pytest

from news import is_return, mark_superseded, news_kind, news_player
from preview import live_preview
from waiver import _overlay, live_waiver

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "data"


def slug(n):
    return re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")


def sleeper(*pairs):
    """A status block: Sleeper's records keyed by an id, one per (name, injury code)."""
    return {str(i): {"name": n, "injury": c} for i, (n, c) in enumerate(pairs)}


# ---- Preview ----------------------------------------------------------------------------------------

def preview(status=None):
    raw = json.loads((FIXTURES / "game_previews.json").read_text(encoding="utf-8"))
    return {g["key"].split("_", 2)[2]: g for g in live_preview(raw, slug, status=status)["games"]}


def test_preview_without_status_is_the_morning_take():
    inj = preview()["DET_CAR"]["inj"]
    assert [(r["n"], r["s"]) for r in inj["CAR"]] == [("Jalen Coker", "out")]
    assert [(r["n"], r["s"]) for r in inj["DET"]] == [("Amon-Ra St. Brown", "q")]
    assert not any("changed" in r for rows in inj.values() for r in rows)


def test_preview_fresh_status_wins_and_says_what_moved():
    g = preview(sleeper(("Amon-Ra St. Brown", "Doubtful"), ("Jahmyr Gibbs", "Out"), ("Jalen Coker", "Out")))["DET_CAR"]
    det = {r["n"]: r for r in g["inj"]["DET"]}
    assert (det["Amon-Ra St. Brown"]["s"], det["Amon-Ra St. Brown"]["changed"]) == ("d", True)
    assert (det["Jahmyr Gibbs"]["s"], det["Jahmyr Gibbs"]["changed"]) == ("out", True)               # healthy at noon
    assert [r["s"] for r in g["inj"]["DET"]] == ["out", "d"]                                         # worst first
    coker = g["inj"]["CAR"][0]
    assert coker["s"] == "out" and "changed" not in coker and coker["avg"] == 14.4                  # unchanged


def test_preview_a_player_cleared_since_the_take_drops_out():
    g = preview(sleeper(("Amon-Ra St. Brown", None), ("Jalen Coker", None)))["DET_CAR"]
    assert g["inj"] == {"DET": [], "CAR": []}
    assert not any(f["k"] == "out" for f in g["flags"])        # the key-player flag followed the fresh status


def test_preview_a_player_sleeper_does_not_list_keeps_the_takes_row():
    g = preview(sleeper(("Someone Else", "Out")))["DET_CAR"]
    assert [r["n"] for r in g["inj"]["CAR"]] == ["Jalen Coker"]


def test_preview_out_and_ir_are_one_group_not_a_change():
    row = preview(sleeper(("Jalen Coker", "IR")))["DET_CAR"]["inj"]["CAR"][0]
    assert row["s"] == "ir" and "changed" not in row


# ---- News -------------------------------------------------------------------------------------------

def story(title, desc=None):
    name, slugs = news_player(title)
    it = {"title": title, "desc": desc, "impact": None}
    return {**it, "kind": news_kind(it), "player": name, "slugs": slugs}


def test_a_later_cleared_story_supersedes_an_earlier_out_one():
    items = mark_superseded([                                    # newest first, as load_news sorts them
        story("Cooper Kupp (back) cleared to play Sunday"),
        story("Cooper Kupp (back) ruled out for Sunday"),
        story("Josh Jacobs (knee) ruled out for Sunday")])
    assert [it["kind"] for it in items][1:] == ["out", "out"]
    assert [it["superseded"] for it in items] == [False, True, False]


def test_an_out_story_with_nothing_after_it_stays_the_lead():
    items = mark_superseded([story("Cooper Kupp (back) ruled out for Sunday"),
                             story("Cooper Kupp (back) cleared to play Sunday")])   # the cleared one is OLDER
    assert [it["superseded"] for it in items] == [False, False]


def test_a_later_story_for_another_player_does_not_supersede():
    items = mark_superseded([story("Josh Jacobs (knee) cleared to play"), story("Cooper Kupp (back) ruled out")])
    assert items[1]["superseded"] is False


def test_a_later_bad_news_story_does_not_supersede():
    items = mark_superseded([story("Cooper Kupp (back) will not play Sunday"), story("Cooper Kupp (back) ruled out")])
    assert [it["superseded"] for it in items] == [False, False]


@pytest.mark.parametrize("title", ["Kupp activated from injured reserve", "Kupp removed from injury report",
                                   "Kupp returns to practice", "Kupp cleared for Sunday",
                                   "Kupp will play Sunday", "Kupp active for Sunday"])
def test_a_return_headline_is_a_return(title):
    assert is_return({"title": title})


@pytest.mark.parametrize("title", ["Kupp inactive Sunday", "Kupp signs with active roster",
                                   "Kupp not expected to play", "Kupp not cleared to return", "Kupp ruled out"])
def test_a_headline_that_is_not_a_return_is_not_one(title):
    assert not is_return({"title": title})


def test_the_lead_pin_skips_a_superseded_story():
    js = (ROOT / "design/src/js/surface/news/news.js").read_text(encoding="utf-8")
    assert re.search(r'newsKind\(it\) === "out" && !it\.superseded', js)


# ---- Waivers ----------------------------------------------------------------------------------------

def waivers(status=None):
    feed = FIXTURES / "no-feed.json"          # absent: the packet file is read directly
    return live_waiver(feed, FIXTURES, slug, status=status)


def test_waiver_without_status_keeps_the_packet_order_and_flags_nothing():
    base = waivers()
    assert all(r["status_now"] is None and r["status_flag"] is None for r in base["players"])
    assert [r["tier"] for r in base["players"]][:2] == ["must", "must"]


def test_waiver_a_must_card_now_out_is_flagged_and_sorts_after_its_tier_peers():
    base = [r for r in waivers()["players"] if r["tier"] == "must"]
    first = base[0]
    live = waivers(sleeper((first["n"], "Out")))["players"]
    must = [r for r in live if r["tier"] == "must"]
    assert [r["n"] for r in must] == [r["n"] for r in base[1:]] + [first["n"]]
    flagged = must[-1]
    assert (flagged["status_now"], flagged["tier"]) == ("Out", "must")           # the tier is the packet's own
    assert flagged["status_flag"] == "O"                                         # the packet's own code; the card words it
    assert all(r["status_flag"] is None for r in must[:-1])


def test_waiver_a_card_whose_packet_already_says_out_is_not_flagged():
    rows = [{"slug": "a-b", "tier": "must", "injury": "O"}, {"slug": "c-d", "tier": "must", "injury": "Q"}]
    _overlay(rows, sleeper(("A B", "Out"), ("C D", "Doubtful")), slug)
    assert [(r["status_now"], r["status_flag"]) for r in rows] == [
        ("Out", None), ("Doubtful", "D")]


def test_waiver_questionable_and_a_stash_are_shown_not_flagged():
    rows = waivers()["players"]
    stash = next(r for r in rows if r["tier"] == "stash")
    got = waivers(sleeper((stash["n"], "Out"), (rows[0]["n"], "Questionable")))["players"]
    by = {r["n"]: r for r in got}
    assert by[stash["n"]]["status_now"] == "Out" and by[stash["n"]]["status_flag"] is None   # not a go-get-him tier
    assert by[rows[0]["n"]]["status_now"] is None                                            # Questionable plays


# ---- The build and the page -------------------------------------------------------------------------

def test_build_passes_sleeper_status_to_preview_and_waivers():
    src = (ROOT / "design/build.py").read_text(encoding="utf-8")
    assert "live_preview(load_game_preview(), slugify, load_preview_record(), status=load_status())" in src
    assert "live_waiver(FEED, DWR, slugify, status=load_status())" in src


def test_the_flag_words_are_copy_keys_the_page_uses():
    copy = json.loads((ROOT / "design/src/content.json").read_text(encoding="utf-8"))
    research = (ROOT / "design/src/js/surface/preview/research.js").read_text(encoding="utf-8")
    wcard = (ROOT / "design/src/js/surface/teams/wcard.js").read_text(encoding="utf-8")
    assert "{s}" in copy["waiver.card.nowFlag"] and copy["preview.inj.changed"]
    assert 't("preview.inj.changed")' in research and "r.changed" in research
    assert 't("waiver.card.nowFlag"' in wcard and "r.status_flag" in wcard


def test_every_waiver_flag_code_has_a_word():
    wcard = (ROOT / "design/src/js/surface/teams/wcard.js").read_text(encoding="utf-8")
    words = set(re.findall(r'(\w+): \(\) => t\("waiver\.injury', wcard))
    from waiver import NOW_LABEL
    assert set(NOW_LABEL.values()) <= words
