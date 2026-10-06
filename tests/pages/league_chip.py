"""The League's one team line (design/src/js/surface/league/switch.js): the chip with the league's name, the line
under it, and the team switch it holds, drawn the same on every League leaf.

The chip is not Roster's or Teams' or Recap's: it is the League's, and it carries no test id yet, so every
locator here is a class or id (`.lgchip`, `.lgchip-lg`, `.lgchip-sub`, `#hdrswitch`). When switch.js gets
`data-testid`s they replace these in this file and nowhere else. Roster's Sheet / Cards switch beside it is
`RosterPage.mode_switch()`.

The header bar's team switch (`#hdrswitch`, chrome/, no test id either) and the sub-row's leaves are read here
too, because the League's tests ask them beside the chip.

`visit(leaf)` walks the League's leaves to read the chip on each; it is the journey helper for "every leaf draws
the same line", and it reads only the chip and whether a hero is still drawn beside it.
"""
DRAWN = "document.getElementById('view').children.length > 0"
RECT = "e => { const r = e.getBoundingClientRect(); return {l: r.left, r: r.right, t: r.top, w: r.width, h: r.height}; }"


def pick_script(key):
    """An init script that makes the reader's team `key` (a TEAMS key) before the page loads."""
    return f'try {{ localStorage.setItem("tw-team", "{key}"); }} catch (e) {{}}\n'


class LeagueChip:
    def __init__(self, page):
        self.page = page
        self._chip, self._sub = page.locator(".lgchip"), page.locator(".lgchip-sub")

    # ---- what the chip draws ----

    def league_name(self):
        """The league the one chip names."""
        return self.page.locator(".lgchip-lg").inner_text()

    def league_text(self):
        """The league's name as the chip's text holds it, trimmed (`league_name` is what shows)."""
        return self.page.locator(".lgchip-lg").text_content().strip()

    def chip_switch_count(self):
        """Team switches inside the chip: 1."""
        return self.page.locator(".lgchip #switch").count()

    def team_name(self):
        """The team the chip's own switch names."""
        return self.page.locator(".lgchip .ts-team").text_content()

    def chip_count(self):
        return self._chip.count()

    def switch_hidden(self):
        """The team switch inside the chip: a phone hides it, the header bar's is the one there."""
        return self.page.locator(".lgchip .teamswitch").is_hidden()

    def header_switch_visible(self):
        return self.page.locator("#hdrswitch").is_visible()

    def old_league_chips(self):
        """The league chips Teams had of its own until 2026-10-05."""
        return self.page.locator(".lg-switch, [data-lgpick]").count()

    def left(self):
        """The chip's left edge, the frame's edge."""
        return self._chip.first.evaluate("e => e.getBoundingClientRect().left")

    def line(self):
        """The chip's box, the league line's box, that line's scroll height, and which team switches show."""
        return {"line": self._chip.first.evaluate(RECT), "sub": self._sub.first.evaluate(RECT),
                "sub_scroll_height": self._sub.first.evaluate("e => e.scrollHeight"),
                "chip_switch_hidden": self.switch_hidden(), "header_switch_visible": self.header_switch_visible()}

    # ---- the reader's pick and the League's leaves ----

    def pick_on_screen_team(self):
        """The team on screen is the reader's, as after any pick."""
        self.page.evaluate("pickTeam(VIEW)")

    def pick(self, key):
        """Choose a team in the chip's own switch (a desktop's): open it, tap the team, wait for it to be the view."""
        self.page.locator(".lgchip [data-tsbtn]").first.click()
        self.page.locator(f".lgchip .ts-item[data-k='{key}']").first.click()
        self.page.wait_for_function("k => VIEW === k", arg=key)

    def pick_team(self, key):
        """Switch the reader's team as the switch does (pickTeam), drawn at once."""
        self.page.evaluate("k => pickTeam(k)", key)

    def has_team(self, key):
        """The page holds team `key` (a build with no AYO files holds no `ayo`)."""
        return self.page.evaluate("k => k in TEAMS", key)

    def view(self):
        """The team on screen (VIEW)."""
        return self.page.evaluate("VIEW")

    def reload(self):
        """Load the page again, as a reader's refresh does; the pick is the team, so it survives."""
        self.page.reload()
        self.page.wait_for_function(DRAWN)

    def league_leaves(self):
        """The League's leaves the sub-row shows."""
        return self.page.evaluate("navTabsOf('league').filter(k => !NAV_HIDDEN.includes(k))")

    def visit(self, leaf):
        """Go to a leaf, to the top, and read its team line: {chips, heroes, name, top}."""
        self.page.evaluate(f"navGo('{leaf}'); window.scrollTo(0, 0)")
        self.page.wait_for_function(f"SURFACE === '{leaf}' && document.querySelector('#view .lgchip')")
        return {"chips": self.page.locator("#view .lgchip").count(), "heroes": self.page.locator("#view .hero").count(),
                "name": self.league_name(), "top": round(self._sub.first.evaluate(RECT)["t"])}

    def back_to_roster(self):
        self.page.evaluate("navGo('roster')")

    def open_old_recap(self):
        """A Yahoo team's old My recap address, as a link from outside would open it."""
        self.page.evaluate("VIEW = 'yahoo'; navGo('myrecap')")

    def surface(self):
        return self.page.evaluate("SURFACE")

    def chrome(self):
        """What a leaf draws above its body besides the chip: heroes, and the chip's team switch."""
        return {"heroes": self.page.locator(".hero").count(), "chip_switch": self.page.locator(".lgchip #switch").count()}

    # ---- the header bar's switch (a phone's) ----

    def open_header_switch(self):
        self.page.click("#hdrswitch [data-tsbtn]")

    def header_switch_teams(self):
        """The team keys the open header switch lists, in order."""
        return self.page.evaluate("[...document.querySelectorAll('#hdrswitch .ts-menu .ts-item[data-k]')].map(b => b.dataset.k)")

    def pick_in_header(self, key):
        self.page.click(f"#hdrswitch .ts-item[data-k='{key}']")

    def header_team(self):
        """The team the header's switch names."""
        return self.page.locator("#hdrswitch .ts-team").text_content()

    # ---- the sub-row and the page ----

    def subnav_leaves(self):
        """The leaves the sub-row draws, in order."""
        return self.page.evaluate("[...document.querySelectorAll('#subnav [data-leaf]')].map(b => b.dataset.leaf)")

    def tap_leaf(self, leaf):
        """Tap a leaf in the sub-row and wait for it to be drawn."""
        self.page.locator(f"[data-leaf='{leaf}']").first.click()
        self.page.wait_for_function("l => SURFACE === l", arg=leaf)

    def open_by_hash(self, leaf):
        """A link from outside: the address's hash names the leaf."""
        self.page.evaluate("l => { location.hash = '#' + l; }", leaf)
        self.page.wait_for_function("l => SURFACE === l", arg=leaf)

    def view_text(self):
        """Everything the open leaf draws, as text."""
        return self.page.locator("#view").text_content()
