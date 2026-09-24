/* The search sheet: opened from the nav bar's last slot, or "/" on a keyboard. On a phone the
   input docks just above the keyboard and results stack upward, best match nearest the thumb
   (search.css reverses the list; the DOM stays best-first, which is what a screen reader and the
   arrow keys follow). A result opens the profile over the sheet, and closing the profile comes
   back here with the query intact: comparing two players is search, tap, close, tap. Back closes
   one layer at a time (layers.js). The index and the matcher are data/search.js. */
const SEARCH_MAX = 8;
const SEARCH_RECENT_KEY = "tw.search.recent";
let SEARCH_ROWS = [];
let SEARCH_AT = 0;
/* Set by searchOpen(fn): a pick hands the player to fn and closes, instead of opening his
   profile. The Board fills a slot with it -- the same sheet, the same index, one destination
   swapped, rather than a second player picker built beside this one. */
let SEARCH_TAKE = null;

const searchEl = id => document.getElementById(id);

/* The last five players whose profile was opened, from anywhere on the page. Browser storage can
   throw (private mode, blocked site data); then there is simply no history. */
function searchRecent(){
  try { return JSON.parse(localStorage.getItem(SEARCH_RECENT_KEY)) || []; } catch (e){ return []; }
}
function searchRemember(p){
  const slug = p.slug || slugOf(p.n);
  try {
    localStorage.setItem(SEARCH_RECENT_KEY, JSON.stringify([slug, ...searchRecent().filter(s => s !== slug)].slice(0, 5)));
  } catch (e){ /* no storage, no history */ }
}

/* Before a letter is typed: the recent five, or on a first visit the roster of the team on screen. */
function searchIdle(){
  const by = new Map(searchIndex().map(e => [e.slug, e]));
  const recent = searchRecent().map(s => by.get(s)).filter(Boolean);
  if (recent.length) return {rows: recent, cap: t("search.list.recent")};
  const mine = ((TEAMS[VIEW] || {}).roster || []).map(p => by.get(p.slug)).filter(Boolean);
  return {rows: mine, cap: t("search.list.roster")};
}

function searchRowHTML(e, marks, i){
  const tags = e.leagues.map(k => `<span class="tag sr-lg sr-${k}">${esc(TEAMS[k].plat)}</span>`).join("");
  const meta = [e.pos, e.team].filter(Boolean).map(esc).join(" · ");
  return `<li class="sr-row" role="option" id="sr-${i}" data-sr="${i}" aria-selected="${i === SEARCH_AT}">
    <span class="sr-head">${headHTML(e)}</span>
    <span class="sr-who"><span class="sr-name">${searchNameHTML(e.n, marks)}</span><span class="sr-meta">${meta}</span></span>
    <span class="sr-tags">${tags}</span></li>`;
}

function searchPaint(){
  const q = searchEl("search-q").value.trim();
  const found = q ? searchFind(q, SEARCH_MAX) : null;
  const idle = found ? null : searchIdle();
  SEARCH_ROWS = found ? found.map(r => r.e) : idle.rows;
  SEARCH_AT = 0;
  const rows = SEARCH_ROWS.map((e, i) => searchRowHTML(e, found ? found[i].marks : [], i)).join("");
  searchEl("search-list").innerHTML = found && !found.length
    ? `<li class="sr-none" role="presentation">${t("search.empty.none", {q: esc(q)})}</li>`
    : rows + (idle && rows ? `<li class="sr-cap" role="presentation">${idle.cap}</li>` : "");
  searchEl("search-q").setAttribute("aria-activedescendant", SEARCH_ROWS.length ? "sr-0" : "");
}

function searchMove(step){
  if (!SEARCH_ROWS.length) return;
  SEARCH_AT = (SEARCH_AT + step + SEARCH_ROWS.length) % SEARCH_ROWS.length;
  searchEl("search-list").querySelectorAll("[data-sr]")
    .forEach(li => li.setAttribute("aria-selected", +li.dataset.sr === SEARCH_AT));
  searchEl("search-q").setAttribute("aria-activedescendant", `sr-${SEARCH_AT}`);
  searchEl(`sr-${SEARCH_AT}`).scrollIntoView({block: "nearest"});
}

function searchPick(i){
  const e = SEARCH_ROWS[i];
  if (!e) return;
  // Taken before the close, because closing clears it.
  if (SEARCH_TAKE){ const take = SEARCH_TAKE; searchClose(); take(searchPlayer(e)); return; }
  openProfile(searchPlayer(e), searchEl(`sr-${i}`));
}

/* iOS leaves a fixed element's bottom under the keyboard: the keyboard shrinks the visual
   viewport, not the layout one. Sizing the sheet to the visual viewport, measured here on every
   change rather than guessed, is what keeps the input on top of the keys. */
function searchFit(){
  const s = searchEl("search"), v = window.visualViewport;
  if (s.hidden || !v) return;
  s.style.setProperty("--vv-h", `${Math.round(v.height)}px`);
  s.style.setProperty("--vv-top", `${Math.round(v.offsetTop)}px`);
  // A keyboard is up when it has taken a real bite of the screen; 760.css drops the home-indicator
  // inset then, since the keyboard already covers that edge.
  s.toggleAttribute("data-kb", v.height < window.innerHeight - 120);
}

function searchOpen(take){
  const s = searchEl("search");
  if (!s.hidden) return;
  SEARCH_TAKE = typeof take === "function" ? take : null;
  s.hidden = false;
  // Focus inside the tap itself: iOS raises the keyboard only for a focus the user caused.
  searchEl("search-q").focus({preventScroll: true});
  searchPaint();
  searchFit();
  layerPush("search", searchShut);
}

/* The close itself; searchClose also takes back the history entry (layers.js). */
function searchShut(){
  const s = searchEl("search");
  if (s.hidden) return;
  s.hidden = true;
  SEARCH_TAKE = null;
  searchEl("search-q").value = "";
  searchEl("navsearch").focus({preventScroll: true});
}
function searchClose(){ searchShut(); layerDone("search"); }

function buildSearch(){
  const s = searchEl("search"), q = searchEl("search-q");
  searchEl("navsearch").addEventListener("click", searchOpen);
  searchEl("search-x").addEventListener("click", searchClose);
  q.addEventListener("input", searchPaint);
  q.addEventListener("keydown", e => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp"){ e.preventDefault(); searchMove(e.key === "ArrowDown" ? 1 : -1); }
    else if (e.key === "Enter"){ e.preventDefault(); searchPick(SEARCH_AT); }
  });
  searchEl("search-list").addEventListener("click", e => {
    const li = e.target.closest("[data-sr]");
    if (li) searchPick(+li.dataset.sr);
  });
  // The sheet's own backdrop (desktop, around the panel) closes it, like a modal's scrim.
  s.addEventListener("click", e => { if (e.target === s) searchClose(); });
  s.addEventListener("keydown", e => {
    if (e.key === "Escape" && !modalOpen().length) searchClose();
    // Two stops, the input and Cancel; results are reached with the arrow keys, not Tab.
    if (e.key === "Tab"){ e.preventDefault(); (document.activeElement === q ? searchEl("search-x") : q).focus(); }
  });
  document.addEventListener("keydown", e => {
    if (e.key !== "/" || e.metaKey || e.ctrlKey || e.altKey || modalOpen().length) return;
    const a = document.activeElement;
    if (a && (/^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName) || a.isContentEditable)) return;
    e.preventDefault();
    searchOpen();
  });
  if (window.visualViewport){
    visualViewport.addEventListener("resize", searchFit);
    visualViewport.addEventListener("scroll", searchFit);
  }
}
