/* The week's pack (2026-09-25): once per league per week, the Cards view opens with a sealed pack
   holding the players who rank in the top 12 at their position this week (cards.js cardTier "ur" and
   up), so how many cards it holds is itself the news. Tap tears it; the cards deal face down and turn
   from the lowest rank to the highest, the signature card last and signed as it lands. A tap skips to
   the end; reduced motion gets the end at once. Web Animations only, no library. Opening is
   remembered in localStorage, which can refuse: then the pack simply shows again next load. */
const PACK_TIERS = ["ur", "sr", "sig", "one"];

/* The week of the next kickoff on the schedule, or null when there is none to name. */
function packWeek(){
  if (typeof LIVE_SCHEDULE === "undefined" || !LIVE_SCHEDULE) return null;
  const now = Date.now() - 4 * 3600e3;
  const next = LIVE_SCHEDULE.games.filter(g => Date.parse(g.kickoff) > now)
    .sort((a, b) => Date.parse(a.kickoff) - Date.parse(b.kickoff))[0];
  return next ? next.week : null;
}
const packKey = (team, wk) => `tw-pack-${team.key}-${wk}`;
function packOpened(team, wk){
  try { return localStorage.getItem(packKey(team, wk)) === "1"; } catch (e) { return false; }
}
function packMark(team, wk){
  try { localStorage.setItem(packKey(team, wk), "1"); } catch (e) { /* shows again next load */ }
}

/* The pack's players with their profile index, lowest rank first so the best turns last. */
function packCards(team){
  const ordered = team.roster.filter(p => p.start)
    .concat(team.roster.filter(p => !p.start && p.slot !== "OUT"), team.roster.filter(p => p.slot === "OUT"));
  return ordered.map((p, i) => ({p, i, rank: cardRank(p)}))
    .filter(c => c.rank && PACK_TIERS.includes(cardTier(c.rank)))
    .sort((a, b) => b.rank - a.rank);
}

function packHTML(team){
  const wk = packWeek(), cards = packCards(team);
  if (!wk || !cards.length || packOpened(team, wk)) return "";
  return `<div class="pack" data-pack="${wk}">
    <p class="pack-msg">${t("teams.pack.lead", {wk, n: cards.length})}</p>
    <button class="pack-seal" type="button" aria-label="${t("teams.pack.open")}">
      <span class="pack-top"></span><b>TEAM<i>//</i>WATCH</b>
      <span class="pack-wk">${t("teams.pack.week", {wk})}</span><span class="pack-n">${t("teams.pack.count", {n: cards.length})}</span>
    </button>
    <p class="pack-hint">${t("teams.pack.hint")}</p>
  </div>`;
}

function wirePack(v, team){
  const box = v.querySelector(".pack");
  if (!box) return;
  const wk = +box.dataset.pack;
  box.querySelector(".pack-seal").addEventListener("click", e => { e.stopPropagation(); packReveal(box, team, wk); });
}

async function packReveal(box, team, wk){
  packMark(team, wk);
  const cards = packCards(team), still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let skip = still;
  const seal = box.querySelector(".pack-seal"), msg = box.querySelector(".pack-msg");
  const run = (el, frames, o) => skip || !el.animate ? Promise.resolve() : el.animate(frames, {fill: "both", ...o}).finished;
  const wait = ms => skip ? Promise.resolve() : new Promise(r => setTimeout(r, ms));
  box.addEventListener("click", () => { skip = true; box.getAnimations({subtree: true}).forEach(a => a.finish()); });

  box.querySelector(".pack-hint").remove();
  await run(seal.querySelector(".pack-top"), [{transform: "none"}, {transform: "translate(40px,-70px) rotate(-16deg)", opacity: 0}], {duration: 420, easing: "ease-in"});
  await run(seal, [{transform: "none"}, {transform: "translateY(280px)", opacity: 0}], {duration: 420, easing: "ease-in"});
  seal.remove();

  const grid = document.createElement("div");
  grid.className = "cardgrid pack-grid";
  grid.innerHTML = cards.map(c => cardHTML(c.p, c.i, team.key)).join("");
  box.appendChild(grid);
  const els = [...grid.querySelectorAll(".tc")];
  els.forEach(el => el.classList.add("pk-down"));
  await Promise.all(els.map((el, i) => run(el, [{transform: "translateY(-120px) scale(.6)", opacity: 0}, {transform: "none", opacity: 1}],
    {duration: 420, delay: i * 90, easing: "cubic-bezier(.2,.8,.2,1)"})));

  for (const [i, el] of els.entries()){
    const last = i === els.length - 1, sig = el.classList.contains("tier-sig") || el.classList.contains("tier-one");
    await wait(last ? 450 : 160);
    if (sig) await run(el, [0, -3, 3, -3, 3, 0].map(d => ({transform: `rotate(${d}deg)`})), {duration: 420});
    await run(el, [{transform: "rotateY(0)"}, {transform: "rotateY(90deg)"}], {duration: sig ? 260 : 180, easing: "ease-in"});
    el.classList.remove("pk-down");
    await run(el, [{transform: "rotateY(-90deg)"}, {transform: "none"}], {duration: sig ? 520 : 300, easing: "cubic-bezier(.22,1,.36,1)"});
    const ink = el.querySelector(".tc-sig");
    if (ink) await run(ink, [{clipPath: "inset(0 100% 0 0)"}, {clipPath: "inset(0 0 0 0)"}], {duration: 900, easing: "ease-in-out"});
  }
  // Every animation above ends where the card rests anyway; cancel them so a held transform can't
  // override the tilt (cardmotion.js) or the flip once the cards are handed over.
  box.getAnimations({subtree: true}).forEach(a => a.cancel());
  els.forEach(el => el.classList.remove("pk-down"));
  const top = cards[cards.length - 1];
  msg.innerHTML = t("teams.pack.done", {name: esc(nameInitial(top.p.n)), rank: top.rank, pos: esc(top.p.pos)});
  const done = document.createElement("button");
  done.type = "button"; done.className = "chip pack-done"; done.textContent = t("teams.pack.close");
  done.addEventListener("click", e => { e.stopPropagation(); render(); });
  box.appendChild(done);
  wireCards(grid);
}
