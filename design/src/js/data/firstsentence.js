/* The summary's first sentence: the waiver card's lede on the front, and where the back's rest of the
   summary starts (surface/teams/wcard.js, wback.js). A period after a short word ("St.", "Jr.", "vs.")
   or inside a number ("2.6") is not an end; one after a unit ("pts/wk.") is. Pure; tests/test_js_firstsentence.py. */
function wvFirstSentence(text){
  const m = /^(.+?(?:\b\w{3,}|\d|%|\)|\/\w+)[.!?])\s+(?=[A-Z])/.exec(text || "");
  return m ? m[1] : text || "";
}
