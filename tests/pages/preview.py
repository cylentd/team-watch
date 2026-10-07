"""This week > Preview (design/src/js/surface/preview/): the slate of every game by kickoff window and a game's
dossier (answer, headline, call, box score, player calls). Past games is `PreviewPage.record`
(pages/preview_record.py) and the hand-off to Slips is `PreviewPage.handoff` (pages/preview_handoff.py).

Every locator lives here, data-testid first (`preview-*`, test hooks only: no CSS or JS reads them). Three things
have no hook, so they are found by attribute or class: the index of a game (`data-pvopen`, a parameter a test id
cannot carry), the classes a state wears (`.open`, `.rec`, `.cur`), and the classes of parts a test proves are gone
(`.pv-pb`, `.pv-note`, ...). The confidence word (`.pv-conf`) is drawn by data/preview.js, outside surface/preview/.

`PreviewPage` is the view mounted (tests/component.py) or on the full page. Reads return plain data and no method
asserts. State a tap cannot reach (a game that is over) is planted by a method named for it; the page draws again,
the way it would.
"""
import re

from pages.preview_handoff import PreviewHandoff
from pages.preview_record import PreviewRecord

SWIPE = """(el, dx) => {
  const t = x => new Touch({identifier: 1, target: el, clientX: x, clientY: 300});
  el.dispatchEvent(new TouchEvent('touchstart', {touches: [t(200)], changedTouches: [t(200)], bubbles: true}));
  el.dispatchEvent(new TouchEvent('touchend', {touches: [], changedTouches: [t(200 + dx)], bubbles: true}));
}"""
WINDOWS = """ws => ws.map(w => [w.querySelector('[data-testid="preview-win-name"]').textContent,
  [...w.querySelectorAll('[data-testid="preview-row-match"]')].map(r => r.textContent)])"""
LIME = """slate => { const lime = getComputedStyle(document.documentElement).getPropertyValue('--lime').trim();
  const probe = document.createElement('i'); probe.style.color = lime; document.body.append(probe);
  const rgb = getComputedStyle(probe).color; probe.remove();
  return [...slate.querySelectorAll('*')].filter(e => e.children.length === 0 &&
    (getComputedStyle(e).color === rgb || getComputedStyle(e).backgroundColor === rgb)).map(e => e.innerText.trim()); }"""
INK = """() => ['--ink', '--ink-2'].map(v => { const e = document.createElement('i');
  e.style.color = `var(${v})`; document.body.append(e); const c = getComputedStyle(e).color; e.remove(); return c; })"""
FACES = """cases => cases.map(c => pvFacePlayer(c).n)"""
CHILD_CLASSES = "e => [...e.children].map(c => c.className)"
CLASS_AT_1 = "rs => rs.map(r => r.classList[1])"
ENDED = """([idx, hours]) => { const t = new Date(Date.now() - hours * 3600e3).toISOString();
  idx.forEach(i => LIVE_PREVIEW.games[i].kickoff = t); render(); }"""


def squash(s):
    return re.sub(r"\s+", " ", s).strip()


