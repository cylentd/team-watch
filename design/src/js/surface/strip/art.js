/* ------------------------------------------------------------------
   STRIP ART — the drawn pieces and the field's four numbers. Pure strings and arithmetic; nothing
   here reads the DOM or the payload.

   Globals are st-prefixed, the way Live's are gd-prefixed: the assembler puts every part in one
   scope, so a surface that owned bare names would collide with the next one.
------------------------------------------------------------------ */

/* GH is the plane's height in px (which is the field's WIDTH, seen from the sideline); BASE is the
   play lane measured down from the top of the plane -- the middle of the field, where the ball and
   the goalposts live; PEAK caps the tallest arc so a bomb still clears the banner band; EZ is each
   end zone as a percentage of the whole plane. Every other measurement is derived from these. */
const ST_FIELD = {GH: 132, BASE: 66, PEAK: 58, EZ: 8};
/* the end zone as a percentage of the TURF (the plane minus its two end zones), which is the
   coordinate space the play marks are drawn in */
const ST_EZ_PCT = ST_FIELD.EZ / (100 - 2 * ST_FIELD.EZ) * 100;
/* the posts stand on the field's centre line, one under each upright: NFL uprights are 18.5 ft
   apart on a field 160 ft wide, and the lane is measured up from the bottom of the plane */
const ST_LANE = ST_FIELD.GH - ST_FIELD.BASE, ST_HALF = 18.5 / 160 * ST_FIELD.GH / 2;

const ST_BALL = '<svg class="stball" viewBox="0 0 26 16" aria-hidden="true">'
  + '<path d="M1 8C5 1.2 21 1.2 25 8C21 14.8 5 14.8 1 8Z" fill="var(--ball)" stroke="var(--ball-lace)" stroke-opacity=".55" stroke-width=".8"/>'
  + '<path d="M9 8h8M11 6.2v3.6M13 6.2v3.6M15 6.2v3.6" stroke="var(--ball-lace)" stroke-width="1.1" fill="none"/></svg>';

/* One figure, facing right. Far limbs first so the near ones paint over them; the joints carry the
   class names figure.css rotates (hip, knee, sh, elb, torso) and pose.js sets directly on a kick. */
const ST_RUNNER = '<svg class="strig" viewBox="-18 -4 84 68" aria-hidden="true">'
  + '<g class="hip far"><path class="p" d="M17.4 29.5Q16.8 37 19 43.5L25 43.5Q27.2 37 26.6 29.5Z"/>'
  + '<g class="knee"><path class="j" d="M19 42.5L20 55L24.2 55L25 42.5Z"/><path class="s" d="M19.3 46.5H24.7"/>'
  + '<path class="k" d="M19.4 54h5.4q3.6.4 4 3.2h-9.4z"/></g></g>'
  + '<g class="torso"><g class="sh far"><path class="j" d="M18.4 11L19.2 22.5L24.8 22.5L25.6 11Z"/>'
  + '<g class="elb"><path class="p" d="M19.5 21.5L20.2 31L23.8 31L24.5 21.5Z"/><circle class="k" cx="22" cy="32.2" r="3"/></g></g>'
  + '<path class="j" d="M15.6 13Q14.8 27 17 31.5L27 31.5Q29.2 27 28.4 13Z"/><ellipse class="j" cx="22" cy="11.5" rx="9.6" ry="5.8"/>'
  + '<path class="s" d="M13.4 13.6Q22 17.6 30.6 13.6"/><rect class="p" x="16.6" y="28.4" width="10.8" height="4.4" rx="2"/>'
  + '<g class="sh near"><path class="j" d="M18.4 11L19.2 22.5L24.8 22.5L25.6 11Z"/>'
  + '<g class="elb"><path class="p" d="M19.5 21.5L20.2 31L23.8 31L24.5 21.5Z"/><circle class="k" cx="22" cy="32.2" r="3"/></g></g></g>'
  + '<g class="hip near"><path class="p" d="M17.4 29.5Q16.8 37 19 43.5L25 43.5Q27.2 37 26.6 29.5Z"/>'
  + '<g class="knee"><path class="j" d="M19 42.5L20 55L24.2 55L25 42.5Z"/><path class="s" d="M19.3 46.5H24.7"/>'
  + '<path class="k" d="M19.4 54h5.4q3.6.4 4 3.2h-9.4z"/></g></g></svg>';

/* the post's path is rewritten every frame from its two anchors -- see stPostPath */
const ST_POST = '<span class="stpost"><svg aria-hidden="true"><path d=""/></svg></span>';

/* The two anchors under one post, on the end line at the back of its end zone: A is the left end
   of the field, B the right. They are zero-size and invisible; only their screen positions matter. */
const stPostAnchors = k => {
  const x = k === "A" ? "14%" : "86%";
  return `<i class="stanc a-n${k}" style="left:${x};bottom:${ST_LANE - ST_HALF}px"></i>`
       + `<i class="stanc a-f${k}" style="left:${x};bottom:${ST_LANE + ST_HALF}px"></i>`;
};

/* Drawn from the NEAR upright's base at 0,0; the far base lands at dx,dy on screen, so how far the
   crossbar recedes is measured, not invented. Crossbar 10 ft up, uprights 35 ft above that. */
const stPostPath = (dx, dy) => {
  const CB = 16, T = 54, gx = dx / 2, gy = dy / 2;
  return `M${gx} ${gy}V${gy - CB}M0 ${-CB}L${dx} ${dy - CB}M0 ${-CB}V${-T}M${dx} ${dy - CB}V${dy - T}`;
};

/* the painted numbers, counting back down from midfield the way a real field does */
function stYards(){
  let s = "";
  for (let x = 10; x <= 90; x += 10) s += `<span class="styd" data-x="${x}" style="left:${x}%">${x <= 50 ? x : 100 - x}</span>`;
  return s;
}

const stInitials = n => String(n || "").replace(/[^A-Z]/g, "").slice(0, 2);

/* A face, or his initials when the feed carries no headshot for him -- which is a real case, not a
   fallback for nothing: a play names whoever ESPN's prose names, and a lineman who recovers his
   own fumble has no boxscore row to take a picture from. The name is on the element either way. */
function stFace(who, url, cls = ""){
  const label = ` role="img" aria-label="${esc(who || "")}"`;
  return url
    ? `<span class="stface${cls}"${label} style="background-image:url(${encodeURI(url)})"></span>`
    : `<span class="stface${cls}"${label}>${esc(stInitials(who))}</span>`;
}

const stFigure = (who, url) => `<div class="stpose">${stFace(who, url)}${ST_RUNNER}<span class="stheld">${ST_BALL}</span></div>`;
