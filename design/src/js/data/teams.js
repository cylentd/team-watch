/* ------------------------------------------------------------------
   SAMPLE DATA — shaped exactly how the team-watch skill will deliver it.
   Rosters are real (Yahoo draft 2026-09-07, ESPN draft 2026-09-08).
   trend / rank / news payloads are placeholders.
------------------------------------------------------------------ */
const P = (n, pos, team, slug, o) => Object.assign({n, pos, team, slug}, o);

const TEAMS = {
  yahoo: {
    key:"yahoo", plat:"Yahoo", tint:"var(--yahoo)", slot:12,
    name:"Chat Take the Wheel", record:"0–0",
    meta:["12-team", "half PPR", "slot 12", "1 QB / 2 RB / 3 WR / TE / FLEX / DEF"],
    roster:[
      P("Matthew Stafford","QB","LAR","matthew-stafford",{slot:"QB",start:1,trend:[41,38,44,40,46,49],d:+6.2,rank:[11,32,+2,.66],news:1}),
      P("Derrick Henry","RB","BAL","derrick-henry",{slot:"RB1",start:1,trend:[62,58,66,71,69,74],d:+9.4,rank:[5,58,+1,.92],news:2,hot:1}),
      P("De'Von Achane","RB","MIA","devon-achane",{slot:"RB2",start:1,trend:[70,73,68,77,80,83],d:+11.8,rank:[3,58,+2,.96],news:3,hot:1,dual:1}),
      P("Rashee Rice","WR","KC","rashee-rice",{slot:"WR1",start:1,trend:[55,52,49,44,41,38],d:-14.1,rank:[24,74,-6,.68],news:2,status:"Q"}),
      P("Davante Adams","WR","LAR","davante-adams",{slot:"WR2",start:1,trend:[58,60,57,59,55,56],d:-1.2,rank:[16,74,0,.79],news:1}),
      P("Tetairoa McMillan","WR","CAR","tetairoa-mcmillan",{slot:"WR3",start:1,trend:null,d:null,rank:[38,74,0,.49],news:1,dual:1}),
      P("Dallas Goedert","TE","PHI","dallas-goedert",{slot:"TE",start:1,trend:[33,31,36,34,30,29],d:-4.8,rank:[12,26,-3,.55],news:0}),
      P("Jameson Williams","WR","DET","jameson-williams",{slot:"FLEX",start:1,trend:[44,47,51,56,58,63],d:+13.6,rank:[21,74,+5,.72],news:2,hot:1}),
      P("Tony Pollard","RB","TEN","tony-pollard",{slot:"BN",trend:[48,46,45,49,47,44],d:-2.9,rank:[28,58,-1,.52],news:1,dual:1}),
      P("Courtland Sutton","WR","DEN","courtland-sutton",{slot:"BN",trend:[42,45,43,41,44,46],d:+1.8,rank:[31,74,+1,.58],news:0}),
      P("Xavier Worthy","WR","KC","xavier-worthy",{slot:"BN",trend:[36,39,45,48,52,57],d:+15.2,rank:[29,74,+7,.61],news:2,hot:1}),
      P("Deebo Samuel Sr.","WR","WAS","deebo-samuel",{slot:"BN",trend:[47,44,40,38,35,33],d:-9.7,rank:[46,74,-8,.38],news:1}),
      P("Josh Jacobs","RB","GB","josh-jacobs",{slot:"OUT",trend:[64,61,58,0,0,0],d:null,rank:[null,58,null,null],news:4,status:"OUT",statusText:"EXEMPT",
        note:"On the commissioner exempt list since 2026-08-30. Hearing set for Sept 10."}),
    ]
  },
  espn: {
    key:"espn", plat:"ESPN", tint:"var(--espn)", slot:11,
    name:"D. Luu", record:"0–0",
    meta:["12-team","half PPR","slot 11","no kicker · 2 FLEX"],
    roster:[]   // hydrated from LIVE_ESPN below
  }
};

