/* The Breaking rail: what moved on this league's wire since the claims cleared, one still row per
   event, in rail order (data/wire.js). Never a crawl: rows stack and stay put, and only a row
   newer than the reader's last visit flashes, once. On claim day it rides under the hero, three
   rows and a "Show all"; the rest of the week it leads the tab as its own section. */
const WV_RAIL_CAP = 3;
const WV_KIND = {
  path: () => t("waiver.rail.kind.path"), drop: () => t("waiver.rail.kind.drop"),
  status: () => t("waiver.rail.kind.status"), adds: () => t("waiver.rail.kind.adds"),
};
const WV_HEALTH = {healthy: () => t("waiver.rail.healthy"), ...WV_INJURY};
const wvHealth = s => (WV_HEALTH[s] ? WV_HEALTH[s]() : esc(s || ""));
const wvNote = n => n ? ` (${esc(n)})` : "";

/* A path's "→ J. Wright is FA" / "is on waivers until Thu 3:00 AM": whether a claim on him is a
   bid. Anything but fa/waiver is unknown and says so, never "FA". */
function wvAvail(e, key){
  if (e.status === "fa") return t("waiver.rail.fa");
  if (e.status !== "waiver") return t("waiver.rail.unknown");
  const when = waiverWhen(e.clears || (waiverMeta()[key] || {}).clears);
  return when ? t("waiver.rail.waiver", {when}) : t("waiver.rail.waiverNoWhen");
}

/* What claiming him does for this roster, the producer's verdict in words: "fills your RB need",
   "starts over C. Brown at FLEX, +1.4/wk", "bench over T. Higgins, +2.1/wk". A drop always has
   one; a path has one when ff-jarvis sent it. */
function wvRailVerdict(e){
  const v = e.verdict || {};
  return v.kind === "need" ? t("waiver.rail.need", {pos: esc(e.pos)})
    : v.start ? t("waiver.rail.start", {over: esc(nameInitial(v.over)), slot: esc(v.slot || ""), margin: wvMarginHTML(v.margin)})
    : t("waiver.rail.bench", {over: esc(nameInitial(v.over)), margin: wvMarginHTML(v.margin)});
}

function wvRailText(e, key){
  const name = `<b>${esc(nameInitial(e.name))}</b>`;
  if (e.kind === "path"){
    const b = e.because || {};
    const why = WV_PRACTICE[b.practice] ? b.practice : wvHealth(b.status);
    const path = t("waiver.rail.path", {because: esc(nameInitial(b.name)), why: esc(why) + wvNote(b.note), name, avail: wvAvail(e, key)});
    return e.verdict ? t("waiver.rail.pathVerdict", {path, what: wvRailVerdict(e)}) : path;
  }
  if (e.kind === "drop")
    return t("waiver.rail.drop", {by: esc(e.by), name, pos: esc(e.pos), what: wvRailVerdict(e)});
  if (e.kind === "status"){
    const prac = WV_PRACTICE[e.practice] ? `, ${WV_PRACTICE[e.practice]()}` : "";
    return t("waiver.rail.status", {name, from: wvHealth(e.from), to: wvHealth(e.to) + wvNote(e.note) + prac});
  }
  return e.count === 1 ? t("waiver.rail.addsOne", {name}) : t("waiver.rail.adds", {n: e.count, name});
}

function wvRailRowHTML(e, key, since){
  const fresh = wireAt(e) > since ? " fresh" : "";
  // A drop's availability rides on the meta line, as the card states it: "Wed 9:20 AM · FA".
  const when = [waiverWhen(e.at), e.kind === "drop" ? wvStatusText(e, key) : ""].filter(Boolean).join(" · ");
  return `<li class="wvr-row k-${esc(e.kind)}${fresh}">
    <span class="wvr-k">${WV_KIND[e.kind]()}</span>
    <p class="wvr-t">${wvRailText(e, key)}${e.headline ? `<span class="wvr-h">${esc(e.headline)}</span>` : ""}</p>
    ${when ? `<span class="wvr-at">${when}</span>` : ""}
  </li>`;
}

/* The day the empty rail counts from: the packet's day, the day the claims were set. */
function wvRailEmptyHTML(mode){
  const day = waiverWhen(WAIVER && WAIVER.date) || waiverWhen(WIRE && WIRE.asof);
  return `<section class="wvr ${mode} empty"><p class="wvr-none">${day ? t("waiver.rail.none", {day}) : t("waiver.rail.noneYet")}</p></section>`;
}

function wvRailHTML(key, mode, since){
  const ev = wireEvents(key);
  if (!ev.length) return wvRailEmptyHTML(mode);
  const rows = ev.map(e => wvRailRowHTML(e, key, since));
  const head = `<div class="rule"><h2>${t("waiver.rail.title")}</h2>${wvCountHTML(ev.length)}<span class="hair"></span></div>`;
  if (mode === "watch")
    return `<section class="wvr watch" aria-label="${t("waiver.rail.title")}">${head}<ol class="wvr-list">${rows.join("")}</ol></section>`;
  const rest = rows.slice(WV_RAIL_CAP);
  return `<section class="wvr claim" aria-label="${t("waiver.rail.title")}">${head}
    <ol class="wvr-list">${rows.slice(0, WV_RAIL_CAP).join("")}</ol>
    ${rest.length ? `<details class="wvr-more"><summary>${t("waiver.rail.showAll", {n: ev.length})}</summary>
      <ol class="wvr-list">${rest.join("")}</ol></details>` : ""}
  </section>`;
}