class PreviewPage:
    def __init__(self, page):
        self.page = page
        tid = page.get_by_test_id
        self._root, self._slate, self._rows = tid("preview-root"), tid("preview-slate"), tid("preview-row")
        self._folds, self._dossier, self._article = tid("preview-fold"), tid("preview-dossier"), tid("preview-article")
        self._answer, self._bets, self._header = tid("preview-answer"), tid("preview-bets"), tid("preview-header")
        self._deks, self._sections, self._wins = tid("preview-dek"), tid("preview-section"), tid("preview-win")
        self.record, self.handoff = PreviewRecord(page), PreviewHandoff(page)

    # ---- what a reader does ----

    def tap_game(self, i):
        """Tap game `i` (kickoff order) on the slate."""
        self._row(i).click()

    def show_game(self, i):
        """Game `i`'s dossier open, by state, with no history entry."""
        self.page.evaluate(f"() => {{ PV_I = {i}; PV_OPEN = true; render(); }}")

    def close_dossier(self):
        self.page.evaluate("() => { PV_OPEN = false; render(); }")

    def step(self, d):
        """The dossier's arrow: -1 the game before, 1 the one after."""
        (self.page.get_by_test_id("preview-step").first if d < 0 else self.page.get_by_test_id("preview-step").last).click()

    def swipe(self, dx):
        self._article.evaluate(SWIPE, dx)

    def tap_back(self):
        """The dossier's back button (to the slate, or to Past games when it opened from there)."""
        self.page.get_by_test_id("preview-back").first.click()

    def open_record(self, wk=None):
        """Past games: from the first row under the slate, or straight to a week as a slate row would."""
        if wk is None:
            self._folds.first.click()
        else:
            self.page.evaluate(f"() => pvRecOpen({wk})")
        self.page.wait_for_function("document.querySelector('.pv').classList.contains('rec')")

    def scroll_to(self, y):
        self.page.evaluate(f"window.scrollTo(0, {y})")

    def scroll_fold_into_view(self):
        """Scrolled down to the first Past-games row, centred: the phone's bottom bar covers the last 64px."""
        self._folds.first.evaluate("e => e.scrollIntoView({block: 'center'})")

    def tap_player(self, n):
        self.page.get_by_test_id("preview-player").nth(n).click()

    def tap_name(self, name):
        """A bold name in the story."""
        self._deks.get_by_role("button", name=name, exact=True).click()

    def browser_back(self):
        self.page.go_back()

    def wait_for_dossier_closed(self):
        self.page.wait_for_function("!document.querySelector('.pv').classList.contains('open')")

    def wait_for_record_closed(self):
        self.page.wait_for_function("!document.querySelector('.pv').classList.contains('rec')")

    def wait_for_scroll(self, y):
        self.page.wait_for_function(f"scrollY === {y}")

    def wait_for_slate_at(self, y):
        self.page.wait_for_function(f"scrollY === {y} && !!document.querySelector('.pv-slate')")

    def spy_on_profile(self):
        """The profile sheet is another view's: replace the opener with one that records the slug."""
        self.page.evaluate("() => { window.__opened = []; openProfile = p => window.__opened.push(p.slug); }")

    # ---- what a test plants ----

    def end_games(self, *idx, hours=5):
        """Games `idx` that many hours past kickoff, so the page counts them over (the grace is 4 hours)."""
        self.page.evaluate(ENDED, [list(idx), hours])

    # ---- the slate ----

    def windows(self):
        """[[window name, [matchups]]] in order."""
        return self._wins.evaluate_all(WINDOWS)

    def first_window_time(self):
        return self.page.get_by_test_id("preview-win-time").first.inner_text()

    def title(self):
        return self.page.get_by_test_id("preview-title").inner_text()

    def slate_visible(self):
        return self._slate.is_visible()

    def slate_text(self):
        return self._slate.inner_text()

    def matches(self):
        """The matchup of every row left on the slate."""
        return self._squashed(self.page.get_by_test_id("preview-row-match"))

    def row_text(self, i):
        return self._row(i).inner_text()

    def row_ats_count(self, i):
        return self._row(i).get_by_test_id("preview-row-ats").count()

    def ats_words(self):
        return self._squashed(self.page.get_by_test_id("preview-row-ats"))

    def row_face_count(self, i):
        return self._row(i).get_by_test_id("preview-row-face").locator("img, .fallback").count()

    def lime_words(self):
        """The text of every leaf on the slate drawn in the lime."""
        return self._slate.evaluate(LIME)

    def legacy_slate_parts(self):
        """Parts the quiet slate dropped: a bar, a key, a meta line, flags."""
        return self._slate.locator(".pv-pb, .pv-key, .pv-meta, .pv-f").count()

    def side_word_count(self):
        """The "getting 2.5" a row used to show right of the matchup."""
        return self._rows.locator(".pv-side").count()

    def window_head_font(self):
        return self.page.get_by_test_id("preview-win-head").first.evaluate("e => getComputedStyle(e).fontFamily")

    def row_head_font(self):
        return self.page.get_by_test_id("preview-row-head").first.evaluate("e => getComputedStyle(e).fontFamily")

    def serif_colours(self):
        """[a window head's colour, game 1's headline's, a matchup's] and the site's [--ink, --ink-2] as colours."""
        got = [self.page.get_by_test_id("preview-win-head").first, self._row(1).get_by_test_id("preview-row-head"),
               self.page.get_by_test_id("preview-row-match").first]
        return [e.evaluate("e => getComputedStyle(e).color") for e in got], self.page.evaluate(INK)

    def ground(self):
        return self._root.evaluate("e => getComputedStyle(e).borderImageSource")

    def face_players(self, cases):
        """The player the slate's face is for, per case {head, players: [{n}]}."""
        return self.page.evaluate(FACES, cases)

    def window_count(self):
        return self._wins.count()

    def all_over_text(self):
        return self.page.get_by_test_id("preview-allover").inner_text()

    def fold_texts(self):
        return self._squashed(self._folds)

    def fold_edges(self):
        """(the Past-games row's top, the last window's bottom): the row sits under the games."""
        return (self._folds.first.evaluate("e => e.getBoundingClientRect().top"),
                self._wins.last.evaluate("e => e.getBoundingClientRect().bottom"))

    def current_row_match(self):
        """The matchup of the row marked as the one on screen (a desktop)."""
        return self._rows.and_(self.page.locator(".cur")).get_by_test_id("preview-row-match").inner_text()

    def current_row_count(self):
        return self._rows.and_(self.page.locator(".cur")).count()

    def current_fold_count(self):
        return self._folds.and_(self.page.locator(".cur")).count()

    # ---- the dossier ----

    def is_open(self):
        return self._root.evaluate("e => e.classList.contains('open')")

    def dossier_visible(self):
        return self._dossier.is_visible()

    def dossier_count(self):
        return self._dossier.count()

    def dossier_text(self):
        return self._dossier.inner_text()

    def match(self):
        """The game the dossier is on (or, in Past games, the week stepper's label: the page's first `.pv-mt`)."""
        return self.page.get_by_test_id("preview-match").first.inner_text()

    def back_text(self):
        return self.page.get_by_test_id("preview-back").first.inner_text()

    def kickoff_text(self):
        return self.page.get_by_test_id("preview-kickoff").inner_text()

    def parts(self):
        """The classes of the article's children, in order: the answer, headline, call, box score, story."""
        return self._article.evaluate(CHILD_CLASSES)

    def answer_text(self):
        return self._answer.inner_text()

    def score(self):
        return self._answer.get_by_test_id("preview-score").inner_text()

    def score_count(self):
        return self._answer.get_by_test_id("preview-score").count()

    def bet_heads(self):
        return self._squashed(self._bets.locator("thead th"))

    def bet_rows(self):
        """Each bet's cells: [label, Vegas, Claude]."""
        return self._bets.get_by_test_id("preview-bet").evaluate_all(
            "rs => rs.map(r => [...r.children].map(c => c.innerText.replace(/\\s+/g, ' ').trim()))")

    def bet_ids(self):
        return self._bets.get_by_test_id("preview-bet").evaluate_all("rs => rs.map(r => r.className)")

    def bet_no_edge_count(self, bet):
        """The "no edge" confidence marks in a bet's row ("spread" or "total")."""
        return self._bets.get_by_test_id("preview-bet").and_(self.page.locator("." + bet)).locator(".pv-conf.none").count()

    def answer_bar_count(self):
        return self._answer.locator(".pv-pb").count()

    def section_kinds(self):
        """The box score's rows by kind, in order (matchup, handoff, inj, ds, wx, rest)."""
        return self._sections.evaluate_all(CLASS_AT_1)

    def section_text(self, kind):
        return self._section(kind).inner_text()

    def section_count(self, kind):
        return self._section(kind).count()

    def forecast_text(self):
        return self._section("wx").get_by_test_id("preview-forecast").inner_text()

    def effects_text(self):
        return self.page.get_by_test_id("preview-effects").inner_text()

    def injury_text(self, n):
        return self.page.get_by_test_id("preview-injuries").nth(n).inner_text()

    def short_tag_count(self):
        return self._section("rest").get_by_test_id("preview-rest-short").count()

    def matchup_count(self):
        return self.page.get_by_test_id("preview-matchup").count()

    def dim_matchup_row(self):
        return self.page.get_by_test_id("preview-matchup").locator("tr.dim").inner_text()

    def headline_font(self):
        return self.page.get_by_test_id("preview-headline").evaluate("e => getComputedStyle(e).fontFamily")

    def dek_texts(self):
        return self._squashed(self._deks)

    def dek_fonts(self):
        return self._deks.evaluate_all("ps => ps.map(p => getComputedStyle(p).font)")

    def name_buttons(self):
        """The bold names in the story, in order."""
        return self._deks.get_by_role("button").all_inner_texts()

    def first_name_weight(self):
        return self._deks.get_by_role("button").first.evaluate("e => getComputedStyle(e).fontWeight")

    def call_text(self):
        return self.page.get_by_test_id("preview-call").inner_text()

    def call_count(self):
        return self.page.get_by_test_id("preview-call").count()

    def header_text(self):
        return self._header.inner_text()

    def risk_text(self):
        return self.page.get_by_test_id("preview-risk").inner_text()

    def risk_count(self):
        return self.page.get_by_test_id("preview-risk").count()

    def story_count(self):
        return self.page.get_by_test_id("preview-story").count()

    def players_count(self):
        return self.page.get_by_test_id("preview-players").count()

    def projections(self):
        return self._squashed(self.page.get_by_test_id("preview-player-proj"))

    def story_texts(self):
        """The answer, the headline and the call, in the order they are drawn."""
        both = self._answer.or_(self._header).or_(self.page.get_by_test_id("preview-call"))
        return self._squashed(both)

    def notes_and_footnotes(self):
        """Research notes and footnotes: the dossier no longer draws either."""
        return self.page.locator(".pv-dz .pv-note, .pv-foot").count()

    def score_and_reason_lines(self):
        """(score lines, one-line reasons) drawn: the answer block and the call replaced both."""
        return self.page.locator(".pv-score").count(), self.page.locator(".pv-vs").count()

    def uppercase_labels(self):
        """Section names and run-in words set in capitals: none."""
        return self._article.evaluate("""a => [...a.querySelectorAll('.pva-h, .pv-rin, .pv-k')]
          .filter(e => getComputedStyle(e).textTransform === 'uppercase').length""")

    def answer_box(self):
        """The first screen: {ans: [top, bottom], head: top, dek: top, vh} of the answer, headline and first paragraph."""
        return self.page.evaluate("""() => { const r = t => document.querySelector(`[data-testid="${t}"]`).getBoundingClientRect();
          return {ans: [r('preview-answer').top, r('preview-answer').bottom], head: r('preview-header').top,
                  dek: r('preview-dek').top, vh: innerHeight}; }""")

    def edges(self, kind):
        """[left, top, right] of the slate, the dossier, the call or the box score."""
        return self.page.get_by_test_id(f"preview-{kind}").evaluate("b => { const r = b.getBoundingClientRect(); return [r.left, r.top, r.right]; }")

    # ---- the page's own state ----

    def scroll_y(self):
        return self.page.evaluate("scrollY")

    def scroll_width(self):
        return self.page.evaluate("document.documentElement.scrollWidth")

    def hash(self):
        return self.page.evaluate("location.hash")

    def layers(self):
        return self.page.evaluate("LAYERS.length")

    def opened_profiles(self):
        return self.page.evaluate("window.__opened")

    def wait_for_view(self, leaf):
        self.page.wait_for_function(f"SURFACE === '{leaf}'")

    # ---- helpers ----

    def _row(self, i):
        return self._rows.and_(self.page.locator(f"[data-pvopen='{i}']"))

    def _section(self, kind):
        return self._sections.and_(self.page.locator("." + kind))

    @staticmethod
    def _squashed(loc):
        return [squash(t) for t in loc.all_inner_texts()]
