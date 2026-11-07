"""Rule 22 on a phone: the top pickup's card, the feature of the reading hold, holds 40% of the frame; before he
lands, #3 and #2 are the subject and fill the frame under the title."""
import pytest

from component import mount
from pages.madden_waivers import WaiversFilm, STRIP_HOLD, PAIR_HOLD

PAIR_SHARE = .33     # of the frame's height the #3 and #2 pair holds while it is the subject (David, 2026-11-05)
PAIR_FACE = .15      # of the frame's height each pair portrait is drawn at, at least (59px was 7%)
PAIR_CENTRE = .04    # of the frame's height the gaps above and below the pair may differ by


@pytest.mark.parametrize("width,height", [(390, 844), (360, 800)])
def test_phone_pair_fills_the_frame_centred_under_the_title(mount, width, height):
    film = WaiversFilm(mount.browser, width, height)
    with film:
        film.load()
        film.seek(PAIR_HOLD)
        film.require_hold('pair')
        pair = film.pair_frame()
        assert pair['bottom'] - pair['top'] >= height * PAIR_SHARE, pair
        assert all((height * PAIR_FACE <= drawn <= natural) for (drawn, natural) in zip(pair['faces'], pair['natural'])), [pair for (drawn, natural) in zip(pair['faces'], pair['natural'])]
        assert abs((pair['top'] - pair['title']) - (height - pair['bottom'])) <= height * PAIR_CENTRE, pair
        geometry = film.geometry('pair')
        assert geometry["visible"] and geometry["within"] and not geometry["overlaps"], geometry


@pytest.mark.parametrize("width,height", [(390, 844), (360, 800)])
@pytest.mark.parametrize("seconds", [57.5, STRIP_HOLD])   # 2026-11-05 (David reapproved, +2 s Chapter 3). ~~57.5~~.
def test_phone_top_pickup_occupies_forty_percent(mount, width, height, seconds):
    film = WaiversFilm(mount.browser, width, height)
    with film:
        film.load()
        film.seek(seconds)
        film.require_hold('strip')
        subject = film.card('1').bounding_box()
        assert subject["height"] >= height * .4, subject
        geometry = film.geometry('strip')
        assert geometry["visible"] and geometry["within"] and not geometry["overlaps"], geometry
