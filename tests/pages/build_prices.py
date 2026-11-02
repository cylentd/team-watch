"""All lines (leaf `build`) on DraftKings, the price each line prints (S15, 2026-11-01).

`BuildPrices` is `BuildPage` plus one read: the price printed on a player's line for a market. The row is found by the
player and market its data-prop names (PROPS identifies the row; the price is the text on the screen). Reads return plain
data; none asserts.
"""
from pages.parlay_build import BuildPage

# The price a row prints beside its call: the `<i>` Build draws in DraftKings mode, from the row whose PROPS entry is
# this player's line in this market.
PRICE = """([name, mkt]) => {
  const row = [...document.querySelectorAll('[data-testid="parlay-line"][data-prop]')]
    .find(e => PROPS[+e.dataset.prop].n === name && PROPS[+e.dataset.prop].mkt === mkt);
  return row.querySelector('.bl-call i').textContent;
}"""


class BuildPrices(BuildPage):
    @classmethod
    def open_dk(cls, mount):
        """All lines on DraftKings at a desktop width. (BuildPrices, errors)."""
        return cls.open(mount, book="dk", size=(1280, 900))

    def printed_price(self, name, mkt):
        """The price the line of `name` in market `mkt` prints, as text ("-110", "+160")."""
        return self.page.evaluate(PRICE, [name, mkt])
