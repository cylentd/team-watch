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

function lgShareWrap(ctx, text, maxW){
  const lines = [];
  let cur = "";
  for (const word of String(text).split(/\s+/)){
    const next = cur ? `${cur} ${word}` : word;
    if (cur && ctx.measureText(next).width > maxW){ lines.push(cur); cur = word; } else cur = next;
  }
  return cur ? [...lines, cur] : lines;
}

/* Kicker and headline; returns the next y. */
function lgShareHead(ctx, d, th, y){
  const inner = LG_SHARE_W - 2 * LG_SHARE_PAD;
  ctx.fillStyle = th.league; ctx.fillRect(0, 0, LG_SHARE_W, 10);
  ctx.font = `700 26px ${th.mono}`; ctx.letterSpacing = "3.6px"; ctx.fillStyle = th.kick;
  ctx.fillText(d.kicker.toUpperCase(), LG_SHARE_PAD, y + 26);
  ctx.letterSpacing = "0px";
  y += 26 + 16;
  ctx.font = `900 80px ${th.tab}`; ctx.fillStyle = th.ink;
  lgShareWrap(ctx, d.headline.toUpperCase(), inner).forEach(l => { ctx.fillText(l, LG_SHARE_PAD, y + 66); y += 74; });
  return y + 22;
}

/* One game: its score line, up to two tags (beside it when they fit, else under), then its line. */
function lgShareGame(ctx, r, th, y){
  const inner = LG_SHARE_W - 2 * LG_SHARE_PAD, x0 = LG_SHARE_PAD;
  ctx.fillStyle = th.line; ctx.fillRect(x0, y, inner, 2);
  y += 2 + 18;
  const parts = [[r.win, `800 34px ${th.ui}`, th.ink, 10], [r.winPts, `700 34px ${th.mono}`, th.ink, 16],
    [r.tie ? t("league.lead.tied") : t("league.lead.def"), `500 24px ${th.ui}`, th.ink3, 16],
    [r.lose, `600 34px ${th.ui}`, th.ink3, 10], [r.losePts, `700 34px ${th.mono}`, th.ink3, 0]];
  let x = x0, scoreW = 0;
  parts.forEach(([s, font, , gap]) => { ctx.font = font; scoreW += ctx.measureText(s).width + gap; });
  const pills = r.tags.map(tg => {
    ctx.font = `700 22px ${th.ui}`; const a = ctx.measureText(tg.label).width;
    ctx.font = `600 22px ${th.ui}`; const b = tg.name ? ctx.measureText(tg.name).width + 8 : 0;
    return {tg, a, w: a + b + 22};
  });
  const tagsW = pills.reduce((n, p) => n + p.w + 10, -10), beside = pills.length && scoreW + 16 + tagsW <= inner;
  parts.forEach(([s, font, color, gap]) => { ctx.font = font; ctx.fillStyle = color; ctx.fillText(s, x, y + 34); x += ctx.measureText(s).width + gap; });
  let ty = y + 2, tx = beside ? x0 + inner - tagsW : x0;
  if (pills.length && !beside){ ty = y + 44 + 10; y += 44 + 10; }
  pills.forEach(p => {
    const color = th.tone[p.tg.tone] || th.ink2;
    ctx.strokeStyle = color; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.roundRect(tx + 1.25, ty + 1.25, p.w - 2.5, 37.5, 6); ctx.stroke();
    ctx.font = `700 22px ${th.ui}`; ctx.fillStyle = color; ctx.fillText(p.tg.label, tx + 11, ty + 27);
    if (p.tg.name){ ctx.font = `600 22px ${th.ui}`; ctx.fillStyle = th.ink2; ctx.fillText(p.tg.name, tx + 11 + p.a + 8, ty + 27); }
    tx += p.w + 10;
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
  const mark = await lgShareMark(th), scratch = document.createElement("canvas");
  scratch.width = LG_SHARE_W; scratch.height = 700 + d.rows.length * 420;
  const sc = scratch.getContext("2d");
  sc.fillStyle = th.void; sc.fillRect(0, 0, scratch.width, scratch.height);
  let y = lgShareHead(sc, d, th, 50);
  d.rows.forEach(r => { y = lgShareGame(sc, r, th, y); });
  const h = lgShareFoot(sc, d, th, y, mark), out = document.createElement("canvas");
  out.width = LG_SHARE_W; out.height = h;
  out.getContext("2d").drawImage(scratch, 0, 0);
  return new Promise((ok, no) => out.toBlob(b => b ? ok(b) : no(new Error("share: no png")), "image/png"));
}
