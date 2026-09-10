/* ---------------------------- helpers ---------------------------- */
const initials = n => n.split(/\s+/).slice(0,2).map(w=>w[0]).join("");
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

