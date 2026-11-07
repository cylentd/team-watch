import pytest
from playwright.sync_api import expect

from test_trophy_room import local_file


@pytest.fixture
def headline_page(mount):
    """The film at 1440x900, Play enabled; shared by the board, border-light, framing and spacing tests."""
    context = mount.browser.new_context(viewport={'width': 1440, 'height': 900})
    context.route('http://trophy.test/**', local_file)
    context.route('https://**', lambda route: route.abort())
    page = context.new_page()
    page.goto('http://trophy.test/?film')
    expect(page.locator('[data-play]')).to_be_enabled(timeout=60000)
    yield page
    context.close()
