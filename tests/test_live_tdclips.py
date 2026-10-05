"""Live > TDs' TD clips reel (2026-10-05): Roster's clip rail above the Scored card, of the scorers the chips
keep, newest clip first. Clips come from LIVE_CLIPS (the finished week's) and from our function
(/api/clips?ch=<code>, asked every 5 minutes while the tab is on screen and a game is on).

The page is planted with a game on (SF at KC, kicked off 20:25Z, the clock 22:25Z), four scorers, a stubbed
window.fetch that answers per channel, and the build's names (jersey numbers, nicknames) for one of them."""
import json

from test_live_tabs import live  # noqa: F401
from test_render import open_page  # noqa: F401


def clip(id, title, posted, embed=True):
    return {"id": id, "title": title, "posted": posted, "secs": 30, "shape": "wide", "embed": embed}


def at(hhmm, day=13):
    return f"2026-09-{day:02d}T{hhmm}:00Z"


# Test Rusher is SF (jersey 22, "The Rocket"), Test Catcher is KC, Detroit Grabber is DET, Test Passer is SF.
# The games: SF-KC (kicked off 20:25Z) and LAR-WSH (20:00Z) are on, DET-MIN (17:00Z) is final, MIA-BUF is days old.
REPLIES = {
    "SF": [
        clip("f1", "Test Rusher punches it in", at("22:10")),          # last name
        clip("f2", "TD! #TestRusher again", at("21:40")),               # hashtag
        clip("f3", "No. 22 breaks free for six", at("21:50")),         # jersey, on his own club's channel
        clip("f4", "The Rocket lights up the board", at("21:55")),     # nickname
        clip("f5", "Catcher hauls it in", at("21:30")),                # a KC player on SF's channel
        clip("f6", "Rusher highlights", at("19:00")),                  # posted before kickoff
        clip("f7", "22-17 final, 1:22 left, 4th-and-22", at("22:23")),  # 22 inside a score and times
        clip("o1", "Rusher scores", at("21:00")),                      # also in LIVE_CLIPS, which has no time
    ],
    "KC": [
        clip("g1", "Catcher with the grab", at("22:00")),
        clip("g2", "No. 22 for the win", at("22:05")),                 # Rusher's number on another club's channel
        clip("g3", "Grabber scores", at("22:06")),                     # a DET player on KC's channel
    ],
    "NFL": [
        clip("h1", "Test Rusher and Test Catcher both score", at("22:28")),
        clip("h2", "No. 22 scores", at("22:21")),                      # a jersey number counts only on his own channel
        clip("p1", "Test Passer throws his third", at("22:15")),       # a passer: only under the Pass chip; the NFL's channel names whole players
    ],
    "DET": [clip("d1", "Grabber catches it", at("19:00"), embed=False)],
}
ORDER = ["h1", "f1", "g1", "f4", "f3", "f2", "o1", "d1", "o2"]    # newest first; o2 has no time, so it is last

