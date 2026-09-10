/* ------------------------------------------------------------------
   THE POOL — every player who logged a snap, ranked on usage, not points.
   dShare is the change in snap/target share; dPts the change in points.
   The gap between them is the whole product.
------------------------------------------------------------------ */
const POOL = [
  {n:"Chase Brown",      slug:"chase-brown",      pos:"RB", team:"CIN", snaps:71, dSnap:+14.0, share:23.4, dShare:+9.2,  rz:5, ppg:14.2, luck:+0.4, own:41, v:"CONFIRMED"},
  {n:"Denzel Boston",    slug:"denzel-boston",    pos:"WR", team:"LV",  snaps:44, dSnap:+16.2, share:19.1, dShare:+11.1, rz:1, ppg:6.1,  luck:-2.9, own:6,  v:"BUY LOW"},
  {n:"Bhayshul Tuten",   slug:"bhayshul-tuten",   pos:"RB", team:"JAX", snaps:39, dSnap:+13.1, share:20.8, dShare:+12.4, rz:2, ppg:7.4,  luck:-3.8, own:18, v:"BUY LOW"},
  {n:"Brenton Strange",  slug:"brenton-strange",  pos:"TE", team:"JAX", snaps:63, dSnap:+11.4, share:17.6, dShare:+9.8,  rz:3, ppg:11.0, luck:+0.2, own:37, v:"CONFIRMED"},
  {n:"Isaiah Likely",    slug:"isaiah-likely",    pos:"TE", team:"BAL", snaps:58, dSnap:+9.6,  share:16.2, dShare:+8.1,  rz:4, ppg:12.8, luck:+1.1, own:34, v:"CONFIRMED"},
  {n:"Jalen Coker",      slug:"jalen-coker",      pos:"WR", team:"CAR", snaps:66, dSnap:+10.2, share:18.9, dShare:+7.6,  rz:1, ppg:8.2,  luck:-1.2, own:28, v:"BUY LOW"},
  {n:"Blake Corum",      slug:"blake-corum",      pos:"RB", team:"LA",  snaps:34, dSnap:+8.8,  share:15.1, dShare:+6.9,  rz:2, ppg:8.9,  luck:+0.4, own:22, v:"RISING"},
  {n:"Braelon Allen",    slug:"braelon-allen",    pos:"RB", team:"NYJ", snaps:41, dSnap:+7.1,  share:17.7, dShare:+5.2,  rz:3, ppg:7.8,  luck:-2.6, own:31, v:"BUY LOW"},
  {n:"Dylan Sampson",    slug:"dylan-sampson",    pos:"RB", team:"CLE", snaps:29, dSnap:+6.4,  share:13.9, dShare:+4.4,  rz:1, ppg:6.9,  luck:+1.1, own:12, v:"RISING"},
  {n:"Carnell Tate",     slug:"carnell-tate",     pos:"WR", team:"CHI", snaps:52, dSnap:+5.2,  share:14.8, dShare:+3.8,  rz:2, ppg:11.4, luck:+4.9, own:9,  v:"CONFIRMED"},
  {n:"Adonai Mitchell",  slug:"adonai-mitchell",  pos:"WR", team:"IND", snaps:61, dSnap:-1.9,  share:17.2, dShare:-1.4,  rz:3, ppg:15.6, luck:+9.2, own:26, v:"SELL HIGH"},
  {n:"Alec Pierce",      slug:"alec-pierce",      pos:"WR", team:"IND", snaps:57, dSnap:-3.4,  share:15.0, dShare:-2.8,  rz:1, ppg:13.9, luck:+7.1, own:19, v:"SELL HIGH"},
  {n:"Chig Okonkwo",     slug:"chig-okonkwo",     pos:"TE", team:"TEN", snaps:60, dSnap:-2.6,  share:13.1, dShare:-3.2,  rz:1, ppg:7.2,  luck:-1.8, own:21, v:"hold"},
  {n:"Jalen Nailor",     slug:"jalen-nailor",     pos:"WR", team:"MIN", snaps:46, dSnap:-5.1,  share:11.8, dShare:-4.1,  rz:0, ppg:5.4,  luck:-3.3, own:8,  v:"hold"},
  {n:"Dontayvion Wicks", slug:"dontayvion-wicks", pos:"WR", team:"GB",  snaps:43, dSnap:-7.8,  share:10.4, dShare:-6.2,  rz:2, ppg:11.8, luck:+3.4, own:14, v:"SELL HIGH"},
  {n:"Jerry Jeudy",      slug:"jerry-jeudy",      pos:"WR", team:"CLE", snaps:49, dSnap:-11.6, share:12.2, dShare:-9.4,  rz:0, ppg:6.4,  luck:-5.2, own:44, v:"SELL NOW", mine:1},
];

const VCLASS = {"CONFIRMED":"v-conf","RISING":"v-conf","BUY LOW":"v-buy","SELL HIGH":"v-sell","SELL NOW":"v-sell","hold":"v-hold","NEW":"v-hold"};
const VDOT   = {"CONFIRMED":"var(--up)","RISING":"var(--up)","BUY LOW":"var(--lime)","SELL HIGH":"var(--down)","SELL NOW":"var(--down)","hold":"var(--ink-3)","NEW":"var(--ink-3)"};

let POOL_FILTER = "ALL";
/* The ranked list can run long once real usage data lands (this is sample-capped at 16); the
   scatter above it already shows the whole shape, so the list itself pages the same way the
   props and DFS pools do, 10 at a time. */
let POOL_PAGE = 1;
const POOL_PAGE_SIZE = 10;

