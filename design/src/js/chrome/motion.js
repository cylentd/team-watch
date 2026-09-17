/* Motion that marks a change of context, never motion under something being read:
   - fitTitle: the team name is one line, sized down to fit, so switching teams never changes
     the hero's height (a two-line name used to shove the whole board down and back up).
   - zipFootball: a football crosses the hero on a team switch -- the "new team" beat.
   - morphLogo: the // in TEAM//WATCH crosses into an X and back on a tab switch.
   Every one is skipped under prefers-reduced-motion. */
const REDUCED = () => typeof window !== "undefined" && window.matchMedia
  && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function fitTitle(root){
  const h = (root || document).querySelector(".hero h1.fit");
  if (!h) return;
  h.style.fontSize = ""; h.style.height = "";
  const max = parseFloat(getComputedStyle(h).fontSize);
  // The box keeps the height of one line at full size, so a longer name that has to shrink sits
  // on the same baseline instead of pulling everything below it up.
  const full = h.getBoundingClientRect().height;
  let size = max;
  while (h.scrollWidth > h.clientWidth + 1 && size > 18){ size -= 2; h.style.fontSize = `${size}px`; }
  h.style.height = `${full}px`;
}
if (typeof window !== "undefined") window.addEventListener("resize", () => fitTitle());

const FOOTBALL_SVG = `<svg viewBox="0 0 64 36" aria-hidden="true">
  <ellipse cx="32" cy="18" rx="30" ry="15" fill="var(--ball)"/>
  <path d="M8 18c7-9 41-9 48 0" fill="none" stroke="var(--ball-lace)" stroke-width="1.6" opacity=".35"/>
  <path d="M8 18c7 9 41 9 48 0" fill="none" stroke="var(--ball-lace)" stroke-width="1.6" opacity=".35"/>
  <line x1="22" y1="18" x2="42" y2="18" stroke="var(--ball-lace)" stroke-width="2" stroke-linecap="round"/>
  ${[25, 29, 33, 37].map(x => `<line x1="${x}" y1="15" x2="${x}" y2="21" stroke="var(--ball-lace)" stroke-width="1.6" stroke-linecap="round"/>`).join("")}
</svg>`;

function zipFootball(){
  const hero = document.querySelector("#view .hero");
  if (!hero || REDUCED()) return;
  const z = document.createElement("div");
  z.className = "zip";
  z.innerHTML = `<span class="zip-trail"></span><span class="zip-ball">${FOOTBALL_SVG}</span>`;
  z.addEventListener("animationend", e => { if (e.target === z) z.remove(); });
  hero.appendChild(z);
}

function morphLogo(){
  const s = document.querySelector(".brand-name .slashes");
  if (!s || REDUCED()) return;
  s.classList.remove("morph");
  void s.offsetWidth;            // restart the animation when tabs change quickly
  s.classList.add("morph");
}
