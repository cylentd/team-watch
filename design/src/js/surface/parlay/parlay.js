function parlayHTML(){
  const hasModel = PROPS.some(p=>typeof p.model==="number");
  return `<section class="hero">
    <div class="numghost">${SLIP.length}</div>
    <div class="wrap hero-in">
      <div>
        <div class="hero-eyebrow" style="--tint:var(--lime)">
          <span class="league-mark"></span><span class="lbl">${PROPS.length} lines priced · week 1</span>
        </div>
        <h1>Build the<br><em>slip</em></h1>
        <div class="modes-sub" style="margin-top:14px">
          <span class="lbl" style="margin-right:8px">Book</span>
          <button class="mode-sub" data-parlaybook="dk" aria-pressed="${PARLAY_BOOK==="dk"}">DraftKings</button>
          <button class="mode-sub" data-parlaybook="underdog" aria-pressed="${PARLAY_BOOK==="underdog"}">Underdog</button>
        </div>
      </div>
      ${PARLAY_BOOK === "underdog" ? "" : `<div><div class="signals">
        ${hasModel ? `
        <div class="sig up"><div class="lbl">Legs with edge</div><div class="sig-val">${PROPS.filter(p=>p.edge>0).length}</div><div class="sig-sub">OF ${PROPS.length} PRICED</div></div>` : `
        <div class="sig up"><div class="lbl">Lines priced</div><div class="sig-val">${PROPS.length}</div><div class="sig-sub">${new Set(PROPS.map(p=>p.n)).size} PLAYERS</div></div>
        <div class="sig"><div class="lbl">My players priced</div><div class="sig-val">${new Set(PROPS.filter(p=>p.mine).map(p=>p.n)).size}</div><div class="sig-sub">${PROPS.filter(p=>p.mine).length} LINES</div></div>`}
      </div></div>`}
    </div>
  </section>
  <div class="wrap">
    ${explainHTML("parlay")}
    ${galleryHTML()}
    <div class="build" style="margin-top:24px">
      <div class="side">${slipHTML()}</div>
      <div>
        ${marketHead("props")}
        <div class="filters">
          <span class="lbl">Position</span>
          ${["ALL","QB","RB","WR","TE"].map(p=>`<button class="chip" data-mpos="${p}" aria-pressed="${MKT_POS===p}">${p}</button>`).join("")}
          <span style="flex:1"></span>
          <button class="chip" data-mine="1" aria-pressed="${MKT_MINE}">My players only</button>
        </div>
        <div class="filters" style="margin-top:8px">
          <label class="selwrap"><span class="lbl">Market</span>
            <select class="msel" data-msel="mkind">
              ${[["ALL","All"],["TD","Anytime TD"],["RUSH","Rush yds"],["REC","Rec yds"],["RECS","Receptions"],["PASS","Pass yds"]]
                .map(([k,label])=>`<option value="${k}" ${MKT_KIND===k?"selected":""}>${label}</option>`).join("")}
            </select>
          </label>
          <label class="selwrap"><span class="lbl">Kickoff</span>
            <select class="msel" data-msel="mwin">
              <option value="ALL" ${MKT_WIN==="ALL"?"selected":""}>All</option>
              ${WINDOWS.map(w=>`<option value="${w.k}" ${MKT_WIN===w.k?"selected":""}>${esc(w.label)}</option>`).join("")}
            </select>
          </label>
          <span style="flex:1"></span>
          <label class="selwrap"><span class="lbl">Sort</span>
            <select class="msel" data-msel="msort">
              ${(PARLAY_BOOK === "underdog"
                  // Anytime TD on Underdog is a model read at P(score) on every row, so
                  // Confidence, Model % and Slip-ready would all order it the same way -- one
                  // sort, named for what it is, instead of three that visibly do nothing.
                  ? (MKT_KIND === "TD" ? [["model","Model %"]] : [["conf","Confidence"],["model","Model %"],["ready","Slip-ready"]])
                  : [["edge","Edge"],["model","Model %"],["ready","Slip-ready"]])
                .map(([k,label])=>`<option value="${k}" ${MKT_SORT===k?"selected":""}>${label}</option>`).join("")}
            </select>
          </label>
        </div>
        ${(() => {
          const all = PROPS.filter(p => (MKT_POS==="ALL"||p.pos===MKT_POS) && (MKT_KIND==="ALL"||p.mkt===MKT_KIND)
            && (MKT_WIN==="ALL"||p.win===MKT_WIN) && (!MKT_MINE||p.mine)
            // A real Underdog price without a model rating yet has no higher/lower call to
            // show; udPick covers that plus the TD rows Underdog has no line for at all.
            && (PARLAY_BOOK !== "underdog" || udPick(p))).sort(SORTS[MKT_SORT]);
          // Underdog mode groups the sorted lines by player, first appearance keeping the
          // sort (so a Confidence sort orders players by their strongest call), and pages by
          // player. DK mode stays one row per line.
          const ud = PARLAY_BOOK === "underdog";
          const groups = ud ? [...all.reduce((m, p) => (m.get(p.n) || m.set(p.n, []).get(p.n)).push(p) && m, new Map()).values()] : null;
          const units = ud ? groups : all, size = ud ? UD_PAGE_SIZE : MKT_PAGE_SIZE;
          const pages = Math.max(1, Math.ceil(units.length / size));
          const page = Math.min(MKT_PAGE, pages);
          const rows = units.slice((page-1)*size, page*size);
          const pager = `<div class="filters" style="margin-top:8px">
            <span class="lbl">${all.length} line${all.length===1?"":"s"}${ud ? ` · ${groups.length} player${groups.length===1?"":"s"}` : ""}${ud && all.some(p => udPick(p).synthetic) ? " · TD picks are the model's P(score), Underdog posts no TD line" : ""}</span>
            <span style="flex:1"></span>
            <button class="chip" data-mktpage="prev" ${page<=1?"disabled":""}>‹ Prev</button>
            <span class="lbl">Page ${page} of ${pages}</span>
            <button class="chip" data-mktpage="next" ${page>=pages?"disabled":""}>Next ›</button>
          </div>`;
          return rows.length
            ? `${pager}<div class="legs" style="margin-top:14px">${ud ? rows.map(udPlayerCard).join("") : rows.map((p)=>propCard(p, PROPS.indexOf(p))).join("")}</div>`
            : `<div class="state-empty" style="margin:20px 0;min-height:120px"><div><b>0</b><span>NO LINES MATCH THAT FILTER</span></div></div>`;
        })()}
      </div>
    </div>
  </div>`;
}

