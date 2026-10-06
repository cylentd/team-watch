/* Signed on metal (2026-10-05, the round-4 storyboard's signCard): a white-hot pen tip writes the
   card's autograph left to right, sparks fly off it, and the ink cools to gold a beat behind it.
   It drives the markup cards.js cardAutoHTML draws: .hot is the hot ink, .tip the nib, .cool the
   finished gold. Web Animations only: nothing is left running, every spark removes itself when it
   has fallen, and reduced motion gets the finished gold at once (the static card already shows it).
   The sparks follow the nib's own animation, not the wall clock, so a paused or hurried deal
   (packshow.js pkHurry) moves them with it. Returns when the ink is down. */
const SIGN_COOL = 340;          // ms the gold trails the pen by
const SIGN_STEPS = 24;          // keyframes along the stroke

function cardSign(tc, dur = 1250){
  const w = tc && tc.querySelector(".tc-auto .sgw");
  if (!w || REDUCED()) return Promise.resolve();
  const cool = w.querySelector(".cool"), hot = w.querySelector(".hot"), tip = w.querySelector(".tip");
  const W = cool.offsetWidth, H = cool.offsetHeight, N = SIGN_STEPS, D = dur;
  const clamp = x => Math.max(0, Math.min(1, x));
  const ink = cool.animate([{clipPath: "inset(-40% 100% -40% 0)"}, {clipPath: "inset(-40% 0% -40% 0)"}],
    {duration: D, delay: SIGN_COOL, easing: "linear", fill: "backwards"});
  hot.animate(Array.from({length: N + 1}, (_, k) => {
    const at = k / N * (D + SIGN_COOL);
    return {offset: k / N, opacity: 1, clipPath: `inset(-40% ${100 - clamp(at / D) * 100}% -40% ${clamp((at - SIGN_COOL) / D) * 100}%)`};
  }), {duration: D + SIGN_COOL, easing: "linear"});
  // The nib wobbles a little as it writes and drifts down the line, as a hand does.
  const wob = p => Math.sin(p * Math.PI * 7) * H * .14 - p * H * .08;
  const pen = p => ({x: p * W + 3, y: H * .55 + wob(p)});
  const nib = tip.animate(Array.from({length: N + 1}, (_, k) => ({offset: k / N, opacity: k === N ? 0 : 1,
    transform: `translate(${(k / N * W + 3).toFixed(1)}px,${wob(k / N).toFixed(1)}px)`})), {duration: D, easing: "linear"});
  signSparks(w, nib, D, pen);
  return ink.finished.catch(() => {});
}

/* Two sparks a frame from wherever the nib is, while it writes: thrown up and out, they fall, cool
   from white to gold to orange and go. Drawn in the signature's own box (.sgw), in its pixels. */
function signSparks(w, nib, D, pen){
  const css = getComputedStyle(document.documentElement), col = k => css.getPropertyValue(k).trim();
  const hues = [col("--white"), col("--gold-2"), col("--heat")];
  let seen = -1;
  const frame = () => {
    const t = nib.currentTime;
    if (!w.isConnected || nib.playState === "finished" || nib.playState === "idle" || t === null || t >= D) return;
    if (t !== seen){
      seen = t;
      const {x, y} = pen(t / D);
      for (let n = 0; n < 2; n++) signSpark(w, x, y, hues);
    }
    requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);
}
function signSpark(w, x, y, hues){
  const s = document.createElement("i");
  s.className = "spk"; s.dataset.testid = "roster-card-spark";
  w.appendChild(s);
  const vx = (Math.random() - .3) * 46, vy = -(18 + Math.random() * 34), life = 320 + Math.random() * 380;
  const a = s.animate([
    {transform: `translate(${x}px,${y}px)`, opacity: 1, background: hues[0]},
    {transform: `translate(${x + vx * .55}px,${y + vy * .55 + 6}px)`, opacity: .9, background: hues[1], offset: .5},
    {transform: `translate(${x + vx}px,${y + vy * .7 + 30}px)`, opacity: 0, background: hues[2]}],
    {duration: life, easing: "cubic-bezier(.2,.6,.4,1)"});
  a.finished.then(() => s.remove(), () => s.remove());
}