SETUP = """(cfg) => {
  const week = GD.leagues[0].week;
  window.__now = Date.parse("2026-09-13T20:25:00Z") + cfg.hours * 3600e3;
  Date.now = () => window.__now;
  GD_GAMES.splice(0, GD_GAMES.length,
    {home: "SF", away: "KC", kickoff: "2026-09-13T20:25:00Z", week},
    {home: "DET", away: "MIN", kickoff: "2026-09-13T17:00:00Z", week},
    {home: "LAR", away: "WSH", kickoff: "2026-09-13T20:00:00Z", week},
    {home: "MIA", away: "BUF", kickoff: "2026-09-10T00:20:00Z", week});      // over 30 hours before
  const on = cfg.post ? "post" : "in";
  const g = (clubs, state) => ({state, q: state === "in" ? 3 : 4, clock: state === "in" ? "4:12" : "0:00", half: false, detail: "", clubs});
  GD_CLOCK = {};
  for (const [clubs, state] of [[["SF", "KC"], on], [["LAR", "WSH"], on], [["DET", "MIN"], "post"]]) for (const c of clubs) GD_CLOCK[c] = g(clubs, state);
  GD_STATS = {week, games: {}, stats: {}, lead: {
    "9001": {n: "Test Rusher", pos: "RB", team: "SF", s: {rush_td: 2}, pts: 20},
    "9002": {n: "Test Passer", pos: "QB", team: "SF", s: {pass_td: 3}, pts: 24},
    "9003": {n: "Test Catcher", pos: "WR", team: "KC", s: {rec_td: 1}, pts: 12},
    "9004": {n: "Detroit Grabber", pos: "WR", team: "DET", s: {rec_td: 1}, pts: 11}}};
  GD_AT = Date.now(); GD_ERR = "";
  LIVE_CLIPS.week = cfg.clipsWeek === null ? week : cfg.clipsWeek;
  LIVE_CLIPS.players["test-rusher"] = [{id: "o1", title: "Rusher scores", kind: "play", secs: 20, embed: true, shape: "wide"}];
  LIVE_CLIPS.players["test-catcher"] = [{id: "o2", title: "Catcher's grab", kind: "play", secs: 20, embed: true, shape: "wide"}];
  tdcServed = () => true;
  clipEmbedOk = () => true;
  tdcNameRow = slug => ({"test-rusher": {n: 22, t: "SF", k: ["the rocket"]}, "test-catcher": {n: null, t: "KC", k: []}})[slug] || null;
  window.__realOpen = clipTheaterOpen;
  window.__opened = null;
  window.clipTheaterOpen = (items, i, el) => { window.__opened = {ids: items.map(it => it.c.id), i, el: !!el}; };
  window.clipWarm = () => {};
  window.__replies = cfg.replies; window.__calls = []; window.__fly = 0; window.__peak = 0; window.__gate = null; window.__fail = [];
  window.fetch = async (url) => {
    const ch = /ch=([^&]+)/.exec(url)[1];
    window.__calls.push(ch);
    window.__fly++; window.__peak = Math.max(window.__peak, window.__fly);
    try {
      if (window.__gate) await window.__gate;
      if (window.__fail.includes(ch)) throw new Error("network");
      return {ok: true, json: async () => ({ch, clips: window.__replies[ch] || []})};
    } finally { window.__fly--; }
  };
}"""

ADVANCE = "(s) => { window.__now += s * 1000; GD_AT = Date.now(); paintLive(); }"
REEL = """() => [...document.querySelectorAll('.td-reel .reel-card')].map(c => ({id: c.dataset.clipid,
  nm: c.querySelector('.reel-nm').textContent, cap: c.querySelector('.reel-cap').textContent, tag: c.tagName,
  disc: !!c.querySelector('.reel-disc')}))"""
IDS = "() => [...document.querySelectorAll('.td-reel .reel-card')].map(c => c.dataset.clipid)"
SETTLED = "TDC.at > 0 && !TDC.busy"


def tdclips(browser, page_file, viewport=(360, 800), hours=2, replies=REPLIES, clips_week=None, wait=True, post=False):
    ctx, page, errors = live(browser, page_file, viewport)
    page.evaluate(SETUP, {"hours": hours, "replies": replies, "clipsWeek": clips_week, "post": post})
    page.click("[data-gdtab='tds']")
    if wait:
        page.wait_for_function(SETTLED)
        page.wait_for_selector(".td-reel")
    return ctx, page, errors


def test_the_reel_sits_above_scored_newest_first_with_both_sources_merged(browser, page_file):
    ctx, page, errors = tdclips(browser, page_file)
    assert page.evaluate("document.querySelector('.td-reel').compareDocumentPosition(document.querySelector('.td-card')) & Node.DOCUMENT_POSITION_FOLLOWING")
    assert page.locator(".td-reel h2").inner_text() == "TD clips"
    cards = page.evaluate(REEL)
    assert [c["id"] for c in cards] == ORDER       # one o1 though LIVE_CLIPS and SF both carry it; o2 (no time) last
    by = {c["id"]: c for c in cards}
    # the second line is the scorer's TD line, never the clip's title; a clip of two scorers is one card naming both
    assert by["h1"]["nm"] == "T. Rusher, T. Catcher" and by["h1"]["cap"] == "2 rush TD"
    assert by["g1"]["nm"] == "T. Catcher" and by["g1"]["cap"] == "1 rec TD"
    assert by["d1"]["nm"] == "D. Grabber" and by["o2"]["cap"] == "1 rec TD"
    # the card is Roster's: a disc where it plays here, the YouTube chip and a link where it does not
    assert by["f1"]["tag"] == "BUTTON" and by["f1"]["disc"] and by["d1"]["tag"] == "A" and not by["d1"]["disc"]
    assert page.locator(".td-reel .reel-thumb").first.evaluate("e => [e.offsetWidth, e.offsetHeight]") == [128, 160]
    # Play n counts what plays here (all but d1), and opens the theater on the first
    assert page.locator("[data-reelall]").inner_text() == "Play 8" and page.locator(".td-reel .reel-ti small").inner_text() == "9 clips"
    page.click("[data-reelall]")
    assert page.evaluate("__opened") == {"ids": ORDER, "i": 0, "el": True}
    page.evaluate("__opened = null")
    page.locator(".td-reel [data-clipid='f3']").click()
    assert page.evaluate("__opened")["i"] == ORDER.index("f3")
    # rows are unchanged: Scored still lists the three scorers, and a row opens the profile
    assert page.locator(".td-card").first.locator(".td-row").count() == 3
    opened = page.evaluate("""() => { let got = null; openProfile = p => { got = p; };
      document.querySelector('.td-card .td-row').click(); return got; }""")
    assert opened["n"] == "Test Rusher"
    # the page does not scroll sideways for the rail
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    ctx.close()
    assert errors == []


