"""The Roster's "This week" list (design/src/js/surface/teams/brief.js, folded form in reel.js): a line per thing
to check, "Got it", "Show all", the swipe that checks one line, and the red pill the list's heading carries.

Every locator is a `roster-brief-*` data-testid (test hooks only: no CSS or JS reads them); a line's kind is the
`k-*` class on its testid'd element, and a list folded to its one row is the `.done` class on `roster-brief`.
The pill is `RosterPage.sit_pill` (pages/roster.py); the profile a line opens is `ProfilePage` (pages/profile.py).
"""
from pages.profile import ProfilePage
from pages.roster import RosterPage

# a team's starters out: `n` of them OUT on every team, healthy otherwise, then the roster drawn in `mode`
SITS = """([n, mode]) => { LIVE_INJURY.players = {};
  for (const tm of Object.values(TEAMS)){
    tm.roster.forEach(p => { p.status = null; });
    tm.roster.filter(p => p.start && p.slug && !['K','DST'].includes(p.pos)).slice(0, n)
      .forEach(p => { LIVE_INJURY.players[p.slug] = {s: 'OUT', code: 'IR', note: 'Knee'}; });
  }
  VIEW = 'espn'; ROSTER_MODE = mode; render(); }"""
LINES = "els => els.map(e => ({kind: e.className.match(/k-(\\w+)/)[1], shown: e.offsetParent !== null}))"
RED = """() => { const p = document.querySelector('[data-testid="roster-inj-warn"]'), probe = document.createElement('i');
  probe.style.color = 'var(--down)'; document.body.append(probe);
  const same = getComputedStyle(p).color === getComputedStyle(probe).color; probe.remove(); return same; }"""


class RosterBrief:
    def __init__(self, page):
        self.page = page
        tid = page.get_by_test_id
        self.roster = RosterPage(page)
        self.profile = ProfilePage(page)
        self._lines, self._head = tid("roster-brief-line"), tid("roster-brief-head")
        self._folded = tid("roster-brief").and_(page.locator(".done"))
        self._ok, self._all, self._unfold, self._peek = tid("roster-brief-ok"), tid("roster-brief-all"), tid("roster-brief-unfold"), tid("roster-brief-peek")

    # ---- driving ----

    def show(self, team):
        self.roster.show(team)

    def reload(self):
        self.roster.reload()

    def wire_line(self):
        """The waiver line the brief draws for the team on screen (surface/teams/brief.js)."""
        return self.page.evaluate("briefWire(TEAMS[VIEW])")

    def unfold(self):
        """On a phone the Week plays reel folds the list to its one row; Show opens it."""
        if self._unfold.count():
            self._unfold.click()

    def show_all(self):
        self._all.click()

    def got_it(self):
        self._ok.click()

    def show_checked(self):
        """The Show button on a list whose every line is checked."""
        self._folded.get_by_test_id("roster-brief-peek").click()

    def swipe_first_line(self):
        """A mouse drag across 80% of the first line, from 40px in."""
        box = self._lines.first.bounding_box()
        y = box["y"] + box["height"] / 2
        self.page.mouse.move(box["x"] + 40, y)
        self.page.mouse.down()
        self.page.mouse.move(box["x"] + box["width"] * .8, y, steps=6)
        self.page.mouse.up()

    def wait_for_line_count(self, n):
        self.page.wait_for_function("n => document.querySelectorAll('[data-testid=\"roster-brief-line\"]').length === n", arg=n)

    def plant_sits(self, n, mode):
        """`n` starters OUT on every team and the ESPN roster drawn in `mode` ("sheet" or "cards")."""
        self.page.evaluate(SITS, [n, mode])

    def open_pack(self):
        """Mark this week's pack opened, so no stage covers the roster."""
        self.page.evaluate("w => packMark(TEAMS.espn, w)", self.roster.sched_week())

    # ---- what the list holds ----

    def lines(self):
        """Each line: {kind: its k-* class, shown: whether it takes space}."""
        return self._lines.evaluate_all(LINES)

    def line_count(self):
        return self._lines.count()

    def folded(self):
        """How many lists are folded to their one row."""
        return self._folded.count()

    def peek_buttons(self):
        return self._peek.count()

    def kinds(self):
        return [x["kind"] for x in self.lines()]

    def fits(self, pairs):
        """Whether each (lineup slot, position) pair can be filled, by the page's own rule."""
        return self.page.evaluate("pairs => pairs.map(([slot, pos]) => briefFits(slot, pos))", [list(p) for p in pairs])

    # ---- the heading's pill and where it sits ----

    def sit_pill(self):
        return self.roster.sit_pill()

    def sit_strips(self):
        return self.roster.sit_strips()

    def warn_count(self):
        """Every red pill on the page (the heading's is the only one a list draws)."""
        return self.page.get_by_test_id("roster-inj-warn").count()

    def pill_is_down_colour(self):
        return self.page.evaluate(RED)

    def head_box(self):
        return self._head.bounding_box()

    def pill_box(self):
        return self._head.get_by_test_id("roster-inj-warn").bounding_box()

    def got_it_box(self):
        return self._ok.bounding_box()

    def pill_inside_head(self):
        """Whether the pill's box sits inside the heading's, and its right edge."""
        head, box = self.head_box(), self.pill_box()
        return {"inside": head["y"] <= box["y"] and box["y"] + box["height"] <= head["y"] + head["height"],
                "right": box["x"] + box["width"]}

    # ---- what a swipe must not do ----

    def profile_open(self):
        return self.profile.is_open()
