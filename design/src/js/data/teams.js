/* ------------------------------------------------------------------
   Team shells. Rosters are real (Yahoo draft 2026-09-07, ESPN draft 2026-09-08); the Yahoo list
   below is only the fallback when build.py injects no LIVE_YAHOO. Trend, rank and news are never
   typed here: hydrate.js fills every row from signals.js.
------------------------------------------------------------------ */
const P = (n, pos, team, slug, o) => Object.assign({n, pos, team, slug}, o);

const TEAMS = {
  yahoo: {
    key:"yahoo", plat:"Yahoo", tint:"var(--yahoo)", slot:12,
    name:"Chat Take the Wheel", record:"0–0",
    meta:["12-team", "half PPR", "slot 12", "1 QB / 2 RB / 3 WR / TE / FLEX / DEF"],
    roster:[
      P("Matthew Stafford","QB","LAR","matthew-stafford",{slot:"QB",start:1}),
      P("Derrick Henry","RB","BAL","derrick-henry",{slot:"RB1",start:1}),
      P("De'Von Achane","RB","MIA","devon-achane",{slot:"RB2",start:1}),
      P("Rashee Rice","WR","KC","rashee-rice",{slot:"WR1",start:1}),
      P("Davante Adams","WR","LAR","davante-adams",{slot:"WR2",start:1}),
      P("Tetairoa McMillan","WR","CAR","tetairoa-mcmillan",{slot:"WR3",start:1}),
      P("Dallas Goedert","TE","PHI","dallas-goedert",{slot:"TE",start:1}),
      P("Jameson Williams","WR","DET","jameson-williams",{slot:"FLEX",start:1}),
      P("Tony Pollard","RB","TEN","tony-pollard",{slot:"BN"}),
      P("Courtland Sutton","WR","DEN","courtland-sutton",{slot:"BN"}),
      P("Xavier Worthy","WR","KC","xavier-worthy",{slot:"BN"}),
      P("Deebo Samuel Sr.","WR","WAS","deebo-samuel",{slot:"BN"}),
      P("Josh Jacobs","RB","GB","josh-jacobs",{slot:"BN"}),
    ]
  },
  espn: {
    key:"espn", plat:"ESPN", tint:"var(--espn)", slot:11,
    name:"D. Luu", record:"0–0",
    meta:["12-team","half PPR","slot 11","no kicker · 2 FLEX"],
    roster:[]   // hydrated from LIVE_ESPN below
  }
};
