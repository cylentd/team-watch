"""Inline the draft-war-room headshots into a self-contained index.html.

template.html holds the design; this replaces the /*__HEADS__*/ token with a
slug -> data-URI map so the page works offline and as a published Artifact.
Run: python design/build.py
"""
import base64
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent
HEADS_SRC = pathlib.Path("C:/Users/David/Github/draft-war-room/app/public/heads")

SLUGS = [
    # Yahoo - Toilet Bowl Contender
    "derrick-henry", "devon-achane", "rashee-rice", "tetairoa-mcmillan",
    "davante-adams", "jameson-williams", "josh-jacobs", "tony-pollard",
    "courtland-sutton", "matthew-stafford", "xavier-worthy", "deebo-samuel",
    "dallas-goedert",
    # ESPN - D. Luu
    "amonra-st-brown", "cam-skattebo", "tee-higgins", "george-kittle",
    "dk-metcalf", "brock-purdy", "jordan-mason", "jared-goff", "jerry-jeudy",
    "hunter-henry", "najee-harris", "tyrone-tracy",
    # wire candidates
    "chase-brown", "isaiah-likely", "jalen-coker",
]


def main():
    heads = {}
    missing = []
    for slug in SLUGS:
        path = HEADS_SRC / f"{slug}.webp"
        if not path.exists():
            missing.append(slug)
            continue
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        heads[slug] = f"data:image/webp;base64,{b64}"

    tpl = (ROOT / "template.html").read_text(encoding="utf-8")
    body = tpl.replace("/*__HEADS__*/", "const HEADS = " + json.dumps(heads) + ";")

    # design/index.html is the fragment the Artifact publisher wants (no doctype/head).
    (ROOT / "index.html").write_text(body, encoding="utf-8")

    # The repo root is what Vercel serves, so that copy is a full HTML document.
    favicon = (
        "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
        "%3Crect width='32' height='32' fill='%2308080a'/%3E"
        "%3Crect x='11' y='6' width='10' height='20' fill='%23c8ff2e'/%3E%3C/svg%3E"
    )
    head = "\n".join([
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="description" content="Team Watch - roster console for two fantasy football teams.">',
        f'<link rel="icon" href="{favicon}">',
        "<style>html{background:#08080a;color-scheme:dark}body{margin:0}"
        "img{max-width:100%}[hidden]{display:none!important}</style>",
        "</head>",
        "<body>",
    ])
    page = f"{head}\n{body}\n</body>\n</html>\n"
    (REPO / "index.html").write_text(page, encoding="utf-8")

    kb = len(page.encode("utf-8")) / 1024
    print(f"wrote {REPO/'index.html'} and {ROOT/'index.html'} ({kb:.0f} KB), {len(heads)} heads inlined")
    if missing:
        print("no headshot (initials fallback renders):", ", ".join(missing))


if __name__ == "__main__":
    main()
