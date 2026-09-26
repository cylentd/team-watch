/* The pack's effects (2026-09-25): foil flakes and a buzz. The flakes are small rectangles thrown up
   and out, falling with gravity and turning over as they fall, so each one flashes as it catches the
   light (its height is scaled by the cosine of its spin). Their colours are the tier's: the holo
   spectrum for a #1, the pearl for a signed card, gold otherwise, read from the tokens at run time.
   One canvas over the viewport per burst, removed when the last flake has fallen. Reduced motion
   gets neither. Android buzzes; iOS Safari has no vibrate, and the call is a no-op there. */
const PACK_FX_COLOURS = {
  one: ["--holo-1", "--holo-2", "--holo-3", "--holo-4", "--holo-5"],
  sig: ["--epic-1", "--epic-2", "--iri-2", "--ink"],

  ur: ["--gold-1", "--gold-2"],
};

function packBuzz(pattern){
  if (!REDUCED() && navigator.vibrate) try { navigator.vibrate(pattern); } catch (e) { /* not allowed here */ }
}

function packBurst(x, y, {n = 40, tier = "ur", spread = 1} = {}){
  if (REDUCED()) return;
  const css = getComputedStyle(document.documentElement);
  const colours = (PACK_FX_COLOURS[tier] || PACK_FX_COLOURS.ur).map(k => css.getPropertyValue(k).trim());
  const c = document.createElement("canvas");
  c.className = "pk-fx";
  const dpr = Math.min(2, window.devicePixelRatio || 1), w = innerWidth, h = innerHeight;
  c.width = w * dpr; c.height = h * dpr;
  document.body.appendChild(c);
  const g = c.getContext("2d");
  g.scale(dpr, dpr);
  const flakes = Array.from({length: n}, () => {
    const a = -Math.PI / 2 + (Math.random() - .5) * Math.PI * .9 * spread, v = 4 + Math.random() * 7;
    return {x, y, vx: Math.cos(a) * v, vy: Math.sin(a) * v, s: 3 + Math.random() * 5, r: Math.random() * 6.3,
            vr: (Math.random() - .5) * .5, col: colours[Math.floor(Math.random() * colours.length)], life: 1};
  });
  let last = performance.now();
  const step = now => {
    const dt = Math.min(2, (now - last) / 16.7); last = now;
    g.clearRect(0, 0, w, h);
    let alive = 0;
    for (const f of flakes){
      if (f.life <= 0) continue;
      f.vy += .22 * dt; f.vx *= .985; f.x += f.vx * dt; f.y += f.vy * dt; f.r += f.vr * dt;
      f.life -= .011 * dt;
      if (f.y > h + 20) f.life = 0;
      if (f.life <= 0) continue;
      alive++;
      g.save();
      g.globalAlpha = Math.min(1, f.life * 1.6);
      g.translate(f.x, f.y); g.rotate(f.r); g.scale(1, Math.cos(f.r * 2));
      g.fillStyle = f.col;
      g.fillRect(-f.s / 2, -f.s / 3, f.s, f.s * .66);
      g.restore();
    }
    if (alive) requestAnimationFrame(step); else c.remove();
  };
  requestAnimationFrame(step);
}
