"""The mark that says a number is untested, as the view draws it (S10, 2026-11-01).

A mark is content.json text. A view puts it in a tap or tooltip (`title`, an svg `<title>`) or in a foot's own text.
`MarksPage(page).carriers(text)` returns, for every element in the open view that carries `text` that way, the
words of that element and of its nearest block (the line the number sits in), squeezed to one line each, so a test
can say the mark sits on the element that draws a number. Reads return plain data; none asserts.
"""

CARRIERS = r"""text => {
  const sq = s => s.replace(/\s+/g, ' ').trim(), seen = new Set(), out = [];
  const holds = e => (e.getAttribute('title') || '').includes(text)
    || [...e.children].some(c => c.tagName.toLowerCase() === 'title' && c.textContent.includes(text))
    || (e.children.length === 0 && e.textContent.includes(text));
  for (const e of document.querySelectorAll('#view *')) {
    if (!holds(e) || seen.has(e)) continue;
    seen.add(e);
    const block = e.closest('[data-dgcard]') || e.closest('li, tr, p, h2, h4, details, div') || e;
    out.push({self: sq(e.textContent.split(text).join('')), block: sq(block.textContent.split(text).join(''))});
  }
  return out;
}"""


COLD_WEEK = "() => { Object.values(LIVE_WEATHER.teams).forEach(f => { f.temp_f = 20; }); render(); }"


class MarksPage:
    def __init__(self, page):
        self.page = page

    def plant_cold_week(self):
        """Every forecast at 20 F, the Weather view drawn again: the fixture's own week is mild, and cold is the one
        condition whose mark (weather.cond.coldMark) rides on a number only when the forecast is that cold."""
        self.page.evaluate(COLD_WEEK)

    def carriers(self, text):
        """[{self, block}] for each element of the view carrying `text`, the mark itself taken out of both strings."""
        return self.page.evaluate(CARRIERS, text)
