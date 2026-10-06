/* ============================== LEAGUE > RECAP: SHARE, THE PICTURE ==============================
   The week drawn as one 1080px PNG with Canvas 2D (split from share.js 2026-10-06 at its line budget).
   share.js holds the data, the text version and the click; this file only draws. */

/* ---------- the picture: Canvas 2D, colours and faces read from the page's CSS tokens ---------- */

function lgShareTheme(){
  const css = getComputedStyle(document.documentElement), v = n => css.getPropertyValue(n).trim();
  const tint = (/--[\w-]+/.exec(lgTint()) || ["--yahoo"])[0];
  return {void: v("--void"), ink: v("--ink"), ink2: v("--ink-2"), ink3: v("--ink-3"), line: v("--line"), line2: v("--line-2"),
    lime: v("--lime"), league: v(tint), kick: v(`${tint}-tint`) || v(tint),
    tone: {g: v("--up"), r: v("--down"), a: v("--amber"), x: v("--ink-2")},
    tab: v("--tab"), ui: v("--ui"), mono: v("--mono"), disp: v("--disp")};
}

/* The brand mark (Smug Blip, lib/blip.js) as an image. Its parts are styled by the page's CSS classes, which an
   image does not see, so each part gets its fill and stroke as attributes here. */
async function lgShareMark(th){
  const part = {bulb: `fill="${th.lime}"`, screen: `fill="${th.lime}"`, eye: `fill="${th.void}"`,
    mouth: `fill="none" stroke="${th.void}" stroke-width="4.8" stroke-linecap="round"`};
  const svg = blipSVG("", "smug").replace(/class="blip-(\w+)"/g, (_, k) => part[k] || "")
    .replace("<svg ", `<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg" `);
  const img = new Image();
  img.src = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
  await img.decode();
  return img;
}

/* The lead's Blip, reacting, as an image (David, 2026-10-06: "it would add character"): the one on the page,
   cloned with each part's computed paint written in as attributes, since an image sees no CSS. The resting
   face (.br-f0) goes, so a clone taken mid-animation still shows the reaction. Null when the page has none. */
