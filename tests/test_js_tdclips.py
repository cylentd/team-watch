"""Who a fresh TD clip is of, when to ask for clips, and how a reply joins what a channel held, in Node
(design/src/js/data/gameday/tdcmatch.js and tdclips.js; DESIGN.md "Clips").

The page names a clip of a scorer by its title alone, so the rule must not credit a word that merely is
somebody's last name (week 4: "Chase Brown" credited Ja'Marr Chase, "let him cook" J. Cook). The drawn reel
and the requests the page makes are tests/test_live_tdclips.py; here is only the rule, one clip at a time.

The day is the component tests' (tests/pages/live.py): SF at KC kicked off 2026-09-13T20:25Z, DET at MIN at
17:00Z, four scorers, and the build's names for two of them."""
import pytest

from pages.live import LEAD, NAMES, REPLIES

SF_KICK = "2026-09-13T20:25:00Z"
GAMES = [{"home": "SF", "away": "KC", "kickoff": SF_KICK, "week": 2},
         {"home": "DET", "away": "MIN", "kickoff": "2026-09-13T17:00:00Z", "week": 2},
         {"home": "LAR", "away": "WSH", "kickoff": "2026-09-13T20:00:00Z", "week": 2},
         {"home": "MIA", "away": "BUF", "kickoff": "2026-09-10T00:20:00Z", "week": 2}]
FILES = ("surface/parlay/gamelog.js", "lib/kick.js", "surface/live/nflnow.js", "data/gameday/clock.js",
         "surface/live/tds.js", "data/gameday/tdcmatch.js", "data/gameday/tdclips.js")
NOW = "2026-09-13T22:25:00Z"        # two hours after SF's kickoff, the component tests' clock
KNOWN = ["chase-brown", "harrison-wallace", "thomas-ives", "amonra-st-brown", "jameson-williams", "quincy-williams",
         "dalvin-cook", "dandre-swift", "breece-hall", "jalen-hurts"]

# one clip, one scorer, on one channel: [scorer, club, channel, title, jersey number, nicknames]; the JS reads the
# names and the number from the row, as it reads the build's LIVE_NAMES, and puts the page's own back after
MATCH = """(cfg) => {
  const rows = tdcNameRow, slugs = tdcSlugs;
  TDC_KNOWN = {key: "", set: new Set()};
  tdcSlugs = () => cfg.known;
  try {
    return cfg.rows.map(([name, team, ch, title, n, nicks]) => {
      tdcNameRow = () => n === undefined && !nicks ? null : {n: n === undefined ? null : n, t: team, k: nicks || []};
      return tdcMatches({n: name, slug: slugOf(name), team}, {id: "x", title, posted: "2026-09-13T22:00:00Z"}, ch);
    });
  } finally { tdcNameRow = rows; tdcSlugs = slugs; TDC_KNOWN = {key: "", set: new Set()}; }
}"""

# the games the page asks for at an instant: SF at KC only, the clock of both clubs as ESPN says it (or no word)
QUOTA = """(cfg) => {
  const all = GD_GAMES, k = Date.parse("2026-09-13T20:25:00Z");
  GD_GAMES = all.slice(0, 1);
  try {
    return cfg.cases.map(([state, mins, slack]) => {
      GD_CLOCK = {};
      if (state) for (const c of ["SF", "KC"]) GD_CLOCK[c] = {state, q: 4, clock: "0:00", half: false, detail: "", clubs: ["SF", "KC"]};
      TDC.over = {};
      const games = tdcGames(k + mins * 60e3, slack);
      return games.length ? tdcChannels(games) : [];
    });
  } finally { GD_GAMES = all; GD_CLOCK = {}; TDC.over = {}; }
}"""

MERGE = """() => { const now = Date.now(), h = n => new Date(now - n * 3600e3).toISOString();
  TDC.by = {};
  tdcMerge("ZZ", [{id: "a", title: "old", posted: h(31)}, {id: "b", title: "b", posted: h(29)}, {id: "c", title: "c", posted: h(1)},
                  {id: "b", title: "b2", posted: h(29)}, {id: "x", title: "no time"}], now);
  tdcMerge("ZZ", [{id: "c", title: "c again", posted: h(1)}, {id: "d", title: "d", posted: h(0.5)}], now);
  return TDC.by.ZZ.map(c => c.id + ":" + c.title); }"""