def test_a_fresh_clip_is_of_a_scorer_by_name_hashtag_nickname_or_his_own_jersey(browser, page_file):
    ctx, page, errors = tdclips(browser, page_file)
    ids = set(page.evaluate(IDS))
    assert {"f1", "h1"} <= ids                                      # last name, whole word
    assert "f2" in ids                                              # #TestRusher, no space
    assert "f4" in ids                                              # a nickname
    assert "f3" in ids                                              # No. 22, on SF's own channel
    assert "g2" not in ids and "h2" not in ids                      # 22 on KC's or the NFL's channel is nobody's
    assert "p1" in page.evaluate("tdcFor({n: 'Test Passer', slug: 'test-passer', team: 'SF'}).map(c => c.id)")   # the NFL's channel: first and last name
    assert "f7" not in ids                                          # 22 inside 22-17, 1:22 and 4th-and-22 is not a jersey
    assert "f5" not in ids and "g3" not in ids                      # a name on a channel that is neither his club's nor the NFL's
    assert "f6" not in ids                                          # posted before his game kicked off
    assert "p1" not in ids                                          # Test Passer scored no anytime TD: no Pass chip, no card
    # the rule, one clip at a time: a different player's name is not his
    assert page.evaluate("""() => {
      const w = {n: "Test Rusher", slug: "test-rusher", team: "SF"};
      const c = t => ({id: "x", title: t, posted: "2026-09-13T22:00:00Z"});
      return [tdcMatches(w, c("Test Catcher scores"), "NFL"), tdcMatches(w, c("Rusher's second"), "NFL"),
              tdcMatches(w, c("Rusher's second"), "SF"), tdcMatches(w, c("Rusher's second"), "KC"),
              tdcMatches(w, c("RÚSHER"), "SF"), tdcMatches(w, c("Week 22 recap"), "SF"), tdcMatches(w, c("a 22 yards run"), "SF"),
              tdcMatches(w, c("#22 on the run"), "SF"), tdcMatches(w, c("Test Rusher's second"), "NFL"),
              tdcMatches(w, c("T. Rusher's second"), "NFL")];
    }""") == [False, False, True, False, True, False, False, False, True, True]
    ctx.close()
    assert errors == []


def test_the_chips_decide_whose_clips_the_reel_holds(browser, page_file):
    ctx, page, errors = tdclips(browser, page_file)
    page.click("[data-tdchip='rush']")
    assert page.evaluate(IDS) == ["h1", "f1", "f4", "f3", "f2", "o1"]
    assert page.evaluate(REEL)[0]["nm"] == "T. Rusher"
    page.click("[data-tdchip='rush']")
    page.click("[data-tdchip='rec']")
    assert page.evaluate(IDS) == ["h1", "g1", "d1", "o2"]
    page.click("[data-tdchip='rec']")
    page.click("[data-tdchip='pass']")
    assert page.evaluate(IDS) == ["p1"] and page.evaluate(REEL)[0]["cap"] == "3 pass TD"
    # nobody the chips keep has a clip: no reel, and the Scored card is still there
    page.click("[data-tdchip='pass']")
    page.evaluate("window.__replies = {}; TDC.by = {}; paintLive()")
    page.evaluate("LIVE_CLIPS.week = 99; paintLive()")
    assert page.locator(".td-reel").count() == 0 and page.locator(".td-card .td-row").count() >= 3
    ctx.close()
    assert errors == []


