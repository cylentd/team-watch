"""This week > News, in Chromium (2026-09-30, David: "the first paragraph of each news repeats the headline.
Player names are hard to find on a scan. Should we have a search for players here?")."""
import pytest

from test_render import browser, go, open_page  # noqa: F401  (the suite's one Chromium)


def _news(browser, page_file, size):
    ctx, page, errors = open_page(browser, page_file, size)
    page.goto(page_file.as_uri())
    for _, sel in go("news"):
        page.click(sel)
    page.wait_for_selector(".newsrow")
    return ctx, page, errors


@pytest.mark.render
def test_a_story_with_a_read_drops_the_summary_that_repeats_its_headline(browser, page_file):
    ctx, page, errors = _news(browser, page_file, (1400, 900))
    got = page.evaluate("""() => [...document.querySelectorAll('.newsrow')].map(r => ({
      desc: !!r.querySelector('.ndesc'), impact: !!r.querySelector('.nimpact')}))""")
    assert got and not any(r["desc"] and r["impact"] for r in got)
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_the_players_name_is_the_bright_part_of_the_headline(browser, page_file):
    ctx, page, errors = _news(browser, page_file, (1400, 900))
    got = page.evaluate("""() => [...document.querySelectorAll('.newsrow')].map(r => {
      const t = r.querySelector('.ntitle'), b = t.querySelector('.nname');
      return {title: t.textContent, name: b && b.textContent,
              ink: b && getComputedStyle(b).color, rest: getComputedStyle(t).color}; })""")
    named = [r for r in got if r["name"]]
    assert named, "at least one fixture headline names its player"
    for r in named:
        assert r["name"] in r["title"]
        assert r["ink"] != r["rest"], "the name is brighter than the rest of the headline"
    ctx.close()
    assert errors == []


@pytest.mark.render
@pytest.mark.parametrize("size", [(390, 844), (1400, 900)])
def test_the_search_narrows_the_list_in_place(browser, page_file, size):
    ctx, page, errors = _news(browser, page_file, size)
    total = page.locator(".newslist .newsrow").count()
    # A word from the first listed story's own text matches it, and the box keeps the caret.
    word = page.evaluate("document.querySelector('.newslist .newsrow').dataset.newsq.split(' ')[0]")
    page.fill("#news-q", word)
    shown = page.evaluate("[...document.querySelectorAll('.newslist .newsrow')].filter(r => !r.hidden).length")
    assert 1 <= shown <= total
    assert page.evaluate("document.activeElement.id") == "news-q"
    page.fill("#news-q", "zzqxnotaplayer")
    assert page.evaluate("[...document.querySelectorAll('.newslist .newsrow')].every(r => r.hidden)")
    assert page.locator(".nsearch-none").is_visible()
    # A chip re-renders the list and keeps what was typed.
    page.fill("#news-q", word)
    page.click("[data-newscat='all']")
    assert page.input_value("#news-q") == word
    assert page.evaluate("document.documentElement.scrollWidth") <= size[0]
    ctx.close()
    assert errors == []
