"""League > Teams > Find trades (2026-10-05): ff-jarvis's `trade_offers.json`, written beside the page.

ff-jarvis (model.season.trade_offers) writes, for every owner in every league, up to three bold and three
fair offers to each partner: what each side sends and ONE number, the owner's weekly gain by our projection.
~650 KB, so it is not injected into the page: the build copies it to `trade_offers.json` next to index.html
(compact, byte for byte the same data) and the page fetches it the first time a reader opens the builder
(js/surface/lboard/offers.js). Nothing else reads it.

    {"updated", "season", "rules", "leagues": {"espn"|"yahoo"|"ayo": {"week", "teams": {owner: {partner:
        {"bold": [offer], "fair": [offer]}}}}}}
    offer = {"send": [player], "get": [player], "gain"}
    player = {"name", "pos", "team", "slug", "seen", "injury"}

A pair with no offer of either kind is left out by the producer; a kind with none is []. The shape is checked
at build time (contract.py, TRADE_OFFERS), so a field the producer drops fails the build, not the sheet.
"""
import json

NAME = "trade_offers.json"
KINDS = ("bold", "fair")
OFFER = ("send", "get", "gain")
PLAYER = ("name", "pos", "team", "slug", "seen", "injury")   # `injury` may be null; the key may not be missing
LIMIT = 8                                                    # contract.problems cuts at this many, so stop early


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
        for owner, partners in body["teams"].items():
            for partner, kinds in partners.items():
                here = f"{at}.teams[{owner!r}][{partner!r}]"
                for kind in KINDS:
                    if not isinstance(kinds.get(kind), list):
                        miss.append(f"{here}.{kind}")
                        continue
                    for i, o in enumerate(kinds[kind]):
                        miss += [f"{here}.{kind}[{i}].{k}" for k in OFFER if k not in o]
                        for side in ("send", "get"):
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
