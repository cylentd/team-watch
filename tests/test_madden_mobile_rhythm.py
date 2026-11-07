"""Larger Gibbs identity and earlier QB ranks, David's November 6 phone review."""
import pytest

from pages.madden_mobile_rhythm import MobileRhythmFilm
from test_madden_chapter2 import node


def test_qb_rank_sweep_starts_one_second_earlier_without_moving_later_music_cues():
    result = node("const {waiversPose}=await import(base+'/waivers-motion.mjs'); const {filmPlan}=await import(base+'/film.mjs'); return {weeks:[5.14,5.2,5.85,6,4.9].map(s=>waiversPose(s).weeks), starts:filmPlan().beats.filter(b=>['lineup-defense','power-board','power-close'].includes(b.id)).map(b=>b.start), end:filmPlan().duration};")
    assert result['weeks'][0] == [0] * 6
    assert result['weeks'][1][0] > 0 and result['weeks'][1][-1] == 0
    assert 0 < result['weeks'][2][-1] < 1
    assert result['weeks'][3] == [1] * 6 and result['weeks'][4] == [0] * 6
    assert result['starts'] == pytest.approx([58.077,74.077,84.077])
    assert result['end'] == pytest.approx(98.077)


@pytest.mark.parametrize('size', [(360,800),(390,844),(412,915)])
@pytest.mark.journey
def test_gibbs_phone_identity_is_larger_and_the_card_uses_the_lower_frame(browser, size):
    film = MobileRhythmFilm(browser, *size)
    with film:
        film.load()
        film.seek(59.5)
        geometry = film.manager_geometry()
        card = next(item for item in film.readout()['objects'] if item['text'] == 'Saints')
        assert geometry['avatar']['width'] >= 48 and geometry['nameSize'] >= 28
        assert geometry['titleSize'] >= 25 and geometry['header']['left'] >= 0 and geometry['header']['right'] <= size[0]
        assert card['visible'] and card['inside']
        assert card['box']['top'] >= geometry['header']['bottom'] + size[1] * .035
        assert size[1] * .7 <= card['box']['bottom'] <= size[1] * .85
        assert film.errors == []