const LG_SHARE_PAINT = ["fill", "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin", "opacity", "font-family", "font-size", "font-weight"];
async function lgShareBlip(){
  const src = document.querySelector(".bp2-lead .bp2-blip svg");
  if (!src) return null;
  const copy = src.cloneNode(true), from = [src, ...src.querySelectorAll("*")], to = [copy, ...copy.querySelectorAll("*")];
  from.forEach((el, i) => {
    const cs = getComputedStyle(el);
    LG_SHARE_PAINT.forEach(k => to[i].setAttribute(k, cs.getPropertyValue(k)));
    to[i].removeAttribute("class");
  });
  copy.querySelectorAll("[opacity]").forEach(el => el.setAttribute("opacity", "1"));
  to.forEach((el, i) => { if (from[i].classList.contains("br-f0")) el.remove(); });
  copy.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  copy.setAttribute("width", "120"); copy.setAttribute("height", "120");
  const img = new Image();
  img.src = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(new XMLSerializer().serializeToString(copy))}`;
  try { await img.decode(); return img; } catch (e) { return null; }
}

function lgShareWrap(ctx, text, maxW){
  const lines = [];
  let cur = "";
  for (const word of String(text).split(/\s+/)){
    const next = cur ? `${cur} ${word}` : word;
    if (cur && ctx.measureText(next).width > maxW){ lines.push(cur); cur = word; } else cur = next;
  }
  return cur ? [...lines, cur] : lines;
}

/* Kicker and headline, Blip reacting at the right when there is one; returns the next y. */
const LG_SHARE_BLIP = 180;
function lgShareHead(ctx, d, th, y, blip){
  const inner = LG_SHARE_W - 2 * LG_SHARE_PAD, top = y;
  ctx.fillStyle = th.league; ctx.fillRect(0, 0, LG_SHARE_W, 10);
  ctx.font = `700 26px ${th.mono}`; ctx.letterSpacing = "3.6px"; ctx.fillStyle = th.kick;
  ctx.fillText(d.kicker.toUpperCase(), LG_SHARE_PAD, y + 26);
  ctx.letterSpacing = "0px";
  y += 26 + 16;
  ctx.font = `900 80px ${th.tab}`; ctx.fillStyle = th.ink;
  const wide = blip ? inner - LG_SHARE_BLIP - 24 : inner;
  lgShareWrap(ctx, d.headline.toUpperCase(), wide).forEach(l => { ctx.fillText(l, LG_SHARE_PAD, y + 66); y += 74; });
  if (blip){
    ctx.drawImage(blip, LG_SHARE_W - LG_SHARE_PAD - LG_SHARE_BLIP, top, LG_SHARE_BLIP, LG_SHARE_BLIP);
    y = Math.max(y, top + LG_SHARE_BLIP);
  }
  return y + 22;
}

/* An award stamp, the page's (front.css .lg-stamp): condensed caps outlined in its colour, a slight tilt. With
   draw false it only measures. Returns its width. */
function lgShareStamp(ctx, th, tg, x, y, draw){
  ctx.font = `900 26px ${th.tab}`; ctx.letterSpacing = "1.5px";
  const label = tg.label.toUpperCase(), w = ctx.measureText(label).width + 20, color = th.tone[tg.tone] || th.ink2;
  if (draw){
    ctx.save(); ctx.translate(x + w / 2, y + 22); ctx.rotate(-2 * Math.PI / 180);
    ctx.strokeStyle = color; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.roundRect(-w / 2, -18, w, 36, 5); ctx.stroke();
    ctx.fillStyle = color; ctx.fillText(label, -w / 2 + 10, 10); ctx.restore();
  }
  ctx.letterSpacing = "0px";
  return w;
}

/* One game: its score line, each stamp after the score of the team it names and the Nail-biter last, as on the
   page (lgScoreLineHTML); a side that does not fit starts the next line whole. Then the game's line. */
function lgShareGame(ctx, r, th, y){
  const inner = LG_SHARE_W - 2 * LG_SHARE_PAD, x0 = LG_SHARE_PAD;
  ctx.fillStyle = th.line; ctx.fillRect(x0, y, inner, 2);
  y += 2 + 18;
  // a score beside its name takes the name's face (STYLE.md "Type")
  const txt = (s, font, color, gap) => ({s, font, color, gap}), stamps = side => r.tags.filter(tg => tg.side === side).map(tg => ({tg, gap: 12}));
  const units = [
    [txt(r.win, `800 34px ${th.ui}`, th.ink, 10), txt(r.winPts, `800 34px ${th.ui}`, th.ink, 12), ...stamps("win")],
    [txt(r.tie ? t("league.lead.tied") : t("league.lead.def"), `400 34px ${th.ui}`, th.ink3, 12)],
    [txt(r.lose, `600 34px ${th.ui}`, th.ink3, 10), txt(r.losePts, `600 34px ${th.ui}`, th.ink3, 12), ...stamps("lose")],
    stamps("game")].filter(u => u.length);
  const width = p => p.tg ? lgShareStamp(ctx, th, p.tg, 0, 0, false) : (ctx.font = p.font, ctx.measureText(p.s).width);
  let x = x0;
  units.forEach(u => {
    const uw = u.reduce((n, p) => n + width(p) + p.gap, 0);
    if (x > x0 && x + uw - u[u.length - 1].gap > x0 + inner){ x = x0; y += 48; }
    u.forEach(p => {
      if (p.tg) x += lgShareStamp(ctx, th, p.tg, x, y, true) + p.gap;
      else { ctx.font = p.font; ctx.fillStyle = p.color; ctx.fillText(p.s, x, y + 34); x += ctx.measureText(p.s).width + p.gap; }
    });
  });
  y += 44;
  if (r.line){
    ctx.font = `500 31px ${th.ui}`;
    const lines = lgShareWrap(ctx, r.line, inner - 24);
    ctx.fillStyle = th.line2; ctx.fillRect(x0, y + 10, 6, lines.length * 40);
    ctx.fillStyle = th.ink;
    lines.forEach((l, i) => ctx.fillText(l, x0 + 24, y + 10 + i * 40 + 30));
    y += 10 + lines.length * 40;
  }
  return y + 18;
}

/* The foot: the mark, the TEAM//WATCH wordmark, the link. Returns the image's final height. */
function lgShareFoot(ctx, d, th, y, mark){
  ctx.fillStyle = th.line; ctx.fillRect(LG_SHARE_PAD, y, LG_SHARE_W - 2 * LG_SHARE_PAD, 2);
  y += 2 + 26;
  ctx.drawImage(mark, LG_SHARE_PAD, y, 44, 44);
  const base = y + 34;
  let x = LG_SHARE_PAD + 44 + 10;
  ctx.font = `800 34px ${th.disp}`; ctx.fillStyle = th.ink; ctx.letterSpacing = "-0.68px";
  ctx.fillText("TEAM", x, base);
  x += ctx.measureText("TEAM").width + 7;
  ctx.fillStyle = th.lime;
  [0, 1].forEach(i => {
    ctx.save(); ctx.translate(x + 2.9 + i * 12.5, base - 13); ctx.rotate(22 * Math.PI / 180);
    ctx.fillRect(-2.9, -13.5, 5.8, 27); ctx.restore();
  });
  x += 25 + 7;
  ctx.fillStyle = th.ink; ctx.fillText("WATCH", x, base);
  ctx.letterSpacing = "0px"; ctx.font = `400 24px ${th.mono}`; ctx.fillStyle = th.ink3; ctx.textAlign = "right";
  ctx.fillText(d.url, LG_SHARE_W - LG_SHARE_PAD, base); ctx.textAlign = "left";
  return y + 44 + 52;
}

/* The week as one PNG blob, 1080 wide, as tall as its games need. */
async function lgSharePNG(d){
  const th = lgShareTheme();
  await Promise.all([`900 80px ${th.tab}`, `800 34px ${th.ui}`, `700 26px ${th.mono}`, `800 34px ${th.disp}`].map(f => document.fonts.load(f)));
  const [mark, blip] = await Promise.all([lgShareMark(th), lgShareBlip()]), scratch = document.createElement("canvas");
  scratch.width = LG_SHARE_W; scratch.height = 700 + d.rows.length * 420;
  const sc = scratch.getContext("2d");
  sc.fillStyle = th.void; sc.fillRect(0, 0, scratch.width, scratch.height);
  let y = lgShareHead(sc, d, th, 50, blip);
  d.rows.forEach(r => { y = lgShareGame(sc, r, th, y); });
  const h = lgShareFoot(sc, d, th, y, mark), out = document.createElement("canvas");
  out.width = LG_SHARE_W; out.height = h;
  out.getContext("2d").drawImage(scratch, 0, 0);
  return new Promise((ok, no) => out.toBlob(b => b ? ok(b) : no(new Error("share: no png")), "image/png"));
}