def test_by_game_has_no_reel(browser, page_file):
    ctx, page, errors = tdclips(browser, page_file)
    page.click("[data-tdmode='game']")
    assert page.locator(".td-reel").count() == 0 and page.locator(".td-gcard").count() >= 1
    page.click("[data-tdmode='feed']")
    assert page.locator(".td-reel").count() == 1
    ctx.close()
    assert errors == []


def test_it_asks_one_request_per_channel_four_at_a_time(browser, page_file):
    ctx, page, errors = tdclips(browser, page_file, wait=False)
    # (the tab was opened before the gate: ask again from a clean slate with every request held)
    page.wait_for_function(SETTLED)
    page.evaluate("window.__calls = []; window.__peak = 0; window.__gate = new Promise(r => { window.__open = r; }); TDC.at = 0; TDC.rounds = 0; paintLive()")
    page.wait_for_function("__calls.length === 4")
    page.wait_for_timeout(150)
    assert page.evaluate("[__calls.length, __fly]") == [4, 4], "a fifth waits for one of the four"
    page.evaluate("__open()")
    page.wait_for_function(SETTLED)
    calls = page.evaluate("__calls")
    # a page's first round: SF, KC, LA and WAS (under the nflverse spelling of LAR and WSH) are on, DET and MIN ended
    # two hours ago (inside the first round's six), then NFL; MIA and BUF kicked off days ago
    assert sorted(calls) == sorted(["SF", "KC", "DET", "MIN", "LA", "WAS", "NFL"]), calls
    assert page.evaluate("__peak") == 4
    ctx.close()
    assert errors == []


def test_it_asks_again_only_after_five_minutes_and_only_while_a_game_is_on_and_the_tab_shows(browser, page_file):
    ctx, page, errors = tdclips(browser, page_file)
    n = page.evaluate("__calls.length")
    assert n == 7
    later = 5                                                       # every round after the first: the clubs on now, and NFL
    page.evaluate(ADVANCE, 299)                                     # a poll repaints; the gap is not up
    page.wait_for_timeout(100)
    assert page.evaluate("__calls.length") == n
    # a hidden tab asks nothing, even long after
    page.evaluate("Object.defineProperty(document, 'visibilityState', {configurable: true, get: () => 'hidden'})")
    page.evaluate(ADVANCE, 600)
    page.wait_for_timeout(100)
    assert page.evaluate("__calls.length") == n
    page.evaluate("Object.defineProperty(document, 'visibilityState', {configurable: true, get: () => 'visible'})")
    page.evaluate(ADVANCE, 1)
    page.wait_for_function(f"__calls.length === {n + later} && {SETTLED}")
    assert sorted(page.evaluate(f"__calls.slice({n})")) == ["KC", "LA", "NFL", "SF", "WAS"], "DET and MIN ended over an hour ago"
    # another tab asks nothing either
    page.click("[data-gdtab='games']")
    page.evaluate(ADVANCE, 600)
    page.wait_for_timeout(100)
    assert page.evaluate("__calls.length") == n + later
    ctx.close()
    assert errors == []


def test_with_no_game_on_it_asks_nothing_and_the_reel_still_shows_the_page_clips(browser, page_file):
    ctx, page, errors = tdclips(browser, page_file, hours=20, wait=False)
    page.wait_for_selector(".td-reel")
    page.wait_for_timeout(150)
    assert page.evaluate("__calls.length") == 0
    assert page.evaluate(IDS) == ["o1", "o2"]                        # LIVE_CLIPS alone, no fetch (a Monday)
    ctx.close()
    assert errors == []


def test_a_channel_that_fails_keeps_its_last_clips(browser, page_file):
    ctx, page, errors = tdclips(browser, page_file)
    assert "f1" in page.evaluate(IDS) and "h1" in page.evaluate(IDS)
    page.evaluate("window.__fail = ['SF']; window.__replies = {...__replies, SF: [], NFL: []}")
    page.evaluate(ADVANCE, 301)
    page.wait_for_function(f"__calls.length === 12 && {SETTLED}")
    ids = page.evaluate(IDS)
    assert "f1" in ids and "f3" in ids, "SF failed: its clips stay"
    assert "h1" in ids, "NFL answered with none: what it held before stays (a reply joins, it never replaces)"
    ctx.close()
    assert errors == []


