"""League > Trades, the finder (2026-10-06; Teams > Find trades from 2026-10-05): ff-jarvis's `trade_offers.json`, written beside the page.

ff-jarvis (model.season.trade_offers, v2) writes, for every owner in every league, one flat list of offers ranked
by gain: per position (QB, RB, WR, TE) the best `per_pos` offers whose `get` holds a player there (at most
`per_partner_pos` from one partner), and per partner the best `top` offers with him; the union, deduped. Each
offer is what each side sends and ONE number, the owner's gain in REST-OF-SEASON points (since 2026-10-06, METHODOLOGY
12.99; superseded: the weekly gain by next week's projection). ~400 KB, so it is not injected into the page: the build
copies it to `trade_offers.json` next to index.html (compact, byte for byte the same data) and the page fetches it the
first time a reader opens the finder (js/surface/lboard/offers.js). Nothing else reads it.

    {"updated", "season", "rules", "leagues": {"espn"|"yahoo"|"ayo": {"week", "weeks_left", "teams": {owner: [offer]}}}}
    offer = {"partner", "send": [player], "get": [player], "gain", "drop": [player], "ir_moves": [player],
             "their": {"ir_moves": [player], "drop": [player], "gain"}}
    player = {"name", "pos", "team", "slug", "seen", "injury", "last2", "chips"}

An owner with no offer is left out by the producer. The shape is checked at build time (contract.py, TRADE_OFFERS), so a
field the producer drops fails the build, not the page. Every field below is required, and a file from before the
rest-of-season pricing fails closed here (`rules.unit` and the fields it brought are missing), so a build on old data stops
at the offers step rather than print a weekly number under "pts rest of season".

Edit mode (js/surface/lboard/tbscore.js): each league also carries what the page needs to score a package of its own, and
each offer the players the reader drops to stay at the roster cap:

    league = {..., "lineup": {"slots", "flex", "floor", "ros_floor", "cap", "ir"},
              "values": {team: [player + {"proj", "ros_pg", "games", "priced", "ir", "keep", "ir_ok", "protect"}]},
              "other": {team: n}}     # n = the K/DST the team also holds: they count toward `cap`, are never released

`ros_pg` and `games` are a player's rest-of-season points a game and expected games left, `keep` is their product (his
rest-of-season points), `proj` is next week's projection (the page's weekly chips; it no longer moves a gain), `ros_floor`
is the wire by `ros_pg` (`floor`, by `proj`, is for the chips) and `weeks_left` the weeks the gain covers.

The drop rule (2026-10-05): over the cap, a player who is eligible for IR (`ir_ok`) moves to a free IR slot
(`lineup.ir` minus those on IR) before anyone is dropped, the highest `keep` first (an offer's `ir_moves`); then the
lowest-`keep` players who are not starters, not in `get`, not on IR and not `protect` are dropped (`drop`).

The scoring rule is the producer's (its `rules.scoring` and `rules.drop`, in words); the page ports both and re-scores every
offer it loads, `gain` and `their.gain` too, and hides Edit when one differs (tbscore.js, offers.js).

Option B (price it their way, 2026-10-05): every player object also carries `last2` (his last 2 games' average, null
with fewer than 2) and `chips` (any of "Hot", "Cold", "Early pick"), and every offer a `their`, the partner's room after
the trade by the same drop rule and his own rest-of-season gain (`their.gain`, never negative). The card shows the chips; the
copied pitch quotes a Hot player on his `last2` and says what `their` holds.
"""
import json

