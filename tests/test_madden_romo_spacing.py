"""Romo's finale column sits balanced in the frame (David, 2026-11-05, note 4: "fill the top black area more so
that it's evenly spaced vertically"), with its totals clear of the controls bar, on a desktop and two phones."""
import pytest
from component import mount
from test_madden_headline_entrance import headline_page, seek

FINALE = 43.7   # every row and both totals have entered (David's screenshot)


@pytest.mark.parametrize('width,height', [(1440, 900), (390, 844), (360, 800)])
def test_the_finale_column_has_equal_space_above_and_below_and_clears_the_controls(headline_page, width, height):
    headline_page.set_viewport_size({'width': width, 'height': height})
    seek(headline_page, FINALE)
    room = headline_page.locator('[data-room]').bounding_box()
    column = headline_page.locator('[data-receipt]').bounding_box()
    totals = headline_page.locator('[data-receipt] .receipt-total').last.bounding_box()
    controls = headline_page.locator('footer.controls').bounding_box()
    above = column['y'] - room['y']
    below = room['y'] + room['height'] - (column['y'] + column['height'])
    assert above > 0 and below > 0
    assert abs(above - below) <= .1 * max(above, below)
    assert totals['y'] + totals['height'] < controls['y']
