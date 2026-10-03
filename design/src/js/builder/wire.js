/* Every data-* handler for both Parlay and DFS, lifted into one function so the nav split does
   not duplicate wiring: each querySelectorAll is a harmless no-op on whichever tab has no
   matching nodes (data-dfspage and data-mktpage already worked this way before the split). */
function wireBuilder(v){
  v.querySelectorAll("[data-mpos]").forEach(b=>b.addEventListener("click",()=>{
    MKT_POS = MKT_POS === b.dataset.mpos ? "ALL" : b.dataset.mpos; MKT_PAGE = 1; render();
  }));
  v.querySelectorAll("[data-dpos]").forEach(b=>b.addEventListener("click",()=>{
    DFS_POS = b.dataset.dpos; DFS_PAGE = 1; PICK_ERR = null; render();
  }));
  v.querySelectorAll("[data-dfssite]").forEach(b=>b.addEventListener("click",()=>{
    DFS_SITE = b.dataset.dfssite; DFS_PAGE = 1; ACTIVE_SLOT = null; PICK_ERR = null; render();
  }));
  v.querySelectorAll("[data-slot]").forEach(el=>{
    const pick = ()=>{
      const i = +el.dataset.slot;
      ACTIVE_SLOT = ACTIVE_SLOT === i ? null : i;
      PICK_ERR = null;
      render();
    };
    el.addEventListener("click", e=>{ if (e.target.closest("[data-remove]")) return; pick(); });
    el.addEventListener("keydown", e=>{ if(e.key==="Enter"||e.key===" "){e.preventDefault();pick();} });
  });
  v.querySelectorAll("[data-remove]").forEach(b=>b.addEventListener("click", e=>{
    e.stopPropagation();
    const i = +b.dataset.remove;
    const DFS = dfsSite().lineup;
    DFS[i] = {slot: DFS[i].slot, n: null};
    if (ACTIVE_SLOT === i) ACTIVE_SLOT = null;
    render();
  }));
  v.querySelectorAll("[data-cancelpick]").forEach(b=>b.addEventListener("click",()=>{
    ACTIVE_SLOT = null; PICK_ERR = null; render();
  }));
  v.querySelectorAll("[data-dfs]").forEach(el=>el.addEventListener("click",()=>{
    const p = dfsSite().pool[+el.dataset.dfs];
    if (!p) return;
    const DFS = dfsSite().lineup;
    if (ACTIVE_SLOT !== null){
      if (!slotEligible(DFS[ACTIVE_SLOT].slot, p.pos)){
        PICK_ERR = t("dfs.pick.wrongPos", {name: p.n, pos: p.pos, slot: DFS[ACTIVE_SLOT].slot});
        render();
        return;
      }
      DFS[ACTIVE_SLOT] = {...p, slot: DFS[ACTIVE_SLOT].slot};
      ACTIVE_SLOT = null; PICK_ERR = null;
    } else {
      const idx = DFS.findIndex(d => !d.n && slotEligible(d.slot, p.pos));
      if (idx === -1){ PICK_ERR = t("dfs.pick.noSlot", {pos: p.pos}); render(); return; }
      DFS[idx] = {...p, slot: DFS[idx].slot};
    }
    render();
  }));
  v.querySelectorAll("[data-dfspage]").forEach(b=>b.addEventListener("click",()=>{
    DFS_PAGE = Math.max(1, DFS_PAGE + (b.dataset.dfspage === "next" ? 1 : -1));
    const y = window.scrollY; render(); window.scrollTo(0, y);
  }));
  v.querySelectorAll("[data-mktpage]").forEach(b=>b.addEventListener("click",()=>{
    MKT_PAGE = Math.max(1, MKT_PAGE + (b.dataset.mktpage === "next" ? 1 : -1));
    const y = window.scrollY; render(); window.scrollTo(0, y);
  }));
  v.querySelectorAll("[data-topmode]").forEach(b=>b.addEventListener("click",()=>{
    TOP_MODE = b.dataset.topmode; render();
  }));
  v.querySelectorAll("[data-loadlineup]").forEach(b=>b.addEventListener("click",()=>{
    const l = topLineups()[+b.dataset.loadlineup];
    if (!l) return;
    const lineup = dfsSite().lineup;
    l.players.forEach((d,i)=>{ lineup[i] = {...d}; });
    ACTIVE_SLOT = null; PICK_ERR = null;
    const y = window.scrollY; render(); window.scrollTo(0, y);
  }));
  v.querySelectorAll("[data-mine],[data-mbest]").forEach(b=>b.addEventListener("click",()=>{
    if ("mbest" in b.dataset) MKT_BEST = !MKT_BEST; else MKT_MINE = !MKT_MINE; MKT_PAGE = 1; render();
  }));
  v.querySelectorAll("[data-msel]").forEach(sel=>sel.addEventListener("change",()=>{
    const val = sel.value;
    if (sel.dataset.msel === "mkind"){ MKT_KIND = val; MKT_SORT = val === "TD" ? "model" : (PARLAY_BOOK === "underdog" ? "conf" : "edge"); MKT_PAGE = 1; }
    else if (sel.dataset.msel === "msort"){ MKT_SORT = val; MKT_PAGE = 1; }
    else if (sel.dataset.msel === "gwin"){ GAL_WIN = val; MKT_PAGE = 1; }
    // A kickoff change on Slips keeps the cards that stay in view and slides them (flight.js).
    if (sel.dataset.msel === "gwin") betsFlip(render); else render();
  }));
  // The slip's own controls (presets, copy, remove, save) are wired with the tray (traywire.js).
  v.querySelectorAll("[data-parlaybook]").forEach(b=>b.addEventListener("click",()=>{
    PARLAY_BOOK = b.dataset.parlaybook;
    MKT_PAGE = 1; MKT_SORT = MKT_KIND === "TD" ? "model" : (PARLAY_BOOK === "underdog" ? "conf" : "edge");
    SLIP = []; SLIP_SIDE = {}; SLIP_MODE = "blank";
    render();
  }));
  v.querySelectorAll("[data-explain]").forEach(el=>el.addEventListener("click",()=>openExplain(el.dataset.explain)));
  v.querySelectorAll("[data-prop]").forEach(el=>{
    const toggle = ()=>betsToggleLeg(v, +el.dataset.prop, el.getBoundingClientRect());
    // The ⓘ at the row's end opens the leg sheet instead (wireBets).
    el.addEventListener("click", e=>{ if (e.target.closest(".more")) return; toggle(); });
    el.addEventListener("keydown", e=>{ if (e.target !== el) return; if(e.key==="Enter"||e.key===" "){e.preventDefault();toggle();} });
  });
}

/* A line into the slip or out of it at the model's side: a Build tap, and the leg sheet's Add
   button. An added pick flies from `from` to the tray; a removed one needs no flight, the tray just
   re-counts. */
function betsToggleLeg(v, i, from){
  if (SLIP.includes(i)){ SLIP = SLIP.filter(x=>x!==i); delete SLIP_SIDE[i]; }
  else SLIP = SLIP.concat(i);
  SLIP_MODE = "custom";
  const y = window.scrollY; render(); window.scrollTo(0, y);
  popLeg(v, i, SLIP.includes(i));
  if (SLIP.includes(i)) betsFly(from, PROPS[i].n); else betsLand(SLIP.length);
}

