import { TITLE_FONT, TITLE_PLACE } from "./constants-title.mjs";
export { TITLE_FONT, TITLE_PLACE };
/* Where the film's title sits, in frame fractions from the top left: the 3D words (film-title-drop.mjs) and the
   tagline under or beside them (film.css, through app.mjs's --film-title-foot and --film-tag-gap). Pure, with no
   three.js, so the page's chrome reads the same numbers the letters do.
   Chapter 17 (David): a desktop's title rises off the frame's foot, so clear turf shows under CURSE and the tagline
   sits inside it; ~~baseline .935, caps .15~~. A desktop's row is `width` wide unless its caps would pass `cap`.
   A phone sets two rows, THE MADDEN over CURSE. */
