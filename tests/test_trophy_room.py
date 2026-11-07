"""Exercise the opening without a live server, API requests, or real-time sleeps."""
import mimetypes
from pathlib import Path
from urllib.parse import unquote, urlparse

import pytest
from component import mount

from pages.trophy_room import TrophyRoom

SOURCE = Path(__file__).resolve().parents[1] / 'showcase/madden-curse'


def local_file(route):  # shape: allow exported route fixture reused by film browser test modules
    request = unquote(urlparse(route.request.url).path).lstrip('/')
    base = SOURCE.parents[1] if request.startswith(('avatars/', 'heads/')) else SOURCE
    path = (base / request).resolve()
    if not path.is_relative_to(base.resolve()):
        return route.fulfill(status=403, body='Forbidden')
    if path.is_dir():
        path = path / 'index.html'
    if not path.is_file():
        return route.fulfill(status=404, body='Not found')
    mime = 'text/javascript' if path.suffix == '.mjs' else mimetypes.guess_type(path)[0]
    route.fulfill(path=path, content_type=mime or 'application/octet-stream')


@pytest.fixture(scope='module')
def trophy_browser(mount):
    return mount.browser


@pytest.fixture
def room(trophy_browser):
    context = trophy_browser.new_context(viewport={'width': 360, 'height': 800}, reduced_motion='no-preference')
    context.route('http://trophy.test/**', local_file)
    context.route('https://**', lambda route: route.abort())
    page = context.new_page()
    page.clock.install()
    yield TrophyRoom(page)
    context.close()


def test_opening_waits_for_explicit_play_and_finishes_once(room):
    room.open()
    room.advance(1000)
    assert room.phase() == 'ready' and room.time() == 44
    room.action('Play the show').click()
    room.advance(45000)
    assert room.time() == 44 and room.action('Replay show').is_enabled()
    room.advance(1000)
    assert room.time() == 44


def test_pause_freezes_the_camera_until_resumed(room):
    room.open()
    room.action('Play the show').click()
    room.advance(1000)
    room.action('Pause').click()
    paused = room.time()
    room.advance(2000)
    assert 0 < paused < 6 and room.time() == paused
    room.action('Resume').click()
    room.advance(1000)
    assert room.time() > paused


def test_slow_frames_do_not_stretch_the_forty_six_second_show(room):
    room.page.add_init_script("window.requestAnimationFrame = callback => setTimeout(() => callback(performance.now()), 100); window.cancelAnimationFrame = clearTimeout;")
    room.open()
    room.action('Play the show').click()
    room.advance(45000)
    assert room.time() == 44 and room.action('Replay show').is_enabled()


def test_reduced_motion_retains_static_inspection(room):
    room.page.emulate_media(reduced_motion='reduce')
    room.open()
    assert room.action('Play the show').is_disabled()
    assert room.page.locator('[data-story-title]').inner_text() == 'NOBODY’S SAFE.'
    room.action('Inspect trophy').click()
    assert room.action('Exit inspection').get_attribute('aria-pressed') == 'true'
    room.page.keyboard.press('Escape')
    assert room.action('Inspect trophy').get_attribute('aria-pressed') == 'false'


def test_keyboard_inspection_changes_the_rendered_trophy(room):
    room.open()
    room.action('Inspect trophy').click()
    before = room.page.locator('canvas').screenshot()
    room.page.keyboard.press('ArrowRight')
    after = room.page.locator('canvas').screenshot()
    assert before != after


def test_hiding_the_tab_pauses_without_auto_resume(room):
    room.open()
    room.action('Play the show').click()
    room.advance(500)
    room.hidden_tab()
    paused = room.time()
    room.advance(1000)
    assert room.time() == paused and room.action('Resume').is_enabled()


def test_missing_model_is_disclosed_and_keeps_controls(room):
    room.page.route('**/lombardi.glb', lambda route: route.fulfill(status=404, body='Missing'))
    room.open()
    assert room.phase() == 'study'
    assert room.page.get_by_text('The generated trophy could not load.', exact=False).is_visible()
    assert room.action('Play the show').is_enabled()


def test_without_webgl_the_title_and_explanation_remain(room):
    room.page.add_init_script("const original = HTMLCanvasElement.prototype.getContext; HTMLCanvasElement.prototype.getContext = function(kind, ...args) { return kind.startsWith('webgl') ? null : original.call(this, kind, ...args); };")
    room.open()
    assert room.phase() == 'fallback' and room.visible_title()
    assert room.page.get_by_text('The 3D room is unavailable', exact=False).is_visible()
    assert room.action('Play the show').is_disabled()


def test_context_loss_stays_in_fallback_after_resize(room):
    room.open()
    room.page.locator('canvas').evaluate("element => element.dispatchEvent(new Event('webglcontextlost', {cancelable: true}))")
    room.page.set_viewport_size({'width': 390, 'height': 900})
    room.advance(100)
    assert room.phase() == 'fallback' and room.action('Play the show').is_disabled()
    assert room.page.locator('canvas').count() == 0


def test_sound_requires_an_explicit_opt_in(room):
    room.open()
    assert room.action('Sound off').get_attribute('aria-pressed') == 'false'
    room.action('Sound off').click()
    assert room.action('Sound on').get_attribute('aria-pressed') == 'true'
    room.action('Sound on').click()
    assert room.action('Sound off').get_attribute('aria-pressed') == 'false'


def test_each_team_has_its_own_headline_and_the_full_article(room):
    room.open()
    room.page.get_by_role('slider', name='Show position').fill('12.5')
    assert room.page.locator('[data-story-title]').inner_text() == 'JSN WAS THE PLAN.'
    room.page.get_by_role('slider', name='Show position').fill('34.5')
    assert room.page.locator('[data-story-title]').inner_text() == 'HUBBARD. ROUND EIGHT.'
    assert room.page.locator('[data-report] article').count() == 12
    room.action('Read the report').click()
    assert room.page.locator('[data-report]').evaluate('element => element.getBoundingClientRect().top') <= 1


def test_missing_edition_is_not_misreported_as_a_webgl_failure(room):
    room.page.route('**/edition.json', lambda route: route.fulfill(status=404, body='Missing'))
    room.open()
    assert room.phase() == 'fallback'
    assert room.page.get_by_text('The verified Week 8 stories could not load.', exact=False).is_visible()
    assert room.action('Play the show').is_disabled()


@pytest.mark.parametrize('width', [360, 390, 768, 1280, 1920])
def test_the_entire_headline_fits_the_viewport(room, width):
    room.page.set_viewport_size({'width': width, 'height': 900})
    room.open()
    assert room.title_fits()
    assert room.page.evaluate('document.documentElement.scrollWidth === innerWidth')
