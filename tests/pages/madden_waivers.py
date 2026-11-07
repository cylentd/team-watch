"""Chapter 3 of the Madden Curse film, Best pickups (showcase/madden-curse/waivers-view.mjs): every locator for
its cards and Love's strip of weeks lives here."""
from playwright.sync_api import expect
from pathlib import Path
from urllib.parse import urlparse

from test_trophy_room import local_file


PAIR_HOLD = 52.9     # film s: #3 and #2 have landed, #1 has not (timing.json waiver-claim)
STRIP_HOLD = 57.8    # film s: the reading hold, every card and week drawn (waiver-starts)
# 2026-11-05 (David reapproved, +2 s Chapter 3). ~~STRIP_HOLD = 59.9~~.
SECTION = '[data-waivers]'
CARD = '[data-pickup="{rank}"]'
CARD_PARTS = ['[data-pickup-rank]', '[data-pickup-name]', '[data-pickup-team]', '[data-pickup-added]', '[data-pickup-starts]']
WEEK = '[data-waivers-week]'
WEEK_PARTS = '[data-week-label], [data-week-rank]'


def waiver_file(route):
    request_path = urlparse(route.request.url).path.lstrip('/')
    if request_path.startswith('heads/'):
        root = Path(__file__).resolve().parents[2]
        asset = (root / request_path).resolve()
        if not asset.is_relative_to(root / 'heads'):
            route.fulfill(status=403, body='Forbidden')
        elif not asset.is_file():
            route.fulfill(status=404, body='Not found')
        else:
            route.fulfill(path=asset, content_type='image/webp')
    else:
        local_file(route)


GEOMETRY = '''([expected, cardParts, weekParts]) => {
  const stage = document.querySelector('[data-waivers]');
  if (!stage || stage.hidden) return {visible:false};
  const ranks = expected === 'strip' ? ['3','2','1'] : ['3','2'];
  const cards = ranks.map(rank => stage.querySelector(`[data-pickup="${rank}"]`));
  const opacity = node => {let amount=1; for(let parent=node;parent;parent=parent.parentElement) {const style=getComputedStyle(parent); if(parent.hidden || style.display==='none' || style.visibility!=='visible') return 0; amount*=Number(style.opacity);} return node.getBoundingClientRect().width>0 ? amount : 0;};
  const words = [stage.querySelector('[data-waivers-head]'), stage.querySelector('[data-waivers-sub]'),
    ...cards.flatMap(card => cardParts.map(part => card.querySelector(part)).filter(Boolean)),
    ...(expected === 'strip' ? [...stage.querySelectorAll(weekParts)] : [])];
  const pictures = cards.flatMap(card => [...card.querySelectorAll('[data-pickup-face]')]);
  const lead = expected === 'strip' ? ['1'] : ranks;
  const full = node => opacity(node) > .99;
  const leading = words.filter(node => !node.closest('[data-pickup]') || lead.includes(node.closest('[data-pickup]').dataset.pickup));
  const visible = words.length === (expected === 'strip' ? 2 + 14 + 12 : 2 + 10) && leading.every(full) && words.every(node => opacity(node) > .3);
  const box = node => {const rect=node.getBoundingClientRect(); return {text:node.textContent, left:rect.left, right:rect.right, top:rect.top, bottom:rect.bottom};};
  const hit = (first, second) => first.left < second.right-.5 && second.left < first.right-.5 && first.top < second.bottom-.5 && second.top < first.bottom-.5;
  const pairs = list => list.flatMap((first, index) => list.slice(index+1).filter(second => hit(first, second)).map(second => [first.text, second.text]));
  const wordBoxes = words.map(box), pictureBoxes = pictures.map(box), cardBoxes = cards.map(card => ({...box(card), text:'card ' + card.dataset.pickup}));
  const overlaps = [...pairs(wordBoxes), ...pairs(cardBoxes),
    ...wordBoxes.flatMap(word => pictureBoxes.filter(picture => hit(word, picture)).map(() => [word.text, 'portrait']))];
  const caps = words.map(node => {const style=getComputedStyle(node), pen=document.createElement('canvas').getContext('2d'); pen.font=[style.fontWeight,style.fontSize,style.fontFamily].join(' '); return pen.measureText(node.textContent.toUpperCase()).actualBoundingBoxAscent * node.getBoundingClientRect().height / node.offsetHeight;});
  const inside = [...wordBoxes, ...cardBoxes].every(item => item.left>=0 && item.top>=0 && item.right<=innerWidth && item.bottom<=innerHeight);
  return {visible, within:inside, overlaps, minCapHeight:Math.min(...caps), count:words.length};
}'''


