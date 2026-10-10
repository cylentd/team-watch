// Anytime TDs (2026-10-09): the words on a LIVE_TD_RESEARCH row. Pure: a row in, strings out. Every word is a
// content key, spelled out below so a key search finds its reader.

const TD_POTENTIAL = ["VACATED", "ROOKIE_RAMP", "ROUTES_FIRST", "EFFICIENT_PARTTIMER"];
const TD_FOR_ORDER = ["rz_work", "implied_total", "opp_allowed", "opp_missing", "near_td"];
const TD_CHECK_ORDER = [...TD_FOR_ORDER, "role_up"];
const TD_RANKS = 33; // 32 defenses: rank r in points allowed (1 = fewest) is the (33 - r)th-most

function tdNum(v) {
  return typeof v === "number" ? String(Math.round(v * 10) / 10) : "";
}

function tdPct(p) {
  return typeof p === "number" ? String(Math.round(p * 100)) : "";
}

function tdOrd(n) {
  const teen = Math.floor(n / 10) % 10 === 1;   // 10-19 (and 110-119) end in "th"
  const d = n % 10;
  if (!teen && d === 1) return t("common.ordinal.st", { n });
  if (!teen && d === 2) return t("common.ordinal.nd", { n });
  if (!teen && d === 3) return t("common.ordinal.rd", { n });
  return t("common.ordinal.th", { n });
}

function tdCheck(row, key) {
  return (row.checks || []).find(c => c.key === key) || null;
}

function tdFact(row, c) {
  const v = c.value;
  if (c.key === "rz_work") return t("slips.td.why.rz_work", { v: tdNum(v) });
  if (c.key === "implied_total") return t("slips.td.why.implied_total", { v: tdNum(v) });
  if (c.key === "opp_allowed") return t("slips.td.why.opp_allowed", { ord: tdOrd(TD_RANKS - v), pos: row.pos });
  if (c.key === "opp_missing") return t("slips.td.why.opp_missing", { opp: row.opp, v });
  if (c.key === "near_td") return t("slips.td.why.near_td", { v });
  return t("slips.td.why.role_up");
}

function tdChips(row) {
  const sig = (tdCheck(row, "role_up") || {}).value;
  const list = Array.isArray(sig) ? sig : [];
  const out = [];
  if (list.includes("RISING")) out.push(t("slips.td.chip.rising"));
  if (list.some(s => TD_POTENTIAL.includes(s))) out.push(t("slips.td.chip.newrole"));
  return out;
}

// {forText, against, chips}: up to 3 passed checks in check order, the two misses that argue against, role chips.
function tdWhy(row) {
  const passed = TD_FOR_ORDER.map(k => tdCheck(row, k)).filter(c => c && c.passed);
  const forText = passed.slice(0, 3).map(c => tdFact(row, c)).join(" · ");
  const miss = [];
  const it = tdCheck(row, "implied_total");
  if (it && it.passed === false) miss.push(t("slips.td.against.implied_total", { v: tdNum(it.value) }));
  const rz = tdCheck(row, "rz_work");
  if (rz && rz.passed === false) miss.push(t("slips.td.against.rz_work"));
  const against = miss.length ? t("slips.td.against", { list: miss.join(", ") }) : "";
  return { forText, against, chips: tdChips(row) };
}

// A group's rule line, from the packet's own rule values. "" when a value it needs is missing.
function tdRuleLine(tier, rules) {
  const r = rules || {};
  const lock = tdPct(r.lock_min_p), val = tdPct(r.value_min_p), lo = tdPct(r.list_min_p), n = r.value_min_checks;
  if (tier === "LOCK") return lock ? t("slips.td.rule.LOCK", { p: lock }) : "";
  if (tier === "VALUE") return val && n != null ? t("slips.td.rule.VALUE", { p: val, n }) : "";
  if (tier === "MORE") return val && n != null ? t("slips.td.rule.MORE", { p: val, n }) : "";
  if (tier === "LONG") return lo && val ? t("slips.td.rule.LONG", { lo, hi: val }) : "";
  return "";
}

function tdTierRecord(tier, record) {
  const r = (record || {})[tier];
  return r && r.w != null ? t("slips.td.recordTier", { w: r.w, l: r.l, weeks: r.weeks }) : "";
}

// The card's record line: LOCK's record, or when it starts.
function tdRecordLine(block) {
  const r = ((block && block.record) || {}).LOCK;
  const p = tdPct(((block && block.rules) || {}).lock_min_p);
  if (r && r.w != null && p) return t("slips.td.record", { p, w: r.w, l: r.l, weeks: r.weeks });
  return t("slips.td.record.none", { week: (block && block.week) || "" });
}

function tdLabel(key) {
  if (key === "rz_work") return [t("slips.td.check.rz_work.label"), t("slips.td.check.rz_work.meaning")];
  if (key === "implied_total") return [t("slips.td.check.implied_total.label"), t("slips.td.check.implied_total.meaning")];
  if (key === "opp_allowed") return [t("slips.td.check.opp_allowed.label"), t("slips.td.check.opp_allowed.meaning")];
  if (key === "opp_missing") return [t("slips.td.check.opp_missing.label"), t("slips.td.check.opp_missing.meaning")];
  if (key === "near_td") return [t("slips.td.check.near_td.label"), t("slips.td.check.near_td.meaning")];
  return [t("slips.td.check.role_up.label"), t("slips.td.check.role_up.meaning")];
}

function tdCheckNum(row, c) {
  if (c.key === "opp_allowed") return typeof c.value === "number" ? tdFact(row, c) : "";
  if (c.key === "role_up") return tdChips(row).join(", ");
  return typeof c.value === "number" ? tdNum(c.value) : "";
}

// The sheet's six checks: {key, passed, label, meaning, num}, and how many passed.
function tdSheetChecks(row) {
  const rows = TD_CHECK_ORDER.map(k => tdCheck(row, k)).filter(Boolean).map(c => {
    const [label, meaning] = tdLabel(c.key);
    return { key: c.key, passed: !!c.passed, label, meaning, num: tdCheckNum(row, c) };
  });
  return { rows, n: rows.filter(r => r.passed).length };
}

function tdWork(row) {
  const e = row.evidence || {};
  const out = [];
  if (typeof e.rz_per_game === "number") out.push(t("slips.td.work.rz", { v: tdNum(e.rz_per_game) }));
  if (typeof e.gl_per_game === "number") out.push(t("slips.td.work.gl", { v: tdNum(e.gl_per_game) }));
  if (typeof e.tgt_pct === "number") out.push(t("slips.td.work.tgt", { v: tdNum(e.tgt_pct) }));
  if (typeof e.snap === "number") out.push(t("slips.td.work.snap", { v: tdNum(e.snap) }));
  return out;
}

function tdWeather(row) {
  const w = (row.evidence || {}).weather;
  if (!w) return "";
  if (w.roof && w.roof !== "outdoors" && w.roof !== "open") return t("slips.td.wx.dome");
  return t("slips.td.wx", { wind: w.wind_mph, rain: w.precip_pct, temp: w.temp_f });
}
