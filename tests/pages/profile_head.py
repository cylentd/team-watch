"""The profile's head and strip (design/src/js/surface/profile/): the name block, the verdict and injury lines,
the head rail, the strip of cells and its notes, the link to Usage, and the league owners.

Every locator is a `profile-*` data-testid (test hooks only), through the modal's `_tid`; a few reads go past
one because the element is drawn outside surface/profile/ (the "No line" tag, `.pf-noline`, rbrules.js).

`ProfileHead` extends `ProfileSheet` (pages/profile_sheet.py) and is the base of `ProfilePage` (pages/profile.py):
one object, one API for a test.
"""
from pages.profile_sheet import ProfileSheet


class ProfileHead(ProfileSheet):
    # ---- the head ----

    def title(self):
        return self._tid("profile-title").inner_text()

    def has_title(self):
        return self._tid("profile-title").count() == 1

    def identity(self):
        return self._tid("profile-identity").inner_text()

    def text(self):
        return self._modal.inner_text()

    def page_text(self):
        return self.page.locator("body").inner_text()

    def tags(self):
        """The verdict line under the head, or None: {verdict, why, text}."""
        box = self._tid("profile-tags")
        if box.count() == 0:
            return None
        why = self._tid("profile-why")
        return {"verdict": self._tid("profile-verdict").inner_text().strip(),
                "why": why.inner_text() if why.count() else None, "text": box.inner_text()}

    def owner_marks(self):
        """The retired "On N of your teams" line (`.pf-mine`, 2026-09-28): none."""
        return self._modal.locator(".pf-mine").count()

    def injury(self):
        """The injury line of the name block, or None; with where it sits."""
        box = self._tid("profile-inj")
        if box.count() == 0:
            return None
        return box.evaluate("""e => { const lbl = document.querySelector('#modal [data-testid="profile-identity"]');
          return {cls: e.className, word: e.querySelector('[data-testid="profile-inj-word"]').textContent.trim(),
                  note: (e.querySelector('[data-testid="profile-inj-note"]') || {}).textContent || null,
                  in_who: !!e.closest('[data-testid="profile-who"]'), after_id: lbl.nextElementSibling === e,
                  below_id: e.getBoundingClientRect().top >= lbl.getBoundingClientRect().bottom}; }""")

    def rail_survey(self):
        """Open every skill player and group them by what their head rail holds, in order:
        {"role,style,orb,cmp": {centred, small_compare}, "none": ...}, one example of each shape."""
        return self.page.evaluate("""() => {
          const kinds = () => [...document.querySelectorAll('#modal [data-testid="profile-rail"] > *')].map(e =>
            e.matches('[data-pfarch=role]') ? 'role' : e.matches('[data-pfarch=style]') ? 'style' : e.matches('.pf-orb') ? 'orb' : 'cmp');
          const centred = () => { const r = document.querySelector('#modal [data-testid="profile-rail"]'), k = [...r.children];
            const a = k[0].getBoundingClientRect().left - r.getBoundingClientRect().left;
            const b = r.getBoundingClientRect().right - k[k.length - 1].getBoundingClientRect().right;
            return Math.abs(a - b) <= 2; };
          const out = {};
          for (const e of searchIndex().filter(e => ['RB', 'WR', 'TE', 'QB'].includes(e.pos))){
            openProfile(searchPlayer(e));
            const has = document.querySelector('#modal [data-testid="profile-rail"]');
            const key = has ? kinds().join(',') : 'none';
            if (out[key]) continue;
            out[key] = {centred: has ? centred() : null,
                        small_compare: !has && !!document.querySelector('#modal [data-testid="profile-who"] > [data-testid="profile-compare-open"]')};
          }
          return out; }""")

    def fits(self):
        return self.page.evaluate("document.documentElement.scrollWidth <= innerWidth")

    # ---- the strip, the grid link, the owners ----

    def strip(self):
        """The strip's cells in order: value, label, whether it is the projection."""
        return self._tid("profile-lede-cell").evaluate_all("""cs => cs.map(c => ({
          value: c.querySelector('[data-testid="profile-lede-value"]').innerText,
          label: c.querySelector('[data-testid="profile-lede-label"]').innerText, proj: c.classList.contains('proj')}))""")

    def notes(self):
        """The strip's notes, as read."""
        return self._tid("profile-lede-note").all_inner_texts()

    def noline_tips(self):
        """The tooltip of every "No line" tag on the strip (drawn by data/rbrules.js: no testid); [] when none."""
        return self._modal.locator(".pf-noline").evaluate_all("ts => ts.map(t => t.title)")

    def projection(self, slug):
        return self.page.evaluate("s => projFor({slug: s}).toFixed(1)", slug)

    def ppg_rank(self, slug, pos):
        return self.page.evaluate("([s, p]) => ppgRank({slug: s, pos: p})", [slug, pos])

    def pool_size(self, pos):
        return self.page.evaluate("p => LIVE_POOL.players.filter(r => r.pos === p && r.ppg !== null).length", pos)

    def grid_link(self):
        """The link to his row in Usage: {text, height, slug}, or None."""
        link = self._tid("profile-grid-link")
        if link.count() == 0:
            return None
        return {"text": link.inner_text(), "height": link.bounding_box()["height"], "slug": link.get_attribute("data-pfgrid")}

    def follow_grid_link(self):
        self._tid("profile-grid-link").click()

    def grid_link_markup(self, player):
        return self.page.evaluate("p => pfGridLinkHTML(p)", player)

    def usage_hits(self, slug):
        """Usage's rows that carry the arrival highlight for him (usage.js, not the profile's)."""
        return self.page.locator(f"[data-usage='{slug}'].nav-hit").count()

    def surface(self):
        return self.page.evaluate("SURFACE")

    def hash(self):
        return self.page.evaluate("location.hash")

    def view(self):
        return self.page.evaluate("VIEW")

    def my_team(self):
        return self.page.evaluate("myTeamLoad()")

    def team_name(self, key):
        return self.page.evaluate("k => TEAMS[k].name", key)

    def owners(self):
        """One pill per league: {text, mine, free, button, key}."""
        return self._tid("profile-owner").evaluate_all("""ps => ps.map(p => ({
          text: p.innerText.replace(/\\s+/g, ' ').trim(), mine: p.classList.contains('mine'), free: p.classList.contains('free'),
          button: p.tagName === 'BUTTON', key: p.dataset.ownteam || null,
          league: p.querySelector('[data-testid="profile-owner-league"]').textContent}))""")

    def follow_owner(self, league):
        self._tid("profile-owner").filter(has=self.page.get_by_test_id("profile-owner-league").filter(has_text=league)).click()

    def owner_league_colours(self):
        return self._tid("profile-owner-league").evaluate_all("els => els.map(e => getComputedStyle(e).backgroundColor)")

    def become_a_leaguemate(self):
        """The browser of someone who followed no owner link and picked no team."""
        self.page.evaluate("localStorage.setItem('tw-owner', ''); localStorage.removeItem('tw-team')")
