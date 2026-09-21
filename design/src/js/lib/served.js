/* Can this page make a same-origin request at all?

   Opened from disk -- the rendered-DOM suite does exactly this, and so does anyone who
   double-clicks index.html -- every fetch resolves to a file:// URL. Chromium refuses those and
   logs "URL scheme file is not supported" as a console error, once per attempt, on a page that is
   otherwise working fine. It is also never worth asking: a file on disk has no origin behind it
   to answer.

   Shared rather than repeated. Two callers ask it today (the live board and the build-freshness
   check) and the answer is one fact about the page, not two coincidentally similar checks. */
const PAGE_SERVED = () => location.protocol === "http:" || location.protocol === "https:";
