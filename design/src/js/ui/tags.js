/* Player tags, drawn (2026-10-08, ledger #41): the one pill on a Roster or Ranks row, and the profile's list of every
   tag with its plain line. data/tags.js decides what each says; this only draws it. No block, no tags: every caller
   gets "" and draws as before. No legend and no Fact or Tested word (David, "show not tell"): the line says it. */
const tagBlock = () => typeof LIVE_PLAYER_TAGS !== "undefined" ? LIVE_PLAYER_TAGS : null;
const tagWho = p => ({slug: p.slug || slugOf(p.n), team: p.team});

/* A pill: the tag's word in its colour; its lines are the hover text, and the row's tap opens the profile that says them. */
const tagPillHTML = (v, where) =>
  `<span class="tg tg-${v.cls}" data-testid="${where}-tag" data-tag="${v.tag}" title="${esc(v.tip)}">${esc(v.label)}</span>`;

function tagRowHTML(p, where){
  const v = tagRowView(tagBlock(), tagWho(p));
  return v ? tagPillHTML(v, where) : "";
}

/* The profile's list: each tag's pill, its plain line beside it. */
function tagsBlockHTML(p){
  const vs = tagViews(tagBlock(), tagWho(p));
  if (!vs.length) return "";
  const item = v => `<li class="tg-item" data-testid="profile-tag-item">${tagPillHTML(v, "profile")}`
    + `<span class="tg-lines" data-testid="profile-tag-lines">${v.lines.map(esc).join(" ")}</span></li>`;
  return `<ul class="tg-list" data-testid="profile-tags-list" aria-label="${t("tags.list.label")}">${vs.map(item).join("")}</ul>`;
}