def test_a_clip_that_joins_on_the_left_moves_nothing_the_reader_is_looking_at(browser, page_file):
    ctx, page, errors = tdclips(browser, page_file)
    left = "(id) => { const t = document.querySelector('.td-reel .reel-track'); return document.querySelector(`.td-reel [data-clipid='${id}']`).getBoundingClientRect().left - t.getBoundingClientRect().left; }"
    fresh = clip("n1", "Test Rusher again!", at("22:29"))
    # scrolled to the fifth card: the new clip is first, the same cards stay in view
    page.evaluate("() => { const t = document.querySelector('.td-reel .reel-track'); t.scrollLeft = document.querySelector(\".td-reel [data-clipid='f3']\").offsetLeft - t.offsetLeft; }")
    page.wait_for_function("document.querySelector('.td-reel .reel-track').scrollLeft > 100")
    page.wait_for_timeout(100)
    before, was = page.evaluate(left, "f3"), page.evaluate("document.querySelector('.td-reel .reel-track').scrollLeft")
    page.evaluate("window.__replies = {...__replies, NFL: [...__replies.NFL, %s]}" % json.dumps(fresh))
    page.evaluate(ADVANCE, 301)
    page.wait_for_function(f"__calls.length === 12 && {SETTLED}")
    assert page.evaluate(IDS)[0] == "n1"
    assert abs(page.evaluate(left, "f3") - before) <= 3
    assert page.evaluate("document.querySelector('.td-reel .reel-track').scrollLeft") > was + 100
    # at the start of the rail a new clip is simply first, and in view
    page.evaluate("document.querySelector('.td-reel .reel-track').scrollLeft = 0")
    page.wait_for_timeout(100)
    page.evaluate("window.__replies = {...__replies, NFL: [...__replies.NFL, %s]}" % json.dumps(clip("n2", "Test Rusher thrice", at("22:31"))))
    page.evaluate(ADVANCE, 301)
    page.wait_for_function(f"__calls.length === 17 && {SETTLED}")
    assert page.evaluate(IDS)[0] == "n2" and page.evaluate("document.querySelector('.td-reel .reel-track').scrollLeft") <= 1
    ctx.close()
    assert errors == []


# ---- the review's findings (2026-10-05): what a title may credit, what a reply keeps, when to ask, where focus goes

KNOWN = ["chase-brown", "harrison-wallace", "thomas-ives", "amonra-st-brown", "jameson-williams", "quincy-williams",
         "dalvin-cook", "dandre-swift", "breece-hall", "jalen-hurts"]
MATCH = """(cfg) => {
  TDC_KNOWN = {key: "", set: new Set()};
  tdcSlugs = () => cfg.known;
  return cfg.rows.map(([name, team, ch, title, n, nicks]) => {
    tdcNameRow = () => n === undefined && !nicks ? null : {n: n === undefined ? null : n, t: team, k: nicks || []};
    return tdcMatches({n: name, slug: slugOf(name), team}, {id: "x", title, posted: "2026-09-13T22:00:00Z"}, ch);
  });
}"""


def matches(page, rows):
    return page.evaluate(MATCH, {"rows": rows, "known": KNOWN})


def test_a_last_name_inside_another_players_name_credits_nobody(browser, page_file):
    ctx, page, errors = tdclips(browser, page_file, wait=False)
    traps = [  # (scorer, club, channel, title): another player's full name, on the scorer's own club's channel
        ("Ja'Marr Chase", "DET", "DET", "Chase Brown takes the handoff 40 yards"),
        ("Marvin Harrison Jr.", "MIN", "MIN", "Harrison Wallace gets the TD"),
        ("Zach Thomas", "DET", "DET", "Thomas Ives finds the end zone"),
        ("Equanimeous St. Brown", "DET", "DET", "Amon-Ra St. Brown with the grab"),
        ("Mike Williams", "DET", "DET", "Jameson Williams goes deep, Quincy Williams stops the run")]
    assert matches(page, [list(t) for t in traps]) == [False] * 5
    # the same scorer's bare last name still counts on his club's channel once the other player is out of the title
    assert matches(page, [["Ja'Marr Chase", "DET", "DET", "Chase scores again"],
                          ["Ja'Marr Chase", "DET", "DET", "Ja'Marr Chase and Chase Brown both score"],
                          ["Dalvin Cook", "DET", "DET", "Cook rumbles in"]]) == [True] * 3
    ctx.close()
    assert errors == []


