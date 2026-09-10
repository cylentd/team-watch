/* Every data-* handler for both Parlay and DFS, lifted into one function so the nav split does
   not duplicate wiring: each querySelectorAll is a harmless no-op on whichever tab has no
   matching nodes (data-dfspage and data-mktpage already worked this way before the split). */
function wireBuilder(v){
  v.querySelectorAll("[data-mpos]").forEach(b=>b.addEventListener("click",()=>{
    MKT_POS = b.dataset.mpos; MKT_PAGE = 1; render();
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
        PICK_ERR = `${p.n} is ${p.pos}, not ${DFS[ACTIVE_SLOT].slot}`;
        render();
        return;
      }
      DFS[ACTIVE_SLOT] = {...p, slot: DFS[ACTIVE_SLOT].slot};
      ACTIVE_SLOT = null; PICK_ERR = null;
    } else {
      const idx = DFS.findIndex(d => !d.n && slotEligible(d.slot, p.pos));
      if (idx === -1){ PICK_ERR = `No open ${p.pos} slot — tap one to swap instead`; render(); return; }
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
  v.querySelectorAll("[data-mine]").forEach(b=>b.addEventListener("click",()=>{
    MKT_MINE = !MKT_MINE; MKT_PAGE = 1; render();
  }));
  v.querySelectorAll("[data-msel]").forEach(sel=>sel.addEventListener("change",()=>{
    const val = sel.value;
    if (sel.dataset.msel === "mkind"){ MKT_KIND = val; MKT_SORT = val === "TD" ? "model" : (PARLAY_BOOK === "underdog" ? "conf" : "edge"); MKT_PAGE = 1; }
    else if (sel.dataset.msel === "mwin"){ MKT_WIN = val; MKT_PAGE = 1; }
    else if (sel.dataset.msel === "msort"){ MKT_SORT = val; MKT_PAGE = 1; }
    else if (sel.dataset.msel === "gwin"){ GAL_WIN = val; }
    render();
  }));
  v.querySelectorAll("[data-preset]").forEach(b=>b.addEventListener("click",()=>{
    SLIP_MODE = b.dataset.preset; SLIP = presetSlip(SLIP_MODE, PARLAY_BOOK);
    const y = window.scrollY; render(); window.scrollTo(0, y);
  }));
  v.querySelectorAll("[data-parlaybook]").forEach(b=>b.addEventListener("click",()=>{
    PARLAY_BOOK = b.dataset.parlaybook;
    MKT_PAGE = 1; MKT_SORT = MKT_KIND === "TD" ? "model" : (PARLAY_BOOK === "underdog" ? "conf" : "edge");
    SLIP = []; SLIP_MODE = "blank";
    render();
  }));
  v.querySelectorAll("[data-copy]").forEach(b=>b.addEventListener("click", async ()=>{
    const text = slipText(b.dataset.copy === "picks");
    let ok = false;
    try { await navigator.clipboard.writeText(text); ok = true; }
    catch (e) {
      const ta = document.createElement("textarea"); ta.value = text; document.body.appendChild(ta);
      ta.select(); try { ok = document.execCommand("copy"); } catch (e2) {} ta.remove();
    }
    const was = b.textContent; b.textContent = ok ? "Copied" : "Copy failed";
    setTimeout(()=>{ b.textContent = was; }, 1400);
  }));
  v.querySelectorAll("[data-scope]").forEach(b=>b.addEventListener("click",()=>{
    SLIP_SCOPE = b.dataset.scope;
    render();
  }));
  v.querySelectorAll("[data-loadslip]").forEach(b=>b.addEventListener("click",()=>{
    const [book, i] = b.dataset.loadslip.split(":");
    const card = GALLERIES[book] && GALLERIES[book][+i];
    if (!card) return;
    SLIP = card.legs.slice();
    SLIP_MODE = "custom";
    render();
    v.querySelector(".build .side .slip")?.scrollIntoView({behavior:"smooth", block:"start"});
  }));
  v.querySelectorAll("[data-explain]").forEach(el=>el.addEventListener("toggle",()=>{
    EXPLAIN[el.dataset.explain] = el.open;
  }));
  v.querySelectorAll("[data-removeleg]").forEach(b=>b.addEventListener("click",()=>{
    const i = +b.dataset.removeleg;
    SLIP = SLIP.filter(x=>x!==i);
    SLIP_MODE = "custom";
    render();
  }));
  v.querySelectorAll("[data-prop]").forEach(el=>{
    const toggle = ()=>{
      const i = +el.dataset.prop;
      SLIP = SLIP.includes(i) ? SLIP.filter(x=>x!==i) : SLIP.concat(i);
      SLIP_MODE = "custom";
      const y = window.scrollY; render(); window.scrollTo(0, y);
    };
    el.addEventListener("click", e=>{ if (e.target.closest(".more, .gl, .legx")) return; toggle(); });
    el.addEventListener("keydown", e=>{ if(e.key==="Enter"||e.key===" "){e.preventDefault();toggle();} });
  });
  v.querySelectorAll("[data-more]").forEach(b=>b.addEventListener("click", e=>{
    e.stopPropagation();
    const i = +b.dataset.more;
    if (EXPANDED.has(i)) EXPANDED.delete(i); else EXPANDED.add(i);
    const y = window.scrollY; render(); window.scrollTo(0, y);
  }));
}