NAME = "trade_offers.json"
UNIT = "rest of season points"                              # `rules.unit`: the words under every gain; another unit fails the build
RULE_NUMBERS = ("top", "per_pos", "per_partner_pos", "max_out", "max_in", "min_gain", "min_gain_week")   # the search's numbers; the page reads none
RULE_TEXTS = ("scoring", "drop")                            # the two rules the page ports (tbscore.js)
OFFER = ("send", "get", "gain")                             # and `partner`, a non-empty string (offer_problems)
PLAYER = ("name", "pos", "team", "slug", "seen", "injury")   # `injury` may be null; the key may not be missing
ROS_VALUE = ("proj", "ros_pg", "games", "keep")              # a rostered player's numbers the rule reads
FLAGS = ("ir", "priced", "ir_ok", "protect")                 # and the booleans
VALUE = PLAYER + ("proj", "ros_pg", "games", "priced", "ir") # a rostered player in `values` (the drop rule's `keep`, `ir_ok`, `protect` below)
DROP_VALUE = ("keep", "ir_ok", "protect")                    # what the drop rule reads of a rostered player
LINEUP = ("slots", "flex", "floor", "cap", "ir")
SKILL = ("QB", "RB", "WR", "TE")                             # the positions `lineup.floor` and `lineup.ros_floor` price
PERCEIVED = ("last2", "chips")                            # the two fields every player object gains; `last2` may be null
THEIR = ("ir_moves", "drop")                              # an offer's `their`: the partner's room after the trade (and `gain`)
LIMIT = 8                                                 # contract.problems cuts at this many, so stop early


def number(x):
    """A JSON number (a bool is not one)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def perceived_problems(at, p):
    """A player object's option-B fields: both, `chips` a list."""
    miss = [f"{at}.{k}" for k in PERCEIVED if k not in p]
    if "chips" in p and not isinstance(p["chips"], list):
        miss.append(at + ".chips")
    return miss


def their_problems(at, o):
    """An offer's `their` ({ir_moves, drop, gain}, the partner's room and his rest-of-season gain). Its players are checked
    like any other player's (PLAYER, and the option-B fields)."""
    th = o.get("their")
    if th is None or not isinstance(th, dict):
        return [at + ".their"]
    miss = []
    for side in THEIR:
        if not isinstance(th.get(side), list):
            miss.append(f"{at}.their.{side}")
            continue
        for j, p in enumerate(th[side]):
            miss += [f"{at}.their.{side}[{j}].{k}" for k in PLAYER if k not in p]
            miss += perceived_problems(f"{at}.their.{side}[{j}]", p)
    if not number(th.get("gain")):
        miss.append(at + ".their.gain")
    return miss


def lineup_problems(at, body):
    """`lineup` (slots, flex, floor, ros_floor, cap, ir) and the week count the gain covers."""
    miss = []
    lu = body.get("lineup")
    if not isinstance(lu, dict):
        miss.append(at + ".lineup")
    else:
        miss += [f"{at}.lineup.{k}" for k in LINEUP if k not in lu]
        if not isinstance(lu.get("ros_floor"), dict):
            miss.append(at + ".lineup.ros_floor")
        else:
            miss += [f"{at}.lineup.ros_floor.{k}" for k in SKILL if not number(lu["ros_floor"].get(k))]
    weeks = body.get("weeks_left")
    if not isinstance(weeks, int) or isinstance(weeks, bool) or weeks < 1:
        miss.append(at + ".weeks_left")
    return miss


def values_problems(at, body):
    """The rows the page scores a package from: every rostered player with his rest-of-season numbers and the drop rule's."""
    miss = []
    vals = body.get("values")
    if "other" not in body or not isinstance(body["other"], dict):
        miss.append(at + ".other")
    if not isinstance(vals, dict):
        return miss + [at + ".values"]
    for team, rows in vals.items():
        for j, p in enumerate(rows if isinstance(rows, list) else []):
            here = f"{at}.values[{team!r}][{j}]"
            miss += [f"{here}.{k}" for k in VALUE + DROP_VALUE if k not in p]
            miss += perceived_problems(here, p)
            miss += [f"{here}.{k}" for k in ROS_VALUE + ("seen",) if k in p and not number(p[k])]
            miss += [f"{here}.{k}" for k in FLAGS if k in p and not isinstance(p[k], bool)]
    return miss


