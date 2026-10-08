/* The profile head's second line (2026-09-25): watch's verdict word with its reason. It used to be
   a tag on the roster row; the row became "who, which way, one number" and the storyboard sent it
   here.

   Looked up by slug, never read off the object that opened the sheet. A roster row carries both,
   but search, Waivers and Movers open the sheet with their own objects, and the line has to say the
   same thing whichever way you arrived. The verdict word is watch's own: the page adds none, and
   NEW and hold are dropped as they were on the row (data/signals.js). */
function sheetTagsHTML(p){
  const sig = signalsFor({slug: p.slug || slugOf(p.n)});
  // "On 2 of your teams" left on 2026-09-28: the owner pills (owners.js) name each league's team.
  // A player tag of the same name (RISING, ui/tags.js, 2026-10-08) says it in the body with its own rule: one word, once.
  if (!sig.verdict || tagCovers(tagBlock(), tagWho(p), sig.verdict)) return "";
  // The reason is a sentence (data/signals.js signalWords), not watch's shorthand ("snaps -5.0, share +19").
  const why = signalWords(sig.verdict, sig.why);
  // RISING carries its test in the tooltip (2026-10-06); SELL HIGH passed 12.41 and carries none.
  const tip = sig.verdict === "RISING" ? ` title="${t("profile.signal.risingMark")}"` : "";
  return `<div class="pf-tags" data-testid="profile-tags"><span class="tag verdict" data-testid="profile-verdict"${tip}>${esc(sig.verdict)}</span>`
    + (why ? `<span class="pf-why" data-testid="profile-why">${esc(why)}</span>` : "") + `</div>`;
}
