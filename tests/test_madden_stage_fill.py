"""Chapter 17 (David, 2026-11-04: "the huge black area top-left"): the opening's stage reaches every corner of
the frame. The light rig spans the full width, a faint stand of crowd lights sits behind it, and the haze and
turf run to the edges, so no corner of the settled title's frame is empty black."""
import io

import pytest
from PIL import Image

from component import mount  # noqa: F401  (the shared browser fixture)
from test_madden_opening_clear import SEEK, SIZES, film  # noqa: F401  (the film page fixture)

CORNER = (.25, .3)       # each corner's share of the frame's width and height
BLACK = 12               # a pixel this dark (0-255 luminance) reads as empty
MOST_EMPTY = .5          # at most this share of a corner may be empty


@pytest.mark.parametrize('size', SIZES)
def test_no_corner_of_the_settled_title_is_empty_black(film, size):
    context, page = film(size)
    with context:
        page.add_style_tag(content='.controls{display:none!important}')
        settled = page.evaluate("async () => (await import('./timing.mjs')).TITLE_WORDS.at(-1) + 1")
        page.eval_on_selector('[data-seek]', SEEK, settled)
        page.evaluate("async () => { await document.fonts.ready; await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))); }")
        image = Image.open(io.BytesIO(page.locator('.room').screenshot())).convert('L')
        width, height = image.size
        cw, ch = int(width * CORNER[0]), int(height * CORNER[1])
        for name, (left, top) in {'top-left': (0, 0), 'top-right': (width - cw, 0),
                                  'bottom-left': (0, height - ch), 'bottom-right': (width - cw, height - ch)}.items():
            pixels = list(image.crop((left, top, left + cw, top + ch)).getdata())
            empty = sum(value < BLACK for value in pixels) / len(pixels)
            assert empty <= MOST_EMPTY, f'{name} is {empty:.0%} empty black'  # honest: allow COND_ASSERT each named screenshot region has an independent black-area budget
