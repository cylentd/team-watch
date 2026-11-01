"""How wide a mounted page draws against its window (scenario S1: a 360px phone, no sideways scroll).

Methods return plain data; none asserts.
"""


class PageWidth:
    def __init__(self, page):
        self.page = page

    def widths(self):
        """(scrollWidth, clientWidth) of the document: scrollWidth above clientWidth is a sideways scroll."""
        return tuple(self.page.evaluate(
            "[document.documentElement.scrollWidth, document.documentElement.clientWidth]"))

    def widest_elements(self, limit=3):
        """The elements reaching furthest right, as 'tag.class right-edge', for a failure message."""
        return self.page.evaluate(
            """n => [...document.querySelectorAll('body *')]
              .map(e => [e.tagName.toLowerCase() + '.' + String(e.className).slice(0, 40), Math.round(e.getBoundingClientRect().right)])
              .sort((a, b) => b[1] - a[1]).slice(0, n).map(x => x.join(' '))""", limit)
