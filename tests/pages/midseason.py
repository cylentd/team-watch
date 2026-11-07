"""The midseason show's public controls, layout and accessibility state."""


class MidseasonPage:
    def __init__(self, page):
        self.page = page

    def open(self):
        self.page.get_by_test_id("midseason-entry").click()

    def close(self):
        self.page.get_by_role("button", name="Back to weekly recap").click()

    def visible(self):
        return self.page.get_by_test_id("midseason-show").is_visible()

    def entry_visible(self):
        return self.page.get_by_test_id("midseason-entry").is_visible()

    def name(self):
        return self.page.get_by_test_id("midseason-stage").locator("h2").text_content()

    def pick(self, team_id):
        self.page.get_by_label("Jump to your team").select_option(str(team_id))

    def next(self):
        self.page.get_by_role("button", name="Next team").click()

    def selected(self):
        return self.page.get_by_label("Jump to your team").input_value()

    def next_focused(self):
        return self.page.get_by_role("button", name="Next team").evaluate("element => element === document.activeElement")

    def open_receipts(self):
        self.page.get_by_test_id("midseason-receipts").locator("summary").click()

    def receipt_text(self):
        return self.page.get_by_test_id("midseason-receipts").inner_text()

    def overflow(self):
        return self.page.evaluate("Math.max(0, document.documentElement.scrollWidth - innerWidth)")

    def chart_rows(self):
        return self.page.get_by_test_id("midseason-chart").locator(":scope > div").count()

    def motion(self):
        return self.page.get_by_test_id("midseason-stage").evaluate("element => getComputedStyle(element).animationName")

    def reduce_motion(self):
        self.page.emulate_media(reduced_motion="reduce")

    def restore_motion(self):
        self.page.emulate_media(reduced_motion="no-preference")

    def stage_text(self):
        return self.page.get_by_test_id("midseason-stage").inner_text()

    def report(self):
        return self.page.get_by_test_id("midseason-report")

    def news(self):
        return self.page.get_by_test_id("midseason-news")

    def next_story(self):
        self.page.get_by_role("button", name="Next story", exact=True).click()

    def read_report(self):
        self.page.get_by_role("button", name="Read the full report", exact=True).click()

    def report_heading_top(self):
        return self.report().locator("h2").bounding_box()["y"]

    def play(self):
        self.page.get_by_role("button", name="Play the show", exact=True).click()

    def pause(self):
        self.page.get_by_role("button", name="Pause", exact=True).click()

    def seek(self, time):
        self.page.get_by_label("Show position", exact=True).evaluate("""(element, time) => {
            element.value = time;
            element.dispatchEvent(new Event("input", {bubbles: true}));
        }""", time)

    def film_state(self):
        return self.page.evaluate("({time: MS_STATE.film.time, playing: MS_STATE.film.playing, connected: !!MS_STATE.film.player})")

    def wait_for_playback(self):
        self.page.wait_for_function("MS_STATE.film.time > 0 && MS_STATE.film.playing")

    def advance_clock(self, milliseconds):
        self.page.evaluate("milliseconds => { window.MS_TEST_CLOCK += milliseconds; }", milliseconds)

    def play_disabled(self):
        return self.page.get_by_role("button", name="Play the show", exact=True).is_disabled()

    def race_score(self, team):
        return self.news().locator(f'[data-msracer="{team}"] [data-msracevalue]').text_content()

    def film_status(self):
        return self.news().locator("[data-msfilmstatus]").text_content()

    def disable_engine(self):
        self.page.evaluate("window.MS_SAVED_ANIME = window.anime; window.anime = undefined")

    def restore_engine(self):
        self.page.evaluate("window.anime = window.MS_SAVED_ANIME")

    def leave_for_teams(self):
        self.page.get_by_role("button", name="Teams", exact=True).click()

    def broadcast_cues(self):
        return self.page.get_by_test_id("midseason-stage").evaluate("""element =>
            [".ms-stage-head", ".ms-headline", ".ms-roast", ".ms-hype", ".ms-bar", ".ms-lower"].map(selector => {
                const style = getComputedStyle(element.querySelector(selector));
                return {name: style.animationName, delay: parseFloat(style.animationDelay),
                    duration: parseFloat(style.animationDuration), iterations: style.animationIterationCount};
            })""")

    def finish_broadcast(self):
        return self.page.get_by_test_id("midseason-stage").evaluate("""element => {
            const before = element.getBoundingClientRect().height;
            element.getAnimations({subtree: true}).forEach(animation => animation.finish());
            return {before, after: element.getBoundingClientRect().height,
                running: element.getAnimations({subtree: true}).filter(animation => animation.playState === "running").length};
        }""")
