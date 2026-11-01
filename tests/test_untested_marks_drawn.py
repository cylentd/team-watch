"""S10, an untested number says so, as drawn: "an untested number says 'not backtested'" (PRODUCT.md Principles 1 and 5;
David ruled the label a hard rule on 2026-10-31).

test_flag_marks.py proves each mark key's copy says Untested or Failed test. This file proves the view draws it: for
each key, the mounted view puts `words(key)` on an element (a tap or tooltip, or a foot's own text) whose line also
draws a number. The words are read through `words`, never retyped, so a rewording is a content.json edit only.

Covered views: Ranks, Waivers, Slips, Preview, the Digest on Wednesday and Friday, Weather in a cold week.
Not covered (their state is not in the fixture, a finding for a later branch): the profile, Start/Sit, the Teams brief,
the trade finder, DFS and the leg sheet, the Waivers lanes, the Digest's Thursday card.
"""
import re

import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.digest_cards import DigestCardsPage
from pages.marks import MarksPage
from wording import words

PLAIN = [("ranks", "ranks.row.mxMark"), ("waivers", "waiver.tier.mark"), ("waivers", "waiver.swap.mark"),
         ("waivers", "waiver.rail.pathMark"), ("parlay", "slips.tier.mark"), ("preview", "preview.conf.mark"),
         ("preview", "preview.call.mark")]
DIGEST = [("wed", "digest.card.usage.mark"), ("wed", "digest.card.defenses.foot"), ("fri", "digest.foot.muMark"),
          ("fri", "matchups.takes.markSmash")]


def drawn_beside_a_number(marks, key):
    carriers = marks.carriers(words(key))
    return bool(carriers) and any(re.search(r"\d", c["block"]) for c in carriers)


@pytest.mark.render
@pytest.mark.parametrize(("surface", "key"), PLAIN)
def test_a_view_draws_each_untested_mark_on_a_line_with_a_number(mount, surface, key):
    page, errors = mount(surface, size=(360, 800))
    assert drawn_beside_a_number(MarksPage(page), key), f"{surface} does not draw {key} beside a number"
    assert errors == []


@pytest.mark.render
@pytest.mark.parametrize(("day", "key"), DIGEST)
def test_the_digest_draws_each_untested_mark_on_a_line_with_a_number(mount, day, key):
    page, errors = mount("digest", size=(360, 800))
    DigestCardsPage(page).on(day)
    assert drawn_beside_a_number(MarksPage(page), key), f"the Digest on {day} does not draw {key} beside a number"
    assert errors == []


@pytest.mark.render
def test_a_cold_forecast_draws_the_cold_mark_on_its_temperature(mount):
    page, errors = mount("weather", size=(360, 800))
    marks = MarksPage(page)
    marks.plant_cold_week()
    assert drawn_beside_a_number(marks, "weather.cond.coldMark")
    assert errors == []
