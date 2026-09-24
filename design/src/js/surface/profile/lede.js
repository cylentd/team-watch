/* The three numbers the modal opens on, above the charts and above the tabs: what he scores,
   who he plays, and whether the role backs it up. Nothing else in the modal is set this large.

   Numbers, never a word. DESIGN.md's market rule is the reason: METHODOLOGY 12.46 failed its
   backtest, so the page prices nothing in verdicts -- no START, no BUY. Choosing three numbers
   and sizing them is the compliant way to answer "what do I do with him", and it is a better
   answer anyway, because the reader can disagree with a number.

   A cell whose source has nothing for this player is left out, not dashed: two numbers across a
   row read as two numbers, while a dash reads as a number that failed. The row itself is gone
   when no cell survives. */
function ledeCellHTML(value, label, sub, cls){
  return `<div class="pf-lede-c${cls ? " " + cls : ""}"><b>${value}</b>
    <span class="pf-lede-l">${label}</span><span class="pf-lede-s">${sub}</span></div>`;
}

function ledeProjHTML(p){
  const pts = projFor(p);
  if (pts === null) return "";
  return ledeCellHTML(pts.toFixed(1), t("profile.lede.proj"), t("profile.lede.projSub"));
}

/* The rank counted from whichever end is nearer, the same call matchupRankText makes: "20th
   easiest" reads as easy at a glance when the strip has him on the tough side. A bye is the one
   place a dash earns its keep -- the cell is the week, and the answer for the week is "none". */
function ledeMatchupHTML(prof){
  if (!prof) return "";
  const nx = prof.next;
  if (!nx) return ledeCellHTML("—", t("profile.lede.matchup"), t("profile.lede.bye"));
  const n = easiestRank(nx.factor);
  if (n === null) return "";
  const easy = n <= nx.factor.of / 2;
  return ledeCellHTML(ordinal(easy ? n : nx.factor.of - n + 1),
    easy ? t("profile.lede.easiest") : t("profile.lede.toughest"),
    t("profile.lede.ofPos", {of: nx.factor.of, pos: esc(prof.pos)}),
    matchupClass(n, nx.factor.of));
}

/* His rank on the stat the Grid ranks his position by -- the same axis the radar opens on and
   the card under it starts on, so the lede and the chart are never two different readings. */
function ledeUsageHTML(p){
  const s = sheetFor(p);
  if (!s) return "";
  const axis = s.axes.find(a => a.id === sheetDefaultAxis(s)) || s.axes[0];
  const rk = sheetRank(s.pos, axis.id, p.slug);
  if (!rk) return "";
  return ledeCellHTML(rankMark(rk), esc(axis.label), t("profile.lede.ofN", {of: rk[1]}));
}

function ledeHTML(p, prof){
  const cells = ledeProjHTML(p) + ledeMatchupHTML(prof) + ledeUsageHTML(p);
  return cells ? `<div class="pf-lede">${cells}</div>` : "";
}
