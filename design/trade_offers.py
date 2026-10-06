"""League > Teams > Find trades (2026-10-05): ff-jarvis's `trade_offers.json`, written beside the page.

ff-jarvis (model.season.trade_offers) writes, for every owner in every league, up to three bold and three
fair offers to each partner: what each side sends and ONE number, the owner's weekly gain by our projection.
~650 KB, so it is not injected into the page: the build copies it to `trade_offers.json` next to index.html
(compact, byte for byte the same data) and the page fetches it the first time a reader opens the builder
(js/surface/lboard/offers.js). Nothing else reads it.

    {"updated", "season", "rules", "leagues": {"espn"|"yahoo"|"ayo": {"week", "teams": {owner: {partner:
        {"bold": [offer], "fair": [offer]}}}}}}
    offer = {"send": [player], "get": [player], "gain", "drop": [player], "ir_moves": [player],
             "their": {"ir_moves": [player], "drop": [player]}}
    player = {"name", "pos", "team", "slug", "seen", "injury", "last2", "chips"}

A pair with no offer of either kind is left out by the producer; a kind with none is []. The shape is checked
at build time (contract.py, TRADE_OFFERS), so a field the producer drops fails the build, not the sheet.

Edit mode (2026-10-05, js/surface/lboard/tbscore.js): each league also carries what the page needs to score a
package of its own, and each offer the players the reader drops to stay at the roster cap:

    league = {..., "lineup": {"slots", "flex", "floor", "cap", "ir"},
              "values": {team: [player + {"proj", "ir", "keep", "ir_ok", "protect"}]},
              "other": {team: n}}     # n = the K/DST the team also holds: they count toward `cap`, are never released

The drop rule (2026-10-05): over the cap, a player who is eligible for IR (`ir_ok`) moves to a free IR slot
(`lineup.ir` minus those on IR) before anyone is dropped, the highest `keep` first (an offer's `ir_moves`); then the
lowest-`keep` players who are not starters, not in `get`, not on IR and not `protect` are dropped (`drop`).

The scoring rule is the producer's (its `rules` field); the page re-scores every offer it loads and hides Edit
when one differs (tbscore.js, offers.js). Until ff-jarvis writes the fields they are optional here, and when
present they are checked: `EDIT_REQUIRED` turns that into "must be present" the day the producer lands, and
`DROP_RULE_REQUIRED` does the same for the drop rule's fields (`ir`, `keep`, `ir_ok`, `protect`, `ir_moves`).

Option B (price it their way, 2026-10-05): every player object also carries `last2` (his last 2 games' average, null
with fewer than 2) and `chips` (any of "Hot", "Cold", "Early pick"), and every offer a `their`, the partner's room after
the trade by the same drop rule. The card shows the chips; the copied pitch quotes a Hot player on his `last2` and says
what `their` holds. `OPTION_B_REQUIRED` turns "checked when present" into "must be present" the day the producer lands.
"""
import json

NAME = "trade_offers.json"
KINDS = ("bold", "fair")
OFFER = ("send", "get", "gain")
PLAYER = ("name", "pos", "team", "slug", "seen", "injury")   # `injury` may be null; the key may not be missing
VALUE = PLAYER + ("proj", "ir")                              # a rostered player in `values`
DROP_VALUE = ("keep", "ir_ok", "protect")                    # what the drop rule reads of a rostered player
LINEUP = ("slots", "flex", "floor", "cap")
EDIT_REQUIRED = True     # since 2026-10-05 (ff-jarvis 29e54f2 writes lineup, values, other and drop): the old shape fails the build
# The drop rule of 2026-10-05 (IR moves, then drops by `keep`): lineup.ir, per value keep / ir_ok / protect, per offer ir_moves.
# Required since 2026-10-05 (ff-jarvis 4e69378 writes them; the live file was rewritten the same day): the old shape fails the build.
DROP_RULE_REQUIRED = True
# Option B, price it their way (spec option-b-spec.md, 2026-10-05): every player carries `last2` and `chips`, every offer
# `their`, the partner's room by the same rule. Required since 2026-10-05 (ff-jarvis 79b2b0b writes them; the live file
# was rewritten the same day): the old shape fails the build.
OPTION_B_REQUIRED = True
PERCEIVED = ("last2", "chips")                            # the two fields every player object gains; `last2` may be null
THEIR = ("ir_moves", "drop")                              # an offer's `their`: the partner's room after the trade
LIMIT = 8                                                 # contract.problems cuts at this many, so stop early