def test_the_nfl_channel_never_credits_a_bare_last_name(browser, page_file):
    ctx, page, errors = tdclips(browser, page_file, wait=False)
    words = [("Dalvin Cook", "Let him cook!"), ("D'Andre Swift", "Taylor Swift in the stands"), ("Breece Hall", "A Hall of Fame play"),
             ("Jalen Hurts", "This one hurts"), ("Jordan Love", "Love is in the air"), ("Joe King", "King of the hill"),
             ("Kyle Golden", "A golden moment"), ("Rashid Worthy", "Worthy of the highlight reel"),
             ("Dalvin Cook", "Cook rumbles in")]
    assert matches(page, [[n, "DET", "NFL", t] for n, t in words]) == [False] * 9
    assert matches(page, [[n, "DET", "DET", t] for n, t in words[-1:]]) == [True], "his own club's channel may say it bare"
    # whole names, an initial and last name, #FirstLast and a nickname are the NFL channel's ways in; another initial is another player
    assert matches(page, [["Dalvin Cook", "DET", "NFL", "J. Cook finds the end zone"]]) == [False]
    assert matches(page, [["Dalvin Cook", "DET", "NFL", "Dalvin Cook scores"], ["Dalvin Cook", "DET", "NFL", "D. Cook finds the end zone"],
                          ["Dalvin Cook", "DET", "NFL", "TD! #DalvinCook"], ["Dalvin Cook", "DET", "NFL", "The Rocket takes off", None, ["the rocket"]],
                          ["Ja'Marr Chase", "DET", "NFL", "Ja'Marr Chase takes it 60"], ["Amon-Ra St. Brown", "DET", "NFL", "Amon-Ra St. Brown scores"],
                          ["Marvin Harrison Jr.", "MIN", "NFL", "Marvin Harrison Jr. scores"]]) == [True] * 7
    ctx.close()
    assert errors == []


def test_a_jersey_number_opens_the_title_or_follows_no_and_only_on_his_own_clubs_channel(browser, page_file):
    ctx, page, errors = tdclips(browser, page_file, wait=False)
    counts = [("Panthers 24, Cowboys 17", 24), ("Panthers 24, Cowboys 17", 17), ("3rd and 10", 3), ("3rd and 10", 10),
              ("Top 10 plays of the week", 10), ("4th & 1 stop", 4), ("4th & 1 stop", 1), ("#1 catch", 1), ("a 4 TD day", 4),
              ("up 21 at the half", 21), ("88 yards to the house", 88), ("22-17 final", 22)]
    assert matches(page, [["Dalvin Cook", "DET", "DET", t, n] for t, n in counts]) == [False] * len(counts)
    jerseys = [("88 in the end zone", 88), ("2 GETS HIS FIRST TD", 2), ("No. 88 scores", 88), ("No.88 scores", 88)]
    assert matches(page, [["Dalvin Cook", "DET", "DET", t, n] for t, n in jerseys]) == [True] * 4
    assert matches(page, [["Dalvin Cook", "DET", "NFL", "88 in the end zone", 88], ["Dalvin Cook", "DET", "MIN", "No. 88 scores", 88]]) == [False, False]
    ctx.close()
    assert errors == []


def test_a_reply_joins_what_the_channel_held_by_id_and_clips_older_than_30_hours_go(browser, page_file):
    ctx, page, errors = tdclips(browser, page_file)
    # the NFL posts 40 uploads an hour on a Sunday: its next 50 newest no longer reach the early clips
    page.evaluate("window.__replies = {...__replies, NFL: [%s]}" % json.dumps(clip("n3", "Test Rusher once more", at("22:40"))))
    page.evaluate(ADVANCE, 301)
    page.wait_for_function(f"__calls.length === 12 && {SETTLED}")
    assert page.evaluate("TDC.by.NFL.map(c => c.id)") == ["n3", "h1", "h2", "p1"], "newest first, none lost"
    assert page.evaluate(IDS)[:2] == ["n3", "h1"]
    got = page.evaluate("""() => { const now = Date.now(), h = n => new Date(now - n * 3600e3).toISOString();
      tdcMerge("ZZ", [{id: "a", title: "old", posted: h(31)}, {id: "b", title: "b", posted: h(29)}, {id: "c", title: "c", posted: h(1)},
                      {id: "b", title: "b2", posted: h(29)}, {id: "x", title: "no time"}], now);
      tdcMerge("ZZ", [{id: "c", title: "c again", posted: h(1)}, {id: "d", title: "d", posted: h(0.5)}], now);
      return TDC.by.ZZ.map(c => c.id + ":" + c.title); }""")
    assert got == ["d:d", "c:c again", "b:b2"], "by id, the newer wins; 31 h and no time go; newest first"
    ctx.close()
    assert errors == []


