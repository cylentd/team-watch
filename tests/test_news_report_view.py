"""Players > News as an injury report (ledger #95, 2026-10-09), mounted at 360px: the rows draw, the cells name
their days, a Tuesday drops the cells and groups the rows, a reader with no team reads the starters. Which player
lands in which group and in what order is tests/test_js_newsreport.py's; here only the screen.

Every locator is in tests/pages/news_report.py; every phrase is read from content.json (wording.words)."""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.news_report import NewsReport
from wording import words

pytestmark = [pytest.mark.render, pytest.mark.req("News", ac="the injury report")]

# The suite's clock is Saturday 2026-09-12 (test_render.SEED): a practice week, the report's own day.
TUESDAY = 'Date.now = () => Date.parse("2026-09-15T19:00:00Z");'        # Tuesday noon, Pacific
NOBODY = 'try { localStorage.setItem("tw-follow", "[]"); localStorage.removeItem("tw-team"); } catch (e) {}'
DAYS = [words("news.day.wed"), words("news.day.thu"), words("news.day.fri")]


def test_a_practice_week_draws_a_row_per_player_with_three_day_cells(mount):
    page, errors = mount("news")
    report = NewsReport(page)
    rows = report.rows()
    assert rows, "the fixture's stories name rostered players"
    unlabelled = [r["slug"] for r in rows if [c[:len(d)] for c, d in zip(r["days"], DAYS)] != DAYS]
    assert unlabelled == [], "every row has a Wed, a Thu and a Fri cell, each naming its day"
    assert errors == []


def test_the_sunday_word_is_the_headlines(mount):
    page, errors = mount("news")
    by = {r["slug"]: r for r in NewsReport(page).rows()}
    assert by["tee-higgins"]["sunday"] == words("news.st.out")              # "Tee Higgins ruled out for Week 1"
    assert by["chase-brown"]["sunday"] == words("news.st.questionable")     # "... questionable for Week 1"
    assert errors == []


def test_the_cells_say_what_the_practice_report_says(mount):
    page, errors = mount("news")
    by = {r["slug"]: r for r in NewsReport(page).rows()}
    missed, limited = words("news.mark.dnp"), words("news.mark.limited")
    # tests/fixtures/data/practice_report.json: Higgins DNP all week, Chase Brown LP, DNP, LP.
    assert by["tee-higgins"]["days"] == [d + missed for d in DAYS]
    assert by["chase-brown"]["days"] == [DAYS[0] + limited, DAYS[1] + missed, DAYS[2] + limited]
    assert errors == []


def test_while_the_report_has_no_marks_one_line_says_so_in_place_of_the_cells(mount):
    page, errors = mount("news")
    report = NewsReport(page)
    report.plant_report_without_marks("no marks this week")
    rows = report.rows()
    assert rows and all(r["days"] == [] and r["noreport"] == words("news.noreport") for r in rows)
    assert by_slug(rows)["tee-higgins"]["sunday"] == words("news.st.out")     # the Sunday word stays
    assert errors == []


def test_a_friday_only_report_draws_friday_and_two_open_days(mount):
    """ff-jarvis #100 (00f0a88): NFL.com's report, a week with Friday only. Wed and Thu stay empty cells."""
    page, errors = mount("news")
    report = NewsReport(page)
    report.plant_days("tee-higgins", {"Wed": None, "Thu": None, "Fri": "limited"})
    row = by_slug(report.rows())["tee-higgins"]
    assert row["days"] == [DAYS[0], DAYS[1], DAYS[2] + words("news.mark.limited")]
    assert row["noreport"] is None
    assert report.page_scroll_width() <= 360
    assert errors == []


def by_slug(rows):
    return {r["slug"]: r for r in rows}


def test_a_story_about_no_player_is_not_on_the_report(mount):
    page, errors = mount("news")
    assert "minor roster move" not in NewsReport(page).text()
    assert errors == []


def test_a_row_names_the_player_once(mount):
    page, errors = mount("news")
    rows = NewsReport(page).rows()
    assert [r["name"] for r in rows if (r["story"] or "").startswith(r["name"])] == []
    assert errors == []


def test_tuesday_drops_the_cells_and_keeps_the_groups(mount):
    page, errors = mount("news", init=(TUESDAY,))
    report = NewsReport(page)
    assert all(r["days"] == [] for r in report.rows())
    titles = {words("news.group.mine"), words("news.group.wire"), words("news.group.starter")}
    assert report.groups() and all(g["title"] in titles for g in report.groups())
    assert errors == []


def test_a_reader_with_no_team_reads_the_starters_of_every_league(mount):
    page, errors = mount("news", init=(NOBODY,))
    keys = [g["key"] for g in NewsReport(page).groups()]
    assert "mine" not in keys and keys[0] == "starter"
    assert errors == []


@pytest.mark.parametrize("init", [(), (TUESDAY,)])
def test_nothing_scrolls_sideways_at_360(mount, init):
    page, errors = mount("news", init=init)
    assert NewsReport(page).page_scroll_width() <= 360
    assert errors == []
