"""The broadcast is a finite, controllable infographic, with usable static charts as fallback."""
import pytest
from component import mount

from test_midseason_view import special
from pages.midseason import MidseasonPage

pytestmark = pytest.mark.render


def test_the_show_waits_for_play_then_pauses_and_cleans_up(special):
    page, errors = special("recap", init=("window.MS_TEST_CLOCK = Date.now(); Date.now = () => window.MS_TEST_CLOCK;",))
    show = MidseasonPage(page)
    show.restore_motion()
    show.open()
    assert show.film_state() == {"time": 0, "playing": False, "connected": True}
    show.play()
    show.advance_clock(1000)
    show.wait_for_playback()
    show.pause()
    assert show.film_state()["time"] > 0 and not show.film_state()["playing"]
    show.close()
    assert not show.film_state()["connected"] and errors == []


def test_scrubbing_uses_real_week_frames_and_ends_without_looping(special):
    page, errors = special("recap")
    show = MidseasonPage(page)
    show.restore_motion()
    show.open()
    show.seek(20000)
    assert show.race_score(9) == "600.00"
    show.seek(30000)
    assert show.film_state()["time"] == 30000 and not show.film_state()["playing"]
    assert "End of the show" in show.film_status() and errors == []


def test_reduced_motion_keeps_the_complete_static_charts(special):
    page, errors = special("recap")
    show = MidseasonPage(page)
    show.reduce_motion()
    show.open()
    assert show.play_disabled() and "Reduced motion" in show.film_status()
    show.next_story()
    assert show.race_score(9) == "700.00" and errors == []
    show.restore_motion()


def test_without_the_animation_engine_story_controls_still_work(special):
    page, errors = special("recap")
    show = MidseasonPage(page)
    show.disable_engine()
    show.open()
    assert show.play_disabled() and "unavailable" in show.film_status()
    show.next_story()
    assert show.race_score(9) == "700.00" and errors == []
    show.restore_engine()


def test_leaving_recap_disposes_the_player_without_using_its_back_button(special):
    page, errors = special("recap")
    show = MidseasonPage(page)
    show.open()
    assert show.film_state()["connected"]
    show.leave_for_teams()
    assert not show.film_state()["connected"] and not show.film_state()["playing"]
    assert errors == []