class WaiversFilm:
    def __init__(self, browser, width, height, reduced=False):
        self.width, self.height = width, height
        self.context = browser.new_context(viewport={'width': width, 'height': height}, reduced_motion='reduce' if reduced else 'no-preference')
        self.context.route('http://trophy.test/**', waiver_file)
        self.context.route('https://**', lambda route: route.abort())
        self.page = self.context.new_page()
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))

    def load(self):
        self.page.goto('http://trophy.test/?film')
        expect(self.page.locator('[data-play]')).to_be_enabled(timeout=30000)

    def seek(self, seconds):
        self.page.locator('[data-seek]').evaluate('(element, time) => {element.value=time; element.dispatchEvent(new Event(\'input\'));}', seconds)

    def card(self, rank):
        return self.page.locator(CARD.format(rank=rank))

    def geometry(self, beat):
        return self.page.evaluate(GEOMETRY, [beat, CARD_PARTS, WEEK_PARTS])

    def require_hold(self, beat):
        expect(self.page.locator(SECTION)).to_be_visible()
        expect(self.page.locator('[data-waivers-head]')).to_have_text('Best pickups.')
        # 2026-11-05 (David reapproved, +2 s Chapter 3). ~~Points over who he’d have started instead~~.
        expect(self.page.locator('[data-waivers-sub]')).to_have_text('Ranked by points over replacement (PAR).')
        lead = ['1'] if beat == 'strip' else ['3', '2']
        for rank in lead:
            expect(self.card(rank)).to_be_visible()
            expect(self.card(rank)).to_have_css('opacity', '1')
        if beat == 'strip':
            expect(self.page.locator(WEEK)).to_have_count(6)
            for week in self.page.locator(WEEK).all():
                expect(week).to_have_css('opacity', '1')

    def card_boxes(self):
        def edges(box):
            return {**box, 'left': box['x'], 'top': box['y'], 'right': box['x'] + box['width'], 'bottom': box['y'] + box['height']}
        return {rank: edges(self.card(rank).bounding_box()) for rank in '321'}

    def strip_rows(self):
        return self.page.locator(WEEK).evaluate_all('nodes => {const rows=new Map(); for(const node of nodes) {const top=Math.round(node.getBoundingClientRect().top); rows.set(top,(rows.get(top)||0)+1);} return [...rows.values()];}')

    def card_text(self):
        return [[text.strip() for text in self.card(rank).locator(', '.join(CARD_PARTS)).all_text_contents()] for rank in '321']

    def strip_text(self):
        return self.page.locator(WEEK).evaluate_all(f'nodes => nodes.map(node => [...node.querySelectorAll({WEEK_PARTS!r})].map(part => part.textContent).join(" "))')

    def pair_frame(self):
        """The #3 and #2 cards as the phone's subject: each portrait's drawn and source width, the pair's top and
        bottom, and the title's bottom edge."""
        return self.page.evaluate('''() => {
          const stage = document.querySelector('[data-waivers]');
          const cards = ['3', '2'].map(rank => stage.querySelector(`[data-pickup="${rank}"]`));
          const boxes = cards.map(card => card.getBoundingClientRect());
          const faces = cards.map(card => card.querySelector('[data-pickup-face]'));
          return {faces: faces.map(face => face.getBoundingClientRect().width), natural: faces.map(face => face.naturalWidth),
            top: Math.min(...boxes.map(box => box.top)), bottom: Math.max(...boxes.map(box => box.bottom)),
            title: stage.querySelector('[data-waivers-sub]').getBoundingClientRect().bottom};
        }''')

    def dimmed(self):
        return {rank: float(self.card(rank).evaluate('node => getComputedStyle(node).opacity')) < .99 for rank in '321'}

    def all_text(self):
        return self.page.locator(SECTION).inner_text()

    def shown(self):
        return self.page.evaluate('''() => {
          const shown = node => {if (!node) return false; for (let parent=node; parent; parent=parent.parentElement) {const style=getComputedStyle(parent); if (parent.hidden || style.display==='none' || style.visibility==='hidden' || Number(style.opacity) <= .01) return false;} return true;};
          const stage = document.querySelector('[data-waivers]');
          return {head:shown(stage.querySelector('[data-waivers-head]')), 3:shown(stage.querySelector('[data-pickup="3"]')),
            2:shown(stage.querySelector('[data-pickup="2"]')), 1:shown(stage.querySelector('[data-pickup="1"]')), weeks:shown(stage.querySelector('[data-waivers-weeks]'))};
        }''')

    def card_shown(self):
        return self.page.evaluate("() => {const node=document.querySelector('[data-waivers]'); return !!node && !node.hidden && Number(getComputedStyle(node).opacity) > 0;}")

    def visibility(self):
        return self.page.evaluate('''() => {
          const visible = selector => {const node=document.querySelector(selector); return !!node && !node.hidden && Number(getComputedStyle(node).opacity) > 0;};
          return {trades:visible('[data-trades]'), draft:visible('[data-receipt]')};
        }''')

    def __enter__(self):
        return self

    def __exit__(self, error_type, error, traceback):
        self.close()

    def close(self):
        self.context.close()

    def assets_ready(self):
        return self.page.evaluate("() => {const images=[...document.querySelectorAll('[data-waivers] img')]; return document.fonts.status==='loaded' && images.length===6 && images.every(image=>image.complete && image.naturalWidth>0);}")

    def load_with_delayed_asset(self, resource):
        pending = []
        self.context.route('**/scene.mjs', lambda route: route.fulfill(content_type='application/javascript', body='export async function createRoom(){return {canvas:document.createElement("canvas"),draw(){},dispose(){},pick(){return null;}};}'))
        self.context.route(resource, lambda route: pending.append(route))
        with self.page.expect_request(resource):
            self.page.goto('http://trophy.test/?film', wait_until='domcontentloaded')
        expect(self.page.locator('[data-room]')).to_have_attribute('data-base-ready', 'true', timeout=30000)
        assert len(pending) == 1
        expect(self.page.locator('[data-play]')).to_be_disabled()
        for route in pending:
            waiver_file(route)
        expect(self.page.locator('[data-play]')).to_be_enabled(timeout=30000)

    def fail_portrait_after_base_ready(self):
        pending = []
        self.context.route('**/scene.mjs', lambda route: route.fulfill(content_type='application/javascript', body='window.disposedScenes=0; export async function createRoom(){return {canvas:document.createElement("canvas"),draw(){},dispose(){window.disposedScenes++;}};}'))
        self.context.route('**/heads/lg/jordan-love.webp', lambda route: pending.append(route))
        with self.page.expect_request('**/heads/lg/jordan-love.webp'):
            self.page.goto('http://trophy.test/?film', wait_until='domcontentloaded')
        expect(self.page.locator('[data-room]')).to_have_attribute('data-base-ready', 'true', timeout=30000)
        for route in pending:
            route.fulfill(status=404, body='Not found')
        expect(self.page.locator('[data-room]')).to_have_attribute('data-phase', 'fallback')
        return self.page.evaluate('window.disposedScenes')