@pytest.fixture(scope="module")
def td(node_js):
    js = node_js(*FILES, globals={
        "GD": {"leagues": [{"week": 2}]}, "GD_GAMES": GAMES, "GD_ALIAS": {"LA": "LAR", "WAS": "WSH"},
        "GD_GAME_MS": 13500000, "GD_STATS": {"week": 2, "games": {}, "stats": {}, "lead": LEAD}, "LIVE_NAMES": NAMES})
    js("() => { gdClock = ms => kickFmt(ms); }")      # surface/live/board.js's one-liner: that file draws a board
    return js


def matches(td, rows):
    return td(MATCH, {"rows": rows, "known": KNOWN})


def merged(td, replies):
    """The page's TDC after each channel's reply, at the component tests' clock."""
    td("(cfg) => { TDC.by = {}; for (const [ch, clips] of Object.entries(cfg.replies)) tdcMerge(ch, clips, Date.parse(cfg.now)); }",
       {"replies": replies, "now": NOW})


RUSHER = {"n": "Test Rusher", "slug": "test-rusher", "team": "SF"}


@pytest.mark.req("Clips", ac="a different player's name is not his, and a jersey is only his on his own channel")
def test_one_clip_at_a_time_a_different_players_name_is_not_his(td):
    def titled(t):
        return {"id": "x", "title": t, "posted": "2026-09-13T22:00:00Z"}
    got = [td("tdcMatches", RUSHER, titled(t), ch) for t, ch in
           [("Test Catcher scores", "NFL"), ("Rusher's second", "NFL"), ("Rusher's second", "SF"), ("Rusher's second", "KC"),
            ("RÚSHER", "SF"), ("Week 22 recap", "SF"), ("a 22 yards run", "SF"), ("#22 on the run", "SF"),
            ("Test Rusher's second", "NFL"), ("T. Rusher's second", "NFL")]]
    assert got == [False, False, True, False, True, False, False, False, True, True]


@pytest.mark.req("Clips", ac="a passer's clip on the NFL channel names the whole player")
def test_the_nfl_channels_clip_of_a_passer_is_his_by_first_and_last_name(td):
    merged(td, REPLIES)
    ids = td("(w) => tdcFor(w).map(c => c.id)", {"n": "Test Passer", "slug": "test-passer", "team": "SF"})
    assert "p1" in ids


@pytest.mark.req("Clips", ac="a last name inside another player's name credits nobody")
def test_a_last_name_inside_another_players_name_credits_nobody(td):
    traps = [  # (scorer, club, channel, title): another player's full name, on the scorer's own club's channel
        ("Ja'Marr Chase", "DET", "DET", "Chase Brown takes the handoff 40 yards"),
        ("Marvin Harrison Jr.", "MIN", "MIN", "Harrison Wallace gets the TD"),
        ("Zach Thomas", "DET", "DET", "Thomas Ives finds the end zone"),
        ("Equanimeous St. Brown", "DET", "DET", "Amon-Ra St. Brown with the grab"),
        ("Mike Williams", "DET", "DET", "Jameson Williams goes deep, Quincy Williams stops the run")]
    assert matches(td, [list(t) for t in traps]) == [False] * 5
    # the same scorer's bare last name still counts on his club's channel once the other player is out of the title
    assert matches(td, [["Ja'Marr Chase", "DET", "DET", "Chase scores again"],
                        ["Ja'Marr Chase", "DET", "DET", "Ja'Marr Chase and Chase Brown both score"],
                        ["Dalvin Cook", "DET", "DET", "Cook rumbles in"]]) == [True] * 3


@pytest.mark.req("Clips", ac="the NFL channel never credits a bare last name")
def test_the_nfl_channel_never_credits_a_bare_last_name(td):
    words = [("Dalvin Cook", "Let him cook!"), ("D'Andre Swift", "Taylor Swift in the stands"), ("Breece Hall", "A Hall of Fame play"),
             ("Jalen Hurts", "This one hurts"), ("Jordan Love", "Love is in the air"), ("Joe King", "King of the hill"),
             ("Kyle Golden", "A golden moment"), ("Rashid Worthy", "Worthy of the highlight reel"),
             ("Dalvin Cook", "Cook rumbles in")]
    assert matches(td, [[n, "DET", "NFL", t] for n, t in words]) == [False] * 9
    assert matches(td, [[n, "DET", "DET", t] for n, t in words[-1:]]) == [True], "his own club's channel may say it bare"
    # whole names, an initial and last name, #FirstLast and a nickname are the NFL channel's ways in; another initial is another player
    assert matches(td, [["Dalvin Cook", "DET", "NFL", "J. Cook finds the end zone"]]) == [False]
    assert matches(td, [["Dalvin Cook", "DET", "NFL", "Dalvin Cook scores"], ["Dalvin Cook", "DET", "NFL", "D. Cook finds the end zone"],
                        ["Dalvin Cook", "DET", "NFL", "TD! #DalvinCook"], ["Dalvin Cook", "DET", "NFL", "The Rocket takes off", None, ["the rocket"]],
                        ["Ja'Marr Chase", "DET", "NFL", "Ja'Marr Chase takes it 60"], ["Amon-Ra St. Brown", "DET", "NFL", "Amon-Ra St. Brown scores"],
                        ["Marvin Harrison Jr.", "MIN", "NFL", "Marvin Harrison Jr. scores"]]) == [True] * 7


