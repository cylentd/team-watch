"""Cut the site icons from Smug Blip, the one drawing in design/src/js/lib/blip.js (2026-09-29).

    python design/icons.py      # writes icons/favicon.svg and icons/apple-touch-icon.png

Run it after a change to the smug poses or the colour tokens; the outputs are committed, since the
page and Vercel serve them as they are. Chromium draws blipSVG() with the page's own tokens and
blip.css, then:
    favicon.svg            pose "smug-16", every class resolved to plain fill/stroke attributes, so
                           the file stands alone (build.py inlines it as the page's icon)
    apple-touch-icon.png   pose "smug-app" at 180px, full bleed (iOS rounds the corners itself)
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent
SRC = ROOT / "src"
OUT = REPO / "icons"

# Resolve each shape's computed paint into attributes; drop classes and the a11y attributes the
# page version carries, then serialise.
FLATTEN = """(pose) => {
  const host = document.getElementById("host");
  host.innerHTML = blipSVG("", pose);
  const svg = host.querySelector("svg");
  const hex = c => { const m = c.match(/\\d+(\\.\\d+)?/g); if (!m || c === "none") return "none";
    return "#" + m.slice(0, 3).map(n => (+n).toString(16).padStart(2, "0")).join(""); };
  for (const el of svg.querySelectorAll("path,rect,circle")) {
    const cs = getComputedStyle(el);
    el.setAttribute("fill", hex(cs.fill));
    if (cs.stroke !== "none") {
      el.setAttribute("stroke", hex(cs.stroke));
      el.setAttribute("stroke-width", parseFloat(cs.strokeWidth));
      el.setAttribute("stroke-linecap", cs.strokeLinecap);
      el.setAttribute("stroke-linejoin", cs.strokeLinejoin);
    }
    el.removeAttribute("class");
  }
  svg.removeAttribute("class"); svg.removeAttribute("aria-hidden");
  svg.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  return svg.outerHTML.replace(/>\\s+</g, "><");
}"""


def tokens():
    """The :root custom properties from tokens.css, as one rule."""
    text = (SRC / "css" / "base" / "tokens.css").read_text(encoding="utf-8")
    return ":root{" + "".join(m.group(0) for m in re.finditer(r"--[\w-]+\s*:[^;{}]+;", text)) + "}"


def page():
    css = tokens() + (SRC / "css" / "component" / "blip.css").read_text(encoding="utf-8")
    js = "".join((SRC / "js" / "lib" / f).read_text(encoding="utf-8") for f in ("escape.js", "blip.js"))
    return (f"<!doctype html><style>{css}html,body{{margin:0;background:transparent}}"
            f"#host svg{{display:block;width:180px;height:180px}}</style>"
            f'<div id="host"></div><script>{js}</script>')


def main():
    from playwright.sync_api import sync_playwright
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        p = b.new_page(viewport={"width": 180, "height": 180})
        p.set_content(page())
        svg = p.evaluate(FLATTEN, "smug-16")
        (OUT / "favicon.svg").write_text(svg + "\n", encoding="utf-8", newline="\n")
        p.evaluate("pose => { document.getElementById('host').innerHTML = blipSVG('', pose); }", "smug-app")
        p.locator("#host svg").screenshot(path=str(OUT / "apple-touch-icon.png"))
        b.close()
    print(f"wrote {OUT / 'favicon.svg'} ({len(svg)} bytes) and {OUT / 'apple-touch-icon.png'}")


if __name__ == "__main__":
    main()
