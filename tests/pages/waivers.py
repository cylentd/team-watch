"""League > Waivers (leaf `waivers`) as a visitor sees it, and the one roster line that carries his waiver advice.

No test ids yet: another branch is changing surface/teams/waiver.js, data/waiver.js and chrome/nav.js, so every
locator here is an existing class or id (`.wv-hot`, `.wvc`, `.wvr-row`, `.wvhero`, `#subnav .tabcount`). When that
branch lands, test ids replace them in this file and nowhere else.

A visitor is a browser without David's owner token (data/owner.js): `view_as_visitor` clears it and draws a leaf
again, which is how the suite's seeded page (an owner by default) becomes everyone else's. Methods return plain
data; none asserts. `#subnav` is the nav row, read only for the count badge a waiver tab would carry.
"""


class WaiversPage:
    def __init__(self, page):
        self.page = page
        self._hot = page.locator(".wv-hot li")

    # ---- who is looking ----

    def view_as_visitor(self, leaf="waivers"):
        """Clear the owner token and draw `leaf` again, as a first-time visitor's browser would."""
        self.page.evaluate(f"localStorage.setItem('tw-owner', ''); SURFACE = '{leaf}'; SEARCH_INDEX = null; render(); paintSubnav()")

    def is_owner(self):
        return self.page.evaluate("isOwner()")

    def hash(self):
        return self.page.evaluate("location.hash")

    def wait_for_hash(self, value, timeout=5000):
        self.page.wait_for_function("h => location.hash === h", arg=value, timeout=timeout)

    # ---- the digest's adds the Most added list draws ----

    def digest_adds_count(self):
        """How many adds the page's digest packet carries (0 with no packet)."""
        return self.page.evaluate("(typeof LIVE_DIGEST !== 'undefined' && LIVE_DIGEST ? LIVE_DIGEST.adds : []).length")

    def plant_digest(self, fields):
        """Merge `fields` into the page's digest packet and drop its cut, so the next draw reads them."""
        self.page.evaluate("f => { Object.assign(LIVE_DIGEST, f); DG_CUT = null; }", fields)

    # ---- what Waivers draws ----

    def most_added_count(self):
        return self._hot.count()

    def most_added_counts(self):
        """The count line of each Most added row, in order."""
        return self.page.locator(".wv-hot-pct").all_inner_texts()

    def most_added_source(self):
        """The line under the list's title that names where the counts come from."""
        return self.page.locator(".wv-hot-sub").inner_text()

    def claim_card_count(self):
        """David's claim cards (`.wvc`): none for a visitor."""
        return self.page.locator(".wvc").count()

    def claim_row_count(self):
        """The rows of his claim list (`.wvr-row`): none for a visitor."""
        return self.page.locator(".wvr-row").count()

    def hero_text(self):
        return self.page.locator(".wvhero").inner_text()

    def subnav_count_badges(self):
        """Count badges on the sub-row's tabs: a waiver count shows only to the owner."""
        return self.page.locator("#subnav .tabcount").count()