def perceived_problems(at, p):
    """A player object's option-B fields: both or neither while they are optional, both once required, `chips` a list."""
    if not (OPTION_B_REQUIRED or any(k in p for k in PERCEIVED)):
        return []
    miss = [f"{at}.{k}" for k in PERCEIVED if k not in p]
    if "chips" in p and not isinstance(p["chips"], list):
        miss.append(at + ".chips")
    return miss


def their_problems(at, o):
    """An offer's `their` ({ir_moves, drop}, the partner's room): checked when present, required with OPTION_B_REQUIRED.
    Its players are checked like any other player's (PLAYER, and the option-B fields)."""
    th = o.get("their")
    if th is None:
        return [at + ".their"] if OPTION_B_REQUIRED else []
    if not isinstance(th, dict):
        return [at + ".their"]
    miss = []
    for side in THEIR:
        if not isinstance(th.get(side), list):
            miss.append(f"{at}.their.{side}")
            continue
        for j, p in enumerate(th[side]):
            miss += [f"{at}.their.{side}[{j}].{k}" for k in PLAYER if k not in p]
            miss += perceived_problems(f"{at}.their.{side}[{j}]", p)
    return miss


def edit_problems(at, body):
    """The edit-mode fields of one league: `lineup` and `values`, checked when present, required when EDIT_REQUIRED."""
    miss = []
    lu, vals = body.get("lineup"), body.get("values")
    if lu is None:
        if EDIT_REQUIRED:
            miss.append(at + ".lineup")
    elif not isinstance(lu, dict):
        miss.append(at + ".lineup")
    else:
        miss += [f"{at}.lineup.{k}" for k in LINEUP if k not in lu]
        if "ir" not in lu and DROP_RULE_REQUIRED:
            miss.append(at + ".lineup.ir")
    if "other" not in body:
        if EDIT_REQUIRED:
            miss.append(at + ".other")
    elif not isinstance(body["other"], dict):
        miss.append(at + ".other")
    if vals is None:
        if EDIT_REQUIRED:
            miss.append(at + ".values")
    elif not isinstance(vals, dict):
        miss.append(at + ".values")
    else:
        for team, rows in vals.items():
            for j, p in enumerate(rows if isinstance(rows, list) else []):
                miss += [f"{at}.values[{team!r}][{j}].{k}" for k in VALUE if k not in p]
                miss += perceived_problems(f"{at}.values[{team!r}][{j}]", p)
                # the drop rule's fields: all three or none while they are optional, all three once required
                if DROP_RULE_REQUIRED or any(k in p for k in DROP_VALUE):
                    miss += [f"{at}.values[{team!r}][{j}].{k}" for k in DROP_VALUE if k not in p]
    return miss


def problems(doc):
    """Missing fields as `TRADE_OFFERS.leagues['espn'].teams['A']['B'].bold[0].send[1].seen`, at most LIMIT."""
    miss = []
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
        for owner, partners in body["teams"].items():
            for partner, kinds in partners.items():
                here = f"{at}.teams[{owner!r}][{partner!r}]"
                for kind in KINDS:
                    if not isinstance(kinds.get(kind), list):
                        miss.append(f"{here}.{kind}")
                        continue
                    for i, o in enumerate(kinds[kind]):
                        miss += [f"{here}.{kind}[{i}].{k}" for k in OFFER if k not in o]
                        if "drop" not in o and EDIT_REQUIRED:
                            miss.append(f"{here}.{kind}[{i}].drop")
                        if "ir_moves" not in o and DROP_RULE_REQUIRED:
                            miss.append(f"{here}.{kind}[{i}].ir_moves")
                        miss += their_problems(f"{here}.{kind}[{i}]", o)
                        for side in ("send", "get", "drop", "ir_moves"):
                            for j, p in enumerate(o.get(side) or []):
                                miss += [f"{here}.{kind}[{i}].{side}[{j}].{k}" for k in PLAYER if k not in p]
                                miss += perceived_problems(f"{here}.{kind}[{i}].{side}[{j}]", p)
                if len(miss) >= LIMIT:
                    return miss
    return miss


def compact(doc):
    """The file's text: the same data, no spaces. Emoji in a team name stay as written (the page reads UTF-8)."""
    return json.dumps(doc, ensure_ascii=False, separators=(",", ":"))


def summary(doc):
    pairs = {lg: sum(len(p) for p in body["teams"].values()) for lg, body in doc["leagues"].items()}
    return ", ".join(f"{lg} {n}" for lg, n in pairs.items()) + f" pairs with an offer, updated {doc.get('updated')}"


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
