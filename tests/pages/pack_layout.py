"""Where the pack's stage stands (design/src/css/surface/teams/packshow.css): the pack, the hint over it and
the lead line under it, against the free area between the header bar and the bottom bar a phone draws
under the stage. Reads rects only; `RosterPack` (pages/roster_pack.py) opens the stage."""
from pages.roster_pack import RosterPack

LAYOUT = """() => {
  const box = sel => { const r = document.querySelector(sel).getBoundingClientRect(); return {top: r.top, bottom: r.bottom, height: r.height}; };
  const px = v => { const e = document.createElement('i'); e.style.cssText = 'position:absolute;height:' + v; document.body.appendChild(e);
    const h = e.getBoundingClientRect().height; e.remove(); return h; };
  const top = px('var(--hdr-top, 0px)'), dock = px('var(--dock-b, 0px)'), H = innerHeight;
  return {H, areaMid: top + (H - top - dock) / 2, pack: box('.pk-center'), hint: box('.pk-hint'), msg: box('.pk-msg'),
    hintText: document.querySelector('.pk-hint').textContent, msgText: document.querySelector('.pk-msg').textContent};
}"""


class PackLayout(RosterPack):
    def layout(self):
        """{H, areaMid, pack, hint, msg, hintText, msgText}: the stage's rects and the middle of its free area."""
        return self.page.evaluate(LAYOUT)
