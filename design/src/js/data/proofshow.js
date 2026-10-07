/* Which proof stats a waiver card draws: the ones with a value this week. A stat with none is not
   drawn, and a card with none draws no stats row (surface/teams/proof.js). Pure; tests/test_js_proofshow.py. */
function wvProofShown(cells){
  return (cells || []).filter(c => c.now !== null && c.now !== undefined);
}

/* With no stats row the front has the room, so its text grows into it: the lede is the whole summary
   and the back repeats none of it. With stats, the lede is the first sentence and the back the rest.
   Needs data/firstsentence.js. */
/* A back whose every part is empty adds nothing to the front: the card does not flip. */
const wvBackThin = parts => Object.values(parts).every(p => !p);
/* When the other leagues' lines are all the back would add, they go on the front and the card has no back. */
const wvOthersToFront = parts => !!parts.others && !parts.trends && !parts.summary && !parts.news;
/* An other league that only repeats the header's status says nothing new. In a league where he is
   open (fa or waiver) a verdict or a need is news; elsewhere the line never shows one. */
const wvOtherRepeats = (headStatus, lg) =>
  lg.status === headStatus && (!(lg.status === "fa" || lg.status === "waiver") || (!lg.verdict && !lg.need));
const wvLedeText = (text, hasStats) => hasStats ? wvFirstSentence(text) : text || "";
const wvBackRest = (text, hasStats) => hasStats ? (text || "").slice(wvFirstSentence(text).length).trim() : "";
