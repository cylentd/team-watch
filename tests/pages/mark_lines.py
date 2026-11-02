"""The numbers a not-backtested mark sits beside (S10, David's ruling of 2026-11-01).

pages/marks.py reads the nearest block of the element that carries a mark. That misses a mark that sits on a column
head, a row label or a player header, where the numbers it speaks for are in the cells, lanes or lines beside it.
Here a mark's "beside" is named per kind of row, and `MarkLines(page).beside(...)` returns the text of exactly those
numbers, the mark itself taken out. A test then asserts a digit in each; no read here looks at the rest of the page.

A carrier is an element in the open view, the profile or the leg sheet whose `title` or own text holds the mark.
Reads return plain data (lists of strings); none asserts. The plant methods set state the fixture lacks, in the page
after mount, never in tests/fixtures.
"""

ROOTS = "#view *, #modal *, #legsheet *"

HOLDS = """(e, text) => (e.getAttribute('title') || '').includes(text)
  || (e.children.length === 0 && e.textContent.includes(text))"""

SQ = "s => s.replace(/\\s+/g, ' ').trim()"

# the words of each `numSel` element inside the carrier's closest `rowSel`, the mark taken out
BESIDE = """([text, rowSel, numSel]) => {
  const holds = %s, sq = %s;
  return [...document.querySelectorAll('%s')].filter(e => holds(e, text)).map(e => {
    const row = e.closest(rowSel);
    return row ? [...row.querySelectorAll(numSel)].map(n => sq(n.textContent.split(text).join(''))) : [];
  });
}""" % (HOLDS, SQ, ROOTS)

# the body cells in the column of the head cell that carries the mark
COLUMN = """(text) => {
  const holds = %s, sq = %s;
  return [...document.querySelectorAll('%s')].filter(e => e.tagName === 'TH' && holds(e, text)).map(th => {
    const table = th.closest('table'), at = th.cellIndex;
    return [...table.querySelectorAll('tbody tr')].map(tr => sq(tr.cells[at].textContent));
  });
}""" % (HOLDS, SQ, ROOTS)

# Cincinnati's priciest WR (Higgins) is OUT in the fixture's pool; a cheaper teammate makes the handcuff tag
HANDCUFF = """() => {
  dfsSite().pool.push({n: 'Plant Handcuff', pos: 'WR', team: 'CIN', game: 'CIN@NYJ', sal: 10, proj: 6.1, status: null});
  render();
}"""

# two backs compared on Start/Sit, the first one's weather a cold -0.4 (the fixture has no wx)
COMPARE = """() => {
  const backs = LIVE_RANKS.rows.filter(r => r.pos === 'RB').slice(0, 2).map(r => r.slug);
  LIVE_PROJECTIONS.players[backs[0]].wx = {cond: ['cold'], adj: -0.4};
  SS_PICKS = backs; SS_OPEN = false; SS_Q = ''; SS_CMP = true; render();
}"""

# a hand-written role note on Higgins' lines, which draws the Role tag on his Build header
ROLE_NOTE = "() => { PROPS.filter(p => p.n === 'Tee Higgins').forEach(p => { p.role_note = 'Hand-written role note.'; }); render(); }"


class MarkLines:
    def __init__(self, page):
        self.page = page

    def beside(self, text, row, numbers):
        """One list per carrier of `text`: the words of each `numbers` element inside the carrier's closest `row`."""
        return self.page.evaluate(BESIDE, [text, row, numbers])

    def column(self, text):
        """One list per head cell carrying `text`: the words of the cells under it, down its table."""
        return self.page.evaluate(COLUMN, text)

    def plant_handcuff(self):
        self.page.evaluate(HANDCUFF)

    def compare_two_backs(self):
        self.page.evaluate(COMPARE)

    def plant_role_note(self):
        self.page.evaluate(ROLE_NOTE)
