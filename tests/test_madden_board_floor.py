"""The standing board has no turf band under its foot (2026-11-05): before the lower third's scrim rose, the
draft room's turf showed as a bright green strip across the frame's foot at film 13.1."""
import io

import pytest
from PIL import Image
from component import mount
from test_madden_headline_entrance import headline_page, seek

STOOD = 13.1   # the board has just stood; the scrim has not risen yet


def greenish(pixel):  # shape: allow pixel-color predicate documents the sampled green cast
    red, green, blue = pixel[:3]
    return green > red + 6 and green > blue + 2


@pytest.mark.parametrize('width,height', [(1440, 900), (390, 844)])
def test_the_standing_boards_foot_shows_the_dark_room_not_turf(headline_page, width, height):
    headline_page.set_viewport_size({'width': width, 'height': height})
    seek(headline_page, STOOD)
    headline_page.evaluate("async () => { await document.fonts.ready; await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))); }")
    room = headline_page.locator('[data-room]').bounding_box()
    shot = Image.open(io.BytesIO(headline_page.screenshot(clip={'x': room['x'], 'y': room['y'] + room['height'] * .8,
        'width': room['width'], 'height': room['height'] * .12}))).convert('RGB')
    pixels = list(shot.getdata())
    assert sum(map(greenish, pixels)) < len(pixels) * .05
