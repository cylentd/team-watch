/* The pack's effects (2026-09-25): foil flakes and a buzz. The flakes are small rectangles thrown up
   and out, falling with gravity and turning over as they fall, so each one flashes as it catches the
   light (its height is scaled by the cosine of its spin). Their colours are the tier's: the holo
   spectrum for a #1, the pearl for a signed card, gold otherwise, read from the tokens at run time.
   One canvas over the viewport and one frame loop for every burst at once (2026-09-25: it was a
   canvas per burst, eight of them full-screen during one tear, which stuttered the tear itself);
   the canvas goes when the last flake has fallen. Reduced motion gets neither. Android buzzes; iOS
   Safari has no vibrate, and the call is a no-op there. */
const PACK_FX_COLOURS = {
  one: ["--holo-1", "--holo-2", "--holo-3", "--holo-4", "--holo-5"],
  sig: ["--epic-1", "--epic-2", "--iri-2", "--ink"],

  ur: ["--gold-1", "--gold-2"],
};

function packBuzz(pattern){
  if (!REDUCED() && navigator.vibrate) try { navigator.vibrate(pattern); } catch (e) { /* not allowed here */ }
}

const PACK_FX = {c: null, g: null, w: 0, h: 0, flakes: [], last: 0};

function packBurst(x, y, {n = 40, tier = "ur", spread = 1} = {}){
  if (REDUCED()) return;
  const css = getComputedStyle(document.documentElement);
  const colours = (PACK_FX_COLOURS[tier] || PACK_FX_COLOURS.ur).map(k => css.getPropertyValue(k).trim());
  for (let k = 0; k < n; k++){
    const a = -Math.PI / 2 + (Math.random() - .5) * Math.PI * .9 * spread, v = 4 + Math.random() * 7;
    PACK_FX.flakes.push({x, y, vx: Math.cos(a) * v, vy: Math.sin(a) * v, s: 3 + Math.random() * 5, r: Math.random() * 6.3,
      vr: (Math.random() - .5) * .5, col: colours[Math.floor(Math.random() * colours.length)], life: 1});
  }
  if (PACK_FX.c) return;                          // the loop already running draws these too
  const c = PACK_FX.c = document.createElement("canvas");
  c.className = "pk-fx";
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  PACK_FX.w = innerWidth; PACK_FX.h = innerHeight;
  c.width = PACK_FX.w * dpr; c.height = PACK_FX.h * dpr;
  document.body.appendChild(c);
  PACK_FX.g = c.getContext("2d");
  PACK_FX.g.scale(dpr, dpr);
  PACK_FX.last = performance.now();
  requestAnimationFrame(packFxStep);
}

function packFxStep(now){
  const F = PACK_FX, g = F.g, dt = Math.min(2, (now - F.last) / 16.7);
  F.last = now;
  g.clearRect(0, 0, F.w, F.h);
  F.flakes = F.flakes.filter(f => {
    f.vy += .22 * dt; f.vx *= .985; f.x += f.vx * dt; f.y += f.vy * dt; f.r += f.vr * dt;
    f.life -= .011 * dt;
    if (f.y > F.h + 20 || f.life <= 0) return false;
    g.save();
    g.globalAlpha = Math.min(1, f.life * 1.6);
    g.translate(f.x, f.y); g.rotate(f.r); g.scale(1, Math.cos(f.r * 2));
    g.fillStyle = f.col;
    g.fillRect(-f.s / 2, -f.s / 3, f.s, f.s * .66);
    g.restore();
    return true;
  });
  if (F.flakes.length) requestAnimationFrame(packFxStep);
  else { F.c.remove(); F.c = F.g = null; }
}
