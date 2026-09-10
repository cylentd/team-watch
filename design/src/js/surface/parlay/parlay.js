function parlayHTML(){
  const hasModel = PROPS.some(p=>typeof p.model==="number");
  return `<section class="hero">
    <div class="numghost">${SLIP.length}</div>
    <div class="wrap hero-in">
      <div>
        <div class="hero-eyebrow" style="--tint:var(--lime)">
          <span class="league-mark"></span><span class="lbl">${t("parlay.hero.eyebrow", {n: PROPS.length})}</span>
        </div>
        <h1>${t("parlay.hero.title")}</h1>
        <div class="modes-sub" style="margin-top:14px">
          <span class="lbl" style="margin-right:8px">${t("parlay.book.label")}</span>
          <button class="mode-sub" data-parlaybook="dk" aria-pressed="${PARLAY_BOOK==="dk"}">${t("parlay.book.dk")}</button>
          <button class="mode-sub" data-parlaybook="underdog" aria-pressed="${PARLAY_BOOK==="underdog"}">${t("parlay.book.underdog")}</button>
        </div>
      </div>
      ${PARLAY_BOOK === "underdog" ? "" : `<div><div class="signals">
        ${hasModel ? `
        <div class="sig up"><div class="lbl">${t("parlay.sig.edgeLabel")}</div><div class="sig-val">${PROPS.filter(p=>p.edge>0).length}</div><div class="sig-sub">${t("parlay.sig.edgeSub", {n: PROPS.length})}</div></div>` : `
        <div class="sig up"><div class="lbl">${t("parlay.sig.linesLabel")}</div><div class="sig-val">${PROPS.length}</div><div class="sig-sub">${t("parlay.sig.linesSub", {n: new Set(PROPS.map(p=>p.n)).size})}</div></div>
        <div class="sig"><div class="lbl">${t("parlay.sig.mineLabel")}</div><div class="sig-val">${new Set(PROPS.filter(p=>p.mine).map(p=>p.n)).size}</div><div class="sig-sub">${t("parlay.sig.mineSub", {n: PROPS.filter(p=>p.mine).length})}</div></div>`}
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
          <span class="lbl">${t("parlay.filter.position")}</span>
          ${["ALL","QB","RB","WR","TE"].map(p=>`<button class="chip" data-mpos="${p}" aria-pressed="${MKT_POS===p}">${p}</button>`).join("")}
          <span style="flex:1"></span>
          <button class="chip" data-mine="1" aria-pressed="${MKT_MINE}">${t("parlay.filter.mineOnly")}</button>
        </div>
        <div class="filters" style="margin-top:8px">
          <label class="selwrap"><span class="lbl">${t("parlay.filter.market")}</span>
            <select class="msel" data-msel="mkind">
              ${[["ALL",t("parlay.option.all")],["TD",MKT.TD],["RUSH",MKT.RUSH],["REC",MKT.REC],["RECS",MKT.RECS],["PASS",MKT.PASS]]
                .map(([k,label])=>`<option value="${k}" ${MKT_KIND===k?"selected":""}>${label}</option>`).join("")}
            </select>
          </label>
          <label class="selwrap"><span class="lbl">${t("parlay.filter.kickoff")}</span>
            <select class="msel" data-msel="mwin">
              <option value="ALL" ${MKT_WIN==="ALL"?"selected":""}>${t("parlay.option.all")}</option>
              ${WINDOWS.map(w=>`<option value="${w.k}" ${MKT_WIN===w.k?"selected":""}>${esc(w.label)}</option>`).join("")}
            </select>
          </label>
          <span style="flex:1"></span>
          <label class="selwrap"><span class="lbl">${t("parlay.filter.sort")}</span>
            <select class="msel" data-msel="msort">
              ${(PARLAY_BOOK === "underdog"
                  // Anytime TD on Underdog is a model read at P(score) on every row, so
                  // Confidence, Model % and Slip-ready would all order it the same way -- one
                  // sort, named for what it is, instead of three that visibly do nothing.
                  ? (MKT_KIND === "TD" ? [["model",t("parlay.sort.model")]] : [["conf",t("parlay.sort.conf")],["model",t("parlay.sort.model")],["ready",t("parlay.sort.ready")]])
                  : [["edge",t("parlay.sort.edge")],["model",t("parlay.sort.model")],["ready",t("parlay.sort.ready")]])
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
            <span class="lbl">${t("parlay.pager.lines", {n: all.length, s: all.length===1?"":"s"})}${ud ? ` · ${t("parlay.pager.players", {n: groups.length, s: groups.length===1?"":"s"})}` : ""}${ud && all.some(p => udPick(p).synthetic) ? ` · ${t("parlay.pager.tdNote")}` : ""}</span>
            <span style="flex:1"></span>
            <button class="chip" data-mktpage="prev" ${page<=1?"disabled":""}>${t("common.pager.prev")}</button>
            <span class="lbl">${t("common.pager.page", {page: page, pages: pages})}</span>
            <button class="chip" data-mktpage="next" ${page>=pages?"disabled":""}>${t("common.pager.next")}</button>
          </div>`;
          return rows.length
            ? `${pager}<div class="legs" style="margin-top:14px">${ud ? rows.map(udPlayerCard).join("") : rows.map((p)=>propCard(p, PROPS.indexOf(p))).join("")}</div>`
            : `<div class="state-empty" style="margin:20px 0;min-height:120px"><div><b>0</b><span>${t("parlay.empty.noLines")}</span></div></div>`;
        })()}
      </div>
    </div>
  </div>`;
}