/* Signals keyed by player name. Structure comes from the live pull, these do not —
   model.watch fills them in once nflverse publishes week 1. */
const SIGNALS = {
  "Brock Purdy":        {trend:[39,42,40,45,43,47], d:+5.1,  rank:[14,32,+3,.58], news:1},
  "De'Von Achane":      {trend:[70,73,68,77,80,83], d:+11.8, rank:[3,58,+2,.96],  news:3, hot:1},
  "Cam Skattebo":       {trend:null,                d:null,  rank:[34,58,0,.44],  news:2},
  "Amon-Ra St. Brown":  {trend:[74,72,78,76,80,79], d:+3.3,  rank:[4,74,+1,.95],  news:1},
  "Tee Higgins":        {trend:[59,63,61,66,64,68], d:+6.4,  rank:[13,74,+2,.82], news:1},
  "Tetairoa McMillan":  {trend:null,                d:null,  rank:[38,74,0,.49],  news:1},
  "George Kittle":      {trend:[51,48,54,52,49,53], d:+2.1,  rank:[4,26,+1,.88],  news:1},
  "DK Metcalf":         {trend:[56,54,50,52,48,45], d:-8.3,  rank:[27,74,-4,.63], news:2},
  "Tony Pollard":       {trend:[48,46,45,49,47,44], d:-2.9,  rank:[28,58,-1,.52], news:1},
  "Seahawks":           {trend:[22,26,19,24,28,25], d:+1.4,  rank:[9,32,+2,.71],  news:0},
  "Jared Goff":         {trend:[43,45,42,44,46,45], d:+0.6,  rank:[12,32,0,.63],  news:0},
  "Jordan Mason":       {trend:[31,35,40,44,49,54], d:+18.9, rank:[36,58,+9,.47], news:3, hot:1},
  "Jerry Jeudy":        {trend:[45,42,38,36,33,31], d:-11.4, rank:[52,74,-9,.31], news:1},
  "Hunter Henry":       {trend:[27,29,26,28,25,27], d:-0.4,  rank:[17,26,0,.36],  news:0},
  "Najee Harris":       {trend:[38,36,34,35,32,30], d:-6.8,  rank:[44,58,-5,.26], news:1},
  "Tyrone Tracy Jr.":   {trend:[33,36,34,31,29,27], d:-7.2,  rank:[47,58,-4,.22], news:1},
  "Matthew Stafford":   {trend:[41,38,44,40,46,49], d:+6.2,  rank:[11,32,+2,.66], news:1},
  "Derrick Henry":      {trend:[62,58,66,71,69,74], d:+9.4,  rank:[5,58,+1,.92],  news:2, hot:1},
  "Rashee Rice":        {trend:[55,52,49,44,41,38], d:-14.1, rank:[24,74,-6,.68], news:2, status:"Q"},
  "Davante Adams":      {trend:[58,60,57,59,55,56], d:-1.2,  rank:[16,74,0,.79],  news:1},
  "Dallas Goedert":     {trend:[33,31,36,34,30,29], d:-4.8,  rank:[12,26,-3,.55], news:0},
  "Jameson Williams":   {trend:[44,47,51,56,58,63], d:+13.6, rank:[21,74,+5,.72], news:2, hot:1},
  "Courtland Sutton":   {trend:[42,45,43,41,44,46], d:+1.8,  rank:[31,74,+1,.58], news:0},
  "Xavier Worthy":      {trend:[36,39,45,48,52,57], d:+15.2, rank:[29,74,+7,.61], news:2, hot:1},
  "Deebo Samuel Sr.":   {trend:[47,44,40,38,35,33], d:-9.7,  rank:[46,74,-8,.38], news:1},
  "Josh Jacobs":        {trend:[64,61,58,0,0,0],    d:null,  rank:[null,58,null,null], news:4,
                         status:"OUT", statusText:"EXEMPT",
                         note:"On the commissioner exempt list since 2026-08-30. Hearing set for Sept 10."},
};