@pytest.mark.req("Clips", ac="a jersey number counts only opening the title or after No., on his own club's channel")
def test_a_jersey_number_opens_the_title_or_follows_no_and_only_on_his_own_clubs_channel(td):
    counts = [("Panthers 24, Cowboys 17", 24), ("Panthers 24, Cowboys 17", 17), ("3rd and 10", 3), ("3rd and 10", 10),
              ("Top 10 plays of the week", 10), ("4th & 1 stop", 4), ("4th & 1 stop", 1), ("#1 catch", 1), ("a 4 TD day", 4),
              ("up 21 at the half", 21), ("88 yards to the house", 88), ("22-17 final", 22)]
    assert matches(td, [["Dalvin Cook", "DET", "DET", t, n] for t, n in counts]) == [False] * len(counts)
    jerseys = [("88 in the end zone", 88), ("2 GETS HIS FIRST TD", 2), ("No. 88 scores", 88), ("No.88 scores", 88)]
    assert matches(td, [["Dalvin Cook", "DET", "DET", t, n] for t, n in jerseys]) == [True] * 4
    assert matches(td, [["Dalvin Cook", "DET", "NFL", "88 in the end zone", 88], ["Dalvin Cook", "DET", "MIN", "No. 88 scores", 88]]) == [False, False]


@pytest.mark.req("Clips", ac="a reply joins what the channel held by id; clips older than 30 hours go")
def test_a_reply_joins_what_the_channel_held_by_id_and_clips_older_than_30_hours_go(td):
    td("() => { Date.now = () => Date.parse('2026-09-13T22:25:00Z'); }")
    assert td(MERGE) == ["d:d", "c:c again", "b:b2"], "by id, the newer wins; 31 h and no time go; newest first"


@pytest.mark.req("Clips", ac="the NFL channel's copy of a play within 15 minutes of his club's is dropped")
def test_the_nfl_copy_of_a_play_within_15_minutes_of_his_clubs_is_dropped(td):
    got = td("""() => {
      const c = (id, title, hhmm) => ({id, title, posted: `2026-09-13T${hhmm}:00Z`, secs: 20, shape: "wide", embed: true});
      TDC.by = {SF: [c("s1", "Test Rusher scores", "22:10")],
                NFL: [c("n1", "Test Rusher scores again", "22:20"), c("n2", "Test Rusher highlights", "22:26"),
                      c("n3", "Test Rusher too", "21:56"), c("n4", "Test Catcher scores", "22:12"),
                      c("n5", "Test Rusher and Test Catcher", "22:05")]};
      const ids = w => tdcFor(w).map(x => x.id);
      return [ids({n: "Test Rusher", slug: "test-rusher", team: "SF"}), ids({n: "Test Catcher", slug: "test-catcher", team: "KC"})];
    }""")
    # Rusher: n1 (10 min after his club's), n3 (14 before) and n5 (5 after) are the same play; n2 (16 after) is another
    # Catcher: KC has nothing of his, so the NFL's stay
    assert got == [["s1", "n2"], ["n4", "n5"]]


@pytest.mark.req("Clips", ac="it asks only for clubs whose game is on or ended under an hour ago")
def test_it_asks_only_for_clubs_whose_game_is_on_or_ended_under_an_hour_ago(td):
    hour, six, club = 3600e3, 6 * 3600e3, ["SF", "KC", "NFL"]
    cases = [("in", 60, hour), ("in", 230, hour), ("post", 225, hour), ("post", 270, hour),   # on; past a game's length; ended 30 min; ended 75 min ago
             (None, 225, hour), (None, 260, hour), ("pre", -30, hour),                         # no word but the schedule's; before kickoff
             ("post", 495, six), ("post", 600, six)]                                           # the first round's six hours
    got = td(QUOTA, {"cases": [list(c) for c in cases]})
    assert got == [club, [], club, [], club, [], [], club, []]