def edit_problems(at, body):
    """The edit-mode fields of one league: `lineup`, `weeks_left`, `values` and `other`, all required."""
    return lineup_problems(at, body) + values_problems(at, body)


def rules_problems(doc):
    """`rules` carries the numbers the producer's search ran on, the unit of every gain and the two rule texts the page ports."""
    rules = doc.get("rules")
    if not isinstance(rules, dict):
        return ["TRADE_OFFERS.rules"]
    miss = [f"TRADE_OFFERS.rules.{k}" for k in RULE_NUMBERS if not number(rules.get(k))]
    miss += [f"TRADE_OFFERS.rules.{k}" for k in RULE_TEXTS if not (isinstance(rules.get(k), str) and rules[k])]
    if rules.get("unit") != UNIT:
        miss.append("TRADE_OFFERS.rules.unit")
    return miss


def offer_problems(at, o):
    """One offer of an owner's flat list: its own fields, the partner it is with, and every player object in it."""
    miss = [f"{at}.{k}" for k in OFFER if k not in o]
    if not isinstance(o.get("partner"), str) or not o["partner"]:
        miss.append(f"{at}.partner")
    for k in ("drop", "ir_moves"):
        if k not in o:
            miss.append(f"{at}.{k}")
    miss += their_problems(at, o)
    for side in ("send", "get", "drop", "ir_moves"):
        for j, p in enumerate(o.get(side) or []):
            miss += [f"{at}.{side}[{j}].{k}" for k in PLAYER if k not in p]
            miss += perceived_problems(f"{at}.{side}[{j}]", p)
    return miss


def problems(doc):
    """Missing fields as `TRADE_OFFERS.leagues['espn'].teams['A'][0].send[1].seen`, at most LIMIT."""
    miss = rules_problems(doc)
    if not isinstance(doc.get("leagues"), dict):
        return ["TRADE_OFFERS.leagues"]
    for lg, body in doc["leagues"].items():
        at = f"TRADE_OFFERS.leagues[{lg!r}]"
        if not isinstance(body, dict) or not isinstance(body.get("teams"), dict):
            miss.append(at + ".teams")
            continue
        if "week" not in body:
            miss.append(at + ".week")
        miss += edit_problems(at, body)
        for owner, offers in body["teams"].items():
            here = f"{at}.teams[{owner!r}]"
            if not isinstance(offers, list):
                miss.append(here)
                continue
            for i, o in enumerate(offers):
                miss += offer_problems(f"{here}[{i}]", o)
            if len(miss) >= LIMIT:
                return miss
    return miss


def compact(doc):
    """The file's text: the same data, no spaces. Emoji in a team name stay as written (the page reads UTF-8)."""
    return json.dumps(doc, ensure_ascii=False, separators=(",", ":"))


def summary(doc):
    n = {lg: (len(body["teams"]), sum(len(o) for o in body["teams"].values())) for lg, body in doc["leagues"].items()}
    return ", ".join(f"{lg} {offers} offers from {owners} owner{'s' if owners != 1 else ''}"
                     for lg, (owners, offers) in n.items()) + f", updated {doc.get('updated')}"


def build(repo):
    """build.py's one call: read the offers (feed block first, file second), check them, write
    `<repo>/trade_offers.json`, and return the summary line. With no offers from ff-jarvis nothing is
    written and the line says so; the sheet then shows its error state."""
    import contract                       # imported here: contract.py imports this module for its shape check
    from sources import load_trade_offers
    doc = load_trade_offers()
    if not doc:
        return "Offers: none from ff-jarvis, so the trade builder says it could not load them"
    contract.validate("TRADE_OFFERS", doc)
    text = compact(doc)
    (repo / NAME).write_text(text, encoding="utf-8")
    return f"Offers: {summary(doc)}; {len(text.encode('utf-8')) / 1024:.0f} KB to {NAME}"
