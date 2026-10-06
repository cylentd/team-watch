/* The Digest banner and the Recap banner never carry the same content (David, 2026-10-05: "they should
   never be the same content"). Pure functions, no DOM; the two banners (surface/digest/lead.js,
   surface/recap/banner.js) ask here.

   A banner's subject is the player it is about ("player:<slug>"), else the story itself ("story:<head>");
   "" when it has none, and an empty subject collides with nothing.

   Claude's written story (LIVE_DIGEST.story) is Recap's once the Recap holds a played week and the story
   is a result about that week's top scorer: Recap's banner says it in place of the template headline, and
   the Digest, with no game on, leads with the coming week instead (the packet's own lead). The story
   carries no week of its own: design/digest.py keeps one only for the packet's week, so the Digest's
   week is the story's. A story about anyone else, or of another kind (injury, preview), stays the Digest's.

   Whatever the Digest then leads with must not name the Recap banner's subject: lspPick walks its
   candidates in order and takes the first that does not. */

const lspSubject = L => (L && L.slug ? "player:" + L.slug : L && L.head ? "story:" + L.head : "");

/* Is this story Recap's? Recap must hold a played week (a top scorer, a game final) and it must be the
   story's week. */
function lspOwns(story, digestWeek, recap){
  const p = story && story.player, top = recap && recap.top;
  return !!(p && p.slug && top && top.slug === p.slug && story.kind === "result"
    && recap.week === digestWeek && recap.n_final > 0);
}

const lspRecapStory = (story, digestWeek, recap) => lspOwns(story, digestWeek, recap) ? story : null;
const lspDigestStory = (story, digestWeek, recap) => lspOwns(story, digestWeek, recap) ? null : story || null;

/* The Recap banner's subject: its top scorer, whether it says him with Claude's story (which is only
   ever about him, lspOwns) or with the template. A defense has no slug and so no subject. */
function lspRecapSubject(recap){
  const top = recap && recap.top;
  return top && top.slug ? "player:" + top.slug : "";
}

/* The first candidate (nulls skipped) whose subject is not `avoid`; null when none is. */
function lspPick(candidates, avoid){
  return candidates.find(c => c && (!avoid || lspSubject(c) !== avoid)) || null;
}