QUOTA = """(cfg) => {
  GD_GAMES.splice(1);                                              // SF at KC only
  const k = Date.parse("2026-09-13T20:25:00Z");
  return cfg.cases.map(([state, mins, slack]) => {
    GD_CLOCK = {};
    if (state) for (const c of ["SF", "KC"]) GD_CLOCK[c] = {state, q: 4, clock: "0:00", half: false, detail: "", clubs: ["SF", "KC"]};
    TDC.over = {};
    const games = tdcGames(k + mins * 60e3, slack);
    return games.length ? tdcChannels(games) : [];
  });
}"""


def test_it_asks_only_for_clubs_whose_game_is_on_or_ended_under_an_hour_ago(browser, page_file):
    ctx, page, errors = tdclips(browser, page_file, wait=False)
    hour, six, club = 3600e3, 6 * 3600e3, ["SF", "KC", "NFL"]
    cases = [("in", 60, hour), ("in", 230, hour), ("post", 225, hour), ("post", 270, hour),   # on; past a game's length; ended 30 min; ended 75 min ago
             (None, 225, hour), (None, 260, hour), ("pre", -30, hour),                         # no word but the schedule's; before kickoff
             ("post", 495, six), ("post", 600, six)]                                           # the first round's six hours
    got = page.evaluate(QUOTA, {"cases": [list(c) for c in cases]})
    assert got == [club, [], club, [], club, [], [], club, []]
    ctx.close()
    assert errors == []


def test_a_page_opened_after_the_last_whistle_asks_once_for_the_games_of_the_last_six_hours(browser, page_file):
    ctx, page, errors = tdclips(browser, page_file, hours=4.5, post=True)
    assert sorted(page.evaluate("__calls")) == sorted(["SF", "KC", "LA", "WAS", "DET", "MIN", "NFL"])
    assert page.locator(".td-reel").count() == 1
    page.evaluate(ADVANCE, 301)                                      # every game is over an hour ago now: nothing more
    page.wait_for_timeout(150)
    assert page.evaluate("__calls.length") == 7
    ctx.close()
    ctx, page, errors2 = tdclips(browser, page_file, hours=12, post=True, wait=False)     # opened the morning after
    page.wait_for_selector(".td-reel")
    page.wait_for_timeout(150)
    assert page.evaluate("__calls.length") == 0
    ctx.close()
    assert errors == [] and errors2 == []


def test_the_nfl_copy_of_a_play_within_15_minutes_of_his_clubs_is_dropped(browser, page_file):
    ctx, page, errors = tdclips(browser, page_file)
    got = page.evaluate("""() => {
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
    ctx.close()
    assert errors == []


def test_closing_the_theater_after_a_repaint_gives_focus_back_to_the_same_card_or_the_reel(browser, page_file):
    ctx, page, errors = tdclips(browser, page_file)
    ctx.route("https://**", lambda route: route.abort())
    page.evaluate("clipTheaterOpen = __realOpen; clipPlayerPlay = () => {}; clipPlayerStop = () => {}")
    card = ".td-reel [data-clipid='f3']"
    page.locator(card).click()
    page.wait_for_function("CT !== null")
    page.evaluate("paintLive()")                                     # Live's 30 s poll: the card that opened the theater is detached
    assert page.evaluate("CLIP_RETURN.isConnected") is False
    page.keyboard.press("Escape")
    page.wait_for_function("CT === null")
    assert page.evaluate("document.activeElement.dataset.clipid") == "f3" and page.evaluate("document.activeElement.isConnected")
    page.locator(card).click()
    page.wait_for_function("CT !== null")
    page.evaluate("TDC.by.SF = TDC.by.SF.filter(c => c.id !== 'f3'); paintLive()")      # and now his clip is gone from the reel
    assert page.locator(card).count() == 0
    page.keyboard.press("Escape")
    page.wait_for_function("CT === null")
    assert page.evaluate("document.activeElement === document.querySelector('.td-reel .reel-card')")
    ctx.close()
    assert errors == []

