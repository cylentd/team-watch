/* ---------------------------- helpers ---------------------------- */
const initials = n => n.split(/\s+/).slice(0,2).map(w=>w[0]).join("");
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
/* Copy is data: every user-facing string lives in design/src/content.json, injected above this
   file as `const COPY`. t() looks a key up and fills {name} placeholders. It deliberately does
   NOT escape -- copy may carry intentional markup (<b>, <ol>), and a call site still runs esc()
   over the data it interpolates, exactly as it did before. An unknown key throws rather than
   rendering "undefined": assemble --check catches it first, this catches the rest. */
const t = (k, v) => { const s = COPY[k]; if (s === undefined) throw new Error("copy: " + k); return v ? s.replace(/\{(\w+)\}/g, (_, n) => v[n]) : s; };

