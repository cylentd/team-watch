/* DIGEST CARD: Usage movers (Wednesday). ff-jarvis's five biggest role changes of the week (LIVE_USAGE_MOVERS,
   design/usage_movers.py): the share of team targets (WR, TE) or snaps (RB) now, and its change since last week.
   Row: the player, Claude's line under his name, a sparkline of the last three weeks, the share at the right.
   Research: the three weeks, his targets and carries, and the teammate who lost the work. Descriptive, not a
   model's call, so no pick word and the foot carries the untested mark. Interface: card.js. */

const DG_SPARK = {w: 54, h: 20, padX: 2, padY: 3, r: 2.6};

/* Three weeks of a share as a polyline with the last week dotted; "" for fewer than two numbers. The colours are
   classes in usage.css, so the page's tokens colour it. */
function dgSparkHTML(vals){
  const v = (vals || []).filter(x => typeof x === "number");
  if (v.length < 2) return "";
  const {w, h, padX, padY, r} = DG_SPARK, lo = Math.min(...v), span = (Math.max(...v) - lo) || 1;
  const pts = v.map((x, i) => [padX + i * (w - 2 * padX) / (v.length - 1), h - padY - (x - lo) / span * (h - 2 * padY)]);
  const [lx, ly] = pts[pts.length - 1];
  return `<svg class="dg-us-spark" data-testid="digest-us-spark" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" aria-hidden="true">`
    + `<polyline class="dg-us-line" points="${pts.map(p => p.map(n => n.toFixed(1)).join(",")).join(" ")}"/>`
    + `<circle class="dg-us-dot" cx="${lx.toFixed(1)}" cy="${ly.toFixed(1)}" r="${r}"/></svg>`;
}

const dgUsageDir = c => c > 0 ? "up" : c < 0 ? "down" : "flat";

/* The share now and its change: "78% snaps" over "+23 pts", "28% targets" over "+17 pts". The change is points of
   share, not snaps or targets, so the metric word sits on the share and the change says pts (also Top adds'). */
function dgUsageAnswer(r){
  const unit = r.metric === "snap" ? t("digest.card.usage.unitSnaps") : t("digest.card.usage.unitTargets");
  return {num: `${dgPct(r.now)}%`, unit, change: t("digest.card.usage.chPts", {n: dgSigned(r.change, 0)}), dir: dgUsageDir(r.change)};
}

/* What opens under the row: the weeks, the touches, the teammate who fell. */
function dgUsageResearch(r){
  const share = r.metric === "snap" ? t("digest.card.usage.snapShare") : t("digest.card.usage.tgtShare");
  const weeks = (r.spark || []).map(x => `${dgPct(x)}%`).join(" · ");
  const mate = r.teammate;
  return [weeks ? [share, weeks] : null,
    r.targets != null ? [t("digest.card.usage.targets"), r.targets] : null,
    r.carries != null ? [t("digest.card.usage.carries"), r.carries] : null,
    mate ? [mate.name, `${dgPct(mate.was)}% → ${dgPct(mate.now)}%`] : null].filter(Boolean);
}

function dgUsageRow(r){
  return dgRowHTML("usage", {slug: r.slug, n: dgShort(r.name), meta: esc(r.line || r.team || ""), mid: dgSparkHTML(r.spark),
    answer: dgUsageAnswer(r), research: dgUsageResearch(r)});
}

function dgCardUsage(ctx){
  const b = ctx.usage, rows = ((b && b.rows) || []).filter(r => r && r.now != null);
  if (!rows.length) return "";
  const to = b.to_week;
  const range = Number.isInteger(to) ? t("digest.card.usage.foot", {from: to - 2, to}) : t("digest.card.usage.footNoWeeks");
  return dgCardHTML({id: "usage", title: t("digest.card.usage.title"), more: {leaf: "usage"},
    body: rows.map(dgUsageRow).join(""), foot: range, footTip: t("digest.card.usage.mark")});
}
