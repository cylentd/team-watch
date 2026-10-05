"""League > Teams > Find trades (2026-10-05): ff-jarvis's `trade_offers.json`, written beside the page.

ff-jarvis (model.season.trade_offers) writes, for every owner in every league, up to three bold and three
fair offers to each partner: what each side sends and ONE number, the owner's weekly gain by our projection.
~650 KB, so it is not injected into the page: the build copies it to `trade_offers.json` next to index.html
(compact, byte for byte the same data) and the page fetches it the first time a reader opens the builder
(js/surface/lboard/offers.js). Nothing else reads it.

    {"updated", "season", "rules", "leagues": {"espn"|"yahoo"|"ayo": {"week", "teams": {owner: {partner:
        {"bold": [offer], "fair": [offer]}}}}}}
    offer = {"send": [player], "get": [player], "gain", "drop": [player]}
    player = {"name", "pos", "team", "slug", "seen", "injury"}

A pair with no offer of either kind is left out by the producer; a kind with none is []. The shape is checked
at build time (contract.py, TRADE_OFFERS), so a field the producer drops fails the build, not the sheet.

Edit mode (2026-10-05, js/surface/lboard/tbscore.js): each league also carries what the page needs to score a
package of its own, and each offer the players the reader drops to stay at the roster cap:

    league = {..., "lineup": {"slots", "flex", "floor", "cap"}, "values": {team: [player + {"proj", "ir"}]},
              "other": {team: n}}     # n = the K/DST the team also holds: they count toward `cap`, are never released

The scoring rule is the producer's (its `rules` field); the page re-scores every offer it loads and hides Edit
when one differs (tbscore.js, offers.js). Until ff-jarvis writes the fields they are optional here, and when
present they are checked: `EDIT_REQUIRED` turns that into "must be present" the day the producer lands.
"""
import json

NAME = "trade_offers.json"
KINDS = ("bold", "fair")
OFFER = ("send", "get", "gain")
PLAYER = ("name", "pos", "team", "slug", "seen", "injury")   # `injury` may be null; the key may not be missing
VALUE = PLAYER + ("proj", "ir")                              # a rostered player in `values`
LINEUP = ("slots", "flex", "floor", "cap")
EDIT_REQUIRED = False    # TODO(2026-10-05): True once ff-jarvis writes lineup, values and drop; the old shape then fails the build
LIMIT = 8                                                    # contract.problems cuts at this many, so stop early


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
                        for side in ("send", "get", "drop"):
                            for j, p in enumerate(o.get(side) or []):
                                miss += [f"{here}.{kind}[{i}].{side}[{j}].{k}" for k in PLAYER if k not in p]
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
