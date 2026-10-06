"""The Digest banner and the Recap banner never carry the same content (David, 2026-10-05: "they should
never be the same content"), in Node. design/src/js/data/leadsplit.js is the one place the rule lives:

- a result story about the Recap's week and top scorer is the Recap banner's; the Digest stops announcing it
- whatever the Digest leads with, its subject (a player slug, or the story itself) is never the Recap's;
  if it would be, the Digest takes its next candidate.
"""
import pytest

TOP = {"n": "Tetairoa McMillan", "slug": "tetairoa-mcmillan", "team": "CAR"}
RECAP = {"week": 4, "complete": False, "n_final": 15, "top": TOP}
STORY = {"head": "McMillan torches the Lions for 192 yards", "fact": "14 catches.", "kind": "result",
         "asof": "2026-10-05 21:15:00", "club": "CAR",
         "player": {"n": "Tetairoa McMillan", "slug": "tetairoa-mcmillan", "pos": "WR", "team": "CAR"}}
HURT = {"slug": "puka-nacua", "head": "Puka Nacua is doubtful"}
WEATHER = {"head": "SEA @ WAS in 22 mph wind"}                      # no player: the story itself is its subject
NEWS = {"slug": "bijan-robinson", "head": "Bijan Robinson is back"}


@pytest.fixture(scope="module")
def ls(node_js):
    return node_js("data/leadsplit.js")


def test_a_result_story_about_the_recaps_week_and_top_scorer_is_the_recaps(ls):
    assert ls("lspRecapStory", STORY, 4, RECAP) == STORY


def test_the_digest_stops_announcing_it_and_leads_with_the_coming_week(ls):
    assert ls("lspDigestStory", STORY, 4, RECAP) is None
    # no game on: the packet's own lead (hurt, weather, news) is what is left to lead with
    assert ls("lspPick", [ls("lspDigestStory", STORY, 4, RECAP), HURT], ls("lspRecapSubject", RECAP)) == HURT


@pytest.mark.parametrize("why,story,week,recap", [
    ("another player", {**STORY, "player": {**STORY["player"], "slug": "bijan-robinson"}}, 4, RECAP),
    ("an injury story about him", {**STORY, "kind": "injury"}, 4, RECAP),
    ("a story for another week than the Recap's", STORY, 5, RECAP),
    ("no player on the story", {**STORY, "player": None}, 4, RECAP),
    ("a Recap with no games final", STORY, 4, {**RECAP, "n_final": 0}),
    ("a Recap with no top scorer", STORY, 4, {**RECAP, "top": None}),
    ("no Recap at all", STORY, 4, None)])
def test_any_other_story_stays_the_digests(ls, why, story, week, recap):
    assert ls("lspRecapStory", story, week, recap) is None, why
    assert ls("lspDigestStory", story, week, recap) == story, why


def test_a_story_that_is_the_recaps_is_its_subject_a_template_headline_is_the_top_scorer(ls):
    assert ls("lspRecapSubject", RECAP) == "player:tetairoa-mcmillan"
    assert ls("lspRecapSubject", {**RECAP, "top": {**TOP, "slug": None}}) == ""      # a defense has no face
    assert ls("lspRecapSubject", None) == ""


def test_the_subject_of_a_lead_is_its_player_or_the_story_itself(ls):
    assert ls("lspSubject", HURT) == "player:puka-nacua"
    assert ls("lspSubject", WEATHER) == "story:SEA @ WAS in 22 mph wind"
    assert ls("lspSubject", None) == ""
    assert ls("lspSubject", {"slug": "", "head": ""}) == ""


def test_the_same_player_live_gives_the_digest_its_next_candidate(ls):
    live = {"slug": "tetairoa-mcmillan", "head": "McMillan ERUPTS"}
    assert ls("lspPick", [live, HURT], "player:tetairoa-mcmillan") == HURT
    assert ls("lspPick", [live, HURT], "player:somebody-else") == live


def test_a_candidate_can_be_skipped_down_the_whole_list(ls):
    live = {"slug": "tetairoa-mcmillan", "head": "x"}
    news = {"slug": "tetairoa-mcmillan", "head": "y"}
    assert ls("lspPick", [live, news, WEATHER], "player:tetairoa-mcmillan") == WEATHER
    assert ls("lspPick", [None, live, NEWS], "player:tetairoa-mcmillan") == NEWS


def test_a_list_with_no_distinct_candidate_is_none(ls):
    live = {"slug": "tetairoa-mcmillan", "head": "x"}
    assert ls("lspPick", [live], "player:tetairoa-mcmillan") is None
    assert ls("lspPick", [], "") is None
    assert ls("lspPick", [None], "") is None


def test_a_lead_with_no_subject_never_collides(ls):
    quiet = {"head": "", "fact": "nothing"}
    assert ls("lspPick", [quiet], "player:tetairoa-mcmillan") == quiet
    assert ls("lspPick", [WEATHER], "") == WEATHER, "no Recap subject: nothing to avoid"
